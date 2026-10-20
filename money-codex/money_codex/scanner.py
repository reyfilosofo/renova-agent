"""Public resource discovery. No account access, forms, claims or execution.

Configuration is an operator-reviewed allowlist, not an arbitrary-URL API.
Catalogue evidence proves discovery, never eligibility or expected payout.
"""
from __future__ import annotations

import hashlib
import http.client
import ipaddress
import json
import math
import re
import socket
import ssl
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from html.parser import HTMLParser


PROVIDER_HOSTS = {
    "code4rena": {"code4rena.com", "www.code4rena.com"},
    "immunefi": {"immunefi.com", "www.immunefi.com"},
    "github": {"api.github.com", "github.com"},
    "zealy": {"zealy.io"},
    "galxe": {"app.galxe.com", "galxe.com", "www.galxe.com"},
    "prolific": {"www.prolific.com", "prolific.com"},
    "userinterviews": {"www.userinterviews.com", "userinterviews.com"},
    "respondent": {"www.respondent.io", "respondent.io"},
}
EV_FIELDS = (
    "expected_gross_reward_usd", "reward_probability", "gas_usd", "fees_usd",
    "required_spend_usd", "expected_loss_usd", "time_cost_usd",
    "capital_lockup_cost_usd", "security_risk_cost_usd",
)
_RATE_TIMES: dict[str, float] = {}
_RATE_LOCK = threading.Lock()
_REDIRECT_CODES = {301, 302, 303, 307, 308}
_RSC_MAX_BYTES = 4194304


