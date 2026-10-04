# MONEY Ω · Observatorio v0.2.0

Aplicación privada de investigación para BTC, ETH, SOL, XRP, DOGE y BNB. Separa la estimación experimental **spot** de las probabilidades **de mercado** de contratos Polymarket/Kalshi. Ninguna apuesta, wallet, orden, transferencia, secreto o acceso a cuenta de exchange.

## Ampliación v0.2 · 2026-10-04

La vista principal reúne18 ventanas: seis activos ×5/15/60min. Columnas independientes Polymarket, Predict.fun/Binance Wallet y Kalshi/referencia Coinbase Predictions. Selector ask/bid/midpoint, ambos outcomes, referencia exacta USD/USDT, inicio/fin CDMX y timestamps de libro/recepción. Ask es compra bruta por unidad, sujeta a tamaño y mínimos: UP/DOWN asks pueden sumar más de100%. Midpoint es indicador de mercado, no Pmodelo calibrada.

Delta midpointUP en puntos porcentuales descriptivo:70%−59%=11pp, sin porcentaje «original», edge ni arbitraje. Equivalencia exige referencia, ventana, oráculo/feed, estadístico, redondeo, comparador, empate, anulación, pago y versión de reglas completos/coincidentes. Frescura≤30s y dispersión entre cuatro timestamps/recepciones≤3s se verifican por separado. Datos viejos, incompletos o contratos distintos bloquean comparación económica.

Polymarket1h de los seis activos fue verificado el4 de octubre. Slugs con año y validación UTC real, incluso durante horaET repetida; `startDate` es creación y no inicio del evento. Contratos horarios revisados: BinanceUSDT/open-close1H, empateUP. Cortos revisados: ChainlinkUSD/TWAP60s. Objetivo exacto desconocido queda vacío. Kraken y Coinbase spot se verificaron en el host0.1; BNB-USD de Coinbase no verificado.

Predict Mainnet requiere `PREDICT_API_KEY` como secreto runtime del servidor. Adaptador oficial implementado, sin clave no realiza llamadas ni usa testnet. Descubre categoríasOPEN/CRYPTO_UP_DOWN, une porcategorySlug y valida outcomesUP/DOWN. Catálogo parcial no demuestra inexistencia. SOL/XRP/DOGE no se afirman disponibles sin respuesta oficial. NO se deriva complementando el bookYES validado. Clave solo enheaderHTTPS del host oficial, nunca URL/frontend/archivos/backup. Kalshi mantiene15m;5m/1h no verificados, `updated_time` no acredita frescura delbook y429 activa pausa60s.

Wallets MetaMask, Trust, Binance Wallet y Coinbase Wallet se presentan como rutas a proveedores. No son votos independientes ni se inventan cotizaciones directas. Coinbase Predictions es producto distinto, con referenciaKalshi. Coste: ask bruto, liquidez y subtotal indicativo Polymarket por unidad si se recibe tarifa compatible. Rate0.07/exponent1 usa `rate*p*(1-p)`, sin tratar `base_fee/10000` como coste plano. Fee desconocida permanece vacía. Gas/ruta/conversión/descuento/slippage/mínimos no se afirman incluidos. Coste final wallet/Predict pendiente de verificación.

Agenda `/api/daily?date=YYYY-MM-DD&horizon=60`:24 ventanasCDMX;15m96 y5m288. CSV compatible conExcel/JSON exportables. Primera emisión cuyo origen/objetivo coincide exactamente con la ventana, sin reconstruir pasado ni inventar precios futuros. Una estimación rodante60m09:05→10:05 no se coloca en09:00→10:00. Resultados contra la misma fuenteKraken no alteran probabilidad/referencia originales. Capturas insert-once por activo/horizonte/ventana/corte5m; agenda muestra la primera captura original, distinta de una cotización actual. Migraciones0001/0002 aditivas;0000 inmutable.

REST en página visible: precios10s, matriz15s, análisis al corte5m. Consulta agrupada no es streaming tick a tick. POST privado `/api/collect` emite un único corte público real de seis activos/18modelos y matriz bajo accesoSites; no recibe claves/instrucciones de trading. Debe probarse escritura y lectura posterior antes de programar. Recolección cerrada5/15m necesita un colector externo de esa frecuencia: tareas disponibles tienen límite horario. Una tarea horaria es parcial, no continuidad5/15m. Drive/GitHub respaldan entregas, no cada nuevo corte automático.

Modelo `MONEY_SPOT_ANALOG_V1_PAPER`0.1.0 permanece sin cambios, experimental, fuenteKraken y separado deRENOVA_DESK_V0. No puede usarse Pspot comoPcontrato ni convertir720velas5m en24 probabilidades futuras validadas.

