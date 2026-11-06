"""Rotas de operations do EduControl."""
from ..core import *

@app.get('/api/occurrences')
@require('admin','coordenador','professor')
def occurrences():
    q=Occurrence.query.order_by(Occurrence.created_at.desc())
    if current_user().role=='professor':q=q.join(Class,Occurrence.class_id==Class.id).filter(Class.teacher_id==current_user().id)
    return jsonify([dict(id=o.id,student=student_json(o.student),class_id=o.class_id,category=o.category,description=o.description,author=o.author.name,created_at=o.created_at.isoformat()) for o in q.limit(100)])

@app.post('/api/occurrences')
@require('admin','professor')
def create_occurrence():
    d=request.get_json(silent=True) or {};sid=parse_id(d,'student_id');cid=parse_id(d,'class_id');accessible_class(cid)
    if not Enrollment.query.filter_by(student_id=sid,class_id=cid).first():abort(400,description='Aluno não pertence ao histórico desta turma')
    category=str(d.get('category','')).strip();description=str(d.get('description','')).strip()
    if not category or len(description)<5:abort(400,description='Categoria e descrição de pelo menos 5 caracteres são obrigatórias')
    o=Occurrence(student_id=sid,class_id=cid,author_id=current_user().id,category=category[:60],description=description);db.session.add(o);audit('occurrence.create',str(sid));db.session.commit();return jsonify(id=o.id),201

@app.get('/api/transfers')
@require('admin','coordenador','secretaria')
def transfers():
    return jsonify([dict(id=t.id,student=student_json(db.session.get(Student,t.student_id)),from_class=db.session.get(Class,t.from_class_id).name,to_class=db.session.get(Class,t.to_class_id).name,reason=t.reason,transferred_at=t.transferred_at.isoformat()) for t in Transfer.query.order_by(Transfer.id.desc()).limit(100)])

@app.post('/api/transfers')
@require('admin','coordenador','secretaria')
def create_transfer():
    d=request.get_json(silent=True) or {};eid=parse_id(d,'enrollment_id');cid=parse_id(d,'to_class_id')
    e=db.session.get(Enrollment,eid);dest=db.session.get(Class,cid);reason=str(d.get('reason','')).strip()
    if not e or not dest:abort(404,description='Matrícula ou turma não encontrada')
    if e.status!='active' or e.class_id==cid or not reason:abort(400,description='Transferência inválida ou motivo ausente')
    if e.clazz.course_id!=dest.course_id:abort(400,description='A POC permite transferências apenas entre turmas do mesmo curso')
    if Enrollment.query.filter_by(student_id=e.student_id,class_id=cid,status='active').first():abort(400,description='Aluno já matriculado no destino')
    e.status='transferred';e.closed_at=date.today()
    db.session.add(Enrollment(student_id=e.student_id,class_id=cid,enrolled_at=date.today()))
    db.session.add(Transfer(student_id=e.student_id,from_class_id=e.class_id,to_class_id=cid,reason=reason))
    audit('transfer.create',f'{e.student_id} {e.class_id}->{cid}');db.session.commit();return jsonify(ok=True),201

@app.get('/api/teachers')
@require('admin','coordenador','secretaria')
def teacher_options():
    # Somente dados mínimos necessários para selecionar o responsável da turma.
    return jsonify([{'id':u.id,'name':u.name,'role':u.role} for u in User.query.filter_by(role='professor',active=True).order_by(User.name).all()])
