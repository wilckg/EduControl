import React,{useCallback,useEffect,useState} from 'react';
import{createRoot}from'react-dom/client';
import{LayoutDashboard,GraduationCap,UsersRound,ClipboardCheck,Contact,MessageSquareWarning,ArrowLeftRight,BellRing,LogOut,BookOpen,Plus,ShieldCheck,RefreshCw,CalendarDays,Search,Clock3,UserCog,FilePlus2,FileSpreadsheet}from'lucide-react';


export type Obj=Record<string,any>;
export type Auth={user:Obj,csrf:string};
let csrf='';
export function setCsrf(token:string){csrf=token;}
export async function api(path:string,options:RequestInit={}){
  const response=await fetch('/api'+path,{credentials:'same-origin',...options,headers:{...(options.body?{'Content-Type':'application/json'}:{}),...(options.method&&options.method!=='GET'?{'X-CSRF-Token':csrf}:{}),...(options.headers||{})}});
  const result=await response.json().catch(()=>({}));
  if(!response.ok)throw new Error(result.error||`Erro HTTP ${response.status}`);
  return result;
}
export const send=(path:string,data:Obj,method='POST')=>api(path,{method,body:JSON.stringify(data)});
export async function uploadPhoto(id:number,file:File){
 const body=new FormData();body.append('photo',file);
 const r=await fetch(`/api/students/${id}/photo`,{method:'POST',credentials:'same-origin',headers:{'X-CSRF-Token':csrf},body});
 const data=await r.json().catch(()=>({}));if(!r.ok)throw new Error(data.error||'Não foi possível enviar foto');return data;
}
export function StudentPhoto({student,large=false}:{student:Obj,large?:boolean}){
 return student.photo_url?<img className={large?'student-photo large':'student-photo'} src={student.photo_url+'?v='+encodeURIComponent(String(student.photo_version||''))} alt={'Foto de '+student.name} loading="lazy"/>:<span className={large?'student-initials large':'student-initials'}>{student.name?.split(' ').slice(0,2).map((t:string)=>t[0]).join('')}</span>
}
export function StudentIdentity({student}:{student:Obj}){
 const [expanded,setExpanded]=useState(false);
 return <><span className="student-hover" tabIndex={0} onClick={()=>student.photo_url&&setExpanded(true)}><b>{student.name}</b><span className="photo-tooltip"><StudentPhoto student={student}/><small>{student.school||'Colégio não informado'}</small><small>{student.photo_url?'Clique no nome para ampliar':'Foto não cadastrada'}</small></span></span>{expanded&&<div className="photo-modal" role="dialog" aria-modal="true" aria-label={'Foto de '+student.name} onClick={()=>setExpanded(false)}><div className="photo-modal-content" onClick={e=>e.stopPropagation()}><button type="button" className="outline-btn" onClick={()=>setExpanded(false)}>Fechar ×</button><StudentPhoto student={student} large/><h3>{student.name}</h3><p>{student.school||'Colégio não informado'}</p></div></div>}</>
}

export const roles:Record<string,string>={admin:'Administrador',coordenador:'Coordenação',professor:'Professor',secretaria:'Secretaria'};
export const menu=[['dashboard','Dashboard',LayoutDashboard],['courses','Cursos',BookOpen],['classes','Turmas',GraduationCap],['students','Alunos',UsersRound],['attendance','Chamadas',ClipboardCheck],['carometro','Carômetro',Contact],['occurrences','Ocorrências',MessageSquareWarning],['transfers','Transferências',ArrowLeftRight],['alerts','Alertas',BellRing],['reports','Relatórios',FileSpreadsheet],['users','Usuários',UserCog]] as const;
export const can=(role:string,allowed:string[])=>allowed.includes(role);
// Definição central de visibilidade: a API ainda faz a autorização de verdade.
export const pageRoles:Record<string,string[]>={
 dashboard:['admin','coordenador','professor','secretaria'],
 courses:['admin','coordenador','professor','secretaria'],
 classes:['admin','coordenador','professor','secretaria'],
 students:['admin','coordenador','professor','secretaria'],
 attendance:['admin','coordenador','professor'],
 carometro:['admin','coordenador','professor'],
 occurrences:['admin','coordenador','professor'],
 transfers:['admin','coordenador','secretaria'],
 alerts:['admin','coordenador','secretaria'],
 reports:['admin','coordenador','secretaria'],
 users:['admin']
};
export const permitted=(role:string,page:string)=>pageRoles[page]?.includes(role)??false;
export const dateBR=(v:string)=>v?new Date(v+'T12:00:00').toLocaleDateString('pt-BR'):'—';
export const hours=(v:number)=>`${Number(v||0).toLocaleString('pt-BR',{maximumFractionDigits:1})}h`;
export const flashError=(e:unknown)=>e instanceof Error?e.message:'Ocorreu um erro';
