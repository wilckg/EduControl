"""Baseline compatível com bancos existentes da POC.

Revision ID: 0001_baseline
Revises:
"""
from alembic import op
from sqlalchemy import inspect, text
from app.extensions import db
from app import models  # noqa: F401
revision = '0001_baseline'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    conn=op.get_bind()
    # Cria somente tabelas ausentes; preserva bancos anteriores ao Alembic.
    db.metadata.create_all(bind=conn,checkfirst=True)
    inspector=inspect(conn)
    if 'student' in inspector.get_table_names():
        columns={c['name'] for c in inspector.get_columns('student')}
        if 'school' not in columns: op.execute(text('ALTER TABLE student ADD COLUMN school VARCHAR(180)'))
        if 'photo_url' not in columns: op.execute(text('ALTER TABLE student ADD COLUMN photo_url VARCHAR(500)'))

def downgrade():
    raise RuntimeError('Downgrade da migração baseline bloqueado para preservar os dados acadêmicos')
