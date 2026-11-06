"""Testes estáticos de empacotamento; não substituem integração Flask/Postgres."""
from pathlib import Path
import ast

ROOT=Path(__file__).resolve().parents[1]

def test_all_backend_modules_compile():
    for f in (ROOT/'app').rglob('*.py'):
        ast.parse(f.read_text(encoding='utf-8'),filename=str(f))

def test_route_modules_present():
    expected={'auth','catalog','students','attendance','operations','dashboards'}
    actual={p.stem for p in (ROOT/'app/routes').glob('*.py')}
    assert expected <= actual

def test_cli_commands_present():
    code=(ROOT/'app/commands.py').read_text(encoding='utf-8')
    assert "'init-db'" in code and "'seed'" in code
