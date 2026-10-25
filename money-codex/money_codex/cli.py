"""Operate MONEY's public research rail without financial routes or credentials."""
from __future__ import annotations

import argparse
import json
import os
import signal
import sqlite3
import sys
import tempfile
from pathlib import Path

from .runtime import Runtime, load_runtime_config, require_research_mode
from .store import Store


def _write_json(value, output=None):
    encoded = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n'
    if output is None or output == '-':
        print(encoded, end='')
        return
    target = Path(output).expanduser().absolute()
    if target.is_symlink():
        raise ValueError('Output must not be a symlink')
    target.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix='.' + target.name + '.', dir=target.parent)
    try:
        with os.fdopen(handle, 'w', encoding='utf-8') as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _state_args(parser, config=False):
    parser.add_argument('--state-dir', help='SQLite state directory; defaults to MONEY_STATE_DIR or the local resources directory')
    if config:
        parser.add_argument('--config', help='Public-source config; defaults to MONEY_RESOURCE_CONFIG or config/resource_sources.json')


def _signal_interrupt(*_args):
    raise KeyboardInterrupt()


def main(argv=None):
    parser = argparse.ArgumentParser(prog='money-omega', description='MONEY Ω · CODEX public resource discovery')
    sub = parser.add_subparsers(dest='cmd', required=True)
    desk = sub.add_parser('desk', help='Operate the isolated PAPER observation desk')
    desk.add_argument('desk_args', nargs=argparse.REMAINDER)
    review = sub.add_parser('desk-review', help='Review a normalized snapshot without execution')
    review.add_argument('--input', required=True)
    review.add_argument('--policy')
    review.add_argument('--output')
    scan = sub.add_parser('scan', help='Fetch configured public sources, store observations, and return the scan batch')
    _state_args(scan, config=True)
    scan.add_argument('--source-id', action='append', help='Select one enabled configured source; repeat for multiple sources')
    scan.add_argument('--output', help='Optional atomic JSON result file')
    export = sub.add_parser('export', help='Write a checksummed research packet for offline review')
    _state_args(export)
    export.add_argument('--output', help='Output JSON file or - for stdout')
    preview = sub.add_parser('status', help='Inspect local research state and ledger integrity')
    _state_args(preview)
    ingest = sub.add_parser('import', help='Validate and ingest an offline READ_ONLY resource packet')
    _state_args(ingest)
    ingest.add_argument('--input', required=True)
    serve = sub.add_parser('serve', help='Run the local resource dashboard and persistent scheduler')
    _state_args(serve, config=True)
    serve.add_argument('--host', choices=['127.0.0.1'], default='127.0.0.1')
    serve.add_argument('--port', type=int, default=8787)
    worker = sub.add_parser('worker', help='Run the research scheduler without an HTTP dashboard')
    _state_args(worker, config=True)
    sync = sub.add_parser('sync', help='Inspect configured public integration addresses; no remote writes')
    sync.add_argument('--config', required=True)
    sub.add_parser('score-example', help='Show that EV remains unknown when costs are missing')
    args = parser.parse_args(argv)
    try:
        require_research_mode()
        if args.cmd == 'desk':
            from .desk_runtime import main as desk_main
            return desk_main(args.desk_args)
        if args.cmd == 'desk-review':
            from .desk import review_desk
            from .packets import strict_json_loads
            source = Path(args.input)
            if source.stat().st_size > 262144:
                raise ValueError('Desk input exceeds 256 KB')
            policy = strict_json_loads(Path(args.policy).read_bytes()) if args.policy else None
            _write_json(review_desk(strict_json_loads(source.read_bytes()), policy), args.output)
            return 0
        if args.cmd == 'sync':
            from .sync import load_config, sync
            _write_json([record.to_dict() for record in sync(load_config(args.config))])
            return 0
        if args.cmd == 'score-example':
            from .models import Opportunity
            opportunity = Opportunity('EXAMPLE', 'illustration', 'QUEST', expected_gross_reward_usd=10,
                                      reward_probability=0.5, time_cost_usd=2, security_risk_cost_usd=1)
            _write_json({'example_only': True, 'expected_net_value_usd': opportunity.expected_net_value(),
                         'reason': 'Unknown costs stay null; this is not a discovered opportunity'})
            return 0
        store = Store(args.state_dir)
        if args.cmd == 'status':
            _write_json(store.status())
        elif args.cmd == 'export':
            _write_json(store.export_packet(), args.output)
        elif args.cmd == 'import':
            source = Path(args.input)
            if source.stat().st_size > 2_000_000:
                raise ValueError('Offline packet exceeds 2 MB')
            from .packets import strict_json_loads
            packet = strict_json_loads(source.read_text(encoding='utf-8'))
            _write_json(store.import_packet(packet))
        elif args.cmd == 'scan':
            runtime = Runtime(load_runtime_config(args.config), store)
            batch = runtime.scan_now(source_ids=args.source_id, wait=True)
            _write_json(batch, args.output)
            if batch.get('state') != 'COOLDOWN' and not any(job.get('state') == 'SUCCEEDED' for job in batch.get('jobs', [])):
                return 2
        else:
            runtime = Runtime(load_runtime_config(args.config), store)
            previous_handlers = {}
            for sig in (signal.SIGTERM, signal.SIGINT):
                previous_handlers[sig] = signal.signal(sig, _signal_interrupt)
            server = None
            try:
                if args.cmd == 'serve':
                    from .server import create_server
                    server = create_server(store, runtime, host=args.host, port=args.port)
                runtime.start_scheduler()
                if server:
                    print(json.dumps({'state': 'RUNNING', 'dashboard': f'http://127.0.0.1:{server.server_port}',
                                      'mode': 'READ_ONLY', 'financial_execution_enabled': False}), flush=True)
                    server.serve_forever(poll_interval=0.25)
                else:
                    print(json.dumps({'state': 'RUNNING', 'mode': 'READ_ONLY', 'scheduler': True}), flush=True)
                    while not runtime._stop.wait(1):
                        pass
            except KeyboardInterrupt:
                pass
            finally:
                if server:
                    server.server_close()
                stopped = runtime.stop()
                for sig, handler in previous_handlers.items():
                    signal.signal(sig, handler)
                if not stopped:
                    print(json.dumps({'state': 'INCOMPLETE_SHUTDOWN', 'mode': 'READ_ONLY'}), file=sys.stderr)
                    return 1
        return 0
    except (ValueError, OSError, TypeError, KeyError, RuntimeError, sqlite3.Error) as exc:
        # Do not echo configs, URLs, packet contents or arbitrary exception text.
        print(json.dumps({'state': 'ERROR', 'error': type(exc).__name__, 'mode': 'READ_ONLY'}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
