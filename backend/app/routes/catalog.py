"""Rotas de catalog do EduControl."""
from ..core import *

@app.get('/api/courses')
@require()
def courses(): return jsonify([course_json(c) for c in Course.query.order_by(Course.name)])

@app.post('/api/courses')
@require('admin','secretaria')
def create_course():
    d=request.get_json(silent=True) or {}; name=str(d.get('name','')).strip()
    if not name: abort(400,description='Nome obrigatório')
    try: hours=float(d.get('hours')); min_a=float(d.get('min_attendance',75))
    except (TypeError,ValueError): abort(400,description='Carga horária ou frequência inválida')
    if hours<=0 or not 0<min_a<=100: abort(400,description='Parâmetros fora do intervalo')
    c=Course(name=name,hours=hours,min_attendance=min_a); db.session.add(c);audit('course.create',name);db.session.commit()
    return jsonify(course_json(c)),201

@app.patch('/api/courses/<int:cid>')
@require('admin','secretaria')
def update_course(cid):
    c=db.session.get(Course,cid)
    if not c: abort(404,description='Curso não encontrado')
    d=request.get_json(silent=True) or {}
    name=str(d.get('name',c.name)).strip()
    try: hrs=float(d.get('hours',c.hours)); minimum=float(d.get('min_attendance',c.min_attendance))
    except (ValueError,TypeError): abort(400,description='Valores inválidos')
    if not name or hrs<=0 or not 0<minimum<=100: abort(400,description='Dados inválidos')
    c.name=name;c.hours=hrs;c.min_attendance=minimum
    audit('course.update',cid);db.session.commit();return jsonify(course_json(c))

@app.delete('/api/courses/<int:cid>')
@require('admin','secretaria')
def delete_course(cid):
    c=db.session.get(Course,cid)
    if not c: abort(404,description='Curso não encontrado')
    if Class.query.filter_by(course_id=cid).first(): abort(409,description='Curso possui turmas. Não é possível excluir.')
    db.session.delete(c);audit('course.delete',cid);db.session.commit();return jsonify(ok=True)

@app.get('/api/classes')
@require()
def classes():
    q=Class.query.order_by(Class.id)
    if current_user().role=='professor': q=q.filter_by(teacher_id=current_user().id)
    return jsonify([class_json(c) for c in q.all()])

@app.get('/api/classes/<int:class_id>/overview')
@require()
def class_overview(class_id):
    clazz = accessible_class(class_id)
    enrollments = Enrollment.query.filter_by(class_id=class_id).order_by(Enrollment.id).all()
    lessons = Lesson.query.filter_by(class_id=class_id).order_by(Lesson.held_on.desc(), Lesson.id.desc()).all()
    payload = dict(
        clazz=class_json(clazz),
        enrollments=[dict(**enrollment_json(e), frequency=attendance_stats(e)) for e in enrollments],
        lessons=[dict(**lesson_json(l), present=Attendance.query.filter_by(lesson_id=l.id,status='P').count(),
                      absent=Attendance.query.filter(Attendance.lesson_id==l.id,Attendance.status.in_(['F','J'])).count()) for l in lessons],
    )
    if current_user().role in ('admin','coordenador','professor'):
        occurrences = Occurrence.query.filter_by(class_id=class_id).order_by(Occurrence.created_at.desc()).all()
        payload['occurrences'] = [dict(id=o.id, student=student_json(o.student), category=o.category,
            description=o.description, author=o.author.name, created_at=o.created_at.isoformat()) for o in occurrences]
    if current_user().role in ('admin','coordenador','secretaria'):
        transfers = Transfer.query.filter((Transfer.from_class_id==class_id) | (Transfer.to_class_id==class_id)).order_by(Transfer.transferred_at.desc()).all()
        payload['transfers'] = [dict(id=t.id,student=student_json(db.session.get(Student,t.student_id)),
            from_class=db.session.get(Class,t.from_class_id).name,to_class=db.session.get(Class,t.to_class_id).name,
            reason=t.reason,transferred_at=t.transferred_at.isoformat()) for t in transfers]
    return jsonify(payload)

@app.post('/api/classes')
@require('admin','secretaria')
def create_class():
    d=request.get_json(silent=True) or {}; name=str(d.get('name','')).strip(); course=db.session.get(Course,parse_id(d,'course_id'))
    if not name or not course: abort(400,description='Nome e curso válidos obrigatórios')
    teacher_id=int(d['teacher_id']) if d.get('teacher_id') else None
    if teacher_id and (not db.session.get(User,teacher_id) or db.session.get(User,teacher_id).role!='professor'):abort(400,description='Professor inválido')
    c=Class(name=name,course_id=course.id,teacher_id=teacher_id,start_date=as_date(d['start_date']) if d.get('start_date') else None,end_date=as_date(d['end_date']) if d.get('end_date') else None)
    db.session.add(c);audit('class.create',name);db.session.commit();return jsonify(class_json(c)),201

@app.patch('/api/classes/<int:cid>')
@require('admin','secretaria')
def update_class(cid):
    c=db.session.get(Class,cid)
    if not c: abort(404,description='Turma não encontrada')
    d=request.get_json(silent=True) or {}
    if 'name' in d:
        c.name=str(d['name']).strip()
        if not c.name:abort(400,description='Código da turma obrigatório')
    if 'course_id' in d:
        new_course=db.session.get(Course,parse_id(d,'course_id'))
        if not new_course:abort(404,description='Curso não encontrado')
        if new_course.id!=c.course_id and (Enrollment.query.filter_by(class_id=cid).first() or Lesson.query.filter_by(class_id=cid).first()):abort(409,description='Não altere o curso de uma turma com histórico')
        c.course_id=new_course.id
    if 'teacher_id' in d:
        tid=int(d['teacher_id']) if d['teacher_id'] else None
        if tid and (not db.session.get(User,tid) or db.session.get(User,tid).role!='professor'):abort(400,description='Professor inválido')
        c.teacher_id=tid
    for key in ('start_date','end_date'):
        if key in d:setattr(c,key,as_date(d[key]) if d[key] else None)
    if c.start_date and c.end_date and c.end_date<c.start_date:abort(400,description='Período inválido')
    audit('class.update',cid);db.session.commit();return jsonify(class_json(c))

@app.delete('/api/classes/<int:cid>')
@require('admin','secretaria')
def delete_class(cid):
    c=db.session.get(Class,cid)
    if not c: abort(404,description='Turma não encontrada')
    if (Enrollment.query.filter_by(class_id=cid).first() or Lesson.query.filter_by(class_id=cid).first() or Occurrence.query.filter_by(class_id=cid).first() or Transfer.query.filter((Transfer.from_class_id==cid)|(Transfer.to_class_id==cid)).first()):abort(409,description='Turma com histórico não pode ser excluída; preserve matrículas, aulas e ocorrências')
    db.session.delete(c);audit('class.delete',cid);db.session.commit();return jsonify(ok=True)

