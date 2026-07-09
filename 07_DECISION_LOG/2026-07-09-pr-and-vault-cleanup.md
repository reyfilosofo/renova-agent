---
title: "PR and vault cleanup"
type: decision
project: META
status: aprobado
author: "Carlos Jonathan González Rodríguez"
created: 2026-07-09
updated: 2026-07-09
tags: [github, pulls, codex, seresarte-brain, renova-nous-rsr]
related: ["#2", "#5", "#6", "#7"]
confidence: alta
---

# PR and vault cleanup

## Contexto

El repositorio tenía dos pull requests abiertos con ramas muy desactualizadas y dos issues abiertos sobre SERESARTE Brain / Renova Intelligence Vault.

## Decisiones

1. Integrar manualmente el contenido documental seguro del PR #5 en `main`.
2. Cerrar PR #5 como resuelto, sin merge automático, porque la rama estaba 74 commits detrás de `main`.
3. Cerrar PR #2 como superseded, porque su scaffold Next.js raíz estaba 102 commits detrás de `main` y entraba en conflicto con la arquitectura actual SERESARTE V-OS / Renova Core.
4. Crear estructura base de bóveda SERESARTE Brain con índices por carpeta, taxonomía, glosario, prompts maestros y plantillas.
5. Mantener la regla de no borrar ni sobrescribir arquitectura vigente sin decisión explícita.

## Archivos afectados

- `README.md`
- `MANIFEST.md`
- `.gitignore`
- `.env.example`
- `.github/ISSUE_TEMPLATE/renova-rsr-task.yml`
- `.github/workflows/renova-rsr-ci.yml`
- `docs/security-secrets.md`
- `labs/renova-nous-rsr-lab/`
- `00_INBOX/` a `09_META/`
- `07_DECISION_LOG/`

## Riesgos

- El entorno local de ejecución de ChatGPT no pudo clonar GitHub por falta de resolución DNS; la operación se realizó mediante el conector oficial de GitHub.
- Los workflows se disparan en GitHub después de los commits; su resultado final debe revisarse en Actions.
- La auditoría de árbol completo queda sujeta a una revisión posterior con Codex local o GitHub Actions, porque el conector no expone un listado recursivo completo de archivos.
