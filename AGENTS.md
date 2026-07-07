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

## Protocolo Ruflo / Codex

Este repositorio puede operar con Codex como ejecutor y Ruflo / Claude-Flow como capa de coordinación, memoria y enjambre multiagente.

### Inicialización local recomendada

Ejecutar primero la verificación base del repositorio:

```bash
npm run verify
```

Después inicializar la capa multiagente para Codex:

```bash
npm run codex:init
```

Si se prefiere el inicializador directo de Ruflo:

```bash
npm run ruflo:init
```

Verificar que el servidor MCP esté visible para Codex:

```bash
npm run codex:mcp:list
```

Si no aparece, registrarlo manualmente:

```bash
npm run codex:mcp:add
```

### Uso operativo obligatorio con Codex

Para tareas complejas, Codex debe trabajar en cuatro fases:

1. **Inventariar**: leer estructura, archivos relevantes y restricciones del proyecto.
2. **Coordinar**: dividir la tarea en agentes o roles especializados antes de modificar archivos.
3. **Ejecutar**: producir cambios pequeños, verificables y reversibles.
4. **Recordar**: documentar decisiones, patrones reutilizables y pendientes.

### Roles sugeridos de agentes

- `arquitecto-renova`: estructura filosófica, ontología, coherencia conceptual.
- `editor-seresarte`: estilo editorial, claridad, voz institucional.
- `investigador`: fuentes, trazabilidad, verificación y bibliografía.
- `estratega-nous`: diagnóstico, pitch, entregables y modelo de negocio.
- `ux-cro`: sitio, experiencia de usuario, conversión y estructura web.
- `dev-python`: pruebas, CLI, Renova Core y automatizaciones.
- `dev-frontend`: escritorio virtual, interfaz, HTML, CSS y JavaScript.
- `qa-seguridad`: pruebas, regresiones, privacidad y riesgos.
- `documentador`: README, guías, changelog, índice y manuales.

### Reglas de ejecución multiagente

- No usar más agentes de los necesarios; preferir 3 a 7 para tareas normales.
- Antes de un cambio grande, generar `plan`, `riesgos`, `archivos afectados` y `criterios de aceptación`.
- Después de modificar archivos, ejecutar `npm run verify` cuando el entorno local lo permita.
- No instalar dependencias permanentes sin justificarlo en una decisión documentada.
- No enviar datos privados, biográficos sensibles, contratos, expedientes, contraseñas ni información financiera a proveedores externos sin aprobación explícita.
- No convertir notas especulativas en hechos.
- Todo cambio estratégico debe dejar huella en un archivo de decisión, changelog o documento de proyecto.

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
- sugerir nuevas carpetas o taxonomías;
- preparar planes de trabajo multiagente con Ruflo / Claude-Flow;
- generar pruebas y documentación antes de proponer cambios de arquitectura.

## Restricciones de seguridad editorial

No inventar información biográfica, legal, médica, financiera ni empresarial. No presentar hipótesis como hechos. No eliminar originales. No fusionar archivos sin conservar trazabilidad. No producir entregables comerciales sin indicar versión y fecha.
