"""Rotas de students do EduControl."""
from ..core import *
from ..models import StudentContact

@app.get('/api/students')
@require()
def students():
    if current_user().role=='professor':
        ids=[r[0] for r in db.session.query(Enrollment.student_id).join(Class,Enrollment.class_id==Class.id).filter(Class.teacher_id==current_user().id).distinct()]
        q=Student.query.filter(Student.id.in_(ids))
    else:q=Student.query
    return jsonify([student_json(s) for s in q.order_by(Student.name)])

@app.get('/api/students/<int:sid>/academic-profile')
@require()
def student_academic_profile(sid):
    student=db.session.get(Student,sid)
    if not student: abort(404,description='Aluno não encontrado')
    if not student_visible(student): abort(403,description='Aluno não vinculado às turmas do professor')
    user=current_user()
    registrations=Enrollment.query.filter_by(student_id=sid).order_by(Enrollment.enrolled_at.desc(),Enrollment.id.desc()).all()
    if user.role=='professor':
        registrations=[e for e in registrations if e.clazz.teacher_id==user.id]
    relevant_class_ids=[e.class_id for e in registrations]
    enrollment_ids=[e.id for e in registrations]
    records=[]
    if enrollment_ids:
        joined=(db.session.query(Attendance,Lesson,Enrollment)
            .join(Lesson,Attendance.lesson_id==Lesson.id)
            .join(Enrollment,Attendance.enrollment_id==Enrollment.id)
            .filter(Attendance.enrollment_id.in_(enrollment_ids))
            .order_by(Lesson.held_on.desc(),Lesson.id.desc()).all())
        records=[dict(date=l.held_on.isoformat(),hours=l.hours,topic=l.topic,status=a.status,
                      class_name=e.clazz.name,course=e.clazz.course.name) for a,l,e in joined]
    payload=dict(student=student_json(student),
                 enrollments=[dict(**enrollment_json(e),frequency=attendance_stats(e),course_hours=e.clazz.course.hours) for e in registrations],
                 attendance=records)
    if user.role in ('admin','coordenador','professor'):
        query=Occurrence.query.filter_by(student_id=sid)
        if user.role=='professor':
            query=query.filter(Occurrence.class_id.in_(relevant_class_ids))
        payload['occurrences']=[dict(id=o.id,class_name=db.session.get(Class,o.class_id).name,
            category=o.category,description=o.description,author=o.author.name,created_at=o.created_at.isoformat())
            for o in query.order_by(Occurrence.created_at.desc()).all()]
    if user.role in ('admin','coordenador','secretaria'):
        transfers=Transfer.query.filter_by(student_id=sid).order_by(Transfer.transferred_at.desc()).all()
        payload['transfers']=[dict(id=t.id,from_class=db.session.get(Class,t.from_class_id).name,
            to_class=db.session.get(Class,t.to_class_id).name,reason=t.reason,
            transferred_at=t.transferred_at.isoformat()) for t in transfers]
    return jsonify(payload)

@app.post('/api/students')
@require('admin','secretaria')
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
@require('admin','secretaria')
def delete_student(sid):
    st=db.session.get(Student,sid)
    if not st:abort(404,description='Aluno não encontrado')
    if (Enrollment.query.filter_by(student_id=sid).first() or Occurrence.query.filter_by(student_id=sid).first() or Transfer.query.filter_by(student_id=sid).first() or StudentContact.query.filter_by(student_id=sid).first()):abort(409,description='Aluno com histórico não pode ser excluído')
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

