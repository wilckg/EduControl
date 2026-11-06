"""Consultas para relatórios acadêmicos (horas reais registradas por matrícula)."""
from collections import defaultdict
from datetime import date
from flask import abort
from ..models import Course, Class, Student, Enrollment, Lesson, Attendance
from ..extensions import db


def report_params(args):
    """Valida filtros antes de criar a consulta."""
    result = {}
    for key in ('course_id', 'class_id', 'student_id'):
        value = args.get(key)
        if value:
            try:
                result[key] = int(value)
                if result[key] <= 0: raise ValueError()
            except ValueError:
                abort(400, description=f'Filtro {key} inválido')
    for key in ('date_from', 'date_to'):
        if args.get(key):
            try: result[key] = date.fromisoformat(args[key])
            except ValueError: abort(400, description=f'{key} deve ser AAAA-MM-DD')
    if result.get('date_from') and result.get('date_to') and result['date_from'] > result['date_to']:
        abort(400, description='Período inicial posterior ao final')
    return result


def attendance_report(filters):
    """Por matrícula, sem somar histórico transferido à matrícula nova.

    Percentuais de frequência respeitam o intervalo selecionado.
    Progresso ministrado respeita todas as aulas até a data final; não depende da data inicial.
    Faltas para risco são acumuladas até a data final para evitar mascarar alertas.
    """
    query = db.session.query(Enrollment).join(Class, Enrollment.class_id == Class.id).join(Course, Class.course_id == Course.id)
    if filters.get('course_id'): query = query.filter(Class.course_id == filters['course_id'])
    if filters.get('class_id'): query = query.filter(Enrollment.class_id == filters['class_id'])
    if filters.get('student_id'): query = query.filter(Enrollment.student_id == filters['student_id'])
    enrollments = query.order_by(Class.name, Enrollment.id).all()
    if not enrollments:
        return dict(rows=[], summary=dict(students=0, enrollments=0, average_attendance=None, critical=0, warning=0), notes=_NOTES)

    class_ids = {e.class_id for e in enrollments}
    lessons_query = Lesson.query.filter(Lesson.class_id.in_(class_ids))
    if filters.get('date_to'): lessons_query = lessons_query.filter(Lesson.held_on <= filters['date_to'])
    all_lessons = lessons_query.all()
    lesson_map = {l.id: l for l in all_lessons}
    total_by_class = defaultdict(float)
    for lesson in all_lessons: total_by_class[lesson.class_id] += lesson.hours

    enrollment_ids = [e.id for e in enrollments]
    records = (db.session.query(Attendance)
               .filter(Attendance.enrollment_id.in_(enrollment_ids), Attendance.lesson_id.in_(lesson_map.keys()))
               .all()) if lesson_map else []
    period_present, period_absent, accumulated_absent = defaultdict(float), defaultdict(float), defaultdict(float)
    for record in records:
        lesson = lesson_map[record.lesson_id]
        if record.status in ('F', 'J'): accumulated_absent[record.enrollment_id] += lesson.hours
        if filters.get('date_from') and lesson.held_on < filters['date_from']: continue
        if record.status == 'P': period_present[record.enrollment_id] += lesson.hours
        elif record.status in ('F', 'J'): period_absent[record.enrollment_id] += lesson.hours

    result = []
    for enrollment in enrollments:
        cid = enrollment.class_id
        course = enrollment.clazz.course
        present = period_present[enrollment.id]
        absent = period_absent[enrollment.id]
        recorded = present + absent
        rate = round(100 * present / recorded, 1) if recorded else None
        max_absences = course.hours * (100 - course.min_attendance) / 100
        remain = max_absences - accumulated_absent[enrollment.id]
        severity = ('exceeded' if remain < 0 else 'critical' if remain <= 4 else 'warning' if remain <= 8 else 'ok')
        conducted = total_by_class[cid]
        result.append(dict(enrollment_id=enrollment.id,student_id=enrollment.student.id,
            student=enrollment.student.name,registration=enrollment.student.registration,
            class_id=cid,class_name=enrollment.clazz.name,course_id=course.id,course=course.name,
            enrollment_status=enrollment.status,present_hours=round(present,2),absent_hours=round(absent,2),
            recorded_hours=round(recorded,2),attendance_percent=rate,
            taught_hours=round(conducted,2),course_hours=course.hours,
            progress_percent=round(min(100, 100 * conducted/course.hours),1) if course.hours else 0,
            absent_accumulated=round(accumulated_absent[enrollment.id],2),
            remaining_absent_hours=round(max(0,remain),2),severity=severity))
    rates = [r['attendance_percent'] for r in result if r['attendance_percent'] is not None]
    return dict(rows=result,summary=dict(students=len({r['student_id'] for r in result}),enrollments=len(result),
        average_attendance=round(sum(rates)/len(rates),1) if rates else None,
        critical=sum(r['severity'] in ('critical','exceeded') for r in result),
        warning=sum(r['severity']=='warning' for r in result)),notes=_NOTES)

_NOTES = [
    'Frequência: horas presentes / horas com chamada registrada dentro do período selecionado.',
    'Progresso do curso: horas de aulas da turma ministradas até a data final / carga horária prevista.',
    'Risco: faltas acumuladas até a data final versus máximo permitido no curso (alertas demonstrativos).',
    'Históricos de matrículas após transferência permanecem separados; aulas sem chamada não entram na frequência.',
]
