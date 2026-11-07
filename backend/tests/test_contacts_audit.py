"""Contatos, segurança e auditoria: banco descartável, nunca PostgreSQL da POC."""
import os
import tempfile
from pathlib import Path
import sys
import pytest

_test_dir=tempfile.TemporaryDirectory(prefix='educontrol-tests-contacts-')
if 'app.extensions' not in sys.modules:
    os.environ['DATABASE_URL']='sqlite:///'+str(Path(_test_dir.name)/'contacts.sqlite3')
    os.environ['SECRET_KEY']='contacts-test-only'
from app import app, db  # noqa: E402
from app.models import User, Student, StudentContact, Audit  # noqa: E402
from werkzeug.security import generate_password_hash  # noqa: E402

@pytest.fixture()
def client():
    app.config['TESTING']=True
    with app.app_context():
        assert db.engine.url.get_backend_name()=='sqlite' and 'educontrol-tests-' in str(db.engine.url), 'Proteção contra exclusão de dados reais'
        db.drop_all();db.create_all()
        for role in ('admin','secretaria','coordenador','professor'):
            db.session.add(User(name=role.title(), email=f'{role}@demo.test',role=role,
                       password_hash=generate_password_hash('123456789'),active=True))
        db.session.add(Student(name='Ana Exemplo',registration='ST-100'))
        db.session.commit()
        yield app.test_client()
        db.session.remove()

def login(client,role):
    res=client.post('/api/auth/login',json={'email':f'{role}@demo.test','password':'123456789'})
    assert res.status_code==200
    return {'X-CSRF-Token':res.json['csrf']}

CONTACT={'channel':'whatsapp','subject':'Ausências', 'outcome':'sem_resposta',
         'notes':'Tentativa de contato para acompanhamento de frequência.',
         'next_action':'Retornar contato','followup_on':'2026-11-10',
         'contacted_at':'2026-11-06T12:00:00'}

def test_contact_lifecycle_and_audit(client):
    h=login(client,'secretaria')
    r=client.post('/api/students/1/contacts',headers=h,json=CONTACT)
    assert r.status_code==201,r.json
    contact_id=r.json['id']
    r=client.get('/api/students/1/contacts');assert r.status_code==200
    assert r.json[0]['outcome']=='sem_resposta'
    r=client.patch(f'/api/contacts/{contact_id}',headers=h,json={'outcome':'resolvido'})
    assert r.status_code==200 and r.json['outcome']=='resolvido'
    assert client.delete('/api/students/1',headers=h).status_code==409
    with app.app_context():
        assert StudentContact.query.count()==1
        events=Audit.query.order_by(Audit.id).all()
        assert [x.action for x in events]==['contact.create','contact.update']
        assert events[0].entity_type=='contact'
    client.post('/api/auth/logout',headers=h)
    login(client,'admin')
    result=client.get('/api/audit')
    assert result.status_code==200 and result.json['total']==2
    assert 'password' not in str(result.json)
    assert client.get('/api/audit?action=contact.create').json['total']==1
    assert client.get('/api/audit?date_from=2040-01-01').json['total']==0
    assert client.get('/api/audit?date_from=invalida').status_code==400

def test_professor_cannot_view_contacts_and_coordinator_readonly(client):
    login(client,'professor')
    assert client.get('/api/students/1/contacts').status_code==403
    h=login(client,'coordenador')
    assert client.get('/api/students/1/contacts').status_code==200
    assert client.post('/api/students/1/contacts',headers=h,json=CONTACT).status_code==403
    assert client.get('/api/audit').status_code==403

def test_contact_validation_and_csrf(client):
    h=login(client,'secretaria')
    assert client.post('/api/students/1/contacts',json=CONTACT).status_code==403
    assert client.post('/api/students/1/contacts',headers=h,json={**CONTACT,'channel':'inexistente'}).status_code==400
    assert client.post('/api/students/1/contacts',headers=h,json={**CONTACT,'notes':''}).status_code==400
    assert client.post('/api/students/999/contacts',headers=h,json=CONTACT).status_code==404
    with app.app_context():
        assert StudentContact.query.count()==0
