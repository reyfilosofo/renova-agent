import { and, desc, eq, lt, or, sql } from 'drizzle-orm';
import { getChatGPTUser } from '@/app/chatgpt-auth';
import { getDb } from '@/db';
import { earnLedger } from '@/db/schema';
import { LedgerInputError, ledgerPayloadHash, minorToDecimal, parseLedgerCursor, publicLedgerEntry, readLedgerBody, validWriteOrigin, validateLedgerEntry } from '@/lib/earn-ledger.mjs';

export const dynamic = 'force-dynamic';
const headers = { 'Cache-Control': 'private, no-store', 'Vary': 'Cookie, oai-authenticated-user-id' };
const reply = (body: unknown, status = 200) => Response.json(body, { status, headers });
const unauthorized = () => reply({ error: 'SIGN_IN_REQUIRED', signInUrl: '/signin-with-chatgpt?return_to=%2F%23registro' }, 401);

export async function GET(request: Request) {
  const user = await getChatGPTUser();
  if (!user) return unauthorized();
  try {
    const before = parseLedgerCursor(new URL(request.url).searchParams.get('before'));
    const owned = eq(earnLedger.userId, user.userId);
    const where = before ? and(owned, or(lt(earnLedger.createdAt, before.createdAt), and(eq(earnLedger.createdAt, before.createdAt), lt(earnLedger.id, before.id)))) : owned;
    const db = getDb();
    const [rows, sums] = await Promise.all([
      db.select().from(earnLedger).where(where).orderBy(desc(earnLedger.createdAt), desc(earnLedger.id)).limit(101),
      db.select({currency:earnLedger.currency, income:sql<string>`cast(sum(case when ${earnLedger.type} = 'income' then ${earnLedger.amountMinor} else 0 end) as text)`, expense:sql<string>`cast(sum(case when ${earnLedger.type} = 'expense' then ${earnLedger.amountMinor} else 0 end) as text)`, count:sql<number>`count(*)`}).from(earnLedger).where(and(owned,eq(earnLedger.evidenceStatus,'REPORTED'))).groupBy(earnLedger.currency),
    ]);
    const visible = rows.slice(0, 100); const last = visible.at(-1);
    return reply({ entries: visible.map(publicLedgerEntry), totalsByCurrency:sums.map(s => ({currency:s.currency, income:minorToDecimal(s.income), expense:minorToDecimal(s.expense), net:minorToDecimal(String(BigInt(s.income)-BigInt(s.expense))), count:s.count})), hasMore:rows.length>100, nextCursor:rows.length>100 && last ? `${last.createdAt}_${last.id}` : null,
      status:'REPORTED', accountTruth:false, executionEnabled:false });
  } catch (error) {
    if (error instanceof LedgerInputError) return reply({ error:error.code }, 400);
    return reply({ error:'LEDGER_UNAVAILABLE' }, 503);
  }
}

export async function POST(request: Request) {
  const user = await getChatGPTUser();
  if (!user) return unauthorized();
  if (!validWriteOrigin(request)) return reply({ error:'ORIGIN_REJECTED' }, 403);
  try {
    const input = validateLedgerEntry(await readLedgerBody(request));
    const payloadHash = await ledgerPayloadHash(input);
    const db = getDb();
    const inserted = await db.insert(earnLedger).values({id:crypto.randomUUID(), userId:user.userId, ...input, payloadHash, evidenceStatus:input.source==='LEGACY_EARN_LOCAL'&&input.legacyPaidFlag===false?'PENDING':'REPORTED', createdAt:Date.now()})
      .onConflictDoNothing({target:[earnLedger.userId, earnLedger.clientId]}).returning({id:earnLedger.id});
    const [row] = await db.select().from(earnLedger).where(and(eq(earnLedger.userId,user.userId),eq(earnLedger.clientId,input.clientId))).limit(1);
    if (!row) return reply({ error:'LEDGER_UNAVAILABLE' },503);
    if (row.payloadHash !== payloadHash) return reply({ error:'IDEMPOTENCY_CONFLICT' },409);
    return reply({entry:publicLedgerEntry(row), replay:inserted.length===0, status:'REPORTED', accountTruth:false, executionEnabled:false},inserted.length ? 201 : 200);
  } catch (error) {
    if (error instanceof LedgerInputError) return reply({ error:error.code }, error.code==='BODY_TOO_LARGE' ? 413 : 400);
    return reply({ error:'LEDGER_UNAVAILABLE' },503);
  }
}
