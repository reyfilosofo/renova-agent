# Ω PREDICT · MARKET SCHEMA

## Market identity
`market_id`, `timestamp_observed`, `timezone`, `platform`, `market_type`, `category`, `asset_or_event`, `contract_question`, `contract_url`, `deadline`, `resolution_criteria`, `resolution_source`, `ambiguities`.

## Market state
`yes_price`, `no_price`, `up_price`, `down_price`, `odds`, `implied_probability`, `volume_24h`, `total_volume`, `liquidity`, `spread`, `estimated_slippage`, `fees`, `price_change_recent`, `market_timestamp`.

## Evidence
`primary_sources`, `professional_sources`, `social_sources`, `rumors`, `verified_facts`, `reported_information`, `inferences`, `hypotheses`, `counter_evidence`, `source_freshness`, `information_time_vs_price_move`.

## Model
`p_market`, `p_estimate_central`, `p_estimate_low`, `p_estimate_high`, `edge_gross`, `cost_adjustment`, `uncertainty_adjustment`, `edge_after_adjustments`, `confidence`, `confidence_reason`.

## Thesis control
`thesis`, `catalyst`, `invalidation`, `validity_window`, `what_to_watch`, `red_team_case`, `alternative_explanation`.

## Signal classification
Exactly one:
- NO PLAY
- WATCH
- POSSIBLE EDGE
- STRONG INFORMATIONAL EDGE
- DATA INSUFFICIENT

## Screenshot ingest
`platform`, `market`, `asset`, `event`, `selection`, `visible_price`, `visible_odds`, `yes_no`, `up_down`, `expiry`, `volume`, `liquidity`, `spread`, `visible_timestamp`, `visible_rules`, `current_position`, `amount`, `pnl`, `uncertain_or_illegible_fields`.

## Postmortem
`entry_price_observed`, `initial_p_estimate`, `initial_interval`, `initial_evidence`, `outcome`, `new_information`, `process_strengths`, `process_failures`, `information_edge_present`, `move_foreseeable`, `biases`, `error_class`, `brier_score`.

## Error classes
DATA ERROR / REASONING ERROR / TIMING ERROR / EXECUTION ERROR / RANDOMNESS / UNFORESEEABLE EVENT