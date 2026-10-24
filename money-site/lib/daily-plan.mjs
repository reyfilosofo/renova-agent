export const DAILY_ZONE = 'America/Mexico_City';
export function localDay(now = Date.now()) {
  const p = Object.fromEntries(new Intl.DateTimeFormat('en-CA', { timeZone: DAILY_ZONE, year: 'numeric', month: '2-digit', day: '2-digit' }).formatToParts(now).map(x => [x.type, x.value]));
  return `${p.year}-${p.month}-${p.day}`;
}
export function dayBounds(day) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(day)) throw new Error('Fecha inválida');
  const startAt = Date.parse(`${day}T00:00:00-06:00`);
  if (!Number.isFinite(startAt) || localDay(startAt) !== day || day < '2023-01-01' || day > '2100-12-31') throw new Error('Fecha inválida');
  return { day, timeZone: DAILY_ZONE, startAt, endAt: startAt + 86400000 };
}
export function dailyGrid(day, horizon, assets, forecasts = [], snapshots = [], now = Date.now()) {
  if (![5, 15, 60].includes(horizon)) throw new Error('Horizonte inválido');
  const bounds = dayBounds(day), span = horizon * 60000;
  const firstForecast = new Map();
  for (const raw of [...forecasts].sort((a,b) => a.created - b.created)) {
    if (raw.horizon !== horizon || raw.origin % span !== 0 || raw.target !== raw.origin + span || raw.origin < bounds.startAt || raw.origin >= bounds.endAt || raw.created >= raw.target || raw.created < raw.origin || raw.created > now) continue;
    const key = `${raw.asset}:${raw.origin}`;
    if (!firstForecast.has(key)) firstForecast.set(key, raw);
  }
  const byWindow = new Map();
  for (const s of [...snapshots].sort((a,b) => a.created - b.created)) {
    if (s.horizon !== horizon || s.window_end !== s.window_start + span || s.created > now || s.created >= s.window_end || s.created < s.window_start) continue;
    const key = `${s.asset}:${s.window_start}`;
    if (!byWindow.has(key)) byWindow.set(key,s);
  }
  const rows = [];
  for (let startAt = bounds.startAt; startAt < bounds.endAt; startAt += span) {
    const endAt = startAt + span;
    rows.push({ startAt, endAt, state: now < startAt ? 'FUTURE' : now >= endAt ? 'PAST' : 'CURRENT',
      assets: assets.map(asset => {
        const f = firstForecast.get(`${asset}:${startAt}`), s = byWindow.get(`${asset}:${startAt}`);
        const payload = f ? (typeof f.payload === 'string' ? JSON.parse(f.payload) : f.payload) : null;
        return { asset, forecast: f ? { id:f.id, issuedAt:f.created, origin:f.origin, target:f.target, reference:f.reference, probability:f.probability,
          medianPrice:payload?.medianPrice ?? null, priceBand:payload?.priceBand ?? null, outcome:f.outcome ?? null, finalPrice:f.final_price ?? null,
          source:f.source, strategy:payload?.strategyId, version:payload?.version, calibrated:false, contractProbability:null } : null,
          marketSnapshot: s ? (typeof s.payload === 'string' ? JSON.parse(s.payload) : s.payload) : null,
          state: now < startAt ? 'PENDIENTE DE EMISIÓN' : f ? 'EMITIDO' : 'SIN CORTE PROSPECTIVO ALINEADO' };
      }) });
  }
  return { ...bounds, horizon, rows, generatedAt:now, expectedWindows:rows.length, expectedCells:rows.length*assets.length,
    forecastedCells: rows.reduce((n,r) => n+r.assets.filter(x=>x.forecast).length,0),
    warning:'Agenda prospectiva. Futuro vacío; no son24 precios futuros conocidos. Se conserva la primera emisión alineada. Pspot no es Pcontrato.' };
}
