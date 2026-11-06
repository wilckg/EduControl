"""Importação de alunos em lote: prévia e confirmação com revalidação integral."""
import csv
from itertools import islice
import io
import re
import unicodedata
from collections import Counter
from openpyxl import load_workbook
from ..models import Student, Class, Enrollment
from ..extensions import db

MAX_BYTES = 3 * 1024 * 1024
MAX_ROWS = 2000
FIELDS = ('name', 'registration', 'email', 'school', 'class_name')
ALIASES = {
    'name': ['nome', 'nome completo', 'aluno', 'nome do aluno', 'student', 'student name'],
    'registration': ['matricula', 'numero da matricula', 'ra', 'registro', 'codigo do aluno', 'registration'],
    'email': ['email', 'e mail', 'e-mail'],
    'school': ['colegio', 'escola', 'instituicao de ensino', 'school'],
    'class_name': ['turma', 'codigo da turma', 'classe', 'class', 'class name'],
}

def normalize(value):
    value = unicodedata.normalize('NFKD', str(value or '').strip())
    return re.sub(r'\s+', ' ', ''.join(c for c in value if not unicodedata.combining(c))).casefold()

def read_sheet(filename, filebytes):
    if not filename.lower().endswith(('.csv', '.xlsx')):
        raise ValueError('Formato inválido: utilize .csv ou .xlsx')
    if len(filebytes) > MAX_BYTES:
        raise ValueError('Arquivo excede o limite de 3 MB')
    if not filebytes:
        raise ValueError('Arquivo vazio')
    if filename.lower().endswith('.csv'):
        try: content = filebytes.decode('utf-8-sig')
        except UnicodeDecodeError: raise ValueError('CSV deve estar em UTF-8')
        sample = content[:4096]
        try: dialect = csv.Sniffer().sniff(sample, delimiters=',;\t')
        except csv.Error: dialect = csv.excel
        reader = csv.reader(io.StringIO(content), dialect=dialect)
        parsed = list(islice(reader, MAX_ROWS + 3))
    else:
        try:
            wb = load_workbook(io.BytesIO(filebytes), read_only=True, data_only=True)
            parsed = list(islice(wb.active.iter_rows(values_only=True), MAX_ROWS + 3))
            wb.close()
        except Exception: raise ValueError('Não foi possível ler o arquivo XLSX')
    parsed = [list(r) for r in parsed if any(str(c or '').strip() for c in r)]
    if not parsed or len(parsed) < 2:
        raise ValueError('Planilha precisa ter cabeçalho e pelo menos um aluno')
    if len(parsed) - 1 > MAX_ROWS:
        raise ValueError(f'Máximo de {MAX_ROWS} linhas por importação')
    headers = [str(x or '').strip() for x in parsed[0]]
    if not all(headers) or len(set(normalize(h) for h in headers)) != len(headers):
        raise ValueError('Cabeçalhos vazios ou repetidos')
    if len(headers) > 60:
        raise ValueError('Máximo de 60 colunas')
    entries = []
    for i, r in enumerate(parsed[1:], start=2):
        entries.append({'line':i,'values': {h: str(r[j] if j < len(r) and r[j] is not None else '').strip() for j,h in enumerate(headers)}})
    return headers, entries

def guess_mapping(headers):
    return {field: next((h for h in headers if normalize(h) in [normalize(a) for a in names]), '') for field,names in ALIASES.items()}

def validate_mapping(headers, mapping):
    for field in FIELDS:
        selected = mapping.get(field, '')
        if selected and selected not in headers:
            raise ValueError(f'Coluna inválida para {field}: {selected}')
    if not mapping.get('name') or not mapping.get('registration'):
        raise ValueError('Associe as colunas Nome e Matrícula')

def make_plan(headers, entries, mapping, default_class_id=None):
    validate_mapping(headers,mapping)
    classes = Class.query.order_by(Class.id).all()
    by_name = {}
    for c in classes:
        by_name.setdefault(normalize(c.name), []).append(c)
    chosen = db.session.get(Class,default_class_id) if default_class_id else None
    if default_class_id and not chosen:
        raise ValueError('Turma padrão inexistente')
    registrations = [str(e['values'].get(mapping['registration'], '')).strip() for e in entries]
    known = {s.registration: s for s in Student.query.filter(Student.registration.in_(registrations)).all()}
    existing_enroll = {(e.student_id,e.class_id) for e in Enrollment.query.filter(Enrollment.student_id.in_([s.id for s in known.values()])).all()}
    seen=set(); rows=[]; counts=Counter()
    for entry in entries:
        values=entry['values']; row={f:values.get(mapping.get(f) or '', '').strip() for f in FIELDS}
        row['line']=entry['line']; issues=[]
        if len(row['name']) < 2 or len(row['name']) > 150: issues.append('Nome obrigatório (2 a 150 caracteres)')
        if not row['registration'] or len(row['registration']) > 30: issues.append('Matrícula obrigatória (até 30 caracteres)')
        if len(row['email']) > 150 or (row['email'] and ('@' not in row['email'] or ' ' in row['email'])): issues.append('E-mail inválido')
        if len(row['school']) > 180: issues.append('Colégio excede 180 caracteres')
        if row['registration'] in seen: issues.append('Matrícula repetida na planilha')
        seen.add(row['registration'])
        clazz=None
        if row['class_name']:
            matches=by_name.get(normalize(row['class_name']),[])
            if len(matches)==1: clazz=matches[0]
            else: issues.append('Turma não encontrada ou código ambíguo')
        elif chosen: clazz=chosen
        else: issues.append('Turma não informada; selecione uma turma padrão')
        original=known.get(row['registration'])
        if original and normalize(original.name)!=normalize(row['name']):
            issues.append('Matrícula já cadastrada com outro nome: revisão manual necessária')
        row['class_id']=clazz.id if clazz else None
        row['resolved_class']=clazz.name if clazz else None
        if issues: row['status']='error'
        elif original and (original.id,clazz.id) in existing_enroll: row['status']='skip'
        elif original: row['status']='enroll'
        else: row['status']='create'
        row['issues']=issues
        counts[row['status']]+=1
        rows.append(row)
    return {'headers':headers, 'mapping':mapping, 'rows':rows, 'counts': {x:counts[x] for x in ('create','enroll','skip','error')}, 'can_commit': counts['error']==0 and bool(rows), 'total':len(rows)}

def commit_plan(plan):
    if not plan['can_commit']: raise ValueError('Corrija as linhas inválidas antes de importar')
    created=enrolled=skipped=0
    # An all-or-nothing operation: rollback on unexpected errors, no partial imports.
    try:
        for row in plan['rows']:
            if row['status']=='skip': skipped+=1; continue
            student=Student.query.filter_by(registration=row['registration']).first()
            if student is None:
                student=Student(name=row['name'],registration=row['registration'],email=row['email'] or None,school=row['school'] or None)
                db.session.add(student); db.session.flush(); created+=1
            elif normalize(student.name)!=normalize(row['name']):
                raise ValueError('Dados modificados desde a prévia; faça nova validação')
            if Enrollment.query.filter_by(student_id=student.id,class_id=row['class_id']).first():
                skipped+=1;continue
            db.session.add(Enrollment(student_id=student.id,class_id=row['class_id'],status='active'))
            enrolled+=1
        return {'students_created':created,'enrollments_created':enrolled,'skipped':skipped}
    except Exception:
        db.session.rollback()
        raise
