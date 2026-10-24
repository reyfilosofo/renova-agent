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

    def test_malformed_identity_cannot_be_equivalent_even_when_both_rows_match(self):
        for key, value in [('asset', []), ('quote_currency', True), ('condition', {}), ('option', ''),
                           ('tie_rule', ' '), ('resolution_source', 0), ('settlement_method', []),
                           ('reference', True), ('reference', 0), ('reference', '63000'),
                           ('reference', float('nan')), ('reference', 10**1000)]:
            malformed = {**self.row, key: value}
            with self.subTest(key=key, value_type=type(value).__name__):
                result = compare_contracts(malformed, malformed, self.now)
                self.assertEqual(result['classification'], 'DATA INSUFFICIENT')
                self.assertFalse(result['equivalent'])
                self.assertIsNone(result['divergence_pp'])

    def test_same_invalid_window_is_not_an_equivalent_contract(self):
        for start, end in [('2026-10-08T18:05:00Z', '2026-10-08T18:00:00Z'),
                           ('2026-10-08T18:00:00Z', '2026-10-08T18:00:00Z'),
                           ('9999-12-31T23:59:59-01:00', self.row['window_end_utc'])]:
            data = {**self.row, 'window_start_utc': start, 'window_end_utc': end}
            result = compare_contracts(data, data, self.now)
            self.assertEqual(result['classification'], 'DATA INSUFFICIENT')
            self.assertFalse(result['equivalent'])

    def test_huge_numbers_and_invalid_clock_do_not_escape_validation(self):
        for key in ('fees', 'spread', 'slippage', 'liquidity', 'pmarket'):
            data = {**self.row, key: 10**1000}
            result = compare_contracts(data, self.row, self.now)
            self.assertEqual(result['classification'], 'DATA INSUFFICIENT')
            self.assertIsNone(result['divergence_pp'])
        for clock in (0, False, 'not-a-clock', self.now.replace(tzinfo=None)):
            result = compare_contracts(self.row, self.row, clock)
            self.assertEqual(result['classification'], 'DATA INSUFFICIENT')
            self.assertFalse(result['equivalent'])

    def test_timezone_offsets_compare_the_same_instants_without_normalizing_odds(self):
        right = {**self.row, 'pmarket': 59, 'window_start_utc': '2026-10-08T12:00:00-06:00',
                 'window_end_utc': '2026-10-08T12:05:00-06:00'}
        result = compare_contracts(self.row, right, self.now)
        self.assertEqual(result['classification'], 'WATCH')
        self.assertTrue(result['equivalent'])
        self.assertEqual(result['divergence_pp'], 11)

if __name__ == '__main__':
    unittest.main()
