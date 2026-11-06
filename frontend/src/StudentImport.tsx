import {useState} from 'react';
import {ArrowLeft,FileSpreadsheet,UploadCloud,CheckCircle2,AlertTriangle} from 'lucide-react';
import {flashError,getCsrf} from './shared';
import type {Obj} from './shared';

type Plan={headers:string[],mapping:Record<string,string>,rows:Obj[],counts:Record<string,number>,can_commit:boolean,total:number};
const fields:[string,string][]=[['name','Nome completo'],['registration','Número da matrícula'],['email','E-mail'],['school','Colégio'],['class_name','Turma da planilha']];

export default function StudentImport({classes,onBack,onImported}:{classes:Obj[],onBack:()=>void,onImported:()=>Promise<void>}){
 const [file,setFile]=useState<File|null>(null);
 const [mapping,setMapping]=useState<Record<string,string>>({});
 const [defaultClass,setDefaultClass]=useState('');
 const [plan,setPlan]=useState<Plan|null>(null);const [mappingDirty,setMappingDirty]=useState(false);
 const [error,setError]=useState('');const[success,setSuccess]=useState('');const[busy,setBusy]=useState(false);
 const submit=async(commit=false,explicitMapping?:Record<string,string>)=>{
  if(!file){setError('Selecione uma planilha');return;}
  setBusy(true);setError('');setSuccess('');
  try{
   const form=new FormData();form.append('file',file);if(defaultClass)form.append('default_class_id',defaultClass);
   const m=explicitMapping||mapping;if(Object.values(m).some(Boolean))form.append('mapping',JSON.stringify(m));
   const response=await fetch('/api/imports/students/'+(commit?'commit':'preview'),{method:'POST',body:form,credentials:'same-origin',headers:{'X-CSRF-Token':getCsrf()}});
   const data=await response.json();if(!response.ok)throw new Error(data.error||`Falha HTTP ${response.status}`);
   if(commit){setSuccess(`${data.students_created} aluno(s) cadastrado(s), ${data.enrollments_created} matrícula(s) criada(s), ${data.skipped} ignorado(s).`);setPlan(null);await onImported();}
   else {setPlan(data);setMapping(data.mapping);setMappingDirty(false);}
  }catch(e){setError(flashError(e))}finally{setBusy(false)}
 };
 const pick=(chosen:File|null)=>{setFile(chosen);setPlan(null);setMappingDirty(false);setMapping({});setSuccess('');setError('')};
 return <div className="import-page">
  <div className="record-heading"><div><span className="eyebrow">GESTÃO ACADÊMICA / ALUNOS</span><h2>Importar alunos e matrículas</h2><p>Pré-visualize e valide seus dados antes de confirmar. Nenhuma alteração é feita na etapa de prévia.</p></div><button className="outline-btn" onClick={onBack}><ArrowLeft size={16}/> Voltar aos alunos</button></div>
  <section className="panel import-panel"><h3><UploadCloud size={19}/> 1. Selecionar arquivo</h3><div className="import-fields"><label className="field"><span>Planilha CSV ou XLSX (até 3 MB, 2.000 alunos)</span><input type="file" accept=".csv,.xlsx" onChange={e=>pick(e.target.files?.[0]||null)}/></label><label className="field"><span>Turma padrão, caso o arquivo não informe uma</span><select value={defaultClass} onChange={e=>{setDefaultClass(e.target.value);setPlan(null)}}><option value="">Selecionar pela coluna da planilha</option>{classes.map(c=><option key={c.id} value={c.id}>{c.name} · {c.course}</option>)}</select></label></div><p className="intro">A planilha precisa ter nome e matrícula; o sistema também aceita e-mail, colégio e código da turma. Se as colunas tiverem outros nomes, associe-as na próxima etapa.</p><button className="primary" disabled={!file||busy} onClick={()=>submit(false)}><FileSpreadsheet size={17}/> {busy?'Validando...':'Pré-visualizar importação'}</button></section>
  {error&&<div className="alert error" role="alert">{error}</div>}{success&&<div className="alert success" role="status"><CheckCircle2 size={17}/>{success}</div>}
  {plan&&<><section className="panel import-panel"><h3>2. Associação de colunas</h3><div className="import-mapping">{fields.map(([key,label])=><label className="field" key={key}><span>{label}{['name','registration'].includes(key)?' *':''}</span><select value={mapping[key]||''} onChange={e=>{setMapping(x=>({...x,[key]:e.target.value}));setMappingDirty(true)}}><option value="">Não associar</option>{plan.headers.map(h=><option key={h} value={h}>{h}</option>)}</select></label>)}</div><p className="intro">Se alterar as colunas, clique novamente em Pré-visualizar para recalcular as validações.</p></section><section className="panel import-panel"><h3>3. Conferir resultados</h3><div className="import-summary"><span className="pill blue">{plan.counts.create} novos alunos</span><span className="pill blue">{plan.counts.enroll} novas matrículas</span><span className="pill">{plan.counts.skip} já existentes</span><span className={'pill '+(plan.counts.error?'red':'')}>{plan.counts.error} erros</span></div><div className="table-wrap"><table><thead><tr><th>Linha</th><th>Aluno</th><th>Matrícula</th><th>Turma</th><th>Situação / detalhes</th></tr></thead><tbody>{plan.rows.slice(0,150).map(r=><tr key={r.line}><td>{r.line}</td><td>{r.name}</td><td>{r.registration}</td><td>{r.resolved_class||'—'}</td><td>{r.issues?.length?<span className="import-error"><AlertTriangle size={14}/> {r.issues.join('; ')}</span>:({create:'Novo aluno + matrícula',enroll:'Matricular aluno existente',skip:'Matrícula já existente'} as Record<string,string>)[r.status]}</td></tr>)}</tbody></table></div>{plan.rows.length>150&&<p className="intro">Mostrando as primeiras 150 linhas de {plan.total}. Todas serão validadas e processadas.</p>}<div className="import-actions"><button className="primary" disabled={!plan.can_commit||mappingDirty||busy} onClick={()=>submit(true)}>{busy?'Importando...':'Confirmar importação'}</button>{(mappingDirty||!plan.can_commit)&&<small>Corrija os erros na planilha e gere uma nova prévia antes de confirmar.</small>}</div></section></>}
 </div>
}
