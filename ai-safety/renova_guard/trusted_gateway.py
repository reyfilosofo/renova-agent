"""Offline *simulated* reference monitor for ℛenova AI Safety v0.2.

It cannot call production tools or authenticate a real human. An issue_approval()
call only models an out-of-band trusted human approval: the integration MUST
replace it with a real identity-bound approval service. Do not deploy this module.
"""
from __future__ import annotations
from dataclasses import dataclass
import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any

AUDIENCE = 'renova-mock-tool-gateway-v0.2'
OPS = {'read', 'write_draft', 'send_external', 'delete_draft'}
MUTATING = OPS - {'read'}
MAX_ACTION_BYTES = 8192
MAX_TOKEN_BYTES = 4096
TRUSTED_GRANTS = {
    'researcher': {
        'read': ('sandbox/docs/',),
        'write_draft': ('sandbox/drafts/',),
        'send_external': ('sandbox/outbox/',),
        'delete_draft': ('sandbox/drafts/',),
    },
    'reader': {'read': ('sandbox/docs/',)},
}

class GateError(ValueError):
    """Denial with a stable, non-sensitive reason code."""

def _canonical(value: Any) -> bytes:
    try:
        packed = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'),
                            allow_nan=False).encode('utf-8')
    except (TypeError, ValueError, OverflowError) as exc:
        raise GateError('UNSERIALIZABLE') from exc
    if len(packed) > MAX_ACTION_BYTES:
        raise GateError('ACTION_TOO_LARGE')
    return packed

def _validate_resource(resource: Any) -> str:
    if not isinstance(resource, str) or not resource.startswith('sandbox/') or len(resource) > 180:
        raise GateError('BAD_RESOURCE')
    if resource.endswith('/') or any(part in ('', '.', '..') for part in resource.split('/')):
        raise GateError('PATH_TRAVERSAL_OR_DIRECTORY')
    if '\\' in resource or '?' in resource or '#' in resource or '\x00' in resource:
        raise GateError('BAD_RESOURCE')
    return resource

def _validate_proposal(proposal: Any) -> tuple[dict[str, Any], bytes]:
    if type(proposal) is not dict or set(proposal) != {'operation', 'resource', 'args'}:
        raise GateError('INVALID_PROPOSAL_SCHEMA')
    operation, resource, args = proposal['operation'], proposal['resource'], proposal['args']
    if not isinstance(operation, str) or operation not in OPS:
        raise GateError('UNKNOWN_OPERATION')
    resource = _validate_resource(resource)
    if type(args) is not dict or any(not isinstance(k, str) for k in args):
        raise GateError('INVALID_ARGUMENTS')
    if operation == 'read' and args != {}:
        raise GateError('READ_NO_ARGUMENTS')
    if operation == 'write_draft' and (set(args) != {'text'} or not isinstance(args['text'], str)):
        raise GateError('INVALID_DRAFT_ARGUMENTS')
    if operation == 'send_external' and (set(args) != {'text'} or not isinstance(args['text'], str)):
        raise GateError('INVALID_SEND_ARGUMENTS')
    if operation == 'delete_draft' and args != {}:
        raise GateError('DELETE_NO_ARGUMENTS')
    normalized = {'operation': operation, 'resource': resource, 'args': args}
    return normalized, _canonical(normalized)

def _check_grant(principal: Any, proposal: dict[str, Any]) -> None:
    if not isinstance(principal, str) or principal not in TRUSTED_GRANTS:
        raise GateError('UNKNOWN_PRINCIPAL')
    prefixes = TRUSTED_GRANTS[principal].get(proposal['operation'], ())
    if not any(proposal['resource'].startswith(prefix) for prefix in prefixes):
        raise GateError('PERMISSION_DENIED')

def _encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode('ascii').rstrip('=')

def _decode(raw: str) -> bytes:
    return base64.b64decode(raw + '=' * ((-len(raw)) % 4), altchars=b'-_', validate=True)

@dataclass(frozen=True)
class Outcome:
    decision: str
    executed: bool
    reason: str
    digest: str | None = None

