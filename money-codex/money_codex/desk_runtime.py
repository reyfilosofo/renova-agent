"""Prospective PAPER desk storage and bounded public Coinbase USD observations.

This module has no order, account, wallet, credential or financial adapter.
A collection command performs one bounded pass. Recurrence belongs to its host.
"""
from __future__ import annotations

import argparse
import contextlib
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import http.client
import json
import math
import os
from pathlib import Path
import sqlite3
import tempfile
import time
import urllib.error
import urllib.request
import uuid

from .models import parse_utc, utc_now
from .packets import canonical_json, strict_json_loads

ASSETS = ('BTC', 'ETH', 'SOL', 'DOGE', 'XRP', 'BNB')
BASE = 'https://api.exchange.coinbase.com/products/'
DEFAULT_STATE = Path('/workspace/money/.local-data/desk-PAPER')
MAX_BYTES = 131072
MAX_AGE = 90
MIN_INTERVAL = 240
LEASE_SECONDS = 180


def require_paper(mode='PAPER'):
    if mode != 'PAPER' or os.environ.get('MONEY_DESK_MODE', 'PAPER') != 'PAPER' or os.environ.get('MONEY_EXECUTION_MODE', 'READ_ONLY') not in ('READ_ONLY', 'PAPER'):
        raise ValueError('PAPER desk only; financial execution is not implemented')


def iso(value):
    return value.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')


def _decimal(value):
    if not isinstance(value, str) or len(value) > 64:
        raise ValueError('Invalid public price')
    try:
        amount = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError('Invalid public price') from exc
    if not amount.is_finite() or amount <= 0 or amount > Decimal('1e15'):
        raise ValueError('Invalid public price')
    return amount


def _url(asset):
    if asset not in ASSETS:
        raise ValueError('Unsupported asset')
    return BASE + asset + '-USD/ticker'


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def fetch_ticker(asset):
    """GET one canonical public ticker; retain a hash, never a raw response."""
    url = _url(asset)
    result = {'url': url, 'method': 'GET', 'http_status': None}
    started = time.monotonic()
    request = urllib.request.Request(url, method='GET', headers={
        'User-Agent': 'MONEY-Omega-PAPER-Desk/0.4', 'Accept': 'application/json', 'Accept-Encoding': 'identity'})
    try:
        with urllib.request.build_opener(_NoRedirect()).open(request, timeout=8) as response:
            result['http_status'] = response.status
            if response.status != 200 or response.geturl() != url:
                raise ValueError('HTTP or redirect unavailable')
            if response.headers.get('Content-Type', '').split(';', 1)[0].lower() != 'application/json':
                raise ValueError('JSON response required')
            if response.headers.get('Content-Encoding', 'identity').lower() not in ('', 'identity'):
                raise ValueError('Unsupported encoding')
            length = response.headers.get('Content-Length')
            if length and (not length.isdigit() or int(length) > MAX_BYTES):
                raise ValueError('Response size limit')
            raw = bytearray()
            read = getattr(response, 'read1', response.read)
            while True:
                if time.monotonic() - started >= 12:
                    raise TimeoutError('Public ticker read deadline')
                part = read(min(16384, MAX_BYTES + 1 - len(raw)))
                if not part:
                    break
                raw.extend(part)
                if len(raw) > MAX_BYTES:
                    raise ValueError('Response size limit')
            payload = strict_json_loads(bytes(raw))
            result.update(payload=payload, body_sha256=hashlib.sha256(raw).hexdigest())
    except urllib.error.HTTPError as exc:
        result.update(http_status=exc.code, error_code='HTTP_' + str(exc.code))
        exc.close()
    except (OSError, TimeoutError, ValueError, urllib.error.URLError, http.client.HTTPException):
        result['error_code'] = 'PUBLIC_TICKER_UNAVAILABLE'
    result['received_at_utc'] = iso(utc_now())
    return result


