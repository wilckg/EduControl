import {useEffect,useState} from 'react';
import {History,Search,ChevronLeft,ChevronRight} from 'lucide-react';
import {api,flashError} from './shared';
import type {Obj} from './shared';

export default function AuditPage(){
 const [rows,setRows]=useState<Obj[]>([]);const [total,setTotal]=useState(0);const [page,setPage]=useState(1);
 const [action,setAction]=useState('');const [actor,setActor]=useState('');const [from,setFrom]=useState('');const [to,setTo]=useState('');const [users,setUsers]=useState<Obj[]>([]);const [applied,setApplied]=useState('');const [error,setError]=useState('');const [loading,setLoading]=useState(false);
 useEffect(()=>{api('/users').then(setUsers).catch(()=>{})},[]);
 useEffect(()=>{let active=true;setLoading(true);setError('');
  api(`/audit?page=${page}&${applied}`).then(data=>{if(active){setRows(data.rows||[]);setTotal(data.total||0)}})
   .catch(e=>{if(active)setError(flashError(e))}).finally(()=>{if(active)setLoading(false)});
  return()=>{active=false};
 },[page,applied]);
 return <div className="audit-page">
  <div className="record-heading"><div><span className="eyebrow">ADMINISTRAÇÃO / SEGURANÇA</span><h2>Histórico de ações</h2><p>Rastreabilidade das alterações no sistema. Somente administradores podem consultar.</p></div></div>
  <section className="panel"><form className="audit-search" onSubmit={e=>{e.preventDefault();setPage(1);setApplied(new URLSearchParams({action,user_id:actor,date_from:from,date_to:to}).toString())}}><label className="field"><span>Pesquisar tipo de ação</span><input value={action} onChange={e=>setAction(e.target.value)} placeholder="Ex.: student.update, contact.create"/></label><label className="field"><span>Responsável</span><select value={actor} onChange={e=>setActor(e.target.value)}><option value="">Todos os usuários</option>{users.map(u=><option key={u.id} value={u.id}>{u.name}</option>)}</select></label><label className="field"><span>De</span><input type="date" value={from} onChange={e=>setFrom(e.target.value)}/></label><label className="field"><span>Até</span><input type="date" value={to} onChange={e=>setTo(e.target.value)}/></label><button className="primary" type="submit"><Search size={17}/> Filtrar</button><button className="outline-btn" type="button" onClick={()=>{setAction('');setActor('');setFrom('');setTo('');setApplied('');setPage(1)}}>Limpar</button></form>
   {error&&<div className="alert error" role="alert">{error}</div>}
   <div className="table-wrap"><table><thead><tr><th>Data / hora</th><th>Responsável</th><th>Ação</th><th>Referência</th><th>Detalhes</th></tr></thead><tbody>{rows.map(x=><tr key={x.id}><td>{x.created_at?new Date(x.created_at).toLocaleString('pt-BR'):'—'}</td><td>{x.actor}</td><td><span className="audit-event"><History size={14}/>{x.action}</span></td><td>{x.entity_type?`${x.entity_type} #${x.entity_id}`:'—'}</td><td>{x.details||'—'}</td></tr>)}{!rows.length&&<tr><td colSpan={5}>{loading?'Carregando...':'Nenhum evento registrado.'}</td></tr>}</tbody></table></div>
   <div className="audit-pagination"><small>{total} evento(s) · Página {page} de {Math.max(1,Math.ceil(total/30))}</small><div><button className="outline-btn" disabled={page===1||loading} onClick={()=>setPage(x=>x-1)}><ChevronLeft size={16}/> Anterior</button><button className="outline-btn" disabled={page*30>=total||loading} onClick={()=>setPage(x=>x+1)}>Próxima <ChevronRight size={16}/></button></div></div>
  </section>
 </div>;
}
