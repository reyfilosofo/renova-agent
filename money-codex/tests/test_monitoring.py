from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
import http.client
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch
import urllib.error

from money_codex.monitoring import ASSETS, BASE, MAX_BYTES, SPAN, _fetch, _urls, inspect_snapshot, inspect_archive, main, monitor

NOW = datetime(2026,10,15,1,21,37,tzinfo=timezone.utc)
def ms(value): return int(value.timestamp()*1000)
def research(): return {'strategy':'MONEY_FIXED_WINDOW_ANALOG_PAPER_V1','calibrated':False,'contractProbability':None,'recommendation':'WAIT'}
def snapshot():
    start = ms(NOW)//SPAN*SPAN
    rows=[]
    for symbol in ASSETS:
        rows.append({'symbol':symbol,'windowStart':start,'windowEnd':start+SPAN,'research':research(),
                     'spot':12345, 'venues':[{'name':'Public venue','status':'PUBLICADO','quoteAt':None,'receivedAt':ms(NOW)-1000,
                                             'up':70,'down':30,'contractId':'public-contract','windowStart':start,'windowEnd':start+SPAN}]})
    return {'version':'1.1.0','asOf':ms(NOW)-1000,'serverTime':ms(NOW),'serverReceivedAt':ms(NOW)-2000,'expiresAt':ms(NOW)+44000,
            'timeframe':'5m','windowStart':start,'windowEnd':start+SPAN,'assets':rows}
def archive():
    start=ms(datetime(2026,10,14,6,tzinfo=timezone.utc))
    rows=[]
    for i in range(288):
        opened=start+i*SPAN
        cap=None
        if opened <= ms(NOW):
            cap={'asOf':opened,'row':{'symbol':'BTC','windowStart':opened,'windowEnd':opened+SPAN,'research':research(),'spot':12345}}
        rows.append({'index':i+1,'start':opened,'end':opened+SPAN,'capture':cap,'state':'UNTRUSTED DISPLAY LABEL'})
    return {'version':'1.1.0','date':'2026-10-14','symbol':'BTC','timeframe':'5m','asOf':ms(NOW),'start':start,
            'calendar':rows,'captureCount':sum(row['capture'] is not None for row in rows),'archiveState':'LECTURA VERIFICADA'}
def response(payload): return {'http_status':200,'access_status':'ACCESS VERIFIED','method':'GET','payload':payload}
def fetcher(url):
    if url.endswith('_healthcheck'):
        return response({'version':'1.1.0','assets':list(ASSETS),'frames':['5m','15m','1h'],'contractProbability':None})
    return response(snapshot() if 'snapshot' in url else archive())


class SnapshotMonitorTests(unittest.TestCase):
    def test_public_indicators_do_not_become_live_ticks(self):
        out=inspect_snapshot(snapshot(),NOW)
        self.assertEqual(out['state'],'FRESH')
        self.assertEqual(out['published_without_tick_count'],6)
        self.assertEqual(out['fresh_source_tick_count'],0)
        self.assertTrue(out['paper_flags_verified'])
        self.assertNotIn('spot',json.dumps(out))
        self.assertNotIn('12345',json.dumps(out))
        self.assertNotIn('"up"',json.dumps(out))
    def test_expiry_rollover_and_future_clock_are_fail_closed(self):
        out=inspect_snapshot(snapshot(),NOW+timedelta(minutes=1))
        self.assertEqual(out['state'],'STALE')
        bad=snapshot();bad['serverTime']=ms(NOW)+6000
        self.assertEqual(inspect_snapshot(bad,NOW)['state'],'DATA INSUFFICIENT')
        self.assertEqual(inspect_snapshot(snapshot(),NOW.replace(tzinfo=None))['state'],'DATA INSUFFICIENT')
    def test_malformed_timestamps_scope_assets_and_paper_flags(self):
        for field,value in [('asOf',True),('expiresAt',float('nan')),('serverTime',10**1000),('windowStart','yesterday'),('timeframe','1h')]:
            data=snapshot();data[field]=value
            with self.subTest(field=field):self.assertEqual(inspect_snapshot(data,NOW)['state'],'DATA INSUFFICIENT')
        data=snapshot();data['assets'][0]['symbol']='ETH'
        self.assertEqual(inspect_snapshot(data,NOW)['state'],'DATA INSUFFICIENT')
        data=snapshot();data['assets'][0]['research']['calibrated']=True
        self.assertFalse(inspect_snapshot(data,NOW)['paper_flags_verified'])
    def test_claimed_live_without_source_tick_is_detected(self):
        data=snapshot();data['assets'][0]['venues'][0]['status']='LIVE'
        out=inspect_snapshot(data,NOW)
        self.assertEqual(out['reported_live_count'],1)
        self.assertEqual(out['unverified_live_claim_count'],1)
        self.assertEqual(out['fresh_source_tick_count'],0)
        self.assertEqual(out['state'],'DATA INSUFFICIENT')
        quote=data['assets'][0]['venues'][0];quote['quoteAt']=ms(NOW)-2000
        out=inspect_snapshot(data,NOW)
        self.assertEqual(out['fresh_source_tick_count'],1)
        self.assertEqual(out['unverified_live_claim_count'],0)


