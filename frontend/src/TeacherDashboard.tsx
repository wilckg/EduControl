import React,{useCallback,useEffect,useState} from 'react';
import{LayoutDashboard,GraduationCap,UsersRound,ClipboardCheck,Contact,MessageSquareWarning,ArrowLeftRight,BellRing,LogOut,BookOpen,Plus,ShieldCheck,RefreshCw,CalendarDays,Search,Clock3,UserCog,FilePlus2}from'lucide-react';
import {api,send,uploadPhoto,StudentPhoto,StudentIdentity,roles,menu,can,pageRoles,permitted,dateBR,hours,flashError} from './shared';
import type {Obj,Auth} from './shared';

export default function TeacherDashboard({data,user,onNavigate}:{data:Obj,user:Obj,onNavigate:(p:string)=>void}){
 const classes:Obj[]=data.classes||[];
 const today=new Date().toLocaleDateString('pt-BR',{weekday:'long',day:'2-digit',month:'long'});
 return <div className="teacher-dashboard"><div className="section-lead"><div><span className="eyebrow">ÁREA DO PROFESSOR</span><h2>Bom dia, {user.name.split(' ')[0]}</h2><p>{today} · Acesse suas turmas, realize a chamada e registre ocorrências na própria aula.</p></div><button className="primary" onClick={()=>onNavigate('attendance')}><ClipboardCheck size={17}/> Abrir chamada</button></div>
 <div className="stats teacher-stats">{[['Minhas turmas',classes.length,GraduationCap],['Alunos nas turmas',data.dashboard?.students??0,UsersRound],['Frequência registrada',`${data.dashboard?.average_attendance??100}%`,ClipboardCheck]].map(([label,value,Icon]:any)=><div className="stat" key={label}><div className="statline"><span>{label}</span><Icon size={19}/></div><strong>{value}</strong><small>Resumo de suas turmas</small></div>)}</div>
 <section className="panel"><div className="panel-head"><h3>Minhas turmas</h3><button className="text-action" onClick={()=>onNavigate('attendance')}>Ir para chamadas →</button></div><p className="intro">A agenda detalhada do dia ficará disponível após o cadastro dos horários das aulas. Nesta POC, selecione a turma em Chamadas.</p>{classes.length?classes.map((c:Obj)=><div className="item" key={c.id}><div><b>{c.name}</b><small>{c.course} · {c.students} alunos · {hours(c.hours)}</small></div><button className="outline-btn" onClick={()=>onNavigate('attendance')}><ClipboardCheck size={15}/> Realizar chamada</button></div>):<p className="empty">Nenhuma turma vinculada ao seu usuário.</p>}</section></div>
}

