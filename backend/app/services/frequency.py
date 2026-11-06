"""Indicadores de frequência por matrícula."""
from ..extensions import db
from ..models import Attendance, Lesson

def attendance_stats(e):
    # Dados consolidados por matrícula: histórico de transferências permanece na matrícula antiga.
    records = db.session.query(Attendance,Lesson).join(Lesson,Attendance.lesson_id==Lesson.id).filter(Attendance.enrollment_id==e.id).all()
    present = sum(l.hours for a,l in records if a.status=='P')
    absent = sum(l.hours for a,l in records if a.status in ('F','J'))
    recorded = present+absent
    course = e.clazz.course
    rate = round(100*present/recorded,1) if recorded else 100.0
    allowed = course.hours*(100-course.min_attendance)/100
    remaining = max(0,round(allowed-absent,1))
    # A POC mantém as horas da matrícula antiga separadas após transferências.
    severity = 'exceeded' if absent > allowed else 'critical' if remaining <= 4 else 'warning' if remaining <= 8 else 'ok'
    return dict(present_hours=present,absent_hours=absent,recorded_hours=recorded,attendance_percent=rate,max_absent_hours=round(allowed,1),remaining_absent_hours=remaining,severity=severity,min_attendance=course.min_attendance,course_hours=course.hours)

