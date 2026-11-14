#!/usr/bin/env python3
"""FED-22 offline relay guard. NO network requests, model calls or credentials."""
import argparse
import hashlib
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT = "RENOVA-AI-SAFETY-GOVERNANCE"
FIELDS = {"packet_id","schema_version","created_at","expires_at","source_node","target_node","project_id","data_classification","mission","requested_operation","source_refs","state","provider_receipt_id","readback_verified"}
OPS = {"READ","ANALYZE","REVIEW","PROPOSE_PATCH"}

def when(s):
    v=datetime.fromisoformat(s.replace("Z","+00:00"))
    if v.utcoffset() is None: raise ValueError("timezone required")
    return v.astimezone(timezone.utc)

def check(packet,now=None):
    """Local structural check; NEVER substitutes authentication."""
    p=packet
    if not isinstance(p,dict): return ["not an object"]
    errors=["missing "+k for k in sorted(FIELDS-set(p))]
    errors+=["unexpected "+k for k in sorted(set(p)-FIELDS)]
    if errors: return errors
    if p["project_id"]!=PROJECT or p["schema_version"] not in ("2.1","2.2"): errors.append("project/schema")
    for k in ("packet_id","source_node","target_node"):
        if not isinstance(p[k],str) or not p[k] or len(p[k])>150: errors.append("invalid "+k)
    if not isinstance(p["packet_id"],str) or len(p["packet_id"])<12: errors.append("short packet_id")
    if p["data_classification"] not in ("PUBLIC","INTERNAL","CONFIDENTIAL"): errors.append("bad classification")
    if p["requested_operation"] not in OPS: errors.append("bad operation")
    if p["state"] not in ("PREPARED","DISPATCHED","ACKNOWLEDGED","REJECTED","EXPIRED"): errors.append("bad state")
    if not isinstance(p["mission"],str) or not 10<=len(p["mission"])<=6000: errors.append("bad mission")
    refs=p["source_refs"]
    if not isinstance(refs,list) or not 1<=len(refs)<=15 or not all(isinstance(u,str) and u.startswith("https://") and len(u)<800 for u in refs):errors.append("bad source_refs")
    if p["data_classification"]=="PUBLIC" and isinstance(refs,list) and any(not isinstance(u,str) or not u.startswith("https://github.com/reyfilosofo/renova-agent") for u in refs):errors.append("unapproved public source")
    if type(p["readback_verified"]) is not bool: errors.append("invalid readback")
    try:
        a,b=when(p["created_at"]),when(p["expires_at"])
        n=now or datetime.now(timezone.utc)
        if b<=a or (b-a).total_seconds()>86400:errors.append("invalid expiration window")
        if n>=b:errors.append("expired packet")
        if (a-n).total_seconds()>300:errors.append("future timestamp")
    except (TypeError,ValueError,AttributeError): errors.append("invalid timestamps")
    if p["state"]=="ACKNOWLEDGED" and (not isinstance(p["provider_receipt_id"],str) or not p["provider_receipt_id"] or p["readback_verified"] is not True):errors.append("unverified ack")
    if p["state"]=="PREPARED" and (p["provider_receipt_id"] is not None or p["readback_verified"] is not False):errors.append("fabricated receipt")
    return errors

def stage(packet,ledger_path):
    """Persist one packet ID (replay prevention). Only a local PREPARED draft is staged."""
    issues=check(packet)
    if packet.get("state")!="PREPARED":issues.append("only PREPARED may be staged")
    if issues:raise ValueError(";".join(issues))
    cx=sqlite3.connect(str(ledger_path))
    try:
        cx.execute("CREATE TABLE IF NOT EXISTS packets (packet_id TEXT PRIMARY KEY, sha256 TEXT NOT NULL, status TEXT NOT NULL)")
        digest=hashlib.sha256(json.dumps(packet,sort_keys=True).encode()).hexdigest()
        try:
            cx.execute("INSERT INTO packets VALUES (?,?,?)",(packet["packet_id"],digest,"STAGED_OFFLINE"))
            cx.commit()
        except sqlite3.IntegrityError as exc:
            raise ValueError("replay blocked") from exc
        return {"packet_id":packet["packet_id"],"sha256":digest,"status":"STAGED_OFFLINE","provider_sent":False}
    finally:cx.close()

if __name__=="__main__":
    ap=argparse.ArgumentParser(description="Validates packets. No network transport.")
    ap.add_argument("packet")
    ap.add_argument("--stage",action="store_true")
    ap.add_argument("--ledger",default="fed22_local.sqlite")
    args=ap.parse_args()
    obj=json.loads(Path(args.packet).read_text(encoding="utf-8"))
    try: report=stage(obj,args.ledger) if args.stage else {"valid":not check(obj),"issues":check(obj),"provider_sent":False}
    except ValueError as ex:report={"valid":False,"error":str(ex),"provider_sent":False}
    print(json.dumps(report,ensure_ascii=False))
    sys.exit(0 if report.get("valid",report.get("status")=="STAGED_OFFLINE") else 2)
