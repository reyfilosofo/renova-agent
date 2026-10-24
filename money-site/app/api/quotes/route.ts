import { ASSETS, getQuotes } from '@/lib/market-data.mjs';
export const dynamic = 'force-dynamic';
const cache = new Map<string,{at:number;value:any}>();
export async function GET(request: Request) {
  const asset = new URL(request.url).searchParams.get('asset') ?? 'BTC';
  if(!ASSETS.includes(asset))return Response.json({error:'Activo inválido'},{status:400});
  const previous=cache.get(asset);
  if(previous && Date.now()-previous.at<8000)return Response.json(previous.value,{headers:{'Cache-Control':'no-store'}});
  const quotes=await getQuotes(asset);
  const value={asset,quotes,receivedAt:Date.now()};cache.set(asset,{at:Date.now(),value});
  return Response.json(value,{headers:{'Cache-Control':'no-store'}});
}
