// Public observations only. Price differences never authorize execution.
export const HORIZONS = [5, 15, 60];
export function currentWindow(now, horizon) {
  if (!Number.isFinite(now) || !HORIZONS.includes(horizon)) throw new Error('Ventana inválida');
  const startAt = Math.floor(now / (horizon * 60000)) * horizon * 60000;
  return { startAt, endAt: startAt + horizon * 60000 };
}
const hourlyNames = { BTC: 'bitcoin', ETH: 'ethereum', SOL: 'solana', XRP: 'xrp', DOGE: 'dogecoin', BNB: 'bnb' };
export function polymarketCandidate(asset, horizon, now) {
  if (!hourlyNames[asset]) throw new Error('Activo inválido');
  const window = currentWindow(now, horizon);
  if (horizon !== 60) return { ...window, slug: `${asset.toLowerCase()}-updown-${horizon}m-${window.startAt / 1000}` };
  const parts = new Intl.DateTimeFormat('en-US', { timeZone: 'America/New_York', month: 'long', day: 'numeric', year: 'numeric', hour: 'numeric', hour12: true }).formatToParts(window.startAt);
  const p = Object.fromEntries(parts.map(x => [x.type, x.value.toLowerCase()]));
  // Year is required by current verified hourly contracts. Validate the response
  // against UTC start/end too; ET's repeated hour never establishes identity.
  return { ...window, slug: `${hourlyNames[asset]}-up-or-down-${p.month}-${p.day}-${p.year}-${p.hour}${p.dayPeriod}-et` };
}
const prob = x => typeof x === 'number' && Number.isFinite(x) && x >= 0 && x <= 1;
export function freshness(m, now, maxAgeMs = 30000) {
  if (!m || m.status !== 'OBSERVADO') return { grade: 'UNAVAILABLE', sourceAgeMs: null, label: m?.status ?? 'SIN DATOS' };
  if (!Number.isFinite(m.expiresAt) || now >= m.expiresAt) return { grade: 'EXPIRED', sourceAgeMs: null, label: 'VENCIDO' };
  if (!Number.isFinite(m.receivedAt) || m.receivedAt > now + 5000) return { grade: 'CLOCK_INVALID', sourceAgeMs: null, label: 'RELOJ INVÁLIDO' };
  if (now - m.receivedAt > maxAgeMs) return { grade: 'STALE', sourceAgeMs: null, label: 'RECEPCIÓN ANTIGUA' };
  const timestamps = [m.up?.sourceAt, m.down?.sourceAt].filter(Number.isFinite);
  // Market updated_time is metadata, not a book timestamp.
  if (timestamps.length < 2) return { grade: 'UNKNOWN', sourceAgeMs: null, label: 'FRESCURA DE FUENTE NO VERIFICADA' };
  if (timestamps.some(t => t > now + 5000 || t < 1e12)) return { grade: 'CLOCK_INVALID', sourceAgeMs: null, label: 'TIMESTAMP INVÁLIDO' };
  const sourceAgeMs = now - Math.min(...timestamps);
  if (sourceAgeMs > maxAgeMs) return { grade: 'STALE', sourceAgeMs, label: 'LIBRO ANTIGUO' };
  return { grade: 'OBSERVED_RECENTLY', sourceAgeMs, label: 'OBSERVADO RECIENTEMENTE' };
}
const SPEC_FIELDS = ['asset', 'quoteUnit', 'startAt', 'endAt', 'referenceExact', 'oracleProvider', 'oracleFeedId', 'priceStatistic', 'averagingWindowSeconds', 'rounding', 'operator', 'tiePayout', 'voidPayout', 'payoutCurrency', 'payoutAmount', 'rulesVersion'];
export function semanticComparison(a, b) {
  const x = a?.spec ?? {}, y = b?.spec ?? {};
  const canonical=v=>(typeof v==='string'&&v.trim().length>0)||(typeof v==='number'&&Number.isFinite(v));
  // Objects/arrays/booleans do not establish a canonical settlement rule.
  // String(object) would collapse distinct payouts to '[object Object]'.
  const mismatches = SPEC_FIELDS.filter(k => canonical(x[k]) && canonical(y[k]) && String(x[k]) !== String(y[k]));
  const missing = SPEC_FIELDS.filter(k => !canonical(x[k]) || !canonical(y[k]));
  if (!Number.isFinite(Number(x.referenceExact)) || Number(x.referenceExact) <= 0 || !Number.isFinite(Number(y.referenceExact)) || Number(y.referenceExact) <= 0) if (!missing.includes('referenceExact')) missing.push('referenceExact');
  return { grade: mismatches.length ? 'DIFFERENT' : missing.length ? 'UNVERIFIED' : 'EXACT', mismatches, missing };
}
export function compareMarkets(a, b, now) {
  const semantic = semanticComparison(a, b), fa = freshness(a, now), fb = freshness(b, now);
  const sourceTimes = [a?.up?.sourceAt, a?.down?.sourceAt, b?.up?.sourceAt, b?.down?.sourceAt].filter(Number.isFinite);
  const sourceSkewMs = sourceTimes.length === 4 ? Math.max(...sourceTimes) - Math.min(...sourceTimes) : null;
  const receiveSkewMs = Number.isFinite(a?.receivedAt) && Number.isFinite(b?.receivedAt) ? Math.abs(a.receivedAt - b.receivedAt) : null;
  const grades = [fa.grade, fb.grade];
  const timingGrade = grades.includes('CLOCK_INVALID') ? 'CLOCK_INVALID' : grades.includes('EXPIRED') ? 'EXPIRED' : grades.includes('STALE') ? 'STALE' : grades.includes('UNAVAILABLE') ? 'UNAVAILABLE' : grades.includes('UNKNOWN') ? 'UNKNOWN' : sourceSkewMs > 3000 || receiveSkewMs > 3000 ? 'SKEWED' : 'GROUPED_OBSERVATION';
  const observable = !['CLOCK_INVALID', 'EXPIRED', 'STALE', 'UNAVAILABLE'].includes(timingGrade);
  const midpointDifferencePp = observable && prob(a?.pMarket) && prob(b?.pMarket) ? (a.pMarket - b.pMarket) * 100 : null;
  return { semanticGrade: semantic.grade, timingGrade, mismatches: semantic.mismatches, missing: semantic.missing,
    sourceSkewMs, receiveSkewMs, midpointDifferencePp, comparisonEnabled: semantic.grade === 'EXACT' && timingGrade === 'GROUPED_OBSERVATION',
    executionEnabled: false, edge: null, contractProbability: null,
    note: 'Diferencia descriptiva de midpoint UP, en puntos porcentuales; no probabilidad propia, retorno, ventaja o arbitraje.' };
}
export function perShareCost(m, side) {
  const ask = m?.[side]?.ask;
  if (!prob(ask)) return { ask: null, fee: null, venueSubtotal: null, walletTotal: null, label: 'SIN ASK VERIFICADO' };
  let fee = null;
  if (m.provider === 'POLYMARKET') {
    if (m.feesEnabled === false) fee = 0;
    else if (m.feesEnabled === true && m.feeSchedule?.rate !== null && m.feeSchedule?.rate !== undefined && m.feeSchedule?.rate !== '' && Number(m.feeSchedule?.exponent) === 1 && Number.isFinite(Number(m.feeSchedule.rate)) && Number(m.feeSchedule.rate) >= 0 && Number(m.feeSchedule.rate) <= 1) fee = Math.round(Number(m.feeSchedule.rate) * ask * (1 - ask) * 100000) / 100000;
  }
  return { ask, fee, venueSubtotal: fee === null ? null : ask + fee, walletTotal: null,
    label: fee === null ? 'ASK BRUTO; COMISIÓN NO VERIFICADA' : 'ASK + FEE DEL VENUE POR 1 UNIDAD; INDICATIVO',
    note: 'No incluye coste de wallet/ruta, gas, conversión, deslizamiento ni mínimos. No es una cotización final ejecutable.' };
}
export function evaluateMatrixTiming(rows,now) {
  return rows.map(row=>{
    const markets=row.markets.map(m=>({...m,freshness:freshness(m,now)}));
    const a=markets.find(m=>m.provider==='POLYMARKET'),b=markets.find(m=>m.provider==='PREDICT');
    return {...row,markets,comparison:compareMarkets(a,b,now)};
  });
}
export const ACCESS_PATHS = [
  { name: 'Polymarket', providers: ['POLYMARKET'], state: 'Libro público directo', costs: 'Ask, spread y fee contractual cuando se reciben.' },
  { name: 'Predict.fun', providers: ['PREDICT'], state: 'API oficial requiere clave de servidor', costs: 'Sin conexión: coste no verificable.' },
  { name: 'Binance Wallet', providers: ['PREDICT'], state: 'Acceso a Predict; no API spot Binance', costs: 'Cotización final de la ruta no verificada.' },
  { name: 'Trust Wallet', providers: ['POLYMARKET', 'PREDICT', 'HIP4'], state: 'Mapa de proveedores; conexión directa pendiente', costs: 'No se presume cero fee en cripto; confirmar tarifa del venue y ruta.' },
  { name: 'MetaMask', providers: ['POLYMARKET'], state: 'Proveedor Polymarket; conexión directa pendiente', costs: 'La página oficial publica 4% de transacción; no se suma a ciegas a otra tarifa ni se trata como cotización final.' },
  { name: 'Coinbase Wallet / Base', providers: ['POLYMARKET'], state: 'Proveedor indicado por tu captura/experiencia; cuenta no verificada', costs: 'Ruta y cotización final no verificadas.' },
  { name: 'Coinbase Predictions', providers: ['KALSHI'], state: 'Producto distinto de Coinbase Wallet; referencia pública Kalshi', costs: 'Costes/interfaz Coinbase no verificados.' },
];
