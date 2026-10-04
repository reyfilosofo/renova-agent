---
title: MONEY Ω — Comparador sincronizado y calendario diario
type: proyecto
project: MONEY
version: 0.2.0
created: 2026-10-04
status: activo
confidence: media
---

# Plan de ampliación

## Alcance y aceptación

Ampliar el mismo sitio privado con una matriz de seis activos ×5/15/60min y columnas independientes Polymarket, Predict.fun y Kalshi. Mostrar UP/DOWN bid, ask, midpoint, fuente/recibido, ventana, referencia y condiciones. Comparar solo valores del mismo tipo, sin normalizar asks a100%, sin declarar un porcentaje «original» ni arbitraje. Caducidad y reglas incompletas impiden comparación económica.

Calendario prospectivo diario CDMX con24/96/288ventanas según horizonte, seis activos, primera emisión alineada guardada y desenlace posterior. Las ventanas futuras mantienen datos vacíos; no copiar probabilidades actuales al futuro. No falsear24pronósticos válidos con720velas5m. ExportarCSV/JSON. Vista instantánea se actualiza mientras está visible; recolección desatendida solo por mecanismo soportado y verificado, con límites de programación explícitos.

## Restricciones

Sin apuestas, wallets, órdenes, firma o capital. RENOVA_DESK_V0 y modelos0.1.0 permanecen separados. No evadir451Binance ni401Predict. ClavePredict solo como secreto de servidor, nunca frontend/repositorios/documentos. Sin clave mostrar NO CONFIGURADO, no testnet. BNB/SOL/XRP/DOGE u horizontes no verificados en cada venue quedan vacíos. Trust/MetaMask/BinanceWallet se presentan como vías de acceso con proveedores y costes propios, no votos independientes.

## Roles y riesgos

Root: implementación, publicación, respaldo; api_research: fuentes y catálogo; model_review: comparabilidad y QA. Coordinación requerida por AGENTS canónico.

Riesgos principales: referenciaUSD vsUSDT;TWAPvsvela;empateUPvs50/50;horaET/CDMX/DST;año omitido en slughourly;desfase/asof;snapshotviejo;rate limits;historia insuficiente;costeAPI no equivale a coste final de wallet. El payload preserva incertidumbres. Nunca usa porcentajes experimentales spot para Pcontract.

## Archivos afectados

lib/market-data.mjs; nuevos lib/comparison.mjs,lib/predict.mjs,lib/daily-plan.mjs,lib/market-matrix.ts; app/api/matrix,app/api/daily,app/api/collect; componentes cliente de matriz/calendario;lib/persistence.ts;db/schema.ts y nueva migración aditiva;page/css/README/documentación. Migraciones aplicadas previas inmutables.

## Validación

Pruebas de ventanasUTC/DST/CDMX,bookcomplement,asks no normalizadas,pendingkey,datosviejos/comparabilidad,paginación/catalogue conservador,calendario sinfuturos inventados,insert-once. Typecheck ybuild. HTTPhostmedianteaccesoSitesprivadosincredencialespersistidas; leerregistrotrascollector. No QAvisual con navegador si control-browser soportado falta. Respaldos GitHub técnicos públicos y Drive privados, verificados.
