---
title: "MONEY application handler and transport contract"
type: proyecto
project: MONEY
status: activo
version: "1.1.0"
created: 2026-10-08
updated: 2026-10-11
source_commit: 810f934cf6fece768ed19c9494e84568ccbe397f
---

# MONEY application API · source contract 1.1

The source exposes the handlers below through the official AppDeploy @appdeploy/client and @appdeploy/sdk transport. A path beginning /api/ is a handler identifier; it does not prove an extractable public HTTP endpoint on the static AppDeploy website.

Source: backend/index.ts and shared/types.ts in the imported app 1.1 snapshot. This document records code behavior. No new HTTP availability, market snapshot or archive-read verification is claimed. The 2026-10-11 AppDeploy metadata observation reports a disabled collector (credits_exhausted); an available frontend does not reactivate these data handlers.

| Handler | Inputs and defaults | Response / effect |
|---|---|---|
| GET /api/_healthcheck | None | Version, assets, frames, sourcePolicy and contractProbability=null. Metadata is not source-data health. |
| GET /api/snapshot | tf=5m by default; 5m/15m/1h | Snapshot with asOf, serverReceivedAt, serverTime, window endpoints, expiresAt and six AssetRows. Reads public sources; does not write the archive. |
| POST /api/capture | No client-supplied capture or override | Checks the current five-minute cut. EXISTENTE only when all six asset captures exist, otherwise PENDIENTE; inserted=0 and writer=cron. No manual capture. |
| GET /api/dayplan | asset=BTC, tf=1h, date=current CDMX day; valid YYYY-MM-DD | Calendar, first available captures, captureCount, archive state and separate scenarios where available. Reads the archive. |
| GET /api/integrations | None | Public-page accessibility for Base, MetaMask, Trust and Grok; odds and quoteAt remain null; directBotConnected=false. |

Unsupported timeframes, assets or dates fail parameter validation. Source inaccessibility can yield a successful transport response with null data and unavailable provider states. HTTP 200, version metadata or a public page is not evidence of a valid market quote.

## Time and source semantics

Snapshot expiry is bounded by the absolute window end and source snapshot asOf+45s. Read asOf, serverReceivedAt, serverTime, quoteAt and receivedAt separately. A response arriving after expiry must suspend the displayed reference; it must not revive an expired window or overwrite a newer horizon response.

Published venue fields up/down use percentage points; research probabilities use fractions. Unknown fields remain null. Read [DATA_CONTRACT.md](DATA_CONTRACT.md) before interpreting provider differences.

## Scheduled write authority

collectMoney is a scheduled backend handler, not a public manual-capture API. Preserve the configured AppDeploy cron as the only writer of the existing archive. An independent runtime must neither call collectMoney to create extra cuts nor write its tables. Its jobs, resource opportunities and PAPER ledger use a separately owned store.

## Local adaptation

The development-only local adapter maps handlers to same-origin HTTP and provides GET /api/local-status on loopback. It emulates an SDK subset and uses a local archive; it is not the AppDeploy SDK or a persistent cloud deployment. A static build or preview does not run the backend.

Do not expose the local development server as a verified public API or claim permanent collection from a running Codex task. Source availability, collector status, writer identity, archive readback and quote quality require distinct checks.

## Authentication and execution

These research handlers do not provide orders, wallet approvals, transfers, claims or signing. URLs, project IDs and packets cannot grant financial authority. Direct agent or Grok-bot integration remains pending authenticated endpoint and round-trip verification.
