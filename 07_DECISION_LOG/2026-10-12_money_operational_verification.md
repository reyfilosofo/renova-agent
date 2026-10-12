---
title: "MONEY Ω — Activación y verificación operativa"
type: decision
project: MONEY
status: aprobado
author: "MONEY Ω · CODEX; autorización del operador"
version: "1.0"
created: 2026-10-12
updated: 2026-10-12
tags: [money, recursos, runtime, verificacion]
related: [money-bridge/CURRENT_STATE_2026-10-12.json, money-resources/README.md]
confidence: alta
---

# MONEY Ω — Activación y verificación operativa

## Resumen ejecutivo

El Resource Engine 0.3.0 está integrado en main por PR55 y busca recursos reales
en fuentes públicas. Tres ejecuciones programadas posteriores a la activación
completaron los jobs de prueba y discovery con SUCCESS. La más reciente,
38269686527, terminó el 12-Oct15:22:24Z y conservó 17 candidatos de 10 fuentes.
No se acredita elegibilidad personal, EV neto calculable ni cobros.

## Desarrollo

El panel privado de Sites permanece activo para el propietario:
https://money-omega-recursos.seresarte.chatgpt.site . Consulta el reporte público
actualizado por Actions; tiene filtros y evidencia, sin rutas financieras.
El cron solicita cuatro ejecuciones diarias, pero se observaron demoras
materiales de GitHub. La caché es best effort; los artifacts duran 90 días.
No se presenta una sesión Codex como daemon permanente.

La lectura autenticada AppDeploy del 12-Oct supera la suspensión de créditos
observada el 11-Oct: el cron está habilitado, su run de 16:40:20Z fue exitoso y
failure_count=0. Codex no cambió el cron ni compró créditos. Chromium verificó
GET real al backend AppDeploy, health JSON y snapshot de seis activos con
asOf16:45:17.202Z. El archivo BTC5m registra 130 capturas de 288 ventanas,
última a16:45, y ninguna captura futura. PUBLICADO/quoteAt=null no es LIVE.
Predict y Coinbase/Kalshi mantienen sus estados no verificados cuando faltan
datos; la estrategia experimental conserva WAIT/Pcontract=null/calibrated=false.

Los dos puentes Drive conservaron sus versiones y recibieron adiciones
fechadas. Su readback autenticado se comprobó. Son escrituras documentales
puntuales, no sincronización permanente ni una conexión entre agentes.

## Relaciones conceptuales

Resource discovery, mercado experimental y ejecución financiera permanecen
separados. Los programas listados no son dinero recibido. La cuenta y los fills
no han sido consultados; ningún authorization object real ni adapter LIVE
aparece habilitado. Los project IDs pendientes no se deducen del ID de hosting.

## Decisiones

1. Registrar el estado actual en CURRENT_STATE_2026-10-12.json y preservar las
   observaciones e incidentes históricos del 8 y 11 de octubre.
2. Mantener una sola escritura automática del archivo de mercados en AppDeploy;
   los procesos locales usan su store separado y no rellenan historial remoto.
3. Habilitar el proxy nativo de Node en el arranque local con
   NODE_USE_ENV_PROXY=1, sin modificar la fuente original ni persistir secretos.
4. Publicar sólo metadatos operativos y datos públicos permitidos; evidencias
   privadas y bases de datos permanecen fuera de Git y del panel.

## Pendientes

Verificar elegibilidad, términos y costes antes de elevar una pista a acción;
revalidar datos de contratos antes de interpretar edge; conservar revisiones
independientes y mantener los controles financieros cerrados sin autoridad
estructurada. Claims/airdrops y otras categorías sin fuente configurada siguen
pendientes, sin inventar recursos disponibles.

## Fuentes internas

money-codex/, money-resources/, money-app/API.md y los estados fechados del
bridge. Pruebas: 104 tests del módulo, 25 de integridad y 9 locales de la app,
typecheck/build y 2 tests base del repositorio, aprobados. Los jobs remotos
posteriores confirman la operación del mismo código probado.

## Fuentes externas verificables

- https://github.com/reyfilosofo/renova-agent/pull/55
- https://github.com/reyfilosofo/renova-agent/actions/runs/38269686527
- https://money-z6epdn.v2.appdeploy.ai/
- https://money-omega-recursos.seresarte.chatgpt.site

## Verificación del arranque local

La corrección del proxy nativo de Node permitió obtener los seis spots USD.
El corte local automático de 16:50 UTC terminó a16:50:01.872Z y archivó los
seis activos; recursos conserva 17 WATCH y ledger íntegro. Los procesos se
reiniciaron conservando stores y sin cambiar la app original. Esto verifica
funcionamiento en el host actual, no uptime permanente del workspace.
