'use strict';

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];

const MAX_FILES = 3;
const MAX_FILE_BYTES = 8 * 1024 * 1024;
const ANALYSIS_TIMEOUT_MS = 130_000;
const FILE_TYPES = Object.freeze({
  pdf: 'application/pdf',
  doc: 'application/msword',
  docx: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  txt: 'text/plain',
  md: 'text/markdown',
  csv: 'text/csv',
  json: 'application/json',
  png: 'image/png',
  jpg: 'image/jpeg',
  jpeg: 'image/jpeg'
});

const demoInput = {
  organization: 'SERESARTE',
  sector: 'Creative & cultural organization',
  goal: 'Clarify positioning and priorities',
  website: 'https://seresarte.org',
  context: 'This curated SERESARTE demonstration illustrates how NOUS can structure a multidisciplinary cultural platform spanning philosophy, art, cultural production, publishing and strategic intelligence. The fixed example explores how to clarify an institutional narrative and convert supplied demonstration context into a focused 90-day operating agenda.'
};

const selectedFiles = [];
const evidenceRows = new Map();
let currentAnalysis = null;
let currentMode = 'demo';
let liveAvailable = false;
let isSubmitting = false;

function createElement(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined && text !== null) node.textContent = String(text);
  return node;
}

function safeText(value, fallback = 'Not provided') {
  if (value === undefined || value === null || value === '') return fallback;
  return String(value);
}

function asArray(value) {
  return Array.isArray(value) ? value : [];
}

function clampScore(value, fallback = 0) {
  const number = Number(value);
  return Number.isFinite(number) ? Math.min(100, Math.max(0, number)) : fallback;
}

function evidenceRefs(item) {
  if (!item || typeof item !== 'object') return [];
  return asArray(item.evidence_refs)
    .map((ref) => String(ref).trim())
    .filter(Boolean)
    .filter((ref, index, refs) => refs.indexOf(ref) === index);
}

function itemConfidence(item) {
  const direct = Number(item?.confidence);
  if (Number.isFinite(direct)) return clampScore(direct);
  const referenced = evidenceRefs(item)
    .map((ref) => evidenceRows.get(ref)?.dataset.confidence)
    .map(Number)
    .filter(Number.isFinite);
  if (!referenced.length) return null;
  return Math.round(referenced.reduce((sum, score) => sum + score, 0) / referenced.length);
}

function setView(selector, focusSelector) {
  $$('.view').forEach((view) => {
    const active = view.matches(selector);
    view.classList.toggle('active', active);
    view.setAttribute('aria-hidden', String(!active));
  });
  window.scrollTo(0, 0);
  if (focusSelector) {
    requestAnimationFrame(() => $(focusSelector)?.focus());
  }
}

function toast(message) {
  const node = $('#toast');
  node.classList.remove('show');
  node.textContent = '';
  requestAnimationFrame(() => {
    node.textContent = safeText(message, 'Action completed');
    node.classList.add('show');
    window.setTimeout(() => node.classList.remove('show'), 3000);
  });
}

function clearError() {
  $('#analysisError').hidden = true;
  $('#analysisErrorMessage').textContent = '';
}

function showError(message, title = 'Analysis could not be completed', hint) {
  const panel = $('#analysisError');
  $('#analysisErrorTitle').textContent = title;
  $('#analysisErrorMessage').textContent = safeText(message, 'An unexpected error occurred.').slice(0, 1000);
  $('#analysisErrorHint').textContent = hint || 'Review the information below and try again. No demonstration result has been substituted.';
  panel.hidden = false;
  requestAnimationFrame(() => panel.focus());
}

function setProgress(percent) {
  const value = Math.round(clampScore(percent));
  $('#progressBar').style.width = `${value}%`;
  $('#progressTrack').setAttribute('aria-valuenow', String(value));
}

function fileSize(bytes) {
  return bytes >= 1048576 ? `${(bytes / 1048576).toFixed(1)} MB` : `${Math.max(1, Math.ceil(bytes / 1024))} KB`;
}

function fileExtension(name) {
  const match = String(name).toLowerCase().match(/\.([a-z0-9]+)$/);
  return match ? match[1] : '';
}

function normalizedMime(file) {
  return FILE_TYPES[fileExtension(file.name)] || file.type || 'application/octet-stream';
}

