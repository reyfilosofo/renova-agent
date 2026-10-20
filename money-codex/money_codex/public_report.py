"""Publish registered public discovery fields through a typed allowlist.

Never export receipts, ledger rows, account/wallet details, raw response bodies,
operator notes or configuration values. This exporter is intended for a fresh
public-source scan, not for publishing an operator's private workspace.
"""
from datetime import datetime, timezone
import argparse
import json
import math
from pathlib import Path
import re
from urllib.parse import parse_qsl, unquote, urlencode, urlsplit, urlunsplit

from .packets import assert_no_secret_keys
from .scanner import PROVIDER_HOSTS
from .store import Store
from .models import SOURCE_MAX_AGE_SECONDS, utc_now

OFFICIAL_HOSTS = frozenset(host for hosts in PROVIDER_HOSTS.values() for host in hosts)
PUBLIC_TYPES = {'AIRDROP', 'CLAIM', 'WALLET_BENEFIT', 'QUEST', 'SURVEY', 'PAID_RESEARCH', 'BOUNTY', 'MICROTASK', 'AFFILIATE', 'REFERRAL', 'OTHER', 'PROGRAM_DISCOVERY'}
PUBLIC_CLASSIFICATIONS = {'DO NOW', 'QUEUE', 'WATCH', 'SKIP', 'DATA INSUFFICIENT'}
PUBLIC_ACCESS = {'ACCESS VERIFIED', 'ACCESS PARTIAL', 'ACCESS STALE', 'ACCESS UNAVAILABLE'}
PUBLIC_NUMBERS = ('expected_gross_reward_usd', 'reward_probability', 'expected_net_reward_usd')
PUBLIC_CODES = ('missing_data', 'blocking_reasons')
_ID = re.compile(r'[A-Za-z][A-Za-z0-9_.-]{0,100}')
_RESOURCE_ID = re.compile(r'resource_[0-9a-f]{24}')


def _safe_text(value, limit=300):
    if not isinstance(value, str) or len(value) > limit or any(ord(c) < 32 or ord(c) == 127 for c in value):
        return None
    try:
        assert_no_secret_keys(value)
        value.encode('utf-8')
    except (ValueError, UnicodeError):
        return None
    # Contact details are not needed in public programme titles or identifiers.
    if re.search(r'[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}|\b(?:account|wallet|private|session|password)\s*[:=]', value, re.I):
        return None
    return value


def _identifier(value):
    return value if isinstance(value, str) and _ID.fullmatch(value) and _safe_text(value) else None


def _timestamp(value):
    if not isinstance(value, str) or len(value) > 40:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            return None
        return parsed.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')
    except (ValueError, OverflowError):
        return None


def _age(value, now):
    normalized = _timestamp(value)
    if normalized is None:
        return None
    return (now - datetime.fromisoformat(normalized.replace('Z', '+00:00'))).total_seconds()


def _freshness(value, now):
    age = _age(value, now)
    if age is None:
        return 'UNKNOWN'
    if age < 0:
        return 'FUTURE'
    return 'FRESH' if age <= SOURCE_MAX_AGE_SECONDS else 'STALE'


def safe_url(value, allowed_hosts=OFFICIAL_HOSTS):
    """Only official HTTPS URLs with no credentials, fragments or private query."""
    if not isinstance(value, str) or len(value) >= 2000 or re.search(r'[\x00-\x20\\]', value):
        return None
    try:
        u = urlsplit(value)
        if u.scheme != 'https' or u.hostname not in allowed_hosts or u.username is not None or u.password is not None or u.port not in (None, 443) or u.fragment:
            return None
        path = unquote(u.path)
        if '\\' in path or any(ord(c) < 32 for c in path) or any(part in ('.', '..') for part in path.split('/')):
            return None
        assert_no_secret_keys(path)
        query = parse_qsl(u.query, keep_blank_values=True, strict_parsing=True) if u.query else []
        # The only discovery query currently necessary is the public bounty
        # issue filter. Reject unknown keys, duplicate keys and arbitrary values.
        if query:
            if u.hostname != 'api.github.com' or not re.fullmatch(r'/repos/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/issues', u.path):
                return None
            if len({key for key, _ in query}) != len(query):
                return None
            for key, item in query:
                if key == 'state' and item == 'open' or key == 'labels' and item == 'bounty':
                    continue
                if key in ('per_page', 'page') and item.isdigit() and 1 <= int(item) <= 100:
                    continue
                return None
        return urlunsplit(('https', u.hostname, u.path or '/', urlencode(query), ''))
    except (ValueError, OverflowError):
        return None


