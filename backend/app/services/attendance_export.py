"""Exportação operacional; uma linha por vínculo matrícula/aula, sem presumir layout externo."""
from collections import defaultdict
from .reports import report_params
from ..extensions import db
from ..models import Class, Lesson, Attendance, Enrollment, Student
from flask import abort

HEADERS = ['turma', 'curso', 'matricula', 'aluno', 'data_aula', 'horas_aula', 'conteudo', 'presenca', 'horas_presentes', 'horas_falta']

def attendance_export_rows(filters):
    if not filters.get('class_id'):
        abort(400, description='Selecione uma turma para exportar chamadas')
    clazz = db.session.get(Class, filters['class_id'])
    if clazz is None:
        abort(404, description='Turma não encontrada')
    q = (db.session.query(Attendance, Lesson, Enrollment, Student)
         .join(Lesson, Attendance.lesson_id == Lesson.id)
         .join(Enrollment, Attendance.enrollment_id == Enrollment.id)
         .join(Student, Enrollment.student_id == Student.id)
         .filter(Lesson.class_id == clazz.id, Enrollment.class_id == clazz.id))
    if filters.get('date_from'):
        q = q.filter(Lesson.held_on >= filters['date_from'])
    if filters.get('date_to'):
        q = q.filter(Lesson.held_on <= filters['date_to'])
    q = q.order_by(Lesson.held_on, Lesson.id, Student.name, Enrollment.id)
    rows = []
    for attendance, lesson, enrollment, student in q.all():
        if attendance.status not in ('P', 'F', 'J'):
            continue
        rows.append({
            'turma': clazz.name, 'curso': clazz.course.name,
            'matricula': student.registration, 'aluno': student.name,
            'data_aula': lesson.held_on.isoformat(), 'horas_aula': lesson.hours,
            'conteudo': lesson.topic or '', 'presenca': attendance.status,
            'horas_presentes': lesson.hours if attendance.status == 'P' else 0,
            'horas_falta': lesson.hours if attendance.status in ('F', 'J') else 0,
            '_enrollment_id': enrollment.id, '_lesson_id': lesson.id,
        })
    return clazz, rows

def create_operational_xlsx(clazz, rows):
    from io import BytesIO
    import xlsxwriter
    output = BytesIO()
    wb = xlsxwriter.Workbook(output, {'in_memory': True, 'strings_to_formulas': False, 'strings_to_urls': False})
    header = wb.add_format({'bold': True, 'bg_color':'#143D78', 'font_color': '#FFFFFF'})
    for sheet_name, data, cols in [
        ('Registros', rows, HEADERS),
        ('Matriz', matrix_rows(rows), ['matricula', 'aluno'] + matrix_dates(rows))]:
        sh = wb.add_worksheet(sheet_name)
        for j, name in enumerate(cols): sh.write_string(0, j, name, header)
        for i, item in enumerate(data, start=1):
            for j, key in enumerate(cols):
                value = item.get(key, '')
                if value is None: value = ''
                if isinstance(value, (int,float)): sh.write_number(i,j,value)
                else: sh.write_string(i,j,str(value))
        sh.freeze_panes(1,2)
        sh.set_column(0,0,20);sh.set_column(1,1,35);sh.set_column(2,len(cols)-1,18)
        if cols: sh.autofilter(0,0,max(1,len(data)),len(cols)-1)
    notes = wb.add_worksheet('Legenda')
    for i, line in enumerate([
        'P = presente; F = falta; J = falta justificada (contabiliza horas de falta na POC).',
        'Matriz: colunas de aula são data#ID; aulas distintas no mesmo dia permanecem separadas.',
        'Célula vazia na matriz significa ausência de registro, e não falta.',
        'Aba Registros: somente presenças/faltas salvas; matrícula preservada por vínculo.',
        'Formato provisório: confirmar colunas e regras com a automação externa antes do uso operacional.'
    ]): notes.write_string(i,0,line)
    notes.set_column(0,0,115)
    wb.close(); output.seek(0)
    return output

def matrix_dates(rows):
    return list(dict.fromkeys(f"{r['data_aula']}#{r['_lesson_id']}" for r in rows))

def matrix_rows(rows):
    result = {}
    for row in rows:
        eid = row['_enrollment_id']
        item = result.setdefault(eid, {'matricula':row['matricula'], 'aluno':row['aluno']})
        item[f"{row['data_aula']}#{row['_lesson_id']}"] = row['presenca']
    return list(result.values())
