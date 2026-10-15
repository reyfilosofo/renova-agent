"""Deterministic action-gate prototype. Requires a trusted enforcement boundary.

Input cannot be assumed authentic: a real system must bind identity, tool permissions,
provenance and approval server-side, outside the model's instruction channel.
No calls to external tools are made here.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any, Mapping
import hashlib
import json

LOW_RISK = {'read', 'draft'}
LOCAL_CHANGE = {'write_internal'}
HIGH_RISK = {'send_external', 'payment', 'change_permissions', 'delete', 'execute_code'}
ALL_ACTIONS = LOW_RISK | LOCAL_CHANGE | HIGH_RISK

@dataclass(frozen=True)
class Decision:
    status: str
    reasons: tuple[str, ...]
    policy_version: str = 'renova-guard-0.1.0'
    action_fingerprint: str = ''

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data['reasons'] = list(self.reasons)
        return data


def _fingerprint(action: Mapping[str, Any]) -> str:
    """Hash of minimal action metadata (not payload, recipient, or message body)."""
    minimized = {k: action.get(k) for k in ('type', 'risk', 'reversible', 'authorized', 'human_approved')}
    canonical = json.dumps(minimized, sort_keys=True, ensure_ascii=False, default=str).encode('utf-8')
    return hashlib.sha256(canonical).hexdigest()[:24]


def assess(action: Mapping[str, Any]) -> Decision:
    """Return ALLOW, REVIEW, or DENY for structured, externally asserted metadata.

    REVIEW does not execute an action. High-impact requests cannot be auto-approved
    by the model, even with human_approved=True. A human approval field is merely
    a request to a separate trusted approval service.
    """
    if not isinstance(action, Mapping):
        return Decision('DENY', ('MALFORMED_ACTION',))
    fp = _fingerprint(action)
    typ = action.get('type')
    if not isinstance(typ, str) or typ not in ALL_ACTIONS:
        return Decision('DENY', ('UNKNOWN_ACTION',), action_fingerprint=fp)
    risk = action.get('risk')
    if risk not in ('low', 'medium', 'high'):
        return Decision('REVIEW', ('RISK_NOT_ESTABLISHED',), action_fingerprint=fp)
    authorized = action.get('authorized')
    reversible = action.get('reversible')
    if type(authorized) is not bool:
        return Decision('REVIEW', ('AUTHORIZATION_NOT_ESTABLISHED',), action_fingerprint=fp)
    if type(reversible) is not bool:
        return Decision('REVIEW', ('REVERSIBILITY_NOT_ESTABLISHED',), action_fingerprint=fp)
    if not authorized:
        return Decision('DENY', ('NO_VALID_AUTHORIZATION',), action_fingerprint=fp)
    if action.get('instruction_source') == 'untrusted' and action.get('requested_privilege_escalation') is True:
        return Decision('DENY', ('UNTRUSTED_INSTRUCTION_ESCALATION',), action_fingerprint=fp)
    if typ in HIGH_RISK:
        return Decision('REVIEW', ('EXTERNAL_HIGH_RISK_ACTION', 'TRUSTED_APPROVAL_AND_TOOL_GATE_REQUIRED'), action_fingerprint=fp)
    if risk == 'high' or not reversible:
        return Decision('REVIEW', ('HIGH_RISK_OR_IRREVERSIBLE',), action_fingerprint=fp)
    if typ in LOCAL_CHANGE:
        return Decision('REVIEW', ('INTERNAL_WRITE_REQUIRES_TRUSTED_TRANSACTION_GATE',), action_fingerprint=fp)
    if risk == 'medium':
        return Decision('REVIEW', ('MEDIUM_RISK_HUMAN_REVIEW',), action_fingerprint=fp)
    return Decision('ALLOW', ('LOW_RISK_REHEARSAL_ONLY',), action_fingerprint=fp)


def assess_claim(claim: Mapping[str, Any]) -> Decision:
    """LUCEM label-schema check: citations do not establish truth."""
    if not isinstance(claim, Mapping):
        return Decision('DENY', ('MALFORMED_CLAIM',))
    kind = claim.get('kind')
    if not isinstance(kind, str) or kind not in {'fact', 'inference', 'hypothesis', 'value', 'symbol'}:
        return Decision('REVIEW', ('EPISTEMIC_TYPE_MISSING',))
    if kind == 'fact' and (not isinstance(claim.get('citations'), list) or not claim['citations']):
        return Decision('REVIEW', ('CITATION_REQUIRED',))
    if kind == 'fact':
        return Decision('REVIEW', ('SOURCE_EXISTS_NOT_SAME_AS_FACT_VERIFIED',))
    if claim.get('externally_consequential', False):
        return Decision('REVIEW', ('CONSEQUENTIAL_CLAIM_REVIEW',))
    return Decision('ALLOW', ('EPISTEMIC_LABEL_ACCEPTED_NOT_FACT_CHECKED',))
