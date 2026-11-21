import unittest
from renova_guard.gate import assess, assess_claim

LOW = dict(type='read', risk='low', reversible=True, authorized=True)

class TestSafetyGate(unittest.TestCase):
    def test_read(self): self.assertEqual(assess(LOW).status, 'ALLOW')
    def test_draft(self): self.assertEqual(assess(dict(LOW, type='draft')).status, 'ALLOW')
    def test_unknown_action(self): self.assertEqual(assess(dict(LOW, type='invent_new_action')).status, 'DENY')
    def test_no_auth(self): self.assertEqual(assess(dict(LOW, authorized=False)).status, 'DENY')
    def test_unknown_auth(self): self.assertEqual(assess(dict(LOW, authorized=None)).status, 'REVIEW')
    def test_unknown_risk(self): self.assertEqual(assess(dict(LOW, risk='none')).status, 'REVIEW')
    def test_irreversible(self): self.assertEqual(assess(dict(LOW, reversible=False)).status, 'REVIEW')
    def test_high_risk(self): self.assertEqual(assess(dict(LOW, risk='high')).status, 'REVIEW')
    def test_medium_risk(self): self.assertEqual(assess(dict(LOW, risk='medium')).status, 'REVIEW')
    def test_external_send(self): self.assertEqual(assess(dict(LOW, type='send_external', human_approved=True)).status, 'REVIEW')
    def test_payment(self): self.assertEqual(assess(dict(LOW, type='payment')).status, 'REVIEW')
    def test_delete(self): self.assertEqual(assess(dict(LOW, type='delete')).status, 'REVIEW')
    def test_write(self): self.assertEqual(assess(dict(LOW, type='write_internal')).status, 'REVIEW')
    def test_injection(self): self.assertEqual(assess(dict(LOW, instruction_source='untrusted', requested_privilege_escalation=True)).status, 'DENY')
    def test_missing_reversibility(self): self.assertEqual(assess(dict(LOW, reversible='yes')).status, 'REVIEW')
    def test_malformed(self): self.assertEqual(assess(123).status, 'DENY')
    def test_no_source_fact(self): self.assertEqual(assess_claim(dict(kind='fact',citations=[])).status, 'REVIEW')
    def test_cited_fact_not_verified(self): self.assertEqual(assess_claim(dict(kind='fact',citations=['url'])).status, 'REVIEW')
    def test_hypothesis(self): self.assertEqual(assess_claim(dict(kind='hypothesis')).status, 'ALLOW')
    def test_consequential_hypothesis(self): self.assertEqual(assess_claim(dict(kind='hypothesis',externally_consequential=True)).status, 'REVIEW')
    def test_non_string_claim_kind(self): self.assertEqual(assess_claim({'kind':['fact']}).status, 'REVIEW')
    def test_unknown_claim(self): self.assertEqual(assess_claim(dict(kind='certainty')).status, 'REVIEW')

if __name__ == '__main__': unittest.main()
