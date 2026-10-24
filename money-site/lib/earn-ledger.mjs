export const LEDGER_CURRENCIES = Object.freeze(['USD', 'MXN', 'EUR', 'GBP', 'CAD', 'AUD', 'CHF', 'JPY']);
export const LEDGER_CATEGORIES = Object.freeze(['BOUNTY', 'SURVEY', 'QUEST', 'AIRDROP', 'REWARDS', 'FREELANCE', 'SALE', 'FEES', 'GAS', 'OTHER']);
const FIELDS = new Set(['clientId', 'type', 'amount', 'currency', 'occurredOn', 'category', 'receiptRef', 'source', 'minutes', 'legacyPaidFlag', 'legacyPlatform']);
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const BAD_REF = /(?:secret|password|passwd|bearer|token|private|seed|recovery|wallet|account|iban|email|0x[0-9a-f])/i;

export class LedgerInputError extends Error {
  constructor(code) { super(code); this.name = 'LedgerInputError'; this.code = code; }
}
const fail = (code) => { throw new LedgerInputError(code); };

// Two fixed decimal places, decimal strings only. No binary floating point money.
export function parseAmount(value) {
  if (typeof value !== 'string' || !/^(?:0|[1-9][0-9]{0,8})(?:\.[0-9]{1,2})?$/.test(value)) fail('INVALID_AMOUNT');
  const [whole, fraction = ''] = value.split('.');
  const minor = Number(whole) * 100 + Number(fraction.padEnd(2, '0'));
  if (!Number.isSafeInteger(minor) || minor <= 0) fail('INVALID_AMOUNT');
  return minor;
}

export function minorToDecimal(value) {
  if (!(typeof value === 'number' && Number.isSafeInteger(value)) && !(typeof value === 'string' && /^-?[0-9]+$/.test(value))) fail('INVALID_STORED_AMOUNT');
  const raw = BigInt(value);
  const sign = raw < 0 ? '-' : '';
  const positive = raw < 0 ? -raw : raw;
  return `${sign}${positive / BigInt(100)}.${String(positive % BigInt(100)).padStart(2, '0')}`;
}

export function validateLedgerEntry(input, now = new Date()) {
  if (!input || typeof input !== 'object' || Array.isArray(input) || Object.keys(input).some(key => !FIELDS.has(key))) fail('INVALID_FIELDS');
  if (!Number.isFinite(now.getTime())) fail('INVALID_CLOCK');
  const { clientId, type, currency, occurredOn, category } = input;
  const source = input.source ?? 'OPERATOR';
  if (!['OPERATOR','LEGACY_EARN_LOCAL'].includes(source)) fail('INVALID_SOURCE');
  const legacy = source === 'LEGACY_EARN_LOCAL';
  if (typeof clientId !== 'string' || !UUID.test(clientId)) fail('INVALID_CLIENT_ID');
  if (type !== 'income' && type !== 'expense') fail('INVALID_TYPE');
  if (!LEDGER_CURRENCIES.includes(currency)) fail('INVALID_CURRENCY');
  if (!LEDGER_CATEGORIES.includes(category)) fail('INVALID_CATEGORY');
  if (!(legacy && occurredOn === null)) {
    if (typeof occurredOn !== 'string' || !/^20[0-9]{2}-[0-9]{2}-[0-9]{2}$/.test(occurredOn)) fail('INVALID_DATE');
    const day = new Date(`${occurredOn}T00:00:00.000Z`);
    if (!Number.isFinite(day.getTime()) || day.toISOString().slice(0, 10) !== occurredOn || occurredOn > now.toISOString().slice(0, 10)) fail('INVALID_DATE');
  }
  const minutes = input.minutes ?? null;
  if (minutes !== null && (typeof minutes !== 'number' || !Number.isFinite(minutes) || minutes < 0 || minutes > 1000000)) fail('INVALID_MINUTES');
  const legacyPaidFlag = legacy ? input.legacyPaidFlag : null;
  if (legacy && typeof legacyPaidFlag !== 'boolean') fail('INVALID_LEGACY_PAID_FLAG');
  if (!legacy && (input.legacyPaidFlag != null || input.legacyPlatform != null)) fail('INVALID_SOURCE');
  const legacyPlatform = legacy ? input.legacyPlatform : null;
  if (legacy && (typeof legacyPlatform !== 'string' || !/^[A-Za-z0-9][A-Za-z0-9 ._()-]{0,59}$/.test(legacyPlatform) || BAD_REF.test(legacyPlatform))) fail('INVALID_LEGACY_PLATFORM');
  let receiptRef = input.receiptRef ?? null;
  if (receiptRef === '') receiptRef = null;
  if (receiptRef !== null && (typeof receiptRef !== 'string' || !/^[A-Za-z][A-Za-z0-9_-]{0,31}$/.test(receiptRef) || BAD_REF.test(receiptRef) || /[a-f0-9]{24}/i.test(receiptRef))) fail('INVALID_RECEIPT_REF');
  const amountMinor = legacy && legacyPaidFlag === false && ['0','0.0','0.00'].includes(input.amount) ? 0 : parseAmount(input.amount);
  return { clientId: clientId.toLowerCase(), type, amountMinor, currency, occurredOn, category, receiptRef, source, minutes, legacyPaidFlag, legacyPlatform };
}

