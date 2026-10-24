import {canonicalSnapshot,canonicalMarket} from './market-data.mjs';
// Legacy API/key entry points are intentionally inert; no credential is read or sent.
export function parsePredictBook(){throw new Error('API de libros deshabilitada: MONEY utiliza HTML público.');}
export function selectPredictCategory(){return null;}
export async function predictCatalogue(){return {status:'PUBLIC_WEB',categories:[],partial:null,sourcePolicy:'PUBLIC_HTML_RSC_VIA_CANONICAL_MONEY',error:null};}
export async function predictMarket(asset,horizon,now=Date.now(),_catalogue=null,_unusedKey=null,fetcher=fetch){
  return canonicalMarket(await canonicalSnapshot(horizon,now,fetcher),asset,horizon,'PREDICT',now);
}
