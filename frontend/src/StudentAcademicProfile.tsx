import React,{useCallback,useEffect,useState} from 'react';
import{LayoutDashboard,GraduationCap,UsersRound,ClipboardCheck,Contact,MessageSquareWarning,ArrowLeftRight,BellRing,LogOut,BookOpen,Plus,ShieldCheck,RefreshCw,CalendarDays,Search,Clock3,UserCog,FilePlus2}from'lucide-react';
import {api,send,uploadPhoto,StudentPhoto,StudentIdentity,roles,menu,can,pageRoles,permitted,dateBR,hours,flashError} from './shared';
import type {Obj,Auth} from './shared';

export default function StudentAcademicProfile({studentId,role}:{studentId:number,role:string}){
 const [profile,setProfile]=useState<Obj|null>(null);
 const [error,setError]=useState('');
 const [tab,setTab]=useState('enrollments');
 const [filter,setFilter]=useState('');
 useEffect(()=>{let current=true;setProfile(null);setError('');setTab('enrollments');
   api(`/students/${studentId}/academic-profile`).then(data=>{if(current)setProfile(data)}).catch(e=>{if(current)setError(flashError(e))});
   return()=>{current=false};
 },[studentId]);
 if(error)return <div className="hint" role="alert">Não foi possível carregar a ficha acadêmica: {error}</div>;
 if(!profile)return <div className="hint">Carregando histórico acadêmico...</div>;
 const enrollmentRows:Obj[]=profile.enrollments||[];
 const attend:Obj[]=profile.attendance||[];
 const occurrenceRows:Obj[]=profile.occurrences||[];
 const transferRows:Obj[]=profile.transfers||[];
 const allowedTabs=[{id:'enrollments',label:'Cursos e turmas',count:enrollmentRows.length},{id:'attendance',label:'Chamadas',count:attend.length},
   ...(role==='admin'||role==='coordenador'||role==='professor'?[{id:'occurrences',label:'Ocorrências',count:occurrenceRows.length}]:[]),
   ...(role==='admin'||role==='coordenador'||role==='secretaria'?[{id:'transfers',label:'Transferências',count:transferRows.length}]:[])];
 const includes=(...v:any[])=>v.some(x=>String(x??'').toLowerCase().includes(filter.toLowerCase()));
 return <section className="academic-profile" aria-label="Ficha acadêmica do aluno">
  <div className="academic-top"><div><span className="eyebrow">FICHA ACADÊMICA</span><h3>Histórico do estudante</h3><p>Frequência consolidada por matrícula, com histórico preservado após transferências.</p></div><span className="academic-count">{enrollmentRows.length} matrícula(s)</span></div>
  <div className="academic-overview">
    <div><small>Matrículas ativas</small><strong>{enrollmentRows.filter(x=>x.status==='active').length}</strong></div>
    <div><small>Cursos distintos</small><strong>{new Set(enrollmentRows.map(x=>x.course)).size}</strong></div>
    <div><small>Aulas registradas</small><strong>{attend.length}</strong></div>
  </div>
  <div className="academic-tabs" role="tablist" aria-label="Seções da ficha">
  {allowedTabs.map(t=><button key={t.id} role="tab" aria-selected={tab===t.id} className={tab===t.id?'active':''} onClick={()=>{setTab(t.id);setFilter('')}}>{t.label} <span>{t.count}</span></button>)}
  </div>
  <label className="field academic-search"><span>Pesquisar nesta seção</span><input value={filter} onChange={e=>setFilter(e.target.value)} placeholder="Buscar curso, turma, data ou registro"/></label>
  {tab==='enrollments'&&<div className="academic-enrollments">{enrollmentRows.filter(e=>includes(e.course,e.class_name,e.status,e.enrolled_at)).map(e=><div className="academic-enrollment" key={e.id}>
   <div className="academic-enrollment-heading"><div><b>{e.course}</b><small>{e.class_name} · Desde {dateBR(e.enrolled_at)}</small></div><span className={e.status==='active'?'pill blue':'pill'}>{e.status==='active'?'Ativa':'Encerrada/transferida'}</span></div>
   <div className="academic-metrics"><span>Frequência registrada <b>{e.frequency.attendance_percent}%</b></span><span>Horas presentes <b>{hours(e.frequency.present_hours)}</b></span><span>Horas ausentes <b>{hours(e.frequency.absent_hours)}</b></span><span>Carga horária prevista <b>{hours(e.course_hours)}</b></span></div>
   <div className="academic-progress" role="progressbar" aria-label="Frequência registrada" aria-valuenow={e.frequency.attendance_percent} aria-valuemin={0} aria-valuemax={100}><span style={{width:`${Math.min(100,Math.max(0,e.frequency.attendance_percent))}%`}}/></div>
   <small>Faltas restantes segundo as regras desta matrícula: {hours(e.frequency.remaining_absent_hours)}. Não somamos automaticamente horas de outras turmas.</small>
  </div>)}{!enrollmentRows.some(e=>includes(e.course,e.class_name,e.status,e.enrolled_at))&&<p className="hint">Nenhuma matrícula encontrada.</p>}</div>}
  {tab==='attendance'&&<div className="table-wrap"><table><thead><tr><th>Data</th><th>Turma</th><th>Conteúdo</th><th>Carga horária</th><th>Registro</th></tr></thead><tbody>{attend.filter(a=>includes(a.date,a.class_name,a.course,a.topic,a.status)).map((a,i)=><tr key={i}><td>{dateBR(a.date)}</td><td>{a.class_name}</td><td>{a.topic||'—'}</td><td>{hours(a.hours)}</td><td>{a.status==='P'?'Presente':a.status==='J'?'Falta justificada':'Falta'}</td></tr>)}{!attend.some(a=>includes(a.date,a.class_name,a.course,a.topic,a.status))&&<tr><td colSpan={5}>Nenhuma chamada registrada.</td></tr>}</tbody></table></div>}
  {tab==='occurrences'&&profile.occurrences&&<div className="academic-entries">{occurrenceRows.filter(o=>includes(o.class_name,o.category,o.description,o.author)).map(o=><article key={o.id}><div><b>{o.category}</b><small>{o.class_name} · {new Date(o.created_at).toLocaleDateString('pt-BR')} · {o.author}</small></div><p>{o.description}</p></article>)}{!occurrenceRows.some(o=>includes(o.class_name,o.category,o.description,o.author))&&<p className="hint">Nenhuma ocorrência encontrada.</p>}</div>}
  {tab==='transfers'&&profile.transfers&&<div className="academic-entries">{transferRows.filter(t=>includes(t.from_class,t.to_class,t.reason)).map(t=><article key={t.id}><div><b>{t.from_class} → {t.to_class}</b><small>{new Date(t.transferred_at).toLocaleDateString('pt-BR')}</small></div><p>{t.reason}</p></article>)}{!transferRows.some(t=>includes(t.from_class,t.to_class,t.reason))&&<p className="hint">Nenhuma transferência encontrada.</p>}</div>}
 </section>
}

