"""Loopback dashboard for the MONEY resource research rail.

The only HTTP mutation enqueues configured public-source scans. There is no
account, wallet, financial execution, import, or filesystem API.
"""
from __future__ import annotations

import hashlib
import ipaddress
import json
import math
import re
import secrets
import socket
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit


MAX_BODY = 8192
MAX_RESPONSE = 2_000_000
ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,99}$")
PRIVATE_KEYS = {
    "seed_phrase", "private_key", "api_key", "api_secret", "password",
    "recovery_phrase", "recovery_code", "session_token", "session_cookie",
    "bearer_token", "oauth_refresh_token", "authorization", "cookie",
    "wallet_address", "account_id", "account_scope", "email", "user_id",
    "balances", "positions", "orders", "fills", "portfolio", "personal_profile",
}
OPPORTUNITY_FIELDS = {
    "schema_version", "opportunity_id", "source_id", "source_ids", "name", "title",
    "provider", "type", "status", "classification", "official_url", "geography",
    "deadline_utc", "opened_at_utc", "last_verified_at_utc", "last_seen_at_utc",
    "created_at_utc", "updated_at_utc", "eligibility_basis", "eligibility_status",
    "wallet_network", "kyc_required", "required_capital_usd", "fees_usd",
    "time_cost_minutes", "expected_gross_reward_usd", "reward_probability",
    "expected_net_value_usd", "expected_net_value", "gas_usd", "platform_fees_usd",
    "required_spend_usd", "time_cost_usd", "security_risk_cost_usd",
    "capital_lockup_cost_usd", "expected_loss_usd", "security_risk", "tos_status",
    "repeatability", "invalidation", "evidence", "evidence_ids", "notes", "reason",
    "required_actions", "irreversible_actions", "manual_action_required",
    "costs", "ev", "evaluation", "deadline_status", "receipt_id", "origin",
    "source_evidence", "expected_net_reward_usd", "missing_data",
    "blocking_reasons", "discovery_only", "provider_status", "next_action",
    "evaluated_at_utc", "execution_authority", "execution_allowed",
}
SOURCE_FIELDS = {
    "id", "source_id", "name", "provider", "url", "official_url", "type", "kind",
    "enabled", "status", "access_state", "last_verified_at_utc", "last_scan_at_utc",
    "last_checked_at_utc", "last_attempt_at_utc", "last_received_at_utc", "last_error",
    "last_status", "note", "notes", "classification", "interval_seconds",
    "http_status", "receipt_id", "evidence_id", "observed_at_utc",
    "access_status", "category", "parser", "last_verified_at", "observed_at",
    "candidate_count", "retry_after_seconds",
}
JOB_FIELDS = {
    "id", "job_id", "source_id", "source_ids", "state", "status", "attempts",
    "due", "created", "updated", "created_at", "started_at", "completed_at",
    "created_at_utc", "started_at_utc", "completed_at_utc", "error", "result",
}


def _utc_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _plain(value, depth=0):
    """Bound public metadata, omit private fields, preserve unknown numeric values."""
    if depth > 8:
        return None
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value if math.isfinite(value) else None
    if isinstance(value, str):
        return value[:6000]
    if isinstance(value, dict):
        return {str(key): _plain(item, depth + 1) for key, item in value.items()
                if isinstance(key, str) and key.lower() not in PRIVATE_KEYS}
    if isinstance(value, (list, tuple)):
        return [_plain(item, depth + 1) for item in value[:500]]
    return None


def _url(value):
    if (not isinstance(value, str) or len(value) > 2000
            or re.search(r"[\s\\\x00-\x1f\x7f]", value)):
        return None
    try:
        url = urlsplit(value)
        # Treat common spelling variants alike, including blank query values.
        keys = {re.sub(r"[^a-z0-9]", "", key.casefold())
                for key in parse_qs(url.query, keep_blank_values=True, max_num_fields=100)}
        private = {re.sub(r"[^a-z0-9]", "", key) for key in PRIVATE_KEYS}
        private.update({"token", "key", "wallet", "account", "secret", "session",
                        "accesstoken", "refreshtoken", "apitoken", "authtoken", "clientsecret"})
        if (url.scheme != "https" or not url.hostname or url.username is not None or url.password is not None
                or url.port not in (None, 443) or url.fragment
                or keys & private):
            return None
        host = url.hostname.lower()
        if host == "localhost" or host.endswith((".localhost", ".local", ".internal")) or host.endswith("."):
            return None
        try:
            address = ipaddress.ip_address(host)
        except ValueError:
            # Browsers also interpret inet-style IPv4 (127.1, octal and hex).
            # inet_aton parses literals only; it performs no DNS/network lookup.
            try:
                address = ipaddress.IPv4Address(socket.inet_aton(host))
            except OSError:
                address = None
            if (address is not None and not address.is_global) or "." not in host:
                return None
        else:
            if not address.is_global:
                return None
    except ValueError:
        return None
    return value


