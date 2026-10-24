import test from 'node:test';
import assert from 'node:assert/strict';
import {parseAmount,minorToDecimal,validateLedgerEntry,ledgerPayloadHash,publicLedgerEntry,validWriteOrigin,readLedgerBody,parseLedgerCursor,legacyLedgerPreview} from '../lib/earn-ledger.mjs';
import {DatabaseSync} from 'node:sqlite';
import {readFileSync,readdirSync} from 'node:fs';
const now=new Date('2026-10-24T06:30:00Z');
const entry={clientId:'2ae83368-cb09-4ded-b91c-91acc09fffd9',type:'income',amount:'12.34',currency:'USD',occurredOn:'2026-10-24',category:'BOUNTY',receiptRef:'Receipt-01'};
test('money uses exact fixed decimal minor units and rejects ambiguous or nonfinite input',()=>{
  for(const [amount,minor] of [['0.01',1],['0.1',10],['12.34',1234],['999999999.99',99999999999]])assert.equal(parseAmount(amount),minor);
  for(const amount of [0,1.2,NaN,Infinity,null,{},'-1','0','00.01','1e3',' 1','1 ','1.234','1.','1,00','1000000000'])assert.throws(()=>parseAmount(amount));
  assert.equal(minorToDecimal('100000000000000001'),'1000000000000000.01');assert.equal(minorToDecimal(-1),'-0.01');
});
test('reported records reject ownership, verification overrides and financial actions',()=>{
  for(const extra of [{userId:'other'},{email:'a@example.com'},{evidenceStatus:'VERIFIED'},{executionEnabled:true},{wallet:'x'},{status:'ACTIVE'}])assert.throws(()=>validateLedgerEntry({...entry,...extra},now));
  for(const type of ['transfer','buy','sell','withdraw',null])assert.throws(()=>validateLedgerEntry({...entry,type},now));
  assert.equal(validateLedgerEntry(entry,now).amountMinor,1234);
});
test('calendar rejects impossible and future dates, and scope is strictly typed',()=>{
  for(const occurredOn of ['2026-02-30','2026-10-25','2026-1-01','1999-12-31',null])assert.throws(()=>validateLedgerEntry({...entry,occurredOn},now));
  for(const change of [{clientId:'other'},{currency:'USDT'},{currency:'usd'},{category:[]},{category:'PASSWORD'}])assert.throws(()=>validateLedgerEntry({...entry,...change},now));
  assert.throws(()=>validateLedgerEntry(entry,new Date(NaN)));
});
test('receipt references cannot be URLs, emails, addresses, secrets or free text',()=>{
  for(const receiptRef of ['https://site/a','person@example.com','Juan Perez','Bearer-token','seed_phrase','wallet-01','0x123456789abcdef','a'.repeat(64),'Receipt\nsecret','01234'])assert.throws(()=>validateLedgerEntry({...entry,receiptRef},now));
  assert.equal(validateLedgerEntry({...entry,receiptRef:''},now).receiptRef,null);
});
test('idempotency hashes canonical money but changes for material payload differences',async()=>{
  const normalized=validateLedgerEntry(entry,now);const hash=await ledgerPayloadHash(normalized);
  assert.match(hash,/^[a-f0-9]{64}$/);
  assert.equal(await ledgerPayloadHash(validateLedgerEntry({...entry,amount:'12.34',clientId:'9eebdfb5-ea04-41fb-8da6-4b00b94d4aae'},now)),hash);
  assert.equal(await ledgerPayloadHash(validateLedgerEntry({...entry,amount:'12.3'},now)),await ledgerPayloadHash(validateLedgerEntry({...entry,amount:'12.30'},now)));
  for(const change of [{amount:'12.35'},{type:'expense'},{currency:'MXN'},{receiptRef:'Receipt-02'},{category:'OTHER'},{occurredOn:'2026-10-23'}])assert.notEqual(await ledgerPayloadHash(validateLedgerEntry({...entry,...change},now)),hash);
});
test('private projection excludes identity and internal hashes and cannot imply verified account truth',()=>{
  const publicEntry=publicLedgerEntry({...validateLedgerEntry(entry,now),id:'id',userId:'private',email:'secret@example.com',payloadHash:'private',createdAt:now.getTime(),evidenceStatus:'VERIFIED',accountTruth:true});
  assert.equal(publicEntry.amount,'12.34');assert.equal(publicEntry.evidenceStatus,'REPORTED');
  for(const field of ['userId','email','payloadHash','accountTruth'])assert.equal(Object.hasOwn(publicEntry,field),false);
});
test('write requires exact same-origin and rejects absent, forged and cross-site origins',()=>{
  const req=(headers)=>new Request('https://money.example/api/earn-ledger',{method:'POST',headers});
  assert.equal(validWriteOrigin(req({origin:'https://money.example'})),true);
  for(const headers of [{},{origin:'null'},{origin:'https://evil.example'},{origin:'https://money.example','sec-fetch-site':'cross-site'}])assert.equal(validWriteOrigin(req(headers)),false);
});
test('request parser enforces JSON, bytes and streaming size before parsing',async()=>{
  const req=(body,headers={})=>new Request('https://money.example/api/earn-ledger',{method:'POST',headers:{'content-type':'application/json',...headers},body});
  assert.deepEqual(await readLedgerBody(req(JSON.stringify(entry))),entry);
  await assert.rejects(()=>readLedgerBody(req('x'.repeat(4097))),/BODY_TOO_LARGE/);
  await assert.rejects(()=>readLedgerBody(req('{}',{'content-length':'4097'})),/BODY_TOO_LARGE/);
  await assert.rejects(()=>readLedgerBody(req('{}',{'content-type':'text/plain'})),/JSON_REQUIRED/);
  await assert.rejects(()=>readLedgerBody(req('{')),/INVALID_JSON/);
  await assert.rejects(()=>readLedgerBody(req(new Uint8Array([255]))),/INVALID_JSON/);
});
test('pagination cursor cannot inject query scope or use malformed identity',()=>{
  assert.equal(parseLedgerCursor(null),null);
  assert.deepEqual(parseLedgerCursor(`${now.getTime()}_${entry.clientId}`),{createdAt:now.getTime(),id:entry.clientId});
  for(const value of ['other-user',`${now.getTime()}_sql\x27`,[],`${now.getTime()}_${entry.clientId}?user=other`])assert.throws(()=>parseLedgerCursor(value));
});
test('legacy import preserves unknown dates, duration and unverified paid flags with stable per-row IDs',async()=>{
  const row={platform:'Prolific',net:120.5,mins:30,paid:true};
  const document={source:'MONEY_OMEGA_EARN_LEGACY',schema_version:'1.0',legacyMoneyOmegaLog:[row,{...row,net:0,paid:false},row]};
  const first=await legacyLedgerPreview(document), second=await legacyLedgerPreview(document);
  assert.deepEqual(first,second);assert.notEqual(first[0].clientId,first[2].clientId);
  assert.equal(first[0].occurredOn,null);assert.equal(first[0].minutes,30);assert.equal(first[0].currency,'MXN');
  const pending=validateLedgerEntry(first[1],now);assert.equal(pending.amountMinor,0);
  assert.equal(publicLedgerEntry({...pending,id:'id',createdAt:now.getTime()}).evidenceStatus,'PENDING');
  assert.equal(publicLedgerEntry({...validateLedgerEntry(first[0],now),id:'id',createdAt:now.getTime(),evidenceStatus:'VERIFIED'}).evidenceStatus,'REPORTED');
  assert.throws(()=>validateLedgerEntry({...entry,occurredOn:null},now));
});
test('legacy import refuses fabricated dates, silent rounding and unsafe metadata',async()=>{
  const base={source:'MONEY_OMEGA_EARN_LEGACY',schema_version:'1.0'};
  for(const row of [{platform:'safe',net:1.234,mins:10,paid:false},{platform:'x@example.com',net:1,mins:10,paid:true},{platform:'safe',net:1,mins:Infinity,paid:true},{platform:'safe',net:0,mins:10,paid:true},{platform:'safe',net:1,mins:10,paid:'yes'}])await assert.rejects(()=>legacyLedgerPreview({...base,legacyMoneyOmegaLog:[row]}));
});
test('D1 migration preserves five market tables, isolates duplicate keys per user and excludes pending from totals',()=>{
  const db=new DatabaseSync(':memory:');
  try{
    for(const name of readdirSync(new URL('../drizzle/',import.meta.url)).filter(name=>name.endsWith('.sql')).sort())db.exec(readFileSync(new URL('../drizzle/'+name,import.meta.url),'utf8'));
    const tables=db.prepare("select name from sqlite_master where type='table'").all().map(row=>row.name);
    for(const table of ['money_forecasts','money_observations','money_history_cache','money_comparator_cache','money_market_snapshots','money_earn_ledger'])assert.ok(tables.includes(table));
    const insert=db.prepare('insert into money_earn_ledger (id,user_id,client_id,payload_hash,type,amount_minor,currency,occurred_on,category,evidence_status,source,created_at) values (?,?,?,?,?,?,?,?,?,?,?,?)');
    insert.run('one','user-one',entry.clientId,'hash','income',1234,'USD','2026-10-24','OTHER','REPORTED','OPERATOR',now.getTime());
    assert.throws(()=>insert.run('duplicate','user-one',entry.clientId,'otherhash','income',9999,'USD','2026-10-24','OTHER','REPORTED','OPERATOR',now.getTime()),/UNIQUE constraint/);
    insert.run('two','user-two',entry.clientId,'hash','income',9999,'USD','2026-10-24','OTHER','REPORTED','OPERATOR',now.getTime());
    insert.run('pending','user-one','pending-client','hash','income',50000,'USD',null,'OTHER','PENDING','LEGACY_EARN_LOCAL',now.getTime());
    const sum=db.prepare("select sum(amount_minor) as total from money_earn_ledger where user_id=? and evidence_status='REPORTED'").get('user-one');
    assert.equal(sum.total,1234);assert.equal(db.prepare('select count(*) as total from money_earn_ledger where user_id=?').get('user-one').total,2);
  }finally{db.close();}
});
