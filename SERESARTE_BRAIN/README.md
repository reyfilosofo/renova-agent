# SERESARTE Brain / ℛenova Knowledge Vault

Sistema vivo de memoria estratégica, filosófica, editorial, cultural y operativa para Carlos Jonathan González Rodríguez, SERESARTE, ℛenova, NOUS, DAO IAO, Renova Press, Rey Filósofo, CIVITAS 100 y proyectos asociados.

Este directorio funciona como bóveda Markdown compatible con Obsidian, GitHub y Codex. Su función no es almacenar notas muertas, sino convertir ideas, conversaciones, entregables, libros, prompts, decisiones y archivos de trabajo en conocimiento acumulable, auditable y reutilizable.

## Propósito

SERESARTE Brain sirve para:

- conservar memoria estratégica y editorial;
- ordenar proyectos, clientes, conceptos, libros y metodologías;
- crear una base navegable para ChatGPT y Codex;
- producir entregables profesionales desde notas estructuradas;
- registrar decisiones y cambios de criterio;
- mantener una ontología viva de ℛenova, SERESARTE, DAO, NOUS y sistemas relacionados.

## Arquitectura operativa

```text
ChatGPT = pensamiento, interpretación, escritura, síntesis, estrategia.
Codex = operación sobre archivos, clasificación, enlaces, scripts, índices, cambios.
Obsidian = navegación humana, grafo, lectura, escritura cotidiana.
GitHub = versionamiento, historial, ramas, pull requests, auditoría.
Markdown = formato universal, legible y portable.
```

## Estructura principal

```text
SERESARTE_BRAIN/
├── 00_INBOX/
├── 01_SERESARTE/
├── 02_RENOVA/
├── 03_DAO/
├── 04_NOUS/
├── 05_CLIENTES/
├── 06_LIBROS/
├── 07_PERSONAS/
├── 08_OUTPUTS/
├── 09_META/
├── AGENTS.md
├── MAPA_MAESTRO.md
└── README.md
```

## Regla central

Toda conversación importante debe convertirse en memoria estructurada. Toda decisión debe quedar registrada. Todo concepto recurrente debe tener nota propia. Todo entregable debe poder rastrearse a sus fuentes internas.

## Flujo básico

1. Captura rápida en `00_INBOX`.
2. Clasificación por proyecto, concepto, cliente, libro o persona.
3. Conversión a Markdown con front matter YAML.
4. Creación de enlaces internos estilo Obsidian.
5. Registro de decisiones en `07_DECISION_LOG`.
6. Producción de entregables en `08_OUTPUTS`.
7. Actualización del mapa maestro y manifiestos.

## Convención de estados

```text
inbox      = nota recibida, sin procesar.
activo     = nota/proyecto en desarrollo.
aprobado   = criterio validado por Carlos Jonathan González Rodríguez.
archivado  = material preservado sin acción inmediata.
verificar  = dato que requiere fuente externa o revisión.
```

## Convención de tipos

```text
concepto
proyecto
cliente
persona
obra
capitulo
prompt
plantilla
decision
entregable
fuente
metodologia
```

## Uso con Codex

Pedir a Codex que lea primero:

1. `SERESARTE_BRAIN/AGENTS.md`
2. `SERESARTE_BRAIN/MAPA_MAESTRO.md`
3. `SERESARTE_BRAIN/09_META/reglas_editoriales.md`
4. `SERESARTE_BRAIN/09_META/prompt_maestro_codex.md`

Después, asignar tareas concretas y revisar siempre los cambios antes de aceptarlos.

## Uso con ChatGPT

Crear un Project llamado `SERESARTE Brain / Carlos Jonathan OS` y cargar como archivos de referencia:

- este `README.md`;
- `AGENTS.md`;
- `MAPA_MAESTRO.md`;
- `prompt_maestro_chatgpt.md`;
- documentos centrales de SERESARTE, ℛenova, DAO, NOUS y clientes.

## Norma de protección

No borrar información sin respaldo. No sobrescribir originales. No fusionar cambios de Codex sin revisión humana. No inventar datos biográficos, legales, financieros, científicos o empresariales. Cuando un dato requiera verificación externa, marcarlo como `requiere verificación`.
