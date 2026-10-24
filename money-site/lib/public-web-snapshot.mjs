// Derived from MONEY AppDeploy1.1 canonical public research source. READ_ONLY; no database, cron or transaction adapter.
import {ASSETS,FRAMES,SPAN} from './canonical-types.mjs';
import {forecast,cleanCandles,numberOrNull,quoteState,comparable,windowFor,quantile} from './canonical-research.mjs';
import {absent,object,parsePolymarket,parsePredict,parseCoinbase,polymarketDetailTargets} from './public-web.mjs';
const VERSION = '1.1.0'         ;
const PAIRS                        = { BTC: 'XBTUSD', ETH: 'ETHUSD', SOL: 'SOLUSD', DOGE: 'XDGUSD', XRP: 'XRPUSD', BNB: 'BNBUSD' };
const URLS = {
poly5: 'https://polymarket.com/crypto/5M', poly15: 'https://polymarket.com/crypto/15M', poly60: 'https://polymarket.com/crypto/hourly',
  polyOverview: 'https://polymarket.com/crypto',
  predict: 'https://predict.fun/markets/crypto', coinbase: 'https://www.coinbase.com/predictions/crypto/15%20min',
  base: 'https://www.base.app/', metamask: 'https://metamask.io/prediction-markets', trust: 'https://trustwallet.com/prediction-markets', grok: 'https://themoney.grok.me/',
};
const HOSTS = new Set(['api.kraken.com', 'api.coinbase.com', 'polymarket.com', 'predict.fun', 'www.coinbase.com', 'www.base.app', 'metamask.io', 'trustwallet.com', 'themoney.grok.me']);
                                                                                                