class ArchiveMonitorTests(unittest.TestCase):
    def test_calendar_labels_and_declared_capture_count_are_not_proof(self):
        data=archive()
        for row in data['calendar'][84:217]:row['capture']=None;row['state']='CAPTURADO'
        data['captureCount']=100
        out=inspect_archive(data,NOW)
        self.assertEqual(out['captured_count'],100)
        self.assertEqual(out['missing_past_count'],133)
        self.assertEqual(out['future_count'],55)
        self.assertEqual(out['gaps'],[{'start_utc':'2026-10-14T13:00:00Z','end_utc_exclusive':'2026-10-15T00:05:00Z','window_count':133}])
        self.assertEqual(out['state'],'DEGRADED')
        self.assertEqual(out['scope'],'BTC_5m_ARCHIVE_ONLY')
    def test_current_window_pending_until_close(self):
        data=archive();current=data['calendar'][232];current['capture']=None;data['captureCount']-=1
        out=inspect_archive(data,NOW)
        self.assertEqual(out['missing_past_count'],0)
        self.assertEqual(out['pending_current_count'],1)
        data['asOf']=current['end']
        later=datetime.fromtimestamp(current['end']/1000,timezone.utc)
        out=inspect_archive(data,later)
        self.assertEqual(out['missing_past_count'],1)
    def test_actual_capture_timestamp_and_identity_must_match_window(self):
        for mutate in ('before','at_end','future','wrong_asset','wrong_window','boolean','not_object'):
            data=archive();row=data['calendar'][0]
            if mutate=='before':row['capture']['asOf']=row['start']-1
            elif mutate=='at_end':row['capture']['asOf']=row['end']
            elif mutate=='future':row['capture']['asOf']=ms(NOW)+6000
            elif mutate=='wrong_asset':row['capture']['row']['symbol']='ETH'
            elif mutate=='wrong_window':row['capture']['row']['windowEnd']+=SPAN
            elif mutate=='boolean':row['capture']['asOf']=True
            else:row['capture']='not a capture'
            with self.subTest(mutate=mutate):
                out=inspect_archive(data,NOW)
                self.assertEqual(out['invalid_capture_count'],1)
                self.assertEqual(out['missing_past_count'],1)
    def test_calendar_date_scope_grid_and_missing_payload_are_not_healthy(self):
        for field,value in [('date','2026-10-15'),('symbol','ETH'),('timeframe','15m'),('start',0),('asOf',float('inf'))]:
            data=archive();data[field]=value
            with self.subTest(field=field):self.assertEqual(inspect_archive(data,NOW)['state'],'DATA INSUFFICIENT')
        for change in ('missing','duplicate','shifted'):
            data=archive()
            if change=='missing':data['calendar'].pop()
            elif change=='duplicate':data['calendar'][1]=data['calendar'][0]
            else:data['calendar'][0]['start']+=1
            self.assertEqual(inspect_archive(data,NOW)['state'],'DATA INSUFFICIENT')
        self.assertIsNone(inspect_archive(None,NOW)['missing_past_count'])
    def test_gap_groups_are_bounded_and_private_extra_fields_are_ignored(self):
        data=archive()
        for i in range(0,20,2):data['calendar'][i]['capture']=None
        data['captureCount']-=10
        data['accounts']={'balance':'PRIVATE_SENTINEL'}
        data['calendar'][1]['capture']['row']['raw_body']='PRIVATE_SENTINEL'
        out=inspect_archive(data,NOW)
        self.assertEqual(out['gap_group_count'],10)
        self.assertEqual(len(out['gaps']),5)
        self.assertNotIn('PRIVATE_SENTINEL',json.dumps(out))
        self.assertNotIn('12345',json.dumps(out))
        stale=inspect_archive(data,NOW+timedelta(minutes=3))
        self.assertEqual(stale['freshness'],'STALE')


