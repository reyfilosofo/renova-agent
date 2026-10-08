"""Safe unit tests; no network and no real applicant data."""
import unittest
from career_os import assess, canonical

FIXTURE = {
  "company":"SAMPLE - FICTIONAL", "role":"Partnerships Lead",
  "requisition_id":"FAKE-1", "official_url":"https://example.invalid/job/1?utm_source=sample",
  "active":True, "employer_verified":True, "remote_mexico":True,
  "guaranteed_published_base_mxn_month":60000,
  "salary_source":"FICTIONAL TEST ONLY", "source_timestamp":"2026-10-08",
  "must_haves":["partnerships","negotiation"],
  "reviewed_evidence_tags":["partnerships","negotiation"]
}

class PolicyTests(unittest.TestCase):
    def test_canonical(self):
        self.assertEqual(canonical(FIXTURE["official_url"]), "https://example.invalid/job/1")

    def test_eligible(self):
        self.assertEqual(assess(FIXTURE)["status"], "ELIGIBLE_FOR_REVIEW")

    def test_salary_floor(self):
        job = {**FIXTURE,"guaranteed_published_base_mxn_month":40000}
        self.assertEqual(assess(job)["status"], "PENDING_VERIFICATION")

    def test_missing_hard_skill(self):
        job = {**FIXTURE,"reviewed_evidence_tags":["partnerships"]}
        self.assertEqual(assess(job)["status"], "GAP_REVIEW")

    def test_no_fake_100(self):
        job = {**FIXTURE,"active":False}
        self.assertNotEqual(assess(job)["status"], "ELIGIBLE_FOR_REVIEW")

if __name__ == "__main__":
    unittest.main()
