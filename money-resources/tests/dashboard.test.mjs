import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

const script = readFileSync(new URL('../dashboard.js', import.meta.url), 'utf8');
const NOW = Date.parse('2026-10-20T01:00:00Z');
class Clock extends Date {
  constructor(...args) { super(...(args.length ? args : [NOW])); }
  static now() { return NOW; }
}
class Element {
  constructor(tag = 'div') { this.tag = tag; this.children = []; this.value = ''; this.events = {}; this.hidden = false; }
  set textContent(value) { this.content = String(value); this.children = []; }
  get textContent() { return (this.content || '') + this.children.map(child => typeof child === 'string' ? child : child.textContent).join(' '); }
  set innerHTML(_value) { throw Error('Untrusted HTML sink used'); }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this.content = ''; this.children = children; }
  addEventListener(event, callback) { this.events[event] = callback; }
}
function fixture() {
  return {schema_version:'1.1', mode:'READ_ONLY', ledger_integrity:true, generated_at_utc:'2026-10-20T00:30:00Z',
    quality:{status:'HEALTHY', fresh_verified_sources:1, detail_verified_candidates:1},
    sources:[{source_id:'immunefi_programs', provider:'immunefi', url:'https://immunefi.com/bug-bounty/', last_status:'ACCESS VERIFIED', last_scan_at_utc:'2026-10-20T00:29:00Z'}],
    opportunities:[{opportunity_id:'resource_123', type:'BOUNTY', provider:'immunefi', title:'Example programme',
      classification:'WATCH', last_verified_at_utc:'2026-10-20T00:29:00Z', expected_net_reward_usd:null,
      advertised_max_reward_usd:1_000_000, verification_scope:'PUBLIC_PROGRAM_TERMS_ONLY',
      official_url:'https://immunefi.com/bug-bounty/example/information/', source_evidence:[], missing_data:['reward_probability']}]};
}
async function run(primary, fallback = primary) {
  const elements = new Map();
  const calls = [];
  const document = {hidden:false, getElementById(id) { if (!elements.has(id)) elements.set(id, new Element()); return elements.get(id); },
    createElement:tag => new Element(tag), createTextNode:text => new Element('text').textContent = String(text)};
  vm.runInNewContext(script, {document, URL, Intl, Date:Clock, AbortSignal, setInterval() {},
    fetch:async address => { calls.push(address); const value = address.startsWith('https:') ? primary : fallback;
      if (value instanceof Error) throw value;
      return {ok:true, text:async () => typeof value === 'string' ? value : JSON.stringify(value)}; }});
  for (let i = 0; i < 6; i++) await new Promise(resolve => setImmediate(resolve));
  return {elements, calls, get:id => elements.get(id)};
}
function allNodes(node) { return [node, ...node.children.filter(child => child instanceof Element).flatMap(allNodes)]; }

test('verified terms and announced ceiling do not become expected income', async () => {
  const state = await run(fixture());
  assert.equal(state.get('count').textContent, '1');
  assert.equal(state.get('ev').textContent, 'Por determinar');
  assert.equal(state.get('income').textContent, 'Sin cobros verificados');
  assert.match(state.get('cards').textContent, /no es una recompensa esperada/);
  assert.equal(state.get('alert').hidden, true);
});
test('a malformed successful remote response falls back with an explicit warning', async () => {
  const state = await run('<html>not JSON</html>', fixture());
  assert.equal(state.calls.length, 2);
  assert.equal(state.get('count').textContent, '1');
  assert.equal(state.get('alert').hidden, false);
  assert.match(state.get('alert').textContent, /última publicación/);
  assert.equal(state.get('download').href, 'data/latest.json');
});
test('future or missing report dates never look fresh', async () => {
  const value = fixture(); value.generated_at_utc = '2099-01-01T00:00:00Z';
  const state = await run(value, {...value, generated_at_utc:'invalid'});
  assert.equal(state.get('alert').hidden, false);
  assert.match(state.get('alert').textContent, /No se pudo validar/);
  assert.match(state.get('cards').textContent, /todavía no disponible/);
});
test('expired candidates and old source access are rechecked against the display clock', async () => {
  const value = fixture(); value.generated_at_utc = '2026-10-18T00:00:00Z';
  value.sources[0].last_scan_at_utc = '2026-10-18T00:00:00Z';
  value.opportunities[0].deadline_utc = '2026-10-20T00:50:00Z';
  const state = await run(value);
  assert.match(state.get('cards').textContent, /Descartado/);
  assert.match(state.get('source-list').textContent, /ACCESS STALE/);
  assert.match(state.get('alert').textContent, /doce horas/);
});
test('untrusted titles stay text and private URL aliases cannot become links', async () => {
  const value = fixture(); value.opportunities[0].title = '<img src=x onerror=evil()>';
  value.opportunities[0].official_url = 'https://127.1/secret';
  const state = await run(value);
  assert.match(state.get('cards').textContent, /<img/);
  assert.equal(allNodes(state.get('cards')).some(node => node.href?.includes('127.')), false);
  assert.match(state.get('cards').textContent, /URL por verificar/);
});
test('filters use current classifications and never turn the refresh button into execution', async () => {
  const state = await run(fixture());
  state.get('type').value = 'CLAIM'; state.get('type').events.change();
  assert.match(state.get('cards').textContent, /No hay registros/);
  assert.equal(state.calls.every(address => address.startsWith('https://raw.githubusercontent.com/')), true);
});
