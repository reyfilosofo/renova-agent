"""Exercise real loopback HTTP and public-view compatibility without external scans."""
from __future__ import annotations

import http.client
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import threading
import time
import unittest
from datetime import datetime, timezone

from money_codex.server import MAX_BODY, create_server
from money_codex.runtime import Runtime
from money_codex.store import Store


class PublicStoreFixture:
    def __init__(self):
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self.export_calls = []
        self.sources = [{"source_id": "official", "config": {
            "name": "Fuente oficial", "enabled": True, "provider": "immunefi",
            "category": "BOUNTY", "url": "https://immunefi.com/bug-bounty/", "interval_seconds": 3600,
        }, "status": "FETCHED", "access_status": "ACCESS VERIFIED", "observed_at": now,
            "last_scan_at_utc": now, "account_id": "private-account"},
            {"source_id": "disabled", "config": {"enabled": False, "name": "Desactivada", "url": "https://example.com/"}}]
        self.rows = [{"opportunity_id": "public-1", "source_id": "official", "provider": "immunefi",
                      "title": '<img src=x onerror="window.injected=true">', "type": "BOUNTY",
                      "official_url": "javascript:alert(1)", "status": "WATCH", "classification": "WATCH",
                      "expected_net_value_usd": None, "gas_usd": None, "fees_usd": None,
                      "eligibility_status": "UNKNOWN", "last_verified_at_utc": now,
                      "evidence": ["https://immunefi.com/bug-bounty/"],
                      "source_evidence": {"url": "https://immunefi.com/bug-bounty/", "observed_at": now,
                                          "content_sha256": "a" * 64, "private_key": "never-export"},
                      "missing_data": ["reward_probability", "gas_usd", "eligibility_status"],
                      "wallet_address": "private-wallet", "api_secret": "never-export"}]

    def status(self):
        return {"mode": "READ_ONLY", "rail": "RESOURCES", "counts": {"opportunities": 1},
                "state_directory": "/private/path", "ledger_integrity": True}

    def opportunities(self, limit=100, classification=None, source_id=None):
        return [row for row in self.rows if (not classification or row["classification"] == classification)
                and (not source_id or row["source_id"] == source_id)][:limit]

    def list_sources(self):
        return self.sources

    def joblist(self, limit=100):
        return [{"id": "job-1", "source_id": "official", "state": "SUCCEEDED", "attempts": 1,
                 "created": 1791690000.0, "updated": 1791690030.0, "lease_owner": "private-worker",
                 "result": {"opportunities": 1}, "error": None}][:limit]

    def export_packet(self, now=None, persist=True):
        self.export_calls.append(persist)
        return {"schema_version": "2.1", "packet_id": "packet-1", "payload": {"mode": "READ_ONLY"}}


class RecordingRuntime:
    def __init__(self):
        self.calls = []

    def status(self):
        return {"scheduler": {"running": True, "source_count": 1}, "private_path": "/hidden"}

    def scan_now(self, source_ids=None, wait=False):
        self.calls.append((source_ids, wait))
        return {"state": "QUEUED", "job_ids": ["job-2"], "mode": "READ_ONLY"}