class NetworkMonitorTests(unittest.TestCase):
    def test_only_three_fixed_get_endpoints_and_no_agent_or_cron_inference(self):
        calls=[]
        def reader(url):calls.append(url);return fetcher(url)
        out=monitor(now=NOW,fetcher=reader)
        self.assertEqual(len(calls),3)
        self.assertEqual(set(calls),set(_urls('2026-10-14').values()))
        self.assertEqual(out['status'],'OBSERVATION ONLY')
        self.assertEqual(out['cron_status'],'NOT CHECKED')
        self.assertFalse(out['direct_chatgpt_to_codex'])
        self.assertFalse(out['direct_grok_bot_connected'])
        self.assertFalse(out['account_access_verified'])
        self.assertFalse(out['financial_execution_enabled'])
    def test_402_and_403_are_degraded_without_reading_error_body(self):
        for code in (402,403):
            error=urllib.error.HTTPError(BASE+'_healthcheck',code,'SECRET_SENTINEL',{},None)
            opener=MagicMock();opener.open.side_effect=error
            with patch('money_codex.monitoring.urllib.request.build_opener',return_value=opener):
                out=_fetch(BASE+'_healthcheck')
            self.assertEqual(out['http_status'],code)
            self.assertEqual(out['access_status'],'ACCESS UNAVAILABLE')
            self.assertNotIn('SECRET_SENTINEL',json.dumps(out))
        unavailable=lambda url:{'http_status':402,'access_status':'ACCESS UNAVAILABLE','method':'GET','error_code':'http_unavailable'}
        out=monitor(now=NOW,fetcher=unavailable)
        self.assertEqual(out['status'],'DEGRADED')
        self.assertTrue(all(row['inspection']['state']=='UNAVAILABLE' for row in out['endpoints'].values()))
    def test_canonical_get_bounds_corrupt_json_and_redirect(self):
        for url in ('http://api-v2.appdeploy.ai/',BASE+'capture','https://127.0.0.1/','https://evil.test/',BASE+'dayplan?asset=BTC&tf=5m&date=2026-10-14&token=secret'):
            with self.subTest(url=url),patch('money_codex.monitoring.urllib.request.build_opener') as opener:
                with self.assertRaises(ValueError):_fetch(url)
                opener.assert_not_called()
        url=BASE+'_healthcheck'
        response_mock=MagicMock();response_mock.__enter__.return_value=response_mock;response_mock.status=200
        response_mock.geturl.return_value=url;response_mock.headers={'Content-Type':'application/json'}
        opener=MagicMock();opener.open.return_value=response_mock
        for body in (b'{broken',b'{"x":1,"x":2}',b'x'*(MAX_BYTES+1)):
            response_mock.read.return_value=body
            with patch('money_codex.monitoring.urllib.request.build_opener',return_value=opener):out=_fetch(url)
            self.assertNotIn('payload',out)
        request=opener.open.call_args.args[0]
        self.assertEqual(request.get_method(),'GET')
        self.assertNotIn('Authorization',dict(request.header_items()))
        self.assertEqual(opener.open.call_args.kwargs['timeout'],12)
        response_mock.read.assert_called_with(MAX_BYTES+1)
        response_mock.geturl.return_value='https://evil.test/'
        with patch('money_codex.monitoring.urllib.request.build_opener',return_value=opener):
            self.assertEqual(_fetch(url)['access_status'],'ACCESS UNAVAILABLE')
    def test_cli_writes_outage_report_and_returns_zero_without_raw_output(self):
        report=monitor(now=NOW,fetcher=lambda url:{'http_status':402,'access_status':'ACCESS UNAVAILABLE','method':'GET'})
        with tempfile.TemporaryDirectory() as temp,patch('money_codex.monitoring.monitor',return_value=report):
            target=Path(temp)/'monitor.json'
            with patch('builtins.print'):
                self.assertEqual(main(['--output',str(target)]),0)
            self.assertEqual(json.loads(target.read_text())['status'],'DEGRADED')
        with patch('money_codex.monitoring.monitor') as runner,patch('sys.stderr'):
            with self.assertRaises(SystemExit) as raised:main(['--output','unused','--date','2026-02-31'])
            self.assertEqual(raised.exception.code,2)
            runner.assert_not_called()

    def test_transport_failure_is_observed_unavailable_without_exception_text(self):
        opener=MagicMock();opener.open.side_effect=http.client.IncompleteRead(b'PRIVATE_SENTINEL')
        with patch('money_codex.monitoring.urllib.request.build_opener',return_value=opener):
            out=_fetch(BASE+'_healthcheck')
        self.assertEqual(out['access_status'],'ACCESS UNAVAILABLE')
        self.assertNotIn('PRIVATE_SENTINEL',json.dumps(out))

if __name__=='__main__':unittest.main()
