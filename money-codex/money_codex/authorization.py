"""Contextual fail-closed validation; no execution adapter.
Context must come from a trusted runtime verifier, never from a submitted packet.
"""
from __future__ import annotations
from datetime import datetime
from .models import nonnegative_number, parse_utc, utc_now
from .packets import canonical_json

REQUIRED_LIVE_FIELDS = ("schema_version", "authorization_id", "authorization_version", "status", "issued_by",
                        "issued_at_utc", "expires_at_utc", "strategy_id", "venue", "account_scope",
                        "allowed_products", "allowed_assets", "permissions", "limits", "kill_switch")
LIMITS = ("max_order_usd", "max_gross_exposure_usd", "max_daily_loss_usd", "max_orders_per_hour")
PERMISSIONS = {"read_market_data", "read_account_state", "place_orders", "cancel_orders", "wallet_sign", "withdraw", "external_transfer"}
FRESH_SECONDS = 30
PAPER_ONLY_STRATEGIES = {"RENOVA_DESK_V0", "MONEY_FIXED_WINDOW_ANALOG_PAPER_V1"}

def validate_live_authorization(auth: dict, now: datetime | None = None, *, context: dict | None = None) -> tuple[bool, list[str]]:
    reasons = []
    if not isinstance(auth, dict):
        return False, ["invalid_authorization_type"]
    try:
        canonical_json(auth)
    except ValueError:
        return False, ["invalid_or_secret_authorization_content"]
    try:
        current = utc_now(now)
    except ValueError:
        return False, ["invalid_clock"]
    for key in REQUIRED_LIVE_FIELDS:
        if key not in auth or auth[key] is None or auth[key] == "":
            reasons.append("missing:" + key)
    if set(auth) - set(REQUIRED_LIVE_FIELDS) - {"revoked_at_utc"}:
        reasons.append("unknown_authorization_fields")
    for key in ("authorization_id", "issued_by", "strategy_id", "venue", "account_scope"):
        if not isinstance(auth.get(key), str) or not auth[key].strip():
            reasons.append("invalid:" + key)
    if auth.get("schema_version") != "2.1":
        reasons.append("unsupported_authorization_schema")
    if type(auth.get("authorization_version")) is not int or auth["authorization_version"] < 1:
        reasons.append("invalid:authorization_version")
    if auth.get("status") != "ACTIVE":
        reasons.append("status_not_active")
    if isinstance(auth.get("strategy_id"), str) and auth["strategy_id"] in PAPER_ONLY_STRATEGIES:
        reasons.append("strategy_is_frozen_paper_only")
    if auth.get("revoked_at_utc") is not None:
        reasons.append("authorization_revoked")
    try:
        issued, expiry = parse_utc(auth.get("issued_at_utc")), parse_utc(auth.get("expires_at_utc"))
        if issued > current:
            reasons.append("authorization_not_yet_valid")
        if expiry <= current or expiry <= issued:
            reasons.append("authorization_expired_or_invalid_interval")
    except ValueError:
        reasons.append("invalid_authorization_timestamps")
    for key in ("allowed_products", "allowed_assets"):
        values = auth.get(key)
        if not isinstance(values, list) or not values or any(not isinstance(x, str) or not x.strip() for x in values) or len(set(x for x in values if isinstance(x, str))) != len(values):
            reasons.append("invalid:" + key)
    permissions = auth.get("permissions")
    if not isinstance(permissions, dict) or set(permissions) != PERMISSIONS or any(type(value) is not bool for value in permissions.values()):
        reasons.append("invalid_permissions")
        permissions = {}
    if permissions.get("place_orders") is not True:
        reasons.append("place_orders_not_allowed")
    if any(permissions.get(key) is True for key in ("withdraw", "external_transfer", "wallet_sign")):
        reasons.append("unsupported_sensitive_permission")
    limits = auth.get("limits")
    if not isinstance(limits, dict):
        reasons.append("invalid_limits")
        limits = {}
    if set(limits) != set(LIMITS):
        reasons.append("unknown_or_missing_limits")
    for key in LIMITS:
        try:
            value = nonnegative_number(limits.get(key), key)
            if value <= 0 or (key == "max_orders_per_hour" and type(limits[key]) is not int):
                reasons.append("invalid_limit:" + key)
        except ValueError:
            reasons.append("invalid_limit:" + key)
    try:
        if nonnegative_number(limits.get("max_order_usd"), "max_order_usd") > nonnegative_number(limits.get("max_gross_exposure_usd"), "max_gross_exposure_usd"):
            reasons.append("inconsistent_order_exposure_limits")
    except ValueError:
        pass
    kill = auth.get("kill_switch")
    if not isinstance(kill, dict) or kill.get("state") != "RUN" or kill.get("required") is not True:
        reasons.append("kill_switch_not_run")
        kill = {}
    if set(kill) != {"state", "required", "observed_at_utc"}:
        reasons.append("invalid_kill_switch_fields")
    try:
        age = (current - parse_utc(kill.get("observed_at_utc"))).total_seconds()
        if not 0 <= age <= FRESH_SECONDS:
            reasons.append("kill_switch_stale")
    except ValueError:
        reasons.append("kill_switch_unverified")

    if not isinstance(context, dict):
        return False, list(dict.fromkeys([*reasons, "execution_context_required"]))
    try:
        canonical_json(context)
    except ValueError:
        return False, list(dict.fromkeys([*reasons, "invalid_or_secret_execution_context"]))
    if context.get("execution_mode") != "LIVE_AUTHORIZED":
        reasons.append("execution_mode_not_live")
    if context.get("authorization_verified") is not True:
        reasons.append("authorization_not_independently_verified")
    if context.get("authorization_id") != auth.get("authorization_id"):
        reasons.append("authorization_id_mismatch")
    trusted = context.get("trusted_issuers")
    if context.get("issuer_verified") is not True or not isinstance(trusted, list) or any(not isinstance(x, str) for x in trusted) or auth.get("issued_by") not in trusted:
        reasons.append("issuer_unverified")
    if type(context.get("authorization_version")) is not int or context["authorization_version"] != auth.get("authorization_version"):
        reasons.append("authorization_version_mismatch")
    for key in ("strategy_id", "venue", "account_scope"):
        if not isinstance(context.get(key), str) or context[key] != auth.get(key):
            reasons.append("scope_mismatch:" + key)
    for key, allow in (("asset", "allowed_assets"), ("product", "allowed_products")):
        if not isinstance(context.get(key), str) or context[key] not in (auth.get(allow) if isinstance(auth.get(allow), list) else []):
            reasons.append("scope_mismatch:" + key)
    if context.get("action") != "place_orders":
        reasons.append("unsupported_action")
    if not isinstance(context.get("idempotency_key"), str) or not context["idempotency_key"].strip():
        reasons.append("missing_idempotency_key")
    for key in ("risk_gate_passed", "data_fresh", "costs_verified", "liquidity_verified", "account_state_verified", "exposure_includes_order", "reconciliation_healthy", "revocation_checked", "kill_switch_verified"):
        if context.get(key) is not True:
            reasons.append("unverified:" + key)
    if context.get("kill_switch_state") != "RUN":
        reasons.append("runtime_kill_switch_not_run")
    for field in ("account_state_observed_at_utc", "market_data_observed_at_utc", "kill_switch_observed_at_utc"):
        try:
            age = (current - parse_utc(context.get(field))).total_seconds()
            if not 0 <= age <= FRESH_SECONDS:
                reasons.append("stale_context:" + field)
        except ValueError:
            reasons.append("missing_context:" + field)
    if context.get("revoked") is not False:
        reasons.append("revocation_not_clear")
    try:
        age = (current - parse_utc(context.get("revocation_checked_at_utc"))).total_seconds()
        if not 0 <= age <= FRESH_SECONDS:
            reasons.append("revocation_check_stale")
    except ValueError:
        reasons.append("revocation_check_missing")
    for metric, limit in (("order_usd", "max_order_usd"), ("gross_exposure_usd", "max_gross_exposure_usd"), ("daily_loss_usd", "max_daily_loss_usd"), ("orders_this_hour", "max_orders_per_hour")):
        try:
            value = nonnegative_number(context.get(metric), metric)
            ceiling = nonnegative_number(limits.get(limit), limit)
            if metric == "order_usd" and value <= 0:
                reasons.append("invalid_risk_metric:" + metric)
            if metric == "orders_this_hour" and type(context[metric]) is not int:
                reasons.append("invalid_risk_metric:" + metric)
            if value > ceiling or (metric in ("orders_this_hour", "daily_loss_usd") and value >= ceiling):
                reasons.append("risk_limit_exceeded:" + metric)
        except ValueError:
            reasons.append("invalid_risk_metric:" + metric)
    return not reasons, list(dict.fromkeys(reasons))
