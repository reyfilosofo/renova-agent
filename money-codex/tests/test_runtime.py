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


if __name__ == '__main__':
    unittest.main()
