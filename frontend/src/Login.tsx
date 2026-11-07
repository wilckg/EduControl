import React,{useState} from 'react';
import {GraduationCap,ClipboardCheck,BellRing,Contact} from 'lucide-react';
import InstitutionalFooter from './InstitutionalFooter';
import {send,roles,flashError} from './shared';
import type {Auth} from './shared';

export default function Login({onLogin}:{onLogin:(a:Auth)=>void}){
 const[email,setEmail]=useState('admin@educontrol.local');
 const[password,setPassword]=useState('Demo@12345');
 const[error,setError]=useState('');
 const[busy,setBusy]=useState(false);
 return <div className="login-wrap login-classic-with-photo">
  <div className="login-classic-content">
   <section className="login-info">
    <div className="brand large"><span className="brand-icon"><GraduationCap/></span><span>EduControl<small>SISTEMA DE GESTÃO ACADÊMICA</small></span></div>
    <div className="login-classic-message">
     <h1>A escola conectada<br/>à rotina de quem ensina.</h1>
     <p>Controle turmas, acompanhe a frequência e organize a vida escolar em uma única plataforma.</p>
     <div className="login-feature"><ClipboardCheck size={19}/> Chamadas e frequência</div>
     <div className="login-feature"><BellRing size={19}/> Alertas acadêmicos</div>
     <div className="login-feature"><Contact size={19}/> Carômetro e ocorrências</div>
    </div>
   </section>
   <section className="login-form-pane">
    <form className="login-card" onSubmit={async e=>{e.preventDefault();setBusy(true);setError('');try{onLogin(await send('/auth/login',{email,password}))}catch(e){setError(flashError(e))}finally{setBusy(false)}}}>
     <h2>Acessar plataforma</h2>
     <p>Entre com sua conta do EduControl.</p>
     <label className="field"><span>E-mail</span><input type="email" autoComplete="username" value={email} onChange={e=>setEmail(e.target.value)}/></label>
     <label className="field"><span>Senha</span><input type="password" autoComplete="current-password" value={password} onChange={e=>setPassword(e.target.value)}/></label>
     {error&&<p className="text-error" role="alert">{error}</p>}
     <button className="primary full" disabled={busy}>{busy?'Autenticando...':'Entrar no EduControl'}</button>
     <div className="demo-logins"><small>Trocar perfil para teste:</small>{['admin','coordenador','professor','secretaria'].map(r=><button type="button" key={r} onClick={()=>setEmail(r+'@educontrol.local')}>{roles[r]}</button>)}</div>
    </form>
   </section>
  </div>
  <InstitutionalFooter login/>
 </div>;
}
