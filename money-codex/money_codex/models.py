"""Resource observations and conservative arithmetic; never execution authority."""
from __future__ import annotations
from copy import deepcopy
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import math
from urllib.parse import urlsplit

ACCESS_STATES = {"ACCESS VERIFIED", "ACCESS PARTIAL", "ACCESS STALE", "ACCESS UNAVAILABLE"}
OPPORTUNITY_TYPES = {"AIRDROP", "CLAIM", "WALLET_BENEFIT", "QUEST", "SURVEY", "PAID_RESEARCH", "BOUNTY", "MICROTASK", "AFFILIATE", "REFERRAL", "OTHER", "PROGRAM_DISCOVERY"}
COST_FIELDS = ("gas_usd", "fees_usd", "required_spend_usd", "expected_loss_usd", "time_cost_usd", "capital_lockup_cost_usd", "security_risk_cost_usd")
EV_FIELDS = ("expected_gross_reward_usd", "reward_probability", *COST_FIELDS)
SOURCE_MAX_AGE_SECONDS = 86400

def parse_utc(value: object) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("timestamp must be a nonempty timezone-aware string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError) as exc:
        raise ValueError("invalid timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamp timezone is required")
    return parsed.astimezone(timezone.utc)

def utc_now(now: datetime | None = None) -> datetime:
    value = datetime.now(timezone.utc) if now is None else now
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("now must be timezone-aware")
    return value.astimezone(timezone.utc)

def nonnegative_number(value: object, field: str) -> float:
    if type(value) not in (int, float):
        raise ValueError(f"invalid_numeric:{field}")
    try:
        number = float(value)
    except (OverflowError, ValueError) as exc:
        raise ValueError(f"invalid_numeric:{field}") from exc
    if not math.isfinite(number) or number < 0:
        raise ValueError(f"invalid_numeric:{field}")
    return number

def expected_net_reward(values: dict) -> float | None:
    if not isinstance(values, dict):
        raise ValueError("opportunity must be an object")
    numbers = {}
    for field in EV_FIELDS:
        if values.get(field) is not None:
            numbers[field] = nonnegative_number(values[field], field)
    if numbers.get("reward_probability", 0) > 1:
        raise ValueError("invalid_numeric:reward_probability")
    if len(numbers) != len(EV_FIELDS):
        return None
    gross = numbers["expected_gross_reward_usd"] * numbers["reward_probability"]
    try:
        result = gross - math.fsum(numbers[field] for field in COST_FIELDS)
    except OverflowError as exc:
        raise ValueError("invalid_numeric:expected_net_reward_usd") from exc
    if not math.isfinite(result):
        raise ValueError("invalid_numeric:expected_net_reward_usd")
    return result

@dataclass
class AccessRecord:
    name: str
    target: str
    status: str
    detail: str = ""
    def __post_init__(self):
        if self.status not in ACCESS_STATES:
            raise ValueError(f"Invalid access state: {self.status}")
    def to_dict(self):
        return asdict(self)

@dataclass(init=False)
class Opportunity:
    opportunity_id: str
    provider: str
    type: str
    expected_gross_reward_usd: float | None = None
    reward_probability: float | None = None
    gas_usd: float | None = None
    fees_usd: float | None = None
    required_spend_usd: float | None = None
    expected_loss_usd: float | None = None
    time_cost_usd: float | None = None
    capital_lockup_cost_usd: float | None = None
    security_risk_cost_usd: float | None = None
    def __init__(self, opportunity_id, provider, type, expected_gross_reward_usd=None,
                 reward_probability=None, gas_usd=None, fees_usd=None,
                 required_spend_usd=None, expected_loss_usd=None, time_cost_usd=None,
                 capital_lockup_cost_usd=None, security_risk_cost_usd=None, **legacy):
        values = {"expected_gross_reward_usd": expected_gross_reward_usd, "reward_probability": reward_probability,
                  "gas_usd": gas_usd, "fees_usd": fees_usd, "required_spend_usd": required_spend_usd,
                  "expected_loss_usd": expected_loss_usd, "time_cost_usd": time_cost_usd,
                  "capital_lockup_cost_usd": capital_lockup_cost_usd, "security_risk_cost_usd": security_risk_cost_usd}
        aliases = {"reward_value_usd": "expected_gross_reward_usd", "probability_of_receipt": "reward_probability", "platform_fees_usd": "fees_usd"}
        for name, value in legacy.items():
            if name not in aliases:
                raise TypeError(f"unknown opportunity field: {name}")
            canonical = aliases[name]
            if values[canonical] is not None:
                raise ValueError(f"conflicting opportunity field: {canonical}")
            values[canonical] = value
        for field, value in {"opportunity_id": opportunity_id, "provider": provider, "type": type, **values}.items():
            setattr(self, field, value)
    def to_dict(self):
        return asdict(self)
    def expected_net_value(self) -> float | None:
        return expected_net_reward(self.to_dict())

def _https_url(value) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = urlsplit(value)
        return bool(parsed.scheme == "https" and parsed.hostname and not parsed.username and not parsed.password and not parsed.fragment)
    except ValueError:
        return False

def evaluate_opportunity(data: dict, now: datetime | None = None) -> dict:
    """Assess observed public opportunities for human review, preserving unknowns."""
    if not isinstance(data, dict):
        raise ValueError("opportunity must be an object")
    if data.get("schema_version") not in (None, "2.1"):
        raise ValueError("unsupported_opportunity_schema_explicit_migration_required")
    current = utc_now(now)
    result = deepcopy(data)
    missing, blocking = [], []
    for field in ("opportunity_id", "provider"):
        if not isinstance(data.get(field), str) or not data[field].strip():
            missing.append(field)
    if not isinstance(data.get("type"), str) or data["type"] not in OPPORTUNITY_TYPES:
        blocking.append("invalid_opportunity_type")
    if "discovery_only" in data and type(data["discovery_only"]) is not bool:
        blocking.append("invalid_discovery_only")
    for field in EV_FIELDS:
        result.setdefault(field, None)
        if data.get(field) is None:
            missing.append(field)
    try:
        net = expected_net_reward(data)
    except (ValueError, OverflowError) as exc:
        net = None
        blocking.append(str(exc) if isinstance(exc, ValueError) else "invalid_numeric:expected_net_reward_usd")
    source_ok = True
    if not _https_url(data.get("official_url")):
        missing.append("official_url")
        source_ok = False
    proof = data.get("source_evidence")
    if not isinstance(proof, dict):
        missing.append("source_evidence")
        source_ok = False
    else:
        if not _https_url(proof.get("url")) or (proof.get("url") != data.get("official_url") and proof.get("observed_link") != data.get("official_url")):
            blocking.append("source_identity_unverified")
            source_ok = False
        digest = proof.get("content_sha256")
        if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            missing.append("source_evidence.content_sha256")
            source_ok = False
        if type(proof.get("http_status")) is not int or proof["http_status"] != 200:
            missing.append("source_evidence.http_status")
            source_ok = False
    evidence = data.get("evidence")
    if not isinstance(evidence, list) or not evidence or any(not isinstance(item, str) or not item.strip() for item in evidence):
        missing.append("evidence")
        source_ok = False
    for field, value in (("last_verified_at_utc", data.get("last_verified_at_utc")), ("source_evidence.observed_at", proof.get("observed_at") if isinstance(proof, dict) else None)):
        try:
            observed = parse_utc(value)
            age = (current - observed).total_seconds()
            if age < 0 or age > SOURCE_MAX_AGE_SECONDS:
                blocking.append("stale_or_future:" + field)
                source_ok = False
        except ValueError:
            missing.append(field)
            source_ok = False
    if data.get("deadline_utc") is None and data.get("deadline_status") != "NOT_APPLICABLE":
        missing.append("deadline_utc")
    elif data.get("deadline_utc") is not None:
        try:
            if parse_utc(data["deadline_utc"]) <= current:
                blocking.append("opportunity_expired")
        except ValueError:
            blocking.append("invalid_deadline")
    eligibility = data.get("eligibility_status", "UNKNOWN")
    if eligibility == "INELIGIBLE":
        blocking.append("ineligible")
    elif eligibility != "VERIFIED":
        missing.append("eligibility_status")
    if eligibility == "VERIFIED" and (not isinstance(data.get("eligibility_basis"), str) or not data["eligibility_basis"].strip()):
        missing.append("eligibility_basis")
    tos = data.get("tos_status", "UNKNOWN")
    if tos == "CONFLICT":
        blocking.append("tos_conflict")
    elif tos != "VERIFIED":
        missing.append("tos_status")
    security = data.get("security_risk", "UNKNOWN")
    if security == "HIGH":
        blocking.append("high_security_risk")
    elif security not in ("LOW", "MEDIUM"):
        missing.append("security_risk")
    for field in ("geography", "kyc_requirements", "wallet_network", "required_capital_usd", "required_actions", "irreversible_actions", "time_cost_minutes", "repeatability", "invalidation"):
        result.setdefault(field, None)
        if data.get(field) is None:
            missing.append(field)
    for field in ("required_capital_usd", "time_cost_minutes"):
        if data.get(field) is not None:
            try:
                nonnegative_number(data[field], field)
            except ValueError as exc:
                blocking.append(str(exc))
    for field in ("required_actions", "irreversible_actions"):
        if data.get(field) is not None and (not isinstance(data[field], list) or any(not isinstance(item, str) or not item.strip() for item in data[field])):
            blocking.append("invalid_actions:" + field)
    discovery_only = data.get("discovery_only") is True or data.get("type") == "PROGRAM_DISCOVERY"
    if any(reason in blocking for reason in ("opportunity_expired", "ineligible", "tos_conflict", "high_security_risk")) or (net is not None and net <= 0):
        classification = "SKIP"
    elif not source_ok or any(reason.startswith("invalid_") for reason in blocking):
        classification = "DATA INSUFFICIENT"
    elif missing or blocking or discovery_only:
        classification = "WATCH"
    else:
        classification = "QUEUE"
    result.update(schema_version="2.1", expected_net_reward_usd=net, expected_net_value_usd=net,
                  ev_status="DATA INSUFFICIENT" if net is None else "CALCULATED",
                  classification=classification, discovery_only=discovery_only,
                  status=classification, missing_data=list(dict.fromkeys(missing)), blocking_reasons=list(dict.fromkeys(blocking)),
                  evaluated_at_utc=current.isoformat().replace("+00:00", "Z"), execution_authority=False,
                  execution_allowed=False,
                  next_action="Human review" if classification == "QUEUE" else "Verify missing evidence" if classification in ("WATCH", "DATA INSUFFICIENT") else "Do not pursue")
    return result
