"""Aplicação Flask modular do EduControl."""
from .core import app, db
from .routes import auth, catalog, students, attendance, operations, dashboards, reports, imports
from . import commands
