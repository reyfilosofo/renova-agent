"""Versioned, expiring research artifacts. Hashes prove integrity, not identity.

The envelope is a detached copy. Any subsequent edit invalidates its digest;
create a new envelope instead. Importing it never grants execution authority.
Legacy envelopes require an explicit, separately reviewed migration.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta
import hashlib
import hmac
import json
import math
import re
import uuid
from urllib.parse import parse_qsl, unquote, urlsplit

from .models import parse_utc, utc_now

SCHEMA_VERSION = "2.1"
DEFAULT_TTL_SECONDS = 3600
MAX_TTL_SECONDS = 86400
MAX_JSON_BYTES = 8 * 1024 * 1024
MAX_JSON_DEPTH = 64
FORBIDDEN_KEYS = {
    "seedphrase", "privatekey", "apisecret", "apikey", "password",
    "recoveryphrase", "sessiontoken", "bearertoken", "oauthrefreshtoken",
    "refreshtoken", "accesstoken", "sessioncookie", "authorization",
    "credentials", "clientsecret", "cookie", "env", "apitoken", "authtoken",
    "authorizationheader", "secretaccesskey",
}
_SECRET_VALUE = re.compile(
    r"-----BEGIN(?: [A-Z0-9]+)* PRIVATE KEY-----"
    r"|\bBearer\s+[A-Za-z0-9._~+/=-]{8,}"
    r"|\bsk-[A-Za-z0-9_-]{20,}"
    r"|\bAKIA[A-Z0-9]{16}\b"
    r"|(?:seed[_ -]?phrase|private[_ -]?key|api[_ -]?(?:secret|key)|password|recovery[_ -]?phrase|(?:session|bearer|access|refresh)[_ -]?token)\s*[:=]\s*\S+",
    re.IGNORECASE,
)
_FIELDS = {"schema_version", "packet_id", "object_id", "object_type", "producer", "created_at_utc", "updated_at_utc", "valid_until_utc", "payload", "sha256"}


def _has_secret_value(value: str) -> bool:
    # Inspect common URL encodings as well as literal text. Neither URL userinfo
    # nor credential query parameters belong in a research packet or its logs.
    decoded = value
    for _ in range(3):
        if _SECRET_VALUE.search(decoded):
            return True
        for match in re.finditer(r"https?://[^\s<>\"']+", decoded, re.IGNORECASE):
            try:
                url = urlsplit(match.group())
                if url.username is not None or url.password is not None:
                    return True
                for key, _value in parse_qsl(url.query, keep_blank_values=True):
                    if re.sub(r"[^a-z0-9]", "", key.casefold()) in FORBIDDEN_KEYS:
                        return True
            except ValueError:
                continue
        expanded = unquote(decoded)
        if expanded == decoded:
            break
        decoded = expanded
    return False


def assert_no_secret_keys(obj, *, _depth: int = 0, _ancestors: frozenset | None = None):
    """Reject recognizable credentials and values that cannot be strict JSON.

    This is a preventive guard, not a promise to identify every possible secret.
    It deliberately reports no submitted value in exceptions or logs.
    """
    if _depth > MAX_JSON_DEPTH:
        raise ValueError("json_depth_limit")
    ancestors = _ancestors or frozenset()
    if isinstance(obj, (dict, list)):
        if id(obj) in ancestors:
            raise ValueError("json_cycle")
        ancestors = ancestors | {id(obj)}
    if isinstance(obj, dict):
        for key, value in obj.items():
            if not isinstance(key, str):
                raise ValueError("json_object_keys_must_be_strings")
            normalized = re.sub(r"[^a-z0-9]", "", key.casefold())
            if normalized in FORBIDDEN_KEYS:
                raise ValueError("forbidden_secret_key")
            assert_no_secret_keys(value, _depth=_depth + 1, _ancestors=ancestors)
    elif isinstance(obj, list):
        for value in obj:
            assert_no_secret_keys(value, _depth=_depth + 1, _ancestors=ancestors)
    elif isinstance(obj, str):
        if _has_secret_value(obj):
            raise ValueError("forbidden_secret_value")
    elif type(obj) is float:
        if not math.isfinite(obj):
            raise ValueError("nonfinite_json_number")
    elif obj is not None and type(obj) not in (bool, int):
        raise ValueError("unsupported_json_type")


def canonical_json(obj) -> bytes:
    assert_no_secret_keys(obj)
    try:
        data = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, UnicodeError, OverflowError, RecursionError) as exc:
        raise ValueError("invalid_strict_json") from exc
    if len(data) > MAX_JSON_BYTES:
        raise ValueError("json_size_limit")
    return data


def strict_json_loads(text: str | bytes):
    """Reject duplicate keys, non-finite numbers and credentials before storage."""
    if not isinstance(text, (str, bytes)):
        raise ValueError("json_text_required")
    try:
        raw = text.encode("utf-8") if isinstance(text, str) else text
        if len(raw) > MAX_JSON_BYTES:
            raise ValueError("json_size_limit")
        decoded = raw.decode("utf-8")
    except UnicodeError as exc:
        raise ValueError("invalid_json_encoding") from exc
    def pairs(items):
        obj = {}
        for key, value in items:
            if key in obj:
                raise ValueError("duplicate_json_key")
            obj[key] = value
        return obj
    def constant(_value):
        raise ValueError("nonfinite_json_number")
    try:
        parsed = json.loads(decoded, object_pairs_hook=pairs, parse_constant=constant)
    except (json.JSONDecodeError, RecursionError) as exc:
        raise ValueError("invalid_json_text") from exc
    canonical_json(parsed)
    return parsed


def _iso(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def envelope(object_type: str, producer: str, payload: dict,
             valid_until_utc: str | None = None, *, now: datetime | None = None,
             ttl_seconds: int = DEFAULT_TTL_SECONDS) -> dict:
    if not isinstance(object_type, str) or not object_type.strip() or not isinstance(producer, str) or not producer.strip():
        raise ValueError("packet_identity_required")
    if not isinstance(payload, dict):
        raise ValueError("packet_payload_must_be_object")
    if type(ttl_seconds) is not int or not 0 < ttl_seconds <= MAX_TTL_SECONDS:
        raise ValueError("invalid_packet_ttl")
    current = utc_now(now)
    try:
        expiry = parse_utc(valid_until_utc) if valid_until_utc is not None else current + timedelta(seconds=ttl_seconds)
    except (ValueError, OverflowError) as exc:
        raise ValueError("invalid_packet_ttl") from exc
    if not 0 < (expiry - current).total_seconds() <= MAX_TTL_SECONDS:
        raise ValueError("invalid_packet_ttl")
    canonical_json(payload)
    packet_id = str(uuid.uuid4())
    body = {"schema_version": SCHEMA_VERSION, "packet_id": packet_id,
            "object_id": packet_id, "object_type": object_type, "producer": producer,
            "created_at_utc": _iso(current), "updated_at_utc": _iso(current),
            "valid_until_utc": _iso(expiry), "payload": deepcopy(payload)}
    body["sha256"] = hashlib.sha256(canonical_json(body)).hexdigest()
    return body


def verify_envelope(packet: dict, now: datetime | None = None) -> tuple[bool, list[str]]:
    """Verify shape, strict JSON, immutable digest and expiry, without trust claims."""
    if not isinstance(packet, dict):
        return False, ["packet_must_be_object"]
    try:
        current = utc_now(now)
        canonical_json(packet)
    except ValueError as exc:
        return False, [str(exc)]
    reasons = []
    if set(packet) != _FIELDS:
        reasons.append("invalid_packet_fields")
    if packet.get("schema_version") != SCHEMA_VERSION:
        reasons.append("unsupported_packet_schema_explicit_migration_required")
    for field in ("packet_id", "object_id", "object_type", "producer"):
        if not isinstance(packet.get(field), str) or not packet[field].strip():
            reasons.append("invalid_packet_identity:" + field)
    try:
        identifier = uuid.UUID(packet.get("packet_id", ""))
        if identifier.version != 4 or str(identifier) != packet.get("packet_id") or packet.get("object_id") != packet.get("packet_id"):
            reasons.append("invalid_packet_id")
    except (ValueError, TypeError, AttributeError):
        reasons.append("invalid_packet_id")
    if not isinstance(packet.get("payload"), dict):
        reasons.append("invalid_packet_payload")
    try:
        created = parse_utc(packet.get("created_at_utc"))
        updated = parse_utc(packet.get("updated_at_utc"))
        expiry = parse_utc(packet.get("valid_until_utc"))
        if updated != created:
            reasons.append("packet_is_not_immutable")
        if created > current:
            reasons.append("packet_created_in_future")
        if not 0 < (expiry - created).total_seconds() <= MAX_TTL_SECONDS:
            reasons.append("invalid_packet_ttl")
        if expiry <= current:
            reasons.append("packet_expired")
    except ValueError:
        reasons.append("invalid_packet_timestamps")
    digest = packet.get("sha256")
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        reasons.append("invalid_packet_digest")
    else:
        body = {key: value for key, value in packet.items() if key != "sha256"}
        expected = hashlib.sha256(canonical_json(body)).hexdigest()
        if not hmac.compare_digest(digest, expected):
            reasons.append("packet_integrity_mismatch")
    return not reasons, reasons
