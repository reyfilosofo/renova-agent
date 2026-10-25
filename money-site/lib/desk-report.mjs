export const DESK_REPORT_URL='https://raw.githubusercontent.com/reyfilosofo/renova-agent/main/money-desk/data/latest.json';
export const ROLE_IDS=['MONEY_GAMBLER_PAPER_V1','MONEY_HOUSE_PAPER_V1','MONEY_SPY_PAPER_V1'];
export function deskTimestamp(value){const n=typeof value==='string'&&/(?:Z|[+-]\d{2}:\d{2})$/.test(value)?Date.parse(value):NaN;return Number.isFinite(n)?n:null;}
export function quoteNumber(value){if(typeof value==='string'&&value.length<=64&&/^(?:0|[1-9]\d*)(?:\.\d+)?$/.test(value))value=Number(value);return typeof value==='number'&&Number.isFinite(value)&&value>0&&value<=1e15?value:null;}
export function validateDeskReport(report,now=Date.now()){
 const time=deskTimestamp(report?.generated_at_utc);
 if(!report||report.schema_version!=='1.0'||report.mode!=='PAPER'||time===null||time>now+5000||report.live_execution_enabled!==false||report.paper_execution_enabled!==false||!Array.isArray(report.observations)||report.observations.length>6||!Array.isArray(report.source_status)||report.source_status.length>6)throw Error('Invalid PAPER report');
 const seen=new Set();for(const row of report.observations){if(!['BTC','ETH','SOL','DOGE','XRP','BNB'].includes(row.asset)||seen.has(row.asset))throw Error('Invalid asset');seen.add(row.asset);for(const key of ['price','last_trade_price','bid','ask'])if(row[key]!==null&&row[key]!==undefined&&quoteNumber(row[key])===null)throw Error('Invalid quote');}
 return report;
}
export function deskFreshness(report,now=Date.now()){
 const time=deskTimestamp(report?.generated_at_utc);return time===null||time>now+5000?'INVALID':now-time>15*60000?'STALE':'RECENT OBSERVATION';
}
export function observedQuoteState(row,now=Date.now()){
 const tick=deskTimestamp(row?.last_trade_at_utc??row?.quote_at_utc??row?.source_at_utc),received=deskTimestamp(row?.received_at_utc);
 if(received===null||received>now+5000)return 'SIN FECHA VÁLIDA';
 if(now-received>60000)return 'LECTURA VENCIDA';
 if(tick!==null&&(tick>received||tick>now+5000))return 'FECHAS INCONSISTENTES';
 if(tick!==null&&now-tick>90000)return 'OPERACIÓN ANTIGUA';
 if(tick===null)return 'PUBLICADO · TICK SIN VERIFICAR';
 return 'OBSERVADO · ÚLTIMA OPERACIÓN';
}
