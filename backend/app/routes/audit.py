"""Consulta de auditoria: somente administrador; saída limitada e sem segredos."""
from flask import request, jsonify, abort
from datetime import datetime, timedelta
from ..extensions import app, db
from ..models import Audit, User
from ..security import require

@app.get('/api/audit')
@require('admin')
def audit_list():
    q=Audit.query
    action=request.args.get('action','').strip()
    if action:q=q.filter(Audit.action.ilike('%'+action[:80]+'%'))
    actor=request.args.get('user_id',type=int)
    if actor:q=q.filter(Audit.user_id==actor)
    entity=request.args.get('entity_type','').strip()
    if entity:q=q.filter(Audit.entity_type==entity[:60])
    for key,comparator in [('date_from','from'),('date_to','to')]:
        value=request.args.get(key,'').strip()
        if value:
            try:day=datetime.strptime(value,'%Y-%m-%d')
            except ValueError:abort(400,description='Formato de data inválido')
            q=q.filter(Audit.created_at>=day if comparator=='from' else Audit.created_at<day+timedelta(days=1))
    try:
        page=max(1,int(request.args.get('page',1)))
    except (ValueError,TypeError):abort(400,description='Página inválida')
    if page>10000:abort(400,description='Página inválida')
    total=q.count()
    users={u.id:u.name for u in User.query.all()}
    events=q.order_by(Audit.created_at.desc(),Audit.id.desc()).offset((page-1)*30).limit(30).all()
    return jsonify(total=total,page=page,page_size=30,rows=[{
        'id':a.id,'actor':users.get(a.user_id,'Usuário removido'), 'user_id':a.user_id,
        'action':a.action,'details':a.details,'entity_type':a.entity_type,
        'entity_id':a.entity_id,'created_at':a.created_at.isoformat() if a.created_at else None,
        # O detalhe antes/depois é restrito a metadados não sensíveis definidos por serviço.
        'before_data':a.before_data,'after_data':a.after_data} for a in events])
