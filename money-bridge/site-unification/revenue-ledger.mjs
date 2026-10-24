/**
 * MONEY Ω v0.1 — pure financial receipt reconciler.
 * A computation utility, NOT a database writer or proof of actual income.
 * Input must come from a private, permissioned account verification process.
 * No wallet keys, account numbers or personal details are accepted or stored.
 */
const ID=/^[a-zA-Z0-9_.:-]{3,160}$/;
const CCY=/^[A-Z]{3}$/;
const TIMESTAMP=/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$/;
function decimalAmount(v,field){if(typeof v!=="number"||!Number.isFinite(v)||v<0||v>1e12)throw new Error("INVALID_"+field.toUpperCase());return v}
function normalizeReceipt(row){
 if(!row||typeof row!=="object"||Array.isArray(row))throw new Error("INVALID_RECEIPT");
 const provider=String(row.provider||"").trim().toLowerCase(),id=String(row.external_transaction_id||"").trim(),currency=String(row.currency||"").trim().toUpperCase();
 if(!ID.test(provider)||!ID.test(id)||!CCY.test(currency))throw new Error("INVALID_RECEIPT_IDENTITY");
 if(row.source_type!=="ACCOUNT_VERIFIED"||row.readback_verified!==true||row.status!=="SETTLED")throw new Error("UNVERIFIED_PAYMENT");
 if(typeof row.observed_at_utc!=="string"||!TIMESTAMP.test(row.observed_at_utc)||!Number.isFinite(Date.parse(row.observed_at_utc)))throw new Error("INVALID_TIMESTAMP");
 const gross=decimalAmount(row.gross_amount,"gross"),fees=decimalAmount(row.fees,"fees"),refund=decimalAmount(row.refund_amount??0,"refund");
 if(fees+refund>gross+1e-8)throw new Error("COSTS_EXCEED_GROSS");
 const net=Number((gross-fees-refund).toFixed(8));
 return Object.freeze({key:provider+":"+id+":"+currency,provider,external_transaction_id:id,currency,gross_amount:gross,fees,refund_amount:refund,net_amount:net,observed_at_utc:row.observed_at_utc,status:"PAID_VERIFIED",source_type:"ACCOUNT_VERIFIED"});
}
function reconcileReceipts(records){
 if(!Array.isArray(records))throw new Error("INVALID_RECORD_COLLECTION");
 const map=new Map();
 for(const record of records){const row=normalizeReceipt(record);if(map.has(row.key)){const prev=map.get(row.key);if(JSON.stringify(prev)!==JSON.stringify(row))throw new Error("CONFLICTING_DUPLICATE_RECEIPT");continue;}map.set(row.key,row);}
 const totals={};for(const row of map.values()){const v=totals[row.currency]||(totals[row.currency]={gross:0,fees:0,refunds:0,net:0,receipt_count:0});v.gross=Number((v.gross+row.gross_amount).toFixed(8));v.fees=Number((v.fees+row.fees).toFixed(8));v.refunds=Number((v.refunds+row.refund_amount).toFixed(8));v.net=Number((v.net+row.net_amount).toFixed(8));v.receipt_count++;}
 return Object.freeze({schema_version:"0.1.0",entries:[...map.values()],totals,verified_receipt_count:map.size,warning:"Totals are source-verified only if receipts were actually read from the authorized source. Never convert currencies silently."});
}
export{normalizeReceipt,reconcileReceipts};
