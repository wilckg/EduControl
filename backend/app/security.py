"""Autorização e utilitários compartilhados de API."""
from functools import wraps
from datetime import date
from flask import session, abort
from .extensions import db
from .models import User, Class, Audit

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