function validateFile(file) {
  const extension = fileExtension(file.name);
  if (!FILE_TYPES[extension]) return `${file.name}: unsupported file type.`;
  if (!file.size) return `${file.name}: the file is empty.`;
  if (file.size > MAX_FILE_BYTES) return `${file.name}: exceeds the 8 MB limit.`;
  const duplicate = selectedFiles.some((existing) =>
    existing.name === file.name && existing.size === file.size && existing.lastModified === file.lastModified
  );
  if (duplicate) return `${file.name}: already selected.`;
  return '';
}

function renderFiles() {
  const list = $('#fileList');
  list.replaceChildren();
  selectedFiles.forEach((file, index) => {
    const chip = createElement('div', 'file-chip');
    chip.append(createElement('span', '', `${file.name} · ${fileSize(file.size)}`));
    const remove = createElement('button', '', '×');
    remove.type = 'button';
    remove.setAttribute('aria-label', `Remove ${file.name}`);
    remove.addEventListener('click', () => {
      selectedFiles.splice(index, 1);
      renderFiles();
      toast(`${file.name} removed`);
    });
    chip.append(remove);
    list.append(chip);
  });
}

function addFiles(files) {
  clearError();
  const errors = [];
  for (const file of files) {
    if (selectedFiles.length >= MAX_FILES) {
      errors.push(`Maximum ${MAX_FILES} files allowed.`);
      break;
    }
    const error = validateFile(file);
    if (error) errors.push(error);
    else selectedFiles.push(file);
  }
  renderFiles();
  if (errors.length) showError(errors.join(' '), 'Some evidence could not be added', 'Choose a supported, non-empty file no larger than 8 MB.');
}

function readFileBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result).split(',')[1] || '');
    reader.onerror = () => reject(new Error(`Could not read ${file.name}.`));
    reader.readAsDataURL(file);
  });
}

async function filePayload() {
  return Promise.all(selectedFiles.map(async (file) => ({
    name: file.name,
    type: normalizedMime(file),
    size: file.size,
    data: await readFileBase64(file)
  })));
}

function updateLiveAvailability(available, model) {
  liveAvailable = Boolean(available);
  const toggle = $('#liveToggle');
  toggle.disabled = !liveAvailable;
  if (!liveAvailable) toggle.checked = false;
  $('#statusDot').classList.toggle('live', liveAvailable);
  $('#modeText').textContent = liveAvailable ? 'Live API available' : 'Demo mode';
  $('#modelText').textContent = liveAvailable ? safeText(model, 'GPT-5.6') : 'Live analysis unavailable';
  $('#liveAvailability').textContent = liveAvailable
    ? `${safeText(model, 'GPT-5.6')} is available for a server-side live request.`
    : 'Live analysis is disabled because this server has no usable API key. Curated demo mode returns the fixed SERESARTE example; submitted intake and files do not alter it.';
}

async function init() {
  setView('#intakeView');
  try {
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 8000);
    const response = await fetch('/api/health', { signal: controller.signal, cache: 'no-store' });
    window.clearTimeout(timeout);
    const health = await response.json();
    if (!response.ok || !health.ok) throw new Error('Health check failed');
    updateLiveAvailability(health.live_available, health.model);
  } catch (_error) {
    updateLiveAvailability(false);
    $('#modeText').textContent = 'Server unavailable';
    $('#modelText').textContent = 'Reload to reconnect';
    $('#liveAvailability').textContent = 'The application server could not be reached. Reload before starting an analysis.';
  }
}

function emptyState(message) {
  return createElement('p', 'empty-state', message);
}

function evidenceButton(reference) {
  const button = createElement('button', 'evidence-ref', reference);
  button.type = 'button';
  button.setAttribute('aria-label', `Open evidence ${reference}`);
  button.addEventListener('click', () => focusEvidence(reference));
  return button;
}

function traceNode(item, source) {
  const trace = createElement('div', 'trace-content');
  const confidence = itemConfidence(item);
  if (source) trace.append(createElement('span', 'trace-source', source));
  if (confidence !== null) trace.append(createElement('span', 'trace-confidence', `${confidence}% confidence`));
  const refs = evidenceRefs(item);
  if (refs.length) {
    const group = createElement('span', 'evidence-refs');
    group.append(createElement('span', 'sr-only', 'Evidence references: '));
    refs.forEach((ref) => group.append(evidenceButton(ref)));
    trace.append(group);
  }
  return trace;
}

