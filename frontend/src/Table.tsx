import React,{useCallback,useEffect,useState} from 'react';
import{LayoutDashboard,GraduationCap,UsersRound,ClipboardCheck,Contact,MessageSquareWarning,ArrowLeftRight,BellRing,LogOut,BookOpen,Plus,ShieldCheck,RefreshCw,CalendarDays,Search,Clock3,UserCog,FilePlus2}from'lucide-react';
import {api,send,uploadPhoto,StudentPhoto,StudentIdentity,roles,menu,can,pageRoles,permitted,dateBR,hours,flashError} from './shared';
import type {Obj,Auth} from './shared';

export default function Table({headers,rows}:{headers:string[],rows:any[][]}){return <div className="table-wrap"><table><thead><tr>{headers.map(h=><th key={h}>{h}</th>)}</tr></thead><tbody>{rows.length?rows.map((r,i)=><tr key={i}>{r.map((v,j)=><td key={j}>{v}</td>)}</tr>):<tr><td colSpan={headers.length}>Nenhum registro encontrado.</td></tr>}</tbody></table></div>}
