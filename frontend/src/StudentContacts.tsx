import {useEffect,useState} from 'react';
import type {FormEvent} from 'react';
import {MessageCircle,PhoneCall,Plus,CalendarClock,CheckCircle2,RefreshCcw} from 'lucide-react';
import {api,send,flashError} from './shared';
import type {Obj} from './shared';

const CHANNELS=[['whatsapp','WhatsApp'],['telefone','Ligação'],['email','E-mail'],['presencial','Presencial'],['outro','Outro']];
const OUTCOMES=[['pendente','Pendente'],['sem_resposta','Sem resposta'],['respondeu','Respondeu'],['resolvido','Resolvido']];
const initial={channel:'whatsapp',outcome:'pendente',subject:'',notes:'',next_action:'',followup_on:'',contacted_at:new Date().toISOString().slice(0,10)};
const labelFor=(list:string[][],value:string)=>list.find(x=>x[0]===value)?.[1]||value;

export default function StudentContacts({studentId,role,filter}:{studentId:number,role:string,filter:string}){
 const [rows,setRows]=useState<Obj[]>([]);const [busy,setBusy]=useState(false);const [error,setError]=useState('');
 const [showForm,setShowForm]=useState(false);const [form,setForm]=useState({...initial});
 const editable=['admin','secretaria'].includes(role);
 const reload=async()=>{setError('');try{setRows(await api(`/students/${studentId}/contacts`))}catch(e){setError(flashError(e))}};
 useEffect(()=>{setRows([]);setShowForm(false);void reload()},[studentId]);
 const save=async(e:FormEvent)=>{e.preventDefault();setBusy(true);setError('');try{
  await send(`/students/${studentId}/contacts`,{...form,contacted_at:form.contacted_at+'T12:00:00'});
  setForm({...initial});setShowForm(false);await reload();
 }catch(err){setError(flashError(err))}finally{setBusy(false)}};
 const updateOutcome=async(item:Obj,outcome:string)=>{setBusy(true);setError('');try{await send(`/contacts/${item.id}`,{outcome},'PATCH');await reload()}catch(err){setError(flashError(err))}finally{setBusy(false)}};
 const visible=rows.filter(x=>[x.subject,x.notes,x.channel,x.outcome,x.author,x.next_action].some(v=>String(v||'').toLowerCase().includes(filter.toLowerCase())));
 return <div className="contacts-module">
  <div className="contact-toolbar"><div><h3><MessageCircle size={19}/> Histórico de contatos</h3><p className="intro">Tentativas, respostas e acompanhamentos administrativos do estudante.</p></div>{editable&&<button className="primary" onClick={()=>setShowForm(v=>!v)}><Plus size={16}/>{showForm?'Fechar formulário':'Registrar contato'}</button>}</div>
  {error&&<div className="alert error" role="alert">{error}</div>}
  {showForm&&editable&&<form className="panel contact-form" onSubmit={save}><h3>Novo registro de contato</h3><div className="contact-form-grid">
   <label className="field"><span>Data do contato</span><input type="date" required value={form.contacted_at} onChange={e=>setForm({...form,contacted_at:e.target.value})}/></label>
   <label className="field"><span>Canal utilizado</span><select value={form.channel} onChange={e=>setForm({...form,channel:e.target.value})}>{CHANNELS.map(([k,v])=><option key={k} value={k}>{v}</option>)}</select></label>
   <label className="field"><span>Resultado</span><select value={form.outcome} onChange={e=>setForm({...form,outcome:e.target.value})}>{OUTCOMES.map(([k,v])=><option key={k} value={k}>{v}</option>)}</select></label>
   <label className="field"><span>Assunto</span><input maxLength={150} required placeholder="Ex.: Ausências na última semana" value={form.subject} onChange={e=>setForm({...form,subject:e.target.value})}/></label>
   <label className="field span-two"><span>Descrição / resposta</span><textarea required maxLength={4000} placeholder="Registre objetivamente o que foi conversado ou tentado." value={form.notes} onChange={e=>setForm({...form,notes:e.target.value})}/></label>
   <label className="field"><span>Próxima ação (opcional)</span><input maxLength={400} value={form.next_action} onChange={e=>setForm({...form,next_action:e.target.value})}/></label>
   <label className="field"><span>Retornar em (opcional)</span><input type="date" value={form.followup_on} onChange={e=>setForm({...form,followup_on:e.target.value})}/></label>
  </div><div className="contact-actions"><button className="primary" disabled={busy} type="submit">{busy?'Salvando...':'Salvar contato'}</button><button type="button" className="outline-btn" onClick={()=>setShowForm(false)}>Cancelar</button></div></form>}
  <div className="contact-list">{visible.map(item=><article className="contact-entry" key={item.id}>
   <div className="contact-entry-head"><div><b>{item.subject}</b><small>{new Date(item.contacted_at).toLocaleDateString('pt-BR')} · {labelFor(CHANNELS,item.channel)} · {item.author}</small></div><span className={'contact-state '+item.outcome}>{labelFor(OUTCOMES,item.outcome)}</span></div>
   <p>{item.notes}</p>{item.next_action&&<div className="contact-follow"><CalendarClock size={15}/> {item.next_action}{item.followup_on&&` · Até ${new Date(item.followup_on+'T12:00:00').toLocaleDateString('pt-BR')}`}</div>}
   {editable&&item.outcome!=='resolvido'&&<button className="contact-resolve" disabled={busy} onClick={()=>updateOutcome(item,'resolvido')}><CheckCircle2 size={14}/> Marcar como resolvido</button>}
  </article>)}
  {!visible.length&&<div className="contact-empty"><PhoneCall size={28}/><b>Nenhum contato encontrado</b><span>{rows.length?'Tente alterar a pesquisa.':'Registre o primeiro contato para iniciar o acompanhamento.'}</span></div>}</div>
 </div>;
}
