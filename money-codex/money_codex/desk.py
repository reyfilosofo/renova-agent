"""MONEY Ω PAPER desk v1.0, 2026-10-24. Source: MONEY market/bridge rules.

Deterministic research reviews only. This module has no I/O, fills, orders,
authorization issuance or execution adapters. A WATCH is not paper approval.
Caller-supplied judgments remain attributed reports, never authenticated facts.
"""
from __future__ import annotations

from datetime import datetime, timedelta
import hashlib
import math
import re

from .contracts import IDENTITY_FIELDS, COST_FIELDS, compare_contracts
from .models import _https_url, nonnegative_number, parse_utc, utc_now
from .packets import canonical_json

ASSETS = ("BTC", "ETH", "SOL", "DOGE", "XRP", "BNB")
TIMEFRAMES = {"5m": 5, "15m": 15, "1h": 60}
STRATEGY_IDS = ("MONEY_GAMBLER_PAPER_V1", "MONEY_HOUSE_PAPER_V1", "MONEY_SPY_PAPER_V1")
SNAPSHOT_FIELDS = {"schema_version", "mode", "timeframe", "observed_at_utc", "assets"}
ROW_FIELDS = {"asset", "contracts", "spot_observation", "spot_research", "house", "spy"}
CONTRACT_FIELDS = set(IDENTITY_FIELDS) | set(COST_FIELDS) | {
    "contract_id", "venue", "quote_at_utc", "received_at_utc", "pmarket", "geo_status",
    "costs_unit", "liquidity_unit",
    "pcontract", "pcontract_methodology_id", "pcontract_verified", "pcontract_observed_at_utc", "pcontract_valid_until_utc"}
POLICY_REQUIRED = {"schema_version", "mode", "allowed_assets", "allowed_timeframes", "max_paper_order_usd",
                   "max_paper_exposure_usd", "max_daily_loss_usd", "paper_order_usd", "paper_exposure_usd",
                   "daily_loss_usd", "metrics_observed_at_utc", "kill_switch"}
POLICY_OPTIONAL = {"max_house_inventory_usd", "validated_pcontract_methods", "spy_evidence_hashes"}
JUDGMENT_FIELDS = {"judgment_id", "source", "asset", "timeframe", "kind", "value", "observed_at_utc", "expires_at_utc", "source_url"}


class DeskInputError(ValueError):
    """A bounded error code, never submitted content."""


def _fail(code):
    raise DeskInputError(code)


def _object(value, allowed, required=()):
    if not isinstance(value, dict) or set(value) - set(allowed) or set(required) - set(value):
        _fail("invalid_object_fields")


def _identifier(value):
    return isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,119}", value) is not None


def _number(value, positive=False):
    try:
        number = nonnegative_number(value, "desk")
        return number if not positive or number > 0 else None
    except ValueError:
        return None


def _fresh(value, now, seconds=30):
    try:
        return 0 <= (now - parse_utc(value)).total_seconds() <= seconds
    except (ValueError, OverflowError):
        return False


def _iso(value):
    return value.isoformat().replace("+00:00", "Z")


