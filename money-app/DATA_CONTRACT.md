---
title: "MONEY data contract"
type: proyecto
project: MONEY
status: activo
version: "1.1.0"
created: 2026-10-04
updated: 2026-10-11
source_commit: 810f934cf6fece768ed19c9494e84568ccbe397f
---

# MONEY Data Contract v1.1

This documentation describes the app 1.1 source and the required audit semantics. It does not silently rename existing wire fields, migrate historical records or replace the bridge packet schemas. Consult [API.md](API.md) for implemented responses.

## Identity, units and time

Identify every observation by asset, timeframe, window_start_utc, window_end_utc, option/direction definition, contract identity, reference/unit and resolution source/rules. Material incompatibility is CONTRACT_MISMATCH; absent identity is NO_VERIFICADO.

Persist UTC and display America/Mexico_City. The app uses Unix milliseconds for windowStart/windowEnd, quoteAt, receivedAt, asOf and expiry fields. A normalized export must declare its timestamp encoding and units explicitly.

- Spot values: USD, with source and source reading time. Do not substitute USDT.
- WebQuote.up/down: published percentage points in [0,100], nullable. Keep the original independent Polymarket sides.
- Research.pUp and intervalUp: experimental fractions in [0,1], nullable; conditioned on non-flat spot analogues.
- Predict Down: derived complement when the parser supplies it, not a separately observed executable offer.
- Pcontract / Research.contractProbability: null in MONEY 1.1.
- divergencePp: percentage-point difference only after the implemented comparability gate; publishedDifferencePp is a descriptive display and does not establish economic equivalence or edge.

## Provenance and unknowns

Retain provider, exact observed URL, contractId, asset, option, window endpoints, reference, referenceUnit, resolutionSource, rules, priceKind, original published sides, quoteAt, receivedAt and costs. A cache read time, page read time or window opening is not a market tick.

Null means unknown. Zero is valid only when explicitly observed and meaningful for the field. Reject nonfinite values, contradictory identities and unsupported units. Unknown costs, spread, slippage, depth, fills or fees cannot be converted to zero or inferred from another venue.

The legacy normalized v1.0 names remain meaningful only with explicit units and provenance: observed_at_utc, spot_price, spot_sources, start_price, venue_up_probability, venue_down_probability, venue_status, venue_market_url, resolution_source, contract_match_status, money_estimated_up_probability, money_uncertainty_range, divergence_pp, confidence, classification, invalidation_conditions and validity_window. money_estimated_up_probability refers to Pspot experimental, never Pcontract. An exporter must map these names explicitly to the source fields; this document is not an implemented exporter.

## Venue states

| State | Meaning |
|---|---|
| LIVE | Identified current window, verified source tick and fresh reading. The source implementation requires tick age ≤30s and reading age ≤90s, with a small clock-skew check. |
| PUBLICADO | Valid published indicator without a verified quoteAt. Not a live tick or executable signal. |
| STALE | Expired window or timestamp/reading outside allowed freshness. Suspend the reference. |
| NO_VERIFICADO | Required market identity or evidence is missing. |
| UNAVAILABLE | Public content cannot be retrieved or read. |
| CONTRACT_MISMATCH | Incompatibility is evidenced; do not compare as the same event. |

Current public-page parsers leave quoteAt=null. They cannot generate LIVE venue quotes merely because polling or cron succeeded. A 403/429/451 triggers abstention or a bounded pause, without evasion or aggressive retries.

## Research, comparisons and classifications

MONEY_FIXED_WINDOW_ANALOG_PAPER_V1 uses closed Kraken USD five-minute candles and the real opening of a fixed window. The final Kraken OHLC row remains unconfirmed even if cached data crosses a boundary. Invalid histories, gaps, missing exact references and nonfinite features invalidate the model.

Keep Pmarket, Pspot experimental and Pcontract separate. A descriptive Wilson interval is not validated calibration, profitability or a contractual win rate. Research retains calibrated=false, contractProbability=null, recommendation=WAIT and confidence MUY BAJA.

Before evaluating any economic difference, verify matching reference, resolution, tie/void rules, timing, price kind and comparable fees/spread/slippage/liquidity. Missing evidence prevents an actionable edge claim. Evaluation ends with exactly one of NO PLAY, WATCH, POSSIBLE EDGE, STRONG INFORMATIONAL EDGE or DATA INSUFFICIENT, with uncertainty and validity/invalidation stated.

## Prospectivity and archive

The single collectMoney cron preserves actual asOf inside the window and the first available capture per asset/window. Future rows remain pending; a later observation must not be backdated. Daily views contain 24/96/288 windows for 1h/15m/5m.

POST /api/capture only reads and reports EXISTENTE or PENDIENTE. It never inserts or replaces records. Other runtimes use separate stores and do not write the existing app archive.

The 24 future scenarios preserve reference, origin and descriptive P10–P90 bands. They are distinct from historical captures and venue quotes; unavailable outcomes are not wins, fills or validated forecasts.

## Public/private boundary

Only sanitized methodology, schemas and technical documentation enter public GitHub. Private account data, conversations, screenshots, balances, session credentials and secrets remain outside it. Any new schema or methodology receives an explicit version and migration record; preserve previous evidence.
