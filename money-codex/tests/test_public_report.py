from copy import deepcopy
from datetime import datetime, timezone
import json
import unittest
from unittest.mock import Mock

from money_codex.public_report import make_public_report, safe_url

STAMP='2026-10-11T17:00:00Z'


def source():
    return {'source_id':'immunefi_programs','access_status':'ACCESS VERIFIED','last_scan_at_utc':STAMP,
            'config':{'provider':'immunefi','source_id':'immunefi_programs','enabled':True,'method':'READ_ONLY','url':'https://immunefi.com/bug-bounty/'}}


def opportunity():
    return {'opportunity_id':'resource_'+'a'*24, 'source_id':'immunefi_programs','provider':'Immunefi programmes',
            'type':'BOUNTY','title':'Official programme','official_url':'https://immunefi.com/bug-bounty/ens/information/',
            'last_verified_at_utc':STAMP,'classification':'WATCH','ev_status':'DATA INSUFFICIENT',
            'expected_gross_reward_usd':None,'reward_probability':None,'expected_net_reward_usd':None,'discovery_only':True,
            'missing_data':['reward_probability'],'blocking_reasons':[],
            'source_evidence':{'url':'https://immunefi.com/bug-bounty/','observed_link':'https://immunefi.com/bug-bounty/ens/information/',
                               'observed_at':STAMP,'content_sha256':'b'*64,'http_status':200}}


class PublicReportTests(unittest.TestCase):
    def store(self, rows=None, sources=None):
        store=Mock()
        store.opportunities.return_value=[opportunity()] if rows is None else rows
        store.list_sources.return_value=[source()] if sources is None else sources
        store.status.return_value={'ledger_integrity':True,'state_directory':'PRIVATE_WORKSPACE_SENTINEL',
                                   'receipts':[{'account':'ACCOUNT_SENTINEL'}]}
        return store

    def test_public_fields_known_proof_unknown_ev_and_no_private_methods(self):
        store=self.store()
        result=make_public_report(store)
        self.assertEqual(result['opportunity_count'],1)
        self.assertIsNone(result['opportunities'][0]['expected_gross_reward_usd'])
        self.assertIsNone(result['verified_income_usd'])
        self.assertFalse(result['direct_grok_bot_connected'])
        self.assertEqual(result['opportunities'][0]['source_evidence'][0]['http_status'],200)
        self.assertEqual({call[0] for call in store.method_calls},{'opportunities','list_sources','status'})
        self.assertNotIn('PRIVATE_WORKSPACE_SENTINEL',json.dumps(result))
        self.assertNotIn('ACCOUNT_SENTINEL',json.dumps(result))

    def test_allowlisted_fields_do_not_copy_nested_private_values(self):
        row=opportunity()
        row.update({'accounts':{'balance':1234},'wallet':'WALLET_SENTINEL','receipts':['RECEIPT_SENTINEL'],
                    'invalidation':'PRIVATE_OPERATOR_SENTINEL','raw_evidence':'RAW_EVIDENCE_SENTINEL',
                    'expected_gross_reward_usd':{'account':'NESTED_SENTINEL'},
                    'reward_probability':True,'expected_net_reward_usd':float('nan'),
                    'missing_data':[{'privateKey':'PRIVATE_SENTINEL'},'ACCOUNT_SENTINEL=123','reward_probability'],
                    'blocking_reasons':['HTTP failed with api_key=SECRET_SENTINEL']})
        row['source_evidence'].update({'body':'RAW_RESPONSE_SENTINEL','headers':{'Authorization':'SECRET_SENTINEL'},'account':'PRIVATE_ACCOUNT_SENTINEL'})
        result=make_public_report(self.store([row]))
        serialized=json.dumps(result,allow_nan=False)
        for forbidden in ('ACCOUNT_SENTINEL','NESTED_SENTINEL','RECEIPT_SENTINEL','OPERATOR_SENTINEL','RAW_EVIDENCE_SENTINEL','RAW_RESPONSE_SENTINEL','PRIVATE_ACCOUNT_SENTINEL','SECRET_SENTINEL','PRIVATE_SENTINEL'):
            self.assertNotIn(forbidden,serialized)
        self.assertIsNone(result['opportunities'][0]['expected_gross_reward_usd'])
        self.assertIsNone(result['opportunities'][0]['reward_probability'])
        self.assertIsNone(result['opportunities'][0]['expected_net_reward_usd'])

    def test_unsafe_titles_private_markers_unregistered_or_wrong_provider_excluded(self):
        for changes in ({'title':{'privateKey':'secret'}},{'title':'Account: PRIVATE_ACCOUNT'}, {'title':'person@example.org'},
                        {'title':'Bearer secret_token_sentinal'},{'private':True},{'privacy':'CONFIDENTIAL'},
                        {'source_id':'unknown'},{'official_url':'https://zealy.io/'}):
            with self.subTest(changes=changes):
                self.assertEqual(make_public_report(self.store([{**opportunity(),**changes}]))['opportunity_count'],0)

    def test_unverified_http_hash_source_link_or_source_config_excluded(self):
        for changes in ({'http_status':403},{'http_status':True},{'content_sha256':'x'}, {'observed_at':'invalid'},
                        {'url':'https://evil.test/'},{'observed_link':'https://immunefi.com/unrelated'}):
            row=opportunity();row['source_evidence'].update(changes)
            with self.subTest(changes=changes): self.assertEqual(make_public_report(self.store([row]))['opportunity_count'],0)
        config=source();config['config']['method']='LIVE'
        self.assertEqual(make_public_report(self.store(sources=[config]))['opportunity_count'],0)

    def test_urls_reject_tokens_fragments_credentials_nonofficial_and_private_routes(self):
        urls=['http://immunefi.com/','https://immunefi.com.evil.test/','https://127.0.0.1/',
              'https://immunefi.com:8443/','https://user:password@immunefi.com/','https://immunefi.com/?access_token=SENTINEL',
              'https://immunefi.com/#BearerSENTINEL','https://immunefi.com/a/../b','https://immunefi.com/private_key=sentinel',
              'https://api.github.com/repos/a/b/issues?token=SENTINEL','https://api.github.com/repos/a/b/issues?labels=bounty&labels=private',
              'https://api.github.com/repos/a/b/issues?%61ccess_token=sentinel']
        for url in urls:
            with self.subTest(url=url):self.assertIsNone(safe_url(url))
        self.assertEqual(safe_url('https://api.github.com/repos/a/b/issues?state=open&labels=bounty&per_page=20'),
                         'https://api.github.com/repos/a/b/issues?state=open&labels=bounty&per_page=20')
        row=opportunity();row['official_url']='https://immunefi.com/?token=SENTINEL'
        self.assertNotIn('SENTINEL',json.dumps(make_public_report(self.store([row]))))

    def test_status_exception_text_and_arbitrary_config_are_not_exported(self):
        item=source();item['access_status']='api_key=SECRET_STATUS_SENTINEL'
        item['config'].update({'api_secret':'SECRET_CONFIG_SENTINEL','account_id':'PRIVATE_ACCOUNT_SENTINEL'})
        result=make_public_report(self.store(sources=[item]))
        self.assertEqual(result['sources'][0]['last_status'],'ACCESS UNAVAILABLE')
        serialized=json.dumps(result)
        self.assertNotIn('SENTINEL',serialized)

if __name__=='__main__': unittest.main()
