import {useRef,useState} from 'react';
import {ArrowLeft,ArrowRight,FileSpreadsheet,UploadCloud,CheckCircle2,AlertTriangle,Download,FileCheck2,FileWarning,UsersRound,ClipboardList,ShieldCheck,RotateCcw,Info} from 'lucide-react';
import {flashError,getCsrf} from './shared';
import type {Obj} from './shared';

type Plan={headers:string[],mapping:Record<string,string>,rows:Obj[],counts:Record<string,number>,can_commit:boolean,total:number};
const fields:[string,string][]=[['name','Nome completo'],['registration','Número da matrícula'],['email','E-mail'],['school','Colégio'],['class_name','Turma da planilha']];
const STEPS=[{title:'Enviar arquivo',subtitle:'CSV ou Excel'},{title:'Conferir dados',subtitle:'Colunas e validações'},{title:'Confirmar',subtitle:'Revisar e importar'}];
const statusLabels:Record<string,string>={create:'Novo aluno + matrícula',enroll:'Nova matrícula',skip:'Já matriculado',error:'Revisar'};

export default function StudentImport({classes,onBack,onImported}:{classes:Obj[],onBack:()=>void,onImported:()=>Promise<void>}){
 const fileInput=useRef<HTMLInputElement>(null);
 const [file,setFile]=useState<File|null>(null);const [dragging,setDragging]=useState(false);const [step,setStep]=useState(0);
 const [mapping,setMapping]=useState<Record<string,string>>({});const [defaultClass,setDefaultClass]=useState('');
 const [plan,setPlan]=useState<Plan|null>(null);const [mappingDirty,setMappingDirty]=useState(false);
 const [error,setError]=useState('');const [success,setSuccess]=useState('');const [busy,setBusy]=useState(false);
 const reset=(chosen:File|null)=>{setError('');setSuccess('');setFile(null);setPlan(null);setMapping({});setMappingDirty(false);setStep(0);
  if(!chosen)return;const ext=chosen.name.toLowerCase();if(!ext.endsWith('.csv')&&!ext.endsWith('.xlsx')){setError('Selecione um arquivo CSV ou XLSX.');return}
  if(chosen.size>3*1024*1024){setError('O arquivo deve ter no máximo 3 MB.');return}setFile(chosen);
 };
 const downloadExample=()=>{
  const csv='Nome;Matrícula;E-mail;Colégio;Turma\nAna Exemplo;EDU0001;ana@exemplo.local;Escola Exemplo;WEB-A\nBruno Exemplo;EDU0002;bruno@exemplo.local;Colégio Exemplo;WEB-A\n';
  const blob=new Blob(['\ufeff',csv],{type:'text/csv;charset=utf-8'});const url=URL.createObjectURL(blob);
  const a=document.createElement('a');a.href=url;a.download='modelo_importacao_educontrol.csv';a.click();URL.revokeObjectURL(url);
 };
 const submit=async(commit=false)=>{
  if(!file){setError('Selecione uma planilha.');return;}
  setBusy(true);setError('');setSuccess('');
  try{
   const form=new FormData();form.append('file',file);if(defaultClass)form.append('default_class_id',defaultClass);
   if(Object.values(mapping).some(Boolean))form.append('mapping',JSON.stringify(mapping));
   const response=await fetch(`/api/imports/students/${commit?'commit':'preview'}`,{method:'POST',body:form,credentials:'same-origin',headers:{'X-CSRF-Token':getCsrf()}});
   const data=await response.json();if(!response.ok)throw new Error(data.error||`Falha HTTP ${response.status}`);
   if(commit){setSuccess(`${data.students_created} aluno(s) cadastrados, ${data.enrollments_created} matrícula(s) criadas e ${data.skipped} registro(s) ignorados.`);setPlan(null);setStep(3);await onImported()}
   else {setPlan(data);setMapping(data.mapping);setMappingDirty(false);setStep(1)}
  }catch(e){setError(flashError(e))}finally{setBusy(false)}
 };
 const counters=plan?.counts||{};
 return <div className="import-page import-wizard">
  <div className="record-heading import-hero"><div><span className="eyebrow">GESTÃO ACADÊMICA / ALUNOS</span><h2>Importar alunos e matrículas</h2><p>Cadastre uma turma inteira com segurança, revisando os dados antes de salvar.</p></div><button className="outline-btn" onClick={onBack}><ArrowLeft size={16}/> Voltar aos alunos</button></div>
  <div className="import-steps" aria-label="Progresso da importação">{STEPS.map((item,i)=><div className={'import-step '+(step===i?'current ':step>i?'complete':'')} key={item.title}><span className="import-step-number">{step>i?<CheckCircle2 size={18}/>:i+1}</span><span><b>{item.title}</b><small>{item.subtitle}</small></span></div>)}</div>
  {error&&<div className="alert error" role="alert"><AlertTriangle size={18}/>{error}</div>}
  {step===0&&<section className="panel import-card">
   <div className="import-section-title"><div className="import-section-icon"><UploadCloud size={23}/></div><div><h3>Selecione sua planilha</h3><p>Carregue os dados exportados do sistema de origem.</p></div></div>
   <div className={'import-dropzone '+(dragging?'dragging':'')+(file?' with-file':'')} role="button" tabIndex={0} onKeyDown={e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();fileInput.current?.click()}}} onClick={e=>{if(e.target!==fileInput.current)fileInput.current?.click()}} onDragOver={e=>{e.preventDefault();setDragging(true)}} onDragLeave={e=>{e.preventDefault();setDragging(false)}} onDrop={e=>{e.preventDefault();setDragging(false);reset(e.dataTransfer.files?.[0]||null)}}>
    <input ref={fileInput} type="file" accept=".csv,.xlsx" aria-label="Selecionar planilha para importar" onChange={e=>reset(e.target.files?.[0]||null)} hidden/>
    <span className="import-dropicon">{file?<FileSpreadsheet size={31}/>:<UploadCloud size={31}/>}</span>
    <b>{file?file.name:'Arraste o arquivo até aqui'}</b><span>{file?`${(file.size/1024).toLocaleString('pt-BR',{maximumFractionDigits:1})} KB · Clique para trocar o arquivo`:'ou clique para selecionar no seu computador'}</span><small>Formatos aceitos: .CSV e .XLSX · Até 3 MB e 2.000 linhas</small>
   </div>
   <div className="import-under-drop"><div className="import-note"><Info size={17}/><p><b>Não tem um modelo?</b> Baixe uma planilha de exemplo e ajuste os dados e a turma para sua instituição.</p></div><button className="outline-btn" onClick={downloadExample}><Download size={17}/> Baixar modelo CSV</button></div>
   <div className="import-select-row"><label className="field"><span>Turma padrão (opcional)</span><select value={defaultClass} onChange={e=>{setDefaultClass(e.target.value);setPlan(null)}}><option value="">Usar a turma informada na planilha</option>{classes.map(c=><option key={c.id} value={c.id}>{c.name} · {c.course}</option>)}</select></label><p>Se todas as linhas forem da mesma turma e a planilha não tiver essa coluna, selecione-a aqui.</p></div>
   <div className="import-footer-actions"><span>Nenhum dado é salvo durante a análise.</span><button className="primary" disabled={!file||busy} onClick={()=>submit()}>{busy?'Analisando arquivo...':'Analisar planilha'} <ArrowRight size={17}/></button></div>
  </section>}
  {step===1&&plan&&<>
   <section className="panel import-card"><div className="import-section-title"><div className="import-section-icon"><ClipboardList size={22}/></div><div><h3>Associe as colunas</h3><p>Confirme quais informações do arquivo correspondem aos campos do EduControl.</p></div></div>
   <div className="import-mapping">{fields.map(([key,label])=><label className="field" key={key}><span>{label}{['name','registration'].includes(key)?' *':''}</span><select value={mapping[key]||''} onChange={e=>{setMapping(old=>({...old,[key]:e.target.value}));setMappingDirty(true)}}><option value="">Não associar</option>{plan.headers.map(h=><option key={h} value={h}>{h}</option>)}</select></label>)}</div>
   {mappingDirty&&<div className="import-inline-warning"><AlertTriangle size={16}/> O mapeamento foi alterado. Recalcule a prévia antes de avançar.</div>}
   <div className="import-footer-actions"><button className="outline-btn" onClick={()=>setStep(0)}><ArrowLeft size={16}/> Voltar</button><button className="outline-btn" disabled={busy} onClick={()=>submit()}><RotateCcw size={16}/> {busy?'Revalidando...':'Revalidar colunas'}</button></div>
   </section>
   <section className="panel import-card"><div className="import-section-title"><div className="import-section-icon"><FileCheck2 size={22}/></div><div><h3>Resultado da validação</h3><p>Confira os registros novos, as matrículas e as linhas que precisam de correção.</p></div></div>
   <div className="import-kpis"><div><UsersRound size={20}/><small>Novos alunos</small><strong>{counters.create||0}</strong></div><div><FileCheck2 size={20}/><small>Novas matrículas</small><strong>{counters.enroll||0}</strong></div><div><CheckCircle2 size={20}/><small>Já existentes</small><strong>{counters.skip||0}</strong></div><div className={(counters.error||0)>0?'with-error':''}><FileWarning size={20}/><small>Registros com erros</small><strong>{counters.error||0}</strong></div></div>
   <div className="import-table-head"><h4>Pré-visualização <span>({plan.total} linha(s))</span></h4><span>Mostrando até 150 linhas</span></div>
   <div className="table-wrap"><table><thead><tr><th>Linha</th><th>Aluno</th><th>Matrícula</th><th>Turma</th><th>Validação</th></tr></thead><tbody>{plan.rows.slice(0,150).map(r=><tr key={r.line}><td>{r.line}</td><td><b>{r.name||'—'}</b></td><td>{r.registration||'—'}</td><td>{r.resolved_class||'—'}</td><td>{r.issues?.length?<span className="import-result error"><AlertTriangle size={14}/>{r.issues.join('; ')}</span>:<span className={'import-result '+r.status}>{statusLabels[r.status]||r.status}</span>}</td></tr>)}</tbody></table></div>
   <div className="import-footer-actions"><span>{plan.can_commit?'Os dados estão prontos para revisão final.':'Corrija as linhas com erro na planilha e envie o arquivo novamente.'}</span><button className="primary" disabled={!plan.can_commit||mappingDirty||busy} onClick={()=>setStep(2)}>Revisar importação <ArrowRight size={17}/></button></div>
   </section>
  </>}
  {step===2&&plan&&<section className="panel import-card import-confirm"><span className="import-confirm-icon"><ShieldCheck size={34}/></span><h3>Confirmar importação</h3><p>Você está prestes a cadastrar os registros aprovados no EduControl. Verifique o resumo antes de continuar.</p>
   <div className="import-final-summary"><div><span>Arquivo</span><b>{file?.name}</b></div><div><span>Alunos novos</span><b>{counters.create||0}</b></div><div><span>Novas matrículas</span><b>{counters.enroll||0}</b></div><div><span>Já existentes</span><b>{counters.skip||0}</b></div></div>
   <div className="import-confirm-notice"><Info size={18}/> O backend validará novamente o arquivo. Caso encontre registros inconsistentes, a importação será bloqueada sem cadastros parciais.</div>
   <div className="import-footer-actions"><button className="outline-btn" onClick={()=>setStep(1)}><ArrowLeft size={16}/> Revisar planilha</button><button className="primary" disabled={busy||!plan.can_commit||mappingDirty} onClick={()=>submit(true)}>{busy?'Importando...':'Confirmar e importar'} <CheckCircle2 size={17}/></button></div>
  </section>}
  {step===3&&<section className="panel import-card import-confirm" role="status"><span className="import-confirm-icon success"><CheckCircle2 size={34}/></span><h3>Importação concluída</h3><p>{success}</p><div className="import-footer-actions"><button className="outline-btn" onClick={()=>reset(null)}>Importar outra planilha</button><button className="primary" onClick={onBack}>Voltar à lista de alunos <ArrowRight size={17}/></button></div></section>}
 </div>;
}
