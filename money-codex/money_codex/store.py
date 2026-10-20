"""Durable research storage. It has no financial execution or remote write adapter."""
from __future__ import annotations

import contextlib
import hashlib
import json
import os
import math
import re
import sqlite3
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_STATE_DIR = Path('/workspace/money/.local-data/resources')


def timestamp(value=None):
    if value is None:
        return time.time()
    if isinstance(value, datetime):
        if value.tzinfo is None:
            raise ValueError('A timezone is required')
        return value.timestamp()
    if isinstance(value, str):
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if parsed.tzinfo is None:
            raise ValueError('A timezone is required')
        return parsed.timestamp()
    if isinstance(value, bool):
        raise ValueError("Boolean timestamps are invalid")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("Finite timestamp required")
    return result


def utc(value=None):
    return datetime.fromtimestamp(timestamp(value), timezone.utc).isoformat().replace('+00:00', 'Z')


def moment(value=None):
    return datetime.fromtimestamp(timestamp(value), timezone.utc)


def canonical(data):
    from .packets import assert_no_secret_keys
    assert_no_secret_keys(data)
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


class Store:
    def __init__(self, state_dir=None):
        candidate = Path(state_dir or os.environ.get('MONEY_STATE_DIR') or DEFAULT_STATE_DIR).expanduser()
        self.state_dir = Path(os.path.abspath(candidate))
        self.state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        if self.state_dir.resolve() != self.state_dir:
            raise ValueError('State directory must not use symlinks')
        self.path = self.state_dir / 'resources.sqlite3'
        if self.path.is_symlink():
            raise ValueError('Database must not use symlinks')
        os.chmod(self.state_dir, 0o700)
        with self._connect() as db:
            db.execute('PRAGMA journal_mode=WAL')
            db.executescript('''
                CREATE TABLE IF NOT EXISTS sources(id TEXT PRIMARY KEY,payload TEXT NOT NULL,updated REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS evidence(id TEXT PRIMARY KEY,source_id TEXT NOT NULL,payload TEXT NOT NULL,created REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS opportunities(id TEXT PRIMARY KEY,source_id TEXT NOT NULL,payload TEXT NOT NULL,updated REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,dedupe_key TEXT UNIQUE NOT NULL,source_id TEXT NOT NULL,
                  state TEXT NOT NULL CHECK(state IN ('PENDING','RUNNING','RETRY','SUCCEEDED','FAILED')),
                  attempts INTEGER NOT NULL DEFAULT 0,max_attempts INTEGER NOT NULL DEFAULT 3,
                  due REAL NOT NULL,lease_owner TEXT,lease_until REAL,error TEXT,result TEXT,created REAL NOT NULL,updated REAL NOT NULL);
                CREATE INDEX IF NOT EXISTS jobs_due ON jobs(state,due);
                CREATE TABLE IF NOT EXISTS ledger(seq INTEGER PRIMARY KEY AUTOINCREMENT,event_id TEXT UNIQUE NOT NULL,
                  kind TEXT NOT NULL,payload TEXT NOT NULL,created REAL NOT NULL,previous_hash TEXT NOT NULL,hash TEXT NOT NULL);
                CREATE TRIGGER IF NOT EXISTS ledger_no_update BEFORE UPDATE ON ledger BEGIN SELECT RAISE(ABORT,'append-only ledger'); END;
                CREATE TRIGGER IF NOT EXISTS ledger_no_delete BEFORE DELETE ON ledger BEGIN SELECT RAISE(ABORT,'append-only ledger'); END;
                CREATE TABLE IF NOT EXISTS outbox(packet_id TEXT PRIMARY KEY,payload TEXT NOT NULL,state TEXT NOT NULL DEFAULT 'EXPORTED',created REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS receipts(packet_id TEXT PRIMARY KEY,payload TEXT NOT NULL,created REAL NOT NULL);
            ''')
            # Serialize migration inspection with other processes starting up.
            db.execute('BEGIN IMMEDIATE')
            columns = {r['name'] for r in db.execute('PRAGMA table_info(jobs)')}
            if 'lease_token' not in columns:
                db.execute('ALTER TABLE jobs ADD COLUMN lease_token TEXT')
        os.chmod(self.path, 0o600)

    @contextlib.contextmanager
    def _connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA busy_timeout=10000')
        db.execute('PRAGMA foreign_keys=ON')
        try:
            with db:
                yield db
        finally:
            db.close()

    @contextlib.contextmanager
    def _transaction(self):
        with self._connect() as db:
            db.execute('BEGIN IMMEDIATE')
            yield db

    @staticmethod
    def _event(db, kind, payload, at):
        body = canonical(payload)
        previous = db.execute('SELECT hash FROM ledger ORDER BY seq DESC LIMIT 1').fetchone()
        previous_hash = previous['hash'] if previous else '0' * 64
        event_id = str(uuid.uuid4())
        digest = hashlib.sha256(canonical({'event_id': event_id, 'kind': kind, 'payload': payload, 'created': at, 'previous_hash': previous_hash}).encode()).hexdigest()
        db.execute('INSERT INTO ledger(event_id,kind,payload,created,previous_hash,hash) VALUES(?,?,?,?,?,?)', (event_id, kind, body, at, previous_hash, digest))

    def register_sources(self, sources, now=None, deactivate_missing=False):
        at = timestamp(now)
        with self._transaction() as db:
            for source in sources:
                sid = str(source.get('source_id') or source.get('id') or '')
                if not sid:
                    raise ValueError('Source id required')
                old = db.execute('SELECT payload FROM sources WHERE id=?', (sid,)).fetchone()
                payload = json.loads(old['payload']) if old else {}
                payload.update({'source_id': sid, 'config': source, 'enabled': source.get('enabled', True), 'mode': 'READ_ONLY'})
                payload.setdefault('status', 'NOT_CHECKED')
                db.execute('INSERT INTO sources VALUES(?,?,?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload,updated=excluded.updated', (sid, canonical(payload), at))
            if deactivate_missing:
                configured = {source.get('source_id') or source.get('id') for source in sources}
                for row in db.execute('SELECT id,payload FROM sources').fetchall():
                    if row['id'] not in configured:
                        payload = json.loads(row['payload'])
                        payload['enabled'] = False
                        payload['config'] = {**payload.get('config', {}), 'enabled': False}
                        db.execute('UPDATE sources SET payload=?,updated=? WHERE id=?', (canonical(payload), at, row['id']))

    def enqueue(self, source_id, dedupe_key, now=None, due=None, max_attempts=3):
        at = timestamp(now)
        if not isinstance(source_id, str) or not source_id or not isinstance(dedupe_key, str) or not 1 <= len(dedupe_key) <= 512:
            raise ValueError('Valid source and dedupe key required')
        if type(max_attempts) is not int or not 1 <= max_attempts <= 10:
            raise ValueError('max_attempts must be 1..10')
        with self._transaction() as db:
            if not db.execute('SELECT 1 FROM sources WHERE id=?', (source_id,)).fetchone():
                raise ValueError('Unregistered source')
            existing = db.execute('SELECT id FROM jobs WHERE dedupe_key=?', (dedupe_key,)).fetchone()
            if existing:
                return existing['id']
            active = db.execute("SELECT id FROM jobs WHERE source_id=? AND state IN ('PENDING','RUNNING','RETRY') LIMIT 1", (source_id,)).fetchone()
            if active:
                return active['id']
            jid = str(uuid.uuid4())
            db.execute('INSERT INTO jobs(id,dedupe_key,source_id,state,due,max_attempts,created,updated) VALUES(?,?,?,?,?,?,?,?)', (jid, dedupe_key, source_id, 'PENDING', timestamp(due) if due is not None else at, max_attempts, at, at))
            self._event(db, 'JOB_ENQUEUED', {'job_id': jid, 'source_id': source_id}, at)
            return jid

    def claim_job(self, owner, now=None, lease_seconds=120):
        at = timestamp(now)
        if not isinstance(owner, str) or not 1 <= len(owner) <= 128 or type(lease_seconds) not in (int, float) or not math.isfinite(lease_seconds) or not 1 <= lease_seconds <= 3600:
            raise ValueError('Valid owner and bounded lease required')
        with self._transaction() as db:
            expired = db.execute("SELECT * FROM jobs WHERE state='RUNNING' AND (lease_until<=? OR lease_until IS NULL OR lease_token IS NULL)", (at,)).fetchall()
            for row in expired:
                state = 'FAILED' if row['attempts'] >= row['max_attempts'] else 'RETRY'
                db.execute('UPDATE jobs SET state=?,lease_owner=NULL,lease_until=NULL,lease_token=NULL,error=?,due=?,updated=? WHERE id=?', (state, 'LEASE_EXPIRED', at, at, row['id']))
                self._event(db, 'JOB_LEASE_EXPIRED', {'job_id': row['id'], 'state': state}, at)
            row = db.execute("SELECT * FROM jobs WHERE state IN ('PENDING','RETRY') AND due<=? ORDER BY due,created LIMIT 1", (at,)).fetchone()
            if not row:
                return None
            db.execute("UPDATE jobs SET state='RUNNING',attempts=attempts+1,lease_owner=?,lease_until=?,lease_token=?,updated=? WHERE id=?", (owner, at + lease_seconds, str(uuid.uuid4()), at, row['id']))
            claimed = dict(db.execute('SELECT * FROM jobs WHERE id=?', (row['id'],)).fetchone())
            self._event(db, 'JOB_CLAIMED', {'job_id': row['id'], 'owner': owner, 'attempt': claimed['attempts']}, at)
            return claimed

    @staticmethod
    def _leased(db, job_id, owner, lease_token, at):
        row = db.execute('SELECT * FROM jobs WHERE id=?', (job_id,)).fetchone()
        if (not row or row['state'] != 'RUNNING' or row['lease_owner'] != owner
                or row['lease_until'] <= at or not lease_token or row['lease_token'] != lease_token):
            raise ValueError('Job lease is absent, expired or superseded')
        return row

    @staticmethod
    def _finish(db, row, result, error, at, retry_seconds):
        if type(retry_seconds) not in (int, float) or not math.isfinite(retry_seconds) or not 0 <= retry_seconds <= 86400:
            raise ValueError('Invalid retry delay')
        # Store controlled error codes only; arbitrary exception messages may contain secrets.
        code = None if error is None else str(error)
        if code is not None and not re.fullmatch(r'[A-Z][A-Z0-9_]{0,99}', code):
            code = 'JOB_FAILED'
        state = 'SUCCEEDED' if code is None else ('FAILED' if row['attempts'] >= row['max_attempts'] else 'RETRY')
        db.execute('UPDATE jobs SET state=?,result=?,error=?,due=?,lease_owner=NULL,lease_until=NULL,lease_token=NULL,updated=? WHERE id=?',
                   (state, canonical(result) if result is not None else None, code, at + retry_seconds if code else at, at, row['id']))
        Store._event(db, 'JOB_' + state, {'job_id': row['id'], 'source_id': row['source_id'], 'error': code}, at)
        return state

    def finish_job(self, job_id, owner, result=None, error=None, now=None, retry_seconds=60, lease_token=None):
        at = timestamp(now)
        with self._transaction() as db:
            row = self._leased(db, job_id, owner, lease_token, at)
            return self._finish(db, row, result, error, at, retry_seconds)

    @staticmethod
    def _prepared_scan(result, at):
        from .models import evaluate_opportunity
        if not isinstance(result, dict) or result.get('mode', 'READ_ONLY') != 'READ_ONLY':
            raise ValueError('Only READ_ONLY scans can be stored')
        canonical(result)
        prepared = {**json.loads(canonical(result)), 'opportunities': []}
        for key in ('opportunities', 'source_status', 'evidence', 'detail_status'):
            if not isinstance(result.get(key, []), list) or len(result.get(key, [])) > 2000:
                raise ValueError('Bounded scan arrays required')
            if any(not isinstance(item, dict) for item in result.get(key, [])):
                raise ValueError('Scan entries must be objects')
        for source in result.get('source_status', []):
            if not isinstance(source.get('source_id') or source.get('id'), str) or not (source.get('source_id') or source.get('id')):
                raise ValueError('Source status id required')
        for opportunity in result.get('opportunities', []):
            payload = evaluate_opportunity(opportunity, now=moment(at))
            if not isinstance(payload.get('opportunity_id'), str) or not payload['opportunity_id']:
                raise ValueError('Opportunity id required')
            payload['execution_mode'] = 'READ_ONLY'
            prepared['opportunities'].append(payload)
        return prepared

    @staticmethod
    def _save_scan(db, result, at, imported=False):
        counts = {'opportunities': 0, 'evidence': 0, 'sources': 0}
        for evidence in result.get('evidence', []):
            if not isinstance(evidence, dict):
                raise ValueError('Evidence metadata must be an object')
            body = canonical(evidence)
            eid = hashlib.sha256(body.encode()).hexdigest()
            sid = str(evidence.get('source_id') or evidence.get('provider') or 'connector-import')
            counts['evidence'] += db.execute('INSERT OR IGNORE INTO evidence VALUES(?,?,?,?)', (eid, sid, body, at)).rowcount
        for source in ([] if imported else result.get('source_status', [])):
            sid = str(source.get('source_id') or source.get('id') or '')
            if not sid:
                raise ValueError('Source status id required')
            previous = db.execute('SELECT payload FROM sources WHERE id=?', (sid,)).fetchone()
            payload = json.loads(previous['payload']) if previous else {}
            payload.update({key: value for key, value in source.items() if key not in ('config', 'enabled', 'mode', 'last_scan_at_utc')})
            payload.setdefault('enabled', False)
            if source.get('access_status') == 'ACCESS VERIFIED' and source.get('status') not in ('UNAVAILABLE', 'PARSE_UNAVAILABLE', 'ERROR', 'FAILED', 'BLOCKED'):
                payload['retry_after_seconds'] = source.get('retry_after_seconds', 0)
            payload.update({'source_id': sid, 'mode': 'READ_ONLY', 'last_scan_at_utc': utc(at)})
            db.execute('INSERT INTO sources VALUES(?,?,?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload,updated=excluded.updated', (sid, canonical(payload), at))
            counts['sources'] += 1
        for payload in result.get('opportunities', []):
            oid = payload['opportunity_id']
            sid = str(payload.get('source_id') or payload.get('provider') or 'unknown')
            old = db.execute('SELECT payload FROM opportunities WHERE id=?', (oid,)).fetchone()
            previous = json.loads(old['payload']) if old else None
            if imported:
                # Integrity is not channel authentication: never replace direct
                # local observations with claims supplied in an offline packet.
                payload = {**payload, 'origin': 'OFFLINE_PACKET', 'authenticated_channel_verified': False}
                if previous and previous.get('origin') != 'OFFLINE_PACKET':
                    continue
            incoming_at = Store._observed_at(payload, at)
            previous_at = Store._observed_at(previous, at) if previous else None
            if previous_at is not None and (incoming_at is None or incoming_at < previous_at):
                continue
            body = canonical(payload)
            db.execute('INSERT INTO opportunities VALUES(?,?,?,?) ON CONFLICT(id) DO UPDATE SET source_id=excluded.source_id,payload=excluded.payload,updated=excluded.updated', (oid, sid, body, at))
            if not old or old['payload'] != body:
                Store._event(db, 'OPPORTUNITY_OBSERVED', {'opportunity_id': oid, 'source_id': sid, 'payload_sha256': hashlib.sha256(body.encode()).hexdigest(), 'classification': payload.get('classification')}, at)
            counts['opportunities'] += 1
        if not imported:
            Store._apply_detail_status(db, result.get('detail_status', []), at)
        Store._event(db, 'SCAN_STORED', counts, at)
        return counts

    @staticmethod
    def _observed_at(payload, at):
        try:
            observed = timestamp(payload.get('last_verified_at_utc')) if payload and payload.get('last_verified_at_utc') else None
            return observed if observed is not None and observed <= at else None
        except (TypeError, ValueError, OverflowError):
            return None

    @staticmethod
    def _apply_detail_status(db, statuses, at):
        for detail in statuses:
            oid, sid = detail.get('opportunity_id'), detail.get('source_id')
            disposition = detail.get('status')
            if not isinstance(oid, str) or not isinstance(sid, str) or disposition not in ('ACTIVE', 'INACTIVE', 'UNAVAILABLE'):
                raise ValueError('Invalid detail status identity')
            if not isinstance(detail.get('observed_at'), str):
                raise ValueError('Detail observation timestamp required')
            observed = timestamp(detail['observed_at'])
            if observed > at:
                raise ValueError('Detail status timestamp is in the future')
            row = db.execute('SELECT source_id,payload FROM opportunities WHERE id=?', (oid,)).fetchone()
            if not row or row['source_id'] != sid:
                continue
            payload = json.loads(row['payload'])
            if detail.get('url') != payload.get('official_url'):
                raise ValueError('Detail status URL mismatch')
            old_checked = payload.get('availability_checked_at_utc')
            if (old_checked and timestamp(old_checked) > observed) or (Store._observed_at(payload, at) or 0) > observed:
                continue
            proof = detail.get('source_evidence')
            if disposition in ('ACTIVE', 'INACTIVE'):
                if (not isinstance(proof, dict) or proof.get('url') != detail['url']
                        or proof.get('http_status') != 200 or not isinstance(proof.get('content_sha256'), str)
                        or not re.fullmatch('[0-9a-f]{64}', proof['content_sha256'])
                        or not isinstance(proof.get('observed_at'), str) or timestamp(proof['observed_at']) != observed):
                    raise ValueError('Direct primary evidence required for availability')
            payload.update(availability_status=disposition, availability_checked_at_utc=utc(observed),
                           availability_evidence=proof, availability_reason=detail.get('reason') or detail.get('error_code'))
            db.execute('UPDATE opportunities SET payload=?,updated=? WHERE id=?', (canonical(payload), at, oid))
            Store._event(db, 'OPPORTUNITY_REVALIDATED', {'opportunity_id': oid, 'source_id': sid,
                         'availability_status': disposition, 'observed_at': utc(observed)}, at)

    @staticmethod
    def _opportunity_view(row, at):
        from .models import evaluate_opportunity
        payload = evaluate_opportunity(json.loads(row['payload']), now=moment(at))
        source = json.loads(row['source_payload']) if row['source_payload'] else None
        reasons = []
        disposition = payload.get('availability_status')
        if disposition == 'INACTIVE':
            reasons.append('official_opportunity_inactive')
            payload.update(classification='SKIP', status='SKIP', next_action='Do not pursue')
        elif disposition == 'UNAVAILABLE':
            reasons.append('opportunity_revalidation_unavailable')
        if source:
            payload['source_access_status'] = source.get('access_status')
            payload['source_last_attempt_at_utc'] = source.get('last_scan_at_utc')
            if source.get('enabled') is False:
                reasons.append('source_not_configured')
            if source.get('access_status') == 'ACCESS UNAVAILABLE' or source.get('status') in ('UNAVAILABLE', 'PARSE_UNAVAILABLE', 'ERROR', 'FAILED', 'BLOCKED'):
                reasons.append('source_revalidation_failed')
        if payload.get('origin') == 'OFFLINE_PACKET':
            payload['authenticated_channel_verified'] = False
            reasons.append('offline_packet_identity_not_verified')
        if reasons and payload['classification'] != 'SKIP':
            payload.update(classification='DATA INSUFFICIENT', status='DATA INSUFFICIENT', next_action='Verify missing evidence')
        payload['blocking_reasons'] = list(dict.fromkeys(payload.get('blocking_reasons', []) + reasons))
        return payload

    def save_scan(self, result, now=None):
        at = timestamp(now)
        prepared = self._prepared_scan(result, at)
        with self._transaction() as db:
            return self._save_scan(db, prepared, at)

    def complete_scan(self, job_id, owner, lease_token, result, now=None, error=None, retry_seconds=60):
        """Fence observations and job completion in one transaction.

        A worker whose lease expired cannot persist partial or stale results.
        """
        at = timestamp(now)
        prepared = self._prepared_scan(result, at)
        with self._transaction() as db:
            row = self._leased(db, job_id, owner, lease_token, at)
            if (any(s.get('source_id') != row['source_id'] for s in prepared.get('source_status', []))
                    or any(o.get('source_id') != row['source_id'] for o in prepared.get('opportunities', []))
                    or any(e.get('source_id') != row['source_id'] for e in prepared.get('evidence', []))
                    or any(d.get('source_id') != row['source_id'] for d in prepared.get('detail_status', []))):
                raise ValueError('Worker result belongs to another source')
            counts = self._save_scan(db, prepared, at)
            state = self._finish(db, row, counts, error, at, retry_seconds)
        return state, counts

    def opportunities(self, limit=100, classification=None, source_id=None, now=None):
        at = timestamp(now)
        query = 'SELECT o.payload,s.payload source_payload FROM opportunities o LEFT JOIN sources s ON o.source_id=s.id'
        args = []
        if source_id:
            query += ' WHERE o.source_id=?'
            args.append(source_id)
        query += ' ORDER BY o.updated DESC LIMIT ?'
        args.append(min(max(int(limit), 1), 1000))
        with self._connect() as db:
            rows = db.execute(query, args).fetchall()
        payloads = [self._opportunity_view(row, at) for row in rows]
        return [p for p in payloads if classification is None or p.get('classification') == classification]

    def list_sources(self):
        with self._connect() as db:
            return [json.loads(row['payload']) for row in db.execute('SELECT payload FROM sources ORDER BY id')]

    def joblist(self, limit=100):
        with self._connect() as db:
            rows = db.execute('SELECT * FROM jobs ORDER BY created DESC LIMIT ?', (min(max(int(limit), 1), 1000),)).fetchall()
            return [{**dict(row), 'result': json.loads(row['result']) if row['result'] else None} for row in rows]

    def jobs_by_ids(self, job_ids):
        if not isinstance(job_ids, list) or not 1 <= len(job_ids) <= 100 or any(not isinstance(jid, str) for jid in job_ids):
            raise ValueError('A bounded job id list is required')
        with self._connect() as db:
            rows = db.execute('SELECT * FROM jobs WHERE id IN (' + ','.join('?' for _ in job_ids) + ')', job_ids).fetchall()
            return [{**dict(row), 'result': json.loads(row['result']) if row['result'] else None} for row in rows]

    def evidence(self, evidence_id=None, limit=100):
        with self._connect() as db:
            if evidence_id:
                row = db.execute('SELECT * FROM evidence WHERE id=?', (evidence_id,)).fetchone()
                return {**dict(row), 'payload': json.loads(row['payload'])} if row else None
            return [{**dict(r), 'payload': json.loads(r['payload'])} for r in db.execute('SELECT * FROM evidence ORDER BY created DESC LIMIT ?', (min(max(int(limit), 1), 1000),))]

    def ledger(self, limit=100):
        with self._connect() as db:
            return [{**dict(r), 'payload': json.loads(r['payload'])} for r in db.execute('SELECT * FROM ledger ORDER BY seq DESC LIMIT ?', (min(max(int(limit), 1), 1000),))]

    def verify_ledger(self):
        previous = '0' * 64
        try:
            with self._connect() as db:
                for r in db.execute('SELECT * FROM ledger ORDER BY seq'):
                    data = {'event_id': r['event_id'], 'kind': r['kind'], 'payload': json.loads(r['payload']), 'created': r['created'], 'previous_hash': r['previous_hash']}
                    if r['previous_hash'] != previous or hashlib.sha256(canonical(data).encode()).hexdigest() != r['hash']:
                        return False
                    previous = r['hash']
        except (ValueError, TypeError, sqlite3.DatabaseError):
            return False
        return True

    def status(self):
        with self._connect() as db:
            counts = {table: db.execute('SELECT count(*) FROM ' + table).fetchone()[0] for table in ['sources', 'opportunities', 'evidence', 'jobs', 'ledger', 'outbox', 'receipts']}
            states = {r['state']: r['n'] for r in db.execute('SELECT state,count(*) n FROM jobs GROUP BY state')}
        return {'mode': 'READ_ONLY', 'rail': 'RESOURCES', 'state_directory': str(self.state_dir), 'counts': counts, 'jobs_by_state': states, 'ledger_integrity': self.verify_ledger(), 'direct_bot_connected': False, 'financial_execution_enabled': False}

    def export_packet(self, now=None, persist=True):
        from .packets import envelope
        payload = {'rail': 'RESOURCES', 'mode': 'READ_ONLY', 'opportunities': self.opportunities(now=now), 'source_status': self.list_sources(), 'evidence': [r['payload'] for r in self.evidence()], 'direct_bot_connected': False}
        packet = envelope('RESOURCE_RESEARCH', 'MONEY_CODEX', payload, now=moment(now))
        if not persist:
            return packet
        with self._transaction() as db:
            db.execute('INSERT INTO outbox VALUES(?,?,?,?)', (packet['packet_id'], canonical(packet), 'EXPORTED', timestamp(now)))
            self._event(db, 'PACKET_EXPORTED', {'packet_id': packet['packet_id'], 'state': 'EXPORTED', 'delivery': 'manual'}, timestamp(now))
        return packet

    def import_packet(self, packet, now=None):
        from .packets import verify_envelope
        at = timestamp(now)
        ok, reasons = verify_envelope(packet, now=moment(at))
        if not ok:
            raise ValueError('Invalid evidence envelope: ' + ', '.join(reasons))
        canonical(packet)
        payload = packet['payload']
        required = {'mode', 'rail', 'opportunities', 'source_status', 'evidence'}
        if (packet['object_type'] != 'RESOURCE_RESEARCH' or not required <= set(payload)
                or set(payload) - (required | {'direct_bot_connected'})
                or payload['mode'] != 'READ_ONLY' or payload['rail'] != 'RESOURCES'
                or payload.get('direct_bot_connected', False) is not False):
            raise ValueError('Explicit READ_ONLY resource research schema required')
        packet_id = packet['packet_id']
        prepared = self._prepared_scan(payload, at)
        with self._transaction() as db:
            previous = db.execute('SELECT payload FROM receipts WHERE packet_id=?', (packet_id,)).fetchone()
            if previous:
                receipt = json.loads(previous['payload'])
                if receipt.get('packet_sha256') != packet['sha256']:
                    raise ValueError('Packet id collision or unverified legacy receipt')
                return {'state': 'EXISTING', 'packet_id': packet_id, 'authenticated_channel_verified': False}
            counts = self._save_scan(db, prepared, at, imported=True)
            receipt = {'packet_id': packet_id, 'packet_sha256': packet['sha256'], 'producer': packet['producer'],
                       'verification': 'integrity_and_ttl', 'authenticated_channel_verified': False, 'packet': packet}
            db.execute('INSERT INTO receipts VALUES(?,?,?)', (packet_id, canonical(receipt), at))
            self._event(db, 'PACKET_IMPORTED', {'packet_id': packet_id, 'producer': packet['producer'], 'delivery': 'offline', 'authenticated_channel_verified': False}, at)
        return {'state': 'IMPORTED', 'packet_id': packet_id, 'stored': counts, 'authenticated_channel_verified': False}
