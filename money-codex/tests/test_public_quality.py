from datetime import datetime, timezone
import unittest

import test_public_report as fixtures
from money_codex.public_report import make_public_report

NOW = datetime(2026, 10, 11, 18, tzinfo=timezone.utc)


class PublicQualityTests(unittest.TestCase):
    def store(self, row=None, src=None):
        return fixtures.PublicReportTests().store([row or fixtures.opportunity()], [src or fixtures.source()])

    def test_public_service_health_is_separate_from_personal_readiness(self):
        report = make_public_report(self.store(), now=NOW)
        self.assertEqual(report['quality']['status'], 'HEALTHY')
        self.assertEqual(report['quality']['fresh_verified_sources'], 1)
        self.assertEqual(report['quality']['decision_readiness'], 'DATA INSUFFICIENT')
        self.assertIsNone(report['verified_income_usd'])

    def test_stale_source_and_evidence_cannot_be_republished_as_fresh_watch(self):
        later = datetime(2026, 10, 13, tzinfo=timezone.utc)
        report = make_public_report(self.store(), now=later)
        self.assertEqual(report['sources'][0]['last_status'], 'ACCESS STALE')
        self.assertEqual(report['opportunities'][0]['classification'], 'DATA INSUFFICIENT')
        self.assertEqual(report['quality']['stale_or_undated_candidates'], 1)
        self.assertEqual(report['quality']['status'], 'DEGRADED')

    def test_future_proof_never_becomes_current_evidence(self):
        row, src = fixtures.opportunity(), fixtures.source()
        row['source_evidence']['observed_at'] = '2026-10-12T00:00:00Z'
        src['last_scan_at_utc'] = '2026-10-12T00:00:00Z'
        report = make_public_report(self.store(row, src), now=NOW)
        self.assertEqual(report['opportunities'][0]['evidence_freshness'], 'FUTURE')
        self.assertEqual(report['sources'][0]['last_status'], 'ACCESS UNAVAILABLE')
        self.assertEqual(report['queue_count'], 0)

    def test_announced_ceiling_does_not_fill_reward_probability_or_ev(self):
        row = fixtures.opportunity()
        row.update(advertised_max_reward_usd=1_000_000, verification_scope='PUBLIC_PROGRAM_TERMS_ONLY',
                   detail_status='ACTIVE', detail_verified_at_utc='2026-10-11T17:00:00Z')
        report = make_public_report(self.store(row), now=NOW)
        out = report['opportunities'][0]
        self.assertEqual(out['advertised_max_reward_usd'], 1_000_000)
        self.assertIsNone(out['expected_gross_reward_usd'])
        self.assertIsNone(out['reward_probability'])
        self.assertIsNone(out['expected_net_reward_usd'])
        self.assertEqual(report['quality']['detail_verified_candidates'], 1)

    def test_closed_candidate_stays_skipped_when_its_evidence_ages(self):
        row = fixtures.opportunity()
        row['classification'] = 'SKIP'
        report = make_public_report(self.store(row), now=datetime(2026, 10, 15, tzinfo=timezone.utc))
        self.assertEqual(report['opportunities'][0]['classification'], 'SKIP')


if __name__ == '__main__':
    unittest.main()
