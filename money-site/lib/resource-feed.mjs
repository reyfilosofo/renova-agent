import {buildUnifiedFeed} from './unified-feed.mjs';
export const REPORT_URL='https://raw.githubusercontent.com/reyfilosofo/renova-agent/main/money-resources/data/latest.json';
export const HEALTH_URL='https://raw.githubusercontent.com/reyfilosofo/renova-agent/main/money-resources/data/market-health.json';
export const MAX_AGE=86_400_000;
const HOSTS=new Set(['immunefi.com','www.immunefi.com','code4rena.com','www.code4rena.com','zealy.io','app.galxe.com','galxe.com','prolific.com','www.prolific.com','www.userinterviews.com','userinterviews.com','www.respondent.io','respondent.io','github.com','api.github.com']);
export function timestamp(v){const n=typeof v==='string'&&/(?:Z|[+-]\d{2}:\d{2})$/.test(v)?Date.parse(v):NaN;return Number.isFinite(n)?n:null;}
export function officialURL(value){try{const u=new URL(value);return u.protocol==='https:'&&HOSTS.has(u.hostname)&&!u.username&&!u.password&&!u.hash&&(!u.port||u.port==='443')?u.href:null;}catch{return null;}}
export function validateReport(r,now=Date.now()){
 const t=timestamp(r?.generated_at_utc);
 if(!r||!['1.0','1.1'].includes(r.schema_version)||r.mode!=='READ_ONLY'||t===null||t>now+60_000||!Array.isArray(r.opportunities)||r.opportunities.length>1000||!Array.isArray(r.sources)||r.sources.length>50)throw Error('Invalid report');
 const ids=new Set();for(const row of r.opportunities){if(!row||!/^resource_[a-f0-9]{24}$/.test(row.opportunity_id)||ids.has(row.opportunity_id)||typeof row.title!=='string'||typeof row.type!=='string')throw Error('Invalid opportunity');ids.add(row.opportunity_id);}
 return r;
}
export function currentState(row,sources,now=Date.now()){
 if(row.classification==='SKIP'||row.availability_status==='INACTIVE')return 'SKIP';
 const deadline=timestamp(row.deadline_utc),read=timestamp(row.last_verified_at_utc);
 if(deadline!==null&&deadline<=now)return 'SKIP';
 const source=sources.find(s=>s.source_id===row.source_id),attempt=timestamp(source?.last_scan_at_utc);
 if(read===null||read>now+60_000||now-read>MAX_AGE||attempt===null||attempt>now+60_000||now-attempt>MAX_AGE||source.last_status!=='ACCESS VERIFIED'||row.availability_status==='UNAVAILABLE')return 'DATA INSUFFICIENT';
 return row.classification==='QUEUE'?'QUEUE':row.classification==='WATCH'?'WATCH':'DATA INSUFFICIENT';
}
export function priorityRows(report,now=Date.now()){
 const shared=buildUnifiedFeed(report,{nowUtc:new Date(now).toISOString()});
 const normalized=new Map(shared.modules.earn.items.map(row=>[row.opportunity_id,row]));
 return [...report.opportunities].sort((a,b)=>{
 const state=row=>({QUEUE:0,WATCH:1,'DATA INSUFFICIENT':2,SKIP:3})[currentState(row,report.sources,now)];
 const delta=state(a)-state(b);if(delta)return delta;
 const ev=x=>typeof x.expected_net_reward_usd==='number'&&Number.isFinite(x.expected_net_reward_usd)?x.expected_net_reward_usd:null;
 if(ev(a)!==null&&ev(b)!==null)return ev(b)-ev(a);
 if(ev(a)!==null||ev(b)!==null)return ev(a)!==null?-1:1;
 return (normalized.get(b.opportunity_id)?.review_priority??0)-(normalized.get(a.opportunity_id)?.review_priority??0)||a.provider.localeCompare(b.provider)||a.title.localeCompare(b.title);
 });
}
export function calculateEV(input){
 const keys=['reward','probability','gas','fees','spend','loss','time','lockup','security'];
 if(keys.some(k=>typeof input[k]!=='number'||!Number.isFinite(input[k])||input[k]<0)||input.probability>1)return null;
 const value=input.reward*input.probability-keys.slice(2).reduce((n,k)=>n+input[k],0);return Number.isFinite(value)?value:null;
}
export function displayMoney(n,currency='USD'){return typeof n==='number'&&Number.isFinite(n)?new Intl.NumberFormat('es-MX',{style:'currency',currency}).format(n):'Por verificar';}
