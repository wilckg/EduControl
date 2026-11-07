import {useState} from 'react';

type Institution={name:string;file:string;short:string;compact?:boolean};
const institutions:Institution[]=[
 {name:'Fábrica de Programadores',file:'/institutions/fabrica-de-programadores.jpg',short:'FP'},
 {name:'Prefeitura Municipal de Santana de Parnaíba',file:'/institutions/prefeitura-santana-de-parnaiba.png',short:'PMSP',compact:true},
 {name:'SENAI-SP',file:'/institutions/senai-sp.png',short:'SENAI'},
];
function InstitutionLogo({item}:{item:Institution}){
 const [broken,setBroken]=useState(false);
 return <div className={`institution-logo ${item.compact?'compact':''}`}>
  {!broken?<img src={item.file} alt={item.name} onError={()=>setBroken(true)}/>:<span className="institution-placeholder" aria-label={`Logo pendente: ${item.name}`}>{item.short}</span>}
  <span>{item.name}</span>
 </div>;
}
export default function InstitutionalFooter({login=false}:{login?:boolean}){
 return <footer className={`institutional-footer ${login?'institutional-footer-login':''}`}>
  <div className="institutional-logos">{institutions.map(item=><InstitutionLogo item={item} key={item.short}/>)}</div>
  <div className="institutional-footnote">EduControl · Sistema de gestão acadêmica · Uso experimental para validação visual</div>
 </footer>;
}
