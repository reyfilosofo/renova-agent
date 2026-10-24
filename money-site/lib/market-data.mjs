import { cleanCandles } from './model.mjs';
export const ASSETS = ['BTC', 'ETH', 'SOL', 'XRP', 'DOGE', 'BNB'];
export const NAMES = { BTC: 'Bitcoin', ETH: 'Ethereum', SOL: 'Solana', XRP: 'XRP', DOGE: 'Dogecoin', BNB: 'BNB' };
export const CANONICAL_API = 'https://api-v2.appdeploy.ai/app/money-z6epdn';
const pairs = { BTC: 'XBTUSD', ETH: 'ETHUSD', SOL: 'SOLUSD', XRP: 'XRPUSD', DOGE: 'DOGEUSD', BNB: 'BNBUSD' };
const FRAMES = {5:'5m',15:'15m',60:'1h'};
const HOSTS = new Set(['api.kraken.com', 'api.exchange.coinbase.com', 'api-v2.appdeploy.ai']);
const cooldown = new Map(), snapshots = new Map(), pending = new Map();
const numeric = x => typeof x === 'boolean' || x === null || x === undefined || x === '' ? null : Number.isFinite(Number(x)) ? Number(x) : null;
const probability = x => { const n = numeric(x); return n !== null && n >= 0 && n <= 1 ? n : null; };
export async function publicJson(url, fetcher = fetch, credential = null) {
  const u = new URL(url);
  if (credential !== null) throw new Error('Configuración no permitida: este transporte no utiliza claves de mercados');
  if (u.protocol !== 'https:' || !HOSTS.has(u.hostname) || u.username || u.password || u.port || u.hash) throw new Error('Fuente no permitida');
  if (u.hostname === 'api-v2.appdeploy.ai' && !['/app/money-z6epdn/api/snapshot','/app/money-z6epdn/api/dayplan','/app/money-z6epdn/api/_healthcheck'].includes(u.pathname)) throw new Error('Ruta canónica no permitida');
  const pause=cooldown.get(u.hostname);
  if(fetcher===fetch&&pause&&pause.until>Date.now())throw new Error(`HTTP ${pause.status}; fuente en pausa tras restricción de acceso`);
  const r = await fetcher(u.toString(), { method: 'GET', redirect: 'manual', signal: AbortSignal.timeout(12000), headers: {Accept:'application/json'} });
  if (r.status >= 300 && r.status < 400) throw new Error('Redirección de fuente rechazada; sin datos verificables');
  if (!r.ok) {
    if (fetcher === fetch && [402,403,429,451].includes(r.status)) cooldown.set(u.hostname,{status:r.status,until:Date.now()+(r.status===451?3600000:r.status===402?300000:120000)});
    throw new Error(`HTTP ${r.status}; sin datos verificables`);
  }
  if (Number(r.headers.get('content-length') ?? 0)>2000000) throw new Error('Respuesta excede límite');
  const s = await r.text();
  if (s.length > 2000000) throw new Error('Respuesta excede límite');
  try { return JSON.parse(s); } catch { throw new Error('La fuente no devolvió JSON válido'); }
}
export async function getHistory(asset, now = Date.now(), fetcher = fetch) {
  if (!ASSETS.includes(asset)) throw new Error('Activo no permitido');
  const url = `https://api.kraken.com/0/public/OHLC?pair=${pairs[asset]}&interval=5`;
  const j = await publicJson(url, fetcher);
  if (!Array.isArray(j.error) || j.error.length) throw new Error('Histórico no disponible');
  const entries=Object.entries(j.result??{}).filter(([k,v])=>k!=='last'&&Array.isArray(v));
  if(entries.length!==1)throw new Error('Par histórico ambiguo');
  const data=entries[0][1],receivedAt=Date.now();
  // The final Kraken row is uncommitted, even when a response/cache crosses its close.
  const rows=data.slice(0,-1).map(x=>({t:Number(x[0])*1000,o:Number(x[1]),h:Number(x[2]),l:Number(x[3]),c:Number(x[4]),v:Number(x[6]),confirmed:true,observedAt:receivedAt}));
  return {source:'Kraken USD',intervalMinutes:5,receivedAt,candles:cleanCandles(rows,Math.min(now,receivedAt),5).map(c=>({...c,confirmed:true,observedAt:receivedAt})),sourceUrl:url};
}
export async function getQuotes(asset, fetcher=fetch) {
  if(!ASSETS.includes(asset))throw new Error('Activo no permitido');
  const kraken=async()=>{
    const j=await publicJson(`https://api.kraken.com/0/public/Ticker?pair=${pairs[asset]}`,fetcher);
    if(!Array.isArray(j.error)||j.error.length)throw new Error('Ticker no disponible');
    const values=Object.values(j.result??{});if(values.length!==1)throw new Error('Par ambiguo');const x=values[0];
    const price=numeric(x?.c?.[0]),bid=numeric(x?.b?.[0]),ask=numeric(x?.a?.[0]);
    if(!price||!bid||!ask||price<=0||bid<=0||ask<=0||bid>ask)throw new Error('Ticker inválido');
    return {source:'Kraken',price,bid,ask,currency:'USD',sourceAt:null,receivedAt:Date.now(),timestampVerified:false,status:'OBSERVADO'};
  };
  const coinbase=async()=>{
    if(asset==='BNB')return {source:'Coinbase spot',status:'NO_VERIFICADO',error:'Par BNB-USD no verificado'};
    const j=await publicJson(`https://api.exchange.coinbase.com/products/${asset}-USD/ticker`,fetcher);
    const price=numeric(j.price),bid=numeric(j.bid),ask=numeric(j.ask),sourceAt=Date.parse(j.time);
    if(!price||!bid||!ask||price<=0||bid<=0||ask<=0||bid>ask||!Number.isFinite(sourceAt))throw new Error('Ticker/fecha inválidos');
    return {source:'Coinbase spot',price,bid,ask,currency:'USD',sourceAt,receivedAt:Date.now(),timestampVerified:true,status:'OBSERVADO'};
  };
  return Promise.all([kraken,coinbase].map(async f=>{try{return await f();}catch{return {source:f===kraken?'Kraken':'Coinbase spot',status:'UNAVAILABLE',error:'Fuente spot no disponible',receivedAt:Date.now()};}}));
}
// Retained as a pure historical-book utility. No market API uses it.
export function bestBook(book) {
  const levels=xs=>(xs??[]).map(x=>({price:probability(x.price),size:numeric(x.size)})).filter(x=>x.price!==null&&x.size>0);
  const bids=levels(book?.bids).sort((a,b)=>b.price-a.price),asks=levels(book?.asks).sort((a,b)=>a.price-b.price);
  const bid=bids[0]?.price??null,ask=asks[0]?.price??null;
  if(bid!==null&&ask!==null&&bid>ask)throw new Error('Libro cruzado');
  return {bid,ask,depthAtBid:bids[0]?.size??null,depthAtAsk:asks[0]?.size??null,mid:bid!==null&&ask!==null?(bid+ask)/2:null,sourceAt:numeric(book?.timestamp),minOrderSize:numeric(book?.min_order_size)};
}
export function validateSnapshot(data,horizon,now=Date.now()) {
  const span=horizon*60000;
  if(!FRAMES[horizon]||data?.timeframe!==FRAMES[horizon]||!Number.isFinite(data.asOf)||!Number.isFinite(data.expiresAt)||!Number.isFinite(data.windowStart)||data.windowStart%span!==0||data.windowEnd!==data.windowStart+span||data.asOf<data.windowStart||data.asOf>=data.windowEnd||data.asOf>now+5000||now-data.asOf>120000||data.expiresAt<=now||data.expiresAt<=data.asOf||data.expiresAt>Math.min(data.windowEnd,data.asOf+45000))throw new Error('Snapshot canónico inválido o vencido');
  if(!Array.isArray(data.assets)||data.assets.length!==6||new Set(data.assets.map(r=>r.symbol)).size!==6||data.assets.some(r=>!ASSETS.includes(r.symbol)||!Array.isArray(r.venues)||r.research?.contractProbability!==null||r.research?.calibrated!==false))throw new Error('Contrato de datos canónico incompatible');
  return data;
}
export async function canonicalSnapshot(horizon,now=Date.now(),fetcher=fetch,directReader=null) {
  if(!FRAMES[horizon])throw new Error('Horizonte inválido');
  const key=String(horizon),old=snapshots.get(key);
  if(fetcher===fetch&&old&&now-old.readAt<12000&&old.value.expiresAt>now&&old.value.windowEnd>now)return old.value;
  if(fetcher===fetch&&pending.has(key))return pending.get(key);
  const work=(async()=>{
    let raw;
    try{raw=await publicJson(`${CANONICAL_API}/api/snapshot?tf=${FRAMES[horizon]}`,fetcher);raw={...raw,transport:'CANONICAL_APPDEPLOY',archiveWriterEnabled:null};}
    catch(error){
      const message=String(error?.message??'');
      const explicitStatus=message.match(/HTTP (\d{3})/)?.[1];
      const permitted=explicitStatus==='402'||/^5\d\d$/.test(explicitStatus??'')||(!explicitStatus&&['TypeError','TimeoutError','AbortError'].includes(error?.name));
      if(!permitted||(fetcher!==fetch&&!directReader))throw error;
      const reader=directReader??(await import('./public-web-snapshot.mjs')).publicWebSnapshot;
      raw=await reader(horizon);
      raw={...raw,transport:'DIRECT_PUBLIC_HTML_RSC',archiveState:'LIVE_VIEW_ONLY',archiveWriterEnabled:false,upstreamAvailability:{state:'UNAVAILABLE',httpStatus:explicitStatus?Number(explicitStatus):null,note:'Servicio canónico inaccesible. Esta consulta lee fuentes públicas distintas; no modifica el cron.'}};
    }
    const data=validateSnapshot(raw,horizon,fetcher===fetch?Date.now():now);
    if(fetcher===fetch)snapshots.set(key,{readAt:Date.now(),value:data});return data;
  })();
  if(fetcher===fetch)pending.set(key,work);
  try{return await work;}finally{if(fetcher===fetch)pending.delete(key);}
}
const emptyBook=()=>({bid:null,ask:null,mid:null,sourceAt:null,depthAtAsk:null,depthAtBid:null,minOrderSize:null});
export function canonicalMarket(snapshot,asset,horizon,provider,now=Date.now()) {
  const row=snapshot.assets.find(r=>r.symbol===asset);
  if(!row)throw new Error('Activo ausente del snapshot');
  const match=provider==='POLYMARKET'?'Polymarket':provider==='PREDICT'?'Predict':'Coinbase';
  const q=row.venues.find(v=>v.name===match||provider==='KALSHI'&&v.name?.startsWith(match));
  const stale=now>=snapshot.expiresAt||now>=snapshot.windowEnd;
  const base={provider,venue:provider==='KALSHI'?'Coinbase · Kalshi (página pública)':match,asset,horizon,status:q?.status??'UNAVAILABLE',id:q?.contractId??null,title:q?.contractId??'Contrato sin verificar',startAt:q?.windowStart??null,expiresAt:q?.windowEnd??snapshot.windowEnd,receivedAt:q?.receivedAt??null,requestedAt:snapshot.serverReceivedAt??null,asOf:snapshot.asOf,snapshotExpiresAt:snapshot.expiresAt,url:q?.marketUrl??null,reference:q?.reference??null,rules:q?.rules??null,resolutionSource:q?.resolutionSource??null,quoteAt:null,sourceAt:null,up:emptyBook(),down:emptyBook(),publishedUp:null,publishedDown:null,pMarket:null,pMarketKind:q?.priceKind??'No disponible',contractProbability:null,calibrated:false,classification:'DATA INSUFFICIENT',executionEnabled:false,feeSchedule:null,feesEnabled:null,sourcePolicy:'PUBLIC_HTML_RSC_VIA_CANONICAL_MONEY',reason:q?.note??'Fuente no disponible',error:q?.up===null?q?.note:null,spec:{asset,quoteUnit:q?.referenceUnit??null,startAt:q?.windowStart??null,endAt:q?.windowEnd??null,referenceExact:q?.reference===null||q?.reference===undefined?null:String(q.reference),oracleProvider:null,oracleFeedId:q?.resolutionSource??null,priceStatistic:null,operator:null,tiePayout:null}};
  // Published HTML indicators have no verified source tick or executable book.
  if(stale)base.status='STALE';
  if(q&&numeric(q.up)!==null&&q.up>=0&&q.up<=100&&numeric(q.down)!==null&&q.down>=0&&q.down<=100&&q.contractId&&q.windowStart===snapshot.windowStart&&q.windowEnd===snapshot.windowEnd){
    base.publishedUp=q.up;base.publishedDown=q.down;base.pMarket=q.up/100;
    if(!stale)base.status='PUBLICADO';
  }
  base.complementDerived=provider==='PREDICT';
  return base;
}
export function researchForecast(research,horizon,snapshot,now=Date.now()) {
  const valid=Number.isFinite(research?.validUntil)&&now<research.validUntil&&now<snapshot.expiresAt&&now<snapshot.windowEnd;
  const p=valid&&probability(research?.pUp)!==null?research.pUp:null;
  return {strategyId:'MONEY_FIXED_WINDOW_ANALOG_PAPER_V1',version:'1.1.0',source:'Kraken USD',horizon,p,direction:valid?research?.side??'WAIT':'WAIT',origin:research?.origin??null,target:research?.target??snapshot.windowEnd,validUntil:research?.validUntil??null,reference:research?.reference??null,medianPrice:valid?research?.median??null:null,priceBand:valid?research?.priceBand??[null,null]:[null,null],interval:valid?research?.intervalUp??[null,null]:[null,null],trainCount:research?.trainingCount??0,samples:research?.samples??0,flatFrequency:research?.flatFrequency??null,reason:valid?research?.reason??'Datos insuficientes':'Estimación suspendida: lectura o información cerrada vencida.',redTeam:'Semejanza histórica sin calibración, sin equivalencia contractual ni costes verificados.',invalidation:'Vela abierta, información vencida, huecos, referencia exacta ausente o contrato no verificado.',recommendation:'WAIT',contractProbability:null,calibrated:false,executionEnabled:false,classification:p===null?'DATA INSUFFICIENT':'WATCH',modelKind:'Pspot experimental; no probabilidad de ganar el contrato'};
}
export async function canonicalDayPlan(asset,horizon,date,fetcher=fetch) {
  if(!ASSETS.includes(asset)||!FRAMES[horizon]||!/^20\d\d-\d\d-\d\d$/.test(date)||!Number.isFinite(Date.parse(date+'T00:00:00Z'))||new Date(date+'T00:00:00Z').toISOString().slice(0,10)!==date)throw new Error('Parámetros inválidos');
  const p=await publicJson(`${CANONICAL_API}/api/dayplan?asset=${asset}&tf=${FRAMES[horizon]}&date=${date}`,fetcher);
  if(p?.symbol!==asset||p?.timeframe!==FRAMES[horizon]||p?.date!==date||!Array.isArray(p.calendar)||p.calendar.length!==1440/horizon)throw new Error('Archivo canónico incompatible');
  const beginning=Date.parse(date+'T00:00:00-06:00');
  for(const [index,c] of p.calendar.entries()){if(c.start!==beginning+index*horizon*60000||c.end!==c.start+horizon*60000)throw new Error('Ventana de archivo inválida');if(c.capture&&(!Number.isFinite(c.capture.asOf)||c.capture.asOf<c.start||c.capture.asOf>=c.end||c.capture.asOf>p.asOf))throw new Error('Captura fuera de ventana');}
  return p;
}
export async function polymarket(asset,horizon,now=Date.now(),fetcher=fetch){return canonicalMarket(await canonicalSnapshot(horizon,now,fetcher),asset,horizon,'POLYMARKET',now);}
export async function kalshi(asset,horizon,now=Date.now(),fetcher=fetch){return canonicalMarket(await canonicalSnapshot(horizon,now,fetcher),asset,horizon,'KALSHI',now);}
export async function getMarkets(asset,horizon,now=Date.now(),fetcher=fetch){
  if(!ASSETS.includes(asset)||!FRAMES[horizon])throw new Error('Activo/horizonte inválidos');
  try{const s=await canonicalSnapshot(horizon,now,fetcher);return ['POLYMARKET','PREDICT','KALSHI'].map(p=>canonicalMarket(s,asset,horizon,p,now));}
  catch(e){return ['POLYMARKET','PREDICT','KALSHI'].map(provider=>({provider,venue:provider,status:'UNAVAILABLE',classification:'DATA INSUFFICIENT',error:e.message,contractProbability:null,calibrated:false,executionEnabled:false,receivedAt:Date.now()}));}
}
