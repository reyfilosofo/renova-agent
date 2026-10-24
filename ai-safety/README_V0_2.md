# ℛenova × SERESARTE AI Safety Lab — v0.2

**RESEARCH-ONLY MOCK. Not AGI containment, not production control, not independently validated.**

The new trusted_gateway.py models a server-side reference monitor in a closed Python simulator. It supplies the principal and permissions from a trusted in-memory test harness, rather than accepting the model's authority assertions. Actions that would change simulated data require an HMAC-bound, expiring, one-use, exact-argument approval token. The mock sends no messages, handles no payments, and cannot connect to real APIs.

eval_metrics.py measures forbidden tool actions recorded as executed and legitimate tasks completed, with descriptive Wilson intervals, but performs no confirmatory significance analysis.

Reproduce from the ai-safety directory using Python 3.10+:

    python -m unittest discover -s tests -v
    python -m renova_guard.cli fixtures/demo.json

**69 local tests passed** in the assembled v0.2 code: 21 legacy tests, 38 new mock gateway tests, and 10 event-metric tests. CI confirmation is separate and pending.

See docs/RESEARCH_BRIDGE_2026_10_15.md, docs/SECURITY_REVIEW_V0_2.md and docs/SCOPUS_AND_FACCT_2027_TRACK.md.

Important: simulated_human_attested=True is only a harness-controlled fiction; it does NOT authenticate a human. If exposed to an untrusted model, the mock issuer would be unsafe. Do not deploy.

The public repo has no license grant. No books, paid materials, clients, images, or user-supplied EGRA research pack source code were copied to this branch.