def normalize_ticker(asset, response, now=None):
    clock = utc_now(now)
    observation = {'asset': asset, 'product': asset + '-USD', 'source': 'COINBASE_EXCHANGE',
                   'quote_currency': 'USD', 'source_url': _url(asset), 'mode': 'PAPER',
                   'status': 'UNAVAILABLE', 'price': None, 'quote_at_utc': None, 'last_trade_price': None, 'bid': None, 'ask': None,
                   'last_trade_at_utc': None, 'received_at_utc': None, 'tick_age_seconds': None,
                   'timestamp_scope': 'LAST_TRADE_ONLY', 'bid_ask_timestamp_verified': False,
                   'body_sha256': None}
    if not isinstance(response, dict) or response.get('url') != _url(asset) or response.get('http_status') != 200:
        return observation
    try:
        payload = response['payload']
        if not isinstance(payload, dict):
            raise ValueError('Ticker object required')
        received = parse_utc(response['received_at_utc'])
        traded = parse_utc(payload['time'])
        digest = response['body_sha256']
        if not isinstance(digest, str) or len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
            raise ValueError('Response hash required')
        price, bid, ask = (_decimal(payload[key]) for key in ('price', 'bid', 'ask'))
        if bid > ask or traded > received or received > clock:
            raise ValueError('Inconsistent quote or timestamps')
        age = (clock - traded).total_seconds()
        read_age = (clock - received).total_seconds()
        observation.update(status='OBSERVED' if age <= MAX_AGE and read_age <= MAX_AGE else 'STALE',
                           price=str(price), quote_at_utc=iso(traded), last_trade_price=str(price), bid=str(bid), ask=str(ask), last_trade_at_utc=iso(traded),
                           received_at_utc=iso(received), tick_age_seconds=round(age, 3), body_sha256=digest)
    except (KeyError, ValueError, TypeError, OverflowError):
        pass
    return observation


