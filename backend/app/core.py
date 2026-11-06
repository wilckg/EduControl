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

