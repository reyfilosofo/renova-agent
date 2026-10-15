"""Tests for education only, not a threat-model or real security audit."""
import unittest
from policy_demo import v01, v02, CASES

class DemoTests(unittest.TestCase):
    def test_v01_challenges_find_discrepancies(self):
        self.assertGreater(sum(v01(c) != c["expected"] for c in CASES),0)
    def test_v02_matches_author_defined_probes(self):
        self.assertEqual(sum(v02(c) != c["expected"] for c in CASES),0)
    def test_tool_text_cannot_authorize_publish(self):
        c=dict(operation="publish",authorized=True,sensitive=False,irreversible=False,
               high_stakes=False,sufficient_evidence=True,origin="untrusted_tool_text")
        self.assertEqual(v02(c),"BLOCK")

if __name__=="__main__":
    unittest.main()
