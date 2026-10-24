# Revisión de fuentes y contratos · 2026-10-04

Revisión especializada de APIs, acceso y reglas. Solo se realizaron consultas públicas GET y lecturas de documentación oficial. Sin cuentas, credenciales, firmas, órdenes, instalaciones ni extracción de claves del frontend. Las muestras son observaciones fechadas, no precios actuales ni probabilidades de acierto. No se modificó la aplicación en esta revisión.

## Predict.fun / Binance Wallet

La [FAQ oficial de Binance Wallet](https://www.binance.com/en-IN/support/faq/detail/cfdb4d8b27b545119e66f68c54ef04ec) identifica Predict.fun como proveedor de sus mercados de predicción en BNB Chain. Binance Wallet es una capa de acceso; una cotización de Binance Spot no sustituye el contrato Predict. El catálogo del proveedor tampoco prueba que todos los mercados se muestren en una cuenta concreta de Binance Wallet.

### Acceso comprobado

| Consulta sin autenticación | Observación UTC | Resultado |
| --- | --- | --- |
| `https://api.predict.fun/v1/markets?first=1` | 2026-10-04T09:27:27.170456Z | HTTP 401, JSON de autorización |
| `https://api.predict.fun/v1/categories?first=1` | 2026-10-04T09:27:27.185525Z | HTTP 401, JSON de autorización |
| `https://api-testnet.predict.fun/v1/markets?first=1` | 2026-10-04T09:27:28.412313Z | HTTP 200, datos de TESTNET |

Extracto del error real de producción; identificadores de trazabilidad omitidos:

```json
{
  "success": false,
  "code": 401,
  "error": "unauthorized",
  "message": "authorization error",
  "timestamp": "2026-10-04T09:27:27.090431178Z"
}
```

La única consulta testnet devolvió `success: true`, cursor y un mercado de prueba con `id: 437`. Esto verifica la diferencia de acceso, no precios negociables ni disponibilidad de contratos cripto en producción. El adaptador de la aplicación debe usar exclusivamente producción.

La [documentación principal](https://dev.predict.fun/) confirma API key obligatoria en mainnet, cabecera `x-api-key`, y límite predeterminado de 240 consultas por minuto por clave. Testnet permite 240 por minuto sin clave. No se verificó una tarifa monetaria pública por acceso a la API. Sin configuración autorizada, el estado debe ser `NO_CONFIGURADO`; no repetir peticiones 401 por cada fila. Una clave de datos no requiere leer ni exponer una clave privada de una cartera.

### Rutas y parámetros documentados

Base de producción: `https://api.predict.fun`.

| Ruta GET | Uso | Fuente primaria |
| --- | --- | --- |
| `/v1/categories` | Descubrir categorías, ventanas y mercados anidados | [Get categories](https://dev.predict.fun/get-categories-25326910e0) |
| `/v1/categories/{slug}` | Detalle de una categoría conocida | [Get category by slug](https://dev.predict.fun/get-category-by-slug-25326911e0) |
| `/v1/markets` | Mercados paginados | [Get markets](https://dev.predict.fun/get-markets-25326905e0) |
| `/v1/markets/{id}` | Mercado individual | [Get market by ID](https://dev.predict.fun/get-market-by-id-25552989e0) |
| `/v1/markets/{id}/orderbook` | Libro del lado YES | [Get orderbook](https://dev.predict.fun/get-the-orderbook-for-a-market-25326908e0) |
| `/v1/tags` | Identificadores reales de etiquetas | [Get all tags](https://dev.predict.fun/get-all-tags-27399809e0) |

Los endpoints de producción de detalle/libro se revisaron en documentación; no se obtuvo un libro mainnet autenticado.

Parámetros de `GET /v1/categories`, según su OpenAPI público `.md`:

| Parámetro | Valores o formato |
| --- | --- |
| `first` | Cadena convertible a número; sin máximo ni valor predeterminado documentados |
| `after` | Cursor opaco devuelto por la página anterior |
| `status` | Enum del endpoint: `OPEN`, `RESOLVED` |
| `sort` | `VOLUME_24H_DESC`, `VOLUME_ALL_DESC`, `PUBLISHED_AT_ASC`, `PUBLISHED_AT_DESC`; predeterminado el último |
| `tagIds` | Valores separados por coma o parámetros repetidos; descubrir IDs, no inventarlos |
| `marketVariant` | `CRYPTO_UP_DOWN` está permitido |

Respuesta paginada: `{ "success": true, "cursor": "...", "data": [...] }`. Tratar el cursor como opaco, detener al faltar y protegerse de cursores repetidos. Un límite local de páginas es una decisión del adaptador, no una garantía de catálogo exhaustivo.

El esquema independiente [CategoryStatus](https://dev.predict.fun/categorystatus-14037462d0.md) enumera `OPEN`, `RESOLVED`, `REMOVED`; no existe `LIVE` en ese enum. [CategoryStatusFilter](https://dev.predict.fun/categorystatusfilter-14037463d0.md) añade `ACTIVE` y `REMOVED`, mientras el endpoint limita su parámetro a `OPEN`/`RESOLVED`. [CategorySort](https://dev.predict.fun/categorysort-14037459d0.md) también contiene `POPULAR` y `VOLUME`, ausentes del enum del endpoint. Conviene usar la intersección documentada: `status=OPEN`, `sort=PUBLISHED_AT_DESC`.

`GET /v1/markets` admite `first`, `after`, `status=OPEN|RESOLVED`, `tagIds`, `marketVariant`, `hasActiveRewards` y `sort`. `isBoosted` está deprecado. Los órdenes de mercado incluyen `CHANCE_24H_CHANGE_ASC|DESC`, `VOLUME_24H_ASC|DESC`, `VOLUME_24H_CHANGE_ASC|DESC`, `VOLUME_TOTAL_ASC|DESC` y `REWARD_RATE_ASC|DESC`; sin `sort`, usa prioridades internas.

### Campos para un parser conservador

La ventana pertenece a la **categoría**: `startsAt`, `endsAt`. `createdAt` y `publishedAt` no son sustitutos. Unir el mercado usando `market.categorySlug == category.slug`. Rechazar o dejar sin verificar una ventana incompleta, duración distinta de 300/900/3600 segundos, categoría invisible o estado no abierto.

Campos de categoría: `id`, `slug`, `title`, `shortTitle`, `description`, `status`, `isVisible`, `marketVariant`, `startsAt`, `endsAt`, `resolutionProvider`, `markets`. [CryptoCategoryDetails](https://dev.predict.fun/cryptocategorydetails-16921710d0) aporta `variantDetails.crypto.{priceFeedProvider,priceFeedId,priceFeedSymbol,startPrice,endPrice}`. `variantData` de categoría está deprecado en favor de `variantDetails`.

El [esquema Market](https://dev.predict.fun/market-14037477d0) aporta `id`, `categorySlug`, `title`, `question`, `description`, `tradingStatus`, `status`, `isVisible`, `feeRateBps`, `decimalPrecision`, `conditionId`, `oracleQuestionId`, `resolverAddress`, `outcomes`, `resolution`, `marketVariant`, `variantData` y `variantDetails`. Su ejemplo no incluye el inicio/fin de la ventana. El [esquema cripto](https://dev.predict.fun/cryptoupdownvariantdata-14037469d0) contiene `priceFeedProvider`, `priceFeedId`, `priceFeedSymbol`, `startPrice`, `endPrice`; el ejemplo genérico usa `PYTH`, lo cual no demuestra el oráculo del contrato actual.

[MarketTradingStatus](https://dev.predict.fun/markettradingstatus-14037484d0.md): `OPEN`, `MATCHING_NOT_ENABLED`, `CANCEL_ONLY`, `CLOSED`. [MarketStatus](https://dev.predict.fun/marketstatus-14037482d0.md): `REGISTERED`, `PRICE_PROPOSED`, `PRICE_DISPUTED`, `PAUSED`, `UNPAUSED`, `RESOLVED`, `REMOVED`. Para una fila negociable se necesita `tradingStatus=OPEN`; `status=OPEN` no es el estado de ciclo de vida de Market.

[Outcome](https://dev.predict.fun/outcome-14037514d0) contiene `name`, `indexSet`, `onChainId`, `status`, `bestBid.{price,size}`, `bestAsk.{price,size}`. No asumir que un nombre arbitrario o el primer resultado equivale a UP. Verificar la dirección contra la pregunta y reglas efectivas; un identificador de resultado no es un porcentaje de acierto.

### Libro y WebSocket

Estructura documentada de respuesta REST; los números/identificadores que siguen son ejemplos de forma, **no una cotización obtenida**:

```json
{
  "success": true,
  "data": {
    "marketId": 123,
    "updateTimestampMs": 1736696400000,
    "lastOrderSettled": null,
    "asks": [[0.62, 1500.0]],
    "bids": [[0.61, 2000.0]]
  }
}
```

[OrderbookData](https://dev.predict.fun/orderbookdata-14037511d0.md) y el endpoint especifican niveles `[price, size]`: precio YES de 0 a 1, tamaño en participaciones. `asks` comienza por la venta más barata; `bids`, por la compra más cara. `lastOrderSettled` puede ser `null`; si existe, contiene `{id:string,price:string,kind:string,marketId:number,side:"Ask"|"Bid",outcome:"Yes"|"No"}`. La fecha `updateTimestampMs` es epoch en milisegundos; separarla de la hora en que recibió datos el servidor del observatorio. `feeRateBps` está en Market, no en este libro.

Con correspondencia YES/UP verificada: `ask(NO)=1-bid(YES)` y `bid(NO)=1-ask(YES)`. Conservar la precisión de `decimalPrecision`, no convertir el midpoint en coste ejecutable y no inventar niveles cuando un lado está vacío. Fuente: [Understanding the Orderbook](https://dev.predict.fun/understanding-the-orderbook-685654m0).

[WebSocket oficial](https://dev.predict.fun/general-information-1915499m0): `wss://ws.predict.fun/ws`, TLS, API key en la cabecera de handshake `x-api-key` (preferida) o parámetro `apiKey`. No se probó una conexión autenticada. No se verificó una cuota numérica específica de WebSocket.

La [suscripción](https://dev.predict.fun/subscription-topics-1915507m0) admite `predictOrderbook/{marketId}`, `predictTradingStatus/{marketId}`, `predictMarketStatus/{marketId}`, `predictMarketChanged/{marketId}` y `predictCategoryChanged/{categoryId}`; una por petición. Mensaje: `{"method":"subscribe","requestId":1,"params":["predictOrderbook/123"]}`. El snapshot es de mejor esfuerzo. El libro WS añade `version`, `orderCount`, `settlementsPending` a los niveles y timestamps. [Heartbeats](https://dev.predict.fun/heartbeats-1915508m0): cada 15 segundos, responder `{"method":"heartbeat","data":<mismo timestamp>}`; reconectar con backoff y volver a suscribirse.

### Catálogo y reglas observadas

El [catálogo cripto público de Predict](https://predict.fun/markets/crypto), consultado el 4 de octubre, mostraba BTC, ETH y BNB con 5m, 15m y 1h. No se verificaron contratos SOL/XRP/DOGE: deben permanecer como seguimiento sin mercado verificado. La página web puede estar cacheada; etiquetas «Live» y porcentajes web no equivalen a un feed con fecha comprobada.

| Activo | 5m | 15m | 1h | Nivel de evidencia |
| --- | --- | --- | --- | --- |
| BTC | Visible | Visible | Visible | Catálogo público; reglas 5m y ejemplo 15m leídas |
| ETH | Visible | Visible | Visible | Catálogo público; reglas de un 5m leído |
| BNB | Visible | Visible | Visible | Catálogo público; reglas de un 5m leído |
| SOL / XRP / DOGE | No verificado | No verificado | No verificado | Sin catálogo mainnet autenticado |

Ejemplos primarios: [BTC 5m](https://predict.fun/market/btc-updown-5m-1791104100), [BTC 15m](https://predict.fun/market/btc-updown-15m-1791042300), [ETH 5m](https://predict.fun/market/eth-updown-5m-1791064800), [BNB 5m](https://predict.fun/market/bnb-updown-5m). Los contratos leídos resuelven UP si final > inicial, DOWN si final < inicial, y empate 50/50. Usan Chainlink `{ASSET}/USDT` Top of Book, basado en mid bid/ask de Binance; el precio final corresponde al cierre de la vela de 5 minutos anterior al fin. No extender esta regla a un contrato 1h sin leerlo. La coincidencia del activo y duración no garantiza equivalencia entre venues.

### Costes Predict

[Tarifas oficiales](https://docs.predict.fun/the-basics/predict-fees-and-limits): maker sin comisión; taker variable, base de ejemplo 2%, mínimo 1 USDT. Fórmula publicada: `fee = baseRate × min(p,1-p) × shares`. Leer `market.feeRateBps/10000` para la base del mercado, no fijarla en 200 universalmente. El descuento del 10% solo se aplica si está efectivamente activo. Ejemplo documental: 100 participaciones a 0.50, base 0.02, comisión 1 USDT antes de descuentos. Los costes de proveedor, spread y tamaño ejecutable siguen separados. El patrocinio de gas de Binance Wallet no significa que la comisión del contrato sea cero.

## Polymarket: descubrimiento 1h y cambio de oráculo

Se probaron seis GET públicos exactos el 2026-10-04 entre `09:28:37.945Z` y `09:28:38.062Z`, todos HTTP 200:

| Activo | URL Gamma exacta | Event ID | Market ID |
| --- | --- | --- | --- |
| BTC | `https://gamma-api.polymarket.com/events/slug/bitcoin-up-or-down-october-4-2026-5am-et` | 1118275 | 5200934 |
| ETH | `https://gamma-api.polymarket.com/events/slug/ethereum-up-or-down-october-4-2026-5am-et` | 1118276 | 5200935 |
| SOL | `https://gamma-api.polymarket.com/events/slug/solana-up-or-down-october-4-2026-5am-et` | 1118277 | 5200936 |
| XRP | `https://gamma-api.polymarket.com/events/slug/xrp-up-or-down-october-4-2026-5am-et` | 1118278 | 5200937 |
| DOGE | `https://gamma-api.polymarket.com/events/slug/dogecoin-up-or-down-october-4-2026-5am-et` | 1118279 | 5200938 |
| BNB | `https://gamma-api.polymarket.com/events/slug/bnb-up-or-down-october-4-2026-5am-et` | 1118281 | 5200940 |

Extracto de campos reales del BTC de esa consulta:

```json
{
  "id": "5200934",
  "eventStartTime": "2026-10-04T09:00:00Z",
  "endDate": "2026-10-04T10:00:00Z",
  "startDate": "2026-10-02T09:00:06Z",
  "closed": false,
  "outcomes": "[\"Up\",\"Down\"]",
  "resolutionSource": "https://www.binance.com/en/trade/BTC_USDT",
  "priceToBeat": null,
  "feesEnabled": true,
  "feeType": "crypto_fees_v2",
  "feeSchedule": {"exponent":1,"rate":0.07,"takerOnly":true,"rebateRate":0.2}
}
```

Las seis ventanas fueron `09:00:00Z`–`10:00:00Z`, equivalente a 5–6 AM en `America/New_York` ese día. `startDate` es creación/apertura del mercado, dos días antes; no usarlo para deducir la duración. La slug contiene **año** y hora de Nueva York, con DST: es una candidata de descubrimiento que debe verificarse en la respuesta, no una garantía de que existe. Validar slug, activo, `eventStartTime`, `endDate`, resultados, estado y regla. La [página hourly](https://polymarket.com/crypto/hourly) mostró enlaces cacheados a la ventana anterior; su primer enlace no es necesariamente el contrato actual.

Las reglas de estos 1h, confirmadas en Gamma y en el [contrato oficial BTC](https://polymarket.com/event/bitcoin-up-or-down-october-4-2026-5am-et), usan la vela **Binance Spot `{ASSET}/USDT` de 1 hora**: UP si cierre >= apertura; DOWN en otro caso, cuando la vela queda finalizada. No es Chainlink USD TWAP. Si Gamma no entrega el objetivo, no usar un spot arbitrario como apertura contractual; obtener y etiquetar el open de esa vela exacta o dejar el objetivo sin verificar.

Se comprobaron además dos BTC actuales a `09:35:30Z`, HTTP 200:

| Ruta pública Gamma | Market ID | Ventana UTC | Oráculo devuelto |
| --- | --- | --- | --- |
| `/events/slug/btc-updown-5m-1791106500` | 5228336 | 09:35–09:40 | `https://data.chain.link/streams/btc-usd-twap-60s-streams` |
| `/events/slug/btc-updown-15m-1791106200` | 5228290 | 09:30–09:45 | Misma fuente BTC/USD TWAP de Chainlink |

Estos 5/15m usan el TWAP contractual de Chainlink BTC/USD frente al precio inicial y UP incluye igualdad. No extrapolar a 1h. Leer siempre `description`/`resolutionSource` del contrato y sus actualizaciones; las fuentes cambian.

## Polymarket: fee-rate público y curva vigente

A `09:32:45Z`, Gamma BTC 1h devolvió el `feeSchedule` anterior. Se consultaron ambos tokens públicos a `09:32:48Z`:

```text
GET https://clob.polymarket.com/fee-rate?token_id=97816281538669691961797734138610519066561895399688067544756742470253142977648
HTTP 200 {"base_fee":1000}

GET https://clob.polymarket.com/fee-rate?token_id=79126138467702556562013480346869105935368928608060609156055302350744924694822
HTTP 200 {"base_fee":1000}

GET https://clob.polymarket.com/clob-markets/0x66e17f6498600c6d602304b76ce077c050326541481970c32e0cc84ecbbe8a57
HTTP 200
```

Extracto real del último cuerpo, observado a `2026-10-04T09:32:48.755774Z`:

```json
{
  "c": "0x66e17f6498600c6d602304b76ce077c050326541481970c32e0cc84ecbbe8a57",
  "mbf": 1000,
  "tbf": 1000,
  "ao": true,
  "fd": {"r":0.07,"e":1,"to":true},
  "v": "v1"
}
```

`base_fee:1000` no identifica la tasa real de esta curva; no convertirlo sin más en comisión del 10%. Los [detalles oficiales de mercado](https://docs.polymarket.com/market-data/market-details) documentan `feesEnabled` y `feeSchedule.{rate,exponent,takerOnly,rebateRate}`. Usar esa configuración o contrastarla con `fd` del CLOB; si falta, marcar coste desconocido.

La [página oficial de tarifas vigente](https://docs.polymarket.com/trading/fees) publica `fee = C × feeRate × p × (1-p)`; cripto `feeRate=0.07`, solo taker, maker cero. La curva obtenida tiene exponente 1. Ejemplo: 100 participaciones a 0.50 cuestan 50 antes de comisión y tienen comisión 1.75, equivalente al 3.5% del importe. Sumar costes por nivel de ejecución, no calcular sobre un precio inicial si la orden recorre varios niveles; no descontar rebates potenciales como ingreso garantizado.

## Equivalencia al comparar UP

| Venue / contrato comprobado | Referencia | Igualdad |
| --- | --- | --- |
| Polymarket BTC 5/15m del 4-oct | Chainlink BTC/USD TWAP contractual | UP |
| Polymarket seis activos 1h del 4-oct | Apertura/cierre de vela Binance `{ASSET}/USDT` 1H | UP |
| Predict BTC/ETH/BNB 5m y BTC 15m leídos | Chainlink `{ASSET}/USDT` Top of Book; final de vela 5m | 50/50 |

La comparación requiere el mismo evento: ventanas exactas, moneda de cotización, fuente, estadístico de resolución, objetivo, regla de empate y versión de las reglas. Con fuentes distintas, son referencias paralelas; no restar sus precios como si fueran arbitraje del mismo contrato. Separar cuota implícita, ask ejecutable y estimación estadística calibrada. Un porcentaje del libro no prueba una tasa de acierto del observatorio.

La revisión previa del 3 de octubre sobre Coinbase/Kalshi y Trust queda en [SOURCE_REVIEW.md](SOURCE_REVIEW.md); no se volvieron a consultar cuentas o datos privados de esos servicios en esta ampliación.
