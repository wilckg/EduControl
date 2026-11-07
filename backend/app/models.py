"""Modelos relacionais do EduControl; migrações futuras em Alembic."""
from datetime import date, datetime
from sqlalchemy import UniqueConstraint
from .extensions import db

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

class StudentContact(db.Model):
    """Histórico administrativo de contatos com alunos ou responsáveis."""
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False, index=True)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    contacted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    channel = db.Column(db.String(24), nullable=False)
    subject = db.Column(db.String(150), nullable=False)
    outcome = db.Column(db.String(32), nullable=False)
    notes = db.Column(db.Text, nullable=False)
    next_action = db.Column(db.String(400))
    followup_on = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    student = db.relationship('Student')
    author = db.relationship('User')

class Audit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    action = db.Column(db.String(80), nullable=False)
    details = db.Column(db.String(300))
    entity_type = db.Column(db.String(60), index=True)
    entity_id = db.Column(db.Integer)
    before_data = db.Column(db.JSON)
    after_data = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

