export type LedgerInput = {clientId:string; type:'income'|'expense'; amount:string; currency:string; occurredOn:string|null; category:string; receiptRef?:string|null; source?:'OPERATOR'|'LEGACY_EARN_LOCAL'; minutes?:number|null; legacyPaidFlag?:boolean|null; legacyPlatform?:string|null};
export type LedgerEntry = {id:string; clientId:string; type:'income'|'expense'; amount:string; currency:string; occurredOn:string|null; category:string; receiptRef:string|null; evidenceStatus:'REPORTED'|'PENDING'; createdAt:string; source:'OPERATOR'|'LEGACY_EARN_LOCAL'; minutes:number|null;legacyPaidFlag:boolean|null;legacyPlatform:string|null};
export type LedgerResponse = {entries:LedgerEntry[]; totalsByCurrency:{currency:string; income:string; expense:string; net:string; count:number}[]; hasMore:boolean; nextCursor:string|null; status:'REPORTED'; accountTruth:false; executionEnabled:false};
export const LEDGER_CURRENCIES: readonly string[];
export const LEDGER_CATEGORIES: readonly string[];
export class LedgerInputError extends Error {code:string;}
export function parseAmount(value:unknown):number;
export function minorToDecimal(value:string|number):string;
export function validateLedgerEntry(input:unknown, now?:Date):{clientId:string;type:'income'|'expense';amountMinor:number;currency:string;occurredOn:string|null;category:string;receiptRef:string|null;source:'OPERATOR'|'LEGACY_EARN_LOCAL';minutes:number|null;legacyPaidFlag:boolean|null;legacyPlatform:string|null};
export function legacyLedgerPreview(document:unknown):Promise<LedgerInput[]>;
export function ledgerPayloadHash(entry:ReturnType<typeof validateLedgerEntry>):Promise<string>;
export function publicLedgerEntry(row:Record<string,any>):LedgerEntry;
export function validWriteOrigin(request:Request):boolean;
export function readLedgerBody(request:Request, limit?:number):Promise<unknown>;
export function parseLedgerCursor(value:string|null):{createdAt:number;id:string}|null;
