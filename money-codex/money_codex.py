"""MONEY Ω · CODEX minimal cloud bootstrap. Standard library only."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
import hashlib, json, uuid

ACCESS = {"ACCESS VERIFIED","ACCESS PARTIAL","ACCESS STALE","ACCESS UNAVAILABLE"}

@dataclass
class Opportunity:
    opportunity_id: str
    provider: str
    type: str
    reward_value_usd: Optional[float] = None
    probability_of_receipt: Optional[float] = None
    gas_usd: float = 0.0
    platform_fees_usd: float = 0.0
    required_spend_usd: float = 0.0
    expected_loss_usd: float = 0.0
    time_cost_usd: float = 0.0
    capital_lockup_cost_usd: float = 0.0
    security_risk_cost_usd: float = 0.0

    def expected_net_value(self):
        if self.reward_value_usd is None or self.probability_of_receipt is None:
            return None
        if not 0 <= self.probability_of_receipt <= 1:
            raise ValueError("probability_of_receipt must be in [0,1]")
        return (
            self.reward_value_usd * self.probability_of_receipt
            - self.gas_usd - self.platform_fees_usd - self.required_spend_usd
            - self.expected_loss_usd - self.time_cost_usd
            - self.capital_lockup_cost_usd - self.security_risk_cost_usd
        )

def validate_live_authorization(auth: dict):
    required=("authorization_id","status","expires_at_utc","strategy_id","venue",
              "allowed_assets","permissions","limits","kill_switch")
    reasons=[f"missing:{k}" for k in required if k not in auth or auth[k] in (None,"")]
    if reasons:
        return False,reasons
    if auth["status"]!="ACTIVE":
        reasons.append("status_not_active")
    try:
        exp=datetime.fromisoformat(auth["expires_at_utc"].replace("Z","+00:00"))
        if exp <= datetime.now(timezone.utc):
            reasons.append("authorization_expired")
    except Exception:
        reasons.append("invalid_expiry")
    if not auth.get("permissions",{}).get("place_orders",False):
        reasons.append("place_orders_not_allowed")
    if auth.get("kill_switch",{}).get("state")!="RUN":
        reasons.append("kill_switch_not_run")
    return not reasons,reasons

def packet(object_type: str, producer: str, payload: dict):
    forbidden={"seed_phrase","private_key","api_secret","password","recovery_phrase",
               "session_token","bearer_token","oauth_refresh_token"}
    def scan(x):
        if isinstance(x,dict):
            for k,v in x.items():
                if k.lower() in forbidden:
                    raise ValueError(f"forbidden secret key:{k}")
                scan(v)
        elif isinstance(x,list):
            for v in x: scan(v)
    scan(payload)
    now=datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
    obj={"schema_version":"2.0","object_id":str(uuid.uuid4()),"object_type":object_type,
         "producer":producer,"created_at_utc":now,"payload":payload}
    raw=json.dumps(obj,sort_keys=True,ensure_ascii=False,separators=(",",":")).encode()
    obj["sha256"]=hashlib.sha256(raw).hexdigest()
    return obj
