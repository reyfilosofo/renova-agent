import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch
import urllib.error

from money_codex.sync import _head_or_get, sync, load_config, CANONICAL_PUBLIC_URLS


def config():
    return {'github':{'repo_url':CANONICAL_PUBLIC_URLS['GitHub public repository']},
            'surfaces':{'money_app':CANONICAL_PUBLIC_URLS['MONEY app'],'grok_site':CANONICAL_PUBLIC_URLS['MONEY Grok site']},
            'drive':{'operating_bridge_id':'A_PROJECT_IDENTIFIER_NOT_ACCESS'},
            'projects':{'chatgpt_project_id':'A_PROJECT_IDENTIFIER_NOT_ACCESS','codex_project_id':'PENDING_USER_INPUT'}}


class SyncTests(unittest.TestCase):
    def test_public_2xx_is_partial_never_authenticated_access(self):
        with patch('money_codex.sync._head_or_get',return_value=(True,'HTTP 200; public reachability only')):
            result=sync(config())
        self.assertTrue(all(row.status=='ACCESS PARTIAL' for row in result[:3]))
        self.assertTrue(all(row.status=='ACCESS UNAVAILABLE' for row in result[3:]))
        self.assertTrue(all('not verified' in row.detail or 'no project API read verified' in row.detail for row in result))

    def test_env_values_endpoints_identifiers_and_tokens_never_disclosed(self):
        secrets={'GOOGLE_DRIVE_ACCESS_TOKEN':'DRIVE_SECRET_SENTINEL','GROK_BOT_ENDPOINT':'https://user:BOT_SECRET_SENTINEL@internal.test/?token=secret',
                 'CHATGPT_BRIDGE_ENDPOINT':'CHATGPT_SECRET_SENTINEL'}
        with patch.dict('os.environ',secrets),patch('money_codex.sync._head_or_get',return_value=(False,'network_unavailable')):
            result=sync(config())
        serialized=json.dumps([row.to_dict() for row in result])
        for value in (*secrets.values(),'A_PROJECT_IDENTIFIER_NOT_ACCESS'):
            self.assertNotIn(value,serialized)
        self.assertNotIn('ACCESS VERIFIED',serialized)
        self.assertTrue(all(row.status=='ACCESS UNAVAILABLE' for row in result))

    def test_noncanonical_https_http_private_and_sensitive_config_never_requested(self):
        for target in ('http://github.com/reyfilosofo/renova-agent','https://evil.test/',
                       'https://169.254.169.254/','https://github.com/reyfilosofo/renova-agent?token=SENTINEL',
                       'https://user:secret@github.com/reyfilosofo/renova-agent','https://github.com/other/repo',
                       'https://money-z6epdn.v2.appdeploy.ai:8443/','https://themoney.grok.me/private'):
            with self.subTest(target=target),patch('money_codex.sync.urllib.request.build_opener') as opener:
                self.assertFalse(_head_or_get(target)[0])
                opener.assert_not_called()
        cfg=config();cfg['surfaces']['money_app']='https://themoney.grok.me/'
        with patch('money_codex.sync._head_or_get',return_value=(False,'network_unavailable')) as get:
            result=sync(cfg)
        self.assertEqual(get.call_count,2)
        self.assertEqual(result[1].target,'UNVERIFIED CONFIGURATION')

    def test_only_2xx_is_reachable_and_get_is_canonical_no_redirect_follow(self):
        url=CANONICAL_PUBLIC_URLS['MONEY app']
        for code in (200,204,301,403,404,451,500):
            response=MagicMock();response.__enter__.return_value=response;response.status=code;response.geturl.return_value=url
            opener=MagicMock();opener.open.return_value=response
            with self.subTest(code=code),patch('money_codex.sync.urllib.request.build_opener',return_value=opener):
                ok,detail=_head_or_get(url)
                self.assertEqual(ok,200<=code<300)
                request=opener.open.call_args.args[0]
                self.assertEqual(request.get_method(),'GET')
                self.assertEqual(request.full_url,url)
        response.geturl.return_value='https://private.internal.test/'
        with patch('money_codex.sync.urllib.request.build_opener',return_value=opener): self.assertFalse(_head_or_get(url)[0])

    def test_http_errors_and_network_exceptions_have_no_original_exception_text(self):
        url=CANONICAL_PUBLIC_URLS['MONEY app']
        for error in (urllib.error.HTTPError(url,403,'SECRET_SENTINEL',None,None), urllib.error.URLError('SECRET_SENTINEL'),OSError('SECRET_SENTINEL')):
            opener=MagicMock();opener.open.side_effect=error
            with patch('money_codex.sync.urllib.request.build_opener',return_value=opener):
                ok,detail=_head_or_get(url)
            self.assertFalse(ok)
            self.assertNotIn('SECRET_SENTINEL',detail)

    def test_config_loader_rejects_duplicates_tokens_and_invalid_shape(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'config.json'
            for text in ('{"github":{},"github":{}}','{"apiSecret":"SENTINEL"}','[]','{"x":NaN}'):
                path.write_text(text)
                with self.subTest(text=text),self.assertRaises(ValueError):load_config(path)
            path.write_text(json.dumps(config()))
            self.assertEqual(load_config(path),config())
        with self.assertRaises(ValueError): sync([])
        self.assertTrue(all(row.status=='ACCESS UNAVAILABLE' for row in sync({})))

if __name__=='__main__':unittest.main()
