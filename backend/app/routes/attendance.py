"""Rotas de attendance do EduControl."""
from ..core import *

@app.get('/api/enrollments')
@require()
def enrollments():
    q=Enrollment.query.order_by(Enrollment.id)
    if current_user().role=='professor':q=q.join(Class,Enrollment.class_id==Class.id).filter(Class.teacher_id==current_user().id)
    return jsonify([enrollment_json(e) for e in q.all()])

@app.post('/api/enrollments')
@require('admin','secretaria')
def enroll():
    d=request.get_json(silent=True) or {}; sid=parse_id(d,'student_id');cid=parse_id(d,'class_id')
    if not db.session.get(Student,sid) or not db.session.get(Class,cid):abort(404,description='Aluno ou turma não encontrado')
    if Enrollment.query.filter_by(student_id=sid,class_id=cid,status='active').first():abort(400,description='Aluno já matriculado')
    e=Enrollment(student_id=sid,class_id=cid);db.session.add(e);audit('enrollment.create',f'{sid}/{cid}');db.session.commit();return jsonify(enrollment_json(e)),201

@app.get('/api/classes/<int:class_id>/lessons')
@require()
def lessons(class_id):
    accessible_class(class_id)
    return jsonify([lesson_json(l) for l in Lesson.query.filter_by(class_id=class_id).order_by(Lesson.held_on.desc(),Lesson.id.desc())])

@app.post('/api/lessons')
@require('admin','professor')
def create_lesson():
    d=request.get_json(silent=True) or {};cid=parse_id(d,'class_id');accessible_class(cid)
    l=Lesson(class_id=cid,held_on=as_date(d.get('held_on')),hours=positive_hours(d.get('hours')),topic=str(d.get('topic',''))[:250]);db.session.add(l);db.session.flush()
    for e in Enrollment.query.filter_by(class_id=cid,status='active'):
        db.session.add(Attendance(lesson_id=l.id,enrollment_id=e.id,status='P'))
    audit('lesson.create',str(l.id));db.session.commit();return jsonify(lesson_json(l)),201

@app.get('/api/lessons/<int:lesson_id>/attendance')
@require()
def lesson_attendance(lesson_id):
    lesson=db.session.get(Lesson,lesson_id)
    if not lesson:abort(404)
    accessible_class(lesson.class_id)
    rows=db.session.query(Attendance,Enrollment,Student).join(Enrollment,Attendance.enrollment_id==Enrollment.id).join(Student,Enrollment.student_id==Student.id).filter(Attendance.lesson_id==lesson_id).order_by(Student.name).all()
    return jsonify(dict(lesson=lesson_json(lesson),records=[dict(id=a.id,enrollment_id=e.id,student=student_json(s),status=a.status) for a,e,s in rows]))

@app.put('/api/lessons/<int:lesson_id>/attendance')
@require('admin','professor')
def save_attendance(lesson_id):
    l=db.session.get(Lesson,lesson_id)
    if not l:abort(404)
    accessible_class(l.class_id)
    d=request.get_json(silent=True) or {};items=d.get('records')
    if not isinstance(items,list):abort(400,description='records deve ser lista')
    allowed={a.enrollment_id:a for a in Attendance.query.filter_by(lesson_id=lesson_id)}
    for item in items:
        eid=parse_id(item,'enrollment_id');status=item.get('status')
        if eid not in allowed or status not in ('P','F','J'):abort(400,description='Registro ou status inválido')
        allowed[eid].status=status
    audit('attendance.update',str(lesson_id));db.session.commit();return jsonify(ok=True)

@app.get('/api/alerts')
@require('admin','coordenador','secretaria')
def alerts():
    q=Enrollment.query.filter_by(status='active')
    result=[]
    for e in q.all():
        s=attendance_stats(e)
        if s['severity']!='ok':result.append(dict(enrollment_id=e.id,student=student_json(e.student),class_name=e.clazz.name,**s))
    return jsonify(sorted(result,key=lambda x:({'exceeded':0,'critical':1,'warning':2}.get(x['severity'],3),x['remaining_absent_hours'])))

@app.get('/api/enrollments/<int:eid>/frequency')
@require()
def frequency(eid):
    e=db.session.get(Enrollment,eid)
    if not e:abort(404)
    accessible_class(e.class_id)
    return jsonify(dict(enrollment=enrollment_json(e),**attendance_stats(e)))

