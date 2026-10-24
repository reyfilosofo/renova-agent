import {ASSETS,canonicalSnapshot,canonicalMarket} from './market-data.mjs';
import {HORIZONS,currentWindow,perShareCost,semanticComparison} from './comparison.mjs';
let inFlight:Promise<any>|null=null;
const ACCESS_PATHS=[
  {name:'Polymarket',providers:['POLYMARKET'],state:'HTML/RSC público mediante MONEY canónico',costs:'Cuotas publicadas; tick, ask y coste final sin verificar.'},
  {name:'Predict.fun',providers:['PREDICT'],state:'HTML/RSC público; sin clave de API',costs:'DOWN es complemento derivado; costes sin verificar.'},
  {name:'Coinbase Predictions',providers:['KALSHI'],state:'Página pública; contrato no supuesto',costs:'Sin cotización ejecutable verificada.'},
  {name:'Base / MetaMask / Trust',providers:['POLYMARKET','PREDICT'],state:'Acceso o espejos; no confirmación independiente',costs:'Ruta y cotización final no verificadas.'}
];
async function buildMatrix(){
  const requestedAt=Date.now();
  const snapshots=await Promise.all(HORIZONS.map(async horizon=>{try{return {horizon,snapshot:await canonicalSnapshot(horizon)};}catch(e:any){return {horizon,error:String(e.message).slice(0,180)};}}));
  const completedAt=Date.now(),rows:any[]=[];
  for(const asset of ASSETS)for(const item of snapshots){
    const window=item.snapshot?{startAt:item.snapshot.windowStart,endAt:item.snapshot.windowEnd}:currentWindow(completedAt,item.horizon);
    const markets=['POLYMARKET','PREDICT','KALSHI'].map(provider=>{
      const m:any=item.snapshot?canonicalMarket(item.snapshot,asset,item.horizon,provider,completedAt):{provider,venue:provider,status:'UNAVAILABLE',error:item.error,contractProbability:null,calibrated:false,receivedAt:null};
      const expired=m.expiresAt!==undefined&&completedAt>=m.expiresAt;
      return {...m,costUp:perShareCost(m,'up'),costDown:perShareCost(m,'down'),freshness:{grade:expired?'EXPIRED':m.status==='PUBLICADO'?'UNKNOWN':m.status,label:expired?'VENCIDO':m.status==='PUBLICADO'?'PUBLICADO · TICK SIN VERIFICAR':m.status,sourceAgeMs:null}};
    });
    const p=markets[0],d=markets[1],semantic=semanticComparison(p,d);
    const publishedDifferencePp=p.status==='PUBLICADO'&&d.status==='PUBLICADO'&&p.publishedUp!==null&&d.publishedUp!==null?p.publishedUp-d.publishedUp:null;
    rows.push({asset,horizon:item.horizon,...window,markets,comparison:{semanticGrade:semantic.grade,timingGrade:'UNKNOWN',mismatches:semantic.mismatches,missing:semantic.missing,midpointDifferencePp:null,publishedDifferencePp,comparisonEnabled:false,executionEnabled:false,edge:null,contractProbability:null,note:'Diferencia publicada descriptiva; sin timestamp de tick ni equivalencia verificada.'}});
  }
  return {version:'1.1.0',cutId:'canonical-read:'+requestedAt,requestedAt,completedAt,requestSpanMs:completedAt-requestedAt,rows,validityEvaluatedAt:completedAt,predictConfigured:false,predictPublicWeb:true,predictCataloguePartial:null,accessPaths:ACCESS_PATHS,executionEnabled:false,contractProbability:null,sourcePolicy:'PUBLIC_HTML_RSC_VIA_CANONICAL_MONEY',transports:snapshots.map(s=>({horizon:s.horizon,transport:s.snapshot?.transport??'UNAVAILABLE',upstreamAvailability:s.snapshot?.upstreamAvailability??null})),archive:{status:snapshots.some(s=>s.snapshot?.archiveWriterEnabled===false)?'LIVE_VIEW_ONLY':'READ_ONLY',writer:'AppDeploy collectMoney cron; estado remoto no supuesto',note:'La vista pública no crea capturas. D1 histórico y archivo canónico se consultan por separado.'},warning:'HTML público: porcentajes PUBLICADO con hora del tick desconocida; sin libros ejecutables ni modelo contractual calibrado.'};
}
export async function marketMatrix(){if(inFlight)return inFlight;inFlight=buildMatrix();try{return await inFlight;}finally{inFlight=null;}}
