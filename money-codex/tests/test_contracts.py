import unittest
from datetime import datetime, timezone
from money_codex.contracts import compare_contracts

class ContractTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 8, 18, 2, tzinfo=timezone.utc)
        self.row = dict(asset="BTC", quote_currency="USD", window_start_utc="2026-10-08T18:00:00Z",
                        window_end_utc="2026-10-08T18:05:00Z", condition="UP_DOWN", option="UP",
                        tie_rule="UP_ON_EQUAL", reference=63000, resolution_source="oracle-a",
                        settlement_method="cash", price_kind="executable_offer", fees=0.01,
                        spread=0.02, slippage=0.01, liquidity=1000, pmarket=70,
                        quote_at_utc="2026-10-08T18:01:55Z", received_at_utc="2026-10-08T18:01:58Z")
    def test_70_59_is_only_descriptive(self):
        result=compare_contracts(self.row,dict(self.row,pmarket=59),self.now)
        self.assertEqual(result['classification'],'WATCH')
        self.assertEqual(result['divergence_pp'],11)
    def test_different_reference_blocks_gap(self):
        result=compare_contracts(self.row,dict(self.row,reference=64000,pmarket=59),self.now)
        self.assertEqual(result['classification'],'CONTRACT MISMATCH')
        self.assertIsNone(result['divergence_pp'])
    def test_no_tick_and_unknown_fees_propagate(self):
        result=compare_contracts(dict(self.row,quote_at_utc=None),dict(self.row,fees=None),self.now)
        self.assertEqual(result['classification'],'DATA INSUFFICIENT')
        self.assertIsNone(result['divergence_pp'])
    def test_different_currency(self):
        self.assertEqual(compare_contracts(self.row,dict(self.row,quote_currency='USDT'),self.now)['classification'],'CONTRACT MISMATCH')
    def test_expired_window(self):
        self.assertEqual(compare_contracts(self.row,self.row,datetime(2026,10,8,18,6,tzinfo=timezone.utc))['classification'],'DATA INSUFFICIENT')

if __name__ == '__main__':
    unittest.main()
