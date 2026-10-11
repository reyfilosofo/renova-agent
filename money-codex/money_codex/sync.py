"""Public reachability audit. A URL, project ID or credential is not access.

Authenticated Drive/project/agent round trips must be verified separately. This
module performs no private API requests and never prints environment values.
"""
from __future__ import annotations
import os
import urllib.request
import urllib.error
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
from .models import AccessRecord
from .packets import strict_json_loads

CANONICAL_PUBLIC_URLS = {
    'GitHub public repository': 'https://github.com/reyfilosofo/renova-agent',
    'MONEY app': 'https://money-z6epdn.v2.appdeploy.ai/',
    'MONEY Grok site': 'https://themoney.grok.me/',
}


def _canonical_url(value: object) -> str | None:
    if not isinstance(value, str) or len(value) > 2000 or any(ord(c) <= 32 or ord(c) == 127 for c in value) or '\\' in value:
        return None
    try:
        u = urlsplit(value)
        if u.scheme != 'https' or u.hostname not in {'github.com', 'money-z6epdn.v2.appdeploy.ai', 'themoney.grok.me'} or u.port not in (None, 443) or u.username is not None or u.password is not None or u.query or u.fragment:
            return None
        clean = urlunsplit(('https', u.hostname, u.path or '/', '', ''))
        for canonical in CANONICAL_PUBLIC_URLS.values():
            if clean.rstrip('/') == canonical.rstrip('/'):
                return canonical
        return None
    except ValueError:
        return None


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _head_or_get(url: str, timeout: int = 8) -> tuple[bool, str]:
    target = _canonical_url(url)
    if target is None:
        return False, 'canonical_public_https_url_required'
    req = urllib.request.Request(target, method='GET', headers={'User-Agent': 'MONEY-Omega-Codex/0.3 (public reachability only)'})
    # Do not follow unreviewed redirects into authentication pages or endpoints.
    opener = urllib.request.build_opener(_NoRedirect())
    try:
        with opener.open(req, timeout=timeout) as resp:
            if _canonical_url(resp.geturl()) != target:
                return False, 'response_url_not_canonical'
            status = resp.status
            if type(status) is not int or not 100 <= status <= 599:
                return False, 'invalid_http_status'
            return 200 <= status < 300, f'HTTP {status}; public reachability only'
    except urllib.error.HTTPError as exc:
        code = exc.code
        return False, f'HTTP {code}' if type(code) is int and 100 <= code <= 599 else 'http_error'
    except Exception:
        # HTTP transports and proxies can include URLs or credentials in their
        # exception messages. No submitted value or exception text is exposed.
        return False, 'network_unavailable'


def load_config(path: str | Path) -> dict:
    value = strict_json_loads(Path(path).read_bytes())
    if not isinstance(value, dict):
        raise ValueError('integration_config_must_be_object')
    return value


def sync(config: dict) -> list[AccessRecord]:
    if not isinstance(config, dict):
        raise ValueError('integration_config_must_be_object')
    github = config.get('github', {})
    surfaces = config.get('surfaces', {})
    github = github if isinstance(github, dict) else {}
    surfaces = surfaces if isinstance(surfaces, dict) else {}
    configured = [
        ('GitHub public repository', github.get('repo_url')),
        ('MONEY app', surfaces.get('money_app')),
        ('MONEY Grok site', surfaces.get('grok_site')),
    ]
    out = []
    for name, value in configured:
        target = _canonical_url(value)
        # Each configured role must match its own canonical site.
        if target != CANONICAL_PUBLIC_URLS[name]:
            ok, detail = False, 'canonical_public_https_url_required'
        else:
            ok, detail = _head_or_get(target)
        out.append(AccessRecord(name, target if target == CANONICAL_PUBLIC_URLS[name] else 'UNVERIFIED CONFIGURATION',
                                'ACCESS PARTIAL' if ok else 'ACCESS UNAVAILABLE',
                                detail + '; authenticated access, runtime and round trip not verified'))
    for name, variable, target in (
        ('Google Drive API', 'GOOGLE_DRIVE_ACCESS_TOKEN', 'Google Drive authenticated runtime read'),
        ('Grok Bot authenticated endpoint', 'GROK_BOT_ENDPOINT', 'GROK_BOT_ENDPOINT (unverified configuration)'),
        ('ChatGPT bridge endpoint', 'CHATGPT_BRIDGE_ENDPOINT', 'CHATGPT_BRIDGE_ENDPOINT (unverified configuration)'),
    ):
        present = bool(os.getenv(variable))
        detail = 'configuration present; authenticated read and round trip not verified' if present else 'no runtime configuration; authenticated read and round trip not verified'
        out.append(AccessRecord(name, target, 'ACCESS UNAVAILABLE', detail))
    projects = config.get('projects', {})
    projects = projects if isinstance(projects, dict) else {}
    for name, field in (('ChatGPT project API', 'chatgpt_project_id'), ('Codex project API', 'codex_project_id')):
        value = projects.get(field)
        provided = isinstance(value, str) and bool(value.strip()) and value not in ('PENDING_USER_INPUT', 'PENDING')
        out.append(AccessRecord(name, 'Project identifier only' if provided else 'PENDING USER INPUT', 'ACCESS UNAVAILABLE',
                                'an identifier does not prove programmatic access; no project API read verified'))
    return out
