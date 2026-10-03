// MONEY Ω / MONEY_SPOT_ANALOG_V1_PAPER / v0.1.0
// Pure research module. No contract probability, calibration flag or order path.
export const STRATEGY = 'MONEY_SPOT_ANALOG_V1_PAPER';
export const K = 30;
export const MIN_TRAIN = 40;
export const MIN_NON_FLAT = 15; // provisional engineering floor, not validation
export const MINUTE = 60000;
const mean = a => a.reduce((s, x) => s + x, 0) / a.length;
const clamp = (x, lo, hi) => Math.max(lo, Math.min(hi, x));
export function quantile(values, p) {
  if (!values.length) return null;
  const a = [...values].sort((x, y) => x - y);
  const n = (a.length - 1) * p, i = Math.floor(n);
  return a[i] + (a[Math.min(i + 1, a.length - 1)] - a[i]) * (n - i);
}
export function wilson(up, n) {
  if (n <= 0) return [null, null];
  const z = 1.96, p = up / n, d = 1 + z * z / n;
  const c = (p + z * z / (2 * n)) / d;
  const e = z * Math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d;
  return [clamp(c - e, 0, 1), clamp(c + e, 0, 1)];
}
export function probabilityFromReturns(returns) {
  const up = returns.filter(x => x > 0).length;
  const down = returns.filter(x => x < 0).length;
  const flat = returns.length - up - down;
  const n = up + down;
  return { p: n ? (up + .5) / (n + 1) : null, up, down, flat,
    interval: wilson(up, n), flatFrequency: returns.length ? flat / returns.length : null };
}
export function cleanCandles(input, now, intervalMinutes = 5) {
  const span = intervalMinutes * MINUTE;
  const byTime = new Map();
  for (const raw of input) {
    const c = { t: Number(raw.t), o: Number(raw.o), h: Number(raw.h), l: Number(raw.l), c: Number(raw.c), v: Number(raw.v) };
    if (Object.values(c).some(x => !Number.isFinite(x)) || c.t < 0 || c.t % span !== 0 || c.c <= 0 || c.o <= 0 || c.l <= 0 || c.h < Math.max(c.o, c.c, c.l) || c.l > Math.min(c.o, c.c) || c.v < 0) throw new Error('OHLC inválido');
    if (c.t + span > now) continue; // open/future candle, never train on it
    const prior = byTime.get(c.t);
    if (prior && JSON.stringify(prior) !== JSON.stringify(c)) throw new Error('Timestamp con velas contradictorias');
    byTime.set(c.t, c);
  }
  return [...byTime.values()].sort((a, b) => a.t - b.t);
}
function feature(candles, i, span) {
  const lookback = 60 * MINUTE / span;
  if (!Number.isInteger(lookback) || i < lookback) return null;
  for (let j = i - lookback + 1; j <= i; j++) if (candles[j].t - candles[j - 1].t !== span) return null;
  const r = [];
  for (let j = i - lookback + 1; j <= i; j++) r.push(Math.log(candles[j].c) - Math.log(candles[j - 1].c));
  const m = mean(r), sd = Math.sqrt(mean(r.map(x => (x - m) ** 2)));
  if (!Number.isFinite(sd) || sd < 1e-12) return null;
  const f = [5, 15, 60].map(h => (Math.log(candles[i].c) - Math.log(candles[i - h * MINUTE / span].c)) / (sd * Math.sqrt(h * MINUTE / span)));
  return f.every(Number.isFinite) ? f : null;
}
export function samplesFromCandles(candles, horizon, intervalMinutes = 5) {
  const span = intervalMinutes * MINUTE, steps = horizon / intervalMinutes;
  if (!Number.isInteger(steps)) throw new Error('Horizonte incompatible con la fuente');
  const samples = [];
  for (let i = 0; i + steps < candles.length; i++) {
    const origin = candles[i].t + span;
    if (origin % (horizon * MINUTE) !== 0) continue; // disjoint outcomes per horizon
    const f = feature(candles, i, span);
    if (!f) continue;
    let continuous = true;
    for (let j = i + 1; j <= i + steps; j++) if (candles[j].t - candles[j - 1].t !== span) continuous = false;
    if (!continuous) continue;
    const r = Math.log(candles[i + steps].c) - Math.log(candles[i].c);
    if (Number.isFinite(r)) samples.push({ origin, end: origin + horizon * MINUTE, f, r });
  }
  return samples;
}
function estimate(train, f) {
  if (train.length < MIN_TRAIN) return null;
  // All scaling is fit on eligible training samples only.
  const scales = f.map((_, d) => {
    const a = train.map(x => x.f[d]), m = mean(a);
    return Math.max(.05, Math.sqrt(mean(a.map(v => (v - m) ** 2))));
  });
  const nearest = train.map(x => ({ x, d: x.f.reduce((s, v, j) => s + ((v - f[j]) / scales[j]) ** 2, 0) }))
    .filter(x => Number.isFinite(x.d)).sort((a, b) => a.d - b.d || a.x.origin - b.x.origin).slice(0, K);
  if (nearest.length !== K) return null;
  const returns = nearest.map(x => x.x.r);
  const distribution = probabilityFromReturns(returns);
  if (distribution.p === null || distribution.up + distribution.down < MIN_NON_FLAT) return null;
  return { ...distribution, returns, distance: Math.sqrt(nearest[0].d), samples: nearest.length };
}
export function walkForward(samples, horizon) {
  let n = 0, sum = 0, naive = 0, baseline = 0;
  const bins = Array.from({ length: 10 }, () => ({ n: 0, p: 0, y: 0 }));
  for (let i = Math.max(MIN_TRAIN, samples.length - 80); i < samples.length; i++) {
    const test = samples[i];
    const train = samples.slice(0, i).filter(x => x.end <= test.origin - horizon * MINUTE);
    const result = estimate(train, test.f);
    if (!result || test.r === 0) continue; // conditional on a non-flat outcome
    const y = test.r > 0 ? 1 : 0;
    const base = probabilityFromReturns(train.map(x => x.r)).p ?? .5;
    n++; sum += (result.p - y) ** 2; naive += (.5 - y) ** 2; baseline += (base - y) ** 2;
    const b = bins[Math.min(9, Math.floor(result.p * 10))]; b.n++; b.p += result.p; b.y += y;
  }
  return { n, modelBrier: n ? sum / n : null, naiveBrier: n ? naive / n : null,
    historicalBrier: n ? baseline / n : null, calibrated: false,
    bins: bins.map((b, i) => ({ band: `${i * 10}–${(i + 1) * 10}%`, n: b.n, meanP: b.n ? b.p / b.n : null, observedUp: b.n ? b.y / b.n : null })) };
}
export function forecast(input, horizon, now, source = 'Kraken USD', intervalMinutes = 5) {
  const none = reason => ({ strategyId: STRATEGY, version: '0.1.0', horizon, source,
    p: null, contractProbability: null, calibrated: false, executionEnabled: false,
    classification: 'DATA INSUFFICIENT', reason });
  let candles;
  try { candles = cleanCandles(input, now, intervalMinutes); } catch(e) { return none(e.message); }
  const span = intervalMinutes * MINUTE, last = candles.at(-1);
  if (!last) return none('No hay velas cerradas verificadas');
  const origin = last.t + span, target = origin + horizon * MINUTE;
  if (now - origin >= span) return { ...none('Histórico desactualizado; esperar nueva vela cerrada'), classification: 'NO PLAY', origin, target };
  const f = feature(candles, candles.length - 1, span);
  if (!f) return none('Datos planos, gaps o lookback insuficiente');
  const samples = samplesFromCandles(candles, horizon, intervalMinutes);
  const train = samples.filter(x => x.end <= origin - horizon * MINUTE);
  const result = estimate(train, f);
  if (!result) return none(`Muestra insuficiente: ${train.length}/${MIN_TRAIN} ventanas completas o análogos planos`);
  const projected = [ .1, .5, .9 ].map(q => Math.exp(Math.log(last.c) + quantile(result.returns, q)));
  if (projected.some(x => !Number.isFinite(x) || x <= 0)) return none('Banda numérica inválida; abstención');
  return { strategyId: STRATEGY, version: '0.1.0', horizon, source,
    p: result.p, interval: result.interval, flatFrequency: result.flatFrequency,
    direction: result.p > .5 ? 'UP' : result.p < .5 ? 'DOWN' : 'NEUTRAL',
    reference: last.c, origin, target, issuedAt: now, validUntil: Math.min(target, origin + span),
    medianPrice: projected[1], priceBand: [projected[0], projected[2]], samples: result.samples,
    trainCount: train.length, candleCount: candles.length, intervalMinutes,
    backtest: walkForward(samples, horizon), contractProbability: null, calibrated: false,
    executionEnabled: false, classification: 'WATCH', confidence: 'MUY BAJA',
    reason: 'Pspot experimental condicionada a movimiento (excluye empates). No estimación de contrato ni señal de compra.',
    thesis: 'Patrones trailing5/15/60m comparados con 30 análogos anteriores de la misma fuente.',
    invalidation: 'Vencimiento, datos viejos/gaps, cambio de fuente, quiebre de régimen o comparación con un oráculo diferente.',
    redTeam: 'Análogos dependientes y muestra corta; noticias, volatilidad y selección de vecinos pueden invalidar frecuencias. Ninguna ventaja neta demostrada.' };
}
