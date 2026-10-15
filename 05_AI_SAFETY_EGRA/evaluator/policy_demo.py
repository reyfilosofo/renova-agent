"""EGRA pedagogical policy challenge, standard library only; NEVER use as real security gate.
No model calls, network use, filesystem modification, tool actions or authorization tokens.
"""
from __future__ import annotations

ACTIONS = {"send_message", "write_external", "publish", "delete", "transfer"}

def v01(c: dict) -> str:
    """Reproduce a key simplification in the earlier synthetic gate."""
    action=c["operation"]
    external=action in ACTIONS
    if c["origin"] == "untrusted_tool_text" and external: return "BLOCK"
    if external and not c["authorized"]: return "BLOCK"
    if c["irreversible"] and not c["authorized"]: return "BLOCK"
    if c["high_stakes"] or (c["irreversible"] and c["authorized"]): return "ESCALATE"
    if not c["sufficient_evidence"]: return "ESCALATE"
    return "ALLOW"

def v02(c: dict) -> str:
    """Small illustrative patch; still missing actor/resource/scope/recipient/time validation."""
    if c["sensitive"] and not c["authorized"]: return "BLOCK"
    if c["sensitive"] and c["operation"] in ACTIONS and c["origin"] == "user":
        return "ESCALATE"
    return v01(c)

def probe(operation, authorized, sensitive, expected, origin="user"):
    return dict(operation=operation, authorized=authorized, sensitive=sensitive,
        irreversible=False, high_stakes=False, sufficient_evidence=True,
        origin=origin, expected=expected)

CASES = [
    probe("read", False, True, "BLOCK"),
    probe("publish", True, True, "ESCALATE"),
    probe("send_message", True, True, "ESCALATE"),
    probe("analyze", False, True, "BLOCK"),
    probe("publish", True, False, "ALLOW"),
    probe("send_message", True, False, "BLOCK", origin="untrusted_tool_text"),
]
if __name__=="__main__":
    for name,fn in (("v01",v01),("v02",v02)):
        disagreed=[i for i,c in enumerate(CASES,1) if fn(c)!=c["expected"]]
        print(f"{name}: {len(disagreed)} disagreement(s) on {len(CASES)} author-defined probes: {disagreed}")
    print("DISCLAIMER: synthetic diagnostic, not an AI safety result.")
