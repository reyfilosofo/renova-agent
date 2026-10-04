import { ASSETS, publicJson, bestBook } from './market-data.mjs';
import { currentWindow } from './comparison.mjs';
const finite = x => x !== null && x !== undefined && x !== '' && Number.isFinite(Number(x)) ? Number(x) : null;
export function parsePredictBook(raw, marketId) {
  if (raw?.success !== true || String(raw.data?.marketId) !== String(marketId)) throw new Error('Libro Predict no corresponde al contrato');
  const data=raw.data;
  const levels = xs => {
    if (!Array.isArray(xs)) throw new Error('Niveles de libro inválidos');
    return xs.map(x => { if(!Array.isArray(x) || x.length<2)throw new Error('Nivel inválido'); return {price:x[0],size:x[1]}; });
  };
  const yes=bestBook({bids:levels(data.bids),asks:levels(data.asks),timestamp:data.updateTimestampMs});
  // Avoid exposing binary floating-point artefacts; preserve up to 12 decimal
  // places without inferring a coarser tick size or changing the source book.
  const complement=p=>p===null?null:Number((1-p).toFixed(12));
  const no={bid:complement(yes.ask),ask:complement(yes.bid),
    mid:complement(yes.mid),depthAtAsk:yes.depthAtBid,depthAtBid:yes.depthAtAsk,sourceAt:yes.sourceAt};
  return {yes,no};
}
export function selectPredictCategory(categories, asset, horizon, now) {
  const window=currentWindow(now,horizon);
  return categories.find(c => {
    const crypto=c.variantDetails?.crypto;
    const symbol=String(crypto?.priceFeedSymbol??'').toUpperCase().replace(/[-_]/g,'/');
    const symbolAsset=symbol.split('/')[0];
    return c.status==='OPEN' && c.isVisible!==false && c.marketVariant==='CRYPTO_UP_DOWN' && symbolAsset===asset &&
      Date.parse(c.startsAt)===window.startAt && Date.parse(c.endsAt)===window.endAt && typeof c.slug==='string' && /^[a-z0-9][a-z0-9-]{1,160}$/.test(c.slug);
  }) ?? null;
}
export async function predictCatalogue(apiKey, fetcher=fetch) {
  if(!apiKey)return {status:'NO CONFIGURADO',categories:[],partial:false,error:'Predict Mainnet requiere una clave oficial de API en el servidor; sin datos de testnet ni capturas como cotización.'};
  const categories=[], seen=new Set();let cursor=null,partial=false;
  for(let page=0;page<4;page++){
    const q=new URLSearchParams({first:'100',status:'OPEN',marketVariant:'CRYPTO_UP_DOWN',sort:'PUBLISHED_AT_DESC'});
    if(cursor)q.set('after',cursor);
    const j=await publicJson('https://api.predict.fun/v1/categories?'+q,fetcher,apiKey);
    if(j.success!==true || !Array.isArray(j.data))throw new Error('Catálogo Predict inválido');
    categories.push(...j.data);
    cursor=typeof j.cursor==='string'&&j.cursor?j.cursor:null;
    if(!cursor)break;
    if(seen.has(cursor))throw new Error('Cursor repetido de Predict');seen.add(cursor);
    if(page===3)partial=true;
  }
  return {status:'CATÁLOGO OBSERVADO',categories,partial,receivedAt:Date.now()};
}
export async function predictMarket(asset,horizon,now,catalogue,apiKey,fetcher=fetch){
  const window=currentWindow(now,horizon),base={provider:'PREDICT',venue:'Predict.fun / Binance Wallet',asset,horizon,startAt:window.startAt,expiresAt:window.endAt,contractProbability:null,calibrated:false,classification:'DATA INSUFFICIENT'};
  if(!ASSETS.includes(asset))throw new Error('Activo inválido');
  if(!apiKey)return {...base,status:'NO CONFIGURADO',error:catalogue?.error??'Falta clave oficial de lectura API Predict.'};
  if(!catalogue || !Array.isArray(catalogue.categories))return {...base,status:'UNAVAILABLE',error:catalogue?.error??'Catálogo no disponible'};
  const c=selectPredictCategory(catalogue.categories,asset,horizon,now);
  if(!c)return {...base,status:'NO VERIFICADO',error:catalogue.partial?'No identificado en catálogo parcial; no afirmar inexistencia.':'Sin contrato vigente identificado para activo y ventana; no afirmar inexistencia.'};
  const m=(c.markets??[]).find(x=>x.categorySlug===c.slug && x.tradingStatus==='OPEN' && x.isVisible!==false && x.marketVariant==='CRYPTO_UP_DOWN');
  if(!m || !m.id || !m.description || !Array.isArray(m.outcomes) || m.outcomes.length!==2)throw new Error('Contrato Predict incompleto');
  const names=m.outcomes.map(x=>String(x.name).toLowerCase());
  // YES/NO alone does not certify that YES means UP. Fail closed until explicit
  // outcome labels are returned; no assumptions from screenshots or indexSet.
  if(!names.includes('up')||!names.includes('down'))return {...base,status:'NO VERIFICADO',error:'Mapeo UP/DOWN de outcomes no verificado en API Predict.'};
  const indexSets=m.outcomes.map(x=>Number(x.indexSet));
  if(indexSets.filter(x=>x===1).length!==1||indexSets.filter(x=>x===2).length!==1)throw new Error('Mapeo YES/NO no verificado; indexSets deben ser1 y2 únicos');
  const yesIndex=indexSets.indexOf(1),yesIsUp=names[yesIndex]==='up';
  const requestedAt=Date.now(),book=parsePredictBook(await publicJson(`https://api.predict.fun/v1/markets/${encodeURIComponent(m.id)}/orderbook`,fetcher,apiKey),m.id);
  const up=yesIsUp?book.yes:book.no,down=yesIsUp?book.no:book.yes;
  const crypto=c.variantDetails.crypto,reference=finite(crypto.startPrice)>0?finite(crypto.startPrice):null;
  return {...base,status:'OBSERVADO',id:String(m.id),categoryId:String(c.id),slug:c.slug,title:m.title??c.title,rules:m.description,
    reference,spec:{asset,quoteUnit:String(crypto.priceFeedSymbol??'').split('/')[1]??null,startAt:window.startAt,endAt:window.endAt,
      referenceExact:reference===null?null:String(crypto.startPrice),oracleProvider:crypto.priceFeedProvider??null,oracleFeedId:crypto.priceFeedId??null,
      priceStatistic:null,averagingWindowSeconds:null,rounding:null,operator:null,tiePayout:null,voidPayout:null,payoutCurrency:null,payoutAmount:1,rulesVersion:null},
    up,down,pMarket:up.mid,feeRateBps:finite(m.feeRateBps),decimalPrecision:m.decimalPrecision,
    requestedAt,receivedAt:Date.now(),resolutionSource:crypto.priceFeedProvider??null,
    pMarketKind:'Midpoint del libro oficial, UP/DOWN validados; NO derivado con precios complementarios de YES.',
    url:'https://predict.fun/market/'+c.slug,reason:'Reglas exactas y empate pueden diferir de Polymarket. Pmodelo contractual/coste final no verificados.'};
}
