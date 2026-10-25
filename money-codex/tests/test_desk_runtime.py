import hashlib
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import MagicMock, patch
import urllib.error

from money_codex.desk_runtime import ASSETS, BASE, DeskStore, collect_desk, fetch_ticker, normalize_ticker, require_paper, main

NOW = datetime(2026, 10, 24, 17, 0, 10, tzinfo=timezone.utc)

def response(asset='BTC', now=NOW):
    payload = {'price': '100.01', 'bid': '100.00', 'ask': '100.02', 'time': (now-timedelta(seconds=1)).isoformat()}
    return {'url': BASE+asset+'-USD/ticker', 'method': 'GET', 'http_status': 200,
            'received_at_utc': now.isoformat(), 'payload': payload,
            'body_sha256': hashlib.sha256(json.dumps(payload).encode()).hexdigest()}

class DeskRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = DeskStore(Path(self.temp.name)/'desk')
    def tearDown(self): self.temp.cleanup()

    def test_public_timestamps_and_exact_decimal_strings_keep_their_scope(self):
        quote=normalize_ticker('BTC',response(),NOW)
        self.assertEqual(quote['last_trade_price'],'100.01')
        self.assertEqual(quote['bid'],'100.00')
        self.assertEqual(quote['status'],'OBSERVED')
        self.assertEqual(quote['timestamp_scope'],'LAST_TRADE_ONLY')
        self.assertFalse(quote['bid_ask_timestamp_verified'])
        self.assertNotEqual(quote['last_trade_at_utc'],quote['received_at_utc'])

    def test_missing_product_never_synthesizes_bnb_or_zero_price(self):
        quote=normalize_ticker('BNB',{'url':BASE+'BNB-USD/ticker','http_status':404},NOW)
        self.assertEqual(quote['status'],'UNAVAILABLE')
        self.assertIsNone(quote['price'])
        self.assertIsNone(quote['bid'])

    def test_invalid_book_nonfinite_future_and_wrong_source_are_unavailable(self):
        for change in ({'bid':'200'},{'ask':'NaN'},{'price':'0'},{'time':(NOW+timedelta(seconds=1)).isoformat()}):
            item=response();item['payload'].update(change)
            self.assertEqual(normalize_ticker('BTC',item,NOW)['status'],'UNAVAILABLE')
        item=response();item['url']='http://127.0.0.1/'
        self.assertEqual(normalize_ticker('BTC',item,NOW)['status'],'UNAVAILABLE')

    def test_old_tick_is_stale_even_with_a_new_http_response(self):
        item=response();item['payload']['time']=(NOW-timedelta(minutes=4)).isoformat()
        self.assertEqual(normalize_ticker('BTC',item,NOW)['status'],'STALE')

    def test_worker_recovery_fences_old_owner_and_commits_nothing(self):
        old=self.store.acquire('old',NOW)
        self.assertIsNone(self.store.acquire('second',NOW))
        later=NOW+timedelta(seconds=181)
        fresh=DeskStore(self.store.state_dir).acquire('new',later)
        with self.assertRaises(ValueError):self.store.finish(old,[normalize_ticker('BTC',response(),NOW)],[],now=later)
        self.assertEqual(self.store.status()['counts']['observations'],0)
        self.store.finish(fresh,[],[],now=later)
        with self.store._db() as db: states=[row['state'] for row in db.execute('SELECT state FROM desk_cycles ORDER BY started')]
        self.assertEqual(states,['ABANDONED','FINISHED'])

    def test_complete_cycle_survives_restart_without_repeating_same_observation(self):
        observation=normalize_ticker('BTC',response(),NOW)
        for offset in (0,1):
            lease=self.store.acquire('worker',NOW+timedelta(seconds=offset))
            self.store.finish(lease,[observation],[{'asset':'BTC','status':'OBSERVED'}],now=NOW+timedelta(seconds=offset))
        restarted=DeskStore(self.store.state_dir)
        self.assertEqual(restarted.status()['counts']['observations'],1)
        self.assertTrue(restarted.status()['audit_integrity'])
        self.assertNotIn('BTC',restarted.due(NOW+timedelta(seconds=10)))
        self.assertEqual(restarted.latest(NOW+timedelta(minutes=5))[0][0]['status'],'STALE')

    def test_cycle_rollback_does_not_keep_observations_when_source_identity_is_bad(self):
        lease=self.store.acquire('worker',NOW)
        with self.assertRaises(ValueError):self.store.finish(lease,[normalize_ticker('BTC',response(),NOW)],[{'asset':'NOT_AN_ASSET'}],now=NOW)
        self.assertEqual(self.store.status()['counts']['observations'],0)
        self.store.release(lease,NOW)
        self.assertIsNotNone(self.store.acquire('new',NOW))

    def test_six_asset_collection_has_three_reviews_and_defaults_to_halt(self):
        calls=[]
        def read(asset):calls.append(asset);return response(asset)
        report=collect_desk(self.store.state_dir,now=NOW,fetcher=read)
        self.assertEqual(calls,list(ASSETS))
        self.assertEqual(len(report['observations']),6)
        self.assertEqual([r['timeframe'] for r in report['reviews']],['5m','15m','1h'])
        self.assertEqual(report['risk_state'],'HALT')
        self.assertFalse(report['live_execution_enabled'])
        self.assertFalse(report['paper_execution_enabled'])
        self.assertTrue(all(not r['approvedForPaper'] for r in report['reviews']))
        for snapshot in report['snapshots']:
            self.assertTrue(all(row['contracts']==[] for row in snapshot['assets']))
        self.assertEqual(self.store.status()['counts']['records'],3)
        calls.clear()
        again=collect_desk(self.store.state_dir,now=NOW+timedelta(seconds=1),fetcher=read)
        self.assertEqual(calls,[])
        self.assertEqual(again['state'],'COOLDOWN')

    def test_provider_block_stops_followup_gets_and_cooldown_survives_restart(self):
        calls=[]
        def read(asset):calls.append(asset);return {'url':BASE+asset+'-USD/ticker','http_status':429}
        report=collect_desk(self.store.state_dir,now=NOW,fetcher=read)
        self.assertEqual(calls,['BTC'])
        self.assertTrue(all(s['retry_after_seconds']==900 for s in report['source_status']))
        self.assertEqual(DeskStore(self.store.state_dir).due(NOW+timedelta(minutes=10)),[])
        self.assertTrue(all(row['status']=='UNAVAILABLE' for row in report['observations']))
        self.assertEqual(self.store.status()['counts']['observations'],0)

    def test_export_rechecks_source_ttl_and_retains_explicit_historical_price(self):
        report=collect_desk(self.store.state_dir,now=NOW,fetcher=response)
        self.assertEqual(report['fresh_observation_count'],6)
        exported=DeskStore(self.store.state_dir).public_report(NOW+timedelta(seconds=91))
        self.assertEqual(exported['fresh_observation_count'],0)
        self.assertTrue(all(s['access_status']=='ACCESS STALE' for s in exported['source_status']))
        self.assertTrue(all(q['status']=='STALE' and q['price']=='100.01' for q in exported['observations']))
        self.assertEqual(exported['risk_state'],'HALT')
        self.assertFalse(exported['paper_execution_enabled'])
        self.assertFalse(exported['live_execution_enabled'])

    def test_all_failed_cli_writes_complete_failure_report_and_returns_two(self):
        output=Path(self.temp.name)/'public.json'
        def blocked(asset):return {'url':BASE+asset+'-USD/ticker','http_status':451}
        with patch('money_codex.desk_runtime.fetch_ticker',side_effect=blocked):
            code=main(['collect','--state-dir',str(self.store.state_dir),'--output',str(output)])
        self.assertEqual(code,2)
        report=json.loads(output.read_text())
        self.assertEqual(report['state'],'DEGRADED')
        self.assertEqual(report['schema_version'],'1.0')
        self.assertEqual(report['fresh_observation_count'],0)
        self.assertEqual(len(report['observations']),6)
        self.assertEqual(len(report['source_status']),6)
        self.assertEqual(len(report['reviews']),3)
        self.assertEqual(report['risk_state'],'HALT')
        self.assertTrue(report['audit_integrity'])
        self.assertFalse(report['paper_execution_enabled'])
        self.assertFalse(report['live_execution_enabled'])
        self.assertTrue(all(q['price'] is None for q in report['observations']))

    def test_fetcher_failure_releases_worker_and_rolls_back_partial_cycle(self):
        def broken(asset):
            if asset=='ETH':raise OSError('synthetic interrupted fetch')
            return response(asset)
        with self.assertRaises(OSError):collect_desk(self.store.state_dir,now=NOW,fetcher=broken)
        with self.store._db() as db:
            self.assertEqual(db.execute('SELECT state FROM desk_cycles').fetchone()['state'],'INTERRUPTED')
            self.assertEqual(db.execute('SELECT count(*) FROM desk_worker').fetchone()[0],0)
        self.assertEqual(self.store.status()['counts']['observations'],0)
        report=collect_desk(self.store.state_dir,now=NOW,fetcher=response)
        self.assertEqual(report['fresh_observation_count'],6)
        self.assertTrue(report['audit_integrity'])

    def test_busy_worker_report_is_complete_and_does_not_create_second_cycle(self):
        lease=self.store.acquire('held',NOW)
        report=collect_desk(self.store.state_dir,now=NOW,fetcher=lambda asset:self.fail('busy worker fetched'))
        self.assertEqual(report['state'],'WORKER_BUSY')
        self.assertEqual(len(report['observations']),6)
        self.assertEqual(len(report['source_status']),6)
        self.assertEqual(report['risk_state'],'HALT')
        self.assertEqual(report['counts']['cycles'],1)
        self.store.release(lease,NOW)

    def test_fresh_collection_may_leave_unlisted_bnb_unknown(self):
        def read(asset):return {'url':BASE+asset+'-USD/ticker','http_status':404} if asset=='BNB' else response(asset)
        report=collect_desk(self.store.state_dir,now=NOW,fetcher=read)
        self.assertEqual(report['fresh_observation_count'],5)
        self.assertEqual(report['state'],'COLLECTED')
        self.assertIsNone(next(q for q in report['observations'] if q['asset']=='BNB')['price'])
        self.assertEqual(next(s for s in report['source_status'] if s['asset']=='BNB')['error_code'],'PRODUCT_UNAVAILABLE')

    def test_prospective_judgment_idempotency_and_outcome_cannot_rewrite_history(self):
        judgment={'mode':'PAPER','judgment_id':'j1','issued_at_utc':NOW.isoformat(),'contract_end_utc':(NOW+timedelta(minutes=5)).isoformat(),'asset':'BTC'}
        first=self.store.append_record('JUDGMENT',judgment,'request-1',NOW)
        self.assertEqual(self.store.append_record('JUDGMENT',judgment,'request-1',NOW),first)
        with self.assertRaises(ValueError):self.store.append_record('JUDGMENT',{**judgment,'asset':'ETH'},'request-2',NOW)
        outcome={'mode':'PAPER','judgment_id':'j1','settled_at_utc':(NOW+timedelta(minutes=5)).isoformat(),'result':'UNKNOWN'}
        with self.assertRaises(ValueError):self.store.append_record('OUTCOME',outcome,'outcome-1',NOW)
        later=NOW+timedelta(minutes=5)
        self.store.append_record('OUTCOME',outcome,'outcome-1',later)
        with self.assertRaises(ValueError):self.store.append_record('OUTCOME',{**outcome,'result':'WIN'},'outcome-2',later)
        self.assertTrue(self.store.status()['audit_integrity'])

    def test_judgment_must_be_stored_before_contract_close(self):
        old={'mode':'PAPER','judgment_id':'retro','issued_at_utc':(NOW-timedelta(hours=1)).isoformat(),'contract_end_utc':NOW.isoformat()}
        with self.assertRaises(ValueError):self.store.append_record('JUDGMENT',old,'retro',NOW)
        with self.assertRaises(ValueError):self.store.append_record('OUTCOME',{'mode':'PAPER','judgment_id':'missing','settled_at_utc':NOW.isoformat()},'missing',NOW)

    def test_paper_mode_and_secret_guard_fail_before_writes(self):
        with patch.dict(os.environ,{'MONEY_DESK_MODE':'LIVE'}):
            with self.assertRaises(ValueError):DeskStore(Path(self.temp.name)/'rejected')
        with patch.dict(os.environ,{'MONEY_EXECUTION_MODE':'LIVE'}):
            with self.assertRaises(ValueError):require_paper()
        for payload in ({'mode':'LIVE'},{'mode':'PAPER','execution_enabled':True},{'mode':'PAPER','executionEnabled':True},{'mode':'PAPER','financialAuthority':True},{'mode':'PAPER','approvedForPaper':True},{'mode':'PAPER','private_key':'synthetic-forbidden-key'}):
            with self.assertRaises(ValueError):self.store.append_record('REVIEW',payload,'bad',NOW)
        self.assertEqual(self.store.status()['counts']['records'],0)

    def test_public_fetch_uses_fixed_get_no_auth_and_blocked_response_has_no_body(self):
        error=urllib.error.HTTPError(BASE+'BTC-USD/ticker',403,'Forbidden',{},None)
        opener=MagicMock();opener.open.side_effect=error
        with patch('money_codex.desk_runtime.urllib.request.build_opener',return_value=opener):
            result=fetch_ticker('BTC')
        request=opener.open.call_args.args[0]
        self.assertEqual(request.get_method(),'GET')
        self.assertEqual(request.full_url,BASE+'BTC-USD/ticker')
        self.assertNotIn('Authorization',dict(request.header_items()))
        self.assertEqual(result['http_status'],403)
        self.assertNotIn('payload',result)
        with self.assertRaises(ValueError):fetch_ticker('../accounts')

    def test_append_only_audit_detects_corruption(self):
        self.store.acquire('worker',NOW)
        with self.store._db() as db:
            with self.assertRaises(sqlite3.IntegrityError):db.execute('DELETE FROM desk_events')
            db.execute('DROP TRIGGER desk_events_no_update')
            db.execute("UPDATE desk_events SET payload='{}' WHERE seq=1")
        self.assertFalse(self.store.status()['audit_integrity'])

if __name__=='__main__':unittest.main()
