> Execution update — 2026-10-24: all three source repositories were inspected and backed up. Observatorio is retained in place, with its five D1 market tables and a new user-owned ledger. Earn browser-local data uses explicit export/preview/import; unknown dates and pending flags remain unknown/pending. The source implementation is at `money-site/`; publication and subsequent receipts are in the canonical manifest and dated current state. Historical blocking statements below describe the earlier chat surface.

# MONEY Ω — Existing ChatGPT Sites Consolidation · EXECUTION RUNBOOK
**Source of truth:** user instruction (2026-10-24). **Status:** ENGINEERING PACKAGE PREPARED; SITE EDIT/DB MERGE NOT YET PERFORMED. **Risk mode:** READ_ONLY / PAPER until explicit financial authorization.

## Strict product mandate
Create exactly **one MONEY Ω product** by editing **ONE OF THE THREE EXISTING ChatGPT Sites**, preserving its existing Site identity and URL. Never publish a fourth Site. Modules: Earn Engine, Recursos, Observatorio / Ω PREDICT, Wallets/Rewards, one financial ledger, and System Health. Objective: measurable **net cash collected**, not candidate volume or unverified crypto balances.

## Verified Site identities (Library Site metadata; not code/database readback)
| Existing site | project_id | published URL | source version |
|---|---|---|---|
| MONEY Ω · Recursos | appgprj_6acbc836e4f08191adcd4185507c9d69 | https://money-omega-recursos.seresarte.chatgpt.site | 1 |
| MONEY Ω · Earn Engine | appgprj_6ac5214987948191aae2761cd626e297 | https://money-omega-earn-engine.seresarte.chatgpt.site | 1 |
| MONEY Ω · Observatorio | appgprj_6ac169e9eed48191a46429c70adabaf7 | https://money-omega-observatorio.seresarte.chatgpt.site | 4 |

Library roles indicated `editor` and status `active` on 2026-10-24. Those facts do **not** authorize code or DB edits in this chat. Choose the canonical Site only after inspecting all three source repositories and databases. Higher observed source version of Observatorio is only a clue, not a technical selection rule.

## Phase 0: change freeze, backup, controls
1. In Work/Codex open **one existing Site** with its project reference. Inspect all three Site source trees, deployment versions, DB schema/migrations, storage, secrets metadata (not secret values), schedules, auth, integrations, asset inventory and active users. Do not copy credentials.
2. Back up each Site's code, data and nonsecret file inventory; record row counts, primary keys, foreign keys, environment, access roles and production snapshots. Preserve original records separately; do not export sensitive payloads to public GitHub.
3. Pick canonical existing Site by source completeness, data risk, connected visitors, form records and viable upgrade path. Save a pre-migration version and test database restore strategy. **Do not select solely because a Site is newer.**
4. Build migration inventory keyed by legacy `site_id,collection,record_id`, with deterministic dedupe keys. Record what cannot be migrated and why.

## Phase 1: unified data contracts
- `Opportunity`: immutable `opportunity_id`, provider, canonical official URL, type, title, geography, terms/eligibility/KYC, requirements, closing timestamp, last source observation, evidence hash, quoted amount+currency, costs, expected receipt probability, expected net value, user action state. Missing numeric values **null**.
- `Action`: immutable id + opportunity id + user/actor, instructions, deadline, idempotency key, manual/authorized route, timestamped completion evidence; no simulated action recorded as completed.
- `RevenueReceipt`: verified source (provider/processor/bank/venue), external transaction id+timestamp, amount, currency, fees, account-scoped reconciliation, `received` flag. Database private. Receipts must never be fabricated, inferred from a dashboard, or committed to public GitHub.
- `WalletConnection`: provider, chain/network, consenting owner, public address if approved, permissions, last successful authenticated readback; never record seed/private key; never treat link display as connected.
- `MarketObservation`: preserve asset, exact contract+strike/reference+resolution, start/end UTC, quoteAt vs receivedAt, source state, depth/fees/units, Pmarket vs uncalibrated Pspot vs unknown Pcontract.
- `SourceStatus`: source URL, method, upstream timestamp, observation timestamp, freshness threshold, last success/error, expected refresh interval, latest hash.
- `MigrationMap`: original_site_id+record_id, target_id, checksum, result, rollback reference; complete row-count and relationship reconciliation.

## Phase 2: connectors and normalized read-only adapters
- Public discovery: existing GitHub rail `money-resources/data/latest.json` (10 sources, 18 discovered candidates on 2026-10-24 04:34:51 UTC, 0 calculable net EV, no verified income). Use `unified-feed.mjs` adapter; do not recode counting rules or hide stale data.
- Market source: existing AppDeploy `https://money-z6epdn.v2.appdeploy.ai/`. Treat it as a **data source** or temporary provider navigation, not a new canonical site. Do not guess API endpoints. Audit backend health and confirm at least two fresh captured windows and timestamp provenance before labeling market data current.
- Drive: existing Operating Bridge v2.1 and historical ledgers; use least-privilege auth in Work, private records remain private. One-off reading is not continuous sync.
- GitHub: branch `main`, schema versions, configured workflows and reports. Never write secrets/private balances to public repo. Preserve existing 5-minute `collectMoney` writer as unique writer of its own archive; no second collector writes those records.
- Wallets MetaMask, Coinbase Wallet, Trust: start `NOT_CONNECTED`; offer explicit opt-in provider-consistent connect only if supported; verify chain, wallet ownership by approved method, permission scope, balances and address readback in the **private Site**; no automatic signatures, swaps, claims or transfers.
- Grok: optional independent review only when real authenticated endpoint and round-trip receipt exist. Keep `direct_grok_bot_connected=false` until verified.