def _number(value, *, probability=False, nonnegative=True):
    if type(value) not in (int, float):
        return None
    try:
        result = float(value)
    except (ValueError, OverflowError):
        return None
    if not math.isfinite(result) or nonnegative and result < 0 or probability and result > 1:
        return None
    return value


def _proof(proof, official_url, allowed_hosts):
    if not isinstance(proof, dict):
        return None
    url = safe_url(proof.get('url'), allowed_hosts)
    link = safe_url(proof.get('observed_link'), allowed_hosts)
    digest = proof.get('content_sha256')
    observed = _timestamp(proof.get('observed_at', proof.get('observed_at_utc')))
    if (not url or official_url not in (url, link) or type(proof.get('http_status')) is not int
            or proof['http_status'] != 200 or not observed or not isinstance(digest, str)
            or not re.fullmatch(r'[0-9a-f]{64}', digest)):
        return None
    return {'url': url, 'observed_at_utc': observed, 'content_sha256': digest, 'http_status': 200}


def make_public_report(store, now=None):
    # Read only these three summaries. Do not read accounts, receipts, the
    # raw evidence collection, the event ledger or private packet payloads.
    clock = utc_now(now)
    sources, registered = [], {}
    for source in store.list_sources():
        if not isinstance(source, dict):
            continue
        config = source.get('config', source)
        if not isinstance(config, dict):
            continue
        provider = config.get('provider')
        sid = _identifier(source.get('source_id', config.get('source_id')))
        if not isinstance(provider, str) or provider not in PROVIDER_HOSTS or not sid:
            continue
        allowed = PROVIDER_HOSTS[provider]
        url = safe_url(config.get('url'), allowed)
        if not url or config.get('method', 'READ_ONLY') != 'READ_ONLY':
            continue
        registered[sid] = (provider, allowed)
        status = source.get('access_status', source.get('last_status'))
        scanned = _timestamp(source.get('last_scan_at_utc', source.get('last_scan_at')))
        fresh = _freshness(scanned, clock)
        public_status = status if isinstance(status, str) and status in PUBLIC_ACCESS else 'ACCESS UNAVAILABLE'
        if public_status == 'ACCESS VERIFIED' and fresh != 'FRESH':
            public_status = 'ACCESS STALE' if fresh == 'STALE' else 'ACCESS UNAVAILABLE'
        sources.append({'source_id': sid, 'provider': provider, 'url': url,
                        'enabled': config.get('enabled') is True,
                        'last_scan_at_utc': scanned, 'observation_freshness': fresh,
                        'last_status': public_status})
    rows = []
    for record in store.opportunities(limit=1000, now=clock):
        if not isinstance(record, dict) or record.get('privacy') in ('PRIVATE', 'CONFIDENTIAL') or record.get('private') is True:
            continue
        sid = record.get('source_id')
        if not isinstance(sid, str) or sid not in registered:
            continue
        provider, allowed = registered[sid]
        oid = record.get('opportunity_id')
        if not isinstance(oid, str) or not _RESOURCE_ID.fullmatch(oid):
            continue
        official = safe_url(record.get('official_url'), allowed)
        proof = _proof(record.get('source_evidence'), official, allowed) if official else None
        if not official or not proof:
            continue
        kind, classification = record.get('type'), record.get('classification')
        if not isinstance(kind, str) or kind not in PUBLIC_TYPES or not isinstance(classification, str) or classification not in PUBLIC_CLASSIFICATIONS:
            continue
        title = _safe_text(record.get('title'), 500)
        if not title:
            continue
        ev = record.get('ev_status')
        row = {'opportunity_id': oid, 'source_id': sid, 'provider': provider, 'type': kind,
               'title': title, 'official_url': official,
               'deadline_utc': _timestamp(record.get('deadline_utc', record.get('deadline'))),
               'last_verified_at_utc': _timestamp(record.get('last_verified_at_utc')),
               'classification': classification, 'ev_status': ev if ev in ('CALCULATED', 'DATA INSUFFICIENT') else 'DATA INSUFFICIENT',
               'discovery_only': record.get('discovery_only') is True, 'source_evidence': [proof]}
        freshness = _freshness(proof['observed_at_utc'], clock)
        row['evidence_freshness'] = freshness
        if freshness != 'FRESH' and row['classification'] != 'SKIP':
            row['classification'] = 'DATA INSUFFICIENT'
        # An advertised ceiling is never used as the expected reward or EV.
        row['advertised_max_reward_usd'] = _number(record.get('advertised_max_reward_usd'))
        for field in ('detail_verified_at_utc', 'programme_launch_at_utc', 'programme_updated_at_utc', 'availability_checked_at_utc'):
            row[field] = _timestamp(record.get(field))
        for field, allowed_values in (
            ('verification_scope', ('PROGRAM_DETAIL', 'PUBLIC_PROGRAM_TERMS_ONLY', 'PUBLIC_CLAIM_TERMS_ONLY', 'PROGRAM_CATALOGUE', 'CATALOGUE_LINK', 'PROGRAM_DISCOVERY')),
            ('detail_status', ('VERIFIED', 'ACTIVE', 'INACTIVE', 'UNAVAILABLE', 'NOT_CHECKED')),
            ('availability_status', ('ACTIVE', 'INACTIVE', 'UNAVAILABLE', 'UNKNOWN')),
        ):
            value = record.get(field)
            row[field] = value if isinstance(value, str) and value in allowed_values else None
        for key in PUBLIC_NUMBERS:
            row[key] = _number(record.get(key), probability=key == 'reward_probability', nonnegative=key != 'expected_net_reward_usd')
        for key in PUBLIC_CODES:
            value = record.get(key)
            row[key] = [item for item in value[:100] if isinstance(item, str) and re.fullmatch(r'[a-z][a-z0-9_.:]{0,100}', item) and _safe_text(item)] if isinstance(value, list) else []
        rows.append(row)
    # status() is a summary. Export only its typed integrity boolean.
    status = store.status()
    integrity = status.get('ledger_integrity', status.get('ledger_valid')) if isinstance(status, dict) else None
    enabled = [source for source in sources if source['enabled']]
    fresh_sources = sum(source['last_status'] == 'ACCESS VERIFIED' for source in enabled)
    stale = sum(row['evidence_freshness'] != 'FRESH' for row in rows)
    missing_ev = sum(row['expected_net_reward_usd'] is None for row in rows)
    classes = {value: sum(row['classification'] == value for row in rows) for value in sorted(PUBLIC_CLASSIFICATIONS)}
    quality = {
        'status': 'HEALTHY' if integrity is True and enabled and fresh_sources == len(enabled) else 'DEGRADED',
        'decision_readiness': 'DATA INSUFFICIENT' if not classes['QUEUE'] else 'REVIEW REQUIRED',
        'enabled_sources': len(enabled), 'fresh_verified_sources': fresh_sources,
        'unavailable_or_stale_sources': len(enabled) - fresh_sources,
        'stale_or_undated_candidates': stale, 'missing_ev_candidates': missing_ev,
        'detail_verified_candidates': sum(row['verification_scope'] in ('PROGRAM_DETAIL', 'PUBLIC_PROGRAM_TERMS_ONLY', 'PUBLIC_CLAIM_TERMS_ONLY') and row['evidence_freshness'] == 'FRESH' for row in rows),
        'provider_count': len({source['provider'] for source in enabled}),
        'classification_counts': classes,
        'source_max_age_seconds': SOURCE_MAX_AGE_SECONDS,
    }
    return {'schema_version': '1.1', 'system': 'MONEY Ω', 'rail': 'RESOURCE',
            'generated_at_utc': clock.isoformat().replace('+00:00', 'Z'),
            'mode': 'READ_ONLY', 'verified_income_usd': None, 'income_status': 'NO VERIFIED RECEIPTS',
            'schedule': 'Every six hours, plus code updates and manual runs; platform delays possible',
            'opportunities': rows, 'sources': sources, 'opportunity_count': len(rows),
            'queue_count': sum(row['classification'] == 'QUEUE' for row in rows),
            'quality': quality,
            'ledger_integrity': integrity if type(integrity) is bool else None,
            'direct_chatgpt_to_codex': False, 'direct_grok_bot_connected': False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--state-dir', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    report = make_public_report(Store(args.state_dir))
    if report['ledger_integrity'] is not True:
        raise SystemExit('Public export rejected: ledger integrity is not verified')
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'public_opportunity_count': report['opportunity_count']}))

if __name__ == '__main__':
    main()