function renderEvidence(items) {
  const body = $('#evidenceBody');
  body.replaceChildren();
  evidenceRows.clear();
  if (!items.length) {
    const row = document.createElement('tr');
    const cell = createElement('td', 'empty-state', 'No evidence was returned.');
    cell.colSpan = 5;
    row.append(cell);
    body.append(row);
    return;
  }
  items.forEach((item) => {
    const id = safeText(item.id, 'Unlabeled');
    const row = document.createElement('tr');
    row.tabIndex = -1;
    row.dataset.confidence = String(clampScore(item.confidence));
    const idCell = createElement('th', '', id);
    idCell.scope = 'row';
    row.append(idCell);
    row.append(createElement('td', '', safeText(item.observation)));
    row.append(createElement('td', '', safeText(item.source)));
    const confidenceCell = document.createElement('td');
    confidenceCell.append(createElement('span', 'confidence-pill', `${clampScore(item.confidence)}%`));
    row.append(confidenceCell);
    row.append(createElement('td', '', safeText(item.implication)));
    body.append(row);
    evidenceRows.set(id, row);
  });
}

function focusEvidence(reference) {
  activateTab('evidence', { focusTab: false });
  const row = evidenceRows.get(String(reference));
  if (row) {
    row.classList.add('evidence-highlight');
    row.scrollIntoView({ behavior: 'smooth', block: 'center' });
    row.focus();
    window.setTimeout(() => row.classList.remove('evidence-highlight'), 2200);
  } else {
    $('#tab-evidence').focus();
    toast(`Evidence ${reference} was not found in the ledger.`);
  }
}

function renderMetrics(metrics) {
  const grid = $('#metricGrid');
  grid.replaceChildren();
  if (!metrics.length) {
    grid.append(emptyState('No strategic metrics were returned.'));
    return;
  }
  metrics.forEach((metric) => {
    const score = clampScore(metric.score);
    const card = createElement('div', 'metric');
    const head = createElement('div', 'metric-head');
    head.append(createElement('span', '', safeText(metric.name)), createElement('b', '', score));
    const bar = createElement('div', 'metric-bar');
    bar.setAttribute('role', 'progressbar');
    bar.setAttribute('aria-label', `${safeText(metric.name)} score`);
    bar.setAttribute('aria-valuemin', '0');
    bar.setAttribute('aria-valuemax', '100');
    bar.setAttribute('aria-valuenow', String(score));
    const value = document.createElement('i');
    value.style.width = `${score}%`;
    bar.append(value);
    card.append(head, bar);
    grid.append(card);
  });
}

function renderTopItem(prefix, item) {
  const safeItem = item && typeof item === 'object' ? item : {};
  $(`#${prefix}`).textContent = safeText(safeItem.title);
  $(`#${prefix}Why`).textContent = safeText(safeItem.why);
  const trace = $(`#${prefix}Trace`);
  trace.replaceChildren(traceNode(safeItem));
}

function renderSignals(signals) {
  const grid = $('#signalsGrid');
  grid.replaceChildren();
  if (!signals.length) {
    grid.append(emptyState('No strategic signals were returned.'));
    return;
  }
  const tones = new Set(['opportunity', 'risk', 'neutral']);
  signals.forEach((signal) => {
    const tone = tones.has(signal.tone) ? signal.tone : 'neutral';
    const card = createElement('article', `signal-card ${tone}`);
    card.append(createElement('div', 'type', safeText(signal.type)));
    card.append(createElement('h3', '', safeText(signal.title)));
    card.append(createElement('p', '', safeText(signal.body)));
    const meta = createElement('div', 'signal-meta');
    meta.append(traceNode(signal, safeText(signal.source)));
    card.append(meta);
    grid.append(card);
  });
}

function badge(text) {
  return createElement('span', '', text);
}

