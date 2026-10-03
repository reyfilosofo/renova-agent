---
title: "MONEY Ω Observatorio — plan de construcción"
type: decision
project: MONEY
status: activo
created: 2026-10-03
updated: 2026-10-03
version: 0.1.0
confidence: baja
---

# Alcance

Aplicación privada de consulta e investigación, sin apuestas, órdenes, autenticación de exchanges, wallets ni movimientos de fondos. BTC, ETH, SOL, XRP, DOGE y BNB son una watchlist, no una afirmación de disponibilidad en la cuenta del usuario. Proyecto MONEY Ω; Ω PREDICT es módulo interno. Estrategia nueva `MONEY_SPOT_ANALOG_V1_PAPER`; RENOVA_DESK_V0 queda intacta.

## Roles y plan

Inventario: protocolos en reyfilosofo/renova-agent/main y Operating Bridge en Drive. Investigador de APIs/repositorios; QA de modelo/seguridad; implementador/coordinador del panel. Implementar lectura de datos, modelo experimental y auditoría; probar; publicar owner-private; respaldar fuentes y decisión en rama separada de GitHub y archivo privado en Drive.

## Riesgos

- Pspot no es Pcontrato: fuentes, ventanas, referencias y empates diferentes.
- Polymarket actual usa Chainlink TWAP; Kalshi usa RTI/promedio según reglas concretas. Sin feed exacto no existe estimación independiente de contrato.
- Coinbase devolvió HTML en vez de JSON en comprobación; no afirmar conexión. Binance devolvió 451 geográfico: adaptador detenido, sin reintentos ni evasión. Usar Kraken USD como otra fuente pública identificada, nunca sustitución silenciosa.
- La muestra inicial corta y los análogos dependientes no acreditan calibración ni rentabilidad. calibrated=false siempre en V1.
- Solo registros emitidos previamente son pronósticos prospectivos. El backtest es evaluación retrospectiva temporal, no historial real de operaciones.
- Actualización de pantalla abierta no equivale a proceso 24/7. No prometer recolección con la página cerrada ni copia automática de conversaciones invisibles.
- El repositorio canónico es público: respaldar solo código y documentación técnica sanitizada; nunca posiciones, captura, balances, conversaciones íntegras ni credenciales.

## Archivos y aceptación

app/page.tsx, app/globals.css, app/layout.tsx, app/api/*, lib/model.mjs, lib/market-data.mjs, lib/persistence.ts, db/schema.ts, migraciones Drizzle, tests y docs. Reutilizar infraestructura Sites sin añadir dependencias permanentes. Pruebas de datos futuros/abiertos, gaps, empate, separación spot/contrato, caducidad y errores de fuentes; typecheck/build; publicar fuente exacta. QA visual no disponible porque falta control-browser en entorno gestionado: no improvisar navegador.

## Fuentes internas

AGENTS.md, omega-predict/MASTER_PROTOCOL.md (sha3ede3b25b69011574b2ef4b8ce428c6e91859ab8), money-bridge/README.md, money-bridge/SECURITY.md y Drive Operating Bridge v1.0. La nomenclatura legacy no cambia la identidad MONEY Ω.
