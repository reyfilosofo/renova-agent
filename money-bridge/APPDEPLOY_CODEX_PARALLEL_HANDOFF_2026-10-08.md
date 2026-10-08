# MONEY Ω — AppDeploy/Codex parallel handoff (2026-10-08, America/Mexico_City)

## Scope and authority
Owner: MONEY Ω. Nodes: MONEY Ω · CHATGPT (research / RED TEAM), MONEY Ω · CODEX (engineering and validation), MONEY Ω · GROK (independent review), AppDeploy (public research application). Ω PREDICT is an internal module.
This file is a read-only continuity packet for Codex, not an instruction to place trades, sign with wallets, send money, or enable LIVE.

## Primary current surface — ACCESS VERIFIED
- App ID: `money-z6epdn`
- Site: https://money-z6epdn.v2.appdeploy.ai/
- AppDeploy deployment: READY, after a UI-only coordination change on 2026-10-08.
- Built-in QA snapshot: no frontend or network errors reported; this is not proof of independently validated prices.
- Enabled cron: `money-five-minute-cuts` = `*/5 * * * *`, TZ America/Mexico_City, handler `collectMoney`; latest observed run at time of audit reports success, failure_count=0.
- Second historic deployed MONEY app: `money-umvfi9`; NOT designated canonical. Do not point independent collectors at both.
- Verified code: `src/App.tsx`, `backend/index.ts`, `shared/research.ts`, `tests/tests.json`.

### Change completed exclusively in AppDeploy
Bridge tab now distinguishes CHATGPT/CODEX/GROK roles and links to:
- Canonical GitHub root and `money-codex/` folder;
- Operating Bridge v2.1 on Drive;
- Codex Cloud continuity doc on Drive;
- public Grok site.
UI warns explicitly: direct authenticated CODEX/GROK connections are NOT verified. Market collection, inference and cron behavior were not changed.

## External sites and unresolved identity
- GROK URL: https://themoney.grok.me/ — known canonical URL, but direct content retrieval returned cache miss / inaccessible in audit. ACCESS PARTIAL (URL documented, current UI unverified).
- A distinct **ChatGPT Sites** MONEY URL was not recoverable from the project's attached records, AppDeploy inventory, or Drive continuity. Do not invent a second site or claim it was compared visually. The existing MONEY site built from the ChatGPT side is the AppDeploy URL above.
- Browser and mobile visual QA screenshots are present in AppDeploy's deployment state; independent click-through for all venue quotes remains pending.

## Canonical documentary / technical surfaces — ACCESS VERIFIED
- Drive: https://docs.google.com/document/d/1dPrxCh88qwUZyXgRFrgfPdpunu258-Xu1lxEoBUKMik/edit (Operating Bridge v2.1).
- Codex continuity: https://docs.google.com/document/d/1G0XJnysMf-_47TLBpzWrI0p5LfYTIPY7Lp0Qg8m5RaE/edit (v2.0, project ID pending).
- GitHub technical: https://github.com/reyfilosofo/renova-agent/tree/main/money-codex.
- Main `money-bridge/README.md` still calls nodes 'Ω PREDICT' and 'MONEY Grok Bot' as primary peers; reconcile versioned terminology via Codex change, avoiding opportunistic simultaneous edits to its working files.

## Invariants Codex must preserve
1. Six assets BTC ETH SOL DOGE XRP BNB and 5m/15m/1h fixed windows. No invented future odds.
2. `quoteAt` from the source is distinct from `receivedAt`; absent market quote timestamp means PUBLICADO, not LIVE.
3. Polymarket and Predict quotes require contract identity, matching start/end, resolution, reference, priceKind, and comparable costs; different probabilities alone never constitute edge or arbitrage.
4. `Pcontract = null` and `calibrated=false` for experimental spot model v1.1; never label this a tradeable win probability.
5. `RENOVA_DESK_V0` is isolated BTC-USD PAPER EMA 12/26 1h, 14 days. No LIVE order routing in v0.
6. Any future LIVE rail requires a strategy_id, revocable authorization, valid risk bounds, idempotency, reconciled real exchange account and functioning kill switch. No Coinbase account connection or actual fill was verified in this session.
7. Secrets never enter GitHub, public AppDeploy frontend, or intermodel packets.

## ZIP/code checks
Supplied `MONEY_OMEGA_CODEX_CLOUD_BOOTSTRAP_V2_2026-10-07.zip` contains `money-codex/` Python core and sample tests.
Local `python3 -m unittest discover -s tests -v`: four tests passed (active auth, draft auth rejected, opportunity EV, packet hash).
Important gap: the sample `authorization.py` validates presence of `limits`, not the numeric bounds/max exposure; separately verify field types, issued_at timing, venue/assets, account state, signed authorization provenance and replay protection. Passing four sample tests DOES NOT enable LIVE.

## Next Codex acceptance tasks
- T1: Canonical State: reconcile naming + schemas under `money-app/`, `money-bridge/`, `omega-predict/`, `money-codex/`, Drive v2.1, and AppDeploy 1.1. Keep strategy ledger separated.
- T2: Market acceptance: independently test quote timestamp, contract identity, automatic stale shutdown, venue-gap suppression and fee/slippage null propagation (including 403/429/451).
- T3: Runtime: verify 5-minute jobs store exact real capture timestamps; verify no duplicate writer, no retrodated captures, and consistent export for 24/96/288 windows.
- T4: Security gate: fail closed if authorization or risk policy are incomplete/expired; do not add live adapters by copying PAPER logic.
- T5: Intermodel bridge: only claim CODEX/GROK direct connection after authenticated round-trip proof. Otherwise export review packets through GitHub/Drive.
- T6: Sites compare: obtain the exact additional ChatGPT Sites MONEY URL (if separate), and authenticated/readable Grok UI; test route, mobile UX, freshness, sources and navigation without fabricated results.

## Verification/status
- AppDeploy release for bridge UI: READY, no reported frontend/network errors; cron enabled and recent reported success.
- GitHub/Drive continuity: ACCESS VERIFIED.
- Grok site visual content: ACCESS UNAVAILABLE; public URL documented only.
- Distinct ChatGPT Sites MONEY: ACCESS UNAVAILABLE until exact URL surfaced.
- Coinbase LIVE account/positions/authorization: ACCESS UNAVAILABLE.
- Financial classification: DATA INSUFFICIENT / NO PLAY. NO HAY EDGE DEMOSTRABLE.
