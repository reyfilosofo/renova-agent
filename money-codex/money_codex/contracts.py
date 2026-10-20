"""Conservative identity checks, never a conversion of spot bias into contract odds."""
import math
from .models import parse_utc, utc_now

IDENTITY_FIELDS = (
    "asset", "quote_currency", "window_start_utc", "window_end_utc",
    "condition", "option", "tie_rule", "reference", "resolution_source",
    "settlement_method", "price_kind",
)
COST_FIELDS = ("fees", "spread", "slippage", "liquidity")


def _timestamp(value):
    return parse_utc(value)


def _number(value):
    try:
        return type(value) in (int, float) and math.isfinite(value) and value >= 0
    except (OverflowError, ValueError):
        return False


def compare_contracts(left, right, now=None):
    """Return equivalence and descriptive divergence only; never an executable edge."""
    try:
        now = utc_now(now)
    except ValueError:
        return {"classification": "DATA INSUFFICIENT", "equivalent": False,
                "reasons": ["invalid_clock"], "divergence_pp": None}
    if not isinstance(left, dict) or not isinstance(right, dict):
        return {"classification": "DATA INSUFFICIENT", "equivalent": False,
                "reasons": ["contracts_must_be_objects"], "divergence_pp": None}
    missing, identities = [], {}
    for side, row in (("left", left), ("right", right)):
        identity = {}
        for key in IDENTITY_FIELDS:
            value = row.get(key)
            if key in ("window_start_utc", "window_end_utc"):
                try:
                    identity[key] = _timestamp(value)
                except ValueError:
                    missing.append(f"{side}:{key}")
            elif key == "reference":
                if _number(value) and value > 0:
                    identity[key] = value
                else:
                    missing.append(f"{side}:{key}")
            elif isinstance(value, str) and value and value == value.strip() and value.isprintable():
                identity[key] = value
            else:
                missing.append(f"{side}:{key}")
        if ("window_start_utc" in identity and "window_end_utc" in identity
                and identity["window_end_utc"] <= identity["window_start_utc"]):
            missing.append(f"{side}:invalid_window_interval")
        identities[side] = identity
    identity_complete = not missing
    mismatches = [key for key in IDENTITY_FIELDS if key in identities["left"] and key in identities["right"]
                  and identities["left"][key] != identities["right"][key]]
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
        return {"classification": "DATA INSUFFICIENT", "equivalent": identity_complete,
                "reasons": sorted(set(missing)), "divergence_pp": None}
    return {"classification": "WATCH", "equivalent": True,
            "reasons": ["difference_is_descriptive_not_validated_edge"],
            "divergence_pp": round(left["pmarket"] - right["pmarket"], 8)}
