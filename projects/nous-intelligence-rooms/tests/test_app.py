import base64
import copy
import http.client
import io
import json
import pathlib
import socket
import sys
import threading
import unittest
import urllib.error
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
import server  # noqa: E402


def valid_payload(**overrides):
    payload = {
        "organization": "SERESARTE",
        "sector": "Creative & cultural organization",
        "goal": "Clarify positioning and priorities",
        "website": "https://seresarte.org",
        "context": "Public, user-owned strategic context for the curated demonstration.",
        "use_live": False,
        "files": [],
    }
    payload.update(overrides)
    return payload


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class AnalysisContractTests(unittest.TestCase):
    def test_demo_satisfies_full_local_schema(self):
        data = server.load_demo()
        self.assertIs(server.validate_analysis(data), data)
        self.assertEqual(set(server.SCHEMA["required"]), set(data))

    def test_scores_are_bounded(self):
        data = server.load_demo()
        scores = [data["overall_score"]]
        scores.extend(metric["score"] for metric in data["metrics"])
        scores.extend(signal["confidence"] for signal in data["signals"])
        scores.extend(decision["confidence"] for decision in data["decisions"])
        scores.extend(item["confidence"] for item in data["evidence"])
        for items in data["roadmap"].values():
            scores.extend(item["confidence"] for item in items)
        self.assertTrue(all(0 <= score <= 100 for score in scores))

    def test_every_recommendation_has_valid_evidence_refs(self):
        data = server.load_demo()
        evidence_ids = {item["id"] for item in data["evidence"]}
        items = [data["top_opportunity"], data["top_risk"]]
        items.extend(data["signals"])
        items.extend(data["decisions"])
        for phase in data["roadmap"].values():
            items.extend(phase)
        self.assertTrue(items)
        for item in items:
            self.assertTrue(item["evidence_refs"])
            self.assertTrue(set(item["evidence_refs"]) <= evidence_ids)
            self.assertIn("confidence", item)

    def test_unknown_evidence_reference_is_rejected(self):
        data = copy.deepcopy(server.load_demo())
        data["decisions"][0]["evidence_refs"] = ["E-999"]
        with self.assertRaises(server.AnalysisValidationError):
            server.validate_analysis(data)

    def test_unexpected_nested_field_is_rejected(self):
        data = copy.deepcopy(server.load_demo())
        data["meta"]["fallback_reason"] = "must not enter the strict contract"
        with self.assertRaises(server.AnalysisValidationError):
            server.validate_analysis(data)

    def test_non_sequential_decision_ranks_are_rejected(self):
        data = copy.deepcopy(server.load_demo())
        data["decisions"][1]["rank"] = 9
        with self.assertRaises(server.AnalysisValidationError):
            server.validate_analysis(data)

    def test_empty_sources_and_duplicate_refs_are_rejected(self):
        empty_source = copy.deepcopy(server.load_demo())
        empty_source["evidence"][0]["source"] = "  "
        with self.assertRaises(server.AnalysisValidationError):
            server.validate_analysis(empty_source)

        duplicate_refs = copy.deepcopy(server.load_demo())
        duplicate_refs["decisions"][0]["evidence_refs"] = ["E-01", "E-01"]
        with self.assertRaises(server.AnalysisValidationError):
            server.validate_analysis(duplicate_refs)


class InputValidationTests(unittest.TestCase):
    def test_generic_browser_mime_is_inferred_from_filename(self):
        payload = valid_payload(files=[{
            "name": "brief.pdf",
            "type": "application/octet-stream",
            "data": base64.b64encode(b"%PDF-1.7 audit").decode("ascii"),
        }])
        normalized = server.validate_payload(payload)
        self.assertEqual(normalized["files"][0]["mime"], "application/pdf")

    def test_invalid_base64_is_rejected(self):
        payload = valid_payload(files=[{"name": "brief.pdf", "type": "application/pdf", "data": "not base64!"}])
        with self.assertRaises(server.PublicError) as caught:
            server.validate_payload(payload)
        self.assertEqual(caught.exception.code, "invalid_base64")

    def test_mime_mismatch_is_rejected(self):
        payload = valid_payload(files=[{
            "name": "brief.pdf",
            "type": "image/png",
            "data": base64.b64encode(b"data").decode("ascii"),
        }])
        with self.assertRaises(server.PublicError) as caught:
            server.validate_payload(payload)
        self.assertEqual(caught.exception.code, "mime_mismatch")

    def test_unsupported_extension_is_rejected(self):
        payload = valid_payload(files=[{
            "name": "archive.zip",
            "type": "application/zip",
            "data": base64.b64encode(b"data").decode("ascii"),
        }])
        with self.assertRaises(server.PublicError) as caught:
            server.validate_payload(payload)
        self.assertEqual(caught.exception.code, "unsupported_file_type")

    def test_file_count_is_bounded(self):
        item = {"name": "note.txt", "type": "text/plain", "data": base64.b64encode(b"x").decode("ascii")}
        with self.assertRaises(server.PublicError) as caught:
            server.validate_payload(valid_payload(files=[item] * (server.MAX_FILES + 1)))
        self.assertEqual(caught.exception.code, "too_many_files")

    def test_decoded_file_size_is_bounded(self):
        payload = valid_payload(files=[{
            "name": "note.txt",
            "type": "text/plain",
            "data": base64.b64encode(b"1234").decode("ascii"),
        }])
        with mock.patch.object(server, "MAX_FILE_BYTES", 3):
            with self.assertRaises(server.PublicError) as caught:
                server.validate_payload(payload)
        self.assertEqual(caught.exception.code, "file_too_large")

    def test_payload_fields_are_typed_and_required(self):
        with self.assertRaises(server.PublicError):
            server.validate_payload(valid_payload(organization=[]))
        with self.assertRaises(server.PublicError):
            server.validate_payload(valid_payload(context=""))
        with self.assertRaises(server.PublicError):
            server.validate_payload(valid_payload(website="file:///etc/passwd"))


