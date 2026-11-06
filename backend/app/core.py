"""Camada de compatibilidade temporária para as rotas existentes.

Novas funcionalidades devem importar extensions/models/security/serializers/services
sem aumentar este arquivo. A transição para imports explícitos ocorrerá por módulo.
"""
import os
import secrets
import uuid
from pathlib import Path
from datetime import date, datetime, timedelta
from functools import wraps
from flask import Flask, jsonify, request, session, abort, send_file
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text, inspect, UniqueConstraint, func
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from .extensions import app, db
from .models import *
from .security import *
from .serializers import *
from .services.frequency import attendance_stats
