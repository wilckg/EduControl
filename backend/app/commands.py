"""Comandos Flask para preparar e popular banco de demonstração."""
from .core import *

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

