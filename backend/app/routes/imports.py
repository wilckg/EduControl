"""Endpoints de importação: mesma validação no preview e no commit."""
import json
from flask import request, jsonify, abort
from ..extensions import app, db
from ..security import require, audit
from ..services.imports import read_sheet, guess_mapping, make_plan, commit_plan

@app.post('/api/imports/students/preview')
@app.post('/api/imports/students/commit')
@require('admin','secretaria')
def import_students():
    upload = request.files.get('file')
    if upload is None: abort(400, description='Selecione uma planilha')
    try:
        headers, entries=read_sheet(upload.filename or '', upload.read(3*1024*1024+1))
        raw=request.form.get('mapping')
        mapping=json.loads(raw) if raw else guess_mapping(headers)
        if not isinstance(mapping,dict): raise ValueError('Mapeamento de colunas inválido')
        class_id_raw=request.form.get('default_class_id')
        default_class_id=int(class_id_raw) if class_id_raw else None
        plan=make_plan(headers,entries,mapping,default_class_id)
        if request.path.endswith('/preview'):return jsonify(plan)
        if not plan['can_commit']:
            return jsonify(error='Existem linhas inválidas. Revise a importação.',preview=plan),422
        result=commit_plan(plan)
        audit('students.bulk_import',f"criados={result['students_created']}; matriculados={result['enrollments_created']}; ignorados={result['skipped']}")
        db.session.commit()
        return jsonify(ok=True,**result),201
    except (ValueError,TypeError,KeyError,json.JSONDecodeError) as error:
        db.session.rollback()
        return jsonify(error=str(error)),400