function renderDecisions(decisions) {
  const list = $('#decisionList');
  list.replaceChildren();
  if (!decisions.length) {
    list.append(emptyState('No prioritized decisions were returned.'));
    return;
  }
  decisions.forEach((decision, index) => {
    const card = createElement('article', 'decision-card');
    card.append(createElement('div', 'decision-rank', String(decision.rank ?? index + 1).padStart(2, '0')));
    const copy = document.createElement('div');
    copy.append(createElement('h3', '', safeText(decision.title)), createElement('p', '', safeText(decision.detail)));
    const badges = createElement('div', 'decision-badges');
    badges.append(
      badge(safeText(decision.quadrant)),
      badge(`Impact: ${safeText(decision.impact)}`),
      badge(`Effort: ${safeText(decision.effort)}`),
      badge(safeText(decision.urgency))
    );
    badges.append(traceNode(decision));
    card.append(copy, badges);
    list.append(card);
  });
}

function renderRoadmap(roadmap) {
  const grid = $('#roadmapGrid');
  grid.replaceChildren();
  const phases = roadmap && typeof roadmap === 'object' ? Object.entries(roadmap) : [];
  if (!phases.length) {
    grid.append(emptyState('No execution roadmap was returned.'));
    return;
  }
  phases.forEach(([phase, items], index) => {
    const column = createElement('article', 'roadmap-column');
    column.append(createElement('div', 'phase', `PHASE ${index + 1}`), createElement('h3', '', phase));
    asArray(items).forEach((item) => {
      const row = createElement('div', 'roadmap-item');
      row.append(createElement('strong', '', safeText(item.title)), createElement('span', '', safeText(item.detail)));
      row.append(traceNode(item));
      column.append(row);
    });
    grid.append(column);
  });
}

function validateAnalysis(analysis) {
  if (!analysis || typeof analysis !== 'object') throw new Error('The server returned no structured analysis.');
  const requiredStrings = ['organization', 'decision', 'thesis', 'summary', 'decision_enabled'];
  const missing = requiredStrings.filter((field) => !analysis[field]);
  if (missing.length || !Array.isArray(analysis.evidence)) {
    throw new Error('The server returned an incomplete structured analysis.');
  }
  return analysis;
}

function renderAnalysis(rawAnalysis) {
  const analysis = validateAnalysis(rawAnalysis);
  renderEvidence(asArray(analysis.evidence));

  $('#roomOrganization').textContent = safeText(analysis.organization);
  $('#roomSector').textContent = safeText(analysis.sector, 'Organization').toUpperCase();
  $('#roomDecision').textContent = `Decision: ${safeText(analysis.decision)}`;
  const evidenceScores = asArray(analysis.evidence).map((item) => clampScore(item.confidence));
  const derivedConfidence = evidenceScores.length
    ? Math.round(evidenceScores.reduce((sum, score) => sum + score, 0) / evidenceScores.length)
    : 0;
  const confidence = Number.isFinite(Number(analysis.meta?.confidence))
    ? clampScore(analysis.meta.confidence)
    : derivedConfidence;
  $('#confidenceScore').textContent = `${confidence}%`;
  $('#modeBadge').textContent = currentMode === 'live'
    ? `Live · ${safeText(analysis.meta?.model, 'GPT-5.6')}`
    : 'Curated demo';

  $('#thesis').textContent = safeText(analysis.thesis);
  $('#summary').textContent = safeText(analysis.summary);
  $('#decisionEnabled').textContent = safeText(analysis.decision_enabled);
  const overall = clampScore(analysis.overall_score);
  $('#overallScore').textContent = String(overall);
  $('#scoreInterpretation').textContent = safeText(analysis.score_interpretation);
  $('#ringValue').style.strokeDashoffset = (307.9 * (1 - overall / 100)).toFixed(1);

  renderMetrics(asArray(analysis.metrics));
  renderTopItem('topOpportunity', analysis.top_opportunity);
  renderTopItem('topRisk', analysis.top_risk);
  renderSignals(asArray(analysis.signals));
  renderDecisions(asArray(analysis.decisions));
  renderRoadmap(analysis.roadmap);
}

function backendErrorMessage(data, fallback) {
  if (typeof data?.error === 'string') return data.error;
  if (data?.error?.message) return String(data.error.message);
  if (data?.message) return String(data.message);
  return fallback;
}

function setSubmitting(submitting) {
  isSubmitting = submitting;
  $('#intakeForm').setAttribute('aria-busy', String(submitting));
  $('#loadingView').setAttribute('aria-busy', String(submitting));
  $('#analyzeButton').disabled = submitting;
  $('#loadDemoBtn').disabled = submitting;
  $('#analyzeButtonText').textContent = submitting ? 'Building Intelligence Room…' : 'Open Intelligence Room';
}

