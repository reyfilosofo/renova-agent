// Derived from MONEY AppDeploy1.1 canonical public research source. READ_ONLY; no database, cron or transaction adapter.
import {                                        SPAN, ASSETS } from './canonical-types.mjs';
import { numberOrNull } from './canonical-research.mjs';

                                   
export function object(value         )             { return value && typeof value === 'object' && !Array.isArray(value) ? value        : null; }
function array(value         )            {
  if (Array.isArray(value)) return value;
  if (typeof value !== 'string') return [];
  try { const parsed          = JSON.parse(value); return Array.isArray(parsed) ? parsed : []; } catch { return []; }
}
export function timestamp(value         )                {
  if (typeof value !== 'string' || !/^\d{4}-\d\d-\d\dT/.test(value)) return null;
  const n = Date.parse(value); return Number.isFinite(n) ? n : null;
}
function jsonObjects(text        )            {
  const results            = [];
  // Flight contains length-prefixed text records with arbitrary braces. Parse only complete JSON rows.
  for (const line of text.split('\n')) {
    if (results.length >= 4096) break;
    const record = line.match(/^[0-9a-f]+:([\[{][\s\S]*)$/i);
    if (!record) continue;
    try { results.push(JSON.parse(record[1])); } catch { /* Do not infer JSON from text records. */ }
  }
  return results;
}
export function embeddedObjects(html        )        {
  const roots            = [];
  const flight           = [];
  for (const match of html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/gi)) {
    const body = match[1];
    if (body.trim().startsWith('{')) { try { roots.push(JSON.parse(body)); } catch { /* Not JSON. */ } }
    const push = body.match(/^\s*self\.__next_f\.push\((\[[\s\S]*\])\)\s*;?\s*$/);
    if (push) {
      try {
        const record          = JSON.parse(push[1]);
        if (Array.isArray(record) && record[0] === 1 && typeof record[1] === 'string') flight.push(record[1]);
      } catch { /* Do not execute scripts or evaluate JavaScript. */ }
    }
  }
  roots.push(...jsonObjects(flight.join('')));
  const found        = [], queue = [...roots];
  let visited = 0;
  while (queue.length && visited++ < 40000) {
    const value = queue.pop();
    if (Array.isArray(value)) queue.push(...value);
    else { const obj = object(value); if (obj) { found.push(obj); queue.push(...Object.values(obj)); } }
  }
  return found;
}
function queryData(html        , prefix          )        {
  const objects = embeddedObjects(html);
  const roots = objects.filter(q => Array.isArray(q.queryKey) && prefix.every((key, i) => q.queryKey instanceof Array && q.queryKey[i] === key))
    .map(q => object(q.state)?.data);
  const found        = [], queue = [...roots]; let visited = 0;
  while (queue.length && visited++ < 20000) {
    const value = queue.pop();
    if (Array.isArray(value)) queue.push(...value);
    else { const obj = object(value); if (obj) { found.push(obj); queue.push(...Object.values(obj)); } }
  }
  return found;
}
function observedUrl(html        , origin        , path        , fallback        ) {
  for (const match of html.matchAll(/\bhref\s*=\s*['"]([^'"]+)['"]/gi)) {
    try { const u = new URL(match[1].replace(/&amp;/g, '&'), origin); if (u.origin === origin && u.pathname === path && !u.username && !u.password) return u.origin + u.pathname; } catch { /* Reject malformed or unsupported links. */ }
  }
  return fallback;
}
export function absent(name        , url        , note        , receivedAt                = null)           {
  return { name, up: null, down: null, status: receivedAt === null ? 'UNAVAILABLE' : 'NO_VERIFICADO', sourceType: 'Página pública', quoteAt: null, receivedAt, marketUrl: url, contractId: null, windowStart: null, windowEnd: null, reference: null, referenceUnit: null, resolutionSource: null, rules: null, priceKind: 'No disponible', fee: null, note };
}
function probability(value         )                {
  const n = numberOrNull(value); return n !== null && n >= 0 && n <= 1 ? n * 100 : null;
}
function uniqueQuote(matches            , none          ) {
  const ids = new Set(matches.map(q => q.contractId));
  if (ids.size !== 1) return none;
  const first = matches[0];
  return matches.every(q => q.up === first.up && q.down === first.down && q.reference === first.reference && q.windowStart === first.windowStart && q.windowEnd === first.windowEnd) ? first : none;
}
const WORDS                          = { BTC: ['btc', 'bitcoin'], ETH: ['eth', 'ethereum'], SOL: ['sol', 'solana'], DOGE: ['doge', 'dogecoin'], XRP: ['xrp'], BNB: ['bnb'] };
function slugAsset(slug        , asset       ) { return WORDS[asset].some(w => slug.startsWith(w + '-updown-') || slug.startsWith(w + '-up-or-down-')); }
function nonempty(...values           )                { return values.find((v)              => typeof v === 'string' && v.trim() !== '') ?? null; }
export function polymarketDetailTargets(html        , start        )                                                      {
  const objects = queryData(html, ['crypto-markets']);
  const targets                                                      = [];
  for (const asset of ASSETS) {
    const candidates                                                      = [];
    for (const event of objects) {
      if (typeof event.slug !== 'string' || !slugAsset(event.slug, asset) || event.active !== true || event.closed !== false || timestamp(event.endDate) !== start + SPAN['1h'] || !Array.isArray(event.markets)) continue;
      for (const item of event.markets) {
        const market = object(item);
        if (!market || market.slug !== event.slug || market.active !== true || market.closed !== false || typeof market.conditionId !== 'string' || !/^0x[a-fA-F0-9]{64}$/.test(market.conditionId)) continue;
        const url = observedUrl(html, 'https://polymarket.com', '/event/' + event.slug, '');
        if (url) candidates.push({ asset, url, contractId: 'polymarket:' + market.conditionId });
      }
    }
    if (candidates.length && new Set(candidates.map(c => c.contractId)).size === 1) targets.push(candidates[0]);
  }
  return targets;
}
export function parsePolymarket(html        , asset       , frame       , start        , receivedAt        )           {
  const url = 'https://polymarket.com/crypto/' + (frame === '1h' ? 'hourly' : frame === '5m' ? '5M' : '15M');
  const none = absent('Polymarket', url, 'La página no entregó un contrato y cuotas inequívocos para esta ventana.', receivedAt);
  const objects = [...queryData(html, ['crypto-markets']), ...queryData(html, ['/api/event/slug'])];
  const events = objects.filter(e => typeof e.slug === 'string' && slugAsset(e.slug, asset) && Array.isArray(e.markets));
  const matches             = [];
  for (const event of events) {
    const eventEnd = timestamp(event.endDate);
    if (eventEnd !== start + SPAN[frame] || event.closed !== false || event.active !== true) continue;
    for (const item of event.markets             ) {
      const market = object(item);
      if (!market || market.closed !== false || market.active !== true || market.slug !== event.slug || typeof market.conditionId !== 'string' || !/^0x[a-fA-F0-9]{64}$/.test(market.conditionId)) continue;
      const eventStart = timestamp(event.startTime) ?? timestamp(market.eventStartTime);
      if (eventStart !== start || (timestamp(market.endDate) !== null && timestamp(market.endDate) !== eventEnd)) continue;
      const outcomes = array(market.outcomes).map(v => typeof v === 'string' ? v.toLowerCase() : '');
      if (outcomes.length !== 2 || new Set(outcomes).size !== 2 || !outcomes.includes('up') || !outcomes.includes('down')) continue;
      const prices = array(market.outcomePrices);
      if (prices.length !== 2) continue;
      const up = probability(prices[outcomes.indexOf('up')]);
      const down = probability(prices[outcomes.indexOf('down')]);
      if (up === null || down === null) continue;
      const description = nonempty(market.description, event.description);
      const resolution = nonempty(market.resolutionSource, market.resolution_source, event.resolutionSource);
      const metadata = object(event.eventMetadata);
      const reference = numberOrNull(metadata?.priceToBeat);
      matches.push({ ...none, up, down, status: 'PUBLICADO', marketUrl: observedUrl(html, 'https://polymarket.com', '/event/' + event.slug, url),
        contractId: 'polymarket:' + market.conditionId, windowStart: eventStart, windowEnd: eventEnd,
        reference: reference !== null && reference > 0 ? reference : null,
        resolutionSource: resolution,
        referenceUnit: resolution && /_USDT(?:[/?]|$)/i.test(resolution) ? 'USDT' : resolution && /-usd(?:[/?]|$)/i.test(resolution) ? 'USD' : null,
        rules: description?.slice(0, 6000) ?? null, priceKind: 'Precio publicado; no libro ejecutable',
        note: 'Cuotas publicadas en HTML. Hora del tick y coste total no verificados. Las fechas de caché no son fechas de cotización.',
      });
    }
  }
  return uniqueQuote(matches, none);
}
function edges(value         )        {
  const obj = object(value);
  return array(obj?.edges).map(e => object(object(e)?.node)).filter((x)           => x !== null);
}
export function parsePredict(html        , asset       , frame       , start        , receivedAt        )           {
  const none = absent('Predict', 'https://predict.fun/markets/crypto', 'No hay cuotas web verificables para este activo y corte.', receivedAt);
  const objects = queryData(html, ['categories', 'infinite']);
  const matches             = [];
  for (const category of objects) {
    if (typeof category.slug !== 'string' || !slugAsset(category.slug, asset) || category.marketVariant !== 'CRYPTO_UP_DOWN' || category.status !== 'OPEN' || timestamp(category.startsAt) !== start || timestamp(category.endsAt) !== start + SPAN[frame]) continue;
    const markets = edges(category.markets);
    for (const market of markets) {
      const outcomes = edges(market.outcomes);
      const first = outcomes.find(o => Number(o.index) === 1);
      const second = outcomes.find(o => Number(o.index) === 2);
      if (outcomes.length !== 2 || !first || !second || String(first.name).toLowerCase() !== 'up' || String(second.name).toLowerCase() !== 'down') continue;
      const chance = numberOrNull(market.chancePercentage);
      if (chance === null || chance < 0 || chance > 100 || market.status !== 'REGISTERED' || market.isTradingEnabled !== true || typeof market.id !== 'string') continue;
      const metadata = array(category.marketData).map(object).find(m => m?.marketId === market.id);
      if (metadata?.priceFeedSymbol !== asset + 'USD' && metadata?.priceFeedSymbol !== asset + 'USDT') continue;
      const opening = numberOrNull(metadata?.startPrice);
      matches.push({ ...none, up: chance, down: 100 - chance, status: 'PUBLICADO',
        marketUrl: observedUrl(html, 'https://predict.fun', '/market/' + category.slug, none.marketUrl), contractId: 'predict:' + market.id,
        windowStart: start, windowEnd: start + SPAN[frame],
        reference: opening !== null && opening > 0 ? opening : null,
        referenceUnit: metadata?.priceFeedSymbol === asset + 'USDT' ? 'USDT' : 'USD',
        resolutionSource: typeof metadata?.priceFeedProvider === 'string' && typeof metadata?.priceFeedSymbol === 'string' ? metadata.priceFeedProvider + ':' + metadata.priceFeedSymbol : null,
        rules: typeof market.description === 'string' ? market.description.slice(0, 6000) : null,
        priceKind: 'Indicador publicado; abajo es complemento',
        note: 'Indicador de la página; abajo = 100 − arriba. No son dos ofertas de compra. Hora de cuota y comisiones no verificadas.',
      });
    }
  }
  return uniqueQuote(matches, none);
}
export function parseCoinbase(html        , asset       , frame       , receivedAt        ) {
  const url = 'https://www.coinbase.com/predictions/crypto/' + (frame === '15m' ? '15%20min' : frame === '1h' ? 'Hourly' : '');
  // Marketing/card text omits contract identifiers, exact windows and tick timestamps.
  // Never borrow YES/NO from a neighboring card or translate an hourly threshold into Up/Down.
  const q = absent('Coinbase · Kalshi', url, 'La página pública no permitió verificar contrato, ventana y cuotas de ' + asset + '.', receivedAt);
  if (frame === '1h') return { ...q, status: 'CONTRACT_MISMATCH'         , note: 'Hourly puede mostrar contratos de umbral; no se convierte a Arriba/Abajo.' };
  if (!html || html.includes('Site Unavailable')) return { ...q, status: 'UNAVAILABLE'         , note: 'El servidor no pudo leer la página pública de Coinbase.' };
  return q;
}
