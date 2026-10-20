"""Persistence, recovery and safety tests; public reads use deterministic fixtures."""
import hashlib
import json
import sqlite3
import tempfile
import threading
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from money_codex.runtime import Runtime, load_runtime_config
from money_codex.store import Store, canonical, timestamp

NOW = datetime(2026, 10, 11, 12, 0, tzinfo=timezone.utc)
SOURCE = {'source_id': 'fixture_public', 'name': 'Fixture public source', 'category': 'BOUNTY',
          'url': 'https://example.org/opportunities', 'method': 'READ_ONLY', 'interval_seconds': 60, 'enabled': True}


def fixture(now=NOW, source_id='fixture_public'):
    iso = now.isoformat().replace('+00:00', 'Z')
    proof = {'source_id': source_id, 'url': 'https://example.org/opportunities',
             'observed_link': 'https://example.org/opportunities/fixture', 'observed_at': iso,
             'content_sha256': hashlib.sha256(b'unit-test public document fixture').hexdigest(),
             'hash_basis': 'HTTP_RESPONSE_BYTES', 'http_status': 200}
    return {'mode': 'READ_ONLY', 'source_status': [{'source_id': source_id, 'status': 'DISCOVERED',
             'access_status': 'ACCESS VERIFIED', 'http_status': 200, 'observed_at': iso}],
            'evidence': [proof], 'opportunities': [{'opportunity_id': 'fixture_opportunity', 'source_id': source_id,
             'provider': 'Fixture public source', 'type': 'BOUNTY', 'official_url': proof['observed_link'],
             'source_evidence': proof, 'evidence': ['Deterministic public document fixture'],
             'last_verified_at_utc': iso, 'eligibility_status': 'UNKNOWN', 'deadline_utc': None}]}


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.state = Path(self.temp.name) / 'state'
        self.store = Store(self.state)
        self.store.register_sources([SOURCE], now=NOW)

    def tearDown(self):
        self.temp.cleanup()

    def claim(self, *, lease_seconds=60):
        job_id = self.store.enqueue(SOURCE['source_id'], 'scan:fixture', now=NOW)
        claim = self.store.claim_job('worker', now=NOW, lease_seconds=lease_seconds)
        self.assertEqual(claim['id'], job_id)
        return claim

    def test_storage_survives_restart_and_rechecks_freshness(self):
        self.store.save_scan(fixture(), now=NOW)
        restarted = Store(self.state)
        item = restarted.opportunities(now=NOW)[0]
        self.assertEqual(item['opportunity_id'], 'fixture_opportunity')
        self.assertIsNone(item['expected_net_value_usd'])
        self.assertFalse(item['execution_authority'])
        self.assertEqual(item['execution_mode'], 'READ_ONLY')
        later = restarted.opportunities(now=NOW + timedelta(days=8))[0]
        self.assertEqual(later['classification'], 'DATA INSUFFICIENT')
        self.assertTrue(restarted.verify_ledger())

    def test_enqueues_are_idempotent_and_do_not_overlap_source(self):
        first = self.store.enqueue(SOURCE['source_id'], 'manual:a', now=NOW)
        same = self.store.enqueue(SOURCE['source_id'], 'manual:a', now=NOW)
        concurrent = self.store.enqueue(SOURCE['source_id'], 'manual:b', now=NOW)
        self.assertEqual(first, same)
        self.assertEqual(first, concurrent)
        self.assertEqual(self.store.status()['counts']['jobs'], 1)

    def test_two_process_style_stores_cannot_enqueue_overlapping_jobs(self):
        second = Store(self.state)
        barrier = threading.Barrier(2)
        ids, errors = [], []
        def enqueue(store, dedupe):
            try:
                barrier.wait()
                ids.append(store.enqueue(SOURCE['source_id'], dedupe, now=NOW))
            except Exception as exc:
                errors.append(exc)
        threads = [threading.Thread(target=enqueue, args=(self.store, 'a')),
                   threading.Thread(target=enqueue, args=(second, 'b'))]
        for thread in threads: thread.start()
        for thread in threads: thread.join(timeout=5)
        self.assertFalse(errors)
        self.assertEqual(len(ids), 2)
        self.assertEqual(ids[0], ids[1])

    def test_expired_claim_cannot_commit_after_recovery_even_same_owner(self):
        old = self.claim(lease_seconds=2)
        recovered = Store(self.state).claim_job('worker', now=NOW + timedelta(seconds=3), lease_seconds=60)
        self.assertEqual(old['id'], recovered['id'])
        self.assertNotEqual(old['lease_token'], recovered['lease_token'])
        with self.assertRaises(ValueError):
            self.store.complete_scan(old['id'], 'worker', old['lease_token'], fixture(), now=NOW + timedelta(seconds=3))
        self.assertEqual(self.store.status()['counts']['opportunities'], 0)
        state, counts = self.store.complete_scan(recovered['id'], 'worker', recovered['lease_token'], fixture(), now=NOW + timedelta(seconds=4))
        self.assertEqual(state, 'SUCCEEDED')
        self.assertEqual(counts['opportunities'], 1)
        self.assertTrue(self.store.verify_ledger())

    def test_expired_job_without_recovery_cannot_write(self):
        job = self.claim(lease_seconds=1)
        with self.assertRaises(ValueError):
            self.store.finish_job(job['id'], 'worker', now=NOW + timedelta(seconds=1), lease_token=job['lease_token'])
        self.assertEqual(self.store.status()['counts']['opportunities'], 0)

    def test_complete_scan_rejects_cross_source_observation(self):
        job = self.claim()
        with self.assertRaises(ValueError):
            self.store.complete_scan(job['id'], 'worker', job['lease_token'], fixture(source_id='other'), now=NOW)
        self.assertEqual(self.store.status()['counts']['evidence'], 0)
        self.assertEqual(self.store.joblist()[0]['state'], 'RUNNING')

    def test_invalid_observation_rolls_back_all_scan_writes(self):
        result = fixture()
        result['source_status'] = [{'status': 'DISCOVERED'}]
        with self.assertRaises(ValueError):
            self.store.save_scan(result, now=NOW)
        self.assertEqual(self.store.status()['counts']['evidence'], 0)
        self.assertEqual(self.store.status()['counts']['opportunities'], 0)

    def test_evidence_is_hashed_and_exact_duplicates_are_deduplicated(self):
        scan = fixture()
        first = self.store.save_scan(scan, now=NOW)
        second = self.store.save_scan(scan, now=NOW)
        self.assertEqual(first['evidence'], 1)
        self.assertEqual(second['evidence'], 0)
        evidence = self.store.evidence()[0]
        self.assertEqual(evidence['id'], hashlib.sha256(canonical(evidence['payload']).encode()).hexdigest())
        self.assertEqual(self.store.status()['counts']['opportunities'], 1)

    def test_ledger_is_append_only_and_tampering_is_detected(self):
        self.store.save_scan(fixture(), now=NOW)
        with sqlite3.connect(self.store.path) as db:
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute('DELETE FROM ledger')
            db.execute('DROP TRIGGER ledger_no_update')
            db.execute("UPDATE ledger SET payload='{}' WHERE seq=1")
        self.assertFalse(self.store.verify_ledger())

    def test_packet_import_is_atomic_and_replay_does_not_duplicate_events(self):
        self.store.save_scan(fixture(), now=NOW)
        preview = self.store.export_packet(now=NOW, persist=False)
        self.assertEqual(self.store.status()['counts']['outbox'], 0)
        self.store.export_packet(now=NOW)
        self.assertEqual(self.store.status()['counts']['outbox'], 1)
        target = Store(Path(self.temp.name) / 'target')
        imported = target.import_packet(preview, now=NOW)
        count = target.status()['counts']['ledger']
        replay = target.import_packet(preview, now=NOW)
        self.assertEqual(imported['state'], 'IMPORTED')
        self.assertEqual(replay['state'], 'EXISTING')
        self.assertEqual(target.status()['counts']['ledger'], count)
        self.assertFalse(imported['authenticated_channel_verified'])
        preview['payload']['mode'] = 'LIVE'
        with self.assertRaises(ValueError): target.import_packet(preview, now=NOW)

    def test_runtime_scans_registered_sources_and_respects_schedule(self):
        runtime = Runtime({'mode': 'READ_ONLY', 'sources': [SOURCE]}, self.store,
                          scanner=lambda config, now: fixture(now))
        runtime.schedule_due(NOW)
        runtime.schedule_due(NOW)
        self.assertEqual(len(self.store.joblist()), 1)
        self.assertTrue(runtime.run_once(NOW))
        self.assertEqual(self.store.joblist()[0]['state'], 'SUCCEEDED')
        restarted = Runtime({'sources': [SOURCE]}, Store(self.state), scanner=lambda config, now: fixture(now))
        restarted.schedule_due(NOW + timedelta(seconds=20))
        self.assertEqual(len(self.store.joblist()), 1)
        restarted.schedule_due(NOW + timedelta(seconds=61))
        self.assertEqual(len(self.store.joblist()), 2)

    def test_blocked_source_receives_cooldown_and_no_opportunities(self):
        def blocked(config, now):
            return {'mode': 'READ_ONLY', 'opportunities': [], 'evidence': [], 'source_status': [{
                'source_id': SOURCE['source_id'], 'status': 'UNAVAILABLE',
                'access_status': 'ACCESS UNAVAILABLE', 'http_status': 451}]}
        runtime = Runtime({'sources': [SOURCE]}, self.store, scanner=blocked)
        runtime.schedule_due(NOW)
        runtime.run_once(NOW)
        job = self.store.joblist()[0]
        self.assertEqual(job['state'], 'RETRY')
        self.assertGreaterEqual(job['due'], timestamp(NOW) + 3600)
        self.assertEqual(self.store.opportunities(), [])
        self.assertEqual(self.store.list_sources()[0]['retry_after_seconds'], 3600)
        runtime.schedule_due(NOW + timedelta(seconds=120))
        self.assertFalse(runtime.run_once(NOW + timedelta(seconds=120)))
        self.assertEqual(len(self.store.joblist()), 1)

    def test_scan_exception_is_controlled_and_no_partial_success(self):
        def fail(config, now): raise OSError('private context must never be persisted')
        runtime = Runtime({'sources': [SOURCE]}, self.store, scanner=fail)
        runtime.schedule_due(NOW)
        runtime.run_once(NOW)
        job = self.store.joblist()[0]
        self.assertEqual(job['state'], 'RETRY')
        self.assertEqual(job['error'], 'SCAN_FAILED_OSERROR')
        self.assertNotIn('private context', canonical(self.store.ledger()))
        self.assertEqual(self.store.status()['counts']['opportunities'], 0)

    def test_scheduler_lock_is_released_and_reacquired(self):
        one = Runtime({'sources': []}, self.store)
        two = Runtime({'sources': []}, Store(self.state))
        try:
            one.start_scheduler()
            with self.assertRaises(RuntimeError): two.start_scheduler()
            self.assertTrue(one.stop())
            two.start_scheduler()
            self.assertTrue(two.status()['scheduler']['running'])
        finally:
            one.stop()
            two.stop()

    def test_invalid_mode_source_method_timestamp_and_nonfinite_payload_fail(self):
        with self.assertRaises(ValueError): Runtime({'mode': 'LIVE', 'sources': []}, self.store)
        with self.assertRaises(ValueError): Runtime({'sources': [{**SOURCE, 'method': 'POST'}]}, self.store)
        with self.assertRaises(ValueError): Runtime({'sources': [{**SOURCE, 'enabled': 'false'}]}, self.store)
        with self.assertRaises(ValueError): timestamp(float('inf'))
        with self.assertRaises(ValueError): timestamp(True)
        scan = fixture()
        scan['opportunities'][0]['gas_usd'] = float('nan')
        with self.assertRaises(ValueError): self.store.save_scan(scan)

    def test_live_environment_has_no_execution_adapter(self):
        with patch.dict('os.environ', {'MONEY_EXECUTION_MODE': 'LIVE'}):
            with self.assertRaises(ValueError): Runtime({'sources': []}, self.store)
        with patch.dict('os.environ', {'MONEY_EXECUTION_MODE': 'PAPER'}):
            self.assertFalse(Runtime({'sources': []}, self.store).status()['financial_execution_enabled'])

    def test_cli_scan_export_import_and_status_flags(self):
        from money_codex.cli import main
        import contextlib
        import io
        config = Path(self.temp.name) / 'sources.json'
        config.write_text(json.dumps({'mode': 'READ_ONLY', 'sources': [SOURCE]}))
        output = Path(self.temp.name) / 'scan.json'
        packet_path = Path(self.temp.name) / 'packet.json'
        with patch('money_codex.scanner.scan_sources', side_effect=lambda config, now: fixture(now)):
            self.assertEqual(main(['scan', '--state-dir', str(self.state), '--config', str(config), '--output', str(output)]), 0)
        self.assertEqual(json.loads(output.read_text())['state'], 'COMPLETED')
        self.assertEqual(main(['export', '--state-dir', str(self.state), '--output', str(packet_path)]), 0)
        target = Path(self.temp.name) / 'cli-import-state'
        with contextlib.redirect_stdout(io.StringIO()) as buffer:
            self.assertEqual(main(['import', '--state-dir', str(target), '--input', str(packet_path)]), 0)
        self.assertEqual(json.loads(buffer.getvalue())['state'], 'IMPORTED')
        with contextlib.redirect_stdout(io.StringIO()) as buffer:
            self.assertEqual(main(['status', '--state-dir', str(target)]), 0)
        self.assertTrue(json.loads(buffer.getvalue())['ledger_integrity'])

    def test_manual_scan_cooldown_survives_runtime_restart(self):
        at = timestamp(NOW)
        one = Runtime({'sources': [SOURCE]}, self.store, scanner=lambda config, now: fixture(now))
        with patch('money_codex.runtime.time.time', return_value=at):
            self.assertEqual(one.scan_now(wait=True)['state'], 'COMPLETED')
        two = Runtime({'sources': [SOURCE]}, Store(self.state), scanner=lambda config, now: fixture(now))
        with patch('money_codex.runtime.time.time', return_value=at + 2):
            cooled = two.scan_now(wait=True)
        self.assertEqual(cooled['state'], 'COOLDOWN')
        self.assertEqual(cooled['sources_in_cooldown'][0]['retry_after_seconds'], 58)
        self.assertEqual(len(self.store.joblist()), 1)

    def test_relative_parent_components_are_allowed_without_symlink_aliases(self):
        equivalent = Store(self.state / '..' / 'state')
        self.assertEqual(equivalent.path, self.store.path)
        link = Path(self.temp.name) / 'alias'
        link.symlink_to(self.state, target_is_directory=True)
        with self.assertRaises(ValueError): Store(link)

    def test_secret_fields_rejected_before_storage(self):
        scan = fixture()
        scan['evidence'][0]['private_key'] = 'fixture forbidden field'
        with self.assertRaises(ValueError): self.store.save_scan(scan)
        self.assertEqual(self.store.status()['counts']['evidence'], 0)

    def packet(self, scan=None, now=NOW, **overrides):
        from money_codex.packets import envelope
        payload = {'rail': 'RESOURCES', **(fixture(now) if scan is None else scan)}
        payload.update(overrides)
        return envelope('RESOURCE_RESEARCH', 'TEST_RESEARCH_NODE', payload, now=now)

    def test_import_requires_explicit_resource_schema_and_no_connection_claims(self):
        from money_codex.packets import envelope
        base = {'rail': 'RESOURCES', **fixture()}
        cases = []
        for field in ('rail', 'mode', 'opportunities', 'source_status', 'evidence'):
            changed = dict(base)
            changed.pop(field)
            cases.append(envelope('RESOURCE_RESEARCH', 'TEST', changed, now=NOW))
        cases.append(envelope('AUTHORIZATION', 'TEST', base, now=NOW))
        cases.append(self.packet(direct_bot_connected=True))
        cases.append(self.packet(source_status=[False]))
        cases.append(self.packet(detail_status=[]))
        for candidate in cases:
            with self.subTest(fields=set(candidate['payload']), kind=candidate['object_type']):
                with self.assertRaises(ValueError): self.store.import_packet(candidate, now=NOW)
        self.assertEqual(self.store.status()['counts']['receipts'], 0)
        self.assertEqual(self.store.status()['counts']['opportunities'], 0)

    def test_import_detects_resigned_packet_id_collision_without_writes(self):
        from copy import deepcopy
        from money_codex.packets import canonical_json, verify_envelope
        packet = self.packet()
        self.store.import_packet(packet, now=NOW)
        before = self.store.status()['counts']
        changed = deepcopy(packet)
        changed['payload']['opportunities'][0]['title'] = 'Different claimed observation'
        changed.pop('sha256')
        changed['sha256'] = hashlib.sha256(canonical_json(changed)).hexdigest()
        self.assertTrue(verify_envelope(changed, now=NOW)[0])
        with self.assertRaises(ValueError): self.store.import_packet(changed, now=NOW)
        self.assertEqual(self.store.status()['counts'], before)

    def test_import_never_freshens_or_reconfigures_local_source_or_overwrites_direct_read(self):
        self.store.save_scan(fixture(), now=NOW)
        baseline = self.store.list_sources()[0]
        later = NOW + timedelta(seconds=20)
        scan = fixture(later)
        scan['opportunities'][0]['title'] = 'Untrusted replacement'
        scan['source_status'][0].update(config={'url': 'https://example.org/unreviewed'}, enabled=False)
        packet = self.packet(scan, now=later)
        received = self.store.import_packet(packet, now=later)
        self.assertFalse(received['authenticated_channel_verified'])
        self.assertEqual(self.store.list_sources()[0], baseline)
        item = self.store.opportunities(now=later)[0]
        self.assertEqual(item['last_verified_at_utc'], fixture()['opportunities'][0]['last_verified_at_utc'])
        self.assertNotEqual(item.get('title'), 'Untrusted replacement')
        with self.store._connect() as db:
            receipt = json.loads(db.execute('SELECT payload FROM receipts').fetchone()['payload'])
        self.assertEqual(receipt['packet_sha256'], packet['sha256'])
        self.assertEqual(receipt['packet'], packet)

    def test_import_is_evidence_for_review_without_direct_access_authority(self):
        received = self.store.import_packet(self.packet(), now=NOW)
        self.assertEqual(received['stored']['sources'], 0)
        self.assertIsNone(self.store.list_sources()[0].get('last_scan_at_utc'))
        item = self.store.opportunities(now=NOW)[0]
        self.assertEqual(item['origin'], 'OFFLINE_PACKET')
        self.assertEqual(item['classification'], 'DATA INSUFFICIENT')
        self.assertFalse(item['authenticated_channel_verified'])
        self.assertIn('offline_packet_identity_not_verified', item['blocking_reasons'])

    def test_older_direct_snapshot_cannot_replace_a_newer_observation(self):
        newer = NOW + timedelta(seconds=30)
        scan = fixture(newer)
        scan['opportunities'][0]['title'] = 'Fresh observed title'
        self.store.save_scan(scan, now=newer)
        self.store.save_scan(fixture(), now=newer + timedelta(seconds=5))
        item = self.store.opportunities(now=newer + timedelta(seconds=5))[0]
        self.assertEqual(item['title'], 'Fresh observed title')
        self.assertEqual(item['last_verified_at_utc'], scan['opportunities'][0]['last_verified_at_utc'])

    def test_source_failure_immediately_invalidates_previous_review_classification(self):
        self.store.save_scan(fixture(), now=NOW)
        later = NOW + timedelta(seconds=10)
        for status, access in [('UNAVAILABLE', 'ACCESS UNAVAILABLE'), ('PARSE_UNAVAILABLE', 'ACCESS PARTIAL')]:
            self.store.save_scan({'source_status': [{'source_id': SOURCE['source_id'], 'status': status, 'access_status': access}]}, now=later)
            item = self.store.opportunities(now=later)[0]
            self.assertEqual(item['classification'], 'DATA INSUFFICIENT')
            self.assertIn('source_revalidation_failed', item['blocking_reasons'])
            self.assertEqual(item['last_verified_at_utc'], fixture()['opportunities'][0]['last_verified_at_utc'])
        self.store.save_scan(fixture(later), now=later)
        self.assertEqual(self.store.opportunities(now=later)[0]['classification'], 'WATCH')

    def detail(self, state='INACTIVE', now=None):
        when = now or NOW + timedelta(seconds=5)
        proof = fixture(when)['evidence'][0]
        proof['url'] = fixture()['opportunities'][0]['official_url']
        return {'source_id': SOURCE['source_id'], 'opportunity_id': 'fixture_opportunity',
                'url': proof['url'], 'status': state, 'observed_at': proof['observed_at'],
                'http_status': 200 if state != 'UNAVAILABLE' else 403,
                'source_evidence': proof if state != 'UNAVAILABLE' else None,
                'reason': 'PAUSED' if state == 'INACTIVE' else 'HTTP_403' if state == 'UNAVAILABLE' else 'ACTIVE'}

    def test_only_explicit_primary_inactive_tombstone_retires_cached_opportunity(self):
        self.store.save_scan(fixture(), now=NOW)
        # An empty bounded catalogue cannot establish that a programme closed.
        self.store.save_scan({'source_status': [{'source_id': SOURCE['source_id'], 'status': 'NO_PUBLIC_CANDIDATES', 'access_status': 'ACCESS VERIFIED'}]}, now=NOW + timedelta(seconds=1))
        self.assertEqual(self.store.opportunities(now=NOW + timedelta(seconds=2))[0]['classification'], 'WATCH')
        detail = self.detail()
        self.store.save_scan({'detail_status': [detail]}, now=NOW + timedelta(seconds=5))
        item = self.store.opportunities(now=NOW + timedelta(seconds=6))[0]
        self.assertEqual(item['classification'], 'SKIP')
        self.assertEqual(item['availability_reason'], 'PAUSED')
        self.assertEqual(item['availability_evidence'], detail['source_evidence'])
        self.assertIn('OPPORTUNITY_REVALIDATED', [row['kind'] for row in self.store.ledger()])

    def test_unavailable_detail_is_not_mistaken_for_closed_and_later_read_recovers(self):
        self.store.save_scan(fixture(), now=NOW)
        self.store.save_scan({'detail_status': [self.detail('UNAVAILABLE')]}, now=NOW + timedelta(seconds=5))
        item = self.store.opportunities(now=NOW + timedelta(seconds=6))[0]
        self.assertEqual(item['classification'], 'DATA INSUFFICIENT')
        self.assertIn('opportunity_revalidation_unavailable', item['blocking_reasons'])
        later = NOW + timedelta(seconds=20)
        self.store.save_scan(fixture(later), now=later)
        self.assertEqual(self.store.opportunities(now=later)[0]['classification'], 'WATCH')

    def test_invalid_primary_tombstone_rolls_back_source_and_evidence_writes(self):
        self.store.save_scan(fixture(), now=NOW)
        before = self.store.status()['counts']
        detail = self.detail()
        detail['source_evidence'] = None
        scan = {'source_status': [{'source_id': SOURCE['source_id'], 'status': 'NO_PUBLIC_CANDIDATES'}],
                'detail_status': [detail], 'evidence': [fixture(NOW + timedelta(seconds=5))['evidence'][0]]}
        with self.assertRaises(ValueError): self.store.save_scan(scan, now=NOW + timedelta(seconds=5))
        self.assertEqual(self.store.status()['counts'], before)
        self.assertEqual(self.store.opportunities(now=NOW + timedelta(seconds=6))[0]['classification'], 'WATCH')

    def test_removed_source_stays_disabled_despite_new_observation_metadata(self):
        self.store.save_scan(fixture(), now=NOW)
        Runtime({'sources': []}, self.store)
        status = fixture()['source_status'][0]
        status['enabled'] = True
        status['config'] = SOURCE
        self.store.save_scan({'source_status': [status]}, now=NOW)
        registered = self.store.list_sources()[0]
        self.assertIs(registered['enabled'], False)
        self.assertIs(registered['config']['enabled'], False)
        self.assertIn('source_not_configured', self.store.opportunities(now=NOW)[0]['blocking_reasons'])

    def test_http_code_fallback_applies_pause_and_success_clears_it(self):
        def blocked(config, now):
            return {'source_status': [{'source_id': SOURCE['source_id'], 'status': 'UNAVAILABLE',
                                      'access_status': 'ACCESS UNAVAILABLE', 'http_status': None, 'error_code': 'HTTP_403'}]}
        runtime = Runtime({'sources': [SOURCE]}, self.store, scanner=blocked)
        runtime.schedule_due(NOW)
        runtime.run_once(NOW)
        self.assertGreaterEqual(self.store.joblist()[0]['due'], timestamp(NOW) + 900)
        later = NOW + timedelta(seconds=901)
        healthy = Runtime({'sources': [SOURCE]}, self.store, scanner=lambda config, now: fixture(now))
        healthy.run_once(later)
        self.assertEqual(self.store.list_sources()[0]['retry_after_seconds'], 0)
        healthy.schedule_due(later + timedelta(seconds=61))
        self.assertEqual(len(self.store.joblist()), 2)

    def test_cli_all_failed_batch_returns_nonzero_and_preserves_failure_json(self):
        import contextlib
        import io
        from money_codex.cli import main
        config = Path(self.temp.name) / 'failure-config.json'
        config.write_text(json.dumps({'sources': [SOURCE]}))
        output = Path(self.temp.name) / 'failure-result.json'
        failed = {'source_status': [{'source_id': SOURCE['source_id'], 'status': 'UNAVAILABLE', 'access_status': 'ACCESS UNAVAILABLE'}]}
        with patch('money_codex.scanner.scan_sources', return_value=failed), contextlib.redirect_stdout(io.StringIO()):
            code = main(['scan', '--config', str(config), '--state-dir', str(self.state), '--output', str(output)])
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(output.read_text())['jobs'][0]['state'], 'RETRY')

    def test_cli_incomplete_shutdown_is_not_a_success(self):
        import contextlib
        import io
        from unittest.mock import Mock
        from money_codex.cli import main
        worker = Mock()
        worker._stop.wait.return_value = True
        worker.stop.return_value = False
        with patch('money_codex.cli.Runtime', return_value=worker), patch('money_codex.cli.load_runtime_config', return_value={'sources': []}), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()) as error:
            code = main(['worker', '--state-dir', str(self.state)])
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(error.getvalue())['state'], 'INCOMPLETE_SHUTDOWN')

    def test_stopping_worker_keeps_lock_until_finished_and_refuses_new_scans(self):
        entered, release = threading.Event(), threading.Event()
        def pending(config, now):
            entered.set()
            release.wait(2)
            return fixture(now)
        runtime = Runtime({'sources': [SOURCE]}, self.store, scanner=pending)
        other = Runtime({'sources': [SOURCE]}, Store(self.state), scanner=pending)
        runtime.start_scheduler()
        try:
            self.assertTrue(entered.wait(2))
            self.assertFalse(runtime.stop(timeout=0))
            with self.assertRaises(RuntimeError): runtime.start_scheduler()
            with self.assertRaises(RuntimeError): runtime.scan_now()
            with self.assertRaises(RuntimeError): other.start_scheduler()
        finally:
            release.set()
            self.assertTrue(runtime.stop(timeout=2))
            other.stop()
        self.assertTrue(self.store.verify_ledger())

    def test_crashed_process_lock_metadata_does_not_prevent_restart(self):
        import os
        import subprocess
        import sys
        directory = str(Path(self.temp.name) / 'crashed')
        script = "from money_codex.runtime import Runtime; from money_codex.store import Store; import os; runtime=Runtime({'sources':[]},Store(" + repr(directory) + ")); runtime.start_scheduler(); os._exit(0)"
        subprocess.run([sys.executable, '-c', script], check=True, capture_output=True, timeout=5)
        metadata = json.loads((Path(directory) / '.scheduler.lock').read_text())
        self.assertNotEqual(metadata['pid'], os.getpid())
        restarted = Runtime({'sources': []}, Store(directory))
        try:
            restarted.start_scheduler()
            self.assertTrue(restarted.status()['scheduler']['running'])
        finally:
            restarted.stop()

    def test_invalid_ledger_json_reports_failed_integrity_without_crashing_health(self):
        self.store.save_scan(fixture(), now=NOW)
        with sqlite3.connect(self.store.path) as db:
            db.execute('DROP TRIGGER ledger_no_update')
            db.execute("UPDATE ledger SET payload='{' WHERE seq=1")
        self.assertFalse(self.store.verify_ledger())
        self.assertFalse(self.store.status()['ledger_integrity'])

    def test_waiting_batch_is_not_lost_behind_a_thousand_newer_jobs(self):
        old = self.store.enqueue(SOURCE['source_id'], 'old-recoverable', now=NOW - timedelta(days=1))
        with sqlite3.connect(self.store.path) as db:
            db.executemany('INSERT INTO jobs(id,dedupe_key,source_id,state,due,created,updated) VALUES(?,?,?,?,?,?,?)',
                           [(f'history_{i}', f'history:{i}', 'historical-fixture-source', 'SUCCEEDED', timestamp(NOW), timestamp(NOW), timestamp(NOW)) for i in range(1001)])
        runtime = Runtime({'sources': [SOURCE]}, self.store, scanner=lambda config, now: fixture(now))
        result = runtime.scan_now(wait=True)
        self.assertEqual(result['job_ids'], [old])
        self.assertEqual(result['jobs'][0]['state'], 'SUCCEEDED')

    def test_thread_start_failure_releases_process_lock(self):
        runtime = Runtime({'sources': []}, self.store)
        other = Runtime({'sources': []}, Store(self.state))
        with patch('money_codex.runtime.threading.Thread.start', side_effect=RuntimeError('test thread creation failure')):
            with self.assertRaises(RuntimeError): runtime.start_scheduler()
        try:
            other.start_scheduler()
            self.assertTrue(other.status()['scheduler']['running'])
            self.assertIsNone(runtime._lock_file)
        finally:
            other.stop()
            runtime.stop()


if __name__ == '__main__':
    unittest.main()