function startProgress() {
  const steps = [
    'Structuring evidence…',
    'Testing consistency and confidence…',
    'Detecting strategic signals…',
    'Prioritizing decisions…',
    'Producing the 30/60/90-day roadmap…'
  ];
  let step = 0;
  setProgress(8);
  $$('.loading-steps span').forEach((node, index) => node.classList.toggle('done', index === 0));
  return window.setInterval(() => {
    step = Math.min(step + 1, steps.length - 1);
    $('#loadingStep').textContent = steps[step];
    setProgress(Math.min(90, 8 + step * 19));
    $$('.loading-steps span').forEach((node, index) => node.classList.toggle('done', index <= step));
  }, 900);
}

async function analyze(event) {
  event.preventDefault();
  if (isSubmitting) return;
  clearError();
  const requestedLive = $('#liveToggle').checked;
  if (requestedLive && !liveAvailable) {
    showError('Live analysis is unavailable on this server.', 'Live analysis unavailable', 'Use curated demo mode or configure a valid server-side API key, then reload.');
    return;
  }

  let files = [];
  if (requestedLive) {
    try {
      files = await filePayload();
    } catch (error) {
      showError(error.message, 'Evidence could not be read');
      return;
    }
  }

  const payload = {
    organization: $('#organization').value.trim(),
    sector: $('#sector').value,
    goal: $('#goal').value,
    website: $('#website').value.trim(),
    context: $('#context').value.trim(),
    use_live: requestedLive,
    files
  };

  setSubmitting(true);
  setView('#loadingView', '#loadingTitle');
  $('#pageTitle').textContent = 'Analysis in progress';
  const progressTimer = startProgress();
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), ANALYSIS_TIMEOUT_MS);

  try {
    const response = await fetch('/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: controller.signal
    });
    let data = null;
    try {
      data = await response.json();
    } catch (_error) {
      throw new Error(`The server returned an unreadable response (${response.status}).`);
    }
    if (!response.ok) throw new Error(backendErrorMessage(data, `Analysis failed (${response.status}).`));

    const responseMode = String(data.mode || data.analysis?.meta?.mode || '');
    if (responseMode === 'demo-fallback') {
      throw new Error('Live analysis failed. The server attempted to return a demonstration fallback, which NOUS rejected for transparency.');
    }
    if (requestedLive && responseMode !== 'live') {
      throw new Error('A live analysis was requested, but the server did not return a verified live result.');
    }

    currentMode = responseMode === 'live' ? 'live' : 'demo';
    currentAnalysis = validateAnalysis(data.analysis);
    renderAnalysis(currentAnalysis);
    setProgress(100);
    activateTab('overview');
    setView('#resultsView', '#roomOrganization');
    $('#pageTitle').textContent = 'Intelligence Room';
    $('#printBtn').disabled = false;
    $('#exportJsonBtn').disabled = false;
    $('#newRoomBtn').hidden = false;
    if (currentMode === 'demo' && selectedFiles.length) {
      toast('Curated demo returned the fixed SERESARTE case; selected files were not uploaded.');
    }
  } catch (error) {
    currentAnalysis = null;
    currentMode = 'demo';
    setView('#intakeView');
    $('#pageTitle').textContent = 'New Intelligence Room';
    const timedOut = error.name === 'AbortError';
    showError(
      timedOut ? 'The request exceeded 130 seconds and was cancelled.' : error.message,
      requestedLive ? 'Live analysis could not be verified' : 'Analysis could not be completed',
      requestedLive
        ? 'No curated result has been substituted. Verify API access and retry the live request.'
        : 'No demonstration result has been substituted. Confirm the server is running and retry.'
    );
  } finally {
    window.clearTimeout(timeout);
    window.clearInterval(progressTimer);
    setSubmitting(false);
  }
}

function activateTab(name, options = {}) {
  const tabs = $$('.tab');
  tabs.forEach((tab) => {
    const selected = tab.dataset.tab === name;
    tab.classList.toggle('active', selected);
    tab.setAttribute('aria-selected', String(selected));
    tab.tabIndex = selected ? 0 : -1;
  });
  $$('.tab-panel').forEach((panel) => {
    const selected = panel.id === `tab-${name}`;
    panel.classList.toggle('active', selected);
    panel.hidden = !selected;
  });
  if (options.focusTab) $(`.tab[data-tab="${name}"]`)?.focus();
}

