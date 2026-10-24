"""EduControl POC. Dados de demonstração; não utilizar em produção sem hardening."""
import os
import secrets
import uuid
from pathlib import Path
from sqlalchemy import text, inspect
from werkzeug.utils import secure_filename
from datetime import date, datetime, timedelta
from functools import wraps
from flask import Flask, jsonify, request, session, abort, send_file
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint, func
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get('SECRET_KEY', 'dev-only-change-me'),
    SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL', 'sqlite:///educontrol.db'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=os.getenv('COOKIE_SECURE', 'false').lower() == 'true',
    JSON_SORT_KEYS=False,
)
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), nullable=False)
    active = db.Column(db.Boolean, default=True, nullable=False)

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    hours = db.Column(db.Float, nullable=False)
    min_attendance = db.Column(db.Float, default=75, nullable=False)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    registration = db.Column(db.String(30), unique=True, nullable=False)
    email = db.Column(db.String(150))
    photo_url = db.Column(db.String(500))
    school = db.Column(db.String(180))

class Class(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    status = db.Column(db.String(30), default='active')
    course = db.relationship('Course')
    teacher = db.relationship('User')

class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    status = db.Column(db.String(30), default='active', nullable=False)
    enrolled_at = db.Column(db.Date, default=date.today, nullable=False)
    closed_at = db.Column(db.Date)
    student = db.relationship('Student')
    clazz = db.relationship('Class')

class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    held_on = db.Column(db.Date, nullable=False)
    hours = db.Column(db.Float, nullable=False)
    topic = db.Column(db.String(250), default='')
    clazz = db.relationship('Class')

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'), nullable=False)
    enrollment_id = db.Column(db.Integer, db.ForeignKey('enrollment.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    __table_args__ = (UniqueConstraint('lesson_id','enrollment_id',name='uq_attendance'),)

class Occurrence(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(60), nullable=False)
    description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    student = db.relationship('Student')
    author = db.relationship('User')

class Transfer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    from_class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    to_class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    reason = db.Column(db.String(500), nullable=False)
    transferred_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

class Audit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    action = db.Column(db.String(80), nullable=False)
    details = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

def audit(action, details=''):
    db.session.add(Audit(user_id=session.get('uid'), action=action, details=str(details)[:300]))

def current_user():
    return db.session.get(User, session.get('uid')) if session.get('uid') else None

def require(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            user = current_user()
            if not user or not user.active: abort(401, description='Faça login')
            if roles and user.role not in roles: abort(403, description='Sem permissão')
            return fn(*args, **kwargs)
        return wrapped
    return decorator

def can_view_class(clazz):
    user = current_user()
    return bool(user and (user.role != 'professor' or clazz.teacher_id == user.id))

def accessible_class(class_id):
    clazz = db.session.get(Class, class_id)
    if not clazz: abort(404, description='Turma não encontrada')
    if not can_view_class(clazz): abort(403, description='Turma não atribuída a este professor')
    return clazz

def parse_id(obj, key):
    try: return int(obj[key])
    except (KeyError, ValueError, TypeError): abort(400, description=f'{key} inválido')

def positive_hours(v):
    try: value = float(v)
    except (ValueError, TypeError): abort(400, description='Horas inválidas')
    if not 0 < value <= 24: abort(400, description='Horas devem estar entre 0 e 24')
    return value

def as_date(v):
    try: return date.fromisoformat(v)
    except (ValueError, TypeError): abort(400, description='Data inválida (AAAA-MM-DD)')

def user_json(u): return dict(id=u.id,name=u.name,email=u.email,role=u.role,active=u.active)
def course_json(c): return dict(id=c.id,name=c.name,hours=c.hours,min_attendance=c.min_attendance)
def student_json(s): return dict(id=s.id,name=s.name,registration=s.registration,email=s.email,photo_url=(f"/api/students/{s.id}/photo" if s.photo_url else None),school=s.school)
def class_json(c):
    return dict(id=c.id,name=c.name,course_id=c.course_id,course=c.course.name,hours=c.course.hours,min_attendance=c.course.min_attendance,teacher_id=c.teacher_id,teacher=c.teacher.name if c.teacher else 'Não definido',status=c.status,start_date=c.start_date.isoformat() if c.start_date else None,end_date=c.end_date.isoformat() if c.end_date else None,students=Enrollment.query.filter_by(class_id=c.id,status='active').count())
def lesson_json(l): return dict(id=l.id,class_id=l.class_id,held_on=l.held_on.isoformat(),hours=l.hours,topic=l.topic)
def enrollment_json(e):
    return dict(id=e.id,student=student_json(e.student),class_id=e.class_id,class_name=e.clazz.name,course=e.clazz.course.name,status=e.status,enrolled_at=e.enrolled_at.isoformat(),closed_at=e.closed_at.isoformat() if e.closed_at else None)

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

@app.get('/api/courses')
@require()
def courses(): return jsonify([course_json(c) for c in Course.query.order_by(Course.name)])

@app.post('/api/courses')
@require('admin','coordenador')
def create_course():
    d=request.get_json(silent=True) or {}; name=str(d.get('name','')).strip()
    if not name: abort(400,description='Nome obrigatório')
    try: hours=float(d.get('hours')); min_a=float(d.get('min_attendance',75))
    except (TypeError,ValueError): abort(400,description='Carga horária ou frequência inválida')
    if hours<=0 or not 0<min_a<=100: abort(400,description='Parâmetros fora do intervalo')
    c=Course(name=name,hours=hours,min_attendance=min_a); db.session.add(c);audit('course.create',name);db.session.commit()
    return jsonify(course_json(c)),201

@app.patch('/api/courses/<int:cid>')
@require('admin','coordenador')
def update_course(cid):
    c=db.session.get(Course,cid)
    if not c: abort(404,description='Curso não encontrado')
    d=request.get_json(silent=True) or {}
    name=str(d.get('name',c.name)).strip()
    try: hrs=float(d.get('hours',c.hours)); minimum=float(d.get('min_attendance',c.min_attendance))
    except (ValueError,TypeError): abort(400,description='Valores inválidos')
    if not name or hrs<=0 or not 0<minimum<=100: abort(400,description='Dados inválidos')
    c.name=name;c.hours=hrs;c.min_attendance=minimum
    audit('course.update',cid);db.session.commit();return jsonify(course_json(c))

@app.delete('/api/courses/<int:cid>')
@require('admin','coordenador')
def delete_course(cid):
    c=db.session.get(Course,cid)
    if not c: abort(404,description='Curso não encontrado')
    if Class.query.filter_by(course_id=cid).first(): abort(409,description='Curso possui turmas. Não é possível excluir.')
    db.session.delete(c);audit('course.delete',cid);db.session.commit();return jsonify(ok=True)

@app.get('/api/classes')
@require()
def classes():
    q=Class.query.order_by(Class.id)
    if current_user().role=='professor': q=q.filter_by(teacher_id=current_user().id)
    return jsonify([class_json(c) for c in q.all()])

@app.post('/api/classes')
@require('admin','coordenador','secretaria')
def create_class():
    d=request.get_json(silent=True) or {}; name=str(d.get('name','')).strip(); course=db.session.get(Course,parse_id(d,'course_id'))
    if not name or not course: abort(400,description='Nome e curso válidos obrigatórios')
    teacher_id=int(d['teacher_id']) if d.get('teacher_id') else None
    if teacher_id and (not db.session.get(User,teacher_id) or db.session.get(User,teacher_id).role!='professor'):abort(400,description='Professor inválido')
    c=Class(name=name,course_id=course.id,teacher_id=teacher_id,start_date=as_date(d['start_date']) if d.get('start_date') else None,end_date=as_date(d['end_date']) if d.get('end_date') else None)
    db.session.add(c);audit('class.create',name);db.session.commit();return jsonify(class_json(c)),201

@app.patch('/api/classes/<int:cid>')
@require('admin','coordenador','secretaria')
def update_class(cid):
    c=db.session.get(Class,cid)
    if not c: abort(404,description='Turma não encontrada')
    d=request.get_json(silent=True) or {}
    if 'name' in d:
        c.name=str(d['name']).strip()
        if not c.name:abort(400,description='Código da turma obrigatório')
    if 'course_id' in d:
        new_course=db.session.get(Course,parse_id(d,'course_id'))
        if not new_course:abort(404,description='Curso não encontrado')
        if new_course.id!=c.course_id and (Enrollment.query.filter_by(class_id=cid).first() or Lesson.query.filter_by(class_id=cid).first()):abort(409,description='Não altere o curso de uma turma com histórico')
        c.course_id=new_course.id
    if 'teacher_id' in d:
        tid=int(d['teacher_id']) if d['teacher_id'] else None
        if tid and (not db.session.get(User,tid) or db.session.get(User,tid).role!='professor'):abort(400,description='Professor inválido')
        c.teacher_id=tid
    for key in ('start_date','end_date'):
        if key in d:setattr(c,key,as_date(d[key]) if d[key] else None)
    if c.start_date and c.end_date and c.end_date<c.start_date:abort(400,description='Período inválido')
    audit('class.update',cid);db.session.commit();return jsonify(class_json(c))

@app.delete('/api/classes/<int:cid>')
@require('admin','coordenador','secretaria')
def delete_class(cid):
    c=db.session.get(Class,cid)
    if not c: abort(404,description='Turma não encontrada')
    if (Enrollment.query.filter_by(class_id=cid).first() or Lesson.query.filter_by(class_id=cid).first() or Occurrence.query.filter_by(class_id=cid).first() or Transfer.query.filter((Transfer.from_class_id==cid)|(Transfer.to_class_id==cid)).first()):abort(409,description='Turma com histórico não pode ser excluída; preserve matrículas, aulas e ocorrências')
    db.session.delete(c);audit('class.delete',cid);db.session.commit();return jsonify(ok=True)

@app.get('/api/students')
@require()
def students():
    if current_user().role=='professor':
        ids=[r[0] for r in db.session.query(Enrollment.student_id).join(Class,Enrollment.class_id==Class.id).filter(Class.teacher_id==current_user().id).distinct()]
        q=Student.query.filter(Student.id.in_(ids))
    else:q=Student.query
    return jsonify([student_json(s) for s in q.order_by(Student.name)])

@app.post('/api/students')
@require('admin','coordenador','secretaria')
def create_student():
    d=request.get_json(silent=True) or {};name=str(d.get('name','')).strip();reg=str(d.get('registration','')).strip()
    if not name or not reg:abort(400,description='Nome e matrícula obrigatórios')
    if Student.query.filter_by(registration=reg).first():abort(400,description='Matrícula já existe')
    s=Student(name=name,registration=reg,email=d.get('email') or None,school=str(d.get('school','')).strip()[:180] or None);db.session.add(s);audit('student.create',reg);db.session.commit();return jsonify(student_json(s)),201

@app.patch('/api/students/<int:sid>')
@require('admin','coordenador','secretaria')
def update_student(sid):
    st=db.session.get(Student,sid)
    if not st:abort(404,description='Aluno não encontrado')
    d=request.get_json(silent=True) or {}
    if 'name' in d:
        st.name=str(d['name']).strip()
        if not st.name:abort(400,description='Nome obrigatório')
    if 'registration' in d:
        reg=str(d['registration']).strip()
        if not reg:abort(400,description='Matrícula obrigatória')
        duplicate=Student.query.filter_by(registration=reg).first()
        if duplicate and duplicate.id!=sid:abort(409,description='Matrícula já existe')
        st.registration=reg
    if 'email' in d:st.email=str(d['email']).strip() or None
    if 'school' in d:st.school=str(d['school']).strip()[:180] or None
    audit('student.update',sid);db.session.commit();return jsonify(student_json(st))

@app.delete('/api/students/<int:sid>')
@require('admin','coordenador','secretaria')
def delete_student(sid):
    st=db.session.get(Student,sid)
    if not st:abort(404,description='Aluno não encontrado')
    if (Enrollment.query.filter_by(student_id=sid).first() or Occurrence.query.filter_by(student_id=sid).first() or Transfer.query.filter_by(student_id=sid).first()):abort(409,description='Aluno com histórico não pode ser excluído')
    db.session.delete(st);audit('student.delete',sid);db.session.commit();return jsonify(ok=True)


# Fotos privadas: fora de /static, servidas somente após autorização.
PHOTO_DIR=Path(os.environ.get('PHOTO_DIR','/app/student_photos'))
PHOTO_LIMIT=3*1024*1024
PHOTO_TYPES={'image/jpeg':'.jpg','image/png':'.png','image/webp':'.webp'}

def student_visible(st):
    u=current_user()
    if u.role!='professor':return True
    return db.session.query(Enrollment.id).join(Class,Enrollment.class_id==Class.id).filter(Enrollment.student_id==st.id,Class.teacher_id==u.id).first() is not None

@app.post('/api/students/<int:sid>/photo')
@require('admin','coordenador','secretaria')
def upload_student_photo(sid):
    st=db.session.get(Student,sid)
    if not st:abort(404,description='Aluno não encontrado')
    f=request.files.get('photo')
    if not f:abort(400,description='Envie o campo photo com uma imagem')
    raw=f.read(PHOTO_LIMIT+1)
    if not raw or len(raw)>PHOTO_LIMIT:abort(413,description='Foto deve ter no máximo 3 MB')
    # Assinatura binária mínima; não confiar em extensão ou MIME enviado.
    if raw.startswith(bytes.fromhex('ffd8ff')):ext='.jpg'
    elif raw.startswith(b'\x89PNG\r\n\x1a\n'):ext='.png'
    elif raw.startswith(b'RIFF') and raw[8:12]==b'WEBP':ext='.webp'
    else:abort(415,description='Use JPG, PNG ou WebP')
    PHOTO_DIR.mkdir(parents=True,exist_ok=True)
    filename=f'{uuid.uuid4().hex}{ext}'
    path=PHOTO_DIR/filename
    path.write_bytes(raw)
    old=st.photo_url
    st.photo_url=filename
    audit('student.photo.update',str(sid));db.session.commit()
    if old and (PHOTO_DIR/Path(old).name).is_file():(PHOTO_DIR/Path(old).name).unlink()
    return jsonify(student_json(st))

@app.get('/api/students/<int:sid>/photo')
@require()
def read_student_photo(sid):
    st=db.session.get(Student,sid)
    if not st or not st.photo_url:abort(404)
    if not student_visible(st):abort(403)
    path=PHOTO_DIR/Path(st.photo_url).name
    if not path.is_file():abort(404)
    resp=send_file(path,mimetype={'.jpg':'image/jpeg','.png':'image/png','.webp':'image/webp'}[path.suffix])
    resp.headers['Cache-Control']='private, no-store'
    resp.headers['X-Content-Type-Options']='nosniff'
    return resp

@app.delete('/api/students/<int:sid>/photo')
@require('admin','coordenador','secretaria')
def delete_student_photo(sid):
    st=db.session.get(Student,sid)
    if not st:abort(404)
    old=st.photo_url;st.photo_url=None
    audit('student.photo.delete',str(sid));db.session.commit()
    if old and (PHOTO_DIR/Path(old).name).is_file():(PHOTO_DIR/Path(old).name).unlink()
    return jsonify(student_json(st))

@app.get('/api/enrollments')
@require()
def enrollments():
    q=Enrollment.query.order_by(Enrollment.id)
    if current_user().role=='professor':q=q.join(Class,Enrollment.class_id==Class.id).filter(Class.teacher_id==current_user().id)
    return jsonify([enrollment_json(e) for e in q.all()])

@app.post('/api/enrollments')
@require('admin','coordenador','secretaria')
def enroll():
    d=request.get_json(silent=True) or {}; sid=parse_id(d,'student_id');cid=parse_id(d,'class_id')
    if not db.session.get(Student,sid) or not db.session.get(Class,cid):abort(404,description='Aluno ou turma não encontrado')
    if Enrollment.query.filter_by(student_id=sid,class_id=cid,status='active').first():abort(400,description='Aluno já matriculado')
    e=Enrollment(student_id=sid,class_id=cid);db.session.add(e);audit('enrollment.create',f'{sid}/{cid}');db.session.commit();return jsonify(enrollment_json(e)),201

@app.get('/api/classes/<int:class_id>/lessons')
@require()
def lessons(class_id):
    accessible_class(class_id)
    return jsonify([lesson_json(l) for l in Lesson.query.filter_by(class_id=class_id).order_by(Lesson.held_on.desc(),Lesson.id.desc())])

@app.post('/api/lessons')
@require('admin','coordenador','professor')
def create_lesson():
    d=request.get_json(silent=True) or {};cid=parse_id(d,'class_id');accessible_class(cid)
    l=Lesson(class_id=cid,held_on=as_date(d.get('held_on')),hours=positive_hours(d.get('hours')),topic=str(d.get('topic',''))[:250]);db.session.add(l);db.session.flush()
    for e in Enrollment.query.filter_by(class_id=cid,status='active'):
        db.session.add(Attendance(lesson_id=l.id,enrollment_id=e.id,status='P'))
    audit('lesson.create',str(l.id));db.session.commit();return jsonify(lesson_json(l)),201

@app.get('/api/lessons/<int:lesson_id>/attendance')
@require()
def lesson_attendance(lesson_id):
    lesson=db.session.get(Lesson,lesson_id)
    if not lesson:abort(404)
    accessible_class(lesson.class_id)
    rows=db.session.query(Attendance,Enrollment,Student).join(Enrollment,Attendance.enrollment_id==Enrollment.id).join(Student,Enrollment.student_id==Student.id).filter(Attendance.lesson_id==lesson_id).order_by(Student.name).all()
    return jsonify(dict(lesson=lesson_json(lesson),records=[dict(id=a.id,enrollment_id=e.id,student=student_json(s),status=a.status) for a,e,s in rows]))

@app.put('/api/lessons/<int:lesson_id>/attendance')
@require('admin','coordenador','professor')
def save_attendance(lesson_id):
    l=db.session.get(Lesson,lesson_id)
    if not l:abort(404)
    accessible_class(l.class_id)
    d=request.get_json(silent=True) or {};items=d.get('records')
    if not isinstance(items,list):abort(400,description='records deve ser lista')
    allowed={a.enrollment_id:a for a in Attendance.query.filter_by(lesson_id=lesson_id)}
    for item in items:
        eid=parse_id(item,'enrollment_id');status=item.get('status')
        if eid not in allowed or status not in ('P','F','J'):abort(400,description='Registro ou status inválido')
        allowed[eid].status=status
    audit('attendance.update',str(lesson_id));db.session.commit();return jsonify(ok=True)

@app.get('/api/alerts')
@require('admin','coordenador','secretaria')
def alerts():
    q=Enrollment.query.filter_by(status='active')
    result=[]
    for e in q.all():
        s=attendance_stats(e)
        if s['severity']!='ok':result.append(dict(enrollment_id=e.id,student=student_json(e.student),class_name=e.clazz.name,**s))
    return jsonify(sorted(result,key=lambda x:({'exceeded':0,'critical':1,'warning':2}.get(x['severity'],3),x['remaining_absent_hours'])))

@app.get('/api/enrollments/<int:eid>/frequency')
@require()
def frequency(eid):
    e=db.session.get(Enrollment,eid)
    if not e:abort(404)
    accessible_class(e.class_id)
    return jsonify(dict(enrollment=enrollment_json(e),**attendance_stats(e)))

@app.get('/api/occurrences')
@require('admin','coordenador','professor')
def occurrences():
    q=Occurrence.query.order_by(Occurrence.created_at.desc())
    if current_user().role=='professor':q=q.join(Class,Occurrence.class_id==Class.id).filter(Class.teacher_id==current_user().id)
    return jsonify([dict(id=o.id,student=student_json(o.student),class_id=o.class_id,category=o.category,description=o.description,author=o.author.name,created_at=o.created_at.isoformat()) for o in q.limit(100)])

@app.post('/api/occurrences')
@require('admin','coordenador','professor')
def create_occurrence():
    d=request.get_json(silent=True) or {};sid=parse_id(d,'student_id');cid=parse_id(d,'class_id');accessible_class(cid)
    if not Enrollment.query.filter_by(student_id=sid,class_id=cid).first():abort(400,description='Aluno não pertence ao histórico desta turma')
    category=str(d.get('category','')).strip();description=str(d.get('description','')).strip()
    if not category or len(description)<5:abort(400,description='Categoria e descrição de pelo menos 5 caracteres são obrigatórias')
    o=Occurrence(student_id=sid,class_id=cid,author_id=current_user().id,category=category[:60],description=description);db.session.add(o);audit('occurrence.create',str(sid));db.session.commit();return jsonify(id=o.id),201

@app.get('/api/transfers')
@require('admin','coordenador','secretaria')
def transfers():
    return jsonify([dict(id=t.id,student=student_json(db.session.get(Student,t.student_id)),from_class=db.session.get(Class,t.from_class_id).name,to_class=db.session.get(Class,t.to_class_id).name,reason=t.reason,transferred_at=t.transferred_at.isoformat()) for t in Transfer.query.order_by(Transfer.id.desc()).limit(100)])

@app.post('/api/transfers')
@require('admin','coordenador','secretaria')
def create_transfer():
    d=request.get_json(silent=True) or {};eid=parse_id(d,'enrollment_id');cid=parse_id(d,'to_class_id')
    e=db.session.get(Enrollment,eid);dest=db.session.get(Class,cid);reason=str(d.get('reason','')).strip()
    if not e or not dest:abort(404,description='Matrícula ou turma não encontrada')
    if e.status!='active' or e.class_id==cid or not reason:abort(400,description='Transferência inválida ou motivo ausente')
    if e.clazz.course_id!=dest.course_id:abort(400,description='A POC permite transferências apenas entre turmas do mesmo curso')
    if Enrollment.query.filter_by(student_id=e.student_id,class_id=cid,status='active').first():abort(400,description='Aluno já matriculado no destino')
    e.status='transferred';e.closed_at=date.today()
    db.session.add(Enrollment(student_id=e.student_id,class_id=cid,enrolled_at=date.today()))
    db.session.add(Transfer(student_id=e.student_id,from_class_id=e.class_id,to_class_id=cid,reason=reason))
    audit('transfer.create',f'{e.student_id} {e.class_id}->{cid}');db.session.commit();return jsonify(ok=True),201

@app.get('/api/teachers')
@require('admin','coordenador','secretaria')
def teacher_options():
    # Somente dados mínimos necessários para selecionar o responsável da turma.
    return jsonify([{'id':u.id,'name':u.name,'role':u.role} for u in User.query.filter_by(role='professor',active=True).order_by(User.name).all()])

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

@app.cli.command('init-db')
def init_db():
    db.create_all()
    cols={c['name'] for c in inspect(db.engine).get_columns('student')}
    if 'school' not in cols:
        db.session.execute(text('ALTER TABLE student ADD COLUMN school VARCHAR(180)'));db.session.commit()
    print('Tabelas atualizadas. Para popular execute: flask --app app seed')

@app.cli.command('seed')
def seed():
    db.create_all()
    cols={c['name'] for c in inspect(db.engine).get_columns('student')}
    if 'school' not in cols:
        db.session.execute(text('ALTER TABLE student ADD COLUMN school VARCHAR(180)'));db.session.commit()
    if User.query.first():print('Banco já contém usuários; seed ignorado');return
    users=[('Admin Demo','admin@educontrol.local','admin'),('Coordenação Demo','coordenador@educontrol.local','coordenador'),('Professor Demo','professor@educontrol.local','professor'),('Secretaria Demo','secretaria@educontrol.local','secretaria')]
    password=os.getenv('DEMO_PASSWORD','Demo@12345')
    for name,email,role in users:db.session.add(User(name=name,email=email,role=role,password_hash=generate_password_hash(password)))
    db.session.flush();prof=User.query.filter_by(role='professor').first()
    c1=Course(name='Desenvolvimento Web',hours=100,min_attendance=75);c2=Course(name='Python para Ciência de Dados',hours=80,min_attendance=75)
    db.session.add_all([c1,c2]);db.session.flush()
    classes=[Class(name='WEB-2026-A',course_id=c1.id,teacher_id=prof.id,start_date=date(2026,9,1),end_date=date(2026,12,15)),Class(name='WEB-2026-B',course_id=c1.id,teacher_id=prof.id,start_date=date(2026,9,1),end_date=date(2026,12,15)),Class(name='PY-2026-A',course_id=c2.id,teacher_id=prof.id,start_date=date(2026,9,1),end_date=date(2026,12,15))]
    db.session.add_all(classes);db.session.flush()
    names=['Ana Souza','Bruno Lima','Camila Oliveira','Lucas Martins','Mariana Costa','Rafael Pereira','Julia Santos','Pedro Almeida','Beatriz Rocha','Gabriel Ferreira','Sofia Ribeiro','Daniel Carvalho']
    for i,name in enumerate(names):
        s=Student(name=name,registration=f'EDU{i+1:05d}',email=f'aluno{i+1}@exemplo.local');db.session.add(s);db.session.flush()
        db.session.add(Enrollment(student_id=s.id,class_id=classes[0 if i<8 else 2].id));
    db.session.commit()
    for clazz in [classes[0],classes[2]]:
        for d in range(6):
            l=Lesson(class_id=clazz.id,held_on=date(2026,10,1)+timedelta(days=d*3),hours=4,topic=f'Aula prática {d+1}');db.session.add(l);db.session.flush()
            for e in Enrollment.query.filter_by(class_id=clazz.id,status='active'):
                # Perfis de risco exemplares com curso de 100h: 20h ou 16h de ausências
                absence=(e.student.name=='Ana Souza' and d<5) or (e.student.name=='Lucas Martins' and d<4) or (e.student.name=='Sofia Ribeiro' and d<3)
                db.session.add(Attendance(lesson_id=l.id,enrollment_id=e.id,status='F' if absence else 'P'))
    db.session.add(Occurrence(student_id=1,class_id=classes[0].id,author_id=prof.id,category='Acompanhamento',description='Aluno necessita de orientação sobre atividades pendentes.'))
    db.session.commit();print(f'Seed concluído. Usuários: {[u[1] for u in users]} / senha: definida em DEMO_PASSWORD')

if __name__=='__main__':app.run(host='0.0.0.0',port=5000,debug=os.getenv('FLASK_DEBUG')=='1')
