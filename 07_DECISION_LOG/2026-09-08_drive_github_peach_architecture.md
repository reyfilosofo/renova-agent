---
title: "Decisión — arquitectura Google Drive + GitHub + Peach"
type: decision
project: META
status: aprobado
author: "Carlos Jonathan González Rodríguez"
created: 2026-09-08
updated: 2026-09-08
tags: [decision, connectors, ai-ops, centro]
confidence: alta
---

# Decisión — arquitectura Google Drive + GitHub + Peach

## Contexto

Se dispone de conexiones operativas de GitHub, Google Drive y Peach for WhatsApp Business dentro de ChatGPT. El repositorio `reyfilosofo/renova-agent` ya funciona como SERESARTE_BRAIN y es público; Google Drive contiene el corpus documental y binario; Peach conecta WhatsApp Business.

## Decisión

Adoptar una arquitectura de separación estricta:

- **Drive**: sistema maestro para documentos, masters, binarios y datos privados.
- **GitHub**: sistema de versión para código, Markdown, reglas, decisiones y automatizaciones no sensibles.
- **Peach**: canal de mensajería y operación de WhatsApp, sin replicar datos privados al repositorio.
- **ChatGPT/CENTRO**: orquestador que consulta la fuente adecuada y ejecuta acciones verificables.

Se crea en Drive la raíz `SERESARTE_BRAIN — AI OPS 2026`, replicando la taxonomía principal del repositorio e incorporando `10_WHATSAPP_OPS`.

## Razones

1. Evitar duplicar innecesariamente archivos y conversaciones.
2. Mantener GitHub apto para ser público.
3. Preservar archivos de alta resolución y documentación privada en Drive.
4. Permitir automatización futura sin mezclar secretos con código.
5. Mantener trazabilidad de decisiones y cambios.

## Riesgos mitigados

- filtración de PII por commits;
- publicación accidental de conversaciones;
- exposición de OTP/tokens;
- divergencia entre masters y copias;
- automatización de mensajes sin contexto;
- confusión entre enlaces de pago y pagos confirmados.

## Implementación inicial

- Creada estructura canónica en Drive.
- Documentada arquitectura en `09_META/CONNECTOR_ARCHITECTURE.md`.
- Creado protocolo `10_WHATSAPP_OPS/README.md`.
- Endurecido `.gitignore` para excluir exports y caches privados de conectores.

## Regla de revisión

Revisar esta decisión antes de:

- activar agentes autónomos 24/7;
- incorporar un CRM nuevo;
- hacer sync automático de Drive a GitHub;
- exportar conversaciones;
- convertir el repositorio a privado o dividirlo en varios repositorios.
