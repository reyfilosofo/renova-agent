import { journal } from '@/lib/persistence';
export const dynamic = 'force-dynamic';
export async function GET(request:Request) {
  const q = new URL(request.url).searchParams, asset=q.get('asset')??'ALL',h=Number(q.get('horizon')??0);
  const offset=Number(q.get('offset')??0),limit=Number(q.get('limit')??100);
  if(![0,5,15,60].includes(h)||!Number.isInteger(offset)||offset<0||offset>1000000||!Number.isInteger(limit)||limit<1||limit>500)return Response.json({error:'Paginación inválida'},{status:400});
  try{return Response.json(await journal(asset,h,offset,limit),{headers:{'Cache-Control':'no-store'}});}
  catch{return Response.json({records:[],summary:[],observations:0,error:'No se pudo leer el archivo persistente',hasMore:false},{status:503});}
}
