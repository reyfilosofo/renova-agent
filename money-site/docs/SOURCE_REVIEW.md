# Fuentes primarias y software revisado · 2026-10-03

NoWikipedia. Endpoints públicos solo lectura; no cuentas/credenciales. Observaciones de autoría caducan y no son oportunidades actuales.

## APIs

- CoinbasePredictions: https://help.coinbase.com/en/coinbase/trading-and-funding/prediction-markets/intro — operaKalshi; resolución no basada en spotCoinbase; reglasyregiónpropias. No verificarcuenta/eligibilidadpersonal.
- CoinbaseSpot: https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/products/get-product-ticker — público; HTMLenautoría no pruebadatosválidos.
- Polymarket: https://docs.polymarket.com/market-data/discover-markets — Gammaeventos/slugpúblicos; https://docs.polymarket.com/market-data/prices-orderbook — libro; https://docs.polymarket.com/concepts/prices-orderbook — midpointnoask; https://docs.polymarket.com/market-data/realtime-data — requisitosactualesoráculo.
- Kalshi: https://docs.kalshi.com/getting_started/quick_start_market_data — RESTpúblico. https://docs.kalshi.com/cfbenchmarks/rest-passthrough — RTIrequierecredenciales/entitlement.
- Trust: https://trustwallet.com/prediction-markets — venuesintegrados; https://developer.trustwallet.com/developer/mcp/api-gateway — AccessID/HMACobligatorios; nodeclararcomisionesceroatravésdeltexto comercial.
- Kraken: https://docs.kraken.com/api-reference/market-data/get-ohlc-data — máximo720velas,últimavelaabierta; https://docs.kraken.com/api-reference/market-data/get-ticker-information — tickerRESTsin timestampdeoráculo.
- Binance: https://developers.binance.com/en/docs/catalog/core-trading-spot-trading/api/rest-api/market — consulta451geográfica,detenida.

## GitHub: reutilizables, no ventaja probada

|Proyecto|Licencia observada|Uso/decisión|
|---|---|---|
|https://github.com/Polymarket/ts-sdk|MIT|SDKoficialvigente @polymarket/client; V1usaRESTnativo,mínima superficie,sin rutas órdenes.|
|https://github.com/Polymarket/py-sdk|MIT|SDKPythonvigente; no importadocódigo.|
|https://github.com/coinbase/coinbase-advanced-py|Apache2.0|SDKoficial; no equivale a APIpredictions.|
|https://github.com/trustwallet/wallet-core|Apache2.0|Infraestructuracriptográfica,innecesaria para panelinformativo.|
|https://github.com/gregyoung14/openmarket|Apache2.0|Colección/sincronización/evaluación; dataset congelado,no copiaruncódigo de ejecución.|

RepositoriosPolymarket clob-client/py-clob-client/rs-clob-client aparecieronarchivados; docsrecomiendanUnifiedSDKs. No se adoptaronbots que prometanbeneficios.

## Evidencia contraria

https://arxiv.org/abs/2607.26245 — OpenMarket (preprint2026): modeloBTC15m walk-forward conmicroestructura no superóprobabilidad de mercado fuerademuestra y simulaciónneta negativa bajo sus supuestos. No pruebaque todasestrategiasseanimposibles, sí invalida prometeredgeinicial.

## Límites

Sincoinbaseaccounttruth,Trustdirecto,Grokcontrol,oráculoexactoPcontract,modelo validado o tasaaciertodemostrada. Catálogo6activos observado enKalshi/Polymarket no demuestra que todosestén enCoinbase delusuario.1h contractual requiereidentificación independiente. Precios recibidosahora puedentener timestampantiguo; siempreseparar ambos.