export async function ledgerPayloadHash(entry) {
  const canonical = JSON.stringify([entry.type, entry.amountMinor, entry.currency, entry.occurredOn, entry.category, entry.receiptRef, entry.source, entry.minutes, entry.legacyPaidFlag, entry.legacyPlatform]);
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(canonical));
  return Array.from(new Uint8Array(digest), b => b.toString(16).padStart(2, '0')).join('');
}

export function publicLedgerEntry(row) {
  return { id: row.id, clientId: row.clientId, type: row.type, amount: minorToDecimal(row.amountMinor), currency: row.currency,
    occurredOn: row.occurredOn, category: row.category, receiptRef: row.receiptRef,
    evidenceStatus: row.source === 'LEGACY_EARN_LOCAL' && row.legacyPaidFlag === false ? 'PENDING' : 'REPORTED',
    source:row.source,minutes:row.minutes,legacyPaidFlag:row.legacyPaidFlag,legacyPlatform:row.legacyPlatform,
    createdAt: new Date(row.createdAt).toISOString() };
}

export async function legacyLedgerPreview(document) {
  if (!document || document.source !== 'MONEY_OMEGA_EARN_LEGACY' || document.schema_version !== '1.0' || !Array.isArray(document.legacyMoneyOmegaLog) || !document.legacyMoneyOmegaLog.length || document.legacyMoneyOmegaLog.length > 100) fail('INVALID_LEGACY_DOCUMENT');
  const prepared=[];
  for (let index=0;index<document.legacyMoneyOmegaLog.length;index++) {
    const row=document.legacyMoneyOmegaLog[index];
    if (!row || typeof row.net !== 'number' || !Number.isFinite(row.net) || typeof row.paid !== 'boolean' || (row.mins !== null && row.mins !== undefined && (typeof row.mins !== 'number' || !Number.isFinite(row.mins)))) fail('INVALID_LEGACY_ROW');
    // Refuse silent rounding of historical amounts.
    const amount = String(Math.abs(row.net));
    const canonical=JSON.stringify([index,row.platform,row.net,row.mins??null,row.paid]);
    const bytes=new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(canonical)));
    bytes[6]=(bytes[6]&15)|64;bytes[8]=(bytes[8]&63)|128;
    const hex=Array.from(bytes.slice(0,16),b=>b.toString(16).padStart(2,'0')).join('');
    const clientId=`${hex.slice(0,8)}-${hex.slice(8,12)}-${hex.slice(12,16)}-${hex.slice(16,20)}-${hex.slice(20)}`;
    const input={clientId,type:row.net<0?'expense':'income',amount,currency:'MXN',occurredOn:null,category:'OTHER',receiptRef:null,source:'LEGACY_EARN_LOCAL',minutes:row.mins??null,legacyPaidFlag:row.paid,legacyPlatform:row.platform};
    validateLedgerEntry(input);prepared.push(input);
  }
  return prepared;
}

export function validWriteOrigin(request) {
  const origin = request.headers.get('origin');
  return origin === new URL(request.url).origin && request.headers.get('sec-fetch-site') !== 'cross-site';
}

export async function readLedgerBody(request, limit = 4096) {
  if (!/^application\/json(?:;|$)/i.test(request.headers.get('content-type') ?? '')) fail('JSON_REQUIRED');
  const length = request.headers.get('content-length');
  if (length !== null && (!/^[0-9]+$/.test(length) || Number(length) > limit)) fail('BODY_TOO_LARGE');
  if (!request.body) fail('INVALID_JSON');
  const reader = request.body.getReader();
  const chunks = []; let bytes = 0;
  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      bytes += value.byteLength;
      if (bytes > limit) { await reader.cancel(); fail('BODY_TOO_LARGE'); }
      chunks.push(value);
    }
    const joined = new Uint8Array(bytes); let offset = 0;
    for (const chunk of chunks) { joined.set(chunk, offset); offset += chunk.byteLength; }
    return JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(joined));
  } catch (error) {
    if (error instanceof LedgerInputError) throw error;
    fail('INVALID_JSON');
  } finally { reader.releaseLock(); }
}

export function parseLedgerCursor(value) {
  if (value === null) return null;
  const match = /^([0-9]{13})_([0-9a-f-]{36})$/.exec(value);
  if (!match || !UUID.test(match[2])) fail('INVALID_CURSOR');
  return { createdAt: Number(match[1]), id: match[2] };
}
