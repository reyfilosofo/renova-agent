#!/usr/bin/env python3
"""NOUS public-safe preflight using Draft 2020-12 JSON Schema; no external systems accessed."""
from __future__ import annotations
import json
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker

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
    """Validate *all* nested fields with the authoritative JSON Schema and formats."""
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return validator.is_valid(packet)

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
    assert not validate_fixture({**packet,"created_at_utc":"never"},schema)
    assert not validate_fixture({**packet,"evidence":[{"source":"fictional fixture","status":"INVALID"}]},schema)
    assert not validate_fixture({**packet,"authorization":{"required":True}},schema)
    print("NOUS preflight passed. Counts:", json.dumps(counts,sort_keys=True))
    print("No cloud auth, deployments, synchronization or real business actions were attempted.")

if __name__ == "__main__":
    main()
