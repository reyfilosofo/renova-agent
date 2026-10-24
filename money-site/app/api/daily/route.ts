import {ASSETS,canonicalDayPlan,canonicalMarket} from '@/lib/market-data.mjs';
import {database} from '@/lib/persistence';
import {dailyGrid,dayBounds,localDay} from '@/lib/daily-plan.mjs';
export const dynamic='force-dynamic';
const memory=new Map<string,{at:number;value:any}>();
export async function GET(request:Request){
  const now=Date.now(),q=new URL(request.url).searchParams,day=q.get('date')??localDay(now),horizon=Number(q.get('horizon')??60);let bounds;
  try{bounds=dayBounds(day);if(![5,15,60].includes(horizon))throw new Error();}catch{return Response.json({error:'Fecha/horizonte inválidos'},{status:400});}
  const key=day+':'+horizon,old=memory.get(key);if(old&&now-old.at<12000)return Response.json(old.value,{headers:{'Cache-Control':'no-store'}});
  let legacy:any=null;
  try{const db=database();const [f,s]=await Promise.all([
    db.prepare("SELECT * FROM money_forecasts WHERE horizon=? AND origin>=? AND origin<? AND source='Kraken USD' ORDER BY created ASC LIMIT 5000").bind(horizon,bounds.startAt,bounds.endAt).all<any>(),
    db.prepare('SELECT * FROM money_market_snapshots WHERE horizon=? AND window_start>=? AND window_start<? ORDER BY created ASC LIMIT 5000').bind(horizon,bounds.startAt,bounds.endAt).all<any>()
  ]);legacy={...dailyGrid(day,horizon,ASSETS,f.results,s.results,now),captures:s.results.length,provenance:'D1 histórico del observatorio; estrategia anterior, separado del archivo canónico.'};}catch{legacy={status:'UNAVAILABLE',note:'D1 histórico no accesible; no se modifica ni elimina.'};}
  const plans=await Promise.all(ASSETS.map(async asset=>{try{return {asset,plan:await canonicalDayPlan(asset,horizon,day)};}catch(e:any){return {asset,error:String(e.message).slice(0,180)};}}));
  const span=horizon*60000;let captures=0,forecastedCells=0;
  const rows=Array.from({length:1440/horizon},(_,i)=>{const startAt=bounds.startAt+i*span,endAt=startAt+span;return {startAt,endAt,state:now<startAt?'FUTURE':now>=endAt?'PAST':'CURRENT',assets:plans.map(p=>{
    const entry=p.plan?.calendar.find((c:any)=>c.start===startAt&&c.end===endAt),capture=entry?.capture,observed=capture&&capture.asOf<=now&&capture.asOf>=startAt&&capture.asOf<endAt?capture:null,row=observed?.row??observed?.rows?.find((r:any)=>r.symbol===p.asset),research=row?.research;
    const validResearch=research&&typeof research.pUp==='number'&&Number.isFinite(research.pUp)&&research.pUp>=0&&research.pUp<=1&&research.contractProbability===null&&research.calibrated===false;
    const forecast=observed&&validResearch?{id:`canonical:${p.asset}:${horizon}:${startAt}`,issuedAt:observed.asOf,origin:research.origin,target:endAt,reference:research.reference,probability:research.pUp,side:research.side,medianPrice:research.median,priceBand:research.priceBand,outcome:null,finalPrice:null,source:'Kraken USD',strategy:research.strategy,version:'1.1.0',calibrated:false,contractProbability:null,recommendation:'WAIT'}:null;
    if(forecast)forecastedCells++;
    let marketSnapshot:any=null;
    if(observed&&row){captures++;const snapshot={asOf:observed.asOf,windowStart:startAt,windowEnd:endAt,expiresAt:endAt,assets:[row]};marketSnapshot={created:observed.asOf,provenance:'AppDeploy collectMoney cron',historical:true,markets:['POLYMARKET','PREDICT','KALSHI'].map(provider=>canonicalMarket(snapshot,p.asset,horizon,provider,observed.asOf))};}
    return {asset:p.asset,forecast,marketSnapshot,state:now<startAt?'PENDIENTE DE EMISIÓN':observed?'CAPTURADO':p.error?'ARCHIVO NO DISPONIBLE':'SIN CAPTURA',error:p.error??null};
  })};});
  const available=plans.filter(p=>p.plan).length;
  const value={...bounds,horizon,rows,generatedAt:Date.now(),expectedCells:rows.length*ASSETS.length,forecastedCells,captures,collection:'AppDeploy collectMoney cron; esta pantalla solo lee. Verificar continuidad por capturas existentes.',forecastStrategy:'MONEY_FIXED_WINDOW_ANALOG_PAPER_V1',forecastVersion:'1.1.0',executionEnabled:false,contractProbability:null,sourcePolicy:'PUBLIC_HTML_RSC_VIA_CANONICAL_MONEY',availableAssets:available,legacyLocalArchive:legacy,note:'Archivo canónico separado de D1 histórico. Las ausencias permanecen vacías y no se generan pronósticos retrospectivos.'};
  if(available)memory.set(key,{at:Date.now(),value});return Response.json(value,{status:available||legacy?.rows?200:503,headers:{'Cache-Control':'no-store'}});
}
