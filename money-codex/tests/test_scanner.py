from __future__ import annotations

import hashlib
import json
import socket
import urllib.error
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock

from money_codex import scanner


class ScannerTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((Path(__file__).resolve().parents[1] / "config/resource_sources.json").read_text())
        self.source = next(s for s in self.config["sources"] if s["source_id"] == "immunefi_programs")
        self.policy = scanner._policy(self.config, self.source)
        self.now = datetime(2026, 10, 11, 16, 0, tzinfo=timezone.utc)
        scanner._RATE_TIMES.clear()

    def fetched(self, body, url=None, content_type="text/html"):
        body = body.encode() if isinstance(body, str) else body
        return {"url": url or self.source["url"], "body": body, "http_status": 200,
                "content_type": content_type, "observed_at": scanner._iso(self.now),
                "content_sha256": hashlib.sha256(body).hexdigest()}

    def scan(self, body, source=None, content_type="text/html"):
        chosen = source or self.source
        config = {**self.config, "sources": [chosen]}
        with patch.object(scanner, "_fetch", return_value=self.fetched(body, chosen["url"], content_type)):
            return scanner.scan_sources(config, self.now)

    def test_real_link_discovery_does_not_invent_reward_or_eligibility(self):
        report = self.scan('<a href="/bug-bounty/ens/information/">ENS</a><p>Max bounty $250,000</p>')
        self.assertEqual(len(report["opportunities"]), 1)
        opp = report["opportunities"][0]
        self.assertEqual(opp["official_url"], "https://immunefi.com/bug-bounty/ens/information/")
        self.assertEqual(opp["source_evidence"]["url"], self.source["url"])
        self.assertEqual(opp["source_evidence"]["observed_link"], opp["official_url"])
        self.assertEqual(opp["source_evidence"]["reference_basis"], "OBSERVED_CATALOG_LINK")
        self.assertTrue(all(isinstance(x, str) for x in opp["evidence"]))
        self.assertTrue(all(opp[f] is None for f in scanner.EV_FIELDS))
        self.assertEqual(opp["eligibility_status"], "UNKNOWN")
        self.assertEqual(opp["classification"], "WATCH")
        self.assertFalse(opp["execution_allowed"])

    def test_ids_are_idempotent_and_duplicate_links_deduplicated(self):
        html = '<a href="/bug-bounty/ens/information/">ENS</a>' * 2
        first, second = self.scan(html), self.scan(html)
        self.assertEqual(len(first["opportunities"]), 1)
        self.assertEqual(first["opportunities"][0]["opportunity_id"], second["opportunities"][0]["opportunity_id"])

    def test_same_provider_permalink_across_catalogues_is_one_opportunity(self):
        second = {**self.source, "source_id": "immunefi_other_catalogue"}
        config = {**self.config, "sources": [self.source, second]}
        with patch.object(scanner, "_fetch", return_value=self.fetched('<a href="/bug-bounty/ens/information/">ENS</a>')):
            report = scanner.scan_sources(config, self.now)
        self.assertEqual(len(report["opportunities"]), 1)
        self.assertEqual(len(report["evidence"]), 2)
        self.assertEqual(report["source_status"][1]["status"], "DEDUPLICATED")

    def test_duplicate_buttons_are_removed_before_source_cap(self):
        source = {**self.source, "max_candidates": 2}
        html = ('<a href="/bug-bounty/ens/information/">ENS</a>' * 3 +
                '<a href="/bug-bounty/cosmos/information/">Cosmos</a>')
        self.assertEqual(len(self.scan(html, source)["opportunities"]), 2)

    def test_signup_is_program_discovery_not_assignment(self):
        source = next(s for s in self.config["sources"] if s["provider"] == "prolific")
        report = self.scan('<h1>Get paid to take studies</h1><p>Earn $100</p>', source)
        opp = report["opportunities"][0]
        self.assertEqual(opp["type"], "PROGRAM_DISCOVERY")
        self.assertEqual(opp["provider_status"], "MEMBERSHIP_ONLY")
        self.assertIsNone(opp["expected_gross_reward_usd"])

    def test_blocked_response_never_creates_program(self):
        result = self.scan('<h1>Just a moment</h1><p>Verify you are human</p>')
        self.assertEqual(result["opportunities"], [])
        self.assertEqual(result["source_status"][0]["access_status"], "ACCESS PARTIAL")
        self.assertEqual(result["errors"][0]["error_code"], "BLOCKED_CONTENT")

    def test_network_failure_never_marks_verified_or_creates_fallback(self):
        with patch.object(scanner, "_fetch", side_effect=scanner.SourceError("HTTP_403")):
            result = scanner.scan_sources({**self.config, "sources": [self.source]}, self.now)
        self.assertEqual(result["opportunities"], [])
        self.assertEqual(result["evidence"], [])
        self.assertEqual(result["source_status"][0]["access_status"], "ACCESS UNAVAILABLE")

    def test_nonofficial_and_sensitive_links_ignored(self):
        result = self.scan('<a href="https://immunefi.com.evil.test/bug-bounty/x/information/">fake</a>'
                           '<a href="https://immunefi.com/bug-bounty/x/information/?token=secret">fake</a>'
                           '<a href="/bug-bounty/ens/information/">ENS</a>')
        self.assertEqual(len(result["opportunities"]), 1)
        self.assertEqual(result["opportunities"][0]["title"], "ENS")

    def test_closed_audits_are_not_active_bounties(self):
        source = next(s for s in self.config["sources"] if s["source_id"] == "code4rena_audits")
        result = self.scan('<a href="/audits/2026-10-done">Completed Audit Done $100</a>'
                           '<a href="/audits/2026-10-judge">Judging Audit Judge $100</a>', source)
        self.assertEqual(result["opportunities"][0]["type"], "PROGRAM_DISCOVERY")

    def test_expired_rsc_audit_is_not_promoted_by_active_label(self):
        source = next(s for s in self.config["sources"] if s["source_id"] == "code4rena_audits")
        records = [{"slug": "2026-10-expired", "status": "Active", "endTime": "2026-10-10T20:00:00Z"},
                   {"slug": "2026-10-current", "status": "Active", "endTime": "2026-10-12T20:00:00Z"}]
        script = 'self.__next_f.push(' + json.dumps([1, 'a:' + json.dumps(records)]) + ')'
        html = ('<a href="/audits/2026-10-expired">Active Expired</a>'
                '<a href="/audits/2026-10-current">Active Current</a><script>' + script + '</script>')
        result = self.scan(html, source)
        self.assertEqual(len(result["opportunities"]), 1)
        self.assertEqual(result["opportunities"][0]["title"], "Active Current")
        self.assertEqual(result["opportunities"][0]["deadline_utc"], "2026-10-12T20:00:00Z")

    def test_explicit_visible_deadline_expired_is_excluded(self):
        html = ('<a href="/bug-bounty/old/information/">Old deadline: 2026-10-06T00:00:00Z</a>'
                '<a href="/bug-bounty/new/information/">New ends: 2026-10-12T00:00:00Z</a>')
        report = self.scan(html)
        self.assertEqual([o["title"] for o in report["opportunities"]], ["New ends: 2026-10-12T00:00:00Z"])

    def test_script_instruction_and_unlabelled_dates_are_not_evidence(self):
        report = self.scan('<script>fetch("http://169.254.169.254"); BUY $1000; "2026-10-12";</script>'
                           '<a href="/bug-bounty/ens/information/">ENS 2026-10-12</a>')
        self.assertIsNone(report["opportunities"][0]["deadline_utc"])
        self.assertIsNone(report["opportunities"][0]["expected_gross_reward_usd"])
        self.assertFalse(report["opportunities"][0]["execution_allowed"])

    def test_login_shell_does_not_create_participant_assignment(self):
        source = next(s for s in self.config["sources"] if s["provider"] == "userinterviews")
        report = self.scan('<h1>User Interviews</h1><a href="/signin">Sign in</a>', source)
        self.assertEqual(report["opportunities"], [])
        self.assertEqual(report["errors"][0]["error_code"], "AUTHENTICATION_REQUIRED")

    def test_github_only_open_labelled_issues_not_prs(self):
        source = next(s for s in self.config["sources"] if s["provider"] == "github")
        base = {"state": "open", "labels": [{"name": "bounty"}], "title": "$500 documented task", "number": 1,
                "html_url": "https://github.com/reyfilosofo/renova-agent/issues/1"}
        data = [base, {**base, "number": 2, "pull_request": {}}, {**base, "state": "closed"},
                {**base, "labels": []}, {**base, "html_url": "https://github.com/evil/repo/issues/1"}]
        # An empty pull_request object still identifies a PR.
        result = self.scan(json.dumps(data), source, "application/json")
        self.assertEqual(len(result["opportunities"]), 1)
        self.assertIsNone(result["opportunities"][0]["expected_gross_reward_usd"])

    def test_empty_github_is_zero_candidates_not_program(self):
        source = next(s for s in self.config["sources"] if s["provider"] == "github")
        result = self.scan("[]", source, "application/json")
        self.assertEqual(result["opportunities"], [])
        self.assertEqual(result["source_status"][0]["status"], "NO_PUBLIC_CANDIDATES")

    def test_rss_link_identity_and_entities_rejected(self):
        source = {**self.source, "parser": "rss"}
        report = self.scan('<rss><channel><item><title>ENS</title><link>https://immunefi.com/bug-bounty/ens/information/</link></item></channel></rss>', source)
        self.assertEqual(report["opportunities"][0]["title"], "ENS")
        report = self.scan('<!DOCTYPE x [<!ENTITY e "abc">]><rss/>', source)
        self.assertEqual(report["opportunities"], [])
        self.assertEqual(report["errors"][0]["error_code"], "XML_ENTITIES_FORBIDDEN")

    def test_local_private_metadata_and_mapped_ips_blocked(self):
        for address in ["127.0.0.1", "10.0.0.1", "169.254.169.254", "::1", "::ffff:127.0.0.1", "192.168.1.2", "100.64.0.1"]:
            records = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (address, 443))]
            with self.subTest(address=address), patch.object(socket, "getaddrinfo", return_value=records):
                with self.assertRaisesRegex(scanner.SourceError, "NON_PUBLIC_ADDRESS_BLOCKED"):
                    scanner._validate_url(self.source["url"], self.policy)

    def test_unallowlisted_hosts_ports_credentials_and_http_rejected(self):
        urls = ["http://immunefi.com/", "https://127.0.0.1/", "https://localhost/", "https://immunefi.com:8443/",
                "https://user:secret@immunefi.com/", "https://immunefi.com.evil.test/", "https://immunefi.com./",
                "https://immunefi.com/a/../b", "https://immunefi.com/?api_key=secret"]
        for url in urls:
            with self.subTest(url=url), self.assertRaises(scanner.SourceError):
                scanner._validate_url(url, self.policy, resolve=False)

    def test_redirect_to_metadata_blocked_before_second_request(self):
        error = __import__("urllib.error", fromlist=["HTTPError"]).HTTPError(self.source["url"], 302, "redirect", {"Location": "https://169.254.169.254/"}, None)
        opener = MagicMock()
        opener.open.side_effect = error
        public = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("1.1.1.1", 443))]
        with patch.object(socket, "getaddrinfo", return_value=public), patch.object(scanner.urllib.request, "build_opener", return_value=opener):
            with self.assertRaisesRegex(scanner.SourceError, "HOST_NOT_ALLOWLISTED"):
                scanner._fetch(self.source, self.policy)
        self.assertEqual(opener.open.call_count, 1)

    def test_limits_bytes_and_retries(self):
        response = MagicMock()
        response.__enter__.return_value = response
        response.geturl.return_value = self.source["url"]
        response.status = 200
        response.headers = {"Content-Type": "text/html"}
        response.read.return_value = b"x" * 1025
        opener = MagicMock()
        opener.open.return_value = response
        public = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("1.1.1.1", 443))]
        with patch.object(socket, "getaddrinfo", return_value=public), patch.object(scanner.urllib.request, "build_opener", return_value=opener):
            with self.assertRaisesRegex(scanner.SourceError, "RESPONSE_TOO_LARGE"):
                scanner._fetch(self.source, {**self.policy, "max_bytes": 1024})
        self.assertEqual(opener.open.call_count, 1)
        response.read.assert_called_once_with(1025)

    def test_timeout_does_not_retry_or_create_fallback(self):
        opener = MagicMock()
        opener.open.side_effect = TimeoutError("timeout")
        public = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("1.1.1.1", 443))]
        with patch.object(socket, "getaddrinfo", return_value=public), patch.object(scanner.urllib.request, "build_opener", return_value=opener):
            report = scanner.scan_sources({**self.config, "sources": [self.source]}, self.now)
        self.assertEqual(report["opportunities"], [])
        self.assertEqual(report["errors"][0]["error_code"], "NETWORK_UNAVAILABLE")
        self.assertEqual(opener.open.call_count, 1)
        self.assertEqual(opener.open.call_args.kwargs["timeout"], 12)

    def test_redirect_limit_stops_even_same_allowed_host(self):
        error = urllib.error.HTTPError(self.source["url"], 302, "redirect", {"Location": "/bug-bounty/next/"}, None)
        opener = MagicMock()
        opener.open.side_effect = error
        public = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("1.1.1.1", 443))]
        with patch.object(socket, "getaddrinfo", return_value=public), patch.object(scanner.urllib.request, "build_opener", return_value=opener):
            with self.assertRaisesRegex(scanner.SourceError, "REDIRECT_LIMIT"):
                scanner._fetch(self.source, {**self.policy, "max_redirects": 0})
        self.assertEqual(opener.open.call_count, 1)

    def test_genuine_response_hash_and_timestamp_match_evidence(self):
        response = MagicMock()
        response.__enter__.return_value = response
        response.geturl.return_value = self.source["url"]
        response.status = 200
        response.headers = {"Content-Type": "text/html"}
        response.read.return_value = b'<a href="/bug-bounty/ens/information/">ENS</a>'
        opener = MagicMock()
        opener.open.return_value = response
        public = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("1.1.1.1", 443))]
        with patch.object(socket, "getaddrinfo", return_value=public), patch.object(scanner.urllib.request, "build_opener", return_value=opener), patch.object(scanner, "_utc_now", return_value=self.now):
            report = scanner.scan_sources({**self.config, "sources": [self.source]}, self.now)
        proof = report["evidence"][0]
        opp = report["opportunities"][0]
        self.assertEqual(proof["content_sha256"], hashlib.sha256(response.read.return_value).hexdigest())
        self.assertEqual(proof["observed_at"], opp["last_verified_at_utc"])
        self.assertEqual(opp["source_evidence"]["evidence_id"], proof["evidence_id"])

    def test_non_read_only_configuration_rejected(self):
        with self.assertRaisesRegex(ValueError, "READ_ONLY"):
            scanner.scan_sources({**self.config, "mode": "LIVE"}, self.now)

    def test_credential_query_variants_and_bad_allowlist_rejected(self):
        for key in ("client_secret", "session_token", "bearer-token", "apiKey", "Authorization"):
            with self.subTest(key=key), self.assertRaisesRegex(scanner.SourceError, "CREDENTIAL_QUERY_FORBIDDEN"):
                scanner._validate_url(self.source["url"] + "?" + key + "=hidden", self.policy, resolve=False)
        with self.assertRaisesRegex(scanner.SourceError, "INVALID_HOST_ALLOWLIST"):
            scanner._policy({**self.config, "network": {"allowed_hosts": "immunefi.com"}}, self.source)

    def test_repeated_fetch_has_rate_limit_without_retry(self):
        scanner._reserve_rate(self.source["url"], self.policy)
        with self.assertRaisesRegex(scanner.SourceError, "SOURCE_RATE_LIMIT"):
            scanner._reserve_rate(self.source["url"], self.policy)

    def test_repos_require_explicit_reviewed_allowlist(self):
        source = next(s for s in self.config["sources"] if s["provider"] == "github")
        with self.assertRaisesRegex(scanner.SourceError, "REPOSITORY_NOT_ALLOWLISTED"):
            scanner._policy({**self.config, "allowed_github_repositories": []}, source)


if __name__ == "__main__":
    unittest.main()