class SourceError(ValueError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("UTC-aware datetime required")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _text(value: object, limit: int = 500) -> str:
    return " ".join(re.sub(r"[\x00-\x1f\x7f]", " ", str(value or "")).split())[:limit]


def _number(value: object, default: float, minimum: float, maximum: float) -> float:
    try:
        number = float(value)
    except (ValueError, TypeError):
        return default
    return max(minimum, min(maximum, number)) if math.isfinite(number) else default


def _policy(config: dict, source: dict) -> dict:
    provider = str(source.get("provider", "")).lower().replace(" ", "")
    if provider not in PROVIDER_HOSTS:
        raise SourceError("UNSUPPORTED_PROVIDER")
    network = config.get("network", {})
    if not isinstance(network, dict):
        raise SourceError("INVALID_NETWORK_CONFIG")
    general_hosts = network.get("allowed_hosts", [])
    source_hosts = source.get("allowed_hosts", [])
    if not all(isinstance(v, list) and all(isinstance(h, str) for h in v)
               for v in (general_hosts, source_hosts)):
        raise SourceError("INVALID_HOST_ALLOWLIST")
    allowed = set(general_hosts)
    specific = set(source_hosts)
    if not specific or not specific.issubset(allowed & PROVIDER_HOSTS[provider]):
        raise SourceError("HOST_NOT_ALLOWLISTED")
    repo = source.get("repository")
    if provider == "github":
        if not isinstance(repo, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
            raise SourceError("INVALID_GITHUB_REPOSITORY")
        if repo not in config.get("allowed_github_repositories", []):
            raise SourceError("REPOSITORY_NOT_ALLOWLISTED")
    return {
        "provider": provider, "allowed_hosts": specific, "repository": repo,
        "timeout_seconds": _number(network.get("timeout_seconds"), 12, 1, 30),
        "max_bytes": int(_number(network.get("max_bytes"), 1048576, 1024, 2097152)),
        "max_redirects": int(_number(network.get("max_redirects"), 3, 0, 5)),
        "min_interval_seconds": _number(network.get("min_interval_seconds"), 60, 1, 3600),
        "host_interval_seconds": _number(network.get("host_interval_seconds"), 1, 0.1, 5),
        "source_budget_seconds": _number(source.get("source_budget_seconds", network.get("source_budget_seconds")), 110, 5, 115),
    }


def _validate_url(url: str, policy: dict, *, resolve: bool = True) -> str:
    if not isinstance(url, str) or len(url) > 2048 or re.search(r"[\x00-\x20\\]", url):
        raise SourceError("INVALID_URL")
    try:
        parts = urllib.parse.urlsplit(url)
        port = parts.port
    except ValueError as exc:
        raise SourceError("INVALID_URL") from exc
    if parts.scheme != "https" or parts.username or parts.password or port not in (None, 443):
        raise SourceError("HTTPS_PUBLIC_URL_REQUIRED")
    host = (parts.hostname or "").lower()
    if host not in policy["allowed_hosts"] or host.endswith("."):
        raise SourceError("HOST_NOT_ALLOWLISTED")
    if re.search(r"%(?:2f|5c|00)", parts.netloc, re.I):
        raise SourceError("INVALID_HOST_ENCODING")
    query_keys = {k.lower().replace("-", "_") for k, _ in urllib.parse.parse_qsl(parts.query)}
    if any(re.search(r"(?:token|secret|password|signature|authorization|credential|api_?key|session|cookie)", k)
           or k == "auth" for k in query_keys):
        raise SourceError("CREDENTIAL_QUERY_FORBIDDEN")
    path = urllib.parse.unquote(parts.path)
    if "\\" in path or any(p in (".", "..") for p in path.split("/")):
        raise SourceError("INVALID_PATH")
    if policy["provider"] == "github":
        repo = policy["repository"]
        prefix = f"/repos/{repo}/issues" if host == "api.github.com" else f"/{repo}/issues"
        if path != prefix and not re.fullmatch(re.escape(prefix) + r"/[0-9]+/?", path):
            raise SourceError("REPOSITORY_PATH_NOT_ALLOWLISTED")
    if resolve:
        try:
            addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
        except OSError as exc:
            raise SourceError("DNS_UNAVAILABLE") from exc
        if not addresses:
            raise SourceError("DNS_UNAVAILABLE")
        for record in addresses:
            try:
                address = ipaddress.ip_address(record[4][0].split("%", 1)[0])
            except ValueError as exc:
                raise SourceError("INVALID_DNS_ADDRESS") from exc
            if not address.is_global or address.is_multicast or address.is_unspecified:
                raise SourceError("NON_PUBLIC_ADDRESS_BLOCKED")
    return urllib.parse.urlunsplit(("https", host, parts.path or "/", parts.query, ""))


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _reserve_rate(url: str, policy: dict) -> None:
    host = urllib.parse.urlsplit(url).hostname
    with _RATE_LOCK:
        current = time.monotonic()
        if current - _RATE_TIMES.get("url:" + url, -math.inf) < policy["min_interval_seconds"]:
            raise SourceError("SOURCE_RATE_LIMIT")
        last_host = _RATE_TIMES.get("host:" + str(host), -math.inf)
        delay = max(0, policy["host_interval_seconds"] - (current - last_host))
        if policy.get("deadline_monotonic", math.inf) - current <= delay:
            raise SourceError("SOURCE_BUDGET_EXHAUSTED")
        # Reserve before releasing the lock so simultaneous jobs cannot burst.
        _RATE_TIMES["url:" + url] = current + delay
        _RATE_TIMES["host:" + str(host)] = current + delay
    if delay:
        time.sleep(delay)


def _remaining_timeout(policy: dict) -> float:
    remaining = policy.get("deadline_monotonic", math.inf) - time.monotonic()
    if remaining <= 0:
        raise SourceError("SOURCE_BUDGET_EXHAUSTED")
    return min(policy["timeout_seconds"], remaining)


def _read_response(response, policy: dict) -> bytes:
    """Check the shared source budget between bounded socket reads.

    Real urllib HTTPS responses expose read1, which performs at most one raw
    read; read(n) can otherwise wait for n bytes while a peer trickles data.
    """
    if not isinstance(response, http.client.HTTPResponse):
        # Also supports small substituted openers used by local tests.
        body = response.read(policy["max_bytes"] + 1)
        _remaining_timeout(policy)
        return body
    chunks, size = [], 0
    while True:
        if response.isclosed():
            return b"".join(chunks)
        timeout = _remaining_timeout(policy)
        try:
            response.fp.raw._sock.settimeout(timeout)
        except (AttributeError, OSError) as exc:
            raise SourceError("DEADLINE_UNSUPPORTED_TRANSPORT") from exc
        chunk = response.read1(min(65536, policy["max_bytes"] + 1 - size))
        _remaining_timeout(policy)
        if not chunk:
            return b"".join(chunks)
        size += len(chunk)
        if size > policy["max_bytes"]:
            raise SourceError("RESPONSE_TOO_LARGE")
        chunks.append(chunk)


def _fetch(source: dict, policy: dict) -> dict:
    """urllib inherits configured proxies; TLS verification is always enabled."""
    _remaining_timeout(policy)
    url = _validate_url(source.get("url"), policy)
    _remaining_timeout(policy)
    context = ssl.create_default_context()
    opener = urllib.request.build_opener(_NoRedirect(), urllib.request.HTTPSHandler(context=context))
    for redirect in range(policy["max_redirects"] + 1):
        _reserve_rate(url, policy)
        request = urllib.request.Request(url, method="GET", headers={
            "User-Agent": "MONEY-Omega-ResourceDiscovery/0.3 (public read-only research)",
            "Accept": "text/html,application/json,application/rss+xml,application/atom+xml,text/plain",
            "Accept-Encoding": "identity",
        })
        try:
            response = opener.open(request, timeout=_remaining_timeout(policy))
        except urllib.error.HTTPError as exc:
            if exc.code in _REDIRECT_CODES:
                location = exc.headers.get("Location")
                exc.close()
                if not location or redirect >= policy["max_redirects"]:
                    raise SourceError("REDIRECT_LIMIT")
                url = _validate_url(urllib.parse.urljoin(url, location), policy)
                continue
            status = exc.code
            exc.close()
            raise SourceError(f"HTTP_{status}") from exc
        except (urllib.error.URLError, OSError, TimeoutError) as exc:
            raise SourceError("NETWORK_UNAVAILABLE") from exc
        with response:
            # Recheck the effective URL even for a substituted/custom opener.
            final = _validate_url(response.geturl(), policy)
            status = response.status
            if status != 200:
                raise SourceError(f"HTTP_{status}")
            encoding = response.headers.get("Content-Encoding", "identity").lower()
            if encoding not in ("", "identity"):
                raise SourceError("ENCODED_RESPONSE_UNSUPPORTED")
            length = response.headers.get("Content-Length")
            if length and (not length.isdigit() or int(length) > policy["max_bytes"]):
                raise SourceError("RESPONSE_TOO_LARGE")
            try:
                body = _read_response(response, policy)
            except (OSError, TimeoutError) as exc:
                raise SourceError("NETWORK_UNAVAILABLE") from exc
            if len(body) > policy["max_bytes"]:
                raise SourceError("RESPONSE_TOO_LARGE")
            if not body:
                raise SourceError("EMPTY_RESPONSE")
            content_type = response.headers.get("Content-Type", "").split(";", 1)[0].lower()
            if content_type not in ("text/html", "application/xhtml+xml", "application/json", "application/rss+xml", "application/atom+xml", "text/xml", "application/xml", "text/plain"):
                raise SourceError("CONTENT_TYPE_UNSUPPORTED")
            return {"url": final, "body": body, "http_status": status, "content_type": content_type,
                    "observed_at": _iso(_utc_now()), "content_sha256": hashlib.sha256(body).hexdigest()}
    raise SourceError("REDIRECT_LIMIT")


class _Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links: list[dict] = []
        self._anchor: dict | None = None
        self._hidden = 0
        self.parts: list[str] = []
        self.h1: list[str] = []
        self._in_h1 = False
        self.scripts: list[str] = []
        self._in_script = False
        self.title: list[str] = []
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag in ("script", "style", "noscript"):
            self._hidden += 1
        if tag == "script":
            self._in_script = True
        if tag == "h1":
            self._in_h1 = True
        if tag == "title":
            self._in_title = True
        if tag == "a" and not self._hidden:
            self._anchor = {"href": values.get("href", ""), "parts": []}
        if tag == "img" and self._anchor:
            self._anchor["parts"].append(values.get("alt", ""))

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript"):
            self._hidden = max(0, self._hidden - 1)
        if tag == "script":
            self._in_script = False
        if tag == "h1":
            self._in_h1 = False
        if tag == "title":
            self._in_title = False
        if tag == "a" and self._anchor:
            self.links.append({"href": self._anchor["href"], "title": _text(" ".join(self._anchor["parts"]))})
            self._anchor = None

    def handle_data(self, data):
        if self._in_script:
            self.scripts.append(data)
        if self._hidden:
            return
        self.parts.append(data)
        if self._anchor:
            self._anchor["parts"].append(data)
        if self._in_h1:
            self.h1.append(data)
        if self._in_title:
            self.title.append(data)


def _permalink(url: str, source: dict, policy: dict) -> str | None:
    try:
        clean = _validate_url(urllib.parse.urljoin(source["url"], url), policy, resolve=False)
    except SourceError:
        return None
    path = urllib.parse.urlsplit(clean).path
    provider = policy["provider"]
    patterns = {
        "immunefi": r"/bug-bounty/[^/]+/information/?",
        "code4rena": r"/(?:audits|bounties)/[^/]+/?",
        "zealy": r"/c/[^/]+/questboard(?:/[^/]+)?/?",
        "galxe": r"/quest/[^/]+/[^/]+/?",
    }
    if provider in patterns and re.fullmatch(patterns[provider], path):
        if provider == "galxe" and path.startswith("/quest/explore/"):
            return None
        # Recognised permalink paths identify the programme without trackers.
        parts = urllib.parse.urlsplit(clean)
        return urllib.parse.urlunsplit((parts.scheme, parts.netloc, parts.path.rstrip("/") + "/", "", ""))
    return None


def _aware_time(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc) if parsed.tzinfo is not None else None
    except ValueError:
        return None


def _next_json_values(page: _Page) -> list:
    """Read JSON Flight rows and skip byte-framed text, never evaluate JS.

    Text rows can contain arbitrary programme descriptions and fake JSON. Their
    UTF-8 byte lengths must be respected before reading the next record.
    """
    decoder = json.JSONDecoder()
    chunks = []
    total = 0
    for script in page.scripts:
        for marker in re.finditer(r"self\.__next_f\.push\(", script):
            try:
                item, _ = decoder.raw_decode(script, marker.end())
            except (ValueError, RecursionError):
                continue
            if isinstance(item, list) and len(item) > 1 and isinstance(item[1], str):
                chunks.append(item[1])
                total += len(item[1])
                if total > _RSC_MAX_BYTES:
                    raise SourceError("RSC_SIZE_LIMIT")
    payload = "".join(chunks).encode("utf-8")
    if len(payload) > _RSC_MAX_BYTES:
        raise SourceError("RSC_SIZE_LIMIT")
    values, cursor = [], 0
    while cursor < len(payload) and len(values) < 2000:
        while cursor < len(payload) and payload[cursor] in b"\r\n":
            cursor += 1
        if cursor == len(payload):
            break
        header = re.match(rb"[0-9a-f]{0,16}:", payload[cursor:])
        if not header:
            break
        cursor += header.end()
        text = re.match(rb"T([0-9a-f]{1,8}),", payload[cursor:])
        if text:
            cursor += text.end() + int(text[1], 16)
            if cursor > len(payload):
                raise SourceError("RSC_TRUNCATED_TEXT")
            continue
        tag = re.match(rb"[A-Z]+(?=[\[{])", payload[cursor:])
        if tag:
            cursor += tag.end()
        try:
            tail = payload[cursor:].decode("utf-8")
            item, end = decoder.raw_decode(tail)
        except (ValueError, UnicodeError, RecursionError):
            newline = payload.find(b"\n", cursor)
            if newline < 0:
                break
            cursor = newline + 1
            continue
        values.append(item)
        cursor += len(tail[:end].encode("utf-8"))
    return values


def _object_nodes(value, depth=0):
    if depth > 32:
        return
    if isinstance(value, dict):
        yield value
        for child in value.values():
            if isinstance(child, (dict, list)):
                yield from _object_nodes(child, depth + 1)
    elif isinstance(value, list):
        for child in value:
            yield from _object_nodes(child, depth + 1)


def _code4rena_details(page: _Page) -> dict[str, dict]:
    """Read dates only from exact-slug JSON objects already linked by the page."""
    records = {}
    for value in _next_json_values(page):
        for item in _object_nodes(value):
            slug = item.get("slug")
            if (isinstance(slug, str) and re.fullmatch(r"[a-z0-9-]+", slug)
                    and "endTime" in item and "status" in item):
                records[slug] = item
    return records


def _readable_page(body: bytes) -> tuple[_Page, str]:
    page = _Page()
    page.feed(body.decode("utf-8", errors="replace"))
    visible = _text(" ".join(page.parts), 200000)
    heading = _text(" ".join([*page.h1, *page.title]), 1000)
    if re.search(r"(?i)(verify (?:you are|that you.re) human|just a moment|access denied|captcha challenge|checking your browser|enable javascript and cookies to continue)", visible[:3000]):
        raise SourceError("BLOCKED_CONTENT")
    if re.match(r"(?i)^(?:404\b|page not found\b|not found\b|this page (?:could not be found|does not exist|isn.t available))", heading):
        raise SourceError("PAGE_NOT_FOUND")
    if not visible or len(visible) < 40 and not page.h1 and not page.links:
        raise SourceError("SPA_CONTENT_UNAVAILABLE")
    if len(visible) < 100 and re.search(r"(?i)\b(sign in|log in)\b", visible):
        raise SourceError("AUTHENTICATION_REQUIRED")
    return page, visible


def _html_candidates(source: dict, fetched: dict, policy: dict, now: datetime | None = None) -> list[dict]:
    page, visible = _readable_page(fetched["body"])
    if source.get("parser") == "program":
        return [{"title": _text(" ".join(page.h1)) or source["name"], "url": fetched["url"],
                 "type": "PROGRAM_DISCOVERY", "category": source["category"], "provider_status": "MEMBERSHIP_ONLY"}]
    candidates = []
    details = _code4rena_details(page) if policy["provider"] == "code4rena" else {}
    observed = now or _aware_time(fetched.get("observed_at")) or _utc_now()
    for link in page.links:
        url = _permalink(link["href"], {**source, "url": fetched["url"]}, policy)
        if not url or not link["title"]:
            continue
        if policy["provider"] == "code4rena" and re.search(r"(?i)\b(completed|judging|submissions closed|report in progress|past audit)\b", link["title"]):
            continue
        record = details.get(urllib.parse.urlsplit(url).path.strip("/").split("/")[-1], {})
        deadline = _aware_time(record.get("endTime"))
        start = _aware_time(record.get("startTime"))
        if record and (str(record.get("status", "")).lower() in
                       ("completed", "judging", "submissions closed", "report in progress", "closed")
                       or deadline is not None and deadline <= observed):
            continue
        if deadline and start and deadline <= start:
            continue
        # An explicitly labelled ISO deadline in visible text is also safe to
        # use; a month in a URL or an unlabelled date is not a deadline.
        labelled = re.search(r"(?i)\b(?:deadline|ends|closes)\s*:?\s*(\d{4}-\d{2}-\d{2}T[0-9:.]+(?:Z|[+-]\d{2}:\d{2}))", link["title"])
        if deadline is None and labelled:
            deadline = _aware_time(labelled[1])
        if deadline is not None and deadline <= observed:
            continue
        candidates.append({"title": link["title"], "url": url, "type": source["category"],
                           "category": source["category"], "provider_status": "LISTED; AVAILABILITY UNVERIFIED",
                           "deadline_utc": _iso(deadline) if deadline else None,
                           "starts_at_utc": _iso(start) if start else None,
                           "provider_declared_status": _text(record.get("status")) or None})
    return candidates


def _json_candidates(source: dict, fetched: dict, policy: dict) -> list[dict]:
    data = json.loads(fetched["body"])
    if source.get("parser") != "github_issues" or not isinstance(data, list):
        raise SourceError("UNSUPPORTED_JSON_SHAPE")
    candidates = []
    label = str(source.get("label", "bounty")).lower()
    for issue in data:
        if not isinstance(issue, dict) or "pull_request" in issue or issue.get("state") != "open":
            continue
        labels = {str(x.get("name", "")).lower() for x in issue.get("labels", []) if isinstance(x, dict)}
        if label not in labels:
            continue
        try:
            url = _validate_url(issue.get("html_url"), policy, resolve=False)
        except SourceError:
            continue
        if urllib.parse.urlsplit(url).hostname != "github.com":
            continue
        title = _text(issue.get("title"))
        if not title:
            continue
        # A bounty label alone does not specify a payout. Keep all EV inputs null.
        candidates.append({"title": title, "url": url, "type": "BOUNTY", "category": "BOUNTY",
                           "provider_status": "OPEN ISSUE; PAYMENT AND ELIGIBILITY UNVERIFIED",
                           "provider_item_id": issue.get("number"), "provider_updated_at": issue.get("updated_at")})
    return candidates


def _rss_candidates(source: dict, fetched: dict, policy: dict) -> list[dict]:
    if re.search(br"<!\s*(DOCTYPE|ENTITY)", fetched["body"], re.I):
        raise SourceError("XML_ENTITIES_FORBIDDEN")
    root = ET.fromstring(fetched["body"])
    candidates = []
    for item in root.iter():
        if item.tag.rsplit("}", 1)[-1] not in ("item", "entry"):
            continue
        children = {x.tag.rsplit("}", 1)[-1]: x for x in item}
        title_node, link_node = children.get("title"), children.get("link")
        if title_node is None or link_node is None:
            continue
        url = _permalink(link_node.get("href") or link_node.text or "", source, policy)
        title = _text(title_node.text)
        if url and title:
            candidates.append({"title": title, "url": url, "type": source["category"],
                               "category": source["category"], "provider_status": "FEED ITEM; AVAILABILITY UNVERIFIED"})
    return candidates


def _opportunity_id(source: dict, url: str) -> str:
    provider = str(source["provider"]).lower().replace(" ", "")
    digest = hashlib.sha256((provider + "\n" + url).encode()).hexdigest()
    return "resource_" + digest[:24]


def _proof(source_id: str, fetched: dict, requested_url: str) -> dict:
    return {
        "evidence_id": "evidence_" + hashlib.sha256((source_id + fetched["observed_at"] + fetched["content_sha256"]).encode()).hexdigest()[:24],
        "source_id": source_id, "url": fetched["url"], "requested_url": requested_url,
        "observed_at": fetched["observed_at"], "retrieved_at": fetched["observed_at"],
        "http_status": fetched["http_status"], "content_type": fetched["content_type"],
        "content_sha256": fetched["content_sha256"], "hash_basis": "HTTP_RESPONSE_BYTES",
        "byte_count": len(fetched["body"]),
    }


def _immunefi_information(source: dict, candidate: dict, fetched: dict, policy: dict) -> tuple[dict, str | None]:
    """Extract public programme terms, never a user's eligibility or EV.

    Only the JSON bounty whose official URL and slug match this fetched detail
    page can supply terms. A maximum bounty is not an expected gross reward.
    """
    page, visible = _readable_page(fetched["body"])
    identity = candidate["url"]
    slug = urllib.parse.urlsplit(identity).path.strip("/").split("/")[-2]
    matches = []
    for value in _next_json_values(page):
        for record in _object_nodes(value):
            if (record.get("slug") == slug and "maxBounty" in record
                    and _permalink(record.get("url", ""), source, policy) == identity):
                if record not in matches:
                    matches.append(record)
    if len(matches) != 1 or _permalink(fetched["url"], source, policy) != identity:
        raise SourceError("PROGRAM_IDENTITY_UNVERIFIED")
    record = matches[0]
    if not all(field in record for field in ("pausedAt", "endDate", "launchDate", "updatedDate")):
        raise SourceError("PROGRAM_STATE_INCOMPLETE")
    if not page.h1 or not isinstance(record.get("project"), str) or not record["project"].strip():
        raise SourceError("PROGRAM_IDENTITY_UNVERIFIED")
    if _text(page.h1[0]).casefold() != _text(record["project"]).casefold():
        raise SourceError("PROGRAM_IDENTITY_CONFLICT")
    observed = _aware_time(fetched["observed_at"])
    if observed is None:
        raise SourceError("INVALID_OBSERVATION_TIME")
    parsed = {}
    for field in ("pausedAt", "endDate", "launchDate", "updatedDate"):
        value = record.get(field)
        parsed[field] = _aware_time(value)
        if value is not None and parsed[field] is None:
            raise SourceError("PROGRAM_DATE_UNVERIFIED")
    if parsed["updatedDate"] and parsed["updatedDate"] > observed:
        raise SourceError("PROGRAM_FUTURE_TIMESTAMP")
    inactive = ("PROGRAM_PAUSED" if record["pausedAt"] is not None else
                "PROGRAM_ENDED" if parsed["endDate"] and parsed["endDate"] <= observed else
                "PROGRAM_NOT_STARTED" if parsed["launchDate"] and parsed["launchDate"] > observed else None)
    if not inactive and not re.search(r"(?i)\bSubmit a Bug\b", visible):
        raise SourceError("PROGRAM_SUBMISSION_STATE_UNVERIFIED")
    maximum = record.get("maxBounty")
    if type(maximum) not in (int, float) or not math.isfinite(maximum) or not 0 <= maximum <= 1e12:
        raise SourceError("PROGRAM_REWARD_UNVERIFIED")
    advertised = None
    display = re.search(r"\bMaximum Bounty\s+\$\s*([0-9][0-9,]*(?:\.[0-9]+)?)(?![A-Za-z0-9,.])", visible)
    if display:
        advertised = float(display[1].replace(",", ""))
        if advertised != maximum:
            raise SourceError("PROGRAM_REWARD_CONFLICT")
    enriched = {**candidate, "title": _text(record["project"]),
                "detail_status": "INACTIVE" if inactive else "ACTIVE",
                "detail_verified_at_utc": fetched["observed_at"],
                "verification_scope": "PUBLIC_PROGRAM_TERMS_ONLY",
                "advertised_max_reward_usd": advertised,
                "programme_launch_at_utc": _iso(parsed["launchDate"]) if parsed["launchDate"] else None,
                "programme_updated_at_utc": _iso(parsed["updatedDate"]) if parsed["updatedDate"] else None,
                "deadline_utc": _iso(parsed["endDate"]) if parsed["endDate"] else None,
                "provider_status": "PUBLIC PROGRAMME TERMS VERIFIED; PERSONAL ELIGIBILITY UNKNOWN"}
    if type(record.get("kyc")) is bool:
        enriched["kyc_requirements"] = "REQUIRED BY PROGRAMME" if record["kyc"] else "PROGRAMME DECLARES KYC NOT REQUIRED"
    return enriched, inactive


def _opportunity(source: dict, candidate: dict, proof: dict) -> dict:
    # Provider+canonical permalink survives multiple catalogues and jobs.
    source_evidence = {**proof, "observed_link": candidate["url"],
                       "reference_basis": "DIRECT_PAGE" if proof["url"] == candidate["url"] else "OBSERVED_CATALOG_LINK"}
    return {
        "opportunity_id": _opportunity_id(source, candidate["url"]), "source_id": source["source_id"],
        "provider": source["name"], "type": candidate["type"], "category": candidate["category"],
        "title": candidate["title"], "official_url": candidate["url"], "source_evidence": source_evidence,
        "evidence": [proof["evidence_id"], proof["url"]], "last_verified_at_utc": proof["observed_at"],
        "last_verified_at": proof["observed_at"], "verification_scope": candidate.get("verification_scope", "PUBLIC_PAGE_DISCOVERY_ONLY"),
        "discovery_only": True,
        "deadline_utc": candidate.get("deadline_utc"), "starts_at_utc": candidate.get("starts_at_utc"),
        "provider_declared_status": candidate.get("provider_declared_status"),
        "advertised_max_reward_usd": candidate.get("advertised_max_reward_usd"),
        "programme_launch_at_utc": candidate.get("programme_launch_at_utc"),
        "programme_updated_at_utc": candidate.get("programme_updated_at_utc"),
        "detail_status": candidate.get("detail_status"),
        "detail_verified_at_utc": candidate.get("detail_verified_at_utc"),
        "geography": None, "kyc_requirements": candidate.get("kyc_requirements"),
        "eligibility_status": "UNKNOWN", "eligibility": None, "wallet_network": None,
        "required_capital_usd": None, "required_actions": [], "irreversible_actions": [],
        "actions_verified": False, "time_cost_minutes": None, "capital_lockup": None,
        "security_risk": "UNKNOWN", "tos_status": "UNKNOWN", "repeatability": None,
        **{field: None for field in EV_FIELDS}, "expected_net_reward_usd": None,
        "classification": "WATCH", "status": "WATCH", "ev_status": "DATA INSUFFICIENT",
        "provider_status": candidate["provider_status"],
        "invalidation": "Page removed/closed, deadline passed, rules change, or eligibility fails; reverify before any action.",
        "missing_data": [*EV_FIELDS, "eligibility_status", "tos_status", "security_risk",
                         *([] if candidate.get("deadline_utc") else ["deadline_utc"])],
        "blocking_reasons": ["DISCOVERY_IS_NOT_AUTHORIZATION", "USER_ELIGIBILITY_NOT_VERIFIED"],
        "execution_allowed": False,
    }


def scan_sources(config: dict, now: datetime | None = None) -> dict:
    """GET enabled allowlisted sources once, returning evidence and candidates.

    ``now`` identifies the scheduler cycle; HTTP evidence is timestamped at actual
    retrieval. Failed/blocked responses never create fallback opportunities.
    """
    if not isinstance(config, dict) or not isinstance(config.get("sources"), list):
        raise ValueError("resource source config requires sources list")
    if config.get("mode", "READ_ONLY") != "READ_ONLY":
        raise ValueError("resource source config requires READ_ONLY mode")
    result = {"as_of": _iso(now or _utc_now()), "mode": "READ_ONLY", "opportunities": [],
              "source_status": [], "evidence": [], "errors": []}
    seen_sources: set[str] = set()
    seen_opportunities: set[str] = set()
    for original in config["sources"][:50]:
        if not isinstance(original, dict):
            result["errors"].append({"error_code": "INVALID_SOURCE"})
            continue
        source = {**original, "source_id": original.get("source_id") or original.get("id")}
        source_id = source.get("source_id")
        if not source_id or source_id in seen_sources:
            result["errors"].append({"source_id": source_id, "error_code": "INVALID_OR_DUPLICATE_SOURCE_ID"})
            continue
        seen_sources.add(source_id)
        state = {"source_id": source_id, "provider": source.get("name"), "url": None,
                 "access_status": "ACCESS UNAVAILABLE", "status": "NOT_FETCHED", "observed_at": None,
                 "http_status": None, "opportunity_count": 0, "error_code": None}
        result["source_status"].append(state)
        if source.get("enabled", True) is not True:
            state["status"] = "DISABLED"
            continue
        try:
            if source.get("method", "READ_ONLY") != "READ_ONLY":
                raise SourceError("READ_ONLY_METHOD_REQUIRED")
            if not all(isinstance(source.get(k), str) and source[k] for k in ("name", "category", "url")):
                raise SourceError("INVALID_SOURCE_CONFIG")
            policy = _policy(config, source)
            state["url"] = _validate_url(source["url"], policy, resolve=False)
            fetched = _fetch(source, policy)
            proof = {
                "evidence_id": "evidence_" + hashlib.sha256((source_id + fetched["observed_at"] + fetched["content_sha256"]).encode()).hexdigest()[:24],
                "source_id": source_id, "url": fetched["url"], "requested_url": state["url"],
                "observed_at": fetched["observed_at"], "retrieved_at": fetched["observed_at"],
                "http_status": fetched["http_status"], "content_type": fetched["content_type"],
                "content_sha256": fetched["content_sha256"], "hash_basis": "HTTP_RESPONSE_BYTES",
                "byte_count": len(fetched["body"]),
            }
            result["evidence"].append(proof)
            state.update(access_status="ACCESS VERIFIED", status="FETCHED", observed_at=proof["observed_at"], http_status=proof["http_status"])
            if source.get("parser") == "github_issues":
                candidates = _json_candidates(source, fetched, policy)
            elif source.get("parser") in ("rss", "atom"):
                candidates = _rss_candidates(source, fetched, policy)
            else:
                candidates = _html_candidates(source, fetched, policy, now)
            limit = int(_number(source.get("max_candidates"), 20, 1, 50))
            if not candidates and source.get("fallback_program", True) and source.get("parser") != "github_issues":
                candidates = [{"title": source["name"] + " public program catalogue", "url": fetched["url"],
                               "type": "PROGRAM_DISCOVERY", "category": source["category"],
                               "provider_status": "CATALOGUE_ONLY; NO INDIVIDUAL OPPORTUNITY VERIFIED"}]
            # Deduplicate before the limit: adjacent image/title buttons must
            # not halve the number of distinct catalogue entries examined.
            source_seen: set[str] = set()
            unique = []
            for candidate in candidates:
                if candidate["url"] not in source_seen:
                    unique.append(candidate)
                    source_seen.add(candidate["url"])
            state["candidate_count"] = len(unique)
            state["duplicate_count"] = 0
            for candidate in unique[:limit]:
                opportunity = _opportunity(source, candidate, proof)
                if opportunity["opportunity_id"] in seen_opportunities:
                    state["duplicate_count"] += 1
                    continue
                seen_opportunities.add(opportunity["opportunity_id"])
                result["opportunities"].append(opportunity)
                state["opportunity_count"] += 1
            state["status"] = ("DISCOVERED" if state["opportunity_count"] else
                               "DEDUPLICATED" if state["duplicate_count"] else "NO_PUBLIC_CANDIDATES")
        except (SourceError, ValueError, TypeError, ET.ParseError) as exc:
            code = exc.code if isinstance(exc, SourceError) else "PARSE_OR_CONFIG_ERROR"
            # Error text never includes response bodies, cookies or credentials.
            state.update(status="UNAVAILABLE" if not state["observed_at"] else "PARSE_UNAVAILABLE", error_code=code)
            if state["observed_at"]:
                state["access_status"] = "ACCESS PARTIAL"
            result["errors"].append({"source_id": source_id, "error_code": code})
    return result
