"""Endpoints de relatórios; disponíveis para Administração, Secretaria e Coordenação."""
from io import BytesIO
from flask import request, jsonify, send_file
from ..extensions import app
from ..security import require
from ..services.reports import report_params, attendance_report

@app.get('/api/reports/attendance')
@require('admin', 'secretaria', 'coordenador')
def reports_attendance():
    return jsonify(attendance_report(report_params(request.args)))

@app.get('/api/reports/attendance/export')
@require('admin', 'secretaria', 'coordenador')
def reports_attendance_export():
    import xlsxwriter
    report = attendance_report(report_params(request.args))
    buffer = BytesIO()
    workbook = xlsxwriter.Workbook(buffer, {'in_memory': True, 'strings_to_formulas': False, 'strings_to_urls': False})
    sheet = workbook.add_worksheet('Frequência')
    title = workbook.add_format({'bold': True, 'font_size': 16, 'font_color': '#0D3B78'})
    subtitle = workbook.add_format({'font_color': '#5B6473', 'text_wrap': True})
    header = workbook.add_format({'bold': True, 'font_color': '#FFFFFF', 'bg_color': '#0D3B78', 'border': 0})
    num = workbook.add_format({'num_format': '0.0'})
    percent = workbook.add_format({'num_format': '0.0"%"'})
    sheet.merge_range('A1:K1', 'EduControl • Relatório acadêmico de frequência', title)
    sheet.merge_range('A2:K2', 'Dados por matrícula. Filtros aplicados ao período selecionado.', subtitle)
    columns = ['Aluno','Matrícula','Turma','Curso','Horas presentes','Horas de falta',
               'Frequência (%)','Horas ministradas','Progresso curso (%)','Faltas restantes','Situação']
    for c, name in enumerate(columns): sheet.write(3, c, name, header)
    status = {'ok':'Regular','warning':'Atenção','critical':'Crítico','exceeded':'Limite excedido'}
    for i, row in enumerate(report['rows'], start=4):
        values = [row['student'],row['registration'],row['class_name'],row['course'],
                  row['present_hours'],row['absent_hours'],row['attendance_percent'],row['taught_hours'],
                  row['progress_percent'],row['remaining_absent_hours'],status[row['severity']]]
        for c, value in enumerate(values):
            if value is None: sheet.write_blank(i,c,None)
            elif isinstance(value,(int,float)):sheet.write_number(i,c,value,percent if c in (6,8) else num)
            else:sheet.write_string(i,c,str(value))
    sheet.freeze_panes(4, 4)
    sheet.autofilter(3,0,max(4,len(report['rows'])+3),10)
    sheet.set_column('A:A',28);sheet.set_column('B:C',18);sheet.set_column('D:D',30)
    sheet.set_column('E:J',19);sheet.set_column('K:K',18)
    notes = workbook.add_worksheet('Critérios')
    notes.set_column('A:A',115)
    notes.write('A1','Critérios de cálculo',title)
    for i, note in enumerate(report['notes'],start=2):notes.write_string(i,0,note)
    workbook.close();buffer.seek(0)
    return send_file(buffer,as_attachment=True,download_name='educontrol_frequencia.xlsx',
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
