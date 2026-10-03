# MONEY Ω · Observatorio v0.1.0

Aplicación privada de investigación para BTC, ETH, SOL, XRP, DOGE y BNB. Separa la estimación experimental **spot** de las probabilidades **de mercado** de contratos Polymarket/Kalshi. Ninguna apuesta, wallet, orden, transferencia, secreto o acceso a cuenta de exchange.

## Estado de la primera entrega

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
node --test tests/model.test.mjs
npx tsc --noEmit
npm run build
```

Para otro despliegue no reutilizar identidad Sites. Declarar `d1: "DB"`, aplicar migracionesDrizzle y usar el flujo Sites soportado. No editar tablas en request handlers ni modificar migraciones ya aplicadas. No guardar credenciales en fuente ni compartir el espacio privado públicamente.

QA incluye velasfuturas/abiertas, deduplicación/gaps, OHLC inválido, plana, caducidad, abstención, books, geobloqueo/HTML, ventanaKalshi vssettlement, insert-once y no habilitación de contratos. No hay prueba visual con navegador: control-browser no disponible en el entorno gestionado. Build/typecheck no demuestran acceso a cuentas ni calidad predictiva.

La comprobación HTTP inicial del host detectó que Workers no implementa `redirect: error`. Se corrigió a `manual` con rechazo explícito de respuestas3xx, sin seguir destinos ni debilitar la lista de hosts. Prueba de regresión incluida.

## Fuentes y respaldo

GitHub canónico reyfilosofo/renova-agent/main: AGENTS.md, omega-predict/MASTER_PROTOCOL.md, money-bridge/README.md y SECURITY.md. DriveOperatingBridge v1.0 es documental; usa nomenclatura legacy. Código de esta entrega respaldado en rama separada: no modificar main ni estrategias existentes.

La continuidad documenta conversaciones visibles y antecedentes recuperados, **no exporta todas las conversaciones de ChatGPT ni instala memoria global automática**. GitHub público recibe solo documentación técnica y código sanitizado. Drive privado recibe paquete/documentación de esta entrega.

Ver docs/SOURCE_REVIEW.md, docs/BUILD_PLAN.md y docs/DECISION_2026-10-03.md.