function resetRoom() {
  currentAnalysis = null;
  currentMode = 'demo';
  selectedFiles.splice(0, selectedFiles.length);
  $('#intakeForm').reset();
  $('#liveToggle').disabled = !liveAvailable;
  renderFiles();
  clearError();
  $('#printBtn').disabled = true;
  $('#exportJsonBtn').disabled = true;
  $('#newRoomBtn').hidden = true;
  $('#pageTitle').textContent = 'New Intelligence Room';
  setNavActive($('.nav-item[data-nav="room"]'));
  setView('#intakeView', '#organization');
}

function setNavActive(activeButton) {
  $$('.nav-item').forEach((button) => {
    const active = button === activeButton;
    button.classList.toggle('active', active);
    if (active) button.setAttribute('aria-current', 'page');
    else button.removeAttribute('aria-current');
  });
}

$('#files').addEventListener('change', (event) => {
  addFiles(event.target.files);
  event.target.value = '';
});

const dropzone = $('#dropzone');
['dragenter', 'dragover'].forEach((eventName) => dropzone.addEventListener(eventName, (event) => {
  event.preventDefault();
  dropzone.classList.add('drag');
}));
['dragleave', 'drop'].forEach((eventName) => dropzone.addEventListener(eventName, (event) => {
  event.preventDefault();
  dropzone.classList.remove('drag');
}));
dropzone.addEventListener('drop', (event) => addFiles(event.dataTransfer.files));

$('#loadDemoBtn').addEventListener('click', () => {
  Object.entries(demoInput).forEach(([key, value]) => {
    const field = $(`#${key}`);
    if (field) field.value = value;
  });
  $('#consent').checked = true;
  clearError();
  toast('Curated SERESARTE case loaded');
});

$('#intakeForm').addEventListener('submit', analyze);

$$('.tab').forEach((tab, index, tabs) => {
  tab.addEventListener('click', () => activateTab(tab.dataset.tab));
  tab.addEventListener('keydown', (event) => {
    let nextIndex = null;
    if (event.key === 'ArrowRight') nextIndex = (index + 1) % tabs.length;
    if (event.key === 'ArrowLeft') nextIndex = (index - 1 + tabs.length) % tabs.length;
    if (event.key === 'Home') nextIndex = 0;
    if (event.key === 'End') nextIndex = tabs.length - 1;
    if (nextIndex === null) return;
    event.preventDefault();
    activateTab(tabs[nextIndex].dataset.tab, { focusTab: true });
  });
});

$$('.nav-item').forEach((button) => button.addEventListener('click', () => {
  setNavActive(button);
  const destination = button.dataset.nav;
  if (destination === 'submission') {
    setView('#submissionView', '#mainContent');
    $('#pageTitle').textContent = 'Build Week submission';
    return;
  }
  if (!currentAnalysis) {
    setView('#intakeView', '#organization');
    $('#pageTitle').textContent = 'New Intelligence Room';
    if (destination !== 'room') toast('Complete an analysis to open this section.');
    return;
  }
  setView('#resultsView');
  $('#pageTitle').textContent = 'Intelligence Room';
  const target = destination === 'evidence' ? 'evidence' : destination === 'roadmap' ? 'roadmap' : 'overview';
  activateTab(target, { focusTab: destination !== 'room' });
}));

$('#newRoomBtn').addEventListener('click', resetRoom);
$('#printBtn').addEventListener('click', () => window.print());
$('#exportJsonBtn').addEventListener('click', () => {
  if (!currentAnalysis) return;
  const blob = new Blob([JSON.stringify(currentAnalysis, null, 2)], { type: 'application/json' });
  const link = document.createElement('a');
  const baseName = safeText(currentAnalysis.organization, 'Organization')
    .normalize('NFKD')
    .replace(/[^A-Za-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '') || 'Organization';
  link.href = URL.createObjectURL(blob);
  link.download = `NOUS_${baseName}_Intelligence_Room.json`;
  link.click();
  window.setTimeout(() => URL.revokeObjectURL(link.href), 1000);
});
$('#languageBtn').addEventListener('click', () => toast('Interface language: English. Spanish and English submission copy is included in the project package.'));

init();
