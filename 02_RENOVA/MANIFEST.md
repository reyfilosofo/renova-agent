---
title: "ℛenova Core — Project Manifest"
type: proyecto
project: RENOVA
status: activo
created: 2026-09-08
updated: 2026-09-08
tags: [manifest, renova, corpus, centro]
confidence: alta
---

# ℛenova Core — Project Manifest

## Rol
Corpus filosófico, científico-propositivo y metodológico de ℛenova. Google Drive es la fuente documental; GitHub mantiene ontología, reglas, relaciones, issues y código no sensible.

## Estado canónico
`RECUPERACIÓN EN CURSO`. Existen varios candidatos fuertes, pero no hay un master global confirmado.

## Nodos verificados
- `CJGR-S000004` — corpus/serie ℛenova.
- `CJGR-W000121` — ℛENOVA (H): Hábitat, Herida y Horizonte, V7.5; candidato fuerte, no MASTER.
- `CJGR-W000122` — Filosofía Renovativa · Tratado de la vida que se abre, V2.7.
- `CJGR-W000024` — Tratado Matemático y Lógico / 32 ecuaciones, V4.1 empírico.
- `ℛenova: Ciencia de la Vida`, V8.0 — localizado por Canon.
- `RENOVA OMNIA QUALIA`, V3.0 — localizado; relación ontológica todavía no resuelta.
- `Qualia Renovativos` y `Renova Total Qualia Integrada` — líneas relacionadas que requieren diff.
- `CENTRO Runtime v1.2` — paquete operativo localizado.

## Regla de master
No fusionar tratados automáticamente y no asumir que una compilación posterior invalida o reemplaza una obra previa. `FINAL`, `MAESTRO` o `Vx.y` en filename son evidencia de versión, no de autoridad canónica.

## Quality gates
1. Hash de copias y detección de duplicados reales.
2. Diff textual/estructural entre versiones.
3. Auditoría de citas, referencias y claims científicos.
4. Separación explícita: tesis, hipótesis, modelo, metáfora, hallazgo empírico.
5. Preflight editorial y decisión trazable.

## Próxima acción
Construir un grafo de corpus con relaciones `version_of | derives_from | compiles | expands | independent_of`, seguido de issue ledger por tratado.
