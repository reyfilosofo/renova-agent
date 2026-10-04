import { cleanCandles } from './model.mjs';
import { polymarketCandidate } from './comparison.mjs';
export const ASSETS = ['BTC', 'ETH', 'SOL', 'XRP', 'DOGE', 'BNB'];
export const NAMES = { BTC: 'Bitcoin', ETH: 'Ethereum', SOL: 'Solana', XRP: 'XRP', DOGE: 'Dogecoin', BNB: 'BNB' };
const pairs = { BTC: 'XBTUSD', ETH: 'ETHUSD', SOL: 'SOLUSD', XRP: 'XRPUSD', DOGE: 'DOGEUSD', BNB: 'BNBUSD' };
const series = { BTC: 'KXBTC15M', ETH: 'KXETH15M', SOL: 'KXSOL15M', XRP: 'KXXRP15M', DOGE: 'KXDOGE15M', BNB: 'KXBNB15M' };
const HOSTS = new Set(['api.kraken.com', 'api.exchange.coinbase.com', 'gamma-api.polymarket.com', 'clob.polymarket.com', 'external-api.kalshi.com', 'api.predict.fun']);
const numeric = x => x === null || x === undefined || x === '' ? null : Number.isFinite(Number(x)) ? Number(x) : null;
const probability = x => { const n = numeric(x); return n !== null && n >= 0 && n <= 1 ? n : null; };
const list = v => Array.isArray(v) ? v : typeof v === 'string' ? JSON.parse(v) : [];
export async function publicJson(url, fetcher = fetch, predictKey = null) {
  const u = new URL(url);
  if (u.protocol !== 'https:' || !HOSTS.has(u.hostname) || u.username || u.password || u.port) throw new Error('Fuente no permitida');
  // Workers supports manual/follow, not Node's redirect:error. Never follow a
  // redirect: keep the upstream host allowlist intact in both runtimes.
  const headers = { Accept: 'application/json' };
  // A Predict credential is sent only to the official mainnet API, never to
  // any other source, redirect, URL, returned object or client bundle.
  if (predictKey !== null) {
    if (u.hostname !== 'api.predict.fun' || typeof predictKey !== 'string' || !predictKey || predictKey.length > 1024 || /[\r\n]/.test(predictKey)) throw new Error('Configuración de fuente inválida');
    headers['x-api-key'] = predictKey;
  }
  const r = await fetcher(u.toString(), { method: 'GET', redirect: 'manual', signal: AbortSignal.timeout(10000), headers });
  if (r.status >= 300 && r.status < 400) throw new Error('Redirección de fuente rechazada; sin datos verificables');
  if (!r.ok) throw new Error(`HTTP ${r.status}; sin datos verificables`);
  const s = await r.text();
  if (s.length > 2_000_000) throw new Error('Respuesta excede límite');
  let data;
  try { data = JSON.parse(s); } catch { throw new Error('La fuente no devolvió JSON válido'); }
  return data;
}
export async function getHistory(asset, now = Date.now(), fetcher = fetch) {
  if (!ASSETS.includes(asset)) throw new Error('Activo no permitido');
  const url = `https://api.kraken.com/0/public/OHLC?pair=${pairs[asset]}&interval=5`;
  const j = await publicJson(url, fetcher);
  if (j.error?.length) throw new Error(j.error.join('; '));
  const data = Object.entries(j.result ?? {}).find(([k]) => k !== 'last')?.[1];
  if (!Array.isArray(data)) throw new Error('Histórico no disponible para este par');
  const rows = data.map(x => ({ t: Number(x[0]) * 1000, o: Number(x[1]), h: Number(x[2]), l: Number(x[3]), c: Number(x[4]), v: Number(x[6]) }));
  return { source: 'Kraken USD', intervalMinutes: 5, receivedAt: Date.now(), candles: cleanCandles(rows, now, 5), sourceUrl: url };
}
export async function getQuotes(asset, fetcher = fetch) {
  if (!ASSETS.includes(asset)) throw new Error('Activo no permitido');
  const kraken = async () => {
    const j = await publicJson(`https://api.kraken.com/0/public/Ticker?pair=${pairs[asset]}`, fetcher);
    if (j.error?.length) throw new Error(j.error.join('; '));
    const x = Object.values(j.result ?? {})[0];
    const price = numeric(x?.c?.[0]), bid = numeric(x?.b?.[0]), ask = numeric(x?.a?.[0]);
    if (!price || !bid || !ask || price <= 0 || bid <= 0 || ask <= 0 || bid > ask) throw new Error('Ticker inválido');
    return { source: 'Kraken', price, bid, ask, currency: 'USD', sourceAt: null, receivedAt: Date.now(), timestampVerified: false, status: 'OBSERVADO' };
  };
  const coinbase = async () => {
    if (asset === 'BNB') return { source: 'Coinbase spot', status: 'NO VERIFICADO', error: 'Disponibilidad del par BNB-USD no verificada' };
    const j = await publicJson(`https://api.exchange.coinbase.com/products/${asset}-USD/ticker`, fetcher);
    const price = numeric(j.price), bid = numeric(j.bid), ask = numeric(j.ask), sourceAt = Date.parse(j.time);
    if (!price || !bid || !ask || price <= 0 || bid <= 0 || ask <= 0 || bid > ask || !Number.isFinite(sourceAt)) throw new Error('Ticker/fecha inválidos');
    return { source: 'Coinbase spot', price, bid, ask, currency: 'USD', sourceAt, receivedAt: Date.now(), timestampVerified: true, status: 'OBSERVADO' };
  };
  return Promise.all([kraken, coinbase].map(async f => { try { return await f(); } catch(e) { return { source: f === kraken ? 'Kraken' : 'Coinbase spot', status: 'UNAVAILABLE', error: e.message, receivedAt: Date.now() }; } }));
}
export function bestBook(book) {
  const bids = (book?.bids ?? []).map(x => ({ price: probability(x.price), size: numeric(x.size) })).filter(x => x.price !== null && x.size > 0).sort((a,b) => b.price-a.price);
  const asks = (book?.asks ?? []).map(x => ({ price: probability(x.price), size: numeric(x.size) })).filter(x => x.price !== null && x.size > 0).sort((a,b) => a.price-b.price);
  const bid = bids[0]?.price ?? null, ask = asks[0]?.price ?? null;
  if (bid !== null && ask !== null && bid > ask) throw new Error('Libro cruzado');
  return { bid, ask, depthAtBid:bids[0]?.size ?? null, depthAtAsk: asks[0]?.size ?? null, mid: bid !== null && ask !== null ? (bid + ask) / 2 : null, sourceAt: numeric(book?.timestamp), minOrderSize: numeric(book?.min_order_size) };
}
export async function polymarket(asset, horizon, now = Date.now(), fetcher = fetch) {
  if (!ASSETS.includes(asset) || ![5,15,60].includes(horizon)) return { provider:'POLYMARKET',venue: 'Polymarket', status: 'NO VERIFICADO', error: 'Activo/horizonte no permitido' };
  const requestedAt = Date.now();
  const {slug:candidate,startAt,endAt} = polymarketCandidate(asset,horizon,now);
  const event = await publicJson(`https://gamma-api.polymarket.com/events/slug/${candidate}`, fetcher);
  if (event.slug !== candidate || event.closed || event.active === false) throw new Error('Mercado candidato no verificado/abierto');
  const m = event.markets?.find(x => x.slug === candidate && !x.closed && x.active !== false);
  if (!m) throw new Error('No hay contrato activo');
  const outcomes = list(m.outcomes), tokens = list(m.clobTokenIds), p = list(m.outcomePrices);
  const up = outcomes.findIndex(x => String(x).toLowerCase() === 'up'), down = outcomes.findIndex(x => String(x).toLowerCase() === 'down');
  const expiresAt = Date.parse(m.endDate ?? event.endDate);
  const observedStart = Date.parse(m.eventStartTime ?? event.eventStartTime);
  if (up < 0 || down < 0 || outcomes.length !== 2 || !tokens[up] || !tokens[down] || !Number.isFinite(expiresAt) || expiresAt <= now || expiresAt !== endAt || (Number.isFinite(observedStart) && observedStart !== startAt) || (horizon===60 && !Number.isFinite(observedStart))) throw new Error('Outcomes o ventana contractual no verificados');
  const fetched = await Promise.all([up, down].map(async i => {
    try { return bestBook(await publicJson(`https://clob.polymarket.com/book?token_id=${encodeURIComponent(tokens[i])}`, fetcher)); }
    catch(e) { return { bid: null, ask: null, mid: null, depthAtAsk: null, sourceAt: null, error: e.message }; }
  }));
  const marketUp = probability(p[up]);
  const rawReference = event.eventMetadata?.priceToBeat;
  const reference = numeric(rawReference)>0 ? numeric(rawReference) : null;
  const rules = m.description ?? event.description ?? '';
  const binanceHourly = horizon===60 && /binance/i.test(rules) && /USDT/i.test(rules);
  const twap = /chainlink/i.test(rules) && /TWAP/i.test(rules) && /60/.test(rules);
  const quoteUnit = binanceHourly ? 'USDT' : twap && /USD/.test(rules) ? 'USD' : null;
  const operator = /greater than or equal|higher than or equal/i.test(rules) ? '>=' : /greater than|higher than/i.test(rules) ? '>' : null;
  const spec = {asset,quoteUnit,startAt,endAt,referenceExact:reference===null?null:String(rawReference),
    oracleProvider:binanceHourly?'Binance':twap?'Chainlink':null,oracleFeedId:m.resolutionSource ?? event.resolutionSource ?? null,
    priceStatistic:binanceHourly?'OPEN_CLOSE_1H':twap?'TWAP60S':null,averagingWindowSeconds:twap?60:binanceHourly?0:null,
    rounding:null,operator,tiePayout:operator==='>='?'UP':null,voidPayout:null,payoutCurrency:null,payoutAmount:1,rulesVersion:null};
  return { provider:'POLYMARKET',venue: 'Polymarket', asset, horizon, id: String(m.id), eventId: String(event.id), conditionId:m.conditionId, tokens:{up:String(tokens[up]),down:String(tokens[down])}, slug: event.slug,
    title: m.question ?? event.title, reference, resolutionSource: m.resolutionSource ?? event.resolutionSource ?? null,
    rules, spec, startAt, expiresAt, requestedAt, receivedAt: Date.now(),
    gammaUp: marketUp, gammaDown: probability(p[down]), up: fetched[0], down: fetched[1],
    pMarket: fetched[0].mid, pMarketKind: 'Punto medio del libro UP; no probabilidad propia ni ask',
    feeSchedule: m.feeSchedule ?? null, feesEnabled: m.feesEnabled ?? null,
    url: `https://polymarket.com/event/${event.slug}`, status: 'OBSERVADO',
    classification: 'DATA INSUFFICIENT', contractProbability: null, calibrated: false,
    reason: 'Referencia/oráculo exactos, modelo contractual calibrado y costes finales no verificados.1h puede usar BinanceUSDT;5/15m otras reglas. No comparar con Pspot.' };
}
export async function kalshi(asset, horizon, now = Date.now(), fetcher = fetch) {
  if (!ASSETS.includes(asset) || horizon !== 15) return { provider:'KALSHI',venue: 'Kalshi / referencia Coinbase Predictions', status: 'NO VERIFICADO', error: 'Se verifican Up/Down15m. Consultar cada5m no crea contratos5m ni1h.' };
  const requestedAt=Date.now();
  const j = await publicJson(`https://external-api.kalshi.com/trade-api/v2/markets?series_ticker=${series[asset]}&status=open&limit=20`, fetcher);
  const m = (j.markets ?? []).filter(x => x.ticker?.startsWith(series[asset]+'-') && x.status === 'active' && Date.parse(x.open_time) <= now && Date.parse(x.close_time) > now)
    .sort((a,b) => Date.parse(a.close_time)-Date.parse(b.close_time))[0];
  if (!m || (Date.parse(m.close_time) - Date.parse(m.open_time)) !== 15 * 60000 || !m.rules_primary) throw new Error('Contrato Up/Down15m no verificado');
  const upBid = probability(m.yes_bid_dollars), upAsk = probability(m.yes_ask_dollars);
  const downBid = probability(m.no_bid_dollars), downAsk = probability(m.no_ask_dollars);
  if ((upBid !== null && upAsk !== null && upBid > upAsk) || (downBid !== null && downAsk !== null && downBid > downAsk)) throw new Error('Cotizaciones cruzadas');
  const reference = numeric(m.floor_strike);
  const labelNumber = String(m.yes_sub_title ?? '').match(/\$?([0-9][0-9,]*\.[0-9]+)/)?.[1];
  const labelReference = labelNumber ? numeric(labelNumber.replaceAll(',', '')) : null;
  const startAt=Date.parse(m.open_time),expiresAt=Date.parse(m.close_time),rules=`${m.rules_primary}\n${m.rules_secondary ?? ''}`;
  return { provider:'KALSHI',venue: 'Kalshi / referencia Coinbase Predictions', asset, horizon, id: m.ticker, title: m.title,
    reference, referenceLabel: m.yes_sub_title, labelReference,
    precisionWarning: labelReference !== null && reference !== null && labelReference !== reference,
    rules, startAt,requestedAt,
    spec:{asset,startAt,endAt:expiresAt,referenceExact:reference===null?null:String(m.floor_strike),quoteUnit:/U\.S\. dollars|USD/i.test(rules)?'USD':null,oracleProvider:/CF Benchmarks/i.test(rules)?'CF Benchmarks':null,priceStatistic:/average/i.test(rules)?'RTI_AVERAGE':null,operator:/greater than or equal/i.test(rules)?'>=':null},
    resolutionSource: 'Fuente definida por reglas Kalshi; RTI/CF Benchmarks cuando lo indiquen',
    expiresAt, metadataAt: Date.parse(m.updated_time), sourceAt:null, receivedAt: Date.now(),
    pMarket: upBid !== null && upAsk !== null ? (upBid + upAsk) / 2 : null,
    pMarketKind: 'Midpoint YES de Kalshi (no precio ejecutable Coinbase)',
    up: { bid: upBid, ask: upAsk, mid:upBid!==null&&upAsk!==null?(upBid+upAsk)/2:null, sourceAt:null, depthAtAsk: numeric(m.yes_ask_size_fp) },
    down: { bid: downBid, ask: downAsk, mid:downBid!==null&&downAsk!==null?(downBid+downAsk)/2:null, sourceAt:null, depthAtAsk: null },
    url: 'https://kalshi.com/markets/'+m.ticker.split('-')[0].toLowerCase(), status: 'OBSERVADO',
    classification: 'DATA INSUFFICIENT', contractProbability: null, calibrated: false,
    reason: 'Coinbase tiene sus propios costes/interfaz. Sin RTI y modelo del contrato no hay probabilidad independiente ni ventaja demostrada.' };
}
export async function getMarkets(asset, horizon, now = Date.now(), fetcher = fetch) {
  return Promise.all([polymarket, kalshi].map(async f => { try { return await f(asset, horizon, now, fetcher); }
    catch(e) { return { provider:f===polymarket?'POLYMARKET':'KALSHI',venue: f === polymarket ? 'Polymarket' : 'Kalshi / referencia Coinbase Predictions', status: 'UNAVAILABLE', classification: 'DATA INSUFFICIENT', error: e.message, contractProbability: null, receivedAt: Date.now() }; } }));
}
