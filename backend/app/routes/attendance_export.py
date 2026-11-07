"""API de exportação de chamadas — POC, formato provisório sem integração externa."""
import csv
from io import StringIO, BytesIO
from flask import request, jsonify, send_file, abort
from ..extensions import app
from ..security import require
from ..services.reports import report_params
from ..services.attendance_export import HEADERS, attendance_export_rows, create_operational_xlsx

@app.get('/api/exports/attendance/preview')
@require('admin','secretaria','coordenador')
def attendance_export_preview():
    clazz, rows = attendance_export_rows(report_params(request.args))
    return jsonify(turma=clazz.name, total=len(rows), rows=[{k:r[k] for k in HEADERS} for r in rows[:15]],
                   note='Prévia limitada a 15 registros. P/F/J são os códigos internos do EduControl.')

@app.get('/api/exports/attendance/download')
@require('admin','secretaria','coordenador')
def attendance_export_download():
    filters = report_params(request.args)
    fmt = request.args.get('format','xlsx').lower()
    if fmt not in ('csv','xlsx'): abort(400,description='Formato inválido. Use csv ou xlsx')
    clazz, rows = attendance_export_rows(filters)
    if fmt == 'xlsx':
        content = create_operational_xlsx(clazz, rows)
        mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    else:
        out = StringIO()
        writer = csv.DictWriter(out, fieldnames=HEADERS, extrasaction='ignore', lineterminator='\r\n')
        writer.writeheader()
        # Impede fórmulas ativas quando CSV é aberto em planilhas externas.
        for row in rows:
            safe = {k: ("'"+v if isinstance(v,str) and v.lstrip().startswith(('=', '+', '-', '@')) else v)
                    for k,v in row.items() if k in HEADERS}
            writer.writerow(safe)
        content = BytesIO(('\ufeff'+out.getvalue()).encode('utf-8'))
        mimetype = 'text/csv; charset=utf-8'
    return send_file(content, mimetype=mimetype, as_attachment=True,
                     download_name=f'chamadas_turma_{clazz.id}.{fmt}')
