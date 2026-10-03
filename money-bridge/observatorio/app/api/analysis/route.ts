import { ASSETS } from '@/lib/market-data.mjs';
import { forecast } from '@/lib/model.mjs';
import { historyFor, recordAnalysis } from '@/lib/persistence';
export const dynamic = 'force-dynamic';
export async function POST(request: Request) {
  const origin = request.headers.get('origin');
  if (origin && origin !== new URL(request.url).origin) return Response.json({error:'Origen inválido'},{status:403});
  if (Number(request.headers.get('content-length') ?? 0) > 1024) return Response.json({error:'Petición excesiva'},{status:413});
  let asset: string;
  try { const text = await request.text(); if(text.length>1024)throw new Error(); asset=JSON.parse(text).asset; }
  catch { return Response.json({error:'Solicitud inválida'},{status:400}); }
  if (!ASSETS.includes(asset)) return Response.json({error:'Activo inválido'},{status:400});
  const now = Date.now();
  try {
    const history = await historyFor(asset,now);
    const forecasts = [5,15,60].map(h => forecast(history.candles,h,now,history.source,5));
    const result:any = { asset, receivedAt: now, forecasts, source: history.source,
      candles: history.candles.slice(-120).map((c:any) => ({t:c.t,c:c.c})), candleCount: history.candles.length,
      historySourceUrl: history.sourceUrl, historyReceivedAt: history.receivedAt,
      cache: history.cache, executionEnabled: false, mode:'PAPER' };
    try { result.archive = await recordAnalysis(asset,result,history.candles); }
    catch { result.archive = {status:'ERROR',note:'No se pudo respaldar este corte. No presentar como registrado.'}; }
    return Response.json(result,{headers:{'Cache-Control':'no-store'}});
  } catch(e:any) {
    return Response.json({ asset, receivedAt:now, source:'Kraken USD', forecasts:[5,15,60].map(h => ({horizon:h,p:null,contractProbability:null,calibrated:false,classification:'DATA INSUFFICIENT',reason:e.message})), candles:[],archive:{status:'SIN DATOS'},error:e.message },{headers:{'Cache-Control':'no-store'}});
  }
}
