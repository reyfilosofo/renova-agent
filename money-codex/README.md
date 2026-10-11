# MONEY Ω · CODEX

Version 0.3.0 · 2026-10-11 · Python 3.11+ · standard library only.

The engineering node of MONEY Ω now operates a public resource discovery rail:
ten configured sources for bounties, quests and paid research, a durable SQLite
queue, evidence storage, an append-only ledger, EV assessment, packet exchange
and a local dashboard. This rail runs in READ_ONLY and never submits claims,
personal answers, wallet signatures or orders.

## Run

From the repository root:

```sh
python3 money-codex/check.py
python3 money-codex/run.py scan --state-dir .local-data/resources
python3 money-codex/run.py serve --state-dir .local-data/resources --port 8787
python3 money-codex/run.py status --state-dir .local-data/resources
python3 money-codex/run.py export --state-dir .local-data/resources --output /tmp/money-review.json
```

The local dashboard is `http://127.0.0.1:8787`. `serve` runs both HTTP and the
scheduler; `worker` runs the scheduler alone. State survives process restarts.
Use a service manager for a persistent host; a Codex task itself is not a 24/7
service. [Deployment instructions](deploy/README.md) include Docker and systemd.

The GitHub workflow `money-resource-discovery.yml` runs tests and discovery at
00:17, 06:17, 12:17 and 18:17 UTC, on relevant main updates, or manually. GitHub
may delay scheduled runs. Each run retains private evidence in an Actions
artifact for 90 days and publishes an allowlisted public report. The static
[resource dashboard](../money-resources/index.html) reads that report. Each cloud
run restores SQLite and evidence from a best-effort Actions cache. Cache eviction
can reset this history; local SQLite provides continuing history, while Git
commits and Actions artifacts preserve cloud observations. Complete source
failures retain the last published report and fail the run; partial failures
remain visible as source statuses.

## What the results mean

Discovery is not confirmed eligibility or income. A working provider catalogue
is a `PROGRAM_DISCOVERY` candidate; a bounty listing still needs examination.
Unknown reward probabilities, expenses and costs stay `null`. EV deducts gas,
fees, required spend, expected loss, time, capital lockup and security risk.
Positive fully supported candidates enter `QUEUE` for review. Expired or
unverifiable records cannot become actionable solely because a URL responds.

The initial real scan on 11 October found 17 candidates across ten reachable
sources. No receipt, reward probability, personal eligibility or net EV was
confirmed. Configured category coverage is explicit in
`config/resource_sources.json`; wallet claims, airdrops and other unconfigured
categories remain pending.

## Markets, authorization and packets

Markets remain separate from resource discovery. `RENOVA_DESK_V0` and
`MONEY_FIXED_WINDOW_ANALOG_PAPER_V1` remain PAPER. Contract equivalence precedes
descriptive venue comparisons; Pmarket, experimental Pspot and Pcontract remain
separate. No validated Pcontract estimator is introduced here.

The authorization validator requires independently verified account context,
revocation and kill-switch state, exact scope, expiry and risk limits. A validator
is not an execution adapter: this runtime rejects LIVE and has no financial
route, credentials, wallet signer or order adapter.

Packets use schema 2.1 with finite JSON, expiry and SHA-256. A digest demonstrates
integrity, not authenticated producer identity. Legacy packets need an explicit
migration; they are not silently trusted. Import/export remains offline; direct
ChatGPT↔Codex and Grok connections remain false until authenticated round trips.

## Canonical sources and privacy

GitHub main is technical truth; the current Drive Operating Bridge is documentary
truth; confirmed accounts and fills take precedence for execution. Project IDs
remain pending until supplied and verified. See `CONTEXT_INDEX.md` and
`config/integrations.example.json` for existing MONEY sources.

SQLite, raw evidence, receipts, account records and credentials must remain in
runtime storage, outside Git and the public site. The public report uses a field
allowlist and contains only discovery results and their public evidence links.
Original bootstrap sources remain preserved in the local `upstream/` archive.
