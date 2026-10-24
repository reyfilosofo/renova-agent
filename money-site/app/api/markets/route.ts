import { ASSETS, getMarkets } from '@/lib/market-data.mjs';
export const dynamic = 'force-dynamic';
const cache = new Map<string,{at:number;value:any}>();
export async function GET(request: Request) {
  const q = new URL(request.url).searchParams, asset=q.get('asset')??'BTC', horizon=Number(q.get('horizon')??5);
  if(!ASSETS.includes(asset)||![5,15,60].includes(horizon))return Response.json({error:'Filtro inválido'},{status:400});
  const key=`${asset}:${horizon}`,now=Date.now(),old=cache.get(key);
  if(old&&now-old.at<10000)return Response.json(old.value,{headers:{'Cache-Control':'no-store'}});
  const markets=await getMarkets(asset,horizon,now);
  const value={asset,horizon,markets,receivedAt:Date.now()};cache.set(key,{at:now,value});
  return Response.json(value,{headers:{'Cache-Control':'no-store'}});
}
