'use client';
import { useCallback, useEffect, useRef, useState } from 'react';
import { LEDGER_CATEGORIES, LEDGER_CURRENCIES, legacyLedgerPreview, validateLedgerEntry } from '@/lib/earn-ledger.mjs';
import type { LedgerInput, LedgerResponse } from '@/lib/earn-ledger.mjs';

const today = () => new Date().toISOString().slice(0, 10);
const empty = ():Omit<LedgerInput,'clientId'> => ({type:'income',amount:'',currency:'USD',occurredOn:today(),category:'OTHER',receiptRef:''});
const labels:Record<string,string> = {BOUNTY:'Bounty',SURVEY:'Encuesta',QUEST:'Quest',AIRDROP:'Airdrop',REWARDS:'Recompensa',FREELANCE:'Trabajo',SALE:'Venta',FEES:'Comisiones',GAS:'Gas',OTHER:'Otro'};

async function requestLedger(path = '', init?:RequestInit) {
  const response = await fetch('/api/earn-ledger'+path, {...init,cache:'no-store',credentials:'same-origin'});
  const data:any = await response.json();
  if (!response.ok) throw Object.assign(new Error(response.status===401?'Inicia sesión con ChatGPT para abrir tu registro privado.':response.status===409?'Ese identificador ya contiene otro registro. No se ha duplicado.':data.error==='INVALID_RECEIPT_REF'?'Usa una referencia interna breve, sin URLs, claves ni datos personales.':'No se pudo confirmar el registro. Actualiza o reintenta con el mismo identificador.'),{status:response.status});
  return data;
}

