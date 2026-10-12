---
title: "MONEY — public research application"
type: proyecto
project: MONEY
status: activo
version: "1.1.0"
created: 2026-10-04
updated: 2026-10-12
source_commit: 810f934cf6fece768ed19c9494e84568ccbe397f
---

# MONEY

MONEY is the mobile-first market research surface of MONEY Ω. Ω PREDICT is an internal probabilistic module. Engineering work belongs to MONEY Ω · CODEX; independent review belongs to MONEY Ω · GROK.

Canonical PWA / web app: https://money-z6epdn.v2.appdeploy.ai/

## Scope and current methodology

- Assets: BTC, ETH, SOL, DOGE, XRP, BNB.
- Fixed UTC windows: 5m, 15m and 1h; display timezone America/Mexico_City.
- Spot and experimental research: public Kraken/Coinbase USD. USD and USDT references remain separate.
- Published venue indicators: public Polymarket/Predict HTML/RSC; no Polymarket/Predict market APIs in this app.
- Coinbase/Kalshi: retain unknown or incompatible states until the exact contractual surface is identified.
- Model: MONEY_FIXED_WINDOW_ANALOG_PAPER_V1, experimental spot bias conditioned on non-flat historical analogues. Pcontract=null, calibrated=false, confidence MUY BAJA, recommendation WAIT.
- 24-hour view: historical-return scenarios with a dated common reference and descriptive bands; no invented future market quotes or demonstrated hit rate.

The 1.1 data contract is documented in [DATA_CONTRACT.md](DATA_CONTRACT.md); implemented handler paths and transport limits are in [API.md](API.md). These documents describe source behavior, not a fresh market-data observation.

## Contract and freshness gate

A venue difference is descriptive until the same asset, exact window, option, reference/unit, resolution method, tie rule, price kind, timestamps and costs are verified. A 70% versus 59% display alone does not establish edge or arbitrage.

Keep quoteAt separate from receivedAt. Without a verified source tick, a valid published indicator is PUBLICADO rather than LIVE. Suspend expired readings. Missing data remains null, NO_VERIFICADO or UNAVAILABLE; never synthesize a quote, cost or liquidity value.

Polymarket Up/Down published values stay independent. Predict Down may be a derived complement, labelled accordingly; it is not a second executable offer. Wallets such as Base/Coinbase Wallet, MetaMask and Trust route to underlying providers and do not add independent market confirmations.

## Archive and writers

collectMoney is the single scheduled writer of the existing app archive. The configured five-minute cron is distinct from the visible UI's 15-second polling; neither is exchange streaming.

POST /api/capture only checks whether the current cut exists. It does not produce a manual capture. Preserve actual asOf, the first available capture and future windows as pending. A new MONEY runtime must use a separate store and must not create another writer over the AppDeploy archive.

## Nodes, evidence and deployment

- MONEY Ω · CHATGPT: research, evidence, RED TEAM and review packets.
- MONEY Ω · CODEX: engineering, validation and a separately versioned runtime.
- MONEY Ω · GROK: independent review when actual access exists.
- GitHub main: technical truth; the current Drive Operating Bridge is documentary truth. Its v2.1 reference was read again through authenticated Drive access on 2026-10-11T17:28:54Z; that read does not establish automatic synchronization.
- MONEY skill: 1.1.0. Project IDs, URLs and links do not prove authenticated agent communication.

The dated [parallel handoff](../money-bridge/APPDEPLOY_CODEX_PARALLEL_HANDOFF_2026-10-08.md) records a UI-only release and an earlier enabled cron. The subsequent [credit incident](../money-bridge/APPDEPLOY_CREDIT_INCIDENT_AND_CANDIDATES_2026-10-08.md) records its suspension. A new platform metadata read on 2026-10-11 still reports frontend READY and cron disabled with credits_exhausted; the last reported run is 2026-10-08T16:40:19Z. Source prices, current contract equivalence and archive readback have not been verified by that metadata read.

[DEPLOYMENT.json](DEPLOYMENT.json) remains the historical 2026-10-04 record, including its recorded plugin version. [Current reference annotations](../money-bridge/CURRENT_STATE_2026-10-11.json) are separate; they do not rewrite that history.

Direct ChatGPT↔Codex/Grok-bot connections remain unverified until a real authorized endpoint, authentication and matching round-trip receipt are observed. No order, wallet signature or transfer is authorized by a packet or this documentation.

## Resource discovery

The separate [resource rail](../money-resources/README.md) uses MONEY Ω · CODEX 0.3.0 and public GET requests. Its real 2026-10-11 scan observed 10 sources and 17 discovery candidates: 10 Immunefi bounty programmes and 7 programme/catalogue pages. Eligibility, expected net reward and received income remain unverified. The GitHub Actions schedule is active every six hours, subject to platform delays. [The first production run](https://github.com/reyfilosofo/renova-agent/actions/runs/38160287636) passed its test and discovery jobs on 2026-10-11 at 17:35:53Z and published a real 17-candidate report. The resource dashboard is [published privately in Sites](https://money-omega-recursos.seresarte.chatgpt.site), with owner access and no MCP endpoint. It does not resume the AppDeploy market collector.

No secrets, session credentials, private conversations or personal financial screenshots belong in the public repository.

## Verificación operativa del 12-Oct

El [estado actual verificado](../money-bridge/CURRENT_STATE_2026-10-12.json) registra tres ejecuciones programadas de recursos con SUCCESS. La más reciente terminó el 12-Oct15:22:24Z y publicó 17 candidatos de 10 fuentes, con ledger íntegro y ningún ingreso confirmado. El cron solicita una cadencia de seis horas; hubo demoras reales de GitHub y no se garantiza ese intervalo. El panel privado de Sites sigue activo para el propietario.

Una nueva lectura autenticada de AppDeploy el 12-Oct informa el collector de mercados habilitado y un run reciente exitoso. Esa observación supera el estado deshabilitado del 11-Oct; los incidentes históricos se preservan. Codex no cambió el cron ni compró créditos. El snapshot de la app devuelve datos actuales, pero una cuota PUBLICADO sin quoteAt verificado no es LIVE ni demuestra edge.

Los dos puentes de Drive tienen las adiciones operativas del 11-Oct y su lectura autenticada se verificó otra vez el 12-Oct. Eso acredita actualizaciones documentales, no un Drive writer continuo ni comunicación directa entre agentes.