const cache = new Map                                           ();
const pending = new Map                          ();
const cooldown = new Map                ();
async function readPublic(url        , ttl        )                   {
  const u = new URL(url);
  if (u.protocol !== 'https:' || !HOSTS.has(u.hostname) || u.username || u.password || u.port || u.hash) throw Error('Fuente no autorizada');
  const cached = cache.get(url);
  if (cached && cached.until > Date.now()) return cached.value;
  const existing = pending.get(url); if (existing) return existing;
  const job = (async ()                   => {
    if ((cooldown.get(u.hostname) ?? 0) > Date.now()) return { body: null, receivedAt: Date.now(), status: 429, note: 'Fuente en pausa.' };
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 6500);
    let result         ;
    try {
      const response = await fetch(url, { method: 'GET', redirect: 'manual', signal: controller.signal, headers: { 'user-agent': 'MONEY/1.1 Public research', 'accept': 'text/html,application/json' } });
      if (response.status === 403 || response.status === 429 || response.status === 451) cooldown.set(u.hostname, Date.now() + (response.status === 451 ? 3600000 : 120000));
      if (!response.ok) result = { body: null, receivedAt: Date.now(), status: response.status, note: 'La fuente no entregó contenido público.' };
      else {
        if (Number(response.headers.get('content-length') ?? 0) > 4000000) throw Error('Página demasiado grande');
        const reader = response.body?.getReader(); if (!reader) throw Error('Respuesta vacía');
        const chunks               = []; let size = 0;
        while (true) { const part = await reader.read(); if (part.done) break; size += part.value.length; if (size > 4000000) { await reader.cancel(); throw Error('Respuesta supera el límite'); } chunks.push(part.value); }
        const bytes = new Uint8Array(size); let position = 0;
        for (const chunk of chunks) { bytes.set(chunk, position); position += chunk.length; }
        result = { body: new TextDecoder().decode(bytes), receivedAt: Date.now(), status: response.status, note: 'Lectura pública.' };
      }
    } catch { result = { body: null, receivedAt: Date.now(), status: null, note: 'No se pudo leer la fuente.' }; }
    finally { clearTimeout(timer); }
    cache.set(url, { until: Date.now() + ttl, value: result }); return result;
  })();
  pending.set(url, job); try { return await job; } finally { pending.delete(url); }
}
function decoded(reading         )          { if (!reading.body) return null; try { return JSON.parse(reading.body)           ; } catch { return null; } }
async function history(asset       , interval = 5)                    {
  const reading = await readPublic('https://api.kraken.com/0/public/OHLC?pair=' + PAIRS[asset] + '&interval=' + interval, 15000);
  const raw = object(decoded(reading)); if (!raw || !Array.isArray(raw.error) || raw.error.length) return [];
  const result = object(raw.result); if (!result) return [];
  const entries = Object.entries(result).filter(([k, v]) => k !== 'last' && Array.isArray(v));
  if (entries.length !== 1) return [];
  const candles           = [];
  const sourceRows = entries[0][1]             ;
  for (const [index, row] of sourceRows.entries()) {
    if (!Array.isArray(row) || row.length < 8) return [];
    const values = [row[0], row[1], row[2], row[3], row[4], row[6]].map(numberOrNull);
    if (values.some(n => n === null)) return [];
    // Kraken's final OHLC row is always the uncommitted interval. Cache must retain that fact.
    candles.push({ t: values[0]  * 1000, o: values[1] , h: values[2] , l: values[3] , c: values[4] , v: values[5] , confirmed: index < sourceRows.length - 1, observedAt: reading.receivedAt });
  }
  return candles;
}
async function spots(asset       ) {
  const responses = await Promise.all([
    readPublic('https://api.kraken.com/0/public/Ticker?pair=' + PAIRS[asset], 10000),
    readPublic('https://api.coinbase.com/v2/prices/' + asset + '-USD/spot', 10000),
  ]);
  const sources                          = [];
  const kraken = object(decoded(responses[0])); const result = object(kraken?.result);
  const krakenValues = result ? Object.values(result) : [];
  const c = object(krakenValues[0])?.c;
  const kp = Array.isArray(c) ? numberOrNull(c[0]) : null;
  if (kp !== null && kp > 0 && krakenValues.length === 1 && Array.isArray(kraken?.error) && kraken.error.length === 0) sources.push({ name: 'Kraken', value: kp, unit: 'USD', receivedAt: responses[0].receivedAt, quoteAt: null });
  const coinbase = object(object(decoded(responses[1]))?.data);
  const cp = numberOrNull(coinbase?.amount);
  if (cp !== null && cp > 0 && coinbase?.currency === 'USD' && coinbase?.base === asset) sources.push({ name: 'Coinbase', value: cp, unit: 'USD', receivedAt: responses[1].receivedAt, quoteAt: null });
  const spot = sources.length ? sources.reduce((s, x) => s + x.value, 0) / sources.length : null;
  return { spot, sources };
}
async function webPages() {
const reads = await Promise.all([URLS.poly5, URLS.poly15, URLS.poly60, URLS.predict, URLS.coinbase, URLS.polyOverview].map(url => readPublic(url, 30000)));
  return { poly: { '5m': reads[0], '15m': reads[1], '1h': reads[2] }, predict: reads[3], coinbase: reads[4], polyOverview: reads[5] };
}
                                                                    
