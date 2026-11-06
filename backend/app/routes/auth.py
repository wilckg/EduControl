"""Rotas de auth do EduControl."""
from ..core import *

@app.errorhandler(400)
@app.errorhandler(401)
@app.errorhandler(403)
@app.errorhandler(404)
def http_error(err): return jsonify(error=err.description),err.code

@app.before_request
def csrf_guard():
    if request.method in ('POST','PUT','PATCH','DELETE') and request.path != '/api/auth/login':
        if not session.get('csrf') or not secrets.compare_digest(request.headers.get('X-CSRF-Token',''),session['csrf']):
            return jsonify(error='Token CSRF ausente ou inválido'),403

@app.post('/api/auth/login')
def login():
    data = request.get_json(silent=True) or {}
    email = str(data.get('email','')).strip().lower()
    u = User.query.filter_by(email=email,active=True).first()
    if not u or not check_password_hash(u.password_hash,str(data.get('password',''))):
        return jsonify(error='Credenciais inválidas'),401
    session.clear(); session['uid']=u.id; session['csrf']=secrets.token_urlsafe(32)
    return jsonify(user=user_json(u),csrf=session['csrf'])

@app.post('/api/auth/logout')
@require()
def logout(): session.clear(); return jsonify(ok=True)

@app.get('/api/auth/me')
@require()
def me(): return jsonify(user=user_json(current_user()),csrf=session['csrf'])

@app.get('/api/users')
@require('admin','coordenador')
def users(): return jsonify([user_json(u) for u in User.query.order_by(User.name)])

@app.post('/api/users')
@require('admin')
def create_user():
    d=request.get_json(silent=True) or {}
    name=str(d.get('name','')).strip(); email=str(d.get('email','')).strip().lower()
    password=str(d.get('password','')); role=str(d.get('role',''))
    if not name or '@' not in email or len(password)<8 or role not in ('admin','coordenador','professor','secretaria'):
        abort(400,description='Informe nome, e-mail, perfil válido e senha com 8 caracteres ou mais')
    if User.query.filter_by(email=email).first():abort(409,description='E-mail já cadastrado')
    u=User(name=name,email=email,password_hash=generate_password_hash(password),role=role,active=True)
    db.session.add(u);audit('user.create',email);db.session.commit()
    return jsonify(user_json(u)),201

@app.patch('/api/users/<int:uid>')
@require('admin')
def update_user(uid):
    u=db.session.get(User,uid)
    if not u:abort(404,description='Usuário não encontrado')
    d=request.get_json(silent=True) or {}
    if 'name' in d:
        u.name=str(d['name']).strip()
        if not u.name:abort(400,description='Nome obrigatório')
    if 'email' in d:
        email=str(d['email']).strip().lower()
        if '@' not in email:abort(400,description='E-mail inválido')
        other=User.query.filter_by(email=email).first()
        if other and other.id!=u.id:abort(409,description='E-mail já utilizado')
        u.email=email
    if 'role' in d:
        if d['role'] not in ('admin','coordenador','professor','secretaria'):abort(400,description='Perfil inválido')
        if u.id==current_user().id and d['role']!='admin':abort(400,description='Você não pode retirar seu próprio perfil de administrador')
        u.role=d['role']
    if 'active' in d:
        if not isinstance(d['active'],bool):abort(400,description='Status inválido')
        if u.id==current_user().id and not d['active']:abort(400,description='Você não pode desativar sua própria conta')
        u.active=d['active']
    if 'password' in d and d['password']:
        if len(str(d['password']))<8:abort(400,description='Senha deve ter 8 caracteres ou mais')
        u.password_hash=generate_password_hash(str(d['password']))
    audit('user.update',str(uid));db.session.commit()
    return jsonify(user_json(u))

