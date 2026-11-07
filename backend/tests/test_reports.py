"""Testes isolados em SQLite; NUNCA usam o banco configurado no Docker."""
import os
import tempfile
from pathlib import Path
import pytest

# Importar o app somente após configurar um banco descartável exclusivo deste teste.
_temp = tempfile.TemporaryDirectory(prefix='educontrol-tests-')
os.environ['DATABASE_URL'] = 'sqlite:///' + str(Path(_temp.name) / 'test.sqlite3')
os.environ['SECRET_KEY'] = 'test-secret-do-not-use-production'
from app import app, db  # noqa: E402
from app.models import User, Course, Class, Student, Enrollment, Lesson, Attendance  # noqa: E402
from werkzeug.security import generate_password_hash  # noqa: E402
from datetime import date  # noqa: E402

@pytest.fixture()
def client():
    app.config['TESTING'] = True
    with app.app_context():
        db.drop_all()
        db.create_all()
        admin = User(name='Admin',email='admin@demo.test',password_hash=generate_password_hash('123456789'),role='admin')
        teacher = User(name='Professor',email='prof@demo.test',password_hash=generate_password_hash('123456789'),role='professor')
        db.session.add_all([admin,teacher]); db.session.flush()
        course = Course(name='Web',hours=100,min_attendance=75)
        db.session.add(course); db.session.flush()
        clazz = Class(name='WEB-A',course_id=course.id,teacher_id=teacher.id)
        db.session.add(clazz); db.session.flush()
        student = Student(name='Aluno Teste',registration='T001')
        db.session.add(student); db.session.flush()
        enrollment = Enrollment(student_id=student.id,class_id=clazz.id)
        db.session.add(enrollment); db.session.flush()
        for day,hours,status in [(1,4,'P'),(2,4,'F'),(3,2,'P')]:
            lesson = Lesson(class_id=clazz.id,held_on=date(2026,10,day),hours=hours,topic='Aula')
            db.session.add(lesson); db.session.flush()
            db.session.add(Attendance(lesson_id=lesson.id,enrollment_id=enrollment.id,status=status))
        db.session.commit()
    with app.test_client() as c:
        yield c
    with app.app_context():
        db.session.remove()
        db.drop_all()

def login(client,email):
    response=client.post('/api/auth/login',json={'email':email,'password':'123456789'})
    assert response.status_code==200

def test_report_metrics_and_period(client):
    login(client,'admin@demo.test')
    response=client.get('/api/reports/attendance')
    assert response.status_code==200
    row=response.json['rows'][0]
    assert (row['present_hours'],row['absent_hours'],row['recorded_hours'])==(6,4,10)
    assert row['attendance_percent']==60
    assert row['progress_percent']==10
    response=client.get('/api/reports/attendance?date_from=2026-10-02&date_to=2026-10-02')
    assert response.status_code==200
    row=response.json['rows'][0]
    assert row['present_hours']==0 and row['absent_hours']==4
    assert row['attendance_percent']==0 and row['taught_hours']==8

def test_report_export_and_role(client):
    login(client,'admin@demo.test')
    response=client.get('/api/reports/attendance/export')
    assert response.status_code==200
    assert response.data[:2]==b'PK'
    assert 'attachment' in response.headers['Content-Disposition']
    client.post('/api/auth/logout',headers={'X-CSRF-Token':client.get('/api/auth/me').json['csrf']})
    login(client,'prof@demo.test')
    assert client.get('/api/reports/attendance').status_code==403
    assert client.get('/api/reports/attendance/export').status_code==403

def test_invalid_dates(client):
    login(client,'admin@demo.test')
    assert client.get('/api/reports/attendance?date_from=2026-11-10&date_to=2026-11-01').status_code==400

def test_operational_export_preview_csv_xlsx(client):
    import csv
    from io import StringIO, BytesIO
    from openpyxl import load_workbook
    login(client,'admin@demo.test')
    preview = client.get('/api/exports/attendance/preview?class_id=1')
    assert preview.status_code == 200
    assert preview.json['total'] == 3
    assert [r['presenca'] for r in preview.json['rows']] == ['P','F','P']
    assert [r['horas_falta'] for r in preview.json['rows']] == [0,4,0]
    csv_result = client.get('/api/exports/attendance/download?class_id=1&format=csv')
    assert csv_result.status_code == 200
    assert csv_result.data.startswith(b'\xef\xbb\xbf')
    records = list(csv.DictReader(StringIO(csv_result.data.decode('utf-8-sig'))))
    assert len(records) == 3
    assert records[1]['presenca'] == 'F'
    xlsx_result = client.get('/api/exports/attendance/download?class_id=1&format=xlsx')
    assert xlsx_result.status_code == 200
    wb = load_workbook(BytesIO(xlsx_result.data), read_only=True)
    assert wb.sheetnames == ['Registros','Matriz','Legenda']
    assert wb['Registros']['A2'].value == 'WEB-A'
    assert wb['Matriz']['C2'].value == 'P'


def test_operational_export_validation_and_access(client):
    login(client,'admin@demo.test')
    assert client.get('/api/exports/attendance/preview').status_code == 400
    assert client.get('/api/exports/attendance/download?class_id=1&format=pdf').status_code == 400
    assert client.get('/api/exports/attendance/preview?class_id=1&date_from=2026-12-01&date_to=2026-01-01').status_code == 400
    assert client.get('/api/exports/attendance/preview?class_id=999').status_code == 404
    client.post('/api/auth/logout',headers={'X-CSRF-Token':client.get('/api/auth/me').json['csrf']})
    login(client,'prof@demo.test')
    assert client.get('/api/exports/attendance/preview?class_id=1').status_code == 403
    assert client.get('/api/exports/attendance/download?class_id=1').status_code == 403
