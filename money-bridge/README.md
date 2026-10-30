---
title: "MONEY Ω shared research bridge"
type: proyecto
project: MONEY
status: activo
version: "1.1"
created: 2026-10-04
updated: 2026-10-30
source_commit: 810f934cf6fece768ed19c9494e84568ccbe397f
---

# MONEY Ω — Shared research bridge

The bridge preserves evidence and versioned handoffs among MONEY Ω · CHATGPT, MONEY Ω · CODEX and MONEY Ω · GROK. Ω PREDICT is an internal probabilistic module, not a separate execution authority.

## Roles and access

- CHATGPT: research, provenance, screenshots, RED TEAM and review packets.
- CODEX: engineering, tests, runtime and reconciliation.
- GROK: independent review when real access is verified.
- Human operator: final authority; no prompt or model creates a new authorization.

GitHub main is technical truth; the current Drive Operating Bridge is documentary truth. Authenticated Drive reads on 2026-10-11T17:28:54Z reverified Operating Bridge v2.1, its MONEY skill 1.1.0 reference, and Codex Cloud Bridge v2.0 with pending project IDs. Reading these documents does not establish automatic synchronization. [Current dated annotations](CURRENT_STATE_2026-10-11.json) distinguish these references from [historical deployment](../money-app/DEPLOYMENT.json).

Direct authenticated ChatGPT↔Codex/Grok-bot connectivity is not verified. GitHub, Drive, structured packets and separately verified runtime state are the intended shared bus. A URL or project ID does not establish an API or synchronization.

## Versioned flow and receipts

Research packets carry identity, UTC creation/expiry, source evidence, uncertainty, counter-evidence, costs and invalidation. Receivers validate their declared schema, freshness, producer/source provenance and content hash. Actual transport and matching receipt are required before claiming delivery or a round-trip.

The historical schemas in schemas/ remain version 1.0. The Python runtime uses envelope 2.1; the bootstrap envelope 2.0 and historical attachment formats are separate contracts; do not feed one format into another validator or claim automatic compatibility. Any conversion must have explicit versioned mapping, validation fixtures and provenance. A SHA256 digest is integrity evidence when verified, not producer authentication or financial authority.

Disagreement is recorded explicitly; do not average model conclusions into an executable signal. Preserve expires_at and abstain on stale/incomplete evidence.

## Market integrity and resources

Keep Pmarket, Pspot experimental and Pcontract separate; app1.1 retains Pcontract=null and calibrated=false. Match exact contracts, windows, references, resolution and costs before interpreting venue gaps. Wallet mirrors do not count as independent venues.

