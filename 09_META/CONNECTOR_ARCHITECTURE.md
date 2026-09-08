---
title: "Arquitectura de conectores — Google Drive + GitHub + Peach"
type: decision
project: META
status: aprobado
author: "Carlos Jonathan González Rodríguez"
created: 2026-09-08
updated: 2026-09-08
tags: [ai-ops, github, google-drive, whatsapp, peach, centro]
confidence: alta
---

# Arquitectura de conectores — SERESARTE_BRAIN / CENTRO

## Objetivo

Establecer una arquitectura operativa donde ChatGPT actúe como capa de orquestación entre tres sistemas con funciones separadas:

1. **Google Drive** — bóveda canónica de archivos, documentos, PDFs, imágenes, libros, contratos, materiales privados y activos binarios.
2. **GitHub (`reyfilosofo/renova-agent`)** — sistema de versión para código, Markdown, ontología operativa, reglas, decisiones, prompts, pruebas y automatizaciones no sensibles.
3. **Peach for WhatsApp Business** — canal transaccional de mensajería para leer, clasificar y responder conversaciones autorizadas de WhatsApp Business.

ChatGPT/CENTRO coordina los tres sistemas; ninguno sustituye al otro.

## Principio de separación de responsabilidades

### Google Drive = verdad documental y archivos privados

Guardar en Drive:
- PDF/DOCX/PPTX/XLSX y originales de alta resolución;
- masters editoriales y artbooks;
- contratos, expedientes y documentación privada;
- archivos de clientes;
- exportaciones temporales de mensajería cuando exista una necesidad legítima;
- entregables finales y material de producción.

No usar GitHub público como almacén de estos archivos salvo que un artefacto sea deliberadamente público y apto para versionado.

### GitHub = verdad operativa, código y trazabilidad

Guardar en GitHub:
- Markdown y documentación técnica no sensible;
- código, HTML, scripts y pruebas;
- taxonomías, ontologías y prompts reutilizables;
- decisiones de arquitectura;
- manifiestos y esquemas;
- automatizaciones que no contengan secretos ni datos privados.

El repositorio es público. Por tanto, está prohibido introducir:
- números telefónicos reales;
- conversaciones de WhatsApp;
- correos privados no publicados;
- códigos OTP;
- tokens, claves, cookies o credenciales;
- IDs privados cuando su publicación incremente riesgo;
- información financiera, médica, contractual o personal no destinada a publicación.

### Peach = canal de mensajería, no archivo histórico maestro

Usar Peach para:
- localizar conversaciones;
- detectar mensajes entrantes relevantes;
- preparar y enviar respuestas autorizadas;
- clasificar oportunidades, ventas, trabajo, soporte y seguimiento;
- operar WhatsApp Business desde ChatGPT cuando la ventana de mensajería y permisos lo permitan.

No copiar conversaciones completas a GitHub. Si una conversación genera una decisión relevante, registrar únicamente una **nota abstracta y minimizada** sin PII en GitHub, y mantener los datos fuente en el sistema privado correspondiente.

## Mapa de flujo

```text
                         ┌──────────────────────┐
                         │   ChatGPT / CENTRO   │
                         │  capa de orquestación│
                         └──────────┬───────────┘
                                    │
                 ┌──────────────────┼──────────────────┐
                 │                  │                  │
                 ▼                  ▼                  ▼
        ┌────────────────┐ ┌────────────────┐ ┌──────────────────┐
        │  Google Drive  │ │     GitHub     │ │ Peach / WhatsApp │
        │ archivos/canon │ │ código/version │ │ conversaciones    │
        └────────────────┘ └────────────────┘ └──────────────────┘
                 │                  │                  │
                 └──────────────┬───┴───────┬──────────┘
                                ▼           ▼
                          decisiones     acciones
                          verificables   autorizadas
```

## Taxonomía Drive ↔ GitHub

La carpeta Drive `SERESARTE_BRAIN — AI OPS 2026` replica la taxonomía de alto nivel del repositorio:

- `00_INBOX`
- `01_SERESARTE`
- `02_RENOVA`
- `03_DAO`
- `04_NOUS`
- `05_CLIENTES`
- `06_LIBROS`
- `07_DECISION_LOG`
- `07_PERSONAS`
- `08_OUTPUTS`
- `09_META`
- `10_WHATSAPP_OPS`

Regla: **misma semántica, distinto contenido**. GitHub contiene estructura versionable y no sensible; Drive contiene originales, binarios y documentación privada.

## Clasificación de datos

### P0 — Público
Puede vivir en GitHub público y Drive.
Ejemplos: manifiestos publicados, código abierto, documentación pública, páginas web.

### P1 — Interno
Preferencia Drive; GitHub sólo si está anonimizado y no expone estrategia confidencial.

### P2 — Confidencial
Sólo Drive u otro sistema privado autorizado. Nunca GitHub público.
Ejemplos: clientes, contratos, precios no publicados, propuestas privadas, conversaciones.

### P3 — Secreto / credencial
No almacenar en documentos normales. Usar secrets/env/gestores de credenciales. Nunca GitHub, nunca chats, nunca exportaciones ordinarias.
Ejemplos: API keys, OTP, tokens, passwords, cookies de sesión.

## Protocolo CENTRO

Para tareas que crucen sistemas:

1. **Descubrir** — localizar la fuente correcta antes de actuar.
2. **Clasificar** — determinar P0/P1/P2/P3.
3. **Leer mínimo necesario** — principio de minimización.
4. **Razonar** — separar hechos, inferencias y propuestas.
5. **Actuar** — realizar sólo los writes necesarios.
6. **Verificar** — leer de vuelta o comprobar estado de la operación.
7. **Registrar** — documentar decisiones estructurales en `07_DECISION_LOG/` sin PII.

## Reglas de WhatsApp

- Nunca reenviar OTP o códigos de verificación.
- No responder automáticamente a remitentes de verificación/sistema.
- Para envíos comerciales, comprobar intención, destinatario y contexto.
- No asumir que un link Stripe equivale a una venta confirmada.
- Mantener trazabilidad de ventas en el sistema financiero correspondiente, no en WhatsApp.
- No publicar nombres, teléfonos ni transcripciones en GitHub.

## Estrategia de sincronización

No crear una sincronización bidireccional indiscriminada. Usar **sincronización selectiva por eventos**:

- Drive → GitHub: únicamente especificaciones/texto apto para publicación o anonimizado.
- GitHub → Drive: releases, entregables o snapshots cuando sea útil para archivo.
- Peach → Drive: sólo resúmenes o artefactos necesarios y privados, nunca por defecto.
- Peach → GitHub: sólo decisiones abstractas y métricas agregadas sin PII.

## Criterios de aceptación

La arquitectura se considera correcta cuando:

- GitHub no contiene datos privados de conectores;
- Drive contiene el master documental y los binarios;
- Peach puede usarse como canal de WhatsApp sin convertirse en repositorio de secretos;
- toda acción crítica es verificable;
- las decisiones estructurales quedan registradas;
- la automatización futura sigue el principio de privilegio mínimo.

## Próxima fase

1. Indexar los masters actuales de Drive sin moverlos automáticamente.
2. Crear manifiestos por proyecto con `drive_source`, `github_source`, `status`, `version` y `owner` usando referencias seguras.
3. Definir workflows de ventas/editorial/WhatsApp antes de automatizar respuestas autónomas.
4. Mantener secretos en variables de entorno o gestores específicos, nunca en el repositorio.
