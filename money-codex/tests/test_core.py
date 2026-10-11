"""Arithmetic and discovery behavior; no accounts or financial adapters."""
import unittest
from datetime import datetime, timezone, timedelta
from money_codex.models import Opportunity, COST_FIELDS, EV_FIELDS, evaluate_opportunity, expected_net_reward
from money_codex.authorization import validate_live_authorization
from money_codex.packets import envelope, verify_envelope

NOW = datetime(2026, 10, 11, 12, tzinfo=timezone.utc)

def opportunity():
    return {'opportunity_id': 'test-only', 'provider': 'Official test publisher', 'type': 'BOUNTY',
            'official_url': 'https://example.org/bounty',
            'source_evidence': {'url': 'https://example.org/bounty', 'observed_at': NOW.isoformat(), 'http_status': 200, 'content_sha256': 'a' * 64},
            'evidence': ['Observed test terms'], 'last_verified_at_utc': NOW.isoformat(),
            'expected_gross_reward_usd': 10, 'reward_probability': .5,
            **{k: 0 for k in COST_FIELDS}, 'time_cost_usd': 2, 'security_risk_cost_usd': 1,
            'deadline_utc': (NOW + timedelta(hours=1)).isoformat(),
            'eligibility_status': 'VERIFIED', 'eligibility_basis': 'Synthetic test evidence, not a real identity',
            'tos_status': 'VERIFIED', 'security_risk': 'LOW', 'geography': 'Test jurisdiction',
            'kyc_requirements': 'Not applicable in fixture', 'wallet_network': 'Not applicable',
            'required_capital_usd': 0, 'required_actions': ['Review fixture'], 'irreversible_actions': [],
            'time_cost_minutes': 5, 'repeatability': 'ONE_TIME', 'invalidation': 'Fixture expires'}

