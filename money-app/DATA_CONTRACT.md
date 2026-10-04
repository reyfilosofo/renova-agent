# MONEY Data Contract v1.0

## Asset-window key

Every row is keyed by:

`asset + window_start + window_end + direction_definition + resolution_source`.

Two venue quotes are comparable only when the key is materially equivalent.

## Required row fields

- asset
- timeframe: 5m | 15m | 1h
- observed_at_utc
- window_start_utc
- window_end_utc
- spot_price
- spot_sources
- start_price
- venue
- venue_up_probability
- venue_down_probability
- venue_status
- venue_market_url
- resolution_source
- contract_match_status
- money_estimated_up_probability
- money_uncertainty_range
- divergence_pp
- confidence
- classification
- invalidation_conditions
- validity_window

## Venue status

- LIVE
- STALE
- NO_VERIFICADO
- UNAVAILABLE
- CONTRACT_MISMATCH

## Mandatory safety

No missing odds, liquidity, spread, volume, fills or settlement rules may be invented. Wallet UI values must be attributed to the underlying venue/contract before entering the comparison layer.
