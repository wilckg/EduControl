"""Testes da importação em lote; executar com pytest no container backend."""
import io
import json
import os
import tempfile
from pathlib import Path
import pytest

# Guard rail: never run destructive test setup against the Docker PostgreSQL.
_test_home=tempfile.TemporaryDirectory(prefix='educontrol-tests-import-')
if 'app.extensions' not in __import__('sys').modules:
    os.environ['DATABASE_URL']='sqlite:///'+str(Path(_test_home.name)/'imports.sqlite3')
    os.environ['SECRET_KEY']='import-test-only'

from werkzeug.security import generate_password_hash

@pytest.fixture()
def client(tmp_path):
    from app.extensions import app, db
    from app.models import User, Course, Class
    app.config['TESTING']=True
    # Importantly, config changes after SQLAlchemy init DO NOT update its engine.
    with app.app_context():
        assert 'sqlite' in str(db.engine.url) and 'educontrol-tests-' in str(db.engine.url), 'Recusando apagar banco não isolado'
        db.drop_all()
        db.create_all()
        admin=User(name='Admin', email='admin@teste.local', password_hash=generate_password_hash('pass12345'),role='admin',active=True)
        teacher=User(name='Professor',email='prof@teste.local',password_hash=generate_password_hash('pass12345'),role='professor',active=True)
        db.session.add_all([admin,teacher]);db.session.flush()
        course=Course(name='Web',hours=40,min_attendance=75);db.session.add(course);db.session.flush()
        db.session.add(Class(name='WEB-A',course_id=course.id));db.session.commit()
        yield app.test_client()
        db.session.remove()

def login(client,email='admin@teste.local'):
    res=client.post('/api/auth/login',json={'email':email,'password':'pass12345'})
    assert res.status_code==200
    return {'X-CSRF-Token':res.json['csrf']}

def csv_upload():
    return {'file':(io.BytesIO('Nome;Matrícula;Colégio;Turma\nAna Souza;EDU9001;Escola Exemplo;WEB-A\nBruno Lima;EDU9002;Colégio A;WEB-A\n'.encode()),'alunos.csv')}

def test_preview_then_commit_then_idempotent(client):
    headers=login(client)
    before=client.get('/api/students').json
    resp=client.post('/api/imports/students/preview',data=csv_upload(),headers=headers)
    assert resp.status_code==200,resp.json
    assert resp.json['counts']['create']==2
    assert resp.json['can_commit']
    assert len(client.get('/api/students').json)==len(before)
    resp=client.post('/api/imports/students/commit',data=csv_upload(),headers=headers)
    assert resp.status_code==201,resp.json
    assert resp.json['students_created']==2
    assert resp.json['enrollments_created']==2
    second=client.post('/api/imports/students/commit',data=csv_upload(),headers=headers)
    assert second.status_code==201
    assert second.json['skipped']==2

def test_duplicate_lines_rejected_without_partial_writes(client):
    headers=login(client)
    contents='Nome,Matrícula,Turma\nAna Souza,X1,WEB-A\nOutra pessoa,X1,WEB-A\n'
    payload=lambda:{'file':(io.BytesIO(contents.encode()),'duplicado.csv')}
    resp=client.post('/api/imports/students/preview',data=payload(),headers=headers)
    assert resp.status_code==200
    assert resp.json['counts']['error']==1
    result=client.post('/api/imports/students/commit',data=payload(),headers=headers)
    assert result.status_code==422
    assert client.get('/api/students').json==[]

def test_teacher_cannot_import(client):
    headers=login(client,'prof@teste.local')
    resp=client.post('/api/imports/students/preview',data=csv_upload(),headers=headers)
    assert resp.status_code==403

def test_xlsx_preview(client):
    from openpyxl import Workbook
    wb=Workbook();ws=wb.active;ws.append(['Nome','Matrícula','Turma']);ws.append(['Alice','A01','WEB-A'])
    output=io.BytesIO();wb.save(output);output.seek(0)
    headers=login(client)
    resp=client.post('/api/imports/students/preview',data={'file':(output,'alunos.xlsx')},headers=headers)
    assert resp.status_code==200
    assert resp.json['counts']['create']==1
