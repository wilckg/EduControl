"""Rotas de dashboards do EduControl."""
from ..core import *


@app.get('/api/secretaria/summary')
@require('admin','coordenador','secretaria')
def secretaria_summary():
    transfers=Transfer.query.order_by(Transfer.id.desc()).limit(5).all()
    unassigned=Class.query.filter(Class.teacher_id.is_(None)).order_by(Class.name).all()
    return jsonify(
        students_total=Student.query.count(),
        active_enrollments=Enrollment.query.filter_by(status='active').count(),
        classes_total=Class.query.count(),
        transfers_total=Transfer.query.count(),
        classes_without_teacher=[{'id':c.id,'name':c.name,'course':c.course.name} for c in unassigned],
        recent_transfers=[{'student':db.session.get(Student,t.student_id).name,'from_class':db.session.get(Class,t.from_class_id).name,'to_class':db.session.get(Class,t.to_class_id).name} for t in transfers]
    )

@app.get('/api/dashboard')
@require()
def dashboard():
    cls=Class.query
    if current_user().role=='professor':cls=cls.filter_by(teacher_id=current_user().id)
    classes_list=cls.all();ids=[c.id for c in classes_list]
    enrollments=Enrollment.query.filter(Enrollment.class_id.in_(ids),Enrollment.status=='active').all()
    stats=[attendance_stats(e) for e in enrollments]
    return jsonify(classes=len(classes_list),students=len({e.student_id for e in enrollments}),average_attendance=round(sum(s['attendance_percent'] for s in stats)/len(stats),1) if stats else 100,alerts=sum(s['severity']!='ok' for s in stats))

