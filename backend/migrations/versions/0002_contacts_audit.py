"""Contatos acadêmicos e campos estruturados de auditoria.

Revision ID: 0002_contacts_audit
Revises: 0001_baseline
"""
from alembic import op
import sqlalchemy as sa

revision='0002_contacts_audit'
down_revision='0001_baseline'
branch_labels=None
depends_on=None

def upgrade():
    conn=op.get_bind()
    inspector=sa.inspect(conn)
    existing={c['name'] for c in inspector.get_columns('audit')}
    for name,typ in [('entity_type',sa.String(60)),('entity_id',sa.Integer()),('before_data',sa.JSON()),('after_data',sa.JSON())]:
        if name not in existing:
            op.add_column('audit',sa.Column(name,typ,nullable=True))
    # Cria apenas os índices ausentes, inclusive para bancos migrados da POC.
    indexes={i['name'] for i in sa.inspect(conn).get_indexes('audit')}
    if 'ix_audit_entity_type' not in indexes:
        op.create_index('ix_audit_entity_type','audit',['entity_type'])
    if 'student_contact' not in sa.inspect(conn).get_table_names():
        op.create_table('student_contact',
            sa.Column('id',sa.Integer(),primary_key=True),
            sa.Column('student_id',sa.Integer(),sa.ForeignKey('student.id'),nullable=False),
            sa.Column('author_id',sa.Integer(),sa.ForeignKey('user.id'),nullable=False),
            sa.Column('contacted_at',sa.DateTime(),nullable=False),
            sa.Column('channel',sa.String(24),nullable=False),
            sa.Column('subject',sa.String(150),nullable=False),
            sa.Column('outcome',sa.String(32),nullable=False),
            sa.Column('notes',sa.Text(),nullable=False),
            sa.Column('next_action',sa.String(400)),
            sa.Column('followup_on',sa.Date()),
            sa.Column('created_at',sa.DateTime(),nullable=False),
            sa.Column('updated_at',sa.DateTime(),nullable=False))
    idx={i['name'] for i in sa.inspect(conn).get_indexes('student_contact')}
    for index,column in [('ix_student_contact_student_id','student_id'),('ix_student_contact_contacted_at','contacted_at')]:
        if index not in idx:op.create_index(index,'student_contact',[column])

def downgrade():
    raise RuntimeError('Downgrade bloqueado: contatos e trilhas de auditoria não devem ser apagados')