def _window(now, timeframe):
    minutes = TIMEFRAMES[timeframe]
    start = now.replace(minute=(now.minute // minutes) * minutes, second=0, microsecond=0)
    return start, start + timedelta(minutes=minutes)


def _strict_json(value):
    if len(canonical_json(value)) > 262144:
        _fail("desk_input_too_large")


def validate_snapshot(snapshot, now=None):
    """Validate normalized v1 input; values are observations, not source trust."""
    current = utc_now(now)
    _strict_json(snapshot)
    _object(snapshot, SNAPSHOT_FIELDS, SNAPSHOT_FIELDS)
    if snapshot["schema_version"] != "1.0" or snapshot["mode"] != "PAPER":
        _fail("unsupported_snapshot_mode_or_version")
    if not isinstance(snapshot["timeframe"], str) or snapshot["timeframe"] not in TIMEFRAMES:
        _fail("unsupported_timeframe")
    if not _fresh(snapshot["observed_at_utc"], current):
        _fail("snapshot_stale_or_future")
    rows = snapshot["assets"]
    if not isinstance(rows, list) or len(rows) != len(ASSETS):
        _fail("six_unique_assets_required")
    seen = set()
    for row in rows:
        _object(row, ROW_FIELDS, {"asset", "contracts"})
        asset = row["asset"]
        if not isinstance(asset, str) or asset not in ASSETS or asset in seen:
            _fail("six_unique_assets_required")
        seen.add(asset)
        if not isinstance(row["contracts"], list) or len(row["contracts"]) > 12:
            _fail("invalid_contract_list")
        ids = set()
        for contract in row["contracts"]:
            _object(contract, CONTRACT_FIELDS)
            if not _identifier(contract.get("contract_id")) or not _identifier(contract.get("venue")):
                _fail("invalid_contract_identity")
            key = (contract["venue"], contract["contract_id"])
            if key in ids:
                _fail("duplicate_contract")
            ids.add(key)
    return snapshot


def validate_judgments(judgments, snapshot, now=None):
    """Validate attributed numeric reports without promoting them to Pcontract.

    RESEARCH_SCORE includes external Jev assessments. Its number is not a
    contractual probability. REPORTED_* kinds keep their own meaning/units.
    """
    current = utc_now(now)
    if judgments is None:
        return []
    _strict_json(judgments)
    if not isinstance(judgments, list) or len(judgments) > 24:
        _fail("invalid_judgment_list")
    seen, result = set(), []
    for item in judgments:
        _object(item, JUDGMENT_FIELDS, JUDGMENT_FIELDS)
        if not _identifier(item["judgment_id"]) or item["judgment_id"] in seen or not _identifier(item["source"]):
            _fail("invalid_judgment_identity")
        seen.add(item["judgment_id"])
        if not isinstance(item["asset"], str) or item["asset"] not in ASSETS or item["timeframe"] != snapshot["timeframe"]:
            _fail("judgment_scope_mismatch")
        if not isinstance(item["kind"], str) or item["kind"] not in {"RESEARCH_SCORE", "REPORTED_PSPOT", "REPORTED_PCONTRACT", "REPORTED_PMARKET"}:
            _fail("invalid_judgment_kind")
        value = _number(item["value"])
        ceiling = 100 if item["kind"] == "REPORTED_PMARKET" else 1
        if value is None or value > ceiling:
            _fail("invalid_judgment_value")
        if not _fresh(item["observed_at_utc"], current) or not _https_url(item["source_url"]):
            _fail("judgment_stale_or_source_invalid")
        expiry = parse_utc(item["expires_at_utc"])
        if not current < expiry <= current + timedelta(hours=1):
            _fail("judgment_expired_or_invalid_ttl")
        result.append({**item, "sourceAuthenticated": False, "usedAsPcontract": False})
    return result


def _policy_vetoes(policy, now):
    if policy is None:
        return ["policy_missing"]
    try:
        _strict_json(policy)
        _object(policy, POLICY_REQUIRED | POLICY_OPTIONAL, POLICY_REQUIRED)
    except ValueError:
        return ["policy_invalid_or_secret"]
    reasons = []
    if policy["schema_version"] != "1.0" or policy["mode"] != "PAPER":
        reasons.append("policy_mode_or_version_invalid")
    for key, allowed in (("allowed_assets", ASSETS), ("allowed_timeframes", TIMEFRAMES)):
        values = policy[key]
        if not isinstance(values, list) or not values or any(not isinstance(x, str) or x not in allowed for x in values) or len(set(x for x in values if isinstance(x, str))) != len(values):
            reasons.append("policy_scope_invalid:" + key)
    metrics = {}
    for key in ("max_paper_order_usd", "max_paper_exposure_usd", "max_daily_loss_usd", "paper_order_usd", "paper_exposure_usd", "daily_loss_usd"):
        value = _number(policy[key], key.startswith("max_") or key == "paper_order_usd")
        if value is None:
            reasons.append("policy_metric_invalid:" + key)
        else:
            metrics[key] = value
    if not _fresh(policy["metrics_observed_at_utc"], now):
        reasons.append("policy_metrics_stale_or_future")
    kill = policy["kill_switch"]
    if not isinstance(kill, dict) or set(kill) != {"state", "observed_at_utc"} or kill.get("state") != "RUN" or not _fresh(kill.get("observed_at_utc"), now):
        reasons.append("kill_switch_not_verified_run")
    if len(metrics) == 6:
        order, exposure = metrics["paper_order_usd"], metrics["paper_exposure_usd"]
        if order > metrics["max_paper_order_usd"]:
            reasons.append("max_paper_order_exceeded")
        if not math.isfinite(order + exposure) or order + exposure > metrics["max_paper_exposure_usd"]:
            reasons.append("max_paper_exposure_exceeded")
        if metrics["daily_loss_usd"] >= metrics["max_daily_loss_usd"]:
            reasons.append("max_daily_loss_reached")
        if metrics["max_paper_order_usd"] > metrics["max_paper_exposure_usd"]:
            reasons.append("inconsistent_paper_limits")
    for key in ("validated_pcontract_methods", "spy_evidence_hashes"):
        if key in policy and (not isinstance(policy[key], list) or len(policy[key]) > 32 or any(not _identifier(x) for x in policy[key])):
            reasons.append("policy_allowlist_invalid:" + key)
    return sorted(set(reasons))


def _spot_review(row, now, timeframe):
    result = {"published_spread_bps": None, "sourceTickVerified": False, "direction": "UNDETERMINED", "pspot_experimental": None}
    observation = row.get("spot_observation")
    if isinstance(observation, dict):
        allowed = {"asset", "product", "source", "quote_currency", "last_trade_price", "bid", "ask", "last_trade_at_utc", "received_at_utc", "status", "bid_ask_timestamp_verified"}
        if (not set(observation) - allowed and observation.get("asset") == row["asset"] and observation.get("quote_currency") == "USD"
                and observation.get("status") == "OBSERVED" and _fresh(observation.get("received_at_utc"), now, 90)):
            bid, ask = _number(observation.get("bid"), True), _number(observation.get("ask"), True)
            if bid is not None and ask is not None and bid <= ask:
                # Divide before adding to avoid overflowing finite large quotes.
                midpoint = bid / 2 + ask / 2
                spread = ((ask - bid) / midpoint) * 10000
                if math.isfinite(spread):
                    result["published_spread_bps"] = round(spread, 8)
            # A last-trade timestamp is not the timestamp of a bid/ask quote.
    research = row.get("spot_research")
    if isinstance(research, dict) and set(research) == {"strategy_id", "pspot_experimental", "observed_at_utc", "valid_until_utc", "calibrated", "pcontract", "window_start_utc", "window_end_utc"}:
        value = _number(research["pspot_experimental"])
        try:
            valid = (research["strategy_id"] == "MONEY_FIXED_WINDOW_ANALOG_PAPER_V1" and research["calibrated"] is False and research["pcontract"] is None
                     and value is not None and value <= 1 and _fresh(research["observed_at_utc"], now)
                     and parse_utc(research["window_start_utc"]) == _window(now, timeframe)[0]
                     and parse_utc(research["window_end_utc"]) == _window(now, timeframe)[1]
                     and now < parse_utc(research["valid_until_utc"]) <= _window(now, timeframe)[1])
        except ValueError:
            valid = False
        if valid:
            result["pspot_experimental"] = value
            result["direction"] = "UP_BIAS_EXPERIMENTAL" if value > .5 else "DOWN_BIAS_EXPERIMENTAL" if value < .5 else "NEUTRAL_EXPERIMENTAL"
    return result


def _contract_review(contract, asset, timeframe, policy, now):
    reasons = []
    comparison = compare_contracts(contract, contract, now)
    if comparison["classification"] != "WATCH":
        reasons.extend(comparison["reasons"])
    if contract.get("asset") != asset:
        reasons.append("asset_contract_mismatch")
    start, end = _window(now, timeframe)
    try:
        if parse_utc(contract.get("window_start_utc")) != start or parse_utc(contract.get("window_end_utc")) != end:
            reasons.append("exact_contract_window_mismatch")
    except ValueError:
        reasons.append("exact_contract_window_missing")
    if contract.get("geo_status") != "ALLOWED":
        reasons.append("geography_unverified_or_restricted")
    pcontract = _number(contract.get("pcontract"))
    if pcontract is None:
        reasons.append("pcontract_unknown")
    elif (pcontract > 1 or contract.get("pcontract_verified") is not True
          or not _identifier(contract.get("pcontract_methodology_id"))
          or contract.get("pcontract_methodology_id") not in policy.get("validated_pcontract_methods", [])
          or not _fresh(contract.get("pcontract_observed_at_utc"), now)):
        reasons.append("pcontract_methodology_unverified")
    else:
        try:
            if not now < parse_utc(contract.get("pcontract_valid_until_utc")) <= end:
                reasons.append("pcontract_expired_or_wrong_window")
        except ValueError:
            reasons.append("pcontract_expiry_missing")
    liquidity = _number(contract.get("liquidity"))
    if contract.get("liquidity_unit") != "USD_NOTIONAL":
        reasons.append("liquidity_units_unverified")
    if liquidity is None or liquidity < policy.get("paper_order_usd", math.inf):
        reasons.append("liquidity_below_paper_request_or_unknown")
    costs = {key: _number(contract.get(key)) for key in ("fees", "spread", "slippage")}
    total_cost = None
    if contract.get("costs_unit") != "USD_PER_PAPER_ORDER":
        reasons.append("cost_units_unverified")
    elif all(value is not None for value in costs.values()):
        try:
            total_cost = math.fsum(costs.values())
        except OverflowError:
            reasons.append("total_cost_nonfinite")
        if total_cost is not None:
            total_spend = policy["paper_order_usd"] + total_cost
            if not math.isfinite(total_spend) or total_spend > policy["max_paper_order_usd"]:
                reasons.append("paper_order_plus_costs_exceeds_limit")
            if not math.isfinite(total_spend + policy["paper_exposure_usd"]) or total_spend + policy["paper_exposure_usd"] > policy["max_paper_exposure_usd"]:
                reasons.append("paper_exposure_including_costs_exceeds_limit")
    market = _number(contract.get("pmarket"))
    return {"contract_id": contract["contract_id"], "venue": contract["venue"], "pmarket_percent": market if market is not None and market <= 100 else None,
            "pcontract": pcontract if not reasons else None, "reported_costs": costs, "total_cost_usd": total_cost,
            "liquidity_usd": liquidity if contract.get("liquidity_unit") == "USD_NOTIONAL" else None,
            "reasons": sorted(set(reasons)), "classification": "DATA INSUFFICIENT" if reasons else "WATCH"}


def _house_reasons(row, selected, policy, now):
    data = row.get("house")
    fields = {"bid", "ask", "bid_depth_usd", "ask_depth_usd", "inventory_usd", "observed_at_utc", "inventory_observed_at_utc", "contract_id", "venue"}
    if not isinstance(data, dict) or set(data) != fields:
        return ["house_order_book_and_inventory_missing"]
    reasons = []
    if data["contract_id"] != selected["contract_id"] or data["venue"] != selected["venue"]:
        reasons.append("house_contract_identity_mismatch")
    bid, ask = _number(data["bid"]), _number(data["ask"])
    if bid is None or ask is None or not 0 <= bid < ask <= 1:
        reasons.append("house_two_sided_book_invalid")
    elif abs(ask * 100 - selected["pmarket_percent"]) > 1e-8:
        reasons.append("house_book_offer_mismatch")
    for key in ("bid_depth_usd", "ask_depth_usd"):
        depth = _number(data[key])
        if depth is None or depth < policy["paper_order_usd"]:
            reasons.append("house_depth_insufficient:" + key)
    inventory, limit = _number(data["inventory_usd"]), _number(policy.get("max_house_inventory_usd"), True)
    if inventory is None or limit is None or not math.isfinite(inventory + policy["paper_order_usd"]) or inventory + policy["paper_order_usd"] > limit:
        reasons.append("house_inventory_limit_unverified_or_exceeded")
    if not _fresh(data["observed_at_utc"], now) or not _fresh(data["inventory_observed_at_utc"], now):
        reasons.append("house_book_or_inventory_stale")
    return reasons


def _spy_reasons(row, policy, now):
    data = row.get("spy")
    fields = {"chain", "public_address", "source_url", "evidence_sha256", "observed_at_utc", "chain_verified", "address_verified", "risk_review_verified"}
    if not isinstance(data, dict) or set(data) != fields:
        return ["spy_public_chain_address_and_risk_evidence_missing"]
    chain, address = data["chain"], data["public_address"]
    evm = isinstance(chain, str) and chain in {"ethereum", "base", "arbitrum", "polygon", "bsc"} and isinstance(address, str) and re.fullmatch(r"0x[0-9a-fA-F]{40}", address)
    solana = chain == "solana" and isinstance(address, str) and re.fullmatch(r"[1-9A-HJ-NP-Za-km-z]{32,44}", address)
    evidence = data["evidence_sha256"]
    if (not (evm or solana) or any(data[key] is not True for key in ("chain_verified", "address_verified", "risk_review_verified"))
            or not _https_url(data["source_url"]) or not isinstance(evidence, str) or not re.fullmatch(r"[0-9a-f]{64}", evidence)
            or evidence not in policy.get("spy_evidence_hashes", []) or not _fresh(data["observed_at_utc"], now)):
        return ["spy_evidence_unverified_stale_or_not_allowlisted"]
    return []


def review_desk(snapshot: dict, policy: dict | None = None, *, judgments: list[dict] | None = None, now: datetime | None = None) -> dict:
    """Review three research heads. Risk vetoes cannot be overridden by a head."""
    output = {"schema_version": "1.0", "system": "MONEY Ω", "mode": "PAPER", "generated_at_utc": None,
              "strategies": [], "risk": {"name": "RISK Ω", "state": "HALT", "vetoes": []}, "judgments": [],
              "approvedForPaper": False, "executionEnabled": False, "financialAuthority": False,
              "simulationPerformed": False, "modelAggregation": "NONE", "pcontract": None}
    try:
        current = utc_now(now)
        output["generated_at_utc"] = _iso(current)
        validate_snapshot(snapshot, current)
        _window(current, snapshot["timeframe"])
        output["judgments"] = validate_judgments(judgments, snapshot, current)
    except (ValueError, TypeError, OverflowError):
        output["risk"]["vetoes"] = ["invalid_snapshot_clock_or_judgments"]
        for strategy in STRATEGY_IDS:
            output["strategies"].append({"strategy_id": strategy, "mode": "PAPER", "decision": "HALT", "classification": "DATA INSUFFICIENT", "approvedForPaper": False, "reviews": []})
        return output
    vetoes = _policy_vetoes(policy, current)
    output["scope"] = {"assets": list(ASSETS), "timeframe": snapshot["timeframe"], "window_start_utc": _iso(_window(current, snapshot["timeframe"])[0]), "window_end_utc": _iso(_window(current, snapshot["timeframe"])[1])}
    output["input_sha256"] = hashlib.sha256(canonical_json(snapshot)).hexdigest()
    output["risk"]["vetoes"] = vetoes
    valid_policy = policy if not vetoes else {}
    all_contract_reasons = set()
    for strategy in STRATEGY_IDS:
        reviews = []
        for asset in ASSETS:
            row = next(item for item in snapshot["assets"] if item["asset"] == asset)
            reasons = list(vetoes)
            contracts = []
            if not vetoes:
                if asset not in valid_policy["allowed_assets"] or snapshot["timeframe"] not in valid_policy["allowed_timeframes"]:
                    reasons.append("asset_or_timeframe_not_allowed")
                contracts = [_contract_review(item, asset, snapshot["timeframe"], valid_policy, current) for item in row["contracts"]]
            selected = next((item for item in contracts if not item["reasons"]), None)
            if not row["contracts"]:
                reasons.append("contract_evidence_missing")
            elif not vetoes and selected is None:
                reasons.extend(reason for item in contracts for reason in item["reasons"])
            if not vetoes and strategy == STRATEGY_IDS[1]:
                reasons.extend(_house_reasons(row, selected, valid_policy, current) if selected else ["house_contract_not_validated"])
            if not vetoes and strategy == STRATEGY_IDS[2]:
                reasons.extend(_spy_reasons(row, valid_policy, current))
            spot = _spot_review(row, current, snapshot["timeframe"])
            reasons = sorted(set(reasons))
            all_contract_reasons.update(reasons)
            reviews.append({"asset": asset, "decision": "HALT" if vetoes else "ABSTAIN" if reasons else "WATCH", "classification": "DATA INSUFFICIENT" if reasons else "WATCH",
                            "reasons": reasons, "research": spot, "contracts": contracts, "approvedForPaper": False,
                            "blindCopyAllowed": False, "financialAuthority": False})
        head_watch = any(item["decision"] == "WATCH" for item in reviews)
        output["strategies"].append({"strategy_id": strategy, "mode": "PAPER", "decision": "HALT" if vetoes else "WATCH" if head_watch else "ABSTAIN",
                                     "classification": "WATCH" if head_watch else "DATA INSUFFICIENT", "approvedForPaper": False, "reviews": reviews})
    output["risk"]["state"] = "HALT" if vetoes else "WATCH" if any(item["decision"] == "WATCH" for item in output["strategies"]) else "ABSTAIN"
    output["risk"]["assetVetoes"] = sorted(all_contract_reasons)
    # Different scores may answer different questions/contracts. Their numerical
    # difference alone cannot establish material model disagreement.
    output["modelDisagreement"] = None
    output["modelDisagreementAssessment"] = "REQUIRES_SEPARATE_SCOPE_AND_METHODOLOGY_REVIEW"
    return output


review_paper_desk = review_desk