class MockTrustedApprovals:
    """Test harness for a hypothetical trusted authorization service.

    issue_approval IS NOT human identity verification. A production solution
    requires independent authentication and protected key custody.
    """
    def __init__(self, secret: bytes | None = None):
        self.__key = secret or os.urandom(32)
        if len(self.__key) < 32:
            raise ValueError('Mock signing key too short')

    def issue_approval(self, principal: str, proposal: dict[str, Any],
                       *, simulated_human_attested: bool = False,
                       ttl: int = 120, now: int | None = None) -> str:
        if simulated_human_attested is not True:
            raise GateError('MOCK_HUMAN_APPROVAL_REQUIRED')
        if type(ttl) is not int or not 1 <= ttl <= 300:
            raise GateError('TTL_OUT_OF_RANGE')
        validated, raw = _validate_proposal(proposal)
        _check_grant(principal, validated)
        if validated['operation'] not in MUTATING:
            raise GateError('APPROVAL_NOT_REQUIRED_FOR_READ')
        tick = int(time.time()) if now is None else int(now)
        claims = {'aud': AUDIENCE, 'principal': principal, 'operation': validated['operation'],
                  'resource': validated['resource'], 'intent_sha256': hashlib.sha256(raw).hexdigest(),
                  'iat': tick, 'exp': tick + ttl, 'nonce': os.urandom(16).hex()}
        body = _encode(_canonical(claims))
        signature = _encode(hmac.new(self.__key, body.encode('ascii'), hashlib.sha256).digest())
        return body + '.' + signature

    def verify(self, token: Any, principal: str, proposal: dict[str, Any],
               used_nonces: set[str], now: int | None = None) -> str:
        if not isinstance(token, str) or len(token) > MAX_TOKEN_BYTES or token.count('.') != 1:
            raise GateError('MALFORMED_APPROVAL')
        body, signature = token.split('.')
        try:
            actual = _decode(signature)
            expected = hmac.new(self.__key, body.encode('ascii'), hashlib.sha256).digest()
            if not hmac.compare_digest(actual, expected):
                raise GateError('INVALID_APPROVAL_SIGNATURE')
            claims = json.loads(_decode(body))
        except (ValueError, UnicodeError, json.JSONDecodeError) as exc:
            if isinstance(exc, GateError):
                raise
            raise GateError('MALFORMED_APPROVAL') from exc
        if type(claims) is not dict or claims.get('aud') != AUDIENCE:
            raise GateError('INVALID_APPROVAL_AUDIENCE')
        if claims.get('principal') != principal or claims.get('resource') != proposal['resource'] or claims.get('operation') != proposal['operation']:
            raise GateError('APPROVAL_SCOPE_MISMATCH')
        _, raw = _validate_proposal(proposal)
        if claims.get('intent_sha256') != hashlib.sha256(raw).hexdigest():
            raise GateError('APPROVAL_INTENT_MISMATCH')
        tick = int(time.time()) if now is None else int(now)
        if type(claims.get('iat')) is not int or type(claims.get('exp')) is not int or tick < claims['iat'] or tick >= claims['exp'] or claims['exp'] - claims['iat'] > 300:
            raise GateError('APPROVAL_EXPIRED_OR_NOT_YET_VALID')
        nonce = claims.get('nonce')
        if not isinstance(nonce, str) or len(nonce) != 32 or nonce in used_nonces:
            raise GateError('APPROVAL_REPLAY_OR_INVALID_NONCE')
        return nonce

class MockToolGateway:
    """In-memory simulation only; no sockets, subprocesses, file IO, or live tools."""
    def __init__(self, authority: MockTrustedApprovals):
        self._authority = authority
        self._used_nonces: set[str] = set()
        self._data: dict[str, str] = {'sandbox/docs/welcome': 'public fixture'}
        self._audit: list[dict[str, Any]] = []

    @property
    def audit(self) -> tuple[dict[str, Any], ...]:
        return tuple(dict(event) for event in self._audit)

    @property
    def snapshot(self) -> dict[str, str]:
        return dict(self._data)

    def execute(self, principal: str, proposal: Any, *, approval: str | None = None,
                now: int | None = None) -> Outcome:
        try:
            validated, raw = _validate_proposal(proposal)
            _check_grant(principal, validated)
            digest = hashlib.sha256(raw).hexdigest()
            nonce = None
            if validated['operation'] in MUTATING:
                if not approval:
                    raise GateError('TRUSTED_APPROVAL_REQUIRED')
                nonce = self._authority.verify(approval, principal, validated,
                                               self._used_nonces, now=now)
            elif approval:
                raise GateError('UNEXPECTED_APPROVAL_ON_READ')
            op, resource = validated['operation'], validated['resource']
            if op == 'read':
                self._data.get(resource)
            elif op in ('write_draft', 'send_external'):
                self._data[resource] = validated['args']['text']
            elif op == 'delete_draft':
                self._data.pop(resource, None)
            if nonce:
                self._used_nonces.add(nonce)
            outcome = Outcome('ALLOW', True, 'MOCK_OPERATION_PERFORMED', digest)
        except GateError as exc:
            outcome = Outcome('DENY', False, str(exc))
        except Exception:
            outcome = Outcome('DENY', False, 'UNEXPECTED_VALIDATION_FAILURE')
        self._audit.append({'principal': principal if isinstance(principal, str) and principal in TRUSTED_GRANTS else '<unknown>',
                            'decision': outcome.decision, 'executed': outcome.executed,
                            'reason': outcome.reason, 'digest': outcome.digest})
        return outcome