class MoneyCodexTests(unittest.TestCase):
    def test_opportunity_ev_known_explicit_costs(self):
        op = Opportunity('x', 'p', 'QUEST', 10, .5, **{k: 0 for k in COST_FIELDS if k not in ('time_cost_usd', 'security_risk_cost_usd')}, time_cost_usd=2, security_risk_cost_usd=1)
        self.assertEqual(op.expected_net_value(), 2)

    def test_unknown_costs_are_never_zero(self):
        op = Opportunity('x', 'p', 'QUEST', 10, .5, time_cost_usd=2, security_risk_cost_usd=1)
        self.assertIsNone(op.expected_net_value())
        for field in EV_FIELDS:
            item = opportunity()
            item[field] = None
            with self.subTest(field=field):
                result = evaluate_opportunity(item, NOW)
                self.assertIsNone(result['expected_net_reward_usd'])
                self.assertEqual(result['ev_status'], 'DATA INSUFFICIENT')
                self.assertEqual(result['classification'], 'WATCH')
                self.assertIn(field, result['missing_data'])

    def test_verified_positive_opportunity_is_review_queue_only(self):
        result = evaluate_opportunity(opportunity(), NOW)
        self.assertEqual(result['classification'], 'QUEUE')
        self.assertEqual(result['expected_net_reward_usd'], 2)
        self.assertFalse(result['execution_authority'])
        self.assertFalse(result['execution_allowed'])

    def test_program_discovery_is_never_paid_assignment(self):
        data = {**opportunity(), 'type': 'PROGRAM_DISCOVERY', 'classification': 'DO NOW', 'execution_allowed': True}
        result = evaluate_opportunity(data, NOW)
        self.assertEqual(result['classification'], 'WATCH')
        self.assertTrue(result['discovery_only'])
        self.assertFalse(result['execution_allowed'])

    def test_expiry_revalidated_on_read_without_mutation(self):
        data = opportunity()
        result = evaluate_opportunity(data, NOW + timedelta(hours=2))
        self.assertEqual(result['classification'], 'SKIP')
        self.assertNotIn('evaluated_at_utc', data)

    def test_missing_or_wrong_source_not_eligible(self):
        for mutate in ('digest', 'wrong_url', 'http_error', 'stale', 'future'):
            data = opportunity()
            if mutate == 'digest': data['source_evidence']['content_sha256'] = ''
            if mutate == 'wrong_url': data['source_evidence']['url'] = 'https://example.org/unrelated'
            if mutate == 'http_error': data['source_evidence']['http_status'] = 403
            if mutate == 'stale': data['last_verified_at_utc'] = (NOW - timedelta(days=2)).isoformat()
            if mutate == 'future': data['source_evidence']['observed_at'] = (NOW + timedelta(seconds=1)).isoformat()
            with self.subTest(mutate=mutate):
                self.assertEqual(evaluate_opportunity(data, NOW)['classification'], 'DATA INSUFFICIENT')

    def test_risk_negative_and_ineligible_skip(self):
        for changes in ({'time_cost_usd': 50}, {'eligibility_status': 'INELIGIBLE'}, {'tos_status': 'CONFLICT'}, {'security_risk': 'HIGH'}):
            self.assertEqual(evaluate_opportunity({**opportunity(), **changes}, NOW)['classification'], 'SKIP')

    def test_invalid_probability_and_nonfinite_bool_cost_rejected(self):
        for field, value in [('reward_probability', 1.1), ('gas_usd', float('nan')), ('fees_usd', float('inf')), ('time_cost_usd', True), ('required_spend_usd', -1), ('expected_loss_usd', '0')]:
            data = {**opportunity(), field: value}
            with self.subTest(field=field, value=value):
                with self.assertRaises(ValueError): expected_net_reward(data)
                result = evaluate_opportunity(data, NOW)
                self.assertIsNone(result['expected_net_reward_usd'])
                self.assertEqual(result['classification'], 'DATA INSUFFICIENT')

    def test_legacy_aliases_are_explicit_and_conflicts_rejected(self):
        self.assertIsNone(Opportunity('x', 'p', 'QUEST', reward_value_usd=10, probability_of_receipt=.5).expected_net_value())
        with self.assertRaises(ValueError): Opportunity('x', 'p', 'QUEST', expected_gross_reward_usd=10, reward_value_usd=20)
        with self.assertRaises(TypeError): Opportunity('x', 'p', 'QUEST', invented_cost=0)

    def test_naive_clock_and_version_mismatch_rejected(self):
        with self.assertRaises(ValueError): evaluate_opportunity(opportunity(), NOW.replace(tzinfo=None))
        with self.assertRaises(ValueError): evaluate_opportunity({**opportunity(), 'schema_version': '1.0'}, NOW)

    def test_malformed_type_flags_and_overflow_never_yield_queue(self):
        for changes in ({'type':[]}, {'discovery_only':'false'}, {'required_capital_usd': True}, {'irreversible_actions': False}):
            with self.subTest(changes=changes):
                self.assertEqual(evaluate_opportunity({**opportunity(), **changes}, NOW)['classification'], 'DATA INSUFFICIENT')
        data = opportunity()
        data.update({field: 1e308 for field in COST_FIELDS})
        with self.assertRaises(ValueError): expected_net_reward(data)
        self.assertIsNone(evaluate_opportunity(data, NOW)['expected_net_reward_usd'])

    def test_draft_auth_and_old_weak_active_rejected(self):
        self.assertFalse(validate_live_authorization({'status': 'DRAFT'}, NOW)[0])
        auth = {'authorization_id': 'A1', 'status': 'ACTIVE', 'issued_at_utc': NOW.isoformat(),
                'expires_at_utc': (NOW + timedelta(hours=1)).isoformat(), 'strategy_id': 'S1', 'venue': 'TEST',
                'allowed_assets': ['BTC'], 'permissions': {'place_orders': True}, 'limits': {'max_order_usd': 10},
                'kill_switch': {'state': 'RUN'}}
        ok, reasons = validate_live_authorization(auth, NOW)
        self.assertFalse(ok)
        self.assertIn('execution_context_required', reasons)

    def test_packet_hash_expiry_and_detached_copy(self):
        data = {'observations': [{'x': 1}]}
        packet = envelope('TEST', 'MONEY Ω · CODEX', data, now=NOW)
        data['observations'][0]['x'] = 9
        self.assertEqual(packet['payload']['observations'][0]['x'], 1)
        self.assertEqual(packet['schema_version'], '2.1')
        self.assertEqual(packet['object_id'], packet['packet_id'])
        self.assertTrue(verify_envelope(packet, NOW)[0])
        self.assertFalse(verify_envelope(packet, NOW + timedelta(hours=1))[0])

if __name__ == '__main__': unittest.main()
