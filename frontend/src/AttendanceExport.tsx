import {useEffect,useMemo,useState} from 'react';
import {Download,FileSpreadsheet,FileText,Eye,Info} from 'lucide-react';
import {api,flashError} from './shared';
import type {Obj} from './shared';
export default function AttendanceExport({classes}:{classes:Obj[]}){
 const [clazz,setClazz]=useState('');const [start,setStart]=useState('');const [end,setEnd]=useState('');
 const [format,setFormat]=useState<'xlsx'|'csv'>('xlsx');const [result,setResult]=useState<Obj|null>(null);
 const [loading,setLoading]=useState(false);const [error,setError]=useState('');
 const q=useMemo(()=>{const p=new URLSearchParams();if(clazz)p.set('class_id',clazz);if(start)p.set('date_from',start);if(end)p.set('date_to',end);return p.toString()},[clazz,start,end]);
 useEffect(()=>{setResult(null);setError('')},[q]);
 const preview=async()=>{setLoading(true);setError('');try{setResult(await api(`/exports/attendance/preview?${q}`))}catch(e){setError(flashError(e))}finally{setLoading(false)}};
 return <section className="panel operational-export">
  <div className="operational-heading"><div><span className="eyebrow">EXPORTAÇÃO OPERACIONAL</span><h2>Exportar chamadas</h2><p>Selecione a turma e o período, confira os registros e gere o arquivo.</p></div><FileSpreadsheet size={28}/></div>
  <div className="operational-filters">
   <label className="field"><span>Turma *</span><select value={clazz} onChange={e=>setClazz(e.target.value)}><option value="">Selecione uma turma</option>{classes.map(c=><option key={c.id} value={c.id}>{c.name} · {c.course}</option>)}</select></label>
   <label className="field"><span>Data inicial</span><input type="date" max={end||undefined} value={start} onChange={e=>setStart(e.target.value)}/></label>
   <label className="field"><span>Data final</span><input type="date" min={start||undefined} value={end} onChange={e=>setEnd(e.target.value)}/></label>
   <label className="field"><span>Formato</span><select value={format} onChange={e=>setFormat(e.target.value as 'xlsx'|'csv')}><option value="xlsx">Excel (.xlsx)</option><option value="csv">CSV (.csv)</option></select></label>
  </div>
  <div className="operational-actions"><button className="outline-btn" onClick={preview} disabled={!clazz||loading}><Eye size={16}/>{loading?'Carregando...':'Pré-visualizar'}</button>
  {result&&<a className="primary" href={`/api/exports/attendance/download?${q}&format=${format}`}><Download size={17}/>Baixar {format.toUpperCase()}</a>}</div>
  {error&&<p className="text-error" role="alert">{error}</p>}
  {result&&<><div className="operational-summary"><b>{result.total} registro(s) encontrados</b><span>Turma {result.turma} · Amostra de até 15 registros</span></div>
   <div className="report-table-scroll"><table className="report-table"><thead><tr><th>Matrícula</th><th>Aluno</th><th>Data</th><th>Horas</th><th>Chamada</th></tr></thead><tbody>{result.rows.map((r:Obj,i:number)=><tr key={i}><td>{r.matricula}</td><td>{r.aluno}</td><td>{r.data_aula}</td><td>{r.horas_aula}</td><td>{r.presenca}</td></tr>)}{result.rows.length===0&&<tr><td colSpan={5}>Nenhuma chamada registrada no período.</td></tr>}</tbody></table></div></>}
  <div className="operational-note"><Info size={18}/><p><strong>Modelo provisório:</strong> P = presente, F = falta, J = falta justificada (conta como ausência). A planilha Excel tem abas “Registros”, “Matriz” e “Legenda”. Nenhum arquivo é enviado automaticamente ao sistema externo. O layout da automação será ajustado quando você compartilhar um exemplo.</p></div>
 </section>;
}
