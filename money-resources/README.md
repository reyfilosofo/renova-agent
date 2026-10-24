---
title: "MONEY Ω — Descubrimiento de recursos"
type: proyecto
project: MONEY
status: activo
version: "0.4.0"
created: 2026-10-11
updated: 2026-10-24
tags: [money, recursos, discovery]
---

# MONEY Ω — Descubrimiento de recursos

Este riel busca oportunidades públicas y conserva evidencia verificable. La primera ejecución real del 11-Oct leyó 10 fuentes oficiales y produjo **17 pistas: 10 programas de bounty de Immunefi y 7 páginas de programas/catálogos**. Ninguna acredita todavía elegibilidad personal, EV neto o ingresos recibidos. Todas quedan para observación; hay cero acciones en cola y los importes desconocidos permanecen null.

El [panel estático](index.html) lee únicamente el [reporte público](data/latest.json). Su fecha corresponde al momento real del reporte: una página accesible o un refresco de pantalla no convierte datos viejos en datos actuales. El [panel alojado en Sites](https://money-omega-recursos.seresarte.chatgpt.site) está publicado de forma privada para el propietario, con recibo SUCCEEDED del 11-Oct17:35:08.055005Z. El workflow GitHub está activo y [su primera ejecución de producción](https://github.com/reyfilosofo/renova-agent/actions/runs/38160287636) completó los jobs test y discover con SUCCESS a las 17:35:53Z. El reporte resultante, generado a las 17:35:47.468176Z, vuelve a observar 10 fuentes y 17 pistas, con integridad de ledger verificada e ingresos recibidos desconocidos. El ID de hosting de Sites no identifica un proyecto Codex y el sitio no tiene MCP.

## Fuentes y alcance

El [registro](../money-codex/config/resource_sources.json) contiene los catálogos de Code4rena, Immunefi, Zealy y Galxe; programas de participación de Prolific, User Interviews y Respondent; y consultas públicas de issues con label bounty en renova-agent y el repositorio oficial de Algora. Las dos consultas GitHub devolvieron cero candidatos. Code4rena publica ahora concursos cerrados: se conserva su página de catálogo sin inventar una bounty activa.

Los enlaces de Immunefi identifican programas listados. Su máximo premio no representa recompensa esperada ni probabilidad de cobrar. Una página de registro a estudios tampoco demuestra que exista una tarea disponible para la ubicación, perfil o identidad del usuario. Los claims, airdrops y beneficios de wallets requieren fuentes oficiales específicas y comprobación de elegibilidad antes de incorporarlos como acciones.

No se presentan los challenges históricos de Algora como recursos vigentes: Turso dice que terminó, Prettier/TSPerf muestran ganadores y Golem conserva un anuncio sin año inequívoco. Los snapshots de claims del 6–7 de octubre necesitan revalidación y no se transforman automáticamente en oportunidades actuales.

## Funcionamiento

MONEY Ω · CODEX 0.3.0 usa GET públicos, evidencia con timestamp/SHA256, SQLite, jobs con leases, deduplicación, conciliación de observaciones y ledger. La [definición del workflow](../.github/workflows/money-resource-discovery.yml) programa una búsqueda cada seis horas (`17 */6 * * *` UTC), permite ejecución manual y responde a cambios de código pertinentes. La activación y primera ejecución remota están verificadas; GitHub puede demorar un job y no garantiza exactamente el minuto previsto. El código fue integrado por [PR55](https://github.com/reyfilosofo/renova-agent/pull/55) en el commit 822c90f7ccdcc763b24d521d9127bd44796aa21c. El primer reporte automático produjo el commit main fa09c8453467a31def3fe0c0bd6f731e1df94a09.

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

La instancia local y su healthcheck en http://127.0.0.1:8787 fueron verificados RUNNING el 11-Oct17:28:54Z (PID3152 en ese momento). Vive mientras su proceso y host estén activos; no es una garantía de uptime permanente. Los jobs remotos conservan evidencia en el artifact 11709839593 con retención de 90 días y vencimiento 2027-01-09. La restauración de caché es best effort: GitHub puede eliminarla y el estado del runner no es almacenamiento permanente. El nuevo scanner mantiene un store separado y no escribe el archivo del market collector AppDeploy.

## EV y acciones

EV_NET = recompensa × probabilidad de recibirla − gas − fees − gasto requerido − pérdida esperada − tiempo − coste de capital bloqueado − coste de riesgo de seguridad.

Si falta un término, el resultado es DATA INSUFFICIENT; no se sustituye con cero. WATCH señala una pista observada, no una autorización. Para una revisión posterior se necesitan condiciones, deadline, geography/KYC, eligibility, ToS, acciones, costes y riesgo verificados. El runtime no coloca órdenes, firma wallets, hace claims ni responde encuestas en nombre del usuario. No inventa identidad ni respuestas personales.

Direct ChatGPT↔Codex y Grok Bot permanecen false hasta verificar endpoint, autenticación, permisos y round-trip. GitHub/Drive/packets son el bus documental y técnico; no constituyen una conexión automática de agentes.

## Estado y procedencia

Consulte el [estado fechado del sistema](../money-bridge/CURRENT_STATE_2026-10-11.json) y el [registro de decisión](../07_DECISION_LOG/2026-10-11_money_resource_engine.md). AppDeploy conserva el market collector por separado: la lectura de metadata del 11-Oct reporta cron deshabilitado por credits_exhausted y último run 8-Oct16:40:19Z, aunque el frontend figure READY.

El reporte público sólo contiene campos permitidos derivados de fuentes públicas. No publique la base de datos privada, conversaciones, cuentas, capturas, credenciales ni logs de sesión.

## Verificación operativa del 12-Oct

El [estado actual verificado](../money-bridge/CURRENT_STATE_2026-10-12.json) registra tres ejecuciones programadas de recursos con SUCCESS. La más reciente terminó el 12-Oct15:22:24Z y publicó 17 candidatos de 10 fuentes, con ledger íntegro y ningún ingreso confirmado. El cron solicita una cadencia de seis horas; hubo demoras reales de GitHub y no se garantiza ese intervalo. El panel privado de Sites sigue activo para el propietario.

Una nueva lectura autenticada de AppDeploy el 12-Oct informa el collector de mercados habilitado y un run reciente exitoso. Esa observación supera el estado deshabilitado del 11-Oct; los incidentes históricos se preservan. Codex no cambió el cron ni compró créditos. El snapshot de la app devuelve datos actuales, pero una cuota PUBLICADO sin quoteAt verificado no es LIVE ni demuestra edge.

Los dos puentes de Drive tienen las adiciones operativas del 11-Oct y su lectura autenticada se verificó otra vez el 12-Oct. Eso acredita actualizaciones documentales, no un Drive writer continuo ni comunicación directa entre agentes.


## Actualización 0.4.0 — 20-Oct

La búsqueda ahora comprueba hasta diez páginas oficiales de detalle de Immunefi
por ejecución, con presupuesto de 110 segundos por fuente. Revisa identidad,
fechas y estado del programa. Un bloqueo, pausa o cierre se conserva como
incertidumbre o indisponibilidad; no se inventa una bounty activa. La ausencia
de un programa del conjunto acotado tampoco acredita su cierre.

El máximo premio anunciado aparece separado del valor esperado neto. Los diez
programas revisados mantienen pendientes la elegibilidad, la probabilidad de
cobro y los costes personales. El panel vuelve a evaluar fechas, advierte si
muestra el informe incluido en la publicación y evita presentar paquetes
importados como consultas propias verificadas.

El [monitor público de mercados](data/market-health.json) se ejecuta por separado.
Sólo observa health, snapshot 5m y el archivo BTC 5m del día CDMX. Cuenta
capturas reales y huecos sin fabricar datos históricos; no demuestra el estado
del cron ni cubre todos los archivos. La lectura autenticada del 20-Oct informa
cron habilitado y ejecución exitosa; el incidente del 19-Oct se preserva como
observación histórica. No se compraron créditos ni se modificó el cron.

La versión se verifica con 179 tests Python del módulo, seis pruebas del panel
y los dos tests raíz. Los resultados operativos y recibos de publicación
figuran en el estado fechado del 20-Oct y en el historial GitHub. Los datos de
fuentes cambian: consulte la fecha real de cada reporte.


La unificación del 24-Oct se implementa en el Site Observatorio existente, como MONEY Ω.
Este directorio conserva el feed público y las fuentes técnicas; no es un producto independiente.
Véase `../money-bridge/MONEY_OMEGA_SINGLE_SITE_MANIFEST.json`.
