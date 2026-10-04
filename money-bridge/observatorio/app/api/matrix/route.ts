import { marketMatrix } from '@/lib/market-matrix';
export const dynamic='force-dynamic';
export async function GET(){
  try{return Response.json(await marketMatrix(),{headers:{'Cache-Control':'no-store'}});}
  catch{return Response.json({rows:[],error:'No se pudo consultar/respaldar la matriz de fuentes',executionEnabled:false},{status:503,headers:{'Cache-Control':'no-store'}});}
}
