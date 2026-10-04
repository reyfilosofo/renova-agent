import { ASSETS } from '@/lib/market-data.mjs';
import { forecast } from '@/lib/model.mjs';
import { historyFor,recordAnalysis } from '@/lib/persistence';
import { marketMatrix } from '@/lib/market-matrix';
export const dynamic='force-dynamic';
export async function POST(request:Request){
  const origin=request.headers.get('origin');
  if(origin&&origin!==new URL(request.url).origin)return Response.json({error:'Origen inválido'},{status:403});
  if(Number(request.headers.get('content-length')??0)>1024)return Response.json({error:'Petición excesiva'},{status:413});
  const body=await request.text();if(body.length>1024)return Response.json({error:'Petición excesiva'},{status:413});
  const startedAt=Date.now();
  const assets=await Promise.all(ASSETS.map(async asset=>{
    try{
      const now=Date.now(),history=await historyFor(asset,now),forecasts=[5,15,60].map(h=>forecast(history.candles,h,now,history.source,5));
      const result={asset,receivedAt:now,source:history.source,forecasts,candleCount:history.candles.length,executionEnabled:false,mode:'PAPER'};
      return {asset,archive:await recordAnalysis(asset,result,history.candles),horizons:forecasts.map(f=>({horizon:f.horizon,origin:'origin' in f?f.origin:null,target:'target' in f?f.target:null,p:f.p,classification:f.classification}))};
    }catch{return {asset,status:'UNAVAILABLE',error:'Sin histórico/corte guardado verificable'};}
  }));
  let matrix:any;try{const m=await marketMatrix();matrix={cutId:m.cutId,archive:m.archive,observed:m.rows.reduce((n:number,r:any)=>n+r.markets.filter((x:any)=>x.status==='OBSERVADO').length,0)};}catch{matrix={status:'ERROR'};}
  return Response.json({startedAt,completedAt:Date.now(),assets,matrix,executionEnabled:false,
    note:'Corte real actual; no rellena ventanas pasadas ni genera precios futuros. Leer /api/daily y /api/history para verificar.'},{headers:{'Cache-Control':'no-store'}});
}