class DeskStore:
    def __init__(self, state_dir=None):
        require_paper()
        self.state_dir = Path(os.path.abspath(Path(state_dir or os.environ.get('MONEY_DESK_STATE_DIR') or DEFAULT_STATE).expanduser()))
        self.state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        if self.state_dir.resolve() != self.state_dir:
            raise ValueError('Desk state cannot use symlinks')
        os.chmod(self.state_dir, 0o700)
        self.path = self.state_dir / 'desk-paper.sqlite3'
        if self.path.is_symlink():
            raise ValueError('Desk database cannot use symlinks')
        with self._db() as db:
            db.execute('PRAGMA journal_mode=WAL')
            db.executescript('''
                CREATE TABLE IF NOT EXISTS desk_observations(id TEXT PRIMARY KEY,asset TEXT NOT NULL,received REAL NOT NULL,payload TEXT NOT NULL);
                CREATE INDEX IF NOT EXISTS desk_observations_asset ON desk_observations(asset,received);
                CREATE TABLE IF NOT EXISTS desk_sources(asset TEXT PRIMARY KEY,last_attempt REAL NOT NULL,next_due REAL NOT NULL,payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS desk_records(id TEXT PRIMARY KEY,kind TEXT NOT NULL,record_key TEXT UNIQUE NOT NULL,payload_hash TEXT NOT NULL,payload TEXT NOT NULL,created REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS desk_cycles(id TEXT PRIMARY KEY,started REAL NOT NULL,finished REAL,state TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS desk_worker(name TEXT PRIMARY KEY,owner TEXT NOT NULL,token TEXT NOT NULL,expires REAL NOT NULL,cycle_id TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS desk_events(seq INTEGER PRIMARY KEY AUTOINCREMENT,kind TEXT NOT NULL,payload TEXT NOT NULL,created REAL NOT NULL,previous_hash TEXT NOT NULL,hash TEXT NOT NULL);
                CREATE TRIGGER IF NOT EXISTS desk_events_no_update BEFORE UPDATE ON desk_events BEGIN SELECT RAISE(ABORT,'append-only PAPER audit'); END;
                CREATE TRIGGER IF NOT EXISTS desk_events_no_delete BEFORE DELETE ON desk_events BEGIN SELECT RAISE(ABORT,'append-only PAPER audit'); END;
            ''')
        os.chmod(self.path, 0o600)

    @contextlib.contextmanager
    def _db(self, write=False):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA busy_timeout=10000')
        try:
            with db:
                if write:
                    db.execute('BEGIN IMMEDIATE')
                yield db
        finally:
            db.close()

    @staticmethod
    def _event(db, kind, payload, at):
        previous = db.execute('SELECT hash FROM desk_events ORDER BY seq DESC LIMIT 1').fetchone()
        previous_hash = previous['hash'] if previous else '0' * 64
        body = {'kind': kind, 'payload': payload, 'created': at, 'previous_hash': previous_hash}
        digest = hashlib.sha256(canonical_json(body)).hexdigest()
        db.execute('INSERT INTO desk_events(kind,payload,created,previous_hash,hash) VALUES(?,?,?,?,?)',
                   (kind, canonical_json(payload).decode(), at, previous_hash, digest))

    def acquire(self, owner, now=None):
        at = utc_now(now).timestamp()
        with self._db(write=True) as db:
            old = db.execute("SELECT * FROM desk_worker WHERE name='collect'").fetchone()
            if old and old['expires'] > at:
                return None
            if old:
                db.execute("UPDATE desk_cycles SET state='ABANDONED',finished=? WHERE id=? AND state='RUNNING'", (at, old['cycle_id']))
            token, cycle = str(uuid.uuid4()), str(uuid.uuid4())
            db.execute('INSERT INTO desk_cycles VALUES(?,?,NULL,?)', (cycle, at, 'RUNNING'))
            db.execute("INSERT INTO desk_worker VALUES('collect',?,?,?,?) ON CONFLICT(name) DO UPDATE SET owner=excluded.owner,token=excluded.token,expires=excluded.expires,cycle_id=excluded.cycle_id", (owner, token, at + LEASE_SECONDS, cycle))
            self._event(db, 'COLLECTION_STARTED', {'cycle_id': cycle}, at)
            return {'token': token, 'cycle_id': cycle, 'owner': owner}

    @staticmethod
    def _lease(db, lease, at):
        row = db.execute("SELECT * FROM desk_worker WHERE name='collect'").fetchone()
        if not row or row['owner'] != lease['owner'] or row['token'] != lease['token'] or row['expires'] <= at:
            raise ValueError('PAPER worker lease expired or superseded')
        return row

    def due(self, now=None):
        at = utc_now(now).timestamp()
        with self._db() as db:
            rows = {row['asset']: row['next_due'] for row in db.execute('SELECT asset,next_due FROM desk_sources')}
        return [asset for asset in ASSETS if rows.get(asset, 0) <= at]

    def finish(self, lease, observations, sources, reviews=(), now=None):
        at = utc_now(now).timestamp()
        for value in (observations, sources, list(reviews)):
            canonical_json(value)
        with self._db(write=True) as db:
            self._lease(db, lease, at)
            for observation in observations:
                if observation.get('asset') not in ASSETS or observation.get('mode') != 'PAPER':
                    raise ValueError('Invalid PAPER observation')
                if observation['received_at_utc'] is None:
                    continue
                digest = hashlib.sha256(canonical_json(observation)).hexdigest()
                db.execute('INSERT OR IGNORE INTO desk_observations VALUES(?,?,?,?)',
                           (digest, observation['asset'], parse_utc(observation['received_at_utc']).timestamp(), canonical_json(observation).decode()))
            for source in sources:
                if source.get('asset') not in ASSETS:
                    raise ValueError('Invalid source identity')
                due = at + source.get('retry_after_seconds', MIN_INTERVAL)
                db.execute('INSERT INTO desk_sources VALUES(?,?,?,?) ON CONFLICT(asset) DO UPDATE SET last_attempt=excluded.last_attempt,next_due=excluded.next_due,payload=excluded.payload',
                           (source['asset'], at, due, canonical_json(source).decode()))
            for review in reviews:
                self._record(db, 'REVIEW', review, lease['cycle_id'] + ':' + review['timeframe'], at)
            db.execute("UPDATE desk_cycles SET state='FINISHED',finished=? WHERE id=?", (at, lease['cycle_id']))
            db.execute("DELETE FROM desk_worker WHERE name='collect' AND token=?", (lease['token'],))
            self._event(db, 'COLLECTION_FINISHED', {'cycle_id': lease['cycle_id'], 'observations': len(observations), 'reviews': len(reviews)}, at)

    def release(self, lease, now=None):
        at = utc_now(now).timestamp()
        with self._db(write=True) as db:
            row = db.execute("SELECT token FROM desk_worker WHERE name='collect'").fetchone()
            if row and row['token'] == lease['token']:
                db.execute("UPDATE desk_cycles SET state='INTERRUPTED',finished=? WHERE id=? AND state='RUNNING'", (at, lease['cycle_id']))
                db.execute("DELETE FROM desk_worker WHERE name='collect' AND token=?", (lease['token'],))

    @staticmethod
    def _record(db, kind, payload, key, at):
        if kind not in ('JUDGMENT', 'REVIEW', 'OUTCOME', 'POSTMORTEM') or not isinstance(key, str) or not 1 <= len(key) <= 200:
            raise ValueError('Invalid PAPER record identity')
        if not isinstance(payload, dict):
            raise ValueError('PAPER record must be an object')
        require_paper(payload.get('mode'))
        if any(payload.get(field, False) is not False for field in ('financial_execution_enabled', 'live_execution_enabled', 'execution_enabled', 'account_truth_verified', 'executionEnabled', 'financialAuthority', 'approvedForPaper')):
            raise ValueError('Financial authority cannot enter PAPER records')
        body = canonical_json(payload).decode()
        digest = hashlib.sha256(body.encode()).hexdigest()
        previous = db.execute('SELECT id,kind,payload_hash FROM desk_records WHERE record_key=?', (key,)).fetchone()
        if previous:
            if previous['kind'] != kind or previous['payload_hash'] != digest:
                raise ValueError('PAPER record idempotency conflict')
            return previous['id']
        if kind in ('JUDGMENT', 'OUTCOME'):
            for prior_row in db.execute('SELECT id,payload_hash,payload FROM desk_records WHERE kind=?', (kind,)):
                prior_payload = json.loads(prior_row['payload'])
                if prior_payload.get('judgment_id') == payload.get('judgment_id'):
                    if prior_row['payload_hash'] != digest:
                        raise ValueError('Prospective judgment identity conflict')
                    return prior_row['id']
        if kind == 'JUDGMENT':
            if (not isinstance(payload.get('judgment_id'), str) or not payload['judgment_id']
                    or parse_utc(payload.get('issued_at_utc')).timestamp() > at
                    or parse_utc(payload.get('contract_end_utc')).timestamp() <= at):
                raise ValueError('Judgments must be prospective')
        if kind == 'OUTCOME':
            target = payload.get('judgment_id')
            judgments = [json.loads(row['payload']) for row in db.execute("SELECT payload FROM desk_records WHERE kind='JUDGMENT'")]
            prior = next((item for item in judgments if item.get('judgment_id') == target), None)
            if (prior is None or parse_utc(prior['contract_end_utc']).timestamp() > at
                    or parse_utc(payload.get('settled_at_utc')).timestamp() > at
                    or parse_utc(payload['settled_at_utc']) < parse_utc(prior['contract_end_utc'])):
                raise ValueError('An elapsed prospective judgment is required')
        identifier = str(uuid.uuid4())
        db.execute('INSERT INTO desk_records VALUES(?,?,?,?,?,?)', (identifier, kind, key, digest, body, at))
        DeskStore._event(db, 'PAPER_' + kind + '_REGISTERED', {'record_id': identifier, 'payload_sha256': digest}, at)
        return identifier

    def append_record(self, kind, payload, idempotency_key, now=None):
        with self._db(write=True) as db:
            return self._record(db, kind, payload, idempotency_key, utc_now(now).timestamp())

    def latest(self, now=None):
        clock = utc_now(now)
        with self._db() as db:
            sources = {row['asset']: json.loads(row['payload']) for row in db.execute('SELECT asset,payload FROM desk_sources')}
            quotes = {}
            for row in db.execute('SELECT asset,payload FROM desk_observations ORDER BY received'):
                quotes[row['asset']] = json.loads(row['payload'])
        rows = []
        source_rows = []
        for asset in ASSETS:
            quote = quotes.get(asset) or normalize_ticker(asset, {}, now=clock)
            if quote.get('received_at_utc') and quote.get('last_trade_at_utc'):
                quote['tick_age_seconds'] = round((clock - parse_utc(quote['last_trade_at_utc'])).total_seconds(), 3)
                if quote['tick_age_seconds'] < 0 or quote['tick_age_seconds'] > MAX_AGE or not 0 <= (clock - parse_utc(quote['received_at_utc'])).total_seconds() <= MAX_AGE:
                    quote['status'] = 'STALE'
            source = sources.get(asset, {'asset': asset, 'status': 'UNAVAILABLE', 'access_status': 'ACCESS UNAVAILABLE',
                                         'http_status': None, 'last_attempt_at_utc': None, 'error_code': 'NOT_FETCHED'})
            if source.get('status') == 'UNAVAILABLE':
                quote['status'] = 'UNAVAILABLE'
            elif quote['status'] == 'STALE':
                source['status'] = 'STALE'
                source['access_status'] = 'ACCESS STALE'
            source_rows.append(source)
            rows.append(quote)
        return rows, source_rows

    def public_report(self, now=None, state='EXPORTED', reviews=None, snapshots=None):
        clock = utc_now(now)
        observations, sources = self.latest(clock)
        if reviews is None:
            with self._db() as db:
                latest_reviews = {}
                for record in db.execute("SELECT payload FROM desk_records WHERE kind='REVIEW' ORDER BY created"):
                    review = json.loads(record['payload'])
                    if review.get('timeframe') in ('5m', '15m', '1h'):
                        latest_reviews[review['timeframe']] = review
            reviews = [latest_reviews[frame] for frame in ('5m', '15m', '1h') if frame in latest_reviews]
        risk_state = 'HALT'
        try:
            if (reviews and any(row['status'] == 'OBSERVED' for row in observations)
                    and all(0 <= (clock - parse_utc(review['generated_at_utc'])).total_seconds() <= 30 for review in reviews)):
                states = {review.get('risk', {}).get('state') for review in reviews}
                risk_state = 'HALT' if not states or not states <= {'HALT', 'ABSTAIN', 'WATCH'} or 'HALT' in states else 'WATCH' if 'WATCH' in states else 'ABSTAIN'
        except (KeyError, ValueError, TypeError):
            pass
        return {'schema_version': '1.0', 'system': 'MONEY Ω', 'mode': 'PAPER', 'state': state,
                'generated_at_utc': iso(clock), 'observations': observations, 'source_status': sources,
                'fresh_observation_count': sum(row['status'] == 'OBSERVED' for row in observations),
                'observations_max_age_seconds': MAX_AGE, 'reviews': reviews, 'snapshots': snapshots or [],
                'risk_state': risk_state, **self.status()}

    def status(self):
        with self._db() as db:
            counts = {name: db.execute('SELECT count(*) FROM desk_' + name).fetchone()[0] for name in ('observations', 'sources', 'records', 'cycles')}
            previous = '0' * 64
            valid = True
            try:
                for row in db.execute('SELECT * FROM desk_events ORDER BY seq'):
                    body = {'kind': row['kind'], 'payload': json.loads(row['payload']), 'created': row['created'], 'previous_hash': row['previous_hash']}
                    if row['previous_hash'] != previous or hashlib.sha256(canonical_json(body)).hexdigest() != row['hash']:
                        valid = False; break
                    previous = row['hash']
            except ValueError:
                valid = False
        return {'mode': 'PAPER', 'counts': counts, 'audit_integrity': valid,
                'paper_execution_enabled': False, 'live_execution_enabled': False, 'account_truth_verified': False}