class ResponsesApiShapeTests(unittest.TestCase):
    def setUp(self):
        self.original_key = server.API_KEY
        server.API_KEY = "placeholder-not-a-real-key"

    def tearDown(self):
        server.API_KEY = self.original_key

    def _response_payload(self):
        return {
            "status": "completed",
            "output": [{
                "type": "message",
                "content": [{"type": "output_text", "text": json.dumps(server.load_demo())}],
            }],
        }

    def test_live_request_uses_responses_structured_outputs_and_store_false(self):
        captured = {}

        def fake_urlopen(request, timeout):
            captured["body"] = json.loads(request.data)
            captured["timeout"] = timeout
            return FakeResponse(self._response_payload())

        pdf_data = base64.b64encode(b"%PDF-1.7 audit").decode("ascii")
        payload = valid_payload(
            use_live=True,
            files=[{"name": "brief.pdf", "type": "application/pdf", "data": pdf_data}],
        )
        with mock.patch.object(server.urllib.request, "urlopen", side_effect=fake_urlopen):
            analysis = server.build_live_analysis(payload)

        body = captured["body"]
        self.assertEqual(body["model"], "gpt-5.6-terra")
        self.assertIs(body["store"], False)
        self.assertEqual(body["max_output_tokens"], 12000)
        self.assertEqual(body["reasoning"], {"effort": "medium"})
        self.assertEqual(body["text"]["format"]["type"], "json_schema")
        self.assertIs(body["text"]["format"]["strict"], True)
        self.assertEqual(body["text"]["format"]["schema"], server.SCHEMA)
        file_item = body["input"][0]["content"][1]
        self.assertEqual(file_item["type"], "input_file")
        self.assertEqual(file_item["file_data"], f"data:application/pdf;base64,{pdf_data}")
        self.assertEqual(analysis["meta"]["mode"], "live")
        self.assertEqual(analysis["meta"]["model"], "gpt-5.6-terra")

    def test_image_input_uses_a_valid_data_url(self):
        captured = {}

        def fake_urlopen(request, timeout):
            captured["body"] = json.loads(request.data)
            return FakeResponse(self._response_payload())

        image_data = base64.b64encode(b"fake-png").decode("ascii")
        payload = valid_payload(
            use_live=True,
            files=[{"name": "image.png", "type": "image/png", "data": image_data}],
        )
        with mock.patch.object(server.urllib.request, "urlopen", side_effect=fake_urlopen):
            server.build_live_analysis(payload)
        image_item = captured["body"]["input"][0]["content"][1]
        self.assertEqual(image_item["type"], "input_image")
        self.assertEqual(image_item["image_url"], f"data:image/png;base64,{image_data}")

    def test_refusal_is_explicit(self):
        response = {"output": [{"type": "message", "content": [{"type": "refusal", "refusal": "No"}]}]}
        with self.assertRaises(server.PublicError) as caught:
            server.extract_output_text(response)
        self.assertEqual(caught.exception.code, "analysis_refused")

    def test_invalid_live_output_is_not_returned(self):
        malformed = copy.deepcopy(server.load_demo())
        malformed["decisions"][0]["evidence_refs"] = ["E-404"]
        response = {
            "output": [{
                "type": "message",
                "content": [{"type": "output_text", "text": json.dumps(malformed)}],
            }],
        }
        with mock.patch.object(server.urllib.request, "urlopen", return_value=FakeResponse(response)):
            with self.assertRaises(server.PublicError) as caught:
                server.build_live_analysis(valid_payload(use_live=True))
        self.assertEqual(caught.exception.code, "invalid_model_response")

    def test_quota_error_is_safe_and_actionable(self):
        provider_error = urllib.error.HTTPError(
            "https://api.openai.com/v1/responses",
            429,
            "Too Many Requests",
            hdrs=None,
            fp=io.BytesIO(json.dumps({
                "error": {
                    "message": "private provider detail must not be returned",
                    "type": "insufficient_quota",
                    "code": "insufficient_quota",
                }
            }).encode("utf-8")),
        )
        with mock.patch.object(server.urllib.request, "urlopen", side_effect=provider_error):
            with self.assertRaises(server.PublicError) as caught:
                server.build_live_analysis(valid_payload(use_live=True))
        self.assertEqual(caught.exception.code, "openai_quota_exhausted")
        self.assertNotIn("private provider detail", caught.exception.message)


class HttpServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = server.ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.port = cls.httpd.server_address[1]
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.thread.join(timeout=2)

    def setUp(self):
        self.original_key = server.API_KEY
        server.API_KEY = ""

    def tearDown(self):
        server.API_KEY = self.original_key

    def request(self, method, path, body=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=3)
        connection.request(method, path, body=body, headers=headers or {})
        response = connection.getresponse()
        raw = response.read()
        result = (response.status, dict(response.getheaders()), raw)
        connection.close()
        return result

    def post_json(self, payload):
        body = json.dumps(payload).encode("utf-8")
        status, headers, raw = self.request(
            "POST", "/api/analyze", body,
            {"Content-Type": "application/json", "Content-Length": str(len(body))},
        )
        return status, headers, json.loads(raw)

    def test_health_reports_real_live_availability(self):
        status, headers, raw = self.request("GET", "/api/health")
        payload = json.loads(raw)
        self.assertEqual(status, 200)
        self.assertFalse(payload["live_available"])
        self.assertEqual(payload["model"], "gpt-5.6-terra")
        self.assertIn("store=false", payload["privacy"])
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
        self.assertIn("form-action 'self'", headers["Content-Security-Policy"])
        self.assertEqual(headers["Permissions-Policy"], "camera=(), microphone=(), geolocation=()")

    def test_demo_analysis_works_without_a_key(self):
        status, _, payload = self.post_json(valid_payload(
            organization="An unrelated organization",
            sector="Other",
            goal="A different decision",
        ))
        self.assertEqual(status, 200)
        self.assertEqual(payload["mode"], "demo")
        self.assertEqual(payload["analysis"]["organization"], "SERESARTE")
        self.assertEqual(payload["analysis"]["decision"], "Clarify positioning and priorities")

    def test_live_request_without_key_is_explicit_not_demo_fallback(self):
        status, _, payload = self.post_json(valid_payload(use_live=True))
        self.assertEqual(status, 503)
        self.assertEqual(payload["error"]["code"], "live_unavailable")
        self.assertNotIn("analysis", payload)

    def test_live_failure_is_explicit_and_public_error_is_safe(self):
        server.API_KEY = "placeholder-not-a-real-key"

        def fail(_payload):
            raise RuntimeError("sensitive provider diagnostics")

        with mock.patch.object(server, "_build_live_analysis", side_effect=fail):
            status, _, payload = self.post_json(valid_payload(use_live=True))
        self.assertEqual(status, 500)
        self.assertEqual(payload["error"]["code"], "internal_error")
        self.assertNotIn("sensitive", json.dumps(payload))
        self.assertNotIn("analysis", payload)

    def test_text_plain_json_is_rejected(self):
        body = json.dumps(valid_payload()).encode("utf-8")
        status, _, raw = self.request(
            "POST", "/api/analyze", body,
            {"Content-Type": "text/plain", "Content-Length": str(len(body))},
        )
        payload = json.loads(raw)
        self.assertEqual(status, 415)
        self.assertEqual(payload["error"]["code"], "unsupported_media_type")

    def test_raw_path_traversal_cannot_read_server_source(self):
        client = socket.create_connection(("127.0.0.1", self.port), timeout=3)
        try:
            client.sendall(
                b"GET /../server.py HTTP/1.1\r\n"
                b"Host: 127.0.0.1\r\n"
                b"Connection: close\r\n\r\n"
            )
            chunks = []
            while True:
                chunk = client.recv(65536)
                if not chunk:
                    break
                chunks.append(chunk)
        finally:
            client.close()
        raw = b"".join(chunks)
        self.assertIn(b" 404 ", raw.split(b"\r\n", 1)[0])
        self.assertNotIn(b"dependency-free demo and Responses API backend", raw)

    def test_encoded_static_path_traversal_cannot_read_server_source(self):
        status, _, raw = self.request("GET", "/static/%2e%2e/server.py")
        self.assertEqual(status, 404)
        self.assertNotIn(b"dependency-free demo and Responses API backend", raw)


if __name__ == "__main__":
    unittest.main()
