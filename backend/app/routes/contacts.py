"""Acompanhamento administrativo de contatos. Não confundir com ocorrência pedagógica."""
from datetime import datetime, date
from flask import request, jsonify, abort
from ..extensions import app, db
from ..models import Student, StudentContact
from ..security import current_user, require, audit

CHANNELS = {'whatsapp','telefone','email','presencial','outro'}
OUTCOMES = {'sem_resposta','respondeu','pendente','resolvido'}

def serialize_contact(item):
    return {'id':item.id,'student_id':item.student_id,'author':item.author.name,
            'contacted_at':item.contacted_at.isoformat(), 'channel':item.channel,
            'subject':item.subject,'outcome':item.outcome,'notes':item.notes,
            'next_action':item.next_action,'followup_on':item.followup_on.isoformat() if item.followup_on else None,
            'created_at':item.created_at.isoformat()}

def validate(payload, partial=False):
    result={}
    if not isinstance(payload,dict):abort(400,description='Dados inválidos')
    if not partial or 'channel' in payload:
        channel=str(payload.get('channel','')).strip().lower()
        if channel not in CHANNELS:abort(400,description='Canal inválido')
        result['channel']=channel
    if not partial or 'outcome' in payload:
        outcome=str(payload.get('outcome','')).strip().lower()
        if outcome not in OUTCOMES:abort(400,description='Resultado inválido')
        result['outcome']=outcome
    for key,maxlen in [('subject',150),('notes',4000),('next_action',400)]:
        if not partial or key in payload:
            value=str(payload.get(key) or '').strip()
            if key in ('subject','notes') and not value:abort(400,description=f'{key} é obrigatório')
            if len(value)>maxlen:abort(400,description=f'{key} excede {maxlen} caracteres')
            result[key]=value if value else None
    if not partial or 'contacted_at' in payload:
        raw=payload.get('contacted_at')
        try: result['contacted_at']=datetime.fromisoformat(raw) if raw else datetime.utcnow()
        except (ValueError,TypeError):abort(400,description='Data de contato inválida')
    if not partial or 'followup_on' in payload:
        try: result['followup_on']=date.fromisoformat(payload['followup_on']) if payload.get('followup_on') else None
        except (ValueError,TypeError):abort(400,description='Data de retorno inválida')
    return result

@app.get('/api/students/<int:sid>/contacts')
@require('admin','secretaria','coordenador')
def list_student_contacts(sid):
    if not db.session.get(Student,sid):abort(404,description='Aluno não encontrado')
    rows=(StudentContact.query.filter_by(student_id=sid)
          .order_by(StudentContact.contacted_at.desc(),StudentContact.id.desc()).limit(300).all())
    return jsonify([serialize_contact(c) for c in rows])

@app.post('/api/students/<int:sid>/contacts')
@require('admin','secretaria')
def create_student_contact(sid):
    if not db.session.get(Student,sid):abort(404,description='Aluno não encontrado')
    values=validate(request.get_json(silent=True))
    c=StudentContact(student_id=sid,author_id=current_user().id,**values)
    db.session.add(c);db.session.flush()
    audit('contact.create',f'Contato #{c.id}',entity_type='contact',entity_id=c.id,
          after={'student_id':sid,'channel':c.channel,'outcome':c.outcome})
    db.session.commit()
    return jsonify(serialize_contact(c)),201

@app.patch('/api/contacts/<int:cid>')
@require('admin','secretaria')
def update_student_contact(cid):
    c=db.session.get(StudentContact,cid)
    if not c:abort(404,description='Contato não encontrado')
    before={'channel':c.channel,'outcome':c.outcome,'followup_on':str(c.followup_on) if c.followup_on else None}
    values=validate(request.get_json(silent=True),partial=True)
    if not values:abort(400,description='Nenhuma alteração informada')
    for key,value in values.items():setattr(c,key,value)
    audit('contact.update',f'Contato #{cid}',entity_type='contact',entity_id=cid,
          before=before,after={'channel':c.channel,'outcome':c.outcome,'followup_on':str(c.followup_on) if c.followup_on else None})
    db.session.commit()
    return jsonify(serialize_contact(c))
