import React,{useCallback,useEffect,useState} from 'react';
import{LayoutDashboard,GraduationCap,UsersRound,ClipboardCheck,Contact,MessageSquareWarning,ArrowLeftRight,BellRing,LogOut,BookOpen,Plus,ShieldCheck,RefreshCw,CalendarDays,Search,Clock3,UserCog,FilePlus2}from'lucide-react';
import {api,send,uploadPhoto,StudentPhoto,StudentIdentity,roles,menu,can,pageRoles,permitted,dateBR,hours,flashError} from './shared';
import type {Obj,Auth} from './shared';

export default function SecretaryDashboard({data,onNavigate,onContactStudent}:{data:Obj,onNavigate:(p:string)=>void,onContactStudent:(studentId:number)=>void}){
 const summary=data.secretaria||{};
 const recent:Obj[]=summary.recent_transfers||[];
 const unassigned:Obj[]=summary.classes_without_teacher||[];
 return <div className="secretary-dashboard">
   <div className="section-lead"><div><span className="eyebrow">ÁREA ADMINISTRATIVA</span><h2>Rotina da Secretaria</h2><p>Uma visão prática de matrículas, turmas e movimentações acadêmicas.</p></div><button className="primary" onClick={()=>onNavigate('students')}><Plus size={17}/> Nova matrícula</button></div>
   <div className="stats secretary-stats">
    {[["Alunos cadastrados",summary.students_total??0,UsersRound],["Matrículas ativas",summary.active_enrollments??0,ClipboardCheck],["Turmas cadastradas",summary.classes_total??0,GraduationCap],["Transferências",summary.transfers_total??0,ArrowLeftRight]].map(([label,value,Icon]:any)=><div className="stat" key={label}><div className="statline"><span>{label}</span><Icon size={19}/></div><strong>{value}</strong><small>Registros acadêmicos</small></div>)}
   </div>
   <section className="panel priority-panel"><div className="panel-head"><h3><BellRing size={18}/> Alertas de frequência</h3><button className="text-action" onClick={()=>onNavigate('alerts')}>Ver todos →</button></div>{(data.alerts||[]).length?(data.alerts||[]).slice(0,5).map((a:Obj)=><div className="item" key={a.enrollment_id}><div><b>{a.student.name}</b><small>{a.class_name} · {hours(a.absent_hours)} de ausência · {hours(a.remaining_absent_hours)} restantes</small></div><button type="button" className="outline-btn" onClick={()=>onContactStudent(a.student.id)}>Registrar contato</button><span className={'pill '+(a.severity==='exceeded'?'red':'orange')}>{a.severity==='exceeded'?'Limite ultrapassado':a.severity==='critical'?'Crítico':'Atenção'}</span></div>):<p className="empty">Sem alertas de frequência no momento.</p>}</section>
   <div className="secretary-actions"><h3>Acessos rápidos</h3><div className="quick-grid">
     <button onClick={()=>onNavigate('students')}><UsersRound size={20}/><span><b>Alunos e matrículas</b><small>Consultar, cadastrar e matricular</small></span><span aria-hidden>↗</span></button>
     <button onClick={()=>onNavigate('classes')}><GraduationCap size={20}/><span><b>Turmas</b><small>Organizar oferta e responsáveis</small></span><span aria-hidden>↗</span></button>
     <button onClick={()=>onNavigate('alerts')}><BellRing size={20}/><span><b>Alertas de frequência</b><small>Acompanhar limites e pendências</small></span><span aria-hidden>↗</span></button>
     <button onClick={()=>onNavigate('transfers')}><ArrowLeftRight size={20}/><span><b>Transferir aluno</b><small>Movimentar e consultar histórico</small></span><span aria-hidden>↗</span></button>
   </div></div>
   <div className="two-col"><section className="panel"><div className="panel-head"><h3>Transferências recentes</h3><button className="text-action" onClick={()=>onNavigate('transfers')}>Ver todas →</button></div>{recent.length?recent.map((t:Obj,i:number)=><div className="item" key={i}><div><b>{t.student}</b><small>{t.from_class} → {t.to_class}</small></div><span className="pill blue">Transferido</span></div>):<p className="empty">Nenhuma transferência registrada.</p>}</section>
   <section className="panel"><div className="panel-head"><h3>Turmas sem professor</h3><button className="text-action" onClick={()=>onNavigate('classes')}>Ver turmas →</button></div>{unassigned.length?unassigned.map((c:Obj)=><div className="item" key={c.id}><div><b>{c.name}</b><small>{c.course}</small></div><span className="pill orange">Sem responsável</span></div>):<p className="empty">Todas as turmas possuem professor responsável.</p>}</section></div>
 </div>
}

