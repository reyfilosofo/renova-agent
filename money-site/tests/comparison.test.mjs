import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,readdirSync} from 'node:fs';
import {DatabaseSync} from 'node:sqlite';
import {currentWindow,polymarketCandidate,freshness,compareMarkets,perShareCost,evaluateMatrixTiming} from '../lib/comparison.mjs';
import {ASSETS,publicJson,polymarket,bestBook} from '../lib/market-data.mjs';
import {dayBounds,localDay,dailyGrid} from '../lib/daily-plan.mjs';
const now=Date.parse('2026-10-04T09:02:00Z');
const spec={asset:'BTC',quoteUnit:'USD',startAt:now-120000,endAt:now+180000,referenceExact:'84000.10',oracleProvider:'Chainlink',oracleFeedId:'BTCUSD',priceStatistic:'TWAP',averagingWindowSeconds:60,rounding:'0.01',operator:'>=',tiePayout:'UP',voidPayout:'REFUND',payoutCurrency:'USD',payoutAmount:1,rulesVersion:'fixture1'};
function market(p=.70,overrides={}){return {status:'OBSERVADO',expiresAt:now+180000,receivedAt:now-1000,pMarket:p,spec:{...spec},up:{sourceAt:now-2000,ask:p+.01,bid:p-.01},down:{sourceAt:now-2000,ask:1-p+.01,bid:1-p-.01},...overrides};}
test('six assets share UTC window boundaries; hourly candidate includes year and ET conversion',()=>{
  for(const h of [5,15,60]){const w=currentWindow(now,h);assert.equal(w.startAt%(h*60000),0);assert.equal(w.endAt-w.startAt,h*60000);}
  const names=['bitcoin','ethereum','solana','xrp','dogecoin','bnb'];
  ASSETS.forEach((a,i)=>assert.equal(polymarketCandidate(a,60,now).slug,`${names[i]}-up-or-down-october-4-2026-5am-et`));
  assert.equal(polymarketCandidate('BTC',60,Date.parse('2026-01-01T04:10:00Z')).slug,'bitcoin-up-or-down-december-31-2025-11pm-et');
  assert.throws(()=>currentWindow(now,10));assert.throws(()=>polymarketCandidate('FAKE',5,now));
});
test('70 versus59 is11 percentage points, never a contract model probability or edge',()=>{
  const c=compareMarkets(market(.70),market(.59),now);
  assert.ok(Math.abs(c.midpointDifferencePp-11)<1e-10);assert.equal(c.executionEnabled,false);assert.equal(c.edge,null);assert.equal(c.contractProbability,null);
  const different=compareMarkets(market(),market(.59,{spec:{...spec,quoteUnit:'USDT',tiePayout:'50/50'}}),now);
  assert.equal(different.semanticGrade,'DIFFERENT');assert.equal(different.comparisonEnabled,false);assert.ok(different.mismatches.includes('tiePayout'));
});
test('unknown reference, incomplete rules and one missing timestamp prevent certified comparison',()=>{
  const a=market(),b=market(.59,{spec:{...spec,referenceExact:null}});
  assert.equal(compareMarkets(a,b,now).semanticGrade,'UNVERIFIED');
  b.spec.referenceExact='0';assert.equal(compareMarkets(a,b,now).comparisonEnabled,false);
  assert.equal(freshness({...a,down:{sourceAt:null}},now).grade,'UNKNOWN');
  assert.equal(compareMarkets(a,{...a,metadataAt:now,up:{sourceAt:null},down:{sourceAt:null}},now).timingGrade,'UNKNOWN');
});
test('old, invalid and expired books cannot display an actionable live difference',()=>{
  for(const bad of [market(.59,{receivedAt:now-31000}),market(.59,{expiresAt:now}),market(.59,{up:{sourceAt:now+6000},down:{sourceAt:now+6000}}),market(.59,{up:{sourceAt:now/1000},down:{sourceAt:now/1000}})]){
    const c=compareMarkets(market(),bad,now);assert.equal(c.midpointDifferencePp,null);assert.equal(c.comparisonEnabled,false);
  }
  assert.equal(freshness(market(.5,{metadataAt:now,up:{sourceAt:now-40000},down:{sourceAt:now-40000}}),now).grade,'STALE');
});
test('all four book timestamps and receipt skew determine grouped observation',()=>{
  assert.equal(compareMarkets(market(),market(.59,{down:{sourceAt:now-7000}}),now).timingGrade,'SKEWED');
  assert.equal(compareMarkets(market(),market(.59,{receivedAt:now-9000}),now).timingGrade,'SKEWED');
});
test('completion and cache re-evaluation cannot retain a fresh comparison after books age',()=>{
  const rows=[{asset:'BTC',horizon:5,markets:[{...market(),provider:'POLYMARKET'},{...market(.59),provider:'PREDICT'}]}];
  const first=evaluateMatrixTiming(rows,now);assert.equal(first[0].comparison.comparisonEnabled,true);
  const slow=evaluateMatrixTiming(first,now+80000);assert.equal(slow[0].markets[0].freshness.grade,'STALE');assert.equal(slow[0].comparison.midpointDifferencePp,null);assert.equal(slow[0].comparison.comparisonEnabled,false);
  assert.equal(first[0].comparison.comparisonEnabled,true,'Original capture is not mutated');
});
test('noncanonical object settlement rules cannot collapse to equal strings',()=>{
  const a=market(.7,{spec:{...spec,tiePayout:{up:1,down:0}}}),b=market(.59,{spec:{...spec,tiePayout:{up:0,down:1}}});
  const c=compareMarkets(a,b,now);assert.equal(c.semanticGrade,'UNVERIFIED');assert.equal(c.comparisonEnabled,false);assert.ok(c.missing.includes('tiePayout'));
});
test('independent asks do not get normalized; an absent fee is never zero',()=>{
  const up=bestBook({bids:[{price:.69,size:5}],asks:[{price:.70,size:5}]}),down=bestBook({bids:[{price:.58,size:5}],asks:[{price:.59,size:5}]});
  assert.equal(up.ask,.70);assert.equal(down.ask,.59);assert.equal(Number((up.ask+down.ask).toFixed(2)),1.29);
  const m={provider:'POLYMARKET',feesEnabled:true,feeSchedule:{rate:.07,exponent:1},up:{ask:.5}};
  assert.equal(perShareCost(m,'up').fee,.0175);assert.equal(perShareCost(m,'up').venueSubtotal,.5175);assert.equal(perShareCost(m,'up').walletTotal,null);
  for(const rate of [null,undefined,'',NaN])assert.equal(perShareCost({...m,feeSchedule:{rate,exponent:1}},'up').fee,null);
  assert.equal(perShareCost({...m,provider:'PREDICT',feeRateBps:200},'up').fee,null);
});
test('daily grids have exactly24/96/288 CDMX windows; invalid dates are rejected',()=>{
  assert.equal(localDay(Date.parse('2026-10-04T03:00:00Z')),'2026-10-03');
  const b=dayBounds('2026-10-04');assert.equal(new Date(b.startAt).toISOString(),'2026-10-04T06:00:00.000Z');
  for(const h of [60,15,5]){const g=dailyGrid('2026-10-04',h,ASSETS,[],[],now);assert.equal(g.rows.length,1440/h);assert.equal(g.expectedCells,g.rows.length*6);assert.equal(g.rows.at(-1).endAt,b.endAt);}
  for(const day of ['2026-02-30','2025-02-29','2022-12-31','bad'])assert.throws(()=>dayBounds(day));
});
test('daily calendar preserves first emission and rejects future, late and rolling forecasts',()=>{
  const b=dayBounds('2026-10-04'),origin=b.startAt+3*3600000,f={id:'first',asset:'BTC',horizon:60,origin,target:origin+3600000,created:origin+1000,reference:100,probability:.6,payload:{medianPrice:101},source:'Kraken USD'};
  const g=dailyGrid('2026-10-04',60,ASSETS,[{...f,id:'later',created:origin+3000,probability:.99},f,{...f,id:'rolling',asset:'ETH',origin:origin+300000,target:origin+3900000},{...f,id:'late',asset:'SOL',created:f.target+1},{...f,id:'future',asset:'DOGE',origin:origin+3600000,target:origin+7200000,created:origin+3601000}],[],origin+10000);
  assert.equal(g.rows[3].assets[0].forecast.probability,.6);assert.equal(g.rows[3].assets[0].forecast.reference,100);assert.equal(g.forecastedCells,1);
  assert.ok(g.rows[4].assets.every(a=>a.forecast===null));assert.equal(g.rows[4].state,'FUTURE');
});
test('daily market snapshot keeps the first original capture and ignores post-close captures',()=>{
  const b=dayBounds('2026-10-04'),s={asset:'BTC',horizon:5,window_start:b.startAt,window_end:b.startAt+300000,created:b.startAt+1000,payload:{created:b.startAt+1000,markets:[{pMarket:.7}]}};
  const g=dailyGrid('2026-10-04',5,ASSETS,[],[{...s,created:s.created+1,payload:{created:s.created+1,markets:[{pMarket:.59}]}},s,{...s,asset:'ETH',created:s.window_end+1}],b.startAt+400000);
  assert.equal(g.rows[0].assets[0].marketSnapshot.markets[0].pMarket,.7);assert.equal(g.rows[0].assets[1].marketSnapshot,null);
});
test('all append-only migrations apply; snapshots are insert-once and daily indexes exist',()=>{
  const db=new DatabaseSync(':memory:'),dir=new URL('../drizzle/',import.meta.url);
  for(const f of readdirSync(dir).filter(x=>/^\d+.*\.sql$/.test(x)).sort())db.exec(readFileSync(new URL(f,dir),'utf8'));
  const ins=db.prepare('INSERT OR IGNORE INTO money_market_snapshots(id,asset,horizon,window_start,window_end,created,payload) VALUES (?,?,?,?,?,?,?)');
  ins.run('same','BTC',5,now,now+300000,now,'{"p":0.7}');ins.run('same','BTC',5,now,now+300000,now,'{"p":0.59}');assert.equal(JSON.parse(db.prepare('SELECT payload FROM money_market_snapshots').get().payload).p,.7);
  const indexes=db.prepare("SELECT name FROM sqlite_master WHERE type='index'").all().map(x=>x.name);assert.ok(indexes.includes('money_forecasts_daily_idx'));assert.ok(indexes.includes('money_market_snapshots_daily_idx'));db.close();
});