let bundleCache                = null;
let bundlePending                         = null;
async function bundle()                  {
  const now = Date.now();
  if (bundleCache && now - bundleCache.captured < 12000 && windowFor('5m', bundleCache.captured).start === windowFor('5m', now).start) return bundleCache;
  if (bundlePending) return bundlePending;
  bundlePending = (async () => {
    const [pages, inputs] = await Promise.all([webPages(), Promise.all(ASSETS.map(async symbol => {
      const [candles, prices] = await Promise.all([history(symbol), spots(symbol)]);
      return { symbol, candles, prices };
    }))]);
    const hourlyStart = windowFor('1h', Date.now()).start;
    const targets = pages.poly['1h'].body ? polymarketDetailTargets(pages.poly['1h'].body, hourlyStart) : [];
    const hourlyDetails = await Promise.all(targets.map(async target => ({ ...target, reading: await readPublic(target.url, 30000) })));
    const completed = Date.now();
    const rows = Object.fromEntries(FRAMES.map(f => [f, []              ]))                             ;
    for (const input of inputs) {
      let priceHistory                           = [];
      try { priceHistory = cleanCandles(input.candles, completed).slice(-13).map(c => ({ at: c.t + 300000, price: c.c })); } catch { /* Invalid charts remain empty. */ }
      const horizons = FRAMES.map(timeframe => { const w = windowFor(timeframe, completed); return { timeframe, research: forecast(input.candles, timeframe, completed), windowStart: w.start, windowEnd: w.end }; });
      const sides = new Set(horizons.map(h => h.research.side).filter(s => s !== 'WAIT'));
      for (const horizon of horizons) {
        const frame = horizon.timeframe, p = pages.poly[frame];
        let poly = p.body ? parsePolymarket(p.body, input.symbol, frame, horizon.windowStart, p.receivedAt) : absent('Polymarket', frame === '1h' ? URLS.poly60 : frame === '5m' ? URLS.poly5 : URLS.poly15, p.note);
        if (poly.up === null && frame === '1h') {
          const detail = hourlyDetails.find(d => d.asset === input.symbol);
          if (detail?.reading.body) {
            const verified = parsePolymarket(detail.reading.body, input.symbol, frame, horizon.windowStart, detail.reading.receivedAt);
            if (verified.contractId === detail.contractId && verified.up !== null) poly = { ...verified, marketUrl: detail.url };
          }
        }
        if (poly.up === null && pages.polyOverview.body) {
          const overview = parsePolymarket(pages.polyOverview.body, input.symbol, frame, horizon.windowStart, pages.polyOverview.receivedAt);
          if (overview.up !== null) poly = overview;
        }
        const predict = pages.predict.body ? parsePredict(pages.predict.body, input.symbol, frame, horizon.windowStart, pages.predict.receivedAt) : absent('Predict', URLS.predict, pages.predict.note);
        const cb = pages.coinbase.body ? parseCoinbase(pages.coinbase.body, input.symbol, frame, pages.coinbase.receivedAt) : absent('Coinbase · Kalshi', URLS.coinbase, pages.coinbase.note);
        const venues = [poly, predict, cb].map(q => ({ ...q, status: quoteState(q, completed) }));
        const pair = venues.find((a, i) => venues.some((b, j) => j > i && comparable(a, b, completed)));
        const partner = pair ? venues.find(q => q !== pair && comparable(pair, q, completed)) : undefined;
        rows[frame].push({ symbol: input.symbol, spot: input.prices.spot, spotSources: input.prices.sources, windowStart: horizon.windowStart, windowEnd: horizon.windowEnd,
          startPrice: horizon.research.reference, changePct: horizon.research.reference !== null && horizon.research.lastClosedPrice !== null ? (horizon.research.lastClosedPrice / horizon.research.reference - 1) * 100 : null,
          research: horizon.research, horizons, horizonsDisagree: sides.size > 1, venues, priceHistory,
          divergencePp: pair?.up !== null && pair?.up !== undefined && partner?.up !== null && partner?.up !== undefined ? Math.abs(pair.up - partner.up) : null,
          publishedDifferencePp: venues[0].up !== null && venues[1].up !== null && venues[0].status !== 'STALE' && venues[1].status !== 'STALE' ? Math.abs(venues[0].up - venues[1].up) : null,
          comparison: pair ? 'MISMO CONTRATO · cotizaciones comparables' : 'Comparación pendiente: falta verificar contrato o vigencia.',
        });
      }
    }
    const value = { captured: completed, rows }; bundleCache = value; return value;
  })();
  try { return await bundlePending; } finally { bundlePending = null; }
}
function snapshot(data        , frame       , serverReceivedAt        )           {
  const w = windowFor(frame, data.captured);
  return { version: VERSION, asOf: data.captured, serverReceivedAt, serverTime: Date.now(), timeframe: frame, windowStart: w.start, windowEnd: w.end, expiresAt: Math.min(w.end, data.captured + 45000), assets: data.rows[frame],
    sourcePolicy: 'Cuotas desde HTML público. Sin APIs de Polymarket/Predict. Spot USD: Kraken/Coinbase.',
    notice: 'La opción dorada es un sesgo experimental de Kraken USD. Probabilidad contractual sin estimar; decisión de operación: ESPERAR hasta verificar contrato, costes y vigencia.',
  };
}

export async function publicWebSnapshot(horizon){const frame=({5:'5m',15:'15m',60:'1h'})[horizon];if(!frame)throw Error('Horizonte inválido');const received=Date.now();const result=snapshot(await bundle(),frame,received);return {...result,transport:'DIRECT_PUBLIC_HTML_RSC',archiveState:'LIVE_VIEW_ONLY',archiveWriterEnabled:false,notice:result.notice+' Esta vista pública no guarda capturas ni sustituye al cron detenido.'};}
