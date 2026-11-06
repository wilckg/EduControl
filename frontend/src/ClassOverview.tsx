import React,{useCallback,useEffect,useState} from 'react';
import{LayoutDashboard,GraduationCap,UsersRound,ClipboardCheck,Contact,MessageSquareWarning,ArrowLeftRight,BellRing,LogOut,BookOpen,Plus,ShieldCheck,RefreshCw,CalendarDays,Search,Clock3,UserCog,FilePlus2}from'lucide-react';
import {api,send,uploadPhoto,StudentPhoto,StudentIdentity,roles,menu,can,pageRoles,permitted,dateBR,hours,flashError} from './shared';
import type {Obj,Auth} from './shared';

export default function ClassOverview({classId,role}:{classId:number,role:string}){
 const [detail,setDetail]=useState<Obj|null>(null);
 const [failure,setFailure]=useState('');
 const [tab,setTab]=useState('students');
 const [search,setSearch]=useState('');
 useEffect(()=>{let active=true;setDetail(null);setFailure('');setTab('students');setSearch('');
  api(`/classes/${classId}/overview`).then(v=>{if(active)setDetail(v)}).catch(e=>{if(active)setFailure(flashError(e))});
  return()=>{active=false};
 },[classId]);
 const tabs=[['students','Alunos matriculados'],['lessons','Chamadas realizadas'],
  ...((['admin','coordenador','professor'].includes(role))?[['occurrences','Ocorrências']]:[]),
  ...((['admin','coordenador','secretaria'].includes(role))?[['transfers','Transferências']]:[])];
 if(failure)return <div className="alert error">Não foi possível consultar o histórico: {failure}</div>;
 if(!detail)return <div className="class-overview-loading">Carregando histórico da turma...</div>;
 const matched=(v:string)=>String(v||'').toLocaleLowerCase('pt-BR').includes(search.toLocaleLowerCase('pt-BR'));
 const students=(detail.enrollments||[]).filter((e:Obj)=>matched(e.student?.name)||matched(e.student?.registration)||matched(e.student?.school));
 const lessons=(detail.lessons||[]).filter((l:Obj)=>matched(l.topic)||matched(dateBR(l.held_on)));
 const occurrences=(detail.occurrences||[]).filter((o:Obj)=>matched(o.student?.name)||matched(o.category)||matched(o.description));
 const transfers=(detail.transfers||[]).filter((t:Obj)=>matched(t.student?.name)||matched(t.from_class)||matched(t.to_class));
 return <div className="class-overview">
  <div className="class-overview-top"><h3>Vida acadêmica da turma</h3><p>Registros históricos permanecem disponíveis após transferências.</p></div>
  <div className="class-tabbar" role="tablist" aria-label="Informações da turma">{tabs.map(([key,label])=><button key={key} type="button" role="tab" aria-selected={tab===key} className={tab===key?'class-tab active':'class-tab'} onClick={()=>{setTab(key);setSearch('')}}>{label}</button>)}</div>
  <label className="field class-overview-search"><span>Filtrar registros desta aba</span><input type="search" value={search} onChange={e=>setSearch(e.target.value)} placeholder="Pesquisar registros..."/></label>
  {tab==='students'&&<><p className="record-count">{students.length} matrícula(s), incluindo histórico</p><div className="class-table-wrap"><table><thead><tr><th>Aluno</th><th>Matrícula</th><th>Colégio</th><th>Situação</th><th>Frequência registrada</th></tr></thead><tbody>{students.map((e:Obj)=><tr key={e.id}><td><StudentIdentity student={e.student}/></td><td>{e.student.registration}</td><td>{e.student.school||'—'}</td><td><span className="class-state">{e.status==='active'?'Ativa':'Transferida'}</span></td><td>{Number(e.frequency?.attendance_percent??100).toLocaleString('pt-BR',{maximumFractionDigits:1})}%</td></tr>)}{!students.length&&<tr><td colSpan={5}>Nenhuma matrícula encontrada.</td></tr>}</tbody></table></div></>}
  {tab==='lessons'&&<><p className="record-count">{lessons.length} aula(s) registrada(s)</p><div className="class-table-wrap"><table><thead><tr><th>Data</th><th>Conteúdo</th><th>Duração</th><th>Presentes</th><th>Ausentes</th></tr></thead><tbody>{lessons.map((l:Obj)=><tr key={l.id}><td>{dateBR(l.held_on)}</td><td>{l.topic||'Sem descrição'}</td><td>{hours(l.hours)}</td><td>{l.present}</td><td>{l.absent}</td></tr>)}{!lessons.length&&<tr><td colSpan={5}>Nenhuma aula registrada.</td></tr>}</tbody></table></div></>}
  {tab==='occurrences'&&<><p className="record-count">{occurrences.length} ocorrência(s)</p>{occurrences.map((o:Obj)=><article className="class-history" key={o.id}><div className="class-history-head"><strong>{o.student.name} · {o.category}</strong><small>{new Date(o.created_at).toLocaleDateString('pt-BR')}</small></div><p>{o.description}</p><small>Responsável: {o.author}</small></article>)}{!occurrences.length&&<p className="empty">Nenhuma ocorrência encontrada.</p>}</>}
  {tab==='transfers'&&<><p className="record-count">{transfers.length} transferência(s)</p>{transfers.map((t:Obj)=><article className="class-history" key={t.id}><div className="class-history-head"><strong>{t.student.name}</strong><small>{new Date(t.transferred_at).toLocaleDateString('pt-BR')}</small></div><p>{t.from_class} → {t.to_class}</p><small>Motivo: {t.reason}</small></article>)}{!transfers.length&&<p className="empty">Nenhuma transferência encontrada.</p>}</>}
 </div>;
}

