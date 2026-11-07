import AttendanceExport from './AttendanceExport';
import {useEffect,useMemo,useState} from 'react';
import {Download,FilterX,BarChart3,AlertTriangle,FileSpreadsheet,Search} from 'lucide-react';
import {api,flashError,hours} from './shared';
import type {Obj} from './shared';

type Report={rows:Obj[];summary:Obj;notes:string[]};
const status:Record<string,string>={ok:'Regular',warning:'Atenção',critical:'Crítico',exceeded:'Limite excedido'};
const formatPercent=(value:number|null)=>value==null?'—':`${Number(value).toLocaleString('pt-BR',{maximumFractionDigits:1})}%`;

export default function Reports({courses,classes,students}:{courses:Obj[],classes:Obj[],students:Obj[]}){
 const [mode,setMode]=useState<'gerencial'|'operacional'>('gerencial');
 const [course,setCourse]=useState('');const [clazz,setClazz]=useState('');const [student,setStudent]=useState('');
 const [start,setStart]=useState('');const [end,setEnd]=useState('');const [search,setSearch]=useState('');
 const [report,setReport]=useState<Report|null>(null);const [loading,setLoading]=useState(false);const [error,setError]=useState('');
 const visibleClasses=useMemo(()=>classes.filter(c=>!course||String(c.course_id)===course),[classes,course]);
 const query=useMemo(()=>{const q=new URLSearchParams();if(course)q.set('course_id',course);if(clazz)q.set('class_id',clazz);if(student)q.set('student_id',student);if(start)q.set('date_from',start);if(end)q.set('date_to',end);return q.toString()},[course,clazz,student,start,end]);
 useEffect(()=>{let live=true;setLoading(true);setError('');api(`/reports/attendance?${query}`).then((r:Report)=>{if(live)setReport(r)}).catch(e=>{if(live)setError(flashError(e))}).finally(()=>{if(live)setLoading(false)});return()=>{live=false}},[query]);
 const rows=useMemo(()=>report?.rows.filter(r=>[r.student,r.registration,r.course,r.class_name].some(v=>String(v||'').toLocaleLowerCase('pt-BR').includes(search.toLocaleLowerCase('pt-BR'))))||[],[report,search]);
 return <div className="reports-page"><div className="report-mode-tabs"><button className={mode==='gerencial'?'active':''} onClick={()=>setMode('gerencial')}>Relatório gerencial</button><button className={mode==='operacional'?'active':''} onClick={()=>setMode('operacional')}>Exportar chamadas</button></div>{mode==='operacional'?<AttendanceExport classes={classes}/>:<>
  <div className="reports-heading"><div><h2>Relatórios acadêmicos</h2><p className="intro">Frequência, carga horária e acompanhamento das matrículas.</p></div><a className="primary report-export" href={`/api/reports/attendance/export?${query}`}><FileSpreadsheet size={17}/> Exportar Excel</a></div>
  <section className="panel report-filters"><div className="report-filter-grid">
   <label className="field"><span>Curso</span><select value={course} onChange={e=>{setCourse(e.target.value);setClazz('')}}><option value="">Todos os cursos</option>{courses.map(c=><option key={c.id} value={c.id}>{c.name}</option>)}</select></label>
   <label className="field"><span>Turma</span><select value={clazz} onChange={e=>setClazz(e.target.value)}><option value="">Todas as turmas</option>{visibleClasses.map(c=><option key={c.id} value={c.id}>{c.name}</option>)}</select></label>
   <label className="field"><span>Aluno</span><select value={student} onChange={e=>setStudent(e.target.value)}><option value="">Todos os alunos</option>{students.map(s=><option key={s.id} value={s.id}>{s.name} · {s.registration}</option>)}</select></label>
   <label className="field"><span>Data inicial</span><input type="date" value={start} max={end||undefined} onChange={e=>setStart(e.target.value)}/></label>
   <label className="field"><span>Data final</span><input type="date" value={end} min={start||undefined} onChange={e=>setEnd(e.target.value)}/></label>
   <button className="outline-btn report-clear" onClick={()=>{setCourse('');setClazz('');setStudent('');setStart('');setEnd('');setSearch('')}}><FilterX size={16}/> Limpar</button>
  </div></section>
  {error&&<div className="alert error">{error}</div>}
  <div className="report-kpis">
   <div className="report-kpi"><BarChart3 size={22}/><div><small>Frequência média registrada</small><strong>{formatPercent(report?.summary?.average_attendance??null)}</strong></div></div>
   <div className="report-kpi"><AlertTriangle size={22}/><div><small>Matrículas críticas</small><strong>{report?.summary?.critical??'—'}</strong></div></div>
   <div className="report-kpi"><Search size={22}/><div><small>Matrículas em atenção</small><strong>{report?.summary?.warning??'—'}</strong></div></div>
   <div className="report-kpi"><Download size={22}/><div><small>Matrículas no relatório</small><strong>{report?.summary?.enrollments??'—'}</strong></div></div>
  </div>
  <section className="panel report-results"><div className="report-table-heading"><div><h3>Frequência dos alunos</h3><small>{loading?'Atualizando relatório...':`${rows.length} matrícula(s) encontradas`}</small></div><label className="field"><span>Pesquisar nos resultados</span><input placeholder="Nome, matrícula, curso ou turma" value={search} onChange={e=>setSearch(e.target.value)}/></label></div>
   <div className="report-table-scroll"><table className="report-table"><thead><tr><th>Aluno</th><th>Turma / curso</th><th>Horas presentes</th><th>Horas de falta</th><th>Frequência</th><th>CH ministrada</th><th>Progresso</th><th>Risco</th></tr></thead><tbody>{rows.map(r=><tr key={r.enrollment_id}><td><strong>{r.student}</strong><small>{r.registration}</small></td><td>{r.class_name}<small>{r.course}</small></td><td>{hours(r.present_hours)}</td><td>{hours(r.absent_hours)}</td><td>{formatPercent(r.attendance_percent)}</td><td>{hours(r.taught_hours)} <small>de {hours(r.course_hours)}</small></td><td>{formatPercent(r.progress_percent)}</td><td><span className={`report-status ${r.severity}`}>{status[r.severity]||r.severity}</span></td></tr>)}{!loading&&rows.length===0&&<tr><td colSpan={8} className="report-empty">Nenhum registro para os filtros selecionados.</td></tr>}</tbody></table></div>
  </section>
  <section className="report-notes"><h3>Como interpretar</h3>{(report?.notes||[]).map((note,i)=><p key={i}>{note}</p>)}</section>
 </>}</div>;
}
