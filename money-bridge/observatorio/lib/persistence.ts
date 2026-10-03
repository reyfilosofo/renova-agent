import { env } from 'cloudflare:workers';
import { ASSETS, getHistory } from './market-data.mjs';

function database() {
  if (!env.DB) throw new Error('Registro persistente no disponible');
  return env.DB;
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
