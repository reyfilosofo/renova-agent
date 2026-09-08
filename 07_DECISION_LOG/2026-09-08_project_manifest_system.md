---
title: "Project Manifest System"
type: decision
project: META
status: aprobado
created: 2026-09-08
updated: 2026-09-08
tags: [centro, manifests, drive, github, canon]
confidence: alta
---

# Decisión — Project Manifest System

## Contexto
El Canon Master Index existente ya contiene un registro rico de obras, proyectos, duplicados, fuentes de verdad y mapas especializados. Sin embargo, la operación multi-conector requería separar el manifest privado —con referencias directas a Drive— del manifest público y versionable en GitHub.

## Decisión
Adoptar un sistema de dos capas:

1. **Manifest privado en Google Drive**: puede contener URLs/IDs de Drive, estados de cliente, relaciones entre masters y otros metadatos P1/P2 necesarios para operar.
2. **Manifest público-safe en GitHub**: conserva Project IDs, estados, políticas, blockers y siguientes acciones, pero no PII, conversaciones, contratos, credenciales ni referencias privadas innecesarias.

## Implementación
- Drive: `SERESARTE_BRAIN — AI OPS 2026/09_META/PROJECT_MANIFESTS_PRIVATE`.
- Drive: `CENTRO — Project Manifest Index · Private · 2026-09-08`.
- GitHub: `09_META/PROJECT_MANIFEST_INDEX.yaml`.
- GitHub: manifests específicos para SERESARTE, ℛenova, DAO, NOUS y ORCAS.
- `CONNECTOR_REGISTRY.yaml` actualizado a v2 para registrar el sistema.

## Política de master
Un filename con `FINAL`, `MASTER`, `MAESTRO`, `MONUMENTAL` o una versión alta no promueve automáticamente el activo. Los estados operativos son:
`DISCOVERED → CANDIDATE → VERIFIED_SOURCE → MASTER_CANDIDATE → MASTER`, con `COMMERCIAL_ACTIVE` y `SUPERSEDED` como estados ortogonales de operación.

## Consecuencia
CENTRO puede consultar el manifest privado para actuar y el manifest público para razonar/versionar sin contaminar el repositorio público con datos privados.

## Próximo gate
Antes de automatizar una entrega o sustitución de fuente debe existir: Project ID estable, fuente verificada, versión/estado, regla de entrega, blockers explícitos y rollback.
