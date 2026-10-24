import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {ASSETS,CANONICAL_API,publicJson,canonicalSnapshot,canonicalMarket,canonicalDayPlan,getHistory,researchForecast,getMarkets,validateSnapshot} from '../lib/market-data.mjs';
import {predictCatalogue,predictMarket,parsePredictBook} from '../lib/predict.mjs';
const now=Date.parse('2026-10-24T01:02:00Z');
function fixture(h=5){
 const start=Math.floor(now/(h*60000))*h*60000,end=start+h*60000;
 return {version:'1.1.0',timeframe:h===60?'1h':h+'m',asOf:now-1000,serverTime:now,serverReceivedAt:now-1200,windowStart:start,windowEnd:end,expiresAt:now+44000,assets:ASSETS.map(symbol=>({symbol,priceHistory:[{at:start,price:100}],research:{strategy:'MONEY_FIXED_WINDOW_ANALOG_PAPER_V1',pUp:.7,side:'UP',origin:start,target:end,validUntil:Math.min(end,start+300000),reference:100,median:101,priceBand:[99,102],intervalUp:[.53,.83],samples:30,trainingCount:100,contractProbability:null,calibrated:false,recommendation:'WAIT'},venues:['Polymarket','Predict','Coinbase · Kalshi'].map((name,index)=>({name,status:index===2?'NO_VERIFICADO':'PUBLICADO',up:index===2?null:70,down:index===2?null:index===0?39:30,contractId:index===2?null:name+':fixture',windowStart:start,windowEnd:end,receivedAt:now-1500,quoteAt:null,reference:null,referenceUnit:null,resolutionSource:null,rules:null,marketUrl:'https://'+(index===1?'predict.fun/markets/crypto':'polymarket.com/crypto/5M'),note:'Public HTML fixture',priceKind:index===1?'Indicador publicado; abajo es complemento':'Precio publicado'}))}))};
}
test('market API hosts and credentials are rejected before any request',async()=>{
 let calls=0;const fetcher=async()=>{calls++;throw Error('must not fetch');};
 for(const host of ['gamma-api.polymarket.com','clob.polymarket.com','api.predict.fun','api-testnet.predict.fun','external-api.kalshi.com'])await assert.rejects(publicJson('https://'+host+'/',fetcher),/Fuente/);
 await assert.rejects(publicJson(CANONICAL_API+'/api/snapshot?tf=5m',fetcher,'fixture-key'),/Configuración/);
 await assert.rejects(publicJson(CANONICAL_API+'/api/capture',fetcher),/Ruta/);
 assert.equal(calls,0);
});
test('canonical transport uses GET only and never sends a market API key',async()=>{
 const seen=[];const fetcher=async(url,options)=>{seen.push(url);assert.equal(options.method,'GET');assert.equal(options.redirect,'manual');assert.equal(options.headers['x-api-key'],undefined);assert.equal(options.body,undefined);return Response.json(fixture());};
 const s=await canonicalSnapshot(5,now,fetcher);assert.equal(s.assets.length,6);assert.deepEqual(seen,[CANONICAL_API+'/api/snapshot?tf=5m']);
 const cat=await predictCatalogue('ignored-fixture-key',fetcher);assert.equal(cat.status,'PUBLIC_WEB');
 const p=await predictMarket('BTC',5,now,cat,'ignored-fixture-key',fetcher);assert.equal(p.status,'PUBLICADO');assert.ok(seen.every(u=>u.startsWith(CANONICAL_API+'/api/snapshot')));assert.throws(()=>parsePredictBook({}),/deshabilitada/);
});
test('six assets and three exact windows preserve public prices with unknown tick/costs',()=>{
 for(const h of [5,15,60])for(const asset of ASSETS){const s=validateSnapshot(fixture(h),h,now),p=canonicalMarket(s,asset,h,'POLYMARKET',now),d=canonicalMarket(s,asset,h,'PREDICT',now);
  assert.equal(p.status,'PUBLICADO');assert.equal(p.publishedUp,70);assert.equal(p.publishedDown,39);assert.equal(p.pMarket,.7);assert.equal(p.publishedUp+p.publishedDown,109);assert.equal(p.up.mid,null);assert.equal(p.up.ask,null);assert.equal(p.down.bid,null);assert.equal(p.sourceAt,null);assert.equal(p.quoteAt,null);assert.equal(p.feesEnabled,null);assert.equal(p.contractProbability,null);assert.equal(d.complementDerived,true);assert.equal(d.publishedDown,30);
 }
});
test('snapshot errors, duplicate assets, wrong windows and unverifiable models fail closed',()=>{
 for(const change of [{timeframe:'15m'},{windowEnd:now+1},{asOf:now+6000},{expiresAt:now+100000},{assets:fixture().assets.slice(0,5)},{assets:fixture().assets.map(r=>({...r,symbol:'BTC'}))},{assets:fixture().assets.map(r=>({...r,research:{...r.research,contractProbability:.9}}))}])assert.throws(()=>validateSnapshot({...fixture(),...change},5,now));
});
test('expiration suspends publication and experiment without altering captured provenance',()=>{
 const s=fixture(),m=canonicalMarket(s,'BTC',5,'POLYMARKET',s.expiresAt);assert.equal(m.status,'STALE');assert.equal(m.receivedAt,now-1500);
 const r=s.assets[0].research,f=researchForecast(r,5,s,r.validUntil);assert.equal(f.p,null);assert.equal(f.direction,'WAIT');assert.equal(f.medianPrice,null);assert.equal(f.contractProbability,null);assert.equal(f.recommendation,'WAIT');
 const f2=researchForecast({...r,side:'WAIT'},5,s,now);assert.equal(f2.p,.7);assert.equal(f2.direction,'WAIT');assert.equal(f2.calibrated,false);
});
test('upstream 402/403/429/451 produce empty unavailable sources without a fallback API',async()=>{
 for(const status of [402,403,429,451]){let calls=0;const rows=await getMarkets('BTC',5,now,async()=>{calls++;return new Response('{}',{status});});assert.equal(calls,1);assert.equal(rows.length,3);assert.ok(rows.every(r=>r.status==='UNAVAILABLE'&&r.contractProbability===null));}
});
test('Kraken last uncommitted row is excluded even if its nominal close predates request now',async()=>{
 const start=Math.floor((now-1200000)/300000)*300000;const raw=[0,1,2].map(i=>[Math.floor((start+i*300000)/1000),'100','101','99','100','100','1',2]);
 const h=await getHistory('BTC',now,async()=>Response.json({error:[],result:{XXBTZUSD:raw,last:0}}));assert.equal(h.candles.length,2);assert.ok(h.candles.every(c=>c.confirmed===true));assert.ok(h.candles.every(c=>c.t!==Number(raw.at(-1)[0])*1000));
});
test('archive preserves original in-window capture; future and post-close records are rejected',async()=>{
 const date='2026-10-23',start=Date.parse(date+'T00:00:00-06:00');
 const plan={symbol:'BTC',timeframe:'5m',date,asOf:start+10000,calendar:Array.from({length:288},(_,i)=>({start:start+i*300000,end:start+(i+1)*300000,capture:i===0?{asOf:start+1000,row:fixture().assets[0]}:null}))};
 const read=async value=>canonicalDayPlan('BTC',5,date,async()=>Response.json(value));assert.equal((await read(plan)).calendar[0].capture.asOf,start+1000);
 for(const at of [start-1,start+300000,start+11000])await assert.rejects(read({...plan,calendar:plan.calendar.map((c,i)=>i===0?{...c,capture:{asOf:at}}:c)}),/fuera/);
 await assert.rejects(read({...plan,calendar:plan.calendar.map((c,i)=>i===1?{...c,start:c.start+1}:c)}),/Ventana/);
});
test('visiting analysis, matrix and collect does not invoke historical D1 writers',()=>{
 for(const path of ['app/api/analysis/route.ts','app/api/collect/route.ts','lib/market-matrix.ts']){const code=readFileSync(new URL('../'+path,import.meta.url),'utf8');assert.ok(!/recordAnalysis|recordMarketMatrix|cachePublicData|historyFor\(/.test(code),path);}
 const daily=readFileSync(new URL('../app/api/daily/route.ts',import.meta.url),'utf8');assert.ok(daily.includes('legacyLocalArchive'));assert.ok(!/INSERT|UPDATE|DELETE/.test(daily));
});

test('402 and server outages invoke one distinct public HTML reader with honest read-only provenance',async()=>{
 for(const status of [402,500,502,503,504]){
  let apiCalls=0,htmlCalls=0;
  const snapshot=await canonicalSnapshot(5,now,async(url,options)=>{apiCalls++;assert.equal(url,CANONICAL_API+'/api/snapshot?tf=5m');assert.equal(options.method,'GET');return new Response('{}',{status});},async horizon=>{htmlCalls++;assert.equal(horizon,5);return fixture();});
  assert.equal(apiCalls,1);assert.equal(htmlCalls,1);assert.equal(snapshot.transport,'DIRECT_PUBLIC_HTML_RSC');assert.equal(snapshot.archiveState,'LIVE_VIEW_ONLY');assert.equal(snapshot.archiveWriterEnabled,false);assert.equal(snapshot.upstreamAvailability.httpStatus,status);
  for(const row of snapshot.assets){assert.equal(row.research.contractProbability,null);assert.equal(row.research.calibrated,false);assert.equal(row.research.recommendation,'WAIT');}
 }
});
test('403 429 451 and authorization failures cannot be routed around using the public reader',async()=>{
 for(const status of [401,403,429,451]){
  let apiCalls=0,htmlCalls=0;
  await assert.rejects(canonicalSnapshot(5,now,async()=>{apiCalls++;return new Response('{}',{status});},async()=>{htmlCalls++;return fixture();}),new RegExp('HTTP '+status));
  assert.equal(apiCalls,1);assert.equal(htmlCalls,0);
 }
});
test('redirects and malformed canonical content do not trigger an alternative reader',async()=>{
 for(const response of [new Response('',{status:302}),new Response('not JSON'),Response.json({timeframe:'5m',assets:[]})]){
  let htmlCalls=0;
  await assert.rejects(canonicalSnapshot(5,now,async()=>response,async()=>{htmlCalls++;return fixture();}));assert.equal(htmlCalls,0);
 }
});
test('a successful canonical response does not invoke fallback or suggest its scheduler was verified',async()=>{
 let htmlCalls=0;const s=await canonicalSnapshot(5,now,async()=>Response.json(fixture()),async()=>{htmlCalls++;return fixture();});
 assert.equal(htmlCalls,0);assert.equal(s.transport,'CANONICAL_APPDEPLOY');assert.equal(s.archiveWriterEnabled,null);
});
test('network and timeout failures allow one public reader, whose failure is not retried',async()=>{
 for(const name of ['TypeError','TimeoutError','AbortError']){
  let apiCalls=0,htmlCalls=0;const error=new Error('unreachable fixture');error.name=name;
  const s=await canonicalSnapshot(5,now,async()=>{apiCalls++;throw error;},async()=>{htmlCalls++;return fixture();});assert.equal(apiCalls,1);assert.equal(htmlCalls,1);assert.equal(s.transport,'DIRECT_PUBLIC_HTML_RSC');assert.equal(s.upstreamAvailability.httpStatus,null);
 }
 let htmlCalls=0;await assert.rejects(canonicalSnapshot(5,now,async()=>new Response('{}',{status:402}),async()=>{htmlCalls++;throw Error('public source unavailable');}),/public source unavailable/);assert.equal(htmlCalls,1);
});
test('malformed or expired fallback snapshots are rejected rather than revived by receipt time',async()=>{
 for(const raw of [{...fixture(),assets:[]},{...fixture(),expiresAt:now},{...fixture(),expiresAt:now-1},{...fixture(),expiresAt:fixture().asOf},{...fixture(),windowEnd:now},{...fixture(),assets:fixture().assets.map(r=>({...r,research:{...r.research,calibrated:true}}))}]){
  let htmlCalls=0;await assert.rejects(canonicalSnapshot(5,now,async()=>new Response('{}',{status:402}),async()=>{htmlCalls++;return raw;}));assert.equal(htmlCalls,1);
 }
});
test('the distinct public HTML reader has no database, cron or market API writer',()=>{
 const code=readFileSync(new URL('../lib/public-web-snapshot.mjs',import.meta.url),'utf8');
 assert.ok(code.includes("method: 'GET'"));assert.ok(code.includes("archiveState:'LIVE_VIEW_ONLY'"));assert.ok(code.includes('archiveWriterEnabled:false'));
 assert.ok(!/@appdeploy\/sdk|recordAnalysis|recordMarketMatrix|db\.|gamma-api\.polymarket|clob\.polymarket|api\.predict\.fun|x-api-key/.test(code));
});
