---
title: "MONEY Ω — unificación de los tres Sites existentes"
type: decision
project: MONEY
status: activo
version: "0.4.0"
author: "Carlos Jonathan González Rodríguez"
created: 2026-10-24
updated: 2026-10-24
tags: [money, sites, runtime, recursos, ingresos]
confidence: alta
---

# MONEY Ω — sitio único

## Decisión y alcance

Se ejecuta la instrucción del propietario de consolidar Observatorio, Earn Engine
y Recursos dentro de un único Site existente. Se reutiliza Observatorio
`appgprj_6ac169e9eed48191a46429c70adabaf7`, conservando su URL, audiencia pública
y binding D1. Recursos era privado; sólo su código e informe sanitizado público
se integran. No se crea un cuarto Site ni se trasladan datos privados al frontend.

## Inventario y respaldo previos

Se obtuvo acceso de propietario y fuente Git de los tres proyectos. Se conservaron
ZIP de fuente, inventarios con SHA-256 y commits originales en el archivo privado
de trabajo. Observatorio tiene cinco tablas D1 de mercados. Earn Engine usa
`moneyOmegaLog` en localStorage del navegador, sin base remota; ese estado no es
legible desde otro origen. Recursos sólo contiene una página estática y el informe
público. Ninguna base o registro original se elimina.

## Implementación y criterios

Una navegación incorpora Inicio, Earn Engine, Wallets/Rewards, Observatorio,
Recursos, Registro y Estado. La lista de oportunidades es común; no se conservan
los importes y scores de demostración de Earn Engine como datos reales. El EV
mantiene valores desconocidos vacíos y separa el máximo anunciado de una bounty.

El registro requiere identidad ChatGPT y queda segregado por usuario. Idempotencia,
importes decimales y evidencia DECLARADA evitan duplicaciones y cobros ficticios.
Los registros del navegador anterior requieren exportación/importación consentida;
una fecha desconocida se conserva desconocida. No se inventan pagos conciliados.

Mercados sigue PAPER. Se retiran las APIs Polymarket/Predict en favor de HTML
público. La lectura canónica AppDeploy se verifica por separado del frontend y del
cron; la falta de créditos no se resuelve comprando ni cambiando el plan. No hay
capturas retroactivas ni segundo collector automático. La lectura de respaldo,
cuando esté disponible, no se presenta como archivo histórico.

## Riesgos y comprobación

Se exige typecheck, tests del módulo/mercados/registro/reportes, build y recibo
nativo de publicación del commit exacto. No hay control-browser/js ni ruta preview
soportada en el entorno actual: no se atribuye una prueba visual nueva. La
verificación de sesión y registro D1 autenticado se distingue de un GET anónimo.
Los sitios anteriores sólo se sustituyen por accesos trasladados después de
publicar y leer la versión integrada; sus respaldos se conservan.

## Fuentes

- `money-bridge/MONEY_OMEGA_SINGLE_SITE_CONTRACT.md` y manifiesto del 23-Oct.
- `money-codex/`, `money-resources/`, `money-site/`.
- Metadatos Sites, lectura de fuente y overview D1 del 24-Oct.
- Scanner 24-Oct: diez fuentes, diez detalles Immunefi, 17 pistas, 20 evidencias.
- Operating Bridge v2.1; MONEY skill 1.1.0.


## Resultado verificado

El Site maestro se publicó con SUCCEEDED el 24-Oct16:31:27Z, versión5, en su URL
original. HTTP confirmó los siete módulos, matriz de 18 filas sin cotizaciones
LIVE, el archivo anterior legible y el registro privado protegido con 401 para
anónimos. D1 conserva cinco tablas de mercados y añade la sexta del registro.
La escritura autenticada por el usuario y el QA visual de navegador no se
realizaron. No se afirma una exportación completa de filas D1 previa al cambio.

Los dos accesos antiguos publicaron avisos de traslado con SUCCEEDED a las
16:33:47Z y16:33:58Z. El prototipo Earn conserva exportación de datos del
navegador y el maestro ofrece previsualización/importación consentida. Los tres
proyectos de hosting se conservan para recuperar fuentes; hay un solo producto.
Se aprobaron 179 tests Python,59 de Site,6 de panel,8 de adapter y2 raíz, además
de TypeScript/build y CI remoto. Ver recibos y límites en el estado fechado.

El plan30–90d se incorpora como flujos de servicios, empleo y producto autoral.
Metas y tarifas privadas no se publican ni se cuentan como ingresos. Los PDFs
adjuntos se inventariaron en archivo privado y no se subieron al sitio o Git.
