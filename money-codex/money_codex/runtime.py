"""Bounded read-only resource scans with durable scheduled jobs."""
from __future__ import annotations
import fcntl
import json
import math
import os
import threading
import time
import uuid
from pathlib import Path
from .store import Store, timestamp, utc, moment

DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / 'config' / 'resource_sources.json'

def require_research_mode():
    mode = os.environ.get('MONEY_EXECUTION_MODE', 'READ_ONLY')
    if mode not in ('READ_ONLY', 'PAPER'):
        raise ValueError('This runtime supports research only; LIVE execution has no adapter')
    return mode


def load_runtime_config(path=None):
    require_research_mode()
    from .packets import strict_json_loads
    data = strict_json_loads(Path(path or os.environ.get('MONEY_RESOURCE_CONFIG') or DEFAULT_CONFIG).read_text(encoding='utf-8'))
    if not isinstance(data, dict) or not isinstance(data.get('sources'), list):
        raise ValueError('Resource config requires sources')
    from .packets import assert_no_secret_keys
    assert_no_secret_keys(data)
    return data

class Runtime:
    def __init__(self, config, store=None, scanner=None):
        require_research_mode()
        if not isinstance(config, dict) or config.get('mode', 'READ_ONLY') != 'READ_ONLY':
            raise ValueError('Runtime supports READ_ONLY only')
        self.config = json.loads(json.dumps(config, allow_nan=False))
        if not isinstance(self.config.get('sources'), list) or len(self.config['sources']) > 50:
            raise ValueError('sources array required')
        self.store = store or Store()
        self.scanner = scanner
        self.owner = 'resource-worker-' + str(uuid.uuid4())
        self._stop, self._wake = threading.Event(), threading.Event()
        self._thread = self._lock_file = self._latest = None
        ids = []
        for source in self.config['sources']:
            if not isinstance(source, dict) or type(source.get('enabled', True)) is not bool:
                raise ValueError('Source object and boolean enabled required')
            sid = source.get('source_id') or source.get('id')
            if not isinstance(sid, str) or not sid or sid in ids:
                raise ValueError('Each source requires a unique id')
            if source.get('mode', 'READ_ONLY') != 'READ_ONLY' or source.get('method', 'READ_ONLY') != 'READ_ONLY':
                raise ValueError('Only READ_ONLY source adapters are allowed')
            interval = source.get('interval_seconds', self.config.get('interval_seconds', 900))
            if isinstance(interval, bool) or not isinstance(interval, (int, float)) or not math.isfinite(interval) or not 60 <= interval <= 86400:
                raise ValueError('Source interval must be 60..86400 seconds')
            ids.append(sid)
        self.store.register_sources(self.config['sources'])

    def _enabled(self):
        return [s for s in self.config['sources'] if s.get('enabled', True)]

    def _source(self, sid):
        return next((s for s in self.config['sources'] if (s.get('source_id') or s.get('id')) == sid), None)

    def scan_now(self, source_ids=None, wait=False):
        enabled = {s.get('source_id') or s.get('id') for s in self._enabled()}
        ids = sorted(enabled) if source_ids is None else list(source_ids)
        if not ids or len(ids) > 100 or any(not isinstance(s, str) or s not in enabled for s in ids):
            raise ValueError('Select registered enabled source ids')
        at, batch = time.time(), str(uuid.uuid4())
        statuses = {item['source_id']: item for item in self.store.list_sources()}
        job_ids, cooling = [], []
        # Rate state survives process restarts; repeated CLI calls cannot bypass
        # the public adapter's minimum interval or a blocking response cooldown.
        network = self.config.get('network', {})
        configured_floor = network.get('min_interval_seconds', 60) if isinstance(network, dict) else 60
        floor = max(60, min(configured_floor, 3600)) if type(configured_floor) in (int, float) and math.isfinite(configured_floor) else 60
        for sid in dict.fromkeys(ids):
            status = statuses.get(sid, {})
            previous = status.get('last_scan_at_utc')
            backoff = status.get('retry_after_seconds', 0)
            cooldown = max(floor, min(backoff, 86400)) if type(backoff) in (int, float) and math.isfinite(backoff) else floor
            if previous and at - timestamp(previous) < cooldown:
                cooling.append({'source_id': sid, 'retry_after_seconds': max(1, math.ceil(cooldown - (at - timestamp(previous))))})
                continue
            job_ids.append(self.store.enqueue(sid, 'manual:' + batch + ':' + sid, now=at))
        if not job_ids:
            return {'state': 'COOLDOWN', 'job_ids': [], 'sources_in_cooldown': cooling, 'mode': 'READ_ONLY'}
        self._wake.set()
        if wait:
            # There may already be due work in the durable queue. Drain available
            # work until this batch finishes or its retries are scheduled later.
            for _ in range(200):
                jobs = {j['id']: j for j in self.store.joblist(1000)}
                selected = [jobs[jid] for jid in job_ids]
                if all(j['state'] in ('SUCCEEDED', 'FAILED') for j in selected) or not self.run_once():
                    break
            jobs = {j['id']: j for j in self.store.joblist(1000)}
            selected = [jobs[jid] for jid in job_ids]
            terminal = all(j['state'] in ('SUCCEEDED', 'FAILED') for j in selected)
            return {'state': 'COMPLETED' if terminal else 'RETRY_SCHEDULED', 'job_ids': job_ids,
                    'jobs': selected, 'sources_in_cooldown': cooling, 'mode': 'READ_ONLY', 'status': self.store.status()}
        return {'state': 'QUEUED', 'job_ids': job_ids, 'sources_in_cooldown': cooling, 'mode': 'READ_ONLY'}

    def schedule_due(self, now=None):
        at = timestamp(now)
        statuses = {s['source_id']: s for s in self.store.list_sources()}
        for source in self._enabled():
            sid = source.get('source_id') or source.get('id')
            status = statuses.get(sid, {})
            interval = source.get('interval_seconds', self.config.get('interval_seconds', 900))
            cooldown = status.get('retry_after_seconds')
            if isinstance(cooldown, (int, float)):
                interval = max(interval, min(max(cooldown, 60), 86400))
            previous = status.get('last_scan_at_utc')
            if previous and at - timestamp(previous) < interval: continue
            self.store.enqueue(sid, 'scheduled:' + sid + ':' + str(math.floor(at / interval)), now=at)

    def run_once(self, now=None):
        at = timestamp(now)
        job = self.store.claim_job(self.owner, now=at, lease_seconds=180)
        if job is None: return False
        try:
            source = self._source(job['source_id'])
            if source is None or not source.get('enabled', True): raise ValueError('SOURCE_DISABLED')
            if self.scanner is None:
                from .scanner import scan_sources
                scan = scan_sources
            else: scan = self.scanner
            result = scan({**self.config, 'sources': [source]}, now=moment(at))
            statuses = result.get('source_status', [])
            for item in statuses:
                if item.get('http_status') in [403, 429, 451]:
                    item['retry_after_seconds'] = max(item.get('retry_after_seconds', 0), 3600 if item.get('http_status') == 451 else 900)
            failed = bool(result.get('errors')) or not statuses or any(s.get('access_status') == 'ACCESS UNAVAILABLE' or s.get('status') in ['ACCESS UNAVAILABLE', 'UNAVAILABLE', 'ERROR', 'FAILED', 'BLOCKED'] for s in statuses)
            cooldown = max([s.get('retry_after_seconds', 0) for s in statuses if isinstance(s.get('retry_after_seconds', 0), (int, float))] or [0])
            delay = max(min(60 * (2 ** (job['attempts'] - 1)), 3600), min(cooldown, 86400))
            finished = timestamp(now) if now is not None else time.time()
            state, counts = self.store.complete_scan(job['id'], self.owner, job['lease_token'], result, error='SOURCE_UNAVAILABLE' if failed else None, retry_seconds=delay, now=finished)
            self._latest = {'job_id': job['id'], 'source_id': job['source_id'], 'state': state, 'stored': counts, 'finished_at_utc': utc(finished)}
        except Exception as exc:
            error = 'SCAN_FAILED_' + type(exc).__name__.upper()
            try:
                state = self.store.finish_job(job['id'], self.owner, error=error, retry_seconds=min(60 * (2 ** (job['attempts'] - 1)), 3600), now=now, lease_token=job['lease_token'])
            except ValueError: state = 'LEASE_EXPIRED'
            self._latest = {'job_id': job['id'], 'source_id': job['source_id'], 'state': state, 'error': error, 'finished_at_utc': utc(now)}
        return True

    def _loop(self):
        while not self._stop.is_set():
            try:
                self.schedule_due()
                if self.run_once(): continue
            except Exception as exc:
                self._latest = {'state': 'SCHEDULER_ERROR', 'error': type(exc).__name__, 'finished_at_utc': utc()}
            self._wake.wait(5)
            self._wake.clear()

    def start_scheduler(self):
        if self._thread and self._thread.is_alive(): return
        lock_path = self.store.state_dir / '.scheduler.lock'
        if lock_path.is_symlink(): raise ValueError('Scheduler lock must not use symlinks')
        lock = open(lock_path, 'a+', encoding='utf-8')
        os.chmod(lock_path, 0o600)
        try: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            lock.close()
            raise RuntimeError('A scheduler already owns this state directory') from None
        lock.seek(0); lock.truncate()
        json.dump({'pid': os.getpid(), 'started_at_utc': utc(), 'mode': 'READ_ONLY'}, lock)
        lock.flush()
        self._lock_file = lock
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name='money-resource-scheduler', daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set(); self._wake.set()
        if self._thread:
            self._thread.join(timeout=30)
            if self._thread.is_alive(): return False
        if self._lock_file:
            fcntl.flock(self._lock_file, fcntl.LOCK_UN)
            self._lock_file.close(); self._lock_file = None
        return True

    def status(self):
        return {**self.store.status(), 'scheduler': {'running': bool(self._thread and self._thread.is_alive()), 'enabled': True, 'pid': os.getpid() if self._lock_file else None, 'latest': self._latest, 'source_count': len(self._enabled())}}