The [resource rail](../money-resources/README.md) now has a locally executed public scanner in MONEY Ω · CODEX 0.3.0. A real scan on 2026-10-11 observed 10 sources and 17 candidates (10 Immunefi bounty programme links, 7 programme/catalogue pages), with zero queued actions and no verified eligibility, EV or received income. GitHub Actions every-six-hour execution is active: [the first production run](https://github.com/reyfilosofo/renova-agent/actions/runs/38160287636) passed both test and discovery jobs, completing on 2026-10-11 at 17:35:53Z. Its report was generated at 17:35:47.468176Z with all 10 source accesses verified and ledger integrity true. [The Sites resource dashboard](https://money-omega-recursos.seresarte.chatgpt.site) was published privately at 17:35:08.055005Z; publication does not establish an agent endpoint.

Resource discovery is a separate rail keyed by opportunity_id. Document eligibility, evidence, deadline, units and nullable costs; unknown costs do not become zero. Scoring or a prepared claim/quest/survey is not an authorized external action.

## Writers and storage

- GitHub: sanitized code, schemas, prompts, technical history and non-secret examples.
- Drive: private documentary reports and human operating archive.
- Runtime: separately owned evidence/jobs/receipts/PAPER ledger; configuration does not prove a deployed service.

No continuous Drive sync or autonomous writer is assumed. New writers require explicit scope, configuration, readback and durable receipt. Preserve the existing AppDeploy collectMoney cron as the sole writer of its archive; independent runtimes never create a second writer over those tables.

No accounts, conversations, raw private screenshots, balances, keys, session credentials or tokens belong in public GitHub or review packets. Follow SECURITY.md.

## Historical evidence

MONEY_APP_BRIDGE_V1.md and prior schemas remain historical versioned evidence. MONEY_APP_GROK_HANDOFF.md reconciles its current reference versions while retaining its original creation date. APPDEPLOY_CODEX_PARALLEL_HANDOFF_2026-10-08.md records a UI-only AppDeploy change and an earlier enabled cron. APPDEPLOY_CREDIT_INCIDENT_AND_CANDIDATES_2026-10-08.md records the subsequent suspension. Platform metadata read on 2026-10-11 reports the cron still disabled (credits_exhausted), with last run 2026-10-08T16:40:19Z. These historical records are preserved; frontend READY does not verify quote data or authorize trading.

## Verificación operativa del 12-Oct

El [estado actual verificado](CURRENT_STATE_2026-10-12.json) registra tres ejecuciones programadas de recursos con SUCCESS. La más reciente terminó el 12-Oct15:22:24Z y publicó 17 candidatos de 10 fuentes, con ledger íntegro y ningún ingreso confirmado. El cron solicita una cadencia de seis horas; hubo demoras reales de GitHub y no se garantiza ese intervalo. El panel privado de Sites sigue activo para el propietario.

Una nueva lectura autenticada de AppDeploy el 12-Oct informa el collector de mercados habilitado y un run reciente exitoso. Esa observación supera el estado deshabilitado del 11-Oct; los incidentes históricos se preservan. Codex no cambió el cron ni compró créditos. El snapshot de la app devuelve datos actuales, pero una cuota PUBLICADO sin quoteAt verificado no es LIVE ni demuestra edge.

Los dos puentes de Drive tienen las adiciones operativas del 11-Oct y su lectura autenticada se verificó otra vez el 12-Oct. Eso acredita actualizaciones documentales, no un Drive writer continuo ni comunicación directa entre agentes.


## Latest reconciled state — 2026-10-30

The current verified *read-only* MONEY Ω status is [CURRENT_STATE_2026-10-30.json](CURRENT_STATE_2026-10-30.json), recorded by the ChatGPT research node from authenticated/source-specific evidence. Earlier dated files above are historical and must not overwrite the new status.

- **Resource discovery:** 10 public sources, 18 candidates, 0 actionable queue; no net EV estimate for any candidate, `verified_income_usd=null`. The 2026-10-30T12:53:54Z run reports healthy collection but decision readiness DATA INSUFFICIENT.
- **PAPER Desk:** 2026-10-30T15:30:45Z, public Coinbase Exchange observations for six assets; audit integrity valid; RISK Ω = HALT, PAPER/LIVE execution disabled. Public spot ticks are not proof of contract edge or private Coinbase account state.
- **AppDeploy collector:** authenticated service still shows frontend READY but `money-five-minute-cuts` disabled with `credits_exhausted`. The independent [market-health monitor](../money-resources/data/market-health.json) logged three HTTP 402 endpoint failures on 2026-10-30T12:53:55Z. The private billing account simultaneously showed monthly credits remaining; do not publish private amounts or assume a billing fix. [Incident #61](https://github.com/reyfilosofo/renova-agent/issues/61) remains OPEN.
- **Drive:** Operating Bridge v2.1 and Codex Cloud Bridge v2.0 received documentary reconciliation updates on 2026-10-30. Their updates are not an automated writer or a ChatGPT↔Codex connection.
- **ChatGPT Sites:** canonical existing MONEY Ω Observatorio Site v6 publication remains the last verified publishing receipt (2026-10-25); no live site readback succeeded through the present public web tool.
- **Intermodel/security:** direct ChatGPT↔Codex and Grok bot authentication remains unverified, no wallet signer, no private fills, no verified income, no trading enablement.

Do not reactivate the archived market collector, buy credits, or unblock LIVE from a documentation update. Confirm real backend reads, cron enabled and two consecutive verified captures before closing #61; keep missing archive rows null and do not backfill.
