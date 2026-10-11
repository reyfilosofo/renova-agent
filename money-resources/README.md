---
title: "MONEY Ω — Descubrimiento de recursos"
type: proyecto
project: MONEY
status: activo
version: "0.3.0"
created: 2026-10-11
updated: 2026-10-11
tags: [money, recursos, discovery]
---

# MONEY Ω — Descubrimiento de recursos

Este riel busca oportunidades públicas y conserva evidencia verificable. La primera ejecución real del 11-Oct leyó 10 fuentes oficiales y produjo **17 pistas: 10 programas de bounty de Immunefi y 7 páginas de programas/catálogos**. Ninguna acredita todavía elegibilidad personal, EV neto o ingresos recibidos. Todas quedan para observación; hay cero acciones en cola y los importes desconocidos permanecen null.

El [panel estático](index.html) lee únicamente el [reporte público](data/latest.json). Su fecha corresponde al momento real del reporte: una página accesible o un refresco de pantalla no convierte datos viejos en datos actuales. El estado de despliegue y activación remota permanece **PENDING** hasta verificar un run exitoso de GitHub Actions y la publicación real del panel.

## Fuentes y alcance

El [registro](../money-codex/config/resource_sources.json) contiene los catálogos de Code4rena, Immunefi, Zealy y Galxe; programas de participación de Prolific, User Interviews y Respondent; y consultas públicas de issues con label bounty en renova-agent y el repositorio oficial de Algora. Las dos consultas GitHub devolvieron cero candidatos. Code4rena publica ahora concursos cerrados: se conserva su página de catálogo sin inventar una bounty activa.

Los enlaces de Immunefi identifican programas listados. Su máximo premio no representa recompensa esperada ni probabilidad de cobrar. Una página de registro a estudios tampoco demuestra que exista una tarea disponible para la ubicación, perfil o identidad del usuario. Los claims, airdrops y beneficios de wallets requieren fuentes oficiales específicas y comprobación de elegibilidad antes de incorporarlos como acciones.

No se presentan los challenges históricos de Algora como recursos vigentes: Turso dice que terminó, Prettier/TSPerf muestran ganadores y Golem conserva un anuncio sin año inequívoco. Los snapshots de claims del 6–7 de octubre necesitan revalidación y no se transforman automáticamente en oportunidades actuales.

## Funcionamiento

MONEY Ω · CODEX 0.3.0 usa GET públicos, evidencia con timestamp/SHA256, SQLite, jobs con leases, deduplicación, conciliación de observaciones y ledger. La [definición del workflow](../.github/workflows/money-resource-discovery.yml) programa una búsqueda cada seis horas (`17 */6 * * *` UTC), permite ejecución manual y responde a cambios de código pertinentes. Su configuración queda separada de la prueba de activación; GitHub puede demorar un job y no garantiza exactamente el minuto previsto.

Para ejecutar un scan desde una copia de este repositorio:

```bash
cd money-codex
MONEY_EXECUTION_MODE=READ_ONLY python run.py scan --state-dir /tmp/money-resources --config config/resource_sources.json
python run.py status --state-dir /tmp/money-resources
```

Para el dashboard y scheduler locales:

```bash
MONEY_EXECUTION_MODE=READ_ONLY python run.py serve --state-dir /tmp/money-resources --config config/resource_sources.json --host 127.0.0.1 --port 8787
```

La instancia local vive mientras su proceso y host estén activos. El workflow remoto y el panel publicado requieren sus propias verificaciones. El nuevo scanner mantiene un store separado y no escribe el archivo del market collector AppDeploy.

## EV y acciones

EV_NET = recompensa × probabilidad de recibirla − gas − fees − gasto requerido − pérdida esperada − tiempo − coste de capital bloqueado − coste de riesgo de seguridad.

Si falta un término, el resultado es DATA INSUFFICIENT; no se sustituye con cero. WATCH señala una pista observada, no una autorización. Para una revisión posterior se necesitan condiciones, deadline, geography/KYC, eligibility, ToS, acciones, costes y riesgo verificados. El runtime no coloca órdenes, firma wallets, hace claims ni responde encuestas en nombre del usuario. No inventa identidad ni respuestas personales.

Direct ChatGPT↔Codex y Grok Bot permanecen false hasta verificar endpoint, autenticación, permisos y round-trip. GitHub/Drive/packets son el bus documental y técnico; no constituyen una conexión automática de agentes.

## Estado y procedencia

Consulte el [estado fechado del sistema](../money-bridge/CURRENT_STATE_2026-10-11.json) y el [registro de decisión](../07_DECISION_LOG/2026-10-11_money_resource_engine.md). AppDeploy conserva el market collector por separado: la lectura de metadata del 11-Oct reporta cron deshabilitado por credits_exhausted y último run 8-Oct16:40:19Z, aunque el frontend figure READY.

El reporte público sólo contiene campos permitidos derivados de fuentes públicas. No publique la base de datos privada, conversaciones, cuentas, capturas, credenciales ni logs de sesión.
