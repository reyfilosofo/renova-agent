# MONEY Ω · PAPER Trading Desk · 0.1 · 2026-10-25

Engineering implementation inspired by the supplied Kiyoro screenshots and
verified against TypeSafe's official typed-decision API. Part of the existing
MONEY Ω system and single Site; not a separate financial project.

The desk separates numerical source data, attributed model judgments, deterministic
risk vetoes and authority. GAMBLER, HOUSE and SPY have distinct new PAPER strategy
IDs. RENOVA_DESK_V0 remains frozen. A missing exact contract, source tick, cost,
liquidity, validated methodology or risk state causes abstention. The shipped
policy deliberately stays HALT with unknown metrics: no limits or balances are
invented. This release does not simulate fills or produce a claimed trading PnL.

## Run and inspect

From the repository root:

```sh
python3 -B money-codex/check.py
python3 money-codex/run.py desk collect --state-dir .local-data/paper-desk --policy money-codex/config/desk_policy.json --output money-desk/data/latest.json
python3 money-codex/run.py desk status --state-dir .local-data/paper-desk
python3 money-codex/run.py desk-review --input /absolute/path/snapshot.json --policy money-codex/config/desk_policy.json --output /tmp/desk-review.json
```

`collect` is one bounded observation pass, not an invisible daemon. It fetches
public Coinbase Exchange USD tickers for the six configured assets. Unsupported
products remain unavailable. Last-trade time and response reception are distinct;
the ticker does not verify the bid/ask quote timestamp. Decimal strings retain
source price precision. HTTP403/429/451 trigger provider cooldown, not evasion.

SQLite uses a separate state directory, process leases, idempotent prospective
records and an append-only audit chain. Research continues while RISK Ω is HALT;
no account, order, wallet signer or financial execution adapter is present.

## Unattended operation

The GitHub workflow `money-paper-desk.yml` requests a bounded pass every five
minutes and publishes an allowlisted observation report. Platform delays or
missed schedules are possible. This is unattended periodic research, not a
continuous low-latency 24/7 trading service. Resource discovery remains separate.

The cloud SQLite cache is best effort and scoped to the UTC day to limit growth.
Each run retains its JSON observation/evidence hashes and reviews as a 90-day
artifact; it does not upload another full historical database every five minutes.
Git preserves public report versions. Full continuous prospective state belongs
on an actual persistent host; `deploy/money-paper-desk.service` and `.timer` are
reviewable templates, not proof of installation or uptime. Configure real paths,
a service account and private writable storage there. Never add keys to these files.

## Jev and Grok

The optional stdlib adapter implements the official `POST /v1/systemone` at
`https://api.typesafe.ai`, pinned to documented model `jev-1.14.0`. Noul, Choice
and Score responses are checked for schema, question identity, model, numerical
ranges and distributions. Typed confidence is not validated market probability.

It is disabled by default. Actual inference requires an explicit enable flag and
server runtime `TYPESAFE_API_KEY`; never paste the value into prompts, files or
logs. A mocked response is labelled unverified. No inference was billed or
claimed authenticated during bootstrap. GitHub secret metadata was inaccessible;
that does not prove whether remote credentials exist. A verified round trip is
still required before reporting the connection as active.

Grok remains offline packet review under `GROK_BOT_CHARTER.md`. Its website is not
a verified API endpoint. No cross-agent connection or authenticated reviewer
identity is inferred from JSON or a checksum.

## Evidence and limitations

The original X article could not establish API behavior or trading profitability.
The local screenshots are attributed claims; official TypeSafe documentation
establishes the API contract only. No reproducible profitable edge, calibrated
Pcontract, verified source-account data, provider receipt or LIVE authorization
was observed. UI publication and tests do not establish those facts.

Sources: https://docs.typesafe.ai/models.md,
https://docs.typesafe.ai/api/system-one.md,
https://api.typesafe.ai/openapi.json,
https://docs.cdp.coinbase.com/exchange/reference/exchangerestapi_getproductticker,
https://x.com/0xkiyoro/status/2107135100911563017.