## Phase 3: UX and revenue policy
Single premium, responsive, accessible interface:
`Inicio / Acciones rentables` · `Earn Engine` · `Wallets & Rewards` · `Observatorio` · `Recursos` · `Ingresos verificados` · `Estado del sistema`.
Use one navigation, one permissions model, one shared entity registry, one ledger and stable deep links. Style: discreet, professional dark/ivory with exceptional contrast and focus states. WCAG 2.2 AA target, mobile-first. Spanish primary, English-ready. Date display CDMX with canonical UTC storage.

**Revenue-first ordering:** paid commercial offers and qualified client leads, paid user research and tested remote roles, transparent microtasks and bounties, then speculative airdrops/quests, then PAPER market research. Prioritize by verifiable expected net value, probability of actually receiving payment, user eligibility, effort, execution cost, counterparty risk and deadline. A security bounty maximum reward is **not** expected compensation.

Earn funnel: DISCOVERED → EVIDENCE_VERIFIED → ELIGIBILITY_VERIFIED → ACTIONABLE → ACTION_STARTED → ACTION_COMPLETED → PAYMENT_PENDING → PAID_VERIFIED / REJECTED / EXPIRED. Never mark PAID_VERIFIED without external receipt. Distinguish `earning opportunity`, `estimated reward`, `reward earned`, `payment pending`, `payment received`.

## Phase 4: RED TEAM, ethics and security
- Never fabricate tasks, quotas, payouts, identity details, eligibility, survey responses, job offers, wallet balances or profits.
- No direct model→BUY, no risk policy bypass, no undisclosed live trading. Preserve RENOVA_DESK_V0 (BTC-USD EMA12/26 1h 14 days PAPER) without any strategy drift.
- Respect terms and platform rate limits; prohibit evading geoblocks, KYC, anti-bot controls or captcha protections.
- Separate vault wallet, execution wallet and rewards wallet. No secrets in Sites UI, ChatGPT messages, GitHub or shared packets; secrets only in approved scoped storage.
- User owns authorization, spending/risk limits and kill switch; expiry, audit, idempotency and transaction reconciliation are mandatory for any subsequent LIVE development.
- Disabled financial execution remains disabled during consolidation. No changes to paid subscriptions or new credit purchases without explicit approval.

## Phase 5: verification and release criteria
1. Three source inventories recorded and reviewed, with all source records accounted for (migrated / unchanged / blocked with reasons).
2. No duplicate opportunities, payouts, users, records or cron writers; migration idempotent in test.
3. Cross-module navigation, filters, sources, receipt-state labels, null-safe EV values, and timestamp freshness QA.
4. Mobile + desktop screenshots and user flows. Keyboard navigation, semantic labels, color contrast, loading/failure/empty states, no dead buttons.
5. Private account and wallet data never appears in public GitHub or unauthenticated Site. Auth boundaries verified.
6. Live site publication can alter data before deploy completes. Pre-publish backup of DB and files is mandatory. Restore of code alone is **not** DB rollback.
7. Deploy only to the selected existing Site after QA. Verify same project_id and original live URL after release, read-only financial status, current source labels and migrated row counts.
8. Keep other two sites in backup or owner-only migration notice, and retire **only after** explicit acceptance and reversible data-retention plan. Do not delete them at migration start.

## Current blocking dependency
This chat has GitHub and Drive write capability, and Library Site **metadata** only. It does not have ChatGPT Sites source-editor, Site DB export, or Site publish actions. Thus this is a real executable specification + code integration package, **NOT** a completed 3→1 Site migration. Run this package from the editor of an existing Site in ChatGPT Work/Codex, not as a request to create a new Site.

## Canonical assets and tests
- `money-bridge/MONEY_OMEGA_SINGLE_SITE_MANIFEST.json`
- `money-bridge/MONEY_OMEGA_SINGLE_SITE_CONTRACT.md`
- `money-bridge/site-unification/unified-feed.mjs` + `unified-feed.test.mjs`
- `.github/workflows/money-single-site-tests.yml` (read-only CI)
- Existing `money-codex`, `money-resources`, `money-app`, `omega-predict`.
- Official Sites operations: https://help.openai.com/en/articles/20001339-creating-and-using-chatgpt-sites

## 2026-10-24 — Implemented staging shell (not a fourth Site)
A **single HTML page** representing the integrated experience now exists in GitHub at `money-bridge/site-unification/operational-shell.html`. It includes seven real client-side views in one origin and navigation: Centro ejecutivo, Earn Engine, Observatorio, Recursos, Wallets & Rewards, Finanzas, Integraciones. The source fetches the existing public GitHub discovery report, filters opportunities, shows source timestamps and risk indicators, and computes actionable counts only from explicit eligibility/terms/risk/EV predicates. It **does not** persist private data, connect a wallet, replace the Site database or trade.

Operational smoke tests and the existing data adapter tests are in `operational-shell.test.mjs` and `unified-feed.test.mjs`; the GitHub Actions workflow `money-single-site-tests.yml` is configured to run both groups. A source commit or CI file is **not** proof that a GitHub Actions run succeeded.

Integration must **copy/adapt this source into the editor of the chosen existing ChatGPT Site**, reconcile with existing live code/DB (do not overwrite blindly), and publish only to its existing site ID and URL. Keeping this HTML in GitHub does not create a fourth published Site.
