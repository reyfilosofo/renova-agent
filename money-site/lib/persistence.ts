import { env } from 'cloudflare:workers';
import { ASSETS, getHistory } from './market-data.mjs';

export function database() {
  if (!env.DB) throw new Error('Registro persistente no disponible');
  return env.DB;
}

export async function cachedPublicData(id:string) {
  const row=await database().prepare('SELECT updated,payload FROM money_comparator_cache WHERE id=?').bind(id).first<{updated:number;payload:string}>();
  return row ? {updated:row.updated,value:JSON.parse(row.payload)} : null;
}
export async function cachePublicData(id:string,updated:number,value:any) {
  const payload=JSON.stringify(value);
  if(payload.length>1500000)throw new Error('Cache de fuente excede límite');
  await database().prepare('INSERT INTO money_comparator_cache(id,updated,payload) VALUES(?,?,?) ON CONFLICT(id) DO UPDATE SET updated=excluded.updated,payload=excluded.payload').bind(id,updated,payload).run();
}
export async function recordMarketMatrix(matrix:any) {
  const db=database(),created=matrix.completedAt;
  const statements=matrix.rows.filter((r:any)=>created>=r.startAt&&created<r.endAt).map((r:any)=>{
    const id=`${r.asset}:${r.horizon}:${r.startAt}:${Math.floor(created/300000)}`;
    const markets=r.markets.map((m:any)=>({provider:m.provider,status:m.status,id:m.id??null,title:m.title??null,startAt:m.startAt??null,
      expiresAt:m.expiresAt??null,reference:m.reference??null,referenceLabel:m.referenceLabel??null,labelReference:m.labelReference??null,
      precisionWarning:m.precisionWarning??null,rules:m.rules??null,decimalPrecision:m.decimalPrecision??null,url:m.url??null,
      pMarket:m.pMarket??null,up:m.up??null,down:m.down??null,
      feesEnabled:m.feesEnabled??null,feeSchedule:m.feeSchedule??null,feeRateBps:m.feeRateBps??null,spec:m.spec??null,
      sourceAt:m.sourceAt??null,requestedAt:m.requestedAt??null,receivedAt:m.receivedAt??null,error:m.error??null,
      costUp:m.costUp,costDown:m.costDown,contractProbability:null}));
    return db.prepare('INSERT OR IGNORE INTO money_market_snapshots(id,asset,horizon,window_start,window_end,created,payload) VALUES(?,?,?,?,?,?,?)')
      .bind(id,r.asset,r.horizon,r.startAt,r.endAt,created,JSON.stringify({created,markets,comparison:r.comparison,cutId:matrix.cutId}));
  });
  const results=statements.length?await db.batch(statements):[];
  if(results.some(r=>r.success!==true||!Number.isFinite(r.meta?.changes)))throw new Error('Guardado de captura no verificado');
  const inserted=results.reduce((n,r)=>n+r.meta.changes,0),existing=statements.length-inserted;
  return {status:statements.length===0?'SIN CAPTURA':inserted===0?'EXISTENTE':existing>0?'PARCIAL':'GUARDADO',windows:inserted,attempted:statements.length,inserted,existing,
    note:statements.length===0?'La consulta terminó fuera de todas las ventanas; no se registró una captura.':existing>0?'Se conserva la primera captura de este corte5m; las nuevas cuotas no reemplazaron registros existentes.':'Primera captura por activo/plazo/corte5m; no se reescribe. No es forecast ni cotización futura.'};
}
export async function historyFor(asset: string, now: number) {
  const db = database();
  const old = await db.prepare('SELECT source, updated, payload FROM money_history_cache WHERE asset = ?').bind(asset).first<{source:string;updated:number;payload:string}>();
  const bucket = Math.floor(now / 300000);
  if (old && Math.floor(old.updated / 300000) === bucket) return { ...JSON.parse(old.payload), cache: true };
  // Kraken is a separately labelled USD research cohort, never a hidden Binance substitute.
  const fresh = await getHistory(asset, now);
  let candles = fresh.candles;
  if (old && old.source === fresh.source) {
    const merged = new Map<number, unknown>();
    for (const c of JSON.parse(old.payload).candles ?? []) merged.set(c.t, c);
    for (const c of candles) merged.set(c.t, c);
    candles = [...merged.values()].sort((a:any,b:any) => a.t-b.t).slice(-20160) as typeof candles;
  }
  const stored = { ...fresh, candles };
  await db.prepare('INSERT INTO money_history_cache(asset, source, updated, payload) VALUES (?, ?, ?, ?) ON CONFLICT(asset) DO UPDATE SET source=excluded.source, updated=excluded.updated, payload=excluded.payload')
    .bind(asset, fresh.source, now, JSON.stringify(stored)).run();
  return { ...stored, cache: false };
}
export async function recordAnalysis(asset: string, result: any, candles: any[]) {
  const db = database(), now = Date.now();
  const calls = [];
  for (const f of result.forecasts) {
    if (f.p === null || !f.origin || now >= f.validUntil || now >= f.target) continue;
    const id = `${f.strategyId}:${f.version}:${f.source}:${asset}:${f.horizon}:${f.origin}`;
    f.forecastId = id;
    calls.push(db.prepare('INSERT OR IGNORE INTO money_forecasts(id, asset, horizon, source, origin, target, reference, probability, created, payload) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)')
      .bind(id, asset, f.horizon, f.source, f.origin, f.target, f.reference, f.p, now, JSON.stringify(f)));
  }
  const id = `${asset}:${Math.floor(now/300000)}`;
  calls.push(db.prepare('INSERT OR IGNORE INTO money_observations(id, asset, created, payload) VALUES (?, ?, ?, ?)').bind(id, asset, now, JSON.stringify(result)));
  await db.batch(calls);
  const pending = await db.prepare('SELECT id, target, reference, source FROM money_forecasts WHERE asset = ? AND outcome IS NULL AND target <= ? ORDER BY target ASC LIMIT 1000')
    .bind(asset, now).all<{id:string;target:number;reference:number;source:string}>();
  const closingPrices = new Map(candles.map(c => [c.t+300000,c.c]));
  const updates = [];
  for (const row of pending.results) {
    const price = closingPrices.get(row.target) as number | undefined;
    if (price === undefined || row.source !== 'Kraken USD') continue;
    const outcome = price > row.reference ? 'UP' : price < row.reference ? 'DOWN' : 'FLAT';
    updates.push(db.prepare('UPDATE money_forecasts SET outcome = ?, resolved = ?, final_price = ? WHERE id = ? AND outcome IS NULL').bind(outcome, now, price, row.id));
  }
  if (updates.length) await db.batch(updates);
  return { status: 'GUARDADO', resolved: updates.length, note: 'Archivo persistente en el sitio; no copia automática a Drive/GitHub. Registro solo mientras se consulta.' };
}
export async function journal(asset: string, horizon: number, offset = 0, limit = 100) {
  const db = database();
  if (asset !== 'ALL' && !ASSETS.includes(asset)) throw new Error('Activo inválido');
  const rows = await db.prepare('SELECT * FROM money_forecasts WHERE (? = \'ALL\' OR asset = ?) AND (? = 0 OR horizon = ?) ORDER BY created DESC, id DESC LIMIT ? OFFSET ?')
    .bind(asset, asset, horizon, horizon, limit+1, offset).all<any>();
  const summary = await db.prepare('SELECT asset,horizon,source,json_extract(payload,\'$.strategyId\') strategy,json_extract(payload,\'$.version\') version,COUNT(*) total,SUM(CASE WHEN outcome IN (\'UP\',\'DOWN\') THEN 1 ELSE 0 END) evaluated,AVG(CASE WHEN outcome=\'UP\' THEN (probability-1)*(probability-1) WHEN outcome=\'DOWN\' THEN probability*probability ELSE NULL END) brier FROM money_forecasts WHERE (? = \'ALL\' OR asset = ?) AND (? = 0 OR horizon = ?) GROUP BY asset,horizon,source,strategy,version')
    .bind(asset,asset,horizon,horizon).all<any>();
  const observations = await db.prepare('SELECT COUNT(*) AS n FROM money_observations').first<{n:number}>();
  return { records: rows.results.slice(0,limit).map(x => ({ ...x, payload: JSON.parse(x.payload) })), hasMore: rows.results.length > limit,
    nextOffset: offset + limit, summary: summary.results, observations: observations?.n ?? 0,
    calibration: 'No calibrado. Separar activos/horizontes; resultados consecutivos15/60m se solapan. FLAT excluido del Brier binario.' };
}
