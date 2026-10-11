"""Conservative identity checks, never a conversion of spot bias into contract odds."""
from datetime import datetime, timezone
import math

IDENTITY_FIELDS = (
    "asset", "quote_currency", "window_start_utc", "window_end_utc",
    "condition", "option", "tie_rule", "reference", "resolution_source",
    "settlement_method", "price_kind",
)
COST_FIELDS = ("fees", "spread", "slippage", "liquidity")


def _timestamp(value):
    if not isinstance(value, str):
        raise ValueError("timestamp required")
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("timezone required")
    return result.astimezone(timezone.utc)


def _number(value):
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def compare_contracts(left, right, now=None):
    """Return equivalence and descriptive divergence only; never an executable edge."""
    now = now or datetime.now(timezone.utc)
    if not isinstance(left, dict) or not isinstance(right, dict):
        return {"classification": "DATA INSUFFICIENT", "equivalent": False,
                "reasons": ["contracts_must_be_objects"], "divergence_pp": None}
    missing = [f"{side}:{key}" for side, row in (("left", left), ("right", right))
               for key in IDENTITY_FIELDS if key not in row or row[key] is None or row[key] == ""]
    mismatches = [key for key in IDENTITY_FIELDS if key not in ("window_start_utc", "window_end_utc")
                  and left.get(key) is not None and right.get(key) is not None
                  and left[key] != right[key]]
    for key in ("window_start_utc", "window_end_utc"):
        if key in left and key in right and left[key] and right[key]:
            try:
                if _timestamp(left[key]) != _timestamp(right[key]):
                    mismatches.append(key)
            except (ValueError, TypeError):
                missing.append("invalid:" + key)
    if mismatches:
        return {"classification": "CONTRACT MISMATCH", "equivalent": False,
                "reasons": mismatches, "divergence_pp": None}
    for side, row in (("left", left), ("right", right)):
        try:
            start, end = _timestamp(row.get("window_start_utc")), _timestamp(row.get("window_end_utc"))
            quote, received = _timestamp(row.get("quote_at_utc")), _timestamp(row.get("received_at_utc"))
            if not start <= now < end or not start <= quote <= received <= now:
                missing.append(side + ":window_or_timestamp_invalid")
            if (now - quote).total_seconds() > 30 or (now - received).total_seconds() > 90:
                missing.append(side + ":stale")
        except (ValueError, TypeError, OverflowError):
            missing.append(side + ":source_tick_or_window_missing")
        for field in COST_FIELDS:
            if not _number(row.get(field)) or (field == "liquidity" and row.get(field) == 0):
                missing.append(side + ":" + field)
        if not _number(row.get("pmarket")) or row.get("pmarket", 101) > 100:
            missing.append(side + ":pmarket")
        if row.get("price_kind") != "executable_offer":
            missing.append(side + ":offer_not_executable")
    if missing:
        return {"classification": "DATA INSUFFICIENT", "equivalent": not any(x.split(":")[-1] in IDENTITY_FIELDS for x in missing),
                "reasons": sorted(set(missing)), "divergence_pp": None}
    return {"classification": "WATCH", "equivalent": True,
            "reasons": ["difference_is_descriptive_not_validated_edge"],
            "divergence_pp": round(left["pmarket"] - right["pmarket"], 8)}
