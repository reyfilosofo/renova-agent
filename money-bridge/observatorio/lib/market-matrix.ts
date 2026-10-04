import { env } from 'cloudflare:workers';
import { ASSETS, polymarket, kalshi } from './market-data.mjs';
import { predictCatalogue, predictMarket } from './predict.mjs';
import { HORIZONS, currentWindow, perShareCost, evaluateMatrixTiming, ACCESS_PATHS } from './comparison.mjs';
import { cachedPublicData, cachePublicData, recordMarketMatrix } from './persistence';
let inFlight:Promise<any>|null=null;
const kalshiMemory=new Map<string,{at:number;value:any}>();
let kalshiCooldownUntil=0;
async function safe(provider:string,fn:()=>Promise<any>) {
  try{return await fn();}catch(e:any){return {provider,venue:provider,status:'UNAVAILABLE',error:String(e.message??'Fuente no disponible').slice(0,240),contractProbability:null,receivedAt:Date.now()};}
}
async function kalshiLimited(asset:string,horizon:number,now:number) {
  if(horizon!==15)return kalshi(asset,horizon,now);
  const old=kalshiMemory.get(asset);
  if(old&&now-old.at<60000&&old.value.expiresAt>now)return old.value;
  if(now<kalshiCooldownUntil)return {provider:'KALSHI',venue:'Kalshi / Coinbase Predictions',status:'RATE_LIMIT',error:'Límite de fuente observado; se respeta una pausa de60s, sin evasión.',contractProbability:null};
  const value=await safe('KALSHI',()=>kalshi(asset,horizon,now));
  if(String(value.error??'').includes('429'))kalshiCooldownUntil=Date.now()+60000;
  kalshiMemory.set(asset,{at:Date.now(),value});
  return value;
}
async function buildMatrix() {
  const requestedAt=Date.now(),key=env.PREDICT_API_KEY??null;
  let catalogue:any;
  if(key){
    const old=await cachedPublicData('predict_catalog');
    if(old&&requestedAt-old.updated<60000)catalogue=old.value;
    else {
      catalogue=await safe('PREDICT',()=>predictCatalogue(key));
      if(catalogue.categories)await cachePublicData('predict_catalog',Date.now(),catalogue);
    }
  }else catalogue=await predictCatalogue(null);
  const pairs=ASSETS.flatMap(asset=>HORIZONS.map(horizon=>({asset,horizon}))),rows:any[]=[];
  // Bound upstream concurrency; do not fire all books at once or equate
  // grouped requests with exchange-wide simultaneous prices.
  for(let offset=0;offset<pairs.length;offset+=4){
    const chunk=await Promise.all(pairs.slice(offset,offset+4).map(async({asset,horizon})=>{
      const window=currentWindow(requestedAt,horizon);
      const markets=await Promise.all([
        safe('POLYMARKET',()=>polymarket(asset,horizon,requestedAt)),
        safe('PREDICT',()=>predictMarket(asset,horizon,requestedAt,catalogue,key)),
        kalshiLimited(asset,horizon,requestedAt)
      ]);
      return {asset,horizon,...window,markets};
    }));
    rows.push(...chunk);
  }
  const completedAt=Date.now();
  for(const row of rows)for(const m of row.markets){m.costUp=perShareCost(m,'up');m.costDown=perShareCost(m,'down');}
  const matrix:any={version:'0.2.0',cutId:'matrix:'+requestedAt,requestedAt,completedAt,requestSpanMs:completedAt-requestedAt,
    rows:evaluateMatrixTiming(rows,completedAt),validityEvaluatedAt:completedAt,predictConfigured:!!key,predictCataloguePartial:catalogue.partial??null,accessPaths:ACCESS_PATHS,executionEnabled:false,
    warning:'Observación agrupada REST, no sincronía tick a tick. Midpoint no es ask; distintas reglas no son arbitraje. Coste final de wallets no verificado.'};
  try{matrix.archive=await recordMarketMatrix(matrix);}catch{matrix.archive={status:'ERROR',note:'La captura no quedó respaldada; no afirmar registro.'};}
  await cachePublicData('matrix',completedAt,matrix);
  return matrix;
}
export async function marketMatrix() {
  const now=Date.now(),old=await cachedPublicData('matrix');
  if(old&&now-old.updated<12000&&old.value.predictConfigured===!!env.PREDICT_API_KEY&&old.value.rows.every((r:any)=>r.endAt>now))return {...old.value,rows:evaluateMatrixTiming(old.value.rows,now),validityEvaluatedAt:now,cache:true};
  if(inFlight)return inFlight;
  inFlight=buildMatrix();
  try{return await inFlight;}finally{inFlight=null;}
}
