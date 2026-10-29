#!/usr/bin/env python3
"""NOUS public-safe federation preflight. Standard library; no external systems accessed."""
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent

def load(name: str) -> dict:
    with (ROOT / name).open(encoding="utf-8") as handle:
        return json.load(handle)

def inspect() -> dict:
    agents = load("agents.registry.json")
    projects = load("projects.registry.json")
    connectors = load("connectors.registry.json")
    schema = load("handoff.schema.json")
    node_ids = [node["id"] for node in agents["nodes"]]
    project_ids = [item["id"] for item in projects["projects"]]
    connector_ids = [item["id"] for item in connectors["integrations"]]
    for name, ids in [("nodes", node_ids), ("projects", project_ids), ("integrations", connector_ids)]:
        assert len(ids) == len(set(ids)), f"Duplicate {name} IDs"
        assert all(isinstance(i, str) and i for i in ids), f"Empty {name} IDs"
    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) <= set(schema["properties"])
    states = {"DISCOVERED", "ACCESS_VERIFIED", "READ_VERIFIED", "WRITE_VERIFIED", "ROUND_TRIP_VERIFIED", "STALE", "UNAVAILABLE"}
    assert all(c["status"] in states for c in connectors["integrations"])
    assert all(c["status"] != "ROUND_TRIP_VERIFIED" for c in connectors["integrations"]), "Round-trip requires authenticated proof"
    return {"nodes": len(node_ids), "projects": len(project_ids), "integrations": len(connector_ids)}

def validate_fixture(packet: dict, schema: dict) -> bool:
    """Subset of structural checks; not a complete JSON Schema validator."""
    if not isinstance(packet, dict): return False
    if set(schema["required"]) - set(packet): return False
    if schema.get("additionalProperties") is False and set(packet) - set(schema["properties"]): return False
    for key, value in packet.items():
        entry = schema["properties"].get(key, {})
        kinds = entry.get("type", [])
        kinds = [kinds] if isinstance(kinds, str) else kinds
        if value is None:
            if "null" not in kinds: return False
            continue
        if "string" in kinds and not isinstance(value, str): return False
        if "boolean" in kinds and not isinstance(value, bool): return False
        if "object" in kinds and not isinstance(value, dict): return False
        if "array" in kinds and not isinstance(value, list): return False
        if "enum" in entry and value not in entry["enum"]: return False
        if "const" in entry and value != entry["const"]: return False
        if "minLength" in entry and len(value) < entry["minLength"]: return False
        if key == "authorization" and not {"required","approved"} <= set(value): return False
        if key == "evidence" and not all(isinstance(x, dict) and {"source","status"} <= set(x) for x in value): return False
        if key in ("created_at_utc", "expires_at_utc") and isinstance(value,str):
            try:
                datetime.fromisoformat(value.replace("Z","+00:00"))
            except ValueError: return False
    return True

def main() -> None:
    counts = inspect()
    schema = load("handoff.schema.json")
    packet = {
        "schema_version":"1.0.0", "packet_id":"NOUS-TEST-0001",
        "created_at_utc":"2026-10-28T23:00:00Z",
        "source_node":"NOUS", "target_node":"CJGR_EXECUTIVE_TWIN",
        "project_id":"P-NOUS", "action":"dry-run test, no external side effects",
        "classification":"PUBLICO", "execution_mode":"READ_ONLY",
        "authorization":{"required":True,"approved":False},
        "evidence":[{"source":"fictional fixture","status":"VERIFIED"}],
        "state":"DRAFT"
    }
    assert validate_fixture(packet,schema), "Valid fictional packet rejected"
    assert not validate_fixture({**packet,"classification":"NOT_ALLOWED"},schema)
    assert not validate_fixture({**packet,"secret":"no"},schema)
    assert not validate_fixture({key:value for key,value in packet.items() if key != "authorization"},schema)
    print("NOUS preflight passed. Counts:", json.dumps(counts,sort_keys=True))
    print("No cloud auth, deployments, synchronization or real business actions were attempted.")

if __name__ == "__main__":
    main()
