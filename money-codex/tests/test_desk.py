"""Synthetic, explicitly hypothetical fixtures; never actual market packets."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import unittest

from money_codex.desk import ASSETS, STRATEGY_IDS, review_desk, validate_snapshot


class DeskTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 24, 17, 2, tzinfo=timezone.utc)
        self.now_text = "2026-10-24T17:02:00Z"
        self.contract = {
            "asset": "BTC", "contract_id": "synthetic-btc", "venue": "SYNTHETIC_FIXTURE",
            "quote_currency": "USD", "window_start_utc": "2026-10-24T17:00:00Z", "window_end_utc": "2026-10-24T17:05:00Z",
            "condition": "UP_DOWN", "option": "UP", "tie_rule": "UP_ON_EQUAL", "reference": 100,
            "resolution_source": "SYNTHETIC_ORACLE", "settlement_method": "cash", "price_kind": "executable_offer",
            "fees": .01, "spread": .02, "slippage": .01, "liquidity": 1000, "pmarket": 70,
            "costs_unit": "USD_PER_PAPER_ORDER", "liquidity_unit": "USD_NOTIONAL",
            "quote_at_utc": "2026-10-24T17:01:55Z", "received_at_utc": "2026-10-24T17:01:58Z", "geo_status": "ALLOWED",
            "pcontract": .6, "pcontract_methodology_id": "SYNTHETIC_METHOD", "pcontract_verified": True,
            "pcontract_observed_at_utc": self.now_text, "pcontract_valid_until_utc": "2026-10-24T17:05:00Z",
        }
        self.snapshot = {"schema_version": "1.0", "mode": "PAPER", "timeframe": "5m", "observed_at_utc": self.now_text,
                         "assets": [{"asset": asset, "contracts": []} for asset in ASSETS]}
        self.snapshot["assets"][0]["contracts"] = [deepcopy(self.contract)]
        self.policy = {"schema_version": "1.0", "mode": "PAPER", "allowed_assets": list(ASSETS), "allowed_timeframes": ["5m", "15m", "1h"],
                       "max_paper_order_usd": 10, "max_paper_exposure_usd": 100, "max_daily_loss_usd": 20,
                       "paper_order_usd": 5, "paper_exposure_usd": 10, "daily_loss_usd": 0,
                       "metrics_observed_at_utc": self.now_text, "kill_switch": {"state": "RUN", "observed_at_utc": self.now_text},
                       "validated_pcontract_methods": ["SYNTHETIC_METHOD"], "max_house_inventory_usd": 50}

    def review(self, snapshot=None, policy=None, **kwargs):
        return review_desk(snapshot if snapshot is not None else self.snapshot, policy if policy is not None else self.policy, now=self.now, **kwargs)

    def btc(self, report, head=0):
        return report["strategies"][head]["reviews"][0]

    def test_new_strategies_are_deterministic_research_without_authority(self):
        first = self.review()
        self.assertEqual(first, self.review())
        self.assertEqual([row["strategy_id"] for row in first["strategies"]], list(STRATEGY_IDS))
        self.assertFalse(first["approvedForPaper"])
        self.assertFalse(first["executionEnabled"])
        self.assertFalse(first["financialAuthority"])
        self.assertFalse(first["simulationPerformed"])
        self.assertEqual(first["mode"], "PAPER")
        self.assertEqual(self.btc(first)["decision"], "WATCH")
        self.assertNotIn("RENOVA_DESK_V0", STRATEGY_IDS)
        self.assertNotIn("orders", first)

    def test_missing_policy_kill_switch_and_losses_have_absolute_veto(self):
        self.assertEqual(review_desk(self.snapshot, now=self.now)["risk"]["state"], "HALT")
        for change in ({"kill_switch": {"state": "HALT", "observed_at_utc": self.now_text}}, {"daily_loss_usd": 20},
                       {"paper_order_usd": 11}, {"paper_exposure_usd": 96}, {"max_paper_order_usd": True},
                       {"metrics_observed_at_utc": "2026-10-24T17:02:01Z"}, {"max_daily_loss_usd": float("inf")},
                       {"max_paper_exposure_usd": 10**1000}, {"mode": "LIVE"}):
            with self.subTest(change=list(change)):
                report = self.review(policy={**self.policy, **change})
                self.assertEqual(report["risk"]["state"], "HALT")
                self.assertTrue(all(head["decision"] == "HALT" for head in report["strategies"]))

    def test_policy_scope_cannot_be_overridden_by_other_heads(self):
        for change in ({"allowed_assets": ["ETH"]}, {"allowed_timeframes": ["1h"]}):
            report = self.review(policy={**self.policy, **change})
            for head in range(3):
                self.assertEqual(self.btc(report, head)["decision"], "ABSTAIN")
                self.assertIn("asset_or_timeframe_not_allowed", self.btc(report, head)["reasons"])

    def test_requires_six_unique_assets_and_exact_typed_input(self):
        for change in ({"assets": self.snapshot["assets"][:5]}, {"assets": [self.snapshot["assets"][0]]*6}, {"timeframe": []},
                       {"mode": "LIVE"}, {"schema_version": "2.0"}, {"observed_at_utc": "2026-10-24T17:02:01Z"},
                       {"observed_at_utc": "2026-10-24T17:01:29Z"}, {"financialAuthority": True}):
            self.assertEqual(self.review(snapshot={**self.snapshot, **change})["risk"]["state"], "HALT")
        for clock in (None, "2026-10-24", self.now.replace(tzinfo=None)):
            if clock is not None:
                self.assertEqual(review_desk(self.snapshot, self.policy, now=clock)["risk"]["state"], "HALT")

    def test_contract_window_identity_tick_and_costs_fail_closed(self):
        for key, value in (("asset", "ETH"), ("window_end_utc", "2026-10-24T17:15:00Z"), ("quote_at_utc", None),
                           ("received_at_utc", "2026-10-24T17:02:01Z"), ("fees", None), ("spread", True),
                           ("slippage", -1), ("liquidity", 0), ("liquidity", 4), ("geo_status", "UNKNOWN"),
                           ("pmarket", float("nan")), ("reference", [])):
            snapshot = deepcopy(self.snapshot)
            snapshot["assets"][0]["contracts"][0][key] = value
            report = self.review(snapshot)
            with self.subTest(field=key):
                self.assertIn(report["risk"]["state"], ("HALT", "ABSTAIN"))
                self.assertFalse(report["approvedForPaper"])

    def test_unknown_or_unverified_contract_model_never_becomes_a_spot_probability(self):
        for change in ({"pcontract": None}, {"pcontract_verified": False}, {"pcontract_methodology_id": "UNVALIDATED"},
                       {"pcontract": True}, {"pcontract_valid_until_utc": self.now_text}):
            snapshot = deepcopy(self.snapshot)
            snapshot["assets"][0]["contracts"][0].update(change)
            report = self.review(snapshot)
            self.assertEqual(self.btc(report)["decision"], "ABSTAIN")
            self.assertIsNone(report["pcontract"])
            self.assertIsNone(self.btc(report)["contracts"][0]["pcontract"])

    def test_zero_costs_are_distinct_from_unknown_costs(self):
        snapshot = deepcopy(self.snapshot)
        snapshot["assets"][0]["contracts"][0].update(fees=0,spread=0,slippage=0)
        self.assertEqual(self.btc(self.review(snapshot))["decision"], "WATCH")

    def test_unknown_units_and_costs_over_limits_veto_even_if_bare_order_fits(self):
        for change in ({"costs_unit":None},{"liquidity_unit":"CONTRACTS"},{"fees":6}, {"fees":1e308,"spread":1e308,"slippage":1e308}):
            snapshot=deepcopy(self.snapshot);snapshot["assets"][0]["contracts"][0].update(change)
            report=self.review(snapshot)
            self.assertEqual(self.btc(report)["decision"],"ABSTAIN")
        report=self.review(policy={**self.policy,"paper_exposure_usd":94.99})
        self.assertIn("paper_exposure_including_costs_exceeds_limit",self.btc(report)["reasons"])

    def test_spot_only_collector_is_descriptive_not_contract_or_live_evidence(self):
        snapshot = deepcopy(self.snapshot)
        snapshot["assets"][0]["contracts"] = []
        snapshot["assets"][0]["spot_observation"] = {"asset": "BTC", "product": "BTC-USD", "source": "COINBASE_EXCHANGE", "quote_currency": "USD",
            "last_trade_price": 100, "bid": 99, "ask": 101, "last_trade_at_utc": self.now_text, "received_at_utc": self.now_text,
            "status": "OBSERVED", "bid_ask_timestamp_verified": False}
        report = self.review(snapshot)
        self.assertEqual(self.btc(report)["research"]["published_spread_bps"], 200)
        self.assertFalse(self.btc(report)["research"]["sourceTickVerified"])
        self.assertEqual(self.btc(report)["decision"], "ABSTAIN")
        self.assertIsNone(report["pcontract"])

    def test_experimental_spot_bias_requires_its_own_current_window_and_does_not_authorize(self):
        snapshot = deepcopy(self.snapshot)
        snapshot["assets"][0]["contracts"] = []
        snapshot["assets"][0]["spot_research"] = {"strategy_id": "MONEY_FIXED_WINDOW_ANALOG_PAPER_V1", "pspot_experimental": .9,
            "observed_at_utc": self.now_text, "valid_until_utc": "2026-10-24T17:05:00Z", "calibrated": False, "pcontract": None,
            "window_start_utc": "2026-10-24T17:00:00Z", "window_end_utc": "2026-10-24T17:05:00Z"}
        report = self.review(snapshot)
        self.assertEqual(self.btc(report)["research"]["direction"], "UP_BIAS_EXPERIMENTAL")
        self.assertEqual(self.btc(report)["decision"], "ABSTAIN")
        snapshot["assets"][0]["spot_research"]["window_end_utc"] = "2026-10-24T18:00:00Z"
        self.assertIsNone(self.btc(self.review(snapshot))["research"]["pspot_experimental"])

    def test_house_requires_its_own_book_and_inventory_and_cannot_inherit_gambler_watch(self):
        self.assertEqual(self.btc(self.review(), 1)["decision"], "ABSTAIN")
        snapshot = deepcopy(self.snapshot)
        snapshot["assets"][0]["house"] = {"bid": .68, "ask": .7, "bid_depth_usd": 100, "ask_depth_usd": 100,
            "inventory_usd": 0, "observed_at_utc": self.now_text, "inventory_observed_at_utc": self.now_text,
            "contract_id": "synthetic-btc", "venue": "SYNTHETIC_FIXTURE"}
        self.assertEqual(self.btc(self.review(snapshot), 1)["decision"], "WATCH")
        for change in ({"inventory_usd": 49}, {"bid": .8}, {"inventory_observed_at_utc": "2026-10-24T17:01:00Z"}, {"contract_id": "other"}):
            mutated = deepcopy(snapshot); mutated["assets"][0]["house"].update(change)
            self.assertEqual(self.btc(self.review(mutated), 1)["decision"], "ABSTAIN")

    def test_spy_requires_allowlisted_public_evidence_never_blind_copy(self):
        self.assertEqual(self.btc(self.review(), 2)["decision"], "ABSTAIN")
        snapshot = deepcopy(self.snapshot)
        snapshot["assets"][0]["spy"] = {"chain": "ethereum", "public_address": "0x"+"1"*40, "source_url": "https://etherscan.io/address/0x"+"1"*40,
            "evidence_sha256": "a"*64, "observed_at_utc": self.now_text, "chain_verified": True, "address_verified": True, "risk_review_verified": True}
        report = self.review(snapshot, policy={**self.policy,"spy_evidence_hashes":["a"*64]})
        self.assertEqual(self.btc(report, 2)["decision"], "WATCH")
        self.assertFalse(self.btc(report, 2)["blindCopyAllowed"])
        self.assertNotIn("public_address", str(report))
        snapshot["assets"][0]["spy"]["chain"] = []
        self.assertEqual(self.btc(self.review(snapshot), 2)["decision"], "ABSTAIN")

    def test_judgments_preserve_independence_and_are_not_contract_probabilities(self):
        base = {"judgment_id": "synthetic-one", "source": "JEV", "asset": "BTC", "timeframe": "5m", "kind": "RESEARCH_SCORE", "value": .8,
                "observed_at_utc": self.now_text, "expires_at_utc": "2026-10-24T17:05:00Z", "source_url": "https://docs.typesafe.ai/"}
        judgments = [base,{**base,"judgment_id":"synthetic-two","source":"GROK","value":.2}]
        report = self.review(judgments=judgments)
        self.assertEqual([row["value"] for row in report["judgments"]], [.8,.2])
        self.assertEqual(report["modelAggregation"], "NONE")
        self.assertIsNone(report["pcontract"])
        self.assertTrue(all(row["sourceAuthenticated"] is False and row["usedAsPcontract"] is False for row in report["judgments"]))
        for change in ({"value": True}, {"value": 2}, {"asset":"OTHER"}, {"source_url":"https://127.0.0.1/"}, {"expires_at_utc":self.now_text}):
            self.assertEqual(self.review(judgments=[{**base,**change}])["risk"]["state"], "HALT")

    def test_recognizable_secret_keys_and_values_never_enter_results(self):
        for secret in ({"api_key":"PRIVATE_SENTINEL"},{"note":"Bearer PRIVATE_SENTINEL_VALUE"}):
            snapshot = {**self.snapshot, **secret}
            report = self.review(snapshot)
            self.assertEqual(report["risk"]["state"], "HALT")
            self.assertNotIn("PRIVATE_SENTINEL", str(report))
        self.assertEqual(self.review(policy={**self.policy,"password":"PRIVATE_SENTINEL"})["risk"]["state"], "HALT")

    def test_no_input_mutation_and_horizon_rollover_invalidates_old_contracts(self):
        original = deepcopy(self.snapshot)
        self.review()
        self.assertEqual(self.snapshot, original)
        shifted = deepcopy(self.snapshot); shifted["timeframe"] = "15m"
        self.assertIn("exact_contract_window_mismatch", self.btc(self.review(shifted))["reasons"])
        later = self.now + timedelta(minutes=3)
        self.assertEqual(review_desk(self.snapshot, self.policy, now=later)["risk"]["state"], "HALT")


if __name__ == "__main__":
    unittest.main()
