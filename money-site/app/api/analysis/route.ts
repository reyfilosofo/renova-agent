import {ASSETS,canonicalSnapshot,researchForecast,CANONICAL_API} from '@/lib/market-data.mjs';
export const dynamic='force-dynamic';
export async function POST(request:Request){
  const origin=request.headers.get('origin');
  if(origin&&origin!==new URL(request.url).origin)return Response.json({error:'Origen inválido'},{status:403});
  let asset:string;
  try{const text=await request.text();if(text.length>1024)throw new Error();asset=JSON.parse(text).asset;}catch{return Response.json({error:'Solicitud inválida'},{status:400});}
  if(!ASSETS.includes(asset))return Response.json({error:'Activo inválido'},{status:400});
  const results=await Promise.all([5,15,60].map(async horizon=>{try{return {horizon,snapshot:await canonicalSnapshot(horizon)};}catch(e:any){return {horizon,error:String(e.message).slice(0,180)};}}));
  const now=Date.now(),successful=results.filter(r=>r.snapshot),latest=successful.at(-1)?.snapshot,row=latest?.assets.find((a:any)=>a.symbol===asset);
  const forecasts=results.map(r=>r.snapshot?researchForecast(r.snapshot.assets.find((a:any)=>a.symbol===asset)?.research,r.horizon,r.snapshot,now):{horizon:r.horizon,p:null,direction:'WAIT',contractProbability:null,calibrated:false,classification:'DATA INSUFFICIENT',recommendation:'WAIT',reason:r.error,source:'Kraken USD',modelKind:'Pspot experimental; no probabilidad contractual'});
  return Response.json({asset,receivedAt:now,forecasts,source:'Kraken USD',candles:(row?.priceHistory??[]).map((c:any)=>({t:c.at-300000,c:c.price,confirmed:true})),candleCount:row?.priceHistory?.length??0,historySourceUrl:CANONICAL_API+'/api/snapshot',historyReceivedAt:latest?.asOf??null,executionEnabled:false,contractProbability:null,calibrated:false,mode:'PAPER',modelKind:'Pspot experimental',sourcePolicy:'PUBLIC_HTML_RSC_VIA_CANONICAL_MONEY',transport:latest?.transport??'UNAVAILABLE',upstreamAvailability:latest?.upstreamAvailability??null,archive:{status:latest?.archiveWriterEnabled===false?'LIVE_VIEW_ONLY':'READ_ONLY',writer:'AppDeploy collectMoney cron; estado remoto no supuesto',note:'La visita no escribe pronósticos ni reconstruye capturas.'},error:successful.length?null:'Backend canónico no disponible; ninguna estimación vigente.'},{status:successful.length?200:503,headers:{'Cache-Control':'no-store'}});
}
