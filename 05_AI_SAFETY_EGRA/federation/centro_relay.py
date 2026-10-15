"""CENTRO packet preflight; OFFLINE ONLY, no API calls, no auth, no publishing.
Research demonstration, not a production security gate.
"""
import argparse, hashlib, json
REQUIRED = {"packet_id","schema_version","created_at_utc","source_node","target_node","project_id","classification","evidence","action","authorization","state"}
PUBLIC = {"github","gitlab","discord","moltbook"}
VALID_CLASS = {"P0_PUBLIC","P1_INTERNAL","P2_CONFIDENTIAL","P3_SECRET"}
VALID_STATE = {"DRAFT","READY","SENT","ACKNOWLEDGED","FAILED","BLOCKED"}
def validate(p):
    errors = []
    if not isinstance(p,dict): return ["packet must be JSON object"]
    if not REQUIRED.issubset(p): errors.append("missing required fields")
    if p.get("schema_version")!="1.0": errors.append("unsupported schema version")
    if p.get("classification") not in VALID_CLASS: errors.append("invalid data class")
    if p.get("state") not in VALID_STATE: errors.append("invalid state")
    if p.get("target_node","").lower() in PUBLIC and p.get("classification")!="P0_PUBLIC":
        errors.append("nonpublic data cannot go to public target")
    if p.get("state") in {"SENT","ACKNOWLEDGED"}:
        if not p.get("result_ref"): errors.append("delivery receipt missing")
        if p.get("authorization")!="explicit_publish_authorization":
            errors.append("explicit publication authorization missing")
    return errors
def sha256(p):
    return hashlib.sha256(json.dumps(p,sort_keys=True,ensure_ascii=False,separators=(",",":")).encode()).hexdigest()
if __name__ == "__main__":
    a=argparse.ArgumentParser(description="Dry run only: packet sanity and hashing")
    a.add_argument("packet")
    args=a.parse_args()
    with open(args.packet,encoding="utf-8") as f: packet=json.load(f)
    errors=validate(packet)
    print(json.dumps({"mode":"DRY_RUN_NO_DELIVERY","valid":not errors,"errors":errors,"sha256":sha256(packet)},indent=2))
    raise SystemExit(bool(errors))
