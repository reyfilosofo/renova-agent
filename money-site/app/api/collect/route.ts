import {ASSETS,canonicalDayPlan} from '@/lib/market-data.mjs';
import {localDay} from '@/lib/daily-plan.mjs';
export const dynamic='force-dynamic';
export async function POST(request:Request){
  const origin=request.headers.get('origin');
  if(origin&&origin!==new URL(request.url).origin)return Response.json({error:'Origen inválido'},{status:403});
  const body=await request.text();if(body.length>1024)return Response.json({error:'Petición excesiva'},{status:413});
  const now=Date.now(),date=localDay(now),cut=Math.floor(now/300000)*300000;
  const assets=await Promise.all(ASSETS.map(async asset=>{try{const plan=await canonicalDayPlan(asset,5,date);return {asset,state:plan.calendar.find((c:any)=>c.start===cut)?.capture?'EXISTENTE':'PENDIENTE',inserted:0};}catch{return {asset,state:'UNAVAILABLE',inserted:0};}}));
  return Response.json({startedAt:now,completedAt:Date.now(),cut,assets,inserted:0,writer:'AppDeploy collectMoney cron',mode:'READ_ONLY',manualCaptureEnabled:false,executionEnabled:false,note:'Solo comprueba el archivo. No crea capturas ni sustituye al recolector programado.'},{headers:{'Cache-Control':'no-store'}});
}
