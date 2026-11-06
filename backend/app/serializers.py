"""Conversão dos modelos para respostas JSON."""
from .models import Enrollment
from .services.frequency import attendance_stats

def user_json(u): return dict(id=u.id,name=u.name,email=u.email,role=u.role,active=u.active)
def course_json(c): return dict(id=c.id,name=c.name,hours=c.hours,min_attendance=c.min_attendance)
def student_json(s): return dict(id=s.id,name=s.name,registration=s.registration,email=s.email,photo_url=(f"/api/students/{s.id}/photo" if s.photo_url else None),school=s.school)
def class_json(c):
    return dict(id=c.id,name=c.name,course_id=c.course_id,course=c.course.name,hours=c.course.hours,min_attendance=c.course.min_attendance,teacher_id=c.teacher_id,teacher=c.teacher.name if c.teacher else 'Não definido',status=c.status,start_date=c.start_date.isoformat() if c.start_date else None,end_date=c.end_date.isoformat() if c.end_date else None,students=Enrollment.query.filter_by(class_id=c.id,status='active').count())
def lesson_json(l): return dict(id=l.id,class_id=l.class_id,held_on=l.held_on.isoformat(),hours=l.hours,topic=l.topic)
def enrollment_json(e):
    return dict(id=e.id,student=student_json(e.student),class_id=e.class_id,class_name=e.clazz.name,course=e.clazz.course.name,status=e.status,enrolled_at=e.enrolled_at.isoformat(),closed_at=e.closed_at.isoformat() if e.closed_at else None)

