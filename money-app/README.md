# MONEY

MONEY is the mobile-first market-intelligence surface for MONEY Ω.

Live PWA / web app: https://money-z6epdn.v2.appdeploy.ai/

## Scope

- Assets: BTC, ETH, SOL, DOGE, XRP, BNB
- Windows: 5m, 15m, 1h
- Spot consensus: Binance + Coinbase public market data
- Prediction surfaces: Polymarket, Binance Predict, Coinbase/Kalshi when contract data is verifiable
- MONEY Ω estimate: independent statistical baseline with uncertainty
- 24H view: 24 hourly scenario projections, explicitly not prediction-market quotes

## Core integrity rule

Do not compare two percentages until the system verifies the same asset, same time window, same Up/Down definition, same contractual resolution method, and sufficiently fresh timestamps. Otherwise mark CONTRACT MISMATCH.

Wallets such as Coinbase Wallet, MetaMask and Trust Wallet are routing/access surfaces. They must not be treated as independent probability sources unless the underlying contract/venue is identified.

Missing data is NO VERIFICADO or UNAVAILABLE. Never synthesize a venue quote.

## Product surfaces

- PWA / web app / website: deployed
- ChatGPT plugin + skill: MONEY v1.0
- GitHub: technical truth and versioned bridge
- Google Drive: human-readable operating archive
- MONEY Ω · GROK: independent review node consuming versioned packets/bridge, when it has real access

No API secrets, wallet keys, seed phrases or session credentials belong in this repository.