class ServerHTTPTests(unittest.TestCase):
    def setUp(self):
        self.store = PublicStoreFixture()
        self.runtime = RecordingRuntime()
        self.server = create_server(self.store, self.runtime, port=0)
        self.worker = threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": .01}, daemon=True)
        self.worker.start()
        self.origin = "http://127.0.0.1:" + str(self.server.server_port)

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.worker.join(timeout=2)

    def request(self, path, method="GET", body=None, headers=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        try:
            conn.request(method, path, body=body, headers=headers or {})
            response = conn.getresponse()
            payload = response.read()
            return response.status, dict(response.getheaders()), payload
        finally:
            conn.close()

    def post(self, body, headers=None):
        token = json.loads(self.request("/api/health")[2])["csrf_token"]
        supplied = {"Origin": self.origin, "X-Money-CSRF": token, "Content-Type": "application/json"}
        supplied.update(headers or {})
        raw = body if isinstance(body, bytes) else json.dumps(body).encode()
        return self.request("/api/scan", "POST", raw, supplied)

    def test_real_http_health_and_headers_are_scoped_to_research(self):
        status, headers, raw = self.request("/api/health")
        self.assertEqual(status, 200)
        data = json.loads(raw)
        self.assertEqual(data["mode"], "READ_ONLY")
        self.assertFalse(data["financial_execution"])
        self.assertFalse(data["direct_bot_connected"])
        self.assertIsNone(data["verified_income_usd"])
        self.assertEqual(data["recorded_income_usd"], 0)
        self.assertNotIn("private/path", raw.decode())
        self.assertNotIn("Access-Control-Allow-Origin", headers)
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")

    def test_source_config_is_flattened_and_disabled_source_remains_disabled(self):
        status, _, raw = self.request("/api/sources")
        self.assertEqual(status, 200)
        sources = json.loads(raw)["items"]
        self.assertEqual(sources[0]["name"], "Fuente oficial")
        self.assertTrue(sources[0]["enabled"])
        self.assertEqual(sources[0]["kind"], "BOUNTY")
        self.assertFalse(sources[1]["enabled"])
        self.assertNotIn("private-account", raw.decode())

    def test_jobs_are_ui_compatible_without_false_start_timestamp(self):
        data = json.loads(self.request("/api/jobs")[2])["items"][0]
        self.assertEqual(data["status"], "SUCCEEDED")
        self.assertEqual(data["job_id"], "job-1")
        self.assertEqual(data["source_ids"], ["official"])
        self.assertTrue(data["completed_at"].endswith("Z"))
        self.assertIsNone(data["started_at"])
        self.assertNotIn("lease_owner", data)

    def test_opportunity_unknowns_private_fields_and_url_safety(self):
        status, _, raw = self.request("/api/opportunities?source_id=official&classification=WATCH&limit=1")
        self.assertEqual(status, 200)
        row = json.loads(raw)["items"][0]
        self.assertIsNone(row["expected_net_value_usd"])
        self.assertIsNone(row["fees_usd"])
        self.assertIsNone(row["official_url"])
        self.assertEqual(row["eligibility_status"], "UNKNOWN")
        self.assertEqual(row["source_evidence"]["content_sha256"], "a" * 64)
        self.assertNotIn("never-export", raw.decode())
        self.assertNotIn("private-wallet", raw.decode())

    def test_nonpublic_and_credential_links_are_not_returned_as_official_urls(self):
        unsafe = [
            "https://127.1/", "https://0177.0.0.1/", "https://0x7f.0.0.1/",
            "https://example.com\t.evil.test/", "https://example.com\\@evil.test/",
            "https://example.com/?api-key=example", "https://example.com/?access_token=example",
            "https://example.com/?session-token=example", "https://example.com/?wallet_address=example",
            "https://example.com/?api_key=", "https://example.com/?session=example",
        ]
        for url in unsafe:
            with self.subTest(url=url):
                self.store.rows[0]["official_url"] = url
                self.store.rows[0]["source_evidence"]["observed_link"] = url
                status, _, raw = self.request("/api/opportunities")
                self.assertEqual(status, 200)
                row = json.loads(raw)["items"][0]
                self.assertIsNone(row["official_url"])
                self.assertIsNone(row["source_evidence"]["observed_link"])
        self.store.rows[0]["official_url"] = "https://immunefi.com/bug-bounty/?utm_source=money"
        row = json.loads(self.request("/api/opportunities")[2])["items"][0]
        self.assertEqual(row["official_url"], self.store.rows[0]["official_url"])

    def test_scan_enqueues_only_registered_sources_and_maps_batch(self):
        status, _, raw = self.post({"source_ids": ["official"]})
        self.assertEqual(status, 202)
        data = json.loads(raw)
        self.assertEqual(data["job"]["job_ids"], ["job-2"])
        self.assertEqual(data["job"]["status"], "QUEUED")
        self.assertEqual(data["job"]["source_ids"], ["official"])
        self.assertEqual(self.runtime.calls, [(["official"], False)])
        self.assertEqual(self.post({})[0], 202)
        self.assertEqual(self.runtime.calls[-1], (None, False))

    def test_scan_rejects_external_or_unconfigured_input_before_runtime(self):
        for payload in ({"url": "https://external.example/"}, {"source_ids": ["disabled"]},
                        {"source_ids": ["unknown"]}, {"source_ids": ["official", "official"]},
                        {"source_ids": []}, {"source_ids": ["https://localhost/"]},
                        {"source_ids": "official"}, {"permissions": {"buy": True}}):
            with self.subTest(payload=payload):
                self.assertEqual(self.post(payload)[0], 400)
        self.assertEqual(self.runtime.calls, [])

    def test_cooldown_reports_no_new_scan_without_accepted_job_status(self):
        self.runtime.scan_now = lambda **kwargs: {
            "state": "COOLDOWN", "job_ids": [], "mode": "READ_ONLY",
            "sources_in_cooldown": [{"source_id": "official", "retry_after_seconds": 59}],
        }
        status, _, raw = self.post({"source_ids": ["official"]})
        self.assertEqual(status, 200)
        job = json.loads(raw)["job"]
        self.assertEqual(job["status"], "COOLDOWN")
        self.assertEqual(job["job_ids"], [])
        self.assertEqual(job["sources_in_cooldown"], [{"source_id": "official", "retry_after_seconds": 59}])

    def test_csrf_origin_host_and_fetch_site_checks(self):
        token = json.loads(self.request("/api/health")[2])["csrf_token"]
        base = {"Origin": self.origin, "X-Money-CSRF": token, "Content-Type": "application/json"}
        for changes in ({"Origin": "https://evil.example"}, {"X-Money-CSRF": "invalid"},
                        {"Sec-Fetch-Site": "cross-site"}, {"Host": "evil.example"}):
            with self.subTest(changes=changes):
                self.assertEqual(self.request("/api/scan", "POST", b"{}", {**base, **changes})[0], 403)
        self.assertEqual(self.request("/api/scan", "POST", b"{}", {"X-Money-CSRF": token, "Content-Type": "application/json"})[0], 403)
        self.assertEqual(self.runtime.calls, [])

    def test_payload_bounds_duplicate_json_and_content_type(self):
        self.assertEqual(self.post(b"x" * (MAX_BODY + 1))[0], 413)
        self.assertEqual(self.post(b'{"source_ids":[],"source_ids":["official"]}')[0], 400)
        self.assertEqual(self.post(b"not-json")[0], 400)
        self.assertEqual(self.post({}, {"Content-Type": "text/plain"})[0], 415)
        self.assertEqual(self.runtime.calls, [])

    def test_nonascii_headers_and_deep_json_fail_without_disconnect_or_enqueue(self):
        self.assertEqual(self.post({}, {"X-Money-CSRF": "\N{LATIN SMALL LETTER E WITH ACUTE}"})[0], 403)
        self.assertEqual(self.post({}, {"Content-Length": "\N{SUPERSCRIPT TWO}"})[0], 411)
        nested = b'{"source_ids":' + b'[' * 1500 + b'0' + b']' * 1500 + b'}'
        self.assertLess(len(nested), MAX_BODY)
        self.assertEqual(self.post(nested)[0], 400)
        self.assertEqual(self.runtime.calls, [])

    def test_unknown_methods_filters_and_financial_routes_fail(self):
        for route in ("/api/buy", "/api/order", "/api/claim", "/api/wallet", "/api/import", "/api/secrets"):
            self.assertEqual(self.request(route)[0], 404)
        self.assertEqual(self.request("/api/health?x=1")[0], 400)
        self.assertEqual(self.request("/api/opportunities?limit=0")[0], 400)
        self.assertEqual(self.request("/api/jobs?limit=Infinity")[0], 400)
        self.assertEqual(self.request("/api/sources?path=../../secret")[0], 400)
        self.assertEqual(self.request("/api/opportunities?limit=1&limit=2")[0], 400)
        self.assertEqual(self.request("/api/scan", "DELETE")[0], 405)
        self.assertEqual(self.runtime.calls, [])

    def test_public_export_is_pure_and_rejects_private_packets(self):
        self.assertEqual(self.request("/api/export")[0], 200)
        self.assertEqual(self.store.export_calls, [False])
        self.store.export_packet = lambda **kwargs: {"payload": {"account_id": "private"}}
        status, _, raw = self.request("/api/export")
        self.assertEqual(status, 400)
        self.assertNotIn("private", raw.decode())

    def test_export_rejects_normalized_credentials_without_mutating_the_packet(self):
        packet = {"payload": {"official_url": "https://example.com/?access_token=example"}}
        self.store.export_packet = lambda **kwargs: packet
        status, _, raw = self.request("/api/export")
        self.assertEqual(status, 400)
        self.assertNotIn("access_token", raw.decode())
        self.assertEqual(packet["payload"]["official_url"], "https://example.com/?access_token=example")

    def test_html_content_security_policy_and_text_only_dom_rendering(self):
        status, headers, raw = self.request("/")
        self.assertEqual(status, 200)
        self.assertIn("sha256-", headers["Content-Security-Policy"])
        text = raw.decode()
        self.assertIn('<html lang="es">', text)
        self.assertIn("textContent", text)
        self.assertNotIn("innerHTML", text)
        self.assertNotIn("document.write", text)
        self.assertNotRegex(text, r"\beval\s*\(")

    def test_real_store_records_serve_without_unavailable_ui_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            store = Store(directory)
            store.register_sources([{"source_id": "real", "enabled": True, "name": "Fuente real", "category": "QUEST", "url": "https://zealy.io/"}])
            store.enqueue("real", "dedupe")
            self.store = store
            other = create_server(store, self.runtime, port=0)
            worker = threading.Thread(target=other.serve_forever, kwargs={"poll_interval": .01}, daemon=True)
            worker.start()
            try:
                connection = http.client.HTTPConnection("127.0.0.1", other.server_port)
                connection.request("GET", "/api/sources")
                response = connection.getresponse()
                sources = json.loads(response.read())["items"]
                self.assertTrue(sources[0]["enabled"])
                self.assertEqual(sources[0]["name"], "Fuente real")
                connection.close()
                before = store.status()["counts"].copy()
                connection = http.client.HTTPConnection("127.0.0.1", other.server_port)
                connection.request("GET", "/api/export")
                response = connection.getresponse()
                self.assertEqual(response.status, 200)
                response.read()
                connection.close()
                self.assertEqual(store.status()["counts"], before)
            finally:
                other.shutdown()
                other.server_close()
                worker.join(timeout=2)

    def test_real_scheduler_serves_queued_scan_completion_and_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            store = Store(directory)
            source = {"source_id": "official", "enabled": True, "name": "Fuente oficial", "category": "BOUNTY",
                      "url": "https://immunefi.com/bug-bounty/", "interval_seconds": 3600}
            calls = []

            def scan(config, now=None):
                calls.append(config["sources"][0]["source_id"])
                return {"source_status": [{"source_id": "official", "status": "FETCHED", "access_status": "ACCESS VERIFIED",
                                          "observed_at": now.isoformat().replace("+00:00", "Z"), "http_status": 200}], "opportunities": [], "evidence": []}

            runtime = Runtime({"sources": [source]}, store=store, scanner=scan)
            # The source is current for scheduled scans, while its manual cooldown has elapsed.
            store.save_scan({"source_status": [{"source_id": "official", "status": "FETCHED", "access_status": "ACCESS VERIFIED"}]}, now=time.time() - 120)
            other = create_server(store, runtime, port=0)
            worker = threading.Thread(target=other.serve_forever, kwargs={"poll_interval": .01}, daemon=True)
            worker.start()
            runtime.start_scheduler()
            try:
                connection = http.client.HTTPConnection("127.0.0.1", other.server_port, timeout=5)
                connection.request("GET", "/api/health")
                token = json.loads(connection.getresponse().read())["csrf_token"]
                connection.close()
                connection = http.client.HTTPConnection("127.0.0.1", other.server_port, timeout=5)
                connection.request("POST", "/api/scan", b'{"source_ids":["official"]}', {
                    "Content-Type": "application/json", "Origin": "http://127.0.0.1:" + str(other.server_port),
                    "X-Money-CSRF": token,
                })
                response = connection.getresponse()
                self.assertEqual(response.status, 202)
                job_ids = json.loads(response.read())["job"]["job_ids"]
                connection.close()
                deadline = time.monotonic() + 3
                while time.monotonic() < deadline:
                    jobs = store.joblist()
                    if jobs and all(job["state"] == "SUCCEEDED" for job in jobs if job["id"] in job_ids):
                        break
                    time.sleep(.01)
                self.assertEqual(calls, ["official"])
                self.assertTrue(store.verify_ledger())
                connection = http.client.HTTPConnection("127.0.0.1", other.server_port, timeout=5)
                connection.request("GET", "/api/jobs")
                job = json.loads(connection.getresponse().read())["items"][0]
                connection.close()
                self.assertEqual(job["status"], "SUCCEEDED")
                self.assertTrue(job["completed_at"].endswith("Z"))
                self.assertEqual(job["result"]["sources"], 1)
            finally:
                runtime.stop()
                other.shutdown()
                other.server_close()
                worker.join(timeout=2)


class DashboardValueTests(unittest.TestCase):
    """Run the dashboard's real pure functions without mocking their logic."""

    def run_javascript(self, assertions):
        node = shutil.which("node")
        if node is None:
            self.skipTest("Node required to exercise dashboard JavaScript")
        html = (Path(__file__).resolve().parents[1] / "web/index.html").read_text()
        script = re.search(r"<script>(.*?)</script>", html, re.S).group(1)
        # The declarations before officialLink don't access the DOM until called.
        pure = script[script.index("const $ ="):script.index("function officialLink")]
        pure += script[script.index("function sourceMatches"):script.index("function updateFilters")]
        result = subprocess.run([node, "-e", "const assert=require('node:assert/strict');\n" + pure + assertions],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_impossible_timestamps_are_unknown_not_normalized(self):
        self.run_javascript("""
          for(const value of ['2026-02-30T12:00:00Z','2026-04-31T12:00:00Z',
              '2026-10-15T24:00:00Z','2026-10-15T12:00:00',null,true]) {
            assert.equal(dateValue(value),null);
            assert.equal(dateText(value),'Desconocida');
          }
          assert.equal(dateValue('2024-02-29T12:00:00.123456Z'),Date.parse('2024-02-29T12:00:00.123456Z'));
          assert.equal(dateValue('2026-10-15T12:00:00-06:00'),Date.parse('2026-10-15T18:00:00Z'));
        """)

    def test_explicit_source_ids_win_and_ambiguous_provider_is_not_a_source(self):
        self.run_javascript("""
          state.sources=[{source_id:'A',provider:'Shared'},{source_id:'B',provider:'Shared'}];
          assert.equal(sourceMatches({source_id:'A',provider:'Shared'},'A'),true);
          assert.equal(sourceMatches({source_id:'A',provider:'Shared'},'B'),false);
          assert.equal(sourceMatches({provider:'Shared'},'B'),false);
          state.sources=[{source_id:'A',provider:'Unique'}];
          assert.equal(sourceMatches({provider:'Unique'},'A'),true);
        """)

    def test_origin_observation_never_fills_an_unknown_verification(self):
        self.run_javascript("""
          const stamp='2026-10-15T12:00:00Z';
          const item={last_verified_at_utc:null,observed_at:stamp};
          assert.equal(verifiedAt(item),null);
          assert.equal(observedAt(item),stamp);
          assert.equal(verifiedAt({observed_at:stamp}),null);
          assert.equal(observedAt({last_verified_at_utc:stamp}),null);
          assert.equal(observedAt({source_evidence:{observed_at:stamp},observed_at:'other'}),stamp);
          assert.equal(label('INELIGIBLE'),'No elegible');
          assert.equal(money(null),'Desconocido');
          assert.notEqual(money(0),'Desconocido');
        """)

    def test_links_reject_credentials_control_characters_and_loopback_aliases(self):
        self.run_javascript("""
          for(const value of ['https://127.1/','https://0177.0.0.1/','https://0x7f.0.0.1/',
              'https://example.org/?access_token=example','https://example.org/?api-key=example',
              'https://example.org/?session=example','https://example.org/?wallet_address=example',
              'https://example.org/?session_token=','https://service.internal/','javascript:alert(1)']) {
            assert.equal(safeURL(value),null);
          }
          assert.equal(safeURL('https://example.org/?utm_source=money').hostname,'example.org');
        """)


if __name__ == "__main__":
    unittest.main()
