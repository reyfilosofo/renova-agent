"""Safe, deterministic FED-22 offline tests; no provider API calls."""
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
import relay

def sample():
    n=datetime.now(timezone.utc)
    return dict(packet_id="FED22-TEST-0001",schema_version="2.2",
        created_at=n.isoformat(),expires_at=(n+timedelta(hours=3)).isoformat(),
        source_node="CENTRO",target_node="GEMINI",project_id=relay.PROJECT,
        data_classification="PUBLIC",mission="Analyze public safety evidence and counterevidence",
        requested_operation="REVIEW",source_refs=["https://github.com/reyfilosofo/renova-agent"],
        state="PREPARED",provider_receipt_id=None,readback_verified=False)

class Guard(unittest.TestCase):
    def test_valid(self):self.assertEqual(relay.check(sample()),[])
    def test_missing(self):p=sample();p.pop("mission");self.assertTrue(relay.check(p))
    def test_extra(self):p=sample();p["secret"]="not-allowed";self.assertTrue(relay.check(p))
    def test_short_id(self):p=sample();p["packet_id"]="a";self.assertTrue(relay.check(p))
    def test_bad_project(self):p=sample();p["project_id"]="OTHER";self.assertTrue(relay.check(p))
    def test_bad_schema(self):p=sample();p["schema_version"]="3";self.assertTrue(relay.check(p))
    def test_bad_op(self):p=sample();p["requested_operation"]="DELETE";self.assertTrue(relay.check(p))
    def test_bad_refs(self):p=sample();p["source_refs"]=["file:///etc/passwd"];self.assertTrue(relay.check(p))
    def test_public_domain(self):p=sample();p["source_refs"]=["https://evil.test/private"];self.assertTrue(relay.check(p))
    def test_expired(self):
        p=sample();n=datetime.now(timezone.utc)-timedelta(days=2)
        p.update(created_at=n.isoformat(),expires_at=(n+timedelta(hours=2)).isoformat())
        self.assertTrue(relay.check(p))
    def test_too_long(self):
        p=sample();p["expires_at"]=(datetime.now(timezone.utc)+timedelta(days=3)).isoformat()
        self.assertTrue(relay.check(p))
    def test_future(self):
        p=sample();n=datetime.now(timezone.utc)+timedelta(hours=2)
        p.update(created_at=n.isoformat(),expires_at=(n+timedelta(hours=1)).isoformat())
        self.assertTrue(relay.check(p))
    def test_fake_ack(self):p=sample();p["state"]="ACKNOWLEDGED";self.assertTrue(relay.check(p))
    def test_fake_prep_receipt(self):p=sample();p["provider_receipt_id"]="fake";self.assertTrue(relay.check(p))
    def test_private_is_structurally_valid_not_send_authorized(self):
        p=sample();p["data_classification"]="CONFIDENTIAL";self.assertEqual(relay.check(p),[])
    def test_offline_stage(self):
        with tempfile.TemporaryDirectory() as d:
            v=relay.stage(sample(),Path(d)/"x.sqlite")
            self.assertFalse(v["provider_sent"]);self.assertEqual(v["status"],"STAGED_OFFLINE")
    def test_replay(self):
        with tempfile.TemporaryDirectory() as d:
            l=Path(d)/"x.sqlite";relay.stage(sample(),l)
            with self.assertRaisesRegex(ValueError,"replay"):relay.stage(sample(),l)
    def test_reject_ack_stage(self):
        with tempfile.TemporaryDirectory() as d:
            p=sample();p.update(state="ACKNOWLEDGED",provider_receipt_id="fake",readback_verified=True)
            with self.assertRaisesRegex(ValueError,"PREPARED"):relay.stage(p,Path(d)/"x.sqlite")
    def test_no_secrets_required(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(relay.stage(sample(),Path(d)/"x.sqlite")["provider_sent"],False)
    def test_canonical_digest(self):
        with tempfile.TemporaryDirectory() as d:
            a=relay.stage(sample(),Path(d)/"x.sqlite")
            self.assertEqual(len(a["sha256"]),64)
if __name__=="__main__":unittest.main()
