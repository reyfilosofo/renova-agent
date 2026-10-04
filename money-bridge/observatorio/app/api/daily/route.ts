import { ASSETS } from '@/lib/market-data.mjs';
import { database } from '@/lib/persistence';
import { dailyGrid,dayBounds,localDay } from '@/lib/daily-plan.mjs';
export const dynamic='force-dynamic';
export async function GET(request:Request){
  const now=Date.now(),q=new URL(request.url).searchParams,day=q.get('date')??localDay(now),horizon=Number(q.get('horizon')??60);
  let bounds;
  try{bounds=dayBounds(day);if(![5,15,60].includes(horizon))throw new Error();}
  catch{return Response.json({error:'Fecha/horizonte inválidos'},{status:400});}
  try{
    const db=database();
    const [f,s]=await Promise.all([
      db.prepare("SELECT * FROM money_forecasts WHERE horizon=? AND origin>=? AND origin<? AND source='Kraken USD' AND json_extract(payload,'$.strategyId')='MONEY_SPOT_ANALOG_V1_PAPER' AND json_extract(payload,'$.version')='0.1.0' ORDER BY created ASC LIMIT 5000").bind(horizon,bounds.startAt,bounds.endAt).all<any>(),
      db.prepare('SELECT * FROM money_market_snapshots WHERE horizon=? AND window_start>=? AND window_start<? ORDER BY created ASC LIMIT 5000').bind(horizon,bounds.startAt,bounds.endAt).all<any>()
    ]);
    const result=dailyGrid(day,horizon,ASSETS,f.results,s.results,now);
    return Response.json({...result,captures:s.results.length,collection:'Página visible; cortes desatendidos solo si hay tarea soportada activada.',
      forecastStrategy:'MONEY_SPOT_ANALOG_V1_PAPER',forecastVersion:'0.1.0',executionEnabled:false},{headers:{'Cache-Control':'no-store'}});
  }catch{return Response.json({error:'No se pudo leer el calendario persistente'},{status:503});}
}