def collect_desk(state_dir=None, policy=None, now=None, fetcher=None):
    require_paper()
    store = DeskStore(state_dir)
    started = utc_now(now)
    lease = store.acquire('paper-worker-' + str(uuid.uuid4()), now=started)
    if lease is None:
        return store.public_report(started, state='WORKER_BUSY')
    began = time.monotonic()
    observations, sources, blocked = [], [], None
    read = fetch_ticker if fetcher is None else fetcher
    try:
        for asset in store.due(now=started):
            if time.monotonic() - began > 150:
                raise TimeoutError('PAPER collection deadline')
            if blocked:
                sources.append({'asset': asset, 'status': 'UNAVAILABLE', 'access_status': 'ACCESS UNAVAILABLE', 'http_status': None,
                                'last_attempt_at_utc': None, 'error_code': 'NOT_FETCHED_AFTER_PROVIDER_BLOCK', 'retry_after_seconds': blocked})
                continue
            if fetcher is None and observations:
                time.sleep(1)
            response = read(asset)
            clock = utc_now(now)
            quote = normalize_ticker(asset, response, now=clock)
            observations.append(quote)
            code = response.get('http_status') if isinstance(response, dict) else None
            state = {'asset': asset, 'status': quote['status'], 'access_status': 'ACCESS VERIFIED' if quote['status'] == 'OBSERVED' else 'ACCESS STALE' if quote['status'] == 'STALE' else 'ACCESS UNAVAILABLE', 'http_status': code,
                     'last_attempt_at_utc': iso(clock), 'retry_after_seconds': MIN_INTERVAL}
            if quote['status'] == 'UNAVAILABLE':
                state['error_code'] = 'PRODUCT_UNAVAILABLE' if code == 404 else 'PUBLIC_TICKER_UNAVAILABLE'
            if code in (403, 429, 451):
                blocked = 3600 if code == 451 else 900
                state['retry_after_seconds'] = blocked
            sources.append(state)
        finished = utc_now(now)
        previous, _ = store.latest(now=finished)
        by_asset = {row['asset']: row for row in previous}
        by_asset.update({row['asset']: row for row in observations})
        for source in sources:
            if source['status'] == 'UNAVAILABLE':
                by_asset[source['asset']] = normalize_ticker(source['asset'], {}, now=finished)
        spot_fields = {'asset', 'product', 'source', 'quote_currency', 'last_trade_price', 'bid', 'ask',
                       'last_trade_at_utc', 'received_at_utc', 'status', 'bid_ask_timestamp_verified'}
        def engine_spot(observation):
            projected = {key: value for key, value in observation.items() if key in spot_fields}
            for field in ('last_trade_price', 'bid', 'ask'):
                projected[field] = float(projected[field]) if projected.get(field) is not None else None
            return projected
        # Explicitly no contracts or calibrated probabilities are synthesized.
        snapshots = [{'schema_version': '1.0', 'mode': 'PAPER', 'timeframe': frame,
                      'observed_at_utc': iso(finished), 'assets': [
                          {'asset': asset, 'contracts': [], 'spot_observation': engine_spot(by_asset[asset])} for asset in ASSETS]}
                     for frame in ('5m', '15m', '1h')]
        from .desk import review_desk
        reviews = [{**review_desk(snapshot, policy, judgments=[], now=finished), 'timeframe': snapshot['timeframe']} for snapshot in snapshots]
        store.finish(lease, observations, sources, reviews, now=finished)
        state = 'COLLECTED' if any(row['status'] == 'OBSERVED' for row in observations) else 'DEGRADED' if observations else 'COOLDOWN'
        return store.public_report(finished, state=state, reviews=reviews, snapshots=snapshots)
    finally:
        store.release(lease, now=utc_now(now))


