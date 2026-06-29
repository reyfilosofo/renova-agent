# AGENTS.md — SERESARTE_BRAIN / ℛenova Agent

## Identidad del repositorio

Este repositorio funciona como el sistema operativo documental, filosófico, editorial, estratégico y creativo de Carlos Jonathan González Rodríguez, SERESARTE, ℛenova, NOUS, Rey Filósofo, Renova Press, DAO IAO, CIVITAS 100 y proyectos asociados.

Codex debe tratar este repositorio como una bóveda Markdown compatible con Obsidian y GitHub. Su función no es sustituir el juicio humano, sino ordenar, documentar, enlazar, auditar y preparar entregables sobre una base de conocimiento viva.

## Principios obligatorios

1. No borrar archivos sin crear respaldo verificable.
2. No sobrescribir decisiones previas sin registrar el cambio en `07_DECISION_LOG/`.
3. Antes de cambios masivos, generar inventario y plan de acción.
4. Mantener estilo profesional, filosófico, editorial, estratégico y claro.
5. Distinguir siempre entre hechos verificados, hipótesis, interpretaciones, propuestas creativas, pendientes y decisiones aprobadas.
6. Cuando haya contradicción entre archivos, reportarla antes de resolverla.
7. Todo entregable debe indicar proyecto, fecha, versión y fuente interna.
8. Usar nombres de archivo limpios, consistentes y compatibles con Markdown/Obsidian.
9. No usar Wikipedia como fuente.
10. Cuando un dato requiera verificación externa, marcarlo como `requiere verificación`.

## Estructura de trabajo recomendada

- `00_INBOX/`: notas sueltas, capturas, transcripciones, ideas rápidas.
- `01_SERESARTE/`: marca, manifiestos, presentaciones, identidad institucional.
- `02_RENOVA/`: ontología, epistemología, matemática, sensibilidad fundante, vida plena.
- `03_DAO/`: DAO IAO, Dao de la Vida, Dao de la Diplomacia, Dao Abrahamico, Dao No Humano.
- `04_NOUS/`: inteligencia estratégica, inteligencia privada, metodologías, dossiers.
- `05_CLIENTES/`: Tayga, Miguel Hidalgo, Transportes Alemar y otros proyectos comerciales.
- `06_LIBROS/`: borradores, capítulos, citas, bibliografía y versiones finales.
- `07_PERSONAS/`: autores, aliados, clientes, referentes, perfiles biográficos.
- `08_OUTPUTS/`: PDF, DOCX, PPTX, ZIP, prompts y entregables finales.
- `09_META/`: taxonomía, ontología general, glosario, reglas editoriales, prompts maestros.

## Formato de notas

Cada nota importante debe usar front matter YAML:

```yaml
title: "Título de la nota"
type: concepto | proyecto | cliente | libro | persona | prompt | entregable | decision
project: SERESARTE | RENOVA | DAO | NOUS | CLIENTES | LIBROS | META
status: inbox | activo | aprobado | archivado | requiere_revision
author: "Carlos Jonathan González Rodríguez"
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: []
related: []
confidence: baja | media | alta
```

Después del front matter, usar esta estructura base:

```markdown
# Título

## Resumen ejecutivo

## Desarrollo

## Relaciones conceptuales

## Decisiones

## Pendientes

## Fuentes internas

## Fuentes externas verificables
```

## Tareas frecuentes permitidas

Codex puede:

- crear índices;
- generar mapas conceptuales;
- detectar duplicados;
- clasificar notas;
- crear backlinks `[[...]]`;
- convertir notas en briefs, dossiers, one pagers o capítulos;
- mantener `MANIFEST.md`;
- actualizar `CHANGELOG.md`;
- generar plantillas Markdown;
- preparar prompts maestros;
- revisar consistencia terminológica;
- sugerir nuevas carpetas o taxonomías.

## Restricciones de seguridad editorial

No inventar información biográfica, legal, médica, financiera ni empresarial. No presentar hipótesis como hechos. No eliminar originales. No fusionar archivos sin conservar trazabilidad. No producir entregables comerciales sin indicar versión y fecha.