export default function MoneyLedger() {
  const [data,setData] = useState<LedgerResponse|null>(null), [form,setForm] = useState(empty), [pending,setPending] = useState<LedgerInput|null>(null);
  const [busy,setBusy] = useState(false), [error,setError] = useState(''), [signedOut,setSignedOut] = useState(false), [notice,setNotice] = useState('');
  const [legacyPreview,setLegacyPreview] = useState<LedgerInput[]|null>(null);
  const file = useRef<HTMLInputElement>(null), mounted = useRef(true);
  const load = useCallback(async(append=false,cursor?:string|null)=>{
    try {const result:LedgerResponse=await requestLedger(cursor?'?before='+encodeURIComponent(cursor):'');if(mounted.current){setData(old=>append&&old?{...result,entries:[...old.entries,...result.entries]}:result);setSignedOut(false);setError('');}}
    catch(e:any){if(mounted.current){setError(e.message);setSignedOut(e.status===401);if(e.status===401)setData(null);}}
  },[]);
  useEffect(()=>{mounted.current=true;load();return()=>{mounted.current=false;};},[load]);
  const submit = async(event:React.FormEvent)=>{
    event.preventDefault();setError('');setNotice('');setBusy(true);
    let input=pending;
    try {
      if(!input){input={...form,clientId:crypto.randomUUID()};validateLedgerEntry(input);setPending(input);}
      await requestLedger('',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(input)});
      setPending(null);setForm(empty());setNotice('Guardado como declarado. Sin verificación de cobro ni acción financiera.');await load();
    } catch(e:any){setError(e.name==='LedgerInputError'?'Revisa importe, fecha y referencia: importe positivo con hasta dos decimales; fecha no futura.':e.message);setSignedOut(e.status===401);}
    finally{setBusy(false);}
  };
  const exportRecords = async()=>{
    setBusy(true);setError('');
    try{
      const entries:LedgerInput[]=[];let cursor:string|null=null;
      for(let page=0;page<100;page++){
        const result:LedgerResponse=await requestLedger(cursor?'?before='+encodeURIComponent(cursor):'');
        entries.push(...result.entries.map(({clientId,type,amount,currency,occurredOn,category,receiptRef,source,minutes,legacyPaidFlag,legacyPlatform})=>({clientId,type,amount,currency,occurredOn,category,receiptRef,source,minutes,legacyPaidFlag,legacyPlatform})));
        cursor=result.nextCursor;if(!result.hasMore)break;if(page===99)throw new Error('Más de 10 000 registros: exportación detenida para evitar un archivo incompleto.');
      }
      const url=URL.createObjectURL(new Blob([JSON.stringify({schema:'money-earn-ledger-v1',status:'REPORTED',exportedAt:new Date().toISOString(),entries},null,2)],{type:'application/json'}));
      const anchor=document.createElement('a');anchor.href=url;anchor.download=`MONEY_registro_privado_${today()}.json`;anchor.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
    }catch(e:any){setError(e.message);}finally{setBusy(false);}
  };
  const importRecords = async(selected:File)=>{
    setBusy(true);setError('');setNotice('');
    try{
      if(selected.size>262144)throw new Error('Archivo demasiado grande. Máximo 256 KB.');
      const doc=JSON.parse(await selected.text());
      if(doc.source==='MONEY_OMEGA_EARN_LEGACY'){setLegacyPreview(await legacyLedgerPreview(doc));return;}
      if(doc.schema!=='money-earn-ledger-v1'||!Array.isArray(doc.entries)||!doc.entries.length||doc.entries.length>100)throw new Error('Importa entre 1 y 100 registros del formato MONEY. La importación no verifica cobros.');
      // Validate the complete batch before the first write. Replays remain idempotent.
      for(const entry of doc.entries)validateLedgerEntry(entry);
      let count=0;
      for(const entry of doc.entries){await requestLedger('',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(entry)});count++;setNotice(`${count}/${doc.entries.length} procesados como declarados. Reimportar el mismo archivo evita duplicados.`);}
      await load();
    }catch(e:any){await load();setError(e.name==='LedgerInputError'?'El archivo contiene campos, importes o referencias no válidos. Corrígelo y vuelve a importar.':e.message);}
    finally{setBusy(false);if(file.current)file.current.value='';}
  };
  const confirmLegacy = async()=>{
    if(!legacyPreview)return;setBusy(true);setError('');let done=0;
    try{for(const input of legacyPreview){await requestLedger('',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(input)});done++;setNotice(`${done}/${legacyPreview.length} apuntes legacy procesados. Fecha desconocida; sin verificación.`);}setLegacyPreview(null);await load();}
    catch(e:any){await load();setError(e.message+' Reimportar el mismo archivo conserva los identificadores.');}
    finally{setBusy(false);}
  };
  return <section className="panel" aria-labelledby="ledger-title">
    <div className="panel-heading"><div><span className="eyebrow">REGISTRO PRIVADO / POR USUARIO</span><h2 id="ledger-title">Recursos declarados</h2></div><span className="badge amber">SIN CONCILIAR</span></div>
    <p>Guarda ingresos y gastos entre dispositivos al iniciar sesión. Tus apuntes no se verifican automáticamente contra cuentas o comprobantes. Registrar un importe no cobra, paga ni mueve dinero.</p>
    {signedOut?<a className="button" href="/signin-with-chatgpt?return_to=%2F%23registro" target="_top">Iniciar sesión con ChatGPT</a>:<>
      <div className="source-links" style={{marginBottom:20}}><button className="button subtle" disabled={busy} onClick={()=>load()}>Actualizar</button><button className="button subtle" disabled={busy||!data} onClick={exportRecords}>Exportar JSON privado</button><button className="button subtle" disabled={busy||!data} onClick={()=>file.current?.click()}>Importar JSON · hasta 100</button><input ref={file} type="file" accept="application/json,.json" hidden onChange={e=>{const selected=e.target.files?.[0];if(selected)importRecords(selected);}}/></div>
      {legacyPreview&&<div className="method-callout"><strong>Revisar migración: {legacyPreview.length} apuntes del dispositivo</strong><p>Moneda original MXN. Fecha desconocida: no se inventará. La marca histórica «pagado» seguirá siendo una declaración; los no pagados quedarán PENDIENTES y fuera de los totales.</p><ul>{legacyPreview.map(row=><li key={row.clientId}>{row.legacyPlatform}: {row.type==='expense'?'-':''}{row.amount} MXN · {row.minutes??'—'} min · {row.legacyPaidFlag?'declarado pagado':'pendiente'}</li>)}</ul><button className="button" disabled={busy} onClick={confirmLegacy}>Confirmar importación privada</button><button className="button subtle" disabled={busy} onClick={()=>setLegacyPreview(null)}>Cancelar</button></div>}
      <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(180px,1fr))',gap:12,marginBottom:22}}>{data?.totalsByCurrency.map(total=><div key={total.currency} className="method-callout"><small>{total.currency} · {total.count} apuntes declarados</small><p>Ingresos: {total.income}<br/>Gastos: {total.expense}<br/><strong>Neto declarado: {total.net}</strong></p></div>)}</div>
      <form onSubmit={submit} style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(150px,1fr))',gap:12,alignItems:'end',marginBottom:20}}>
        <label>Tipo<select className="button subtle" disabled={busy||!!pending} value={form.type} onChange={e=>setForm({...form,type:e.target.value as 'income'|'expense'})}><option value="income">Ingreso declarado</option><option value="expense">Gasto declarado</option></select></label>
        <label>Importe<input className="button subtle" disabled={busy||!!pending} required inputMode="decimal" placeholder="12.34" value={form.amount} onChange={e=>setForm({...form,amount:e.target.value})}/></label>
        <label>Moneda<select className="button subtle" disabled={busy||!!pending} value={form.currency} onChange={e=>setForm({...form,currency:e.target.value})}>{LEDGER_CURRENCIES.map(c=><option key={c}>{c}</option>)}</select></label>
        <label>Fecha<input className="button subtle" disabled={busy||!!pending} required type="date" min="2000-01-01" max={today()} value={form.occurredOn??''} onChange={e=>setForm({...form,occurredOn:e.target.value})}/></label>
        <label>Categoría<select className="button subtle" disabled={busy||!!pending} value={form.category} onChange={e=>setForm({...form,category:e.target.value})}>{LEDGER_CATEGORIES.map(c=><option value={c} key={c}>{labels[c]}</option>)}</select></label>
        <label>Referencia interna · opcional<input className="button subtle" disabled={busy||!!pending} maxLength={32} placeholder="Recibo-01" value={form.receiptRef??''} onChange={e=>setForm({...form,receiptRef:e.target.value})}/></label>
        <button className="button" disabled={busy||!data} type="submit">{busy?'Guardando…':pending?'Reintentar mismo registro':'Guardar declarado'}</button>
      </form>
      {pending&&<p>El intento conserva su identificador para evitar duplicados. Reintenta antes de registrar otro importe.</p>}
      <small>La referencia sólo admite un código breve: sin URLs, nombres personales, cuentas ni secretos. Importar conserva identificadores, sin verificarlos. Cada lote de importación admite 100 registros; un respaldo exportado puede contener hasta 10 000. Las monedas se suman por separado y los pendientes quedan fuera del total.</small>
      <div className="table-wrap" style={{marginTop:20}}><table><thead><tr><th>Fecha</th><th>Tipo / categoría</th><th>Importe</th><th>Tiempo / tasa</th><th>Referencia</th><th>Evidencia</th></tr></thead><tbody>{data?.entries.length?data.entries.map(entry=><tr key={entry.id}><td>{entry.occurredOn??'Desconocida · legado'}</td><td>{entry.type==='income'?'Ingreso':'Gasto'} · {entry.legacyPlatform??labels[entry.category]??entry.category}</td><td>{entry.currency} {entry.amount}</td><td>{entry.minutes===null?'—':`${entry.minutes} min`}{entry.minutes!==null&&entry.minutes>0&&(entry.evidenceStatus==='PENDING'?<small> · tasa no realizada</small>:<small> · {(Number(entry.amount)*60/entry.minutes).toFixed(2)} {entry.currency}/h declarado</small>)}</td><td>{entry.receiptRef??'—'}</td><td><span className="badge dim">{entry.evidenceStatus==='PENDING'?'PENDIENTE':'DECLARADO'}</span></td></tr>):<tr><td className="empty-table" colSpan={6}>{data?'Sin registros declarados.':'Cargando registro privado…'}</td></tr>}</tbody></table></div>
      {data?.hasMore&&<button className="button subtle" disabled={busy} onClick={()=>load(true,data.nextCursor)}>Mostrar 100 más</button>}
    </>}
    {notice&&<p role="status">{notice}</p>}{error&&<p className="error-text" role="alert">{error}</p>}
  </section>;
}
