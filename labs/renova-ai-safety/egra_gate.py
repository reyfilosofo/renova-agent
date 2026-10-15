"""EGRA-002: offline *illustration*, not a deployed security mechanism.
This program performs no external actions. Synthetic tests are not empirical proof.
"""
from dataclasses import dataclass
from enum import Enum

class Verdict(str, Enum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    ESCALATE = "ESCALATE"

class Trust(str, Enum):
    USER = "authenticated_user"
    DOCUMENT = "untrusted_document"
    TOOL = "untrusted_tool_output"
    SYSTEM = "trusted_system_policy"

READ = frozenset({"read_public", "summarize", "draft_local", "analyze_offline"})
EXTERNAL = frozenset({
    "send_message", "publish", "write_external", "delete", "transfer",
    "schedule_task", "deploy", "modify_permissions", "create_account",
    "submit_application", "purchase", "issue_refund", "open_url_with_payload"
})

@dataclass(frozen=True)
class Request:
    operation: str
    instruction_origin: Trust
    user_authorized: bool
    target_scoped: bool
    sensitive: bool = False
    irreversible: bool = False
    high_impact: bool = False
    evidence_sufficient: bool = True
    authorization_verified_out_of_band: bool = False

@dataclass(frozen=True)
class Decision:
    verdict: Verdict
    reason: str

def evaluate(req: Request) -> Decision:
    """Return advisory classification. External deterministic gateway REQUIRED."""
    if req.operation not in READ | EXTERNAL:
        return Decision(Verdict.ESCALATE, "UNRECOGNIZED_OPERATION")
    if req.operation in EXTERNAL:
        if req.instruction_origin in {Trust.DOCUMENT, Trust.TOOL}:
            return Decision(Verdict.BLOCK, "LOW_TRUST_INSTRUCTION_CANNOT_AUTHORIZE")
        if not req.user_authorized or not req.target_scoped:
            return Decision(Verdict.BLOCK, "MISSING_EXPLICIT_SCOPED_AUTHORIZATION")
        if not req.authorization_verified_out_of_band:
            return Decision(Verdict.ESCALATE, "AUTHORIZATION_NOT_INDEPENDENTLY_VERIFIED")
        if req.sensitive or req.irreversible or req.high_impact:
            return Decision(Verdict.ESCALATE, "IMPACT_REQUIRES_HUMAN_CHECKPOINT")
    if req.high_impact or req.sensitive:
        return Decision(Verdict.ESCALATE, "SENSITIVE_OR_HIGH_IMPACT_TASK")
    if not req.evidence_sufficient:
        return Decision(Verdict.ESCALATE, "EVIDENCE_INSUFFICIENT")
    return Decision(Verdict.ALLOW, "MEETS_DEMONSTRATION_POLICY")
