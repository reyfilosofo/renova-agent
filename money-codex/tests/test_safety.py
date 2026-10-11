"""Adversarial fixtures; all issuers/accounts/venues are fictional test scopes."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import unittest
from money_codex.authorization import validate_live_authorization, PERMISSIONS
from money_codex.packets import envelope, verify_envelope, assert_no_secret_keys, canonical_json, strict_json_loads

NOW = datetime(2026, 10, 11, 12, tzinfo=timezone.utc)

def complete_fixture():
    auth = {'schema_version': '2.1', 'authorization_id': 'TEST-ONLY-NOT-AN-AUTHORIZATION', 'authorization_version': 1,
            'status': 'ACTIVE', 'issued_by': 'synthetic-test-issuer', 'issued_at_utc': (NOW - timedelta(minutes=1)).isoformat(),
            'expires_at_utc': (NOW + timedelta(minutes=1)).isoformat(), 'strategy_id': 'SYNTHETIC_TEST_ONLY', 'venue': 'NO_REAL_VENUE',
            'account_scope': 'NO_REAL_ACCOUNT', 'allowed_products': ['TEST_SPOT'], 'allowed_assets': ['BTC'],
            'permissions': {k: k in ('read_market_data', 'read_account_state', 'place_orders') for k in PERMISSIONS},
            'limits': {'max_order_usd': 10, 'max_gross_exposure_usd': 20, 'max_daily_loss_usd': 5, 'max_orders_per_hour': 2},
            'kill_switch': {'state': 'RUN', 'required': True, 'observed_at_utc': NOW.isoformat()}}
    context = {'execution_mode': 'LIVE_AUTHORIZED', 'authorization_verified': True, 'authorization_id': auth['authorization_id'],
               'trusted_issuers': ['synthetic-test-issuer'], 'issuer_verified': True, 'authorization_version': 1,
               'strategy_id': auth['strategy_id'], 'venue': auth['venue'], 'account_scope': auth['account_scope'],
               'asset': 'BTC', 'product': 'TEST_SPOT', 'action': 'place_orders', 'idempotency_key': 'SYNTHETIC-REQUEST-1',
               **{k: True for k in ('risk_gate_passed','data_fresh','costs_verified','liquidity_verified','account_state_verified','exposure_includes_order','reconciliation_healthy','revocation_checked','kill_switch_verified')},
               'revoked': False, 'kill_switch_state': 'RUN', 'revocation_checked_at_utc': NOW.isoformat(),
               **{k: NOW.isoformat() for k in ('account_state_observed_at_utc','market_data_observed_at_utc','kill_switch_observed_at_utc')},
               'order_usd': 5, 'gross_exposure_usd': 10, 'daily_loss_usd': 0, 'orders_this_hour': 0}
    return auth, context

class AuthorizationSafetyTests(unittest.TestCase):
    def test_complete_synthetic_context_only(self):
        auth, context = complete_fixture()
        self.assertTrue(validate_live_authorization(auth, NOW, context=context)[0])
        self.assertFalse(validate_live_authorization(auth, NOW)[0])
        self.assertFalse(validate_live_authorization(auth, NOW, context={'execution_mode':'LIVE_AUTHORIZED'})[0])

    def test_required_context_all_fail_closed_when_missing(self):
        for key in complete_fixture()[1]:
            auth, context = complete_fixture()
            context.pop(key)
            with self.subTest(key=key): self.assertFalse(validate_live_authorization(auth, NOW, context=context)[0])

    def test_scope_issuer_version_and_type_mismatch(self):
        changes = {'authorization_id':'OTHER','asset':'ETH','product':'FUTURES','venue':'OTHER','strategy_id':'OTHER',
                   'account_scope':'OTHER','issuer_verified':'true','authorization_version':True,'action':'withdraw',
                   'idempotency_key':'','revoked':None,'risk_gate_passed':1,'exposure_includes_order':False}
        for key, value in changes.items():
            auth, context = complete_fixture()
            context[key] = value
            with self.subTest(key=key): self.assertFalse(validate_live_authorization(auth, NOW, context=context)[0])

    def test_auth_typed_empty_future_expired_and_revoked(self):
        alterations = [('allowed_assets', []), ('allowed_products', []), ('issued_by', ''), ('status','REVOKED'),
                       ('issued_at_utc',(NOW + timedelta(seconds=1)).isoformat()), ('expires_at_utc', NOW.isoformat()),
                       ('authorization_version',True), ('revoked_at_utc',NOW.isoformat()), ('schema_version','2.0')]
        for key, value in alterations:
            auth, context = complete_fixture(); auth[key] = value
            with self.subTest(key=key): self.assertFalse(validate_live_authorization(auth, NOW, context=context)[0])
        auth, context = complete_fixture(); auth['permissions']['place_orders'] = 'false'
        self.assertFalse(validate_live_authorization(auth, NOW, context=context)[0])
        auth, context = complete_fixture(); auth['limits'] = {}
        self.assertFalse(validate_live_authorization(auth, NOW, context=context)[0])

    def test_every_risk_boundary_and_invalid_metric(self):
        for key, value in [('order_usd',11),('order_usd',0),('gross_exposure_usd',21),('daily_loss_usd',5),('orders_this_hour',2),('order_usd',True),('daily_loss_usd',float('nan')),('orders_this_hour',.5)]:
            auth, context = complete_fixture(); context[key] = value
            with self.subTest(key=key,value=value): self.assertFalse(validate_live_authorization(auth, NOW, context=context)[0])
        for key, value in [('max_order_usd',0),('max_order_usd',float('inf')),('max_orders_per_hour',True),('max_daily_loss_usd',-1)]:
            auth, context = complete_fixture(); auth['limits'][key] = value
            with self.subTest(key=key): self.assertFalse(validate_live_authorization(auth, NOW, context=context)[0])

    def test_suspended_kill_stale_account_and_revocation(self):
        for field in ('account_state_observed_at_utc','market_data_observed_at_utc','kill_switch_observed_at_utc','revocation_checked_at_utc'):
            for age in (-1, 31):
                auth, context = complete_fixture(); context[field] = (NOW - timedelta(seconds=age)).isoformat()
                with self.subTest(field=field,age=age): self.assertFalse(validate_live_authorization(auth, NOW, context=context)[0])
        auth, context = complete_fixture(); auth['kill_switch']['state'] = 'HALT'
        self.assertFalse(validate_live_authorization(auth, NOW, context=context)[0])
        auth, context = complete_fixture(); context['kill_switch_state'] = 'HALT'
        self.assertFalse(validate_live_authorization(auth, NOW, context=context)[0])

    def test_frozen_strategies_remain_paper(self):
        for strategy in ('RENOVA_DESK_V0','MONEY_FIXED_WINDOW_ANALOG_PAPER_V1'):
            auth, context = complete_fixture(); auth['strategy_id'] = context['strategy_id'] = strategy
            self.assertFalse(validate_live_authorization(auth, NOW, context=context)[0])

    def test_sensitive_permissions_rejected_even_with_otherwise_valid_auth(self):
        for key in ('withdraw','external_transfer','wallet_sign'):
            auth, context = complete_fixture(); auth['permissions'][key] = True
            self.assertFalse(validate_live_authorization(auth, NOW, context=context)[0])

class PacketSafetyTests(unittest.TestCase):
    def packet(self): return envelope('TEST','SYNTHETIC_PUBLISHER',{'x':1},now=NOW)
    def rehash(self, packet):
        packet['sha256'] = hashlib.sha256(canonical_json({k:v for k,v in packet.items() if k != 'sha256'})).hexdigest()
        return packet

    def test_mutation_and_freshness_metadata_detected(self):
        for key, value in [('payload',{'x':2}),('producer','OTHER'),('valid_until_utc',(NOW+timedelta(hours=2)).isoformat())]:
            packet=self.packet(); packet[key]=value
            with self.subTest(key=key): self.assertFalse(verify_envelope(packet,NOW)[0])
        packet=self.packet(); packet['updated_at_utc']=(NOW+timedelta(seconds=1)).isoformat(); self.rehash(packet)
        self.assertFalse(verify_envelope(packet,NOW)[0])

    def test_legacy_invalid_ttl_and_future_rejected_even_with_valid_digest(self):
        for changes in ({'schema_version':'2.0'},{'valid_until_utc':NOW.isoformat()},{'valid_until_utc':(NOW+timedelta(days=2)).isoformat()},
                        {'created_at_utc':(NOW+timedelta(seconds=1)).isoformat(),'updated_at_utc':(NOW+timedelta(seconds=1)).isoformat()},
                        {'created_at_utc':'2026-10-11T12:00:00'},{'object_id':'other'}):
            packet=self.packet();packet.update(changes);self.rehash(packet)
            with self.subTest(changes=changes): self.assertFalse(verify_envelope(packet,NOW)[0])

    def test_ttl_mandatory_shape_and_no_legacy_auto_migration(self):
        packet=self.packet();packet.pop('valid_until_utc')
        self.assertFalse(verify_envelope(packet,NOW)[0])
        for ttl in (0,-1,86401,True,1.1):
            with self.subTest(ttl=ttl),self.assertRaises(ValueError): envelope('TEST','P',{},now=NOW,ttl_seconds=ttl)
        for expiry in (NOW.isoformat(),(NOW-timedelta(seconds=1)).isoformat(),'2026-10-11T13:00:00'):
            with self.assertRaises(ValueError): envelope('TEST','P',{},expiry,now=NOW)
        packet=self.packet();packet['unknown']=None;self.rehash(packet)
        self.assertFalse(verify_envelope(packet,NOW)[0])

    def test_secrets_recognized_nested_without_echoing_values(self):
        for key in ('privateKey','PRIVATE KEY','Api-Secret','seed_phrase','BearerToken','OAuthRefreshToken','.env','password'):
            with self.subTest(key=key):
                with self.assertRaises(ValueError) as raised: envelope('TEST','P',{'items':[{key:'SENSITIVE_SENTINEL'}]},now=NOW)
                self.assertNotIn('SENSITIVE_SENTINEL',str(raised.exception))
        for value in ('-----BEGIN PRIVATE KEY-----','Bearer token1234567890','api_key=secret-sentinel','https://example.org/?access_token=sentinel'):
            with self.subTest(value=value),self.assertRaises(ValueError): assert_no_secret_keys({'note':value})

    def test_strict_json_duplicate_nonfinite_cycles_types(self):
        for text in ('{"x":1,"x":2}','{"x":NaN}','{"x":Infinity}','{"x":1e309}','{"items":[{"privateKey":"secret"}]}'):
            with self.subTest(text=text),self.assertRaises(ValueError): strict_json_loads(text)
        self.assertEqual(strict_json_loads('{"x":null,"valid":true}'),{'x':None,'valid':True})
        cycle=[];cycle.append(cycle)
        for data in (cycle,{'x':float('nan')},{1:'a'},{'x':(1,2)}, {'x':datetime.now()}):
            with self.assertRaises(ValueError): canonical_json(data)
        packet=self.packet();packet['payload']['x']=float('nan')
        self.assertFalse(verify_envelope(packet,NOW)[0])

if __name__ == '__main__': unittest.main()
