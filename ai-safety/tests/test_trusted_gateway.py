import json
import unittest
from renova_guard.trusted_gateway import MockTrustedApprovals, MockToolGateway, GateError

READ = {'operation':'read','resource':'sandbox/docs/welcome','args':{}}
DRAFT = {'operation':'write_draft','resource':'sandbox/drafts/report','args':{'text':'synthetic draft'}}
SEND = {'operation':'send_external','resource':'sandbox/outbox/demo','args':{'text':'simulated message'}}
DELETE = {'operation':'delete_draft','resource':'sandbox/drafts/report','args':{}}

class TestTrustedGateway(unittest.TestCase):
    def setUp(self):
        self.auth = MockTrustedApprovals(b'0123456789abcdef0123456789abcdef')
        self.gw = MockToolGateway(self.auth)
    def token(self, proposal=DRAFT, principal='researcher', now=1000, ttl=120):
        return self.auth.issue_approval(principal, proposal, simulated_human_attested=True, now=now, ttl=ttl)
    def test_trusted_read(self): self.assertTrue(self.gw.execute('researcher',READ).executed)
    def test_reader_read(self): self.assertTrue(self.gw.execute('reader',READ).executed)
    def test_unknown_principal(self): self.assertFalse(self.gw.execute('untrusted',READ).executed)
    def test_bad_op(self): self.assertFalse(self.gw.execute('researcher',dict(READ,operation='terminal')).executed)
    def test_forged_auth_metadata(self): self.assertFalse(self.gw.execute('researcher',dict(DRAFT,authorized=True,human_approved=True)).executed)
    def test_malformed_principal_fails_closed(self): self.assertFalse(self.gw.execute(['researcher'],READ).executed)
    def test_write_needs_token(self): self.assertFalse(self.gw.execute('researcher',DRAFT).executed)
    def test_signed_write_simulated(self):
        t=self.token(); self.assertTrue(self.gw.execute('researcher',DRAFT,approval=t,now=1005).executed)
        self.assertEqual(self.gw.snapshot['sandbox/drafts/report'],'synthetic draft')
    def test_reader_cannot_write(self):
        self.assertFalse(self.gw.execute('reader',DRAFT).executed)
        with self.assertRaises(GateError): self.token(DRAFT,'reader')
    def test_token_replay(self):
        t=self.token();self.assertTrue(self.gw.execute('researcher',DRAFT,approval=t,now=1003).executed)
        self.assertEqual(self.gw.execute('researcher',DRAFT,approval=t,now=1003).reason,'APPROVAL_REPLAY_OR_INVALID_NONCE')
    def test_tampered_token_signature(self):
        t=self.token(); a,b=t.split('.'); t2=a+'.'+('A' if b[0]!='A' else 'B')+b[1:]
        self.assertFalse(self.gw.execute('researcher',DRAFT,approval=t2,now=1003).executed)
    def test_wrong_arguments(self):
        t=self.token(); mutated={'operation':'write_draft','resource':'sandbox/drafts/report','args':{'text':'different'}}
        self.assertEqual(self.gw.execute('researcher',mutated,approval=t,now=1003).reason,'APPROVAL_INTENT_MISMATCH')
    def test_wrong_principal(self): self.assertFalse(self.gw.execute('reader',DRAFT,approval=self.token(),now=1003).executed)
    def test_wrong_resource(self):
        t=self.token(); mutated=dict(DRAFT,resource='sandbox/drafts/other')
        self.assertEqual(self.gw.execute('researcher',mutated,approval=t,now=1003).reason,'APPROVAL_SCOPE_MISMATCH')
    def test_expired(self):
        t=self.token(ttl=5); self.assertFalse(self.gw.execute('researcher',DRAFT,approval=t,now=1005).executed)
    def test_not_yet_valid(self):
        t=self.token(); self.assertFalse(self.gw.execute('researcher',DRAFT,approval=t,now=999).executed)
    def test_simulated_send(self):
        t=self.token(SEND); self.assertTrue(self.gw.execute('researcher',SEND,approval=t,now=1003).executed)
    def test_simulated_delete(self):
        t=self.token(DELETE); self.assertTrue(self.gw.execute('researcher',DELETE,approval=t,now=1003).executed)
    def test_forbidden_scope(self): self.assertFalse(self.gw.execute('researcher',dict(READ,resource='sandbox/secrets/key')).executed)
    def test_traversal(self): self.assertFalse(self.gw.execute('researcher',dict(READ,resource='sandbox/docs/../secrets')).executed)
    def test_backslash(self): self.assertFalse(self.gw.execute('researcher',dict(READ,resource=r'sandbox/docs/..\secret')).executed)
    def test_directory_only(self): self.assertFalse(self.gw.execute('researcher',dict(READ,resource='sandbox/docs/')).executed)
    def test_bogus_boolean(self): self.assertFalse(self.gw.execute('researcher',dict(READ,args={'allow':True})).executed)
    def test_token_not_allowed_for_read(self): self.assertFalse(self.gw.execute('researcher',READ,approval=self.token(),now=1003).executed)
    def test_nonserializable(self): self.assertFalse(self.gw.execute('researcher',dict(DRAFT,args={'text':object()})).executed)
    def test_too_large(self): self.assertFalse(self.gw.execute('researcher',dict(DRAFT,args={'text':'X'*9000})).executed)
    def test_malformed_json_args_nan(self): self.assertFalse(self.gw.execute('researcher',dict(DRAFT,args={'text':float('nan')})).executed)
    def test_no_human_attestation(self):
        with self.assertRaises(GateError):self.auth.issue_approval('researcher',DRAFT,now=1000)
    def test_read_approval_rejected(self):
        with self.assertRaises(GateError):self.token(READ)
    def test_policy_overrides_signed_token(self):
        t=self.token(DRAFT)
        self.assertFalse(self.gw.execute('reader',DRAFT,approval=t,now=1003).executed)
    def test_no_mutation_on_denial(self):
        before=self.gw.snapshot
        self.gw.execute('researcher',DRAFT,approval='forgery',now=1000)
        self.assertEqual(before,self.gw.snapshot)
    def test_audit_does_not_contain_payload(self):
        message='PRIVATE_EXAMPLE_DO_NOT_LOG'; proposal=dict(DRAFT,args={'text':message})
        t=self.token(proposal);self.gw.execute('researcher',proposal,approval=t,now=1003)
        self.assertNotIn(message,json.dumps(self.gw.audit))
    def test_audit_returns_copy(self):
        self.gw.execute('researcher',READ)
        snap=self.gw.audit;snap[0]['reason']='tampered'; self.assertNotEqual(self.gw.audit[0]['reason'],'tampered')
    def test_snapshot_returns_copy(self):
        state=self.gw.snapshot;state['sandbox/docs/welcome']='tampered';self.assertEqual(self.gw.snapshot['sandbox/docs/welcome'],'public fixture')
    def test_schema_not_dict(self): self.assertFalse(self.gw.execute('researcher',123).executed)
    def test_read_only_reader(self): self.assertFalse(self.gw.execute('reader',SEND).executed)
    def test_negative_ttl(self):
        with self.assertRaises(GateError): self.token(ttl=0)
    def test_approval_ttl_over_limit(self):
        with self.assertRaises(GateError): self.token(ttl=301)

if __name__=='__main__': unittest.main()