QA inicial:32 pruebas aprobadas (modelo, UTC/CDMX/DST, books, clave Mainnet/redirect, costes desconocidos, agenda futura vacía, primera emisión y todas las migraciones). Typecheck/build/HTTP delhost y respaldos se registran en docs/DECISION_2026-10-04.md. Sin nuevas dependencias. No QAvisual con navegador sincontrol-browser soportado en entorno gestionado.

## Antecedentes de la primera entrega · 2026-10-03

- Panel responsive con seis activos,5/15/60min, precios, gráficos reales (si existe fuente válida), probabilidad spot condicionada a movimiento, medianas/bandas de precio, caducidad, reglas y bid/ask.
- REST público de Polymarket5/15m y Kalshi15m verificado en autoría. No afirmar disponibilidad en una cuenta Coinbase concreta.1h contractual no identificado en V1.
- Adaptadores de Coinbase spot y Kraken implementados. En este entorno de autoría devolvieron HTML en lugar de datos; no se fabrican conexiones. Comprobar estado efectivo en el host publicado.
- Binance devolvió451 geográfico: no hay adaptador activo ni evasión. Kraken USD es fuente/modelo separado, no BinanceUSDT ni el oráculo contractual.
- Trust Wallet: integración directa pendiente de configuración/autoridad; ningún AccessID/HMAC usado. Venues subyacentes no equivalen a una probabilidad Trust independiente.
- Actualización en página visible: quotes10s, mercados15s, análisis al corte de5min. **No streaming tick a tick ni recolección desatendida24/7.**
- Archivo persistente D1: registro insert-once, resultados posteriores contra la misma fuente, métricas por activo/horizonte. JSON exportable;25000registros máximo por descarga, flagtruncated cuando aplica. Drive/GitHub no reciben automáticamente cada corte.

## Modelo

`MONEY_SPOT_ANALOG_V1_PAPER`, nunca mezclado con `RENOVA_DESK_V0` ni estrategias LIVE. V0 queda congeladoBTC-USD/EMA12-26/1H/14días/PAPER.

VelasKrakenUSD5m cerradas, features trailing5/15/60m normalizadas por volatilidad.30análogos uniformes; mínimo40ventanas de entrenamiento y15análogos no planos. P=(UP+0.5)/(UP+DOWN+1), **condicional a movimiento**, empates separados. Percentiles10/50/90 describen retornos de los análogos; bandaWilson es aproximación de frecuencia bajo supuestos, no confianza/calibración demostrada.

Evaluación walk-forward de hasta80ventanas no solapadas por horizonte, entrenamiento anterior purgado un horizonte adicional. Brier frente a0.5 y frecuencia histórica, sin comparar evento spot con evento contractual. `calibrated=false`, `executionEnabled=false`, `contractProbability=null` siempre en V1. Ninguna métrica habilita automáticamente ejecución o edge.

## Pruebas y reproducción

Node24+; infraestructura Vinext/Sites conservada. Sin dependencias añadidas: dependencias existentes del starter para UI/build/persistencia; modelo y fuentes públicas usan JavaScript nativo.

```sh
npm run install:ci
node --test tests/model.test.mjs tests/comparison.test.mjs
npx tsc --noEmit
npm run build
```

Para otro despliegue no reutilizar identidad Sites. Declarar `d1: "DB"`, aplicar migracionesDrizzle y usar el flujo Sites soportado. No editar tablas en request handlers ni modificar migraciones ya aplicadas. No guardar credenciales en fuente ni compartir el espacio privado públicamente.

QA incluye velasfuturas/abiertas, deduplicación/gaps, OHLC inválido, plana, caducidad, abstención, books, geobloqueo/HTML, ventanaKalshi vssettlement, insert-once y no habilitación de contratos. No hay prueba visual con navegador: control-browser no disponible en el entorno gestionado. Build/typecheck no demuestran acceso a cuentas ni calidad predictiva.

La comprobación HTTP inicial del host detectó que Workers no implementa `redirect: error`. Se corrigió a `manual` con rechazo explícito de respuestas3xx, sin seguir destinos ni debilitar la lista de hosts. Prueba de regresión incluida.

## Fuentes y respaldo

GitHub canónico reyfilosofo/renova-agent/main: AGENTS.md, omega-predict/MASTER_PROTOCOL.md, money-bridge/README.md y SECURITY.md. DriveOperatingBridge v1.0 es documental; usa nomenclatura legacy. Código de esta entrega respaldado en rama separada: no modificar main ni estrategias existentes.

La continuidad documenta conversaciones visibles y antecedentes recuperados, **no exporta todas las conversaciones de ChatGPT ni instala memoria global automática**. GitHub público recibe solo documentación técnica y código sanitizado. Drive privado recibe paquete/documentación de esta entrega.

Ver docs/SOURCE_REVIEW_2026-10-04.md, docs/BUILD_PLAN_2026-10-04.md y docs/DECISION_2026-10-04.md. Las decisiones de0.1 se conservan como antecedentes.
