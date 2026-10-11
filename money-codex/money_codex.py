"""Compatibility entry point for the original MONEY Ω bootstrap.

The preserved original is in Git history. All validation now uses the maintained
package; importing this file cannot bypass the current authorization gate.
"""
from money_codex.models import Opportunity, ACCESS_STATES as ACCESS
from money_codex.authorization import validate_live_authorization
from money_codex.packets import envelope, verify_envelope


def packet(object_type, producer, payload):
    return envelope(object_type, producer, payload)


if __name__ == '__main__':
    from money_codex.cli import main
    raise SystemExit(main())
