"""Bounded public GET monitoring; never a market writer or execution service.

Scope: six-asset 5m snapshot and BTC 5m archive only. No prices, odds, account
fields, response bodies, headers or credentials enter the operational output.
A successful handler response proves neither cron configuration nor persistence.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import http.client
import json
import math
import os
from pathlib import Path
import re
import sys
import tempfile
import urllib.error
import urllib.request

from .models import utc_now
from .packets import strict_json_loads

BASE = 'https://api-v2.appdeploy.ai/app/money-z6epdn/api/'
SPAN = 300_000
MAX_BYTES = 2_000_000
TIMEOUT = 12
ASSETS = ('BTC', 'ETH', 'SOL', 'DOGE', 'XRP', 'BNB')
CDMX = timezone(timedelta(hours=-6))  # The app's declared calendar encoding.


def _ms(value):
    try:
        if type(value) not in (int, float) or not math.isfinite(value) or int(value) != value:
            return None
        datetime.fromtimestamp(value / 1000, timezone.utc)
        return int(value)
    except (OverflowError, ValueError, OSError):
        return None


def _iso(value):
    return datetime.fromtimestamp(value / 1000, timezone.utc).isoformat().replace('+00:00', 'Z') if value is not None else None


def _date(value):
    if not isinstance(value, str) or not re.fullmatch(r'20\d\d-\d\d-\d\d', value):
        raise ValueError('invalid_calendar_date')
    try:
        parsed = datetime.strptime(value, '%Y-%m-%d')
    except ValueError as exc:
        raise ValueError('invalid_calendar_date') from exc
    return parsed.replace(tzinfo=CDMX)


def _paper(research):
    return (isinstance(research, dict) and research.get('strategy') == 'MONEY_FIXED_WINDOW_ANALOG_PAPER_V1'
            and research.get('calibrated') is False and 'contractProbability' in research
            and research['contractProbability'] is None and research.get('recommendation') == 'WAIT')


def inspect_snapshot(payload, now=None):
    """Inspect timestamps and declared PAPER flags, without publishing prices."""
    result = {'scope': 'SIX_ASSETS_5m_SNAPSHOT', 'state': 'DATA INSUFFICIENT', 'as_of_utc': None,
              'expires_at_utc': None, 'window_start_utc': None, 'window_end_utc': None,
              'snapshot_age_seconds': None, 'paper_flags_verified': False,
              'venue_readings': None, 'source_tick_count': None, 'fresh_source_tick_count': None,
              'reported_live_count': None, 'unverified_live_claim_count': None,
              'published_without_tick_count': None, 'issues': []}
    issues = result['issues']
    try:
        current = int(utc_now(now).timestamp() * 1000)
    except ValueError:
        issues.append('invalid_clock'); return result
    if not isinstance(payload, dict):
        issues.append('payload_not_object'); return result
    stamps = {key: _ms(payload.get(key)) for key in ('asOf', 'expiresAt', 'windowStart', 'windowEnd', 'serverTime', 'serverReceivedAt')}
    result.update(as_of_utc=_iso(stamps['asOf']), expires_at_utc=_iso(stamps['expiresAt']),
                  window_start_utc=_iso(stamps['windowStart']), window_end_utc=_iso(stamps['windowEnd']))
    if payload.get('version') != '1.1.0' or payload.get('timeframe') != '5m':
        issues.append('unsupported_snapshot_scope')
    if any(value is None for value in stamps.values()):
        issues.append('invalid_timestamp'); return result
    observed, expiry, start, end, server, received = (stamps[key] for key in ('asOf','expiresAt','windowStart','windowEnd','serverTime','serverReceivedAt'))
    result['snapshot_age_seconds'] = round((current - observed) / 1000, 3)
    if end - start != SPAN or start % SPAN or not start <= observed < end or not observed < expiry <= min(end, observed + 45_000):
        issues.append('invalid_snapshot_window')
    if observed > server or received > server or server > current + 5000:
        issues.append('invalid_server_clock')
    if any(stamp > current + 5000 for stamp in (observed, received)):
        issues.append('future_snapshot')
    rows = payload.get('assets')
    if not isinstance(rows, list) or len(rows) != len(ASSETS) or any(not isinstance(row, dict) for row in rows):
        issues.append('incomplete_asset_rows'); return result
    symbols = [row.get('symbol') for row in rows]
    if any(not isinstance(symbol, str) for symbol in symbols) or sorted(symbols) != sorted(ASSETS):
        issues.append('invalid_asset_identity')
    result.update(venue_readings=0, source_tick_count=0, fresh_source_tick_count=0,
                  reported_live_count=0, unverified_live_claim_count=0, published_without_tick_count=0)
    result['paper_flags_verified'] = all(_paper(row.get('research')) for row in rows)
    if not result['paper_flags_verified']:
        issues.append('paper_flags_not_verified')
    for row in rows:
        if _ms(row.get('windowStart')) != start or _ms(row.get('windowEnd')) != end:
            issues.append('asset_window_mismatch')
        venues = row.get('venues')
        if not isinstance(venues, list) or not venues or any(not isinstance(venue, dict) for venue in venues):
            issues.append('invalid_venue_rows'); continue
        for venue in venues:
            result['venue_readings'] += 1
            tick, read = _ms(venue.get('quoteAt')), _ms(venue.get('receivedAt'))
            if tick is not None:
                result['source_tick_count'] += 1
            fresh = (tick is not None and read is not None and start <= tick <= read <= current
                     and 0 <= current - tick <= 30_000 and current - read <= 90_000
                     and _ms(venue.get('windowStart')) == start and _ms(venue.get('windowEnd')) == end
                     and isinstance(venue.get('contractId'), str) and bool(venue['contractId'].strip()))
            if fresh:
                result['fresh_source_tick_count'] += 1
            if venue.get('status') == 'PUBLICADO' and venue.get('quoteAt') is None:
                result['published_without_tick_count'] += 1
            if venue.get('status') == 'LIVE':
                result['reported_live_count'] += 1
                if not fresh:
                    result['unverified_live_claim_count'] += 1
                    issues.append('live_claim_without_verified_tick')
    stale = current >= expiry or current >= end or current - server > 90_000
    result['issues'] = sorted(set(issues))
    result['state'] = 'DATA INSUFFICIENT' if issues else 'STALE' if stale else 'FRESH'
    return result


def inspect_archive(payload, now=None, expected_date=None):
    """Count actual captures, ignoring display labels; closed missing slots form gaps.

    Missing past includes an invalid capture in an elapsed slot. Current windows
    stay pending until their close; a capture must have real asOf in [start,end).
    """
    result = {'scope': 'BTC_5m_ARCHIVE_ONLY', 'timezone': 'America/Mexico_City', 'utc_offset_minutes': -360,
              'date': None, 'state': 'DATA INSUFFICIENT', 'as_of_utc': None,
              'as_of_age_seconds': None, 'freshness': 'UNKNOWN',
              'captured_count': None, 'missing_past_count': None, 'future_count': None,
              'pending_current_count': None, 'invalid_capture_count': None,
              'paper_flags_verified': False, 'gap_group_count': None, 'gaps': [], 'issues': []}
    issues = result['issues']
    try:
        clock = utc_now(now)
        current = int(clock.timestamp() * 1000)
        requested = expected_date if expected_date is not None else clock.astimezone(CDMX).date().isoformat()
        day_start = int(_date(requested).timestamp() * 1000)
    except ValueError:
        issues.append('invalid_clock_or_date'); return result
    result['date'] = requested
    if not isinstance(payload, dict):
        issues.append('payload_not_object'); return result
    observed = _ms(payload.get('asOf'))
    result['as_of_utc'] = _iso(observed)
    if (payload.get('version') != '1.1.0' or payload.get('date') != requested or payload.get('symbol') != 'BTC'
            or payload.get('timeframe') != '5m' or _ms(payload.get('start')) != day_start):
        issues.append('archive_scope_or_date_mismatch'); return result
    if observed is None or observed > current + 5000:
        issues.append('invalid_archive_timestamp'); return result
    result['as_of_age_seconds'] = round((current - observed) / 1000, 3)
    result['freshness'] = 'STALE' if current - observed > 90_000 else 'FRESH'
    if day_start > current:
        issues.append('future_archive_date'); return result
    rows = payload.get('calendar')
    if not isinstance(rows, list) or len(rows) != 288:
        issues.append('incomplete_calendar'); return result
    if any(not isinstance(row, dict) or type(row.get('index')) is not int or row['index'] != i + 1
           or _ms(row.get('start')) != day_start + i * SPAN or _ms(row.get('end')) != day_start + (i + 1) * SPAN
           or 'capture' not in row for i, row in enumerate(rows)):
        issues.append('invalid_calendar_grid'); return result
    result.update(captured_count=0, missing_past_count=0, future_count=0, pending_current_count=0, invalid_capture_count=0)
    cutoff = min(current, observed)
    missing = []
    paper_checks = []
    for i, row in enumerate(rows):
        start, end = day_start + i * SPAN, day_start + (i + 1) * SPAN
        capture = row['capture']
        valid = False
        if capture is not None:
            stored = capture.get('row') if isinstance(capture, dict) else None
            timestamp = _ms(capture.get('asOf')) if isinstance(capture, dict) else None
            valid = (isinstance(stored, dict) and timestamp is not None and start <= timestamp < end
                     and timestamp <= cutoff and stored.get('symbol') == 'BTC'
                     and _ms(stored.get('windowStart')) == start and _ms(stored.get('windowEnd')) == end)
            if valid:
                result['captured_count'] += 1
                paper_checks.append(_paper(stored.get('research')))
            else:
                result['invalid_capture_count'] += 1
        if not valid:
            if end <= cutoff:
                result['missing_past_count'] += 1; missing.append(i)
            elif start > cutoff:
                result['future_count'] += 1
            else:
                result['pending_current_count'] += 1
    groups = []
    for index in missing:
        if groups and index == groups[-1][1] + 1:
            groups[-1][1] = index
        else:
            groups.append([index, index])
    result['gap_group_count'] = len(groups)
    result['gaps'] = [{'start_utc': _iso(day_start + first * SPAN), 'end_utc_exclusive': _iso(day_start + (last + 1) * SPAN),
                       'window_count': last - first + 1} for first, last in groups[:5]]
    result['paper_flags_verified'] = bool(paper_checks) and all(paper_checks)
    if type(payload.get('captureCount')) is not int or payload['captureCount'] != result['captured_count']:
        issues.append('capture_count_not_reconciled')
    if paper_checks and not all(paper_checks):
        issues.append('paper_flags_not_verified')
    if result['invalid_capture_count']:
        issues.append('invalid_captures')
    if result['missing_past_count']:
        issues.append('archive_gaps')
    result['state'] = 'DEGRADED' if issues else 'STALE' if current - observed > 90_000 else 'VERIFIED'
    return result


# Explicit names for callers porting the original app's camelCase types.
inspectSnapshot = inspect_snapshot
inspectArchive = inspect_archive


def _urls(day):
    _date(day)
    return {'health': BASE + '_healthcheck', 'snapshot': BASE + 'snapshot?tf=5m',
            'archive': BASE + 'dayplan?asset=BTC&tf=5m&date=' + day}


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _fetch(url):
    # No configurable URLs, auth headers, cookies, POSTs or redirect traversal.
    permitted = url in (BASE + '_healthcheck', BASE + 'snapshot?tf=5m')
    prefix = BASE + 'dayplan?asset=BTC&tf=5m&date='
    if not permitted and isinstance(url, str) and url.startswith(prefix):
        try:
            permitted = url == prefix + _date(url[len(prefix):]).date().isoformat()
        except ValueError:
            permitted = False
    if not permitted:
        raise ValueError('noncanonical_monitor_endpoint')
    result = {'http_status': None, 'access_status': 'ACCESS UNAVAILABLE', 'method': 'GET'}
    request = urllib.request.Request(url, method='GET', headers={'User-Agent':'MONEY-Omega-ReadOnly-Monitor/1.0', 'Accept':'application/json', 'Accept-Encoding':'identity'})
    try:
        with urllib.request.build_opener(_NoRedirect()).open(request, timeout=TIMEOUT) as response:
            code = response.status
            result['http_status'] = code if type(code) is int and 100 <= code <= 599 else None
            if code != 200 or response.geturl() != url:
                result['error_code'] = 'http_or_redirect_unavailable'; return result
            if response.headers.get('Content-Encoding', 'identity').lower() not in ('', 'identity'):
                result['error_code'] = 'unsupported_content_encoding'; return result
            if response.headers.get('Content-Type', '').split(';', 1)[0].lower() != 'application/json':
                result.update(access_status='ACCESS PARTIAL', error_code='response_not_json'); return result
            length = response.headers.get('Content-Length')
            if length and (not length.isdigit() or int(length) > MAX_BYTES):
                result['error_code'] = 'response_too_large'; return result
            raw = response.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                result['error_code'] = 'response_too_large'; return result
            try:
                payload = strict_json_loads(raw)
            except ValueError:
                result.update(access_status='ACCESS PARTIAL', error_code='invalid_json'); return result
            result.update(access_status='ACCESS VERIFIED', byte_count=len(raw), body_sha256=hashlib.sha256(raw).hexdigest(), payload=payload)
    except urllib.error.HTTPError as exc:
        result['http_status'] = exc.code if type(exc.code) is int and 100 <= exc.code <= 599 else None
        result['error_code'] = 'http_unavailable'
        exc.close()
    except (urllib.error.URLError, OSError, TimeoutError, ValueError, http.client.HTTPException):
        result['error_code'] = 'network_unavailable'
    return result


def monitor(*, now=None, day=None, fetcher=None):
    initial = utc_now(now)
    requested = day if day is not None else initial.astimezone(CDMX).date().isoformat()
    urls = _urls(requested)
    read = _fetch if fetcher is None else fetcher
    responses = {name: read(url) for name, url in urls.items()}
    clock = utc_now(now)
    endpoints = {}
    for name, response in responses.items():
        item = {key: response[key] for key in ('http_status', 'access_status', 'method', 'byte_count', 'body_sha256', 'error_code') if key in response}
        if 'payload' not in response:
            item['inspection'] = {'state': 'UNAVAILABLE'}
        elif name == 'snapshot':
            item['inspection'] = inspect_snapshot(response['payload'], clock)
        elif name == 'archive':
            item['inspection'] = inspect_archive(response['payload'], clock, requested)
        else:
            payload = response['payload']
            good = (isinstance(payload, dict) and payload.get('version') == '1.1.0'
                    and payload.get('assets') == list(ASSETS) and payload.get('frames') == ['5m','15m','1h']
                    and 'contractProbability' in payload and payload['contractProbability'] is None)
            item['inspection'] = {'state': 'VERIFIED' if good else 'DATA INSUFFICIENT', 'cron_status': 'NOT CHECKED'}
        state = item['inspection']['state']
        if state == 'STALE': item['access_status'] = 'ACCESS STALE'
        elif state == 'DATA INSUFFICIENT': item['access_status'] = 'ACCESS PARTIAL'
        endpoints[name] = item
    good = all(row['inspection']['state'] in ('FRESH', 'VERIFIED') for row in endpoints.values())
    return {'schema_version':'1.0', 'system':'MONEY Ω', 'mode':'READ_ONLY',
            'generated_at_utc':clock.isoformat().replace('+00:00','Z'), 'status':'OBSERVATION ONLY' if good else 'DEGRADED',
            'archive_scope':'BTC 5m only', 'archive_date':requested, 'endpoints':endpoints,
            'financial_execution_enabled':False, 'account_access_verified':False, 'cron_status':'NOT CHECKED',
            'direct_chatgpt_to_codex':False, 'direct_grok_bot_connected':False,
            'notice':'Public endpoint reads do not verify cron configuration, other asset archives, agent connectivity or executable edge.'}


def main(argv=None):
    parser = argparse.ArgumentParser(description='MONEY public market observation monitor; never an archive writer')
    parser.add_argument('--output', required=True)
    parser.add_argument('--date', dest='day')
    args = parser.parse_args(argv)
    if args.day is not None:
        try: _date(args.day)
        except ValueError: parser.error('date must be a valid YYYY-MM-DD in 2000–2099')
    report = monitor(day=args.day)
    path = Path(args.output)
    if path.is_symlink(): raise ValueError('monitor_output_must_not_be_symlink')
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix='.market-monitor-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write('\n')
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)
    print(json.dumps({'status':report['status'], 'archive_scope':report['archive_scope'], 'mode':'READ_ONLY'}))
    return 0  # An observed outage degrades the report, independently of discovery.


if __name__ == '__main__':
    raise SystemExit(main())