def _view(record, fields):
    if not isinstance(record, dict):
        return {}
    result = _plain({key: item for key, item in record.items() if key in fields})
    for key in ("url", "official_url"):
        if key in result:
            result[key] = _url(result[key])
    return result


def _iso_time(value):
    """Present stored UNIX timestamps without inventing an observation time."""
    if value is None or isinstance(value, bool):
        return None
    try:
        if isinstance(value, str):
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                return None
        elif isinstance(value, (int, float)) and math.isfinite(value):
            parsed = datetime.fromtimestamp(value, timezone.utc)
        else:
            return None
        return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    except (ValueError, OverflowError, OSError):
        return None


def _source_view(record):
    if not isinstance(record, dict):
        return {}
    config = record.get("config") if isinstance(record.get("config"), dict) else {}
    result = _view({**config, **record}, SOURCE_FIELDS)
    # Match the runtime default; a malformed truthy string is never enabled.
    result["enabled"] = config.get("enabled", record.get("enabled", True)) is True
    result.setdefault("name", result.get("source_id"))
    result.setdefault("kind", result.get("category"))
    result.setdefault("access_status", record.get("access_state", "ACCESS UNAVAILABLE"))
    return result


def _job_view(record):
    result = _view(record, JOB_FIELDS)
    result["job_id"] = result.get("job_id", result.get("id"))
    result["status"] = result.get("status", result.get("state", "UNKNOWN"))
    result["created_at"] = _iso_time(record.get("created_at", record.get("created")))
    result["updated_at"] = _iso_time(record.get("updated_at", record.get("updated")))
    result["started_at"] = _iso_time(record.get("started_at"))
    result["completed_at"] = _iso_time(record.get("completed_at", record.get("updated"))) if result["status"] in {"SUCCEEDED", "FAILED", "COMPLETED"} else None
    result["source_ids"] = result.get("source_ids") or ([result["source_id"]] if result.get("source_id") else [])
    return result


def _opportunity_view(record):
    result = _view(record, OPPORTUNITY_FIELDS)
    proof = record.get("source_evidence")
    if isinstance(proof, dict):
        result["source_evidence"] = _view(proof, {
            "url", "observed_link", "observed_at", "content_sha256", "reference_basis",
            "source_id", "http_status", "observed_at_utc",
        })
        if "observed_link" in result["source_evidence"]:
            result["source_evidence"]["observed_link"] = _url(result["source_evidence"]["observed_link"])
    return result


def _assert_public_packet(value, depth=0):
    """Reject unsafe exports rather than alter a packet's checksum/provenance."""
    if depth == 0:
        from .packets import assert_no_secret_keys
        assert_no_secret_keys(value)
    if depth > 16:
        raise ValueError("Packet nesting exceeds limit")
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str) or key.lower() in PRIVATE_KEYS:
                raise ValueError("Packet contains private fields")
            _assert_public_packet(item, depth + 1)
    elif isinstance(value, list):
        if len(value) > 2000:
            raise ValueError("Packet list exceeds limit")
        for item in value:
            _assert_public_packet(item, depth + 1)
    elif isinstance(value, str):
        if len(value) > 10000:
            raise ValueError("Packet text exceeds limit")
    elif isinstance(value, (int, float)) and not math.isfinite(value):
        raise ValueError("Packet contains non-finite number")


def _json_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON field")
        result[key] = value
    return result


class ResourceServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def create_server(store, runtime, host="127.0.0.1", port=8787):
    if host != "127.0.0.1":
        raise ValueError("El panel de recursos debe escuchar en 127.0.0.1")
    if isinstance(port, bool) or not isinstance(port, int) or not 0 <= port <= 65535:
        raise ValueError("Puerto local inválido")

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"
        server_version = "MONEYResource/1.0"
        sys_version = ""

        def setup(self):
            super().setup()
            self.connection.settimeout(5)

        def log_message(self, format, *args):
            # Never echo user supplied URLs, bodies, tokens or account identifiers.
            return

        def _send(self, status, data, content_type="application/json; charset=utf-8", headers=None):
            encoded = data if isinstance(data, bytes) else json.dumps(
                data, ensure_ascii=False, allow_nan=False, separators=(",", ":")
            ).encode("utf-8")
            if len(encoded) > MAX_RESPONSE:
                status, encoded = 413, b'{"error":"La respuesta supera el limite local"}'
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(encoded)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Cross-Origin-Resource-Policy", "same-origin")
            self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
            self.send_header("Content-Security-Policy", getattr(self.server, "csp", "default-src 'none'; frame-ancestors 'none'"))
            for key, value in (headers or {}).items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(encoded)

        def _fail(self, status, message):
            self.close_connection = True
            self._send(status, {"error": message})

        def _target(self, *, mutation=False):
            if len(self.path) > 4096 or not self.path.startswith("/") or self.path.startswith("//"):
                self._fail(400, "Ruta local inválida")
                return None
            host_header = self.headers.get("Host", "")
            if len(self.headers.get_all("Host", [])) != 1 or len(self.headers.get_all("Origin", [])) > 1:
                self._fail(400, "Cabeceras locales inválidas")
                return None
            valid_hosts = {"127.0.0.1:" + str(self.server.server_port), "localhost:" + str(self.server.server_port)}
            if host_header not in valid_hosts:
                self._fail(403, "El panel sólo admite su dirección local")
                return None
            origin = self.headers.get("Origin")
            if (origin and origin != "http://" + host_header) or (mutation and not origin):
                self._fail(403, "Origen local inválido")
                return None
            if self.headers.get("Sec-Fetch-Site") not in (None, "same-origin", "none"):
                self._fail(403, "Origen local inválido")
                return None
            try:
                target = urlsplit(self.path)
                if target.scheme or target.netloc or target.fragment:
                    raise ValueError()
                query = parse_qs(target.query, keep_blank_values=True, max_num_fields=10)
                if any(len(values) != 1 or len(key) > 100 or len(values[0]) > 200 for key, values in query.items()):
                    raise ValueError()
            except ValueError:
                self._fail(400, "Parámetros locales inválidos")
                return None
            return target.path, {key: values[0] for key, values in query.items()}

        def do_GET(self):
            target = self._target()
            if target is None:
                return
            path, query = target
            try:
                if path in ("/", "/index.html"):
                    if query:
                        return self._fail(400, "Parámetros locales inválidos")
                    return self._send(200, self.server.index, "text/html; charset=utf-8")
                if path == "/api/health":
                    if query:
                        return self._fail(400, "Parámetros locales inválidos")
                    state = store.status()
                    runtime_state = runtime.status()
                    safe_store = {key: state[key] for key in (
                        "mode", "rail", "counts", "jobs_by_state", "ledger_integrity"
                    ) if key in state}
                    safe_runtime = {key: runtime_state[key] for key in (
                        "scheduler", "latest_cycle", "last_cycle", "running", "enabled",
                        "last_scan_at_utc", "next_scan_at_utc"
                    ) if key in runtime_state}
                    return self._send(200, {
                        "mode": "READ_ONLY", "rail": "RESOURCES", "as_of_utc": _utc_now(),
                        "store": _plain(safe_store), "runtime": _plain(safe_runtime),
                        "csrf_token": self.server.csrf_token, "verified_income_usd": None,
                        "recorded_income_usd": 0,
                        "income_scope": "Este motor no ha registrado ingresos cobrados; no consulta balances personales",
                        "financial_execution": False, "direct_bot_connected": False,
                    })
                if path == "/api/opportunities":
                    if set(query) - {"limit", "classification", "source_id"}:
                        return self._fail(400, "Filtro inválido")
                    limit = int(query.get("limit", "200"))
                    if not 1 <= limit <= 500:
                        return self._fail(400, "Límite inválido")
                    items = store.opportunities(limit=limit, classification=query.get("classification"), source_id=query.get("source_id"))
                    return self._send(200, {"items": [_opportunity_view(row) for row in items], "as_of_utc": _utc_now()})
                if path == "/api/sources":
                    if query:
                        return self._fail(400, "Filtro inválido")
                    return self._send(200, {"items": [_source_view(row) for row in store.list_sources()], "as_of_utc": _utc_now()})
                if path == "/api/jobs":
                    if set(query) - {"limit"}:
                        return self._fail(400, "Filtro inválido")
                    limit = int(query.get("limit", "50"))
                    if not 1 <= limit <= 200:
                        return self._fail(400, "Límite inválido")
                    return self._send(200, {"items": [_job_view(row) for row in store.joblist(limit=limit)], "as_of_utc": _utc_now()})
                if path == "/api/export":
                    if query:
                        return self._fail(400, "Parámetros locales inválidos")
                    packet = store.export_packet(persist=False)
                    _assert_public_packet(packet)
                    return self._send(200, packet, headers={
                        "Content-Disposition": 'attachment; filename="MONEY_RESOURCE_PACKET.json"'
                    })
                return self._fail(404, "Ruta no disponible")
            except (ValueError, TypeError):
                return self._fail(400, "Datos o parámetros locales inválidos")
            except Exception:
                return self._fail(500, "No se pudo completar la lectura local")

        def do_POST(self):
            target = self._target(mutation=True)
            if target is None:
                return
            path, query = target
            if path != "/api/scan":
                return self._fail(404, "Ruta no disponible")
            if query:
                return self._fail(400, "Parámetros locales inválidos")
            csrf = self.headers.get("X-Money-CSRF", "")
            if not csrf.isascii() or not secrets.compare_digest(csrf, self.server.csrf_token):
                return self._fail(403, "Recarga el panel antes de buscar")
            if len(self.headers.get_all("X-Money-CSRF", [])) != 1 or len(self.headers.get_all("Content-Length", [])) != 1:
                return self._fail(400, "Cabeceras de cuerpo inválidas")
            if self.headers.get("Transfer-Encoding"):
                return self._fail(400, "Transporte de cuerpo no admitido")
            declared = self.headers.get("Content-Length", "")
            if not declared.isascii() or not declared.isdigit() or len(declared) > 9:
                return self._fail(411, "Se requiere tamaño del cuerpo")
            size = int(declared)
            if size > MAX_BODY:
                return self._fail(413, "El cuerpo supera el límite local")
            if self.headers.get("Content-Type", "").split(";")[0].strip().lower() != "application/json":
                return self._fail(415, "Se requiere application/json")
            try:
                raw = self.rfile.read(size)
                if len(raw) != size:
                    return self._fail(400, "Cuerpo incompleto")
                body = json.loads(raw, object_pairs_hook=_json_pairs)
                if not isinstance(body, dict) or set(body) - {"source_ids"}:
                    return self._fail(400, "Sólo se admiten fuentes configuradas")
                requested = body.get("source_ids")
                available = {row.get("source_id", row.get("id")) for row in map(_source_view, store.list_sources()) if row.get("enabled") is True}
                if requested is not None:
                    if (not isinstance(requested, list) or not 1 <= len(requested) <= 100
                            or any(not isinstance(item, str) or not ID_PATTERN.fullmatch(item) for item in requested)
                            or len(set(requested)) != len(requested)):
                        return self._fail(400, "Selección de fuentes inválida")
                    if not set(requested) <= available:
                        return self._fail(400, "Fuente no configurada o desactivada")
                result = runtime.scan_now(source_ids=requested, wait=False)
                ids = result.get("job_ids", [])
                cooling = [
                    {"source_id": row["source_id"], "retry_after_seconds": row.get("retry_after_seconds")}
                    for row in result.get("sources_in_cooldown", [])
                    if isinstance(row, dict) and row.get("source_id") in available
                ]
                job = {"job_id": "batch:" + hashlib.sha256(json.dumps(ids).encode()).hexdigest()[:20],
                       "job_ids": ids, "source_ids": requested or sorted(available),
                       "status": result.get("state", "QUEUED"), "created_at": _utc_now(),
                       "sources_in_cooldown": cooling}
                return self._send(202 if ids else 200, {"job": _plain(job), "mode": "READ_ONLY", "financial_execution": False})
            except (ValueError, TypeError, UnicodeDecodeError, RecursionError):
                return self._fail(400, "Solicitud de búsqueda inválida")
            except TimeoutError:
                return self._fail(408, "Tiempo de lectura agotado")
            except Exception:
                return self._fail(500, "No se pudo encolar la búsqueda local")

        def do_OPTIONS(self):
            self._fail(405, "Método no disponible")

        do_PUT = do_DELETE = do_PATCH = do_OPTIONS

    server = ResourceServer((host, port), Handler)
    try:
        server.csrf_token = secrets.token_urlsafe(32)
        server.index = (Path(__file__).resolve().parent.parent / "web" / "index.html").read_bytes()
        scripts = re.findall(rb"<script(?:\s[^>]*)?>(.*?)</script>", server.index, flags=re.DOTALL | re.IGNORECASE)
        import base64
        hashes = ["'sha256-" + base64.b64encode(hashlib.sha256(script).digest()).decode() + "'" for script in scripts]
        server.csp = ("default-src 'none'; script-src " + (" ".join(hashes) or "'none'")
                      + "; style-src 'unsafe-inline'; connect-src 'self'; img-src 'self' data:; "
                      + "base-uri 'none'; form-action 'none'; frame-ancestors 'none'")
        return server
    except Exception:
        server.server_close()
        raise


def serve(store, runtime, host="127.0.0.1", port=8787):
    """Serve the dashboard; scheduler lifecycle belongs to the caller/CLI."""
    server = create_server(store, runtime, host=host, port=port)
    try:
        server.serve_forever(poll_interval=0.25)
    finally:
        server.server_close()
