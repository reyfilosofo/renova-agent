// Derived from MONEY AppDeploy1.1 canonical public research source. READ_ONLY; no database, cron or transaction adapter.
import { SPAN,                                                       } from './canonical-types.mjs';

export const MODEL = 'MONEY_FIXED_WINDOW_ANALOG_PAPER_V1';
const FIVE = 300000;
const mean = (a          ) => a.reduce((s, x) => s + x, 0) / a.length;
export function numberOrNull(value         )                {
  if (value === null || value === undefined || value === '' || typeof value === 'boolean') return null;
  const n = typeof value === 'number' ? value : typeof value === 'string' && value.trim() !== '' ? Number(value) : NaN;
  return Number.isFinite(n) ? n : null;
}
export function quantile(a          , p        ) {
  if (!a.length) return null;
  const sorted = [...a].sort((x, y) => x - y);
  const position = (sorted.length - 1) * p;
  const i = Math.floor(position);
  return sorted[i] + (sorted[Math.min(i + 1, sorted.length - 1)] - sorted[i]) * (position - i);
}
export function windowFor(frame       , now        ) {
  const start = Math.floor(now / SPAN[frame]) * SPAN[frame];
  return { start, end: start + SPAN[frame] };
}
export function secondsRemaining(end        , now        ) {
  return Math.max(0, Math.ceil((end - now) / 1000));
}
export function cleanCandles(input          , now        ) {
  const map = new Map                ();
  for (const c of input) {
    if ([c.t, c.o, c.h, c.l, c.c, c.v].some(v => !Number.isFinite(v)) || c.t % FIVE !== 0 || c.t < 0 || c.o <= 0 || c.c <= 0 || c.l <= 0 || c.h < Math.max(c.o, c.c, c.l) || c.l > Math.min(c.o, c.c) || c.v < 0 || (c.observedAt !== undefined && !Number.isFinite(c.observedAt))) throw Error('OHLC inválido');
    if (c.confirmed === false || c.t + FIVE > Math.min(now, c.observedAt ?? now)) continue;
    const prior = map.get(c.t);
    if (prior && JSON.stringify(prior) !== JSON.stringify(c)) throw Error('Velas contradictorias');
    map.set(c.t, c);
  }
  return [...map.values()].sort((a, b) => a.t - b.t);
}
function feature(candles          , i        , reference         , windowSteps         ) {
  if (i < 12) return null;
  const returns           = [];
  for (let j = i - 11; j <= i; j++) {
    if (candles[j].t - candles[j - 1].t !== FIVE) return null;
    returns.push(Math.log(candles[j].c) - Math.log(candles[j - 1].c));
  }
  const m = mean(returns);
  const sd = Math.sqrt(mean(returns.map(r => (r - m) ** 2)));
  if (!Number.isFinite(sd) || sd < 1e-12) return null;
  const values = [1, 3, 12].map(k => (Math.log(candles[i].c) - Math.log(candles[i - k].c)) / (sd * Math.sqrt(k)));
  if (reference !== undefined && windowSteps !== undefined) values.push((Math.log(candles[i].c) - Math.log(reference)) / (sd * Math.sqrt(windowSteps)));
  return values.every(Number.isFinite) ? values : null;
}
export function wilson(up        , n        )                   {
  const z = 1.96, p = up / n, d = 1 + z * z / n;
  const center = (p + z * z / (2 * n)) / d;
  const error = z * Math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d;
  return [Math.max(0, center - error), Math.min(1, center + error)];
}
export function forecast(raw          , frame       , now        )           {
  const w = windowFor(frame, now);
  const base           = {
    strategy: MODEL, pUp: null, intervalUp: null, side: 'WAIT', sideProbability: null,
    sideInterval: null, origin: null, target: w.end, validUntil: null,
    reference: null, lastClosedPrice: null, median: null, priceBand: null,
    samples: 0, trainingCount: 0, flatFrequency: null, reason: 'Datos insuficientes.',
    contractProbability: null, calibrated: false, recommendation: 'WAIT', confidence: 'MUY BAJA',
  };
  let candles          ;
  try { candles = cleanCandles(raw, now); } catch { return { ...base, reason: 'Histórico inconsistente.' }; }
  const last = candles[candles.length - 1];
  if (!last) return base;
  const origin = last.t + FIVE;
  if (now - origin >= FIVE || origin > now) return { ...base, reason: 'Histórico vencido.' };
  // Opening values are observable at their timestamp. Never use an open candle's close as training data.
  const boundary = raw.filter(c => c.t === w.start && Number.isFinite(c.o) && c.o > 0);
  if (boundary.length !== 1) return { ...base, reason: 'Apertura exacta no verificada.' };
  const reference = boundary[0].o;
  const windowSteps = SPAN[frame] / FIVE;
  const phase = (origin - w.start) / FIVE;
  if (!Number.isInteger(phase) || phase < 0 || phase >= windowSteps) return base;
  const f = feature(candles, candles.length - 1, reference, windowSteps);
  if (!f) return { ...base, reason: 'Velas planas, huecos o lookback insuficiente.' };
  const span = SPAN[frame];
  const train                                          = [];
  for (let i = 12; i + windowSteps - phase < candles.length; i++) {
    const t = candles[i].t + FIVE;
    const pastStart = t - phase * FIVE;
    const end = pastStart + span;
    if (pastStart % span !== 0 || end > origin - span) continue;
    const openingIndex = i + 1 - phase;
    if (openingIndex < 0 || candles[openingIndex].t !== pastStart) continue;
    const pastReference = candles[openingIndex].o;
    const fi = feature(candles, i, pastReference, windowSteps);
    if (!fi) continue;
    let gap = false;
    const endIndex = i + windowSteps - phase;
    for (let j = Math.max(1, openingIndex); j <= endIndex; j++) if (candles[j].t - candles[j - 1].t !== FIVE) gap = true;
    const r = Math.log(candles[endIndex].c) - Math.log(pastReference);
    if (!gap && candles[endIndex].t + FIVE === end && Number.isFinite(r)) train.push({ f: fi, r, t });
  }
  const common = { ...base, origin, reference, lastClosedPrice: last.c, validUntil: Math.min(origin + FIVE, w.end), trainingCount: train.length };
  if (train.length < 40) return { ...common, reason: 'Menos de 40 ventanas históricas completas.' };
  const scales = f.map((_, d) => {
    const values = train.map(x => x.f[d]), m = mean(values);
    return Math.max(0.05, Math.sqrt(mean(values.map(v => (v - m) ** 2))));
  });
  if (!scales.every(s => Number.isFinite(s) && s > 0)) return { ...common, reason: 'Escalas numéricas inválidas.' };
  const nearest = train.map(x => ({ ...x, distance: x.f.reduce((s, v, d) => s + ((v - f[d]) / scales[d]) ** 2, 0) }))
    .filter(x => Number.isFinite(x.distance)).sort((a, b) => a.distance - b.distance || a.t - b.t).slice(0, 30);
  if (nearest.length < 30) return { ...common, reason: 'Menos de 30 análogos numéricamente válidos.' };
  const prices = nearest.map(x => Math.exp(Math.log(reference) + x.r));
  if (prices.some(x => !Number.isFinite(x) || x <= 0)) return { ...common, reason: 'Proyección numérica inválida.' };
  // Count the signed observed return, not exp(log(reference)+r), whose rounding can turn flats into Up.
  const up = nearest.filter(x => x.r > 0).length;
  const down = nearest.filter(x => x.r < 0).length;
  const n = up + down;
  if (n < 15) return { ...common, samples: nearest.length, flatFrequency: (nearest.length - n) / nearest.length, reason: 'Demasiados análogos planos.' };
  const pUp = (up + 0.5) / (n + 1);
  const interval = wilson(up, n);
  const side = interval[0] > 0.5 ? 'UP' : interval[1] < 0.5 ? 'DOWN' : 'WAIT';
  return {
    ...common, pUp, intervalUp: interval, side,
    sideProbability: side === 'WAIT' ? null : side === 'UP' ? pUp : 1 - pUp,
    sideInterval: side === 'WAIT' ? null : side === 'UP' ? interval : [1 - interval[1], 1 - interval[0]],
    median: quantile(prices, 0.5), priceBand: [quantile(prices, 0.1) , quantile(prices, 0.9) ],
    samples: nearest.length, flatFrequency: (nearest.length - n) / nearest.length,
    reason: side === 'WAIT' ? 'El intervalo incluye 50%; esperar.' : 'Sesgo de 30 ventanas anteriores en la misma fase, Kraken USD; no es probabilidad de ganar el contrato.',
  };
}
export function quoteState(q          , now        )                     {
  if (q.status === 'UNAVAILABLE' || q.status === 'NO_VERIFICADO' || q.status === 'CONTRACT_MISMATCH') return q.status;
  if (q.windowEnd !== null && q.windowEnd <= now) return 'STALE';
  if (q.receivedAt === null || now - q.receivedAt > 90000) return 'STALE';
  if (q.quoteAt === null) return 'PUBLICADO';
  return q.quoteAt > now + 5000 || now - q.quoteAt > 30000 ? 'STALE' : 'LIVE';
}
export function comparable(a          , b          , now        ) {
  // Same underlying contract ID is sufficient for wallet mirrors, never for distinct venues.
  if (quoteState(a, now) !== 'LIVE' || quoteState(b, now) !== 'LIVE') return false;
  return a.contractId !== null && a.contractId === b.contractId && a.resolutionSource !== null && a.resolutionSource === b.resolutionSource && a.windowStart === b.windowStart && a.windowEnd === b.windowEnd && a.reference !== null && a.reference === b.reference && a.priceKind === b.priceKind && Math.abs(a.quoteAt  - b.quoteAt ) <= 3000;
}
