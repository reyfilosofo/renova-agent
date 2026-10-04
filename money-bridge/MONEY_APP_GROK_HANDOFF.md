# MONEY APP → MONEY Ω · GROK HANDOFF

Created: 2026-10-04
Status: READY FOR INDEPENDENT REVIEW

## System

MONEY Ω

## User-facing application

Name: MONEY
Live PWA / website / web app:
https://money-z6epdn.v2.appdeploy.ai/

AppDeploy ID:
money-z6epdn

## ChatGPT surface

Plugin / skill:
MONEY v1.0.0

Plugin ID:
plugins_6ac2270854448191bbd51cc715d67af9

## Coverage

Assets:
BTC, ETH, SOL, DOGE, XRP, BNB

Windows:
5m, 15m, 1h

Views:
- live market desk
- countdown by window
- spot consensus
- Polymarket
- Binance Predict
- Coinbase/Kalshi public surface when verifiable
- raw venue divergence
- MONEY Ω independent estimate
- 24 hourly statistical scenarios
- clickable market links

## Important contract rule

A 70% reading and a 59% reading are NOT automatically an exploitable discrepancy.

Before interpreting cross-venue divergence as edge, independently verify:

1. same asset
2. same window start
3. same window end
4. same Up/Down condition
5. same or materially equivalent resolution source
6. freshness
7. fees
8. spread
9. slippage
10. liquidity

Otherwise report CONTRACT MISMATCH.

## Wallet rule

Coinbase Wallet, MetaMask and Trust Wallet are access/routing surfaces unless the wallet itself is demonstrably the origin of the market contract. Attribute displayed odds to the actual underlying venue.

## Review request to MONEY Ω · GROK

Independently test:
- source freshness
- Coinbase public 15m extraction
- Binance Predict availability by asset/timeframe
- Polymarket window alignment
- settlement-source differences
- regional availability
- any market-data adapter that can improve reliability

Do not infer execution authority from this handoff.

Return material findings through the existing MONEY Ω intermodel review workflow.

## Canonical references

GitHub:
- money-app/README.md
- money-app/DATA_CONTRACT.md
- money-app/DEPLOYMENT.json
- money-bridge/MONEY_APP_BRIDGE_V1.md
- money-bridge/schemas/
- omega-predict/MASTER_PROTOCOL.md

Drive:
MONEY — MARKET CONSENSUS ENGINE — OPERATING BRIDGE v2.0
Document ID:
1dPrxCh88qwUZyXgRFrgfPdpunu258-Xu1lxEoBUKMik

## Security

No secrets, seed phrases, private keys, passwords or session tokens are included.