def _write_json(value, output):
    target = Path(output)
    if target.is_symlink():
        raise ValueError('Desk output cannot be a symlink')
    target.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n'
    descriptor, temporary = tempfile.mkstemp(prefix='.paper-desk-', dir=target.parent)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
            stream.write(data)
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Bounded PAPER desk research; no orders or credentials')
    parser.add_argument('command', choices=('collect', 'status', 'export'))
    parser.add_argument('--state-dir')
    parser.add_argument('--policy')
    parser.add_argument('--output')
    args = parser.parse_args(argv)
    try:
        if args.command == 'collect':
            policy = strict_json_loads(Path(args.policy).read_bytes()) if args.policy else None
            report = collect_desk(args.state_dir, policy)
        else:
            store = DeskStore(args.state_dir)
            report = store.status()
            if args.command == 'export':
                report = store.public_report()
        if args.output: _write_json(report, args.output)
        else: print(json.dumps(report, ensure_ascii=False, allow_nan=False))
        if not report.get('audit_integrity', True):
            return 1
        if args.command == 'collect' and (report.get('state') == 'WORKER_BUSY' or not report.get('fresh_observation_count')):
            return 2
        return 0
    except (ValueError, OSError, sqlite3.Error, TimeoutError):
        print('{"mode":"PAPER","state":"UNAVAILABLE","live_execution_enabled":false}')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
