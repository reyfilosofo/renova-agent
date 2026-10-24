/* MONEY Ω: public evidence only; no wallet, claim, account or order transport. */
(() => {
  'use strict';
  const REMOTE = 'https://raw.githubusercontent.com/reyfilosofo/renova-agent/main/money-resources/data/latest.json';
  const MAX_AGE = 86400_000;
  const PUBLIC_HOSTS = new Set(['code4rena.com','www.code4rena.com','immunefi.com','www.immunefi.com',
    'api.github.com','github.com','zealy.io','app.galxe.com','galxe.com','www.galxe.com',
    'www.prolific.com','prolific.com','www.userinterviews.com','userinterviews.com','www.respondent.io','respondent.io']);
  const labels = {WATCH:'Por verificar', QUEUE:'Revisar condiciones', 'DATA INSUFFICIENT':'Faltan datos',
    SKIP:'Descartado', PROGRAM_DISCOVERY:'Programa por explorar', BOUNTY:'Bounty', QUEST:'Quest',
    PAID_RESEARCH:'Investigación remunerada', AIRDROP:'Airdrop', CLAIM:'Claim'};
  const $ = id => document.getElementById(id);
  let report = null;
  let fallback = false;

  function el(tag, text, className) {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = String(text ?? '');
    if (className) node.className = className;
    return node;
  }
  function stamp(value) {
    return typeof value === 'string' && /(?:Z|[+-]\d{2}:\d{2})$/.test(value) && Number.isFinite(Date.parse(value)) ? Date.parse(value) : null;
  }
  function date(value) {
    const parsed = stamp(value);
    return parsed === null ? 'Sin fecha verificada' : new Date(parsed).toLocaleString('es-MX', {timeZone:'America/Mexico_City'}) + ' CDMX';
  }
  function money(value) {
    return typeof value === 'number' && Number.isFinite(value) ? new Intl.NumberFormat('es-MX', {style:'currency', currency:'USD'}).format(value) : 'Desconocido';
  }
  function safeURL(value) {
    try {
      const url = new URL(value);
      return url.protocol === 'https:' && PUBLIC_HOSTS.has(url.hostname) && !url.username && !url.password && !url.hash && (!url.port || url.port === '443') ? url.href : null;
    } catch { return null; }
  }
  function link(value, text) {
    const address = safeURL(value);
    if (!address) return el('span', 'URL por verificar');
    const anchor = el('a', text);
    anchor.href = address; anchor.target = '_blank'; anchor.rel = 'noopener noreferrer';
    return anchor;
  }
  function classification(row) {
    if (row.classification === 'SKIP' || row.availability_status === 'INACTIVE') return 'SKIP';
    const deadline = stamp(row.deadline_utc || row.deadline);
    if (deadline !== null && deadline <= Date.now()) return 'SKIP';
    const observed = stamp(row.last_verified_at_utc);
    if (observed === null || observed > Date.now() + 60_000 || Date.now() - observed > MAX_AGE || row.availability_status === 'UNAVAILABLE') return 'DATA INSUFFICIENT';
    return Object.hasOwn(labels, row.classification) ? row.classification : 'DATA INSUFFICIENT';
  }
  function validate(value) {
    if (!value || !['1.0','1.1'].includes(value.schema_version) || value.mode !== 'READ_ONLY' ||
        !Array.isArray(value.opportunities) || value.opportunities.length > 1000 ||
        !Array.isArray(value.sources) || value.sources.length > 50 || stamp(value.generated_at_utc) === null ||
        stamp(value.generated_at_utc) > Date.now() + 60_000 ||
        value.opportunities.some(row => !row || typeof row !== 'object' || typeof row.opportunity_id !== 'string' || typeof row.type !== 'string') ||
        value.sources.some(source => !source || typeof source !== 'object' || typeof source.source_id !== 'string')) throw Error('Invalid public report');
    return value;
  }
  function render() {
    if (!report) return;
    $('cards').replaceChildren();
    const query = $('search').value.toLowerCase();
    const rows = report.opportunities.filter(row => (!$('type').value || row.type === $('type').value) &&
      (!$('status').value || classification(row) === $('status').value) &&
      (!query || [row.title, row.provider, row.type].join(' ').toLowerCase().includes(query)));
    if (!rows.length) $('cards').append(el('p', 'No hay registros para estos filtros.', 'empty'));
    for (const row of rows) {
      const card = el('article', undefined, 'card');
      const heading = el('div', undefined, 'row');
      const status = classification(row);
      heading.append(el('span', labels[row.type] || row.type, 'tag'), el('span', labels[status], 'tag'));
      card.append(heading, el('h3', row.title || row.provider), el('small', row.provider));
      const value = el('div', undefined, 'value');
      value.append(el('span', 'Valor esperado neto'), el('strong', money(row.expected_net_reward_usd)));
      card.append(value);
      if (typeof row.advertised_max_reward_usd === 'number' && Number.isFinite(row.advertised_max_reward_usd)) {
        card.append(el('small', 'Techo publicado del programa: ' + money(row.advertised_max_reward_usd)),
          el('small', 'Ese techo no es una recompensa esperada ni una asignación personal.'));
      }
      const detail = ['PROGRAM_DETAIL', 'PUBLIC_PROGRAM_TERMS_ONLY', 'PUBLIC_CLAIM_TERMS_ONLY'].includes(row.verification_scope);
      card.append(el('small', detail ? 'Alcance: términos públicos del programa.' : 'Alcance: descubrimiento de una página o catálogo.'),
        el('small', 'Elegibilidad personal: pendiente de verificar'), el('small', 'Última lectura: ' + date(row.last_verified_at_utc)));
      if (row.deadline_utc || row.deadline) card.append(el('small', 'Fecha límite publicada: ' + date(row.deadline_utc || row.deadline)));
      const details = el('details'); details.append(el('summary', 'Ver evidencia y datos pendientes'));
      for (const evidence of Array.isArray(row.source_evidence) ? row.source_evidence : []) {
        if (!evidence || typeof evidence !== 'object') continue;
        const proof = el('p');
        proof.append(link(evidence.url, 'Fuente consultada ↗'), el('br'),
          document.createTextNode('Lectura: ' + date(evidence.observed_at_utc || evidence.observed_at)), el('br'),
          document.createTextNode('SHA-256: ' + (typeof evidence.content_sha256 === 'string' ? evidence.content_sha256 : 'No disponible')));
        details.append(proof);
      }
      if (Array.isArray(row.missing_data)) details.append(el('p', 'Por confirmar: ' + row.missing_data.filter(item => typeof item === 'string').join(', ')));
      if (Array.isArray(row.blocking_reasons) && row.blocking_reasons.length) details.append(el('p', 'Motivos de cautela: ' + row.blocking_reasons.filter(item => typeof item === 'string').join(', ')));
      card.append(details, link(row.official_url, 'Abrir fuente del programa ↗')); $('cards').append(card);
    }
    $('source-list').replaceChildren();
    for (const source of report.sources) {
      const node = el('div', undefined, 'source');
      const observed = stamp(source.last_scan_at_utc);
      let status = source.last_status || 'ACCESS UNAVAILABLE';
      if (status === 'ACCESS VERIFIED' && (observed === null || Date.now() - observed > MAX_AGE)) status = 'ACCESS STALE';
      if (observed !== null && observed > Date.now() + 60_000) status = 'ACCESS UNAVAILABLE';
      node.append(link(source.url, source.provider || source.source_id), el('br'), el('span', status),
        el('br'), el('small', 'Último intento: ' + date(source.last_scan_at_utc))); $('source-list').append(node);
    }
    $('count').textContent = report.opportunities.length; $('source-count').textContent = report.sources.length;
    $('last').textContent = 'Último informe: ' + date(report.generated_at_utc);
    const calculated = report.opportunities.filter(row => typeof row.expected_net_reward_usd === 'number' && Number.isFinite(row.expected_net_reward_usd)).length;
    $('ev').textContent = calculated ? calculated + ' evaluaciones' : 'Por determinar';
    $('income').textContent = 'Sin cobros verificados';
    const quality = report.quality;
    $('quality').textContent = quality && typeof quality === 'object' ?
      `${Number.isInteger(quality.fresh_verified_sources) ? quality.fresh_verified_sources : '—'} fuentes con lectura vigente · ${Number.isInteger(quality.detail_verified_candidates) ? quality.detail_verified_candidates : '—'} programas con términos públicos revisados. La elegibilidad y el EV requieren comprobación independiente.` :
      'Informe anterior: revisa las fechas de cada fuente y la evidencia de cada programa.';
    const warnings = [];
    if (fallback) warnings.push('Se muestra el informe incluido en la última publicación porque no se pudo validar el informe remoto.');
    if (Date.now() - stamp(report.generated_at_utc) >= 12 * 3600_000) warnings.push('La última búsqueda supera doce horas. Comprueba el historial antes de tratar los registros como vigentes.');
    if (report.ledger_integrity !== true) warnings.push('La integridad del registro no está verificada.');
    if (quality?.status === 'DEGRADED') warnings.push('Hay fuentes inaccesibles, sin fecha o con datos vencidos.');
    $('alert').hidden = !warnings.length; $('alert').textContent = warnings.join(' ');
  }
  async function readReport(address) {
    const response = await fetch(address, {cache:'no-store', signal:AbortSignal.timeout(12000)});
    if (!response.ok) throw Error('Unavailable report');
    const text = await response.text();
    if (text.length > 2_000_000) throw Error('Oversized report');
    return validate(JSON.parse(text));
  }
  async function refresh() {
    $('refresh').disabled = true;
    try {
      try { report = await readReport(REMOTE + '?at=' + Date.now()); fallback = false; }
      catch { report = await readReport('data/latest.json'); fallback = true; }
      $('download').href = fallback ? 'data/latest.json' : REMOTE;
      render();
    } catch {
      if (report) render();
      $('alert').hidden = false;
      $('alert').textContent = 'No se pudo validar un informe actualizado. Los registros anteriores conservan su fecha y su vigencia.';
      if (!report) $('cards').replaceChildren(el('p', 'Informe todavía no disponible.', 'empty'));
    } finally { $('refresh').disabled = false; }
  }
  for (const id of ['search', 'type', 'status']) $(id).addEventListener(id === 'search' ? 'input' : 'change', render);
  $('refresh').addEventListener('click', refresh);
  setInterval(() => { if (!document.hidden) refresh(); }, 300000);
  refresh();
})();
