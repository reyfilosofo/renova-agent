# SERESARTE V-OS + ℛenova Agent

SERESARTE V-OS es una primera version funcional de ordenador virtual web para RENOVA/SERESARTE. Corre como aplicacion estatica y no requiere dependencias externas.

## SERESARTE Brain

Se añadió una capa de bóveda documental para trabajar el repositorio como segundo cerebro Markdown/Obsidian con apoyo de ChatGPT y Codex.

Archivos nuevos de esta capa:

- `AGENTS.md`: reglas operativas para Codex.
- `SERESARTE_BRAIN_START_HERE.md`: guía de inicio.
- `MANIFEST.md`: inventario vivo del repositorio.
- `09_META/MAPA_MAESTRO.md`: mapa conceptual inicial.
- `PROMPT_CODEX.md`: nota operativa breve para Codex.
- `TAXONOMIA.md`: clasificación mínima inicial.

## Ejecutar

```bash
python3 server.py
```

Abre:

```text
http://localhost:8000
```

Tambien puedes usar:

```bash
./run.sh
npm start
```

## Incluye

- Pantalla de arranque.
- Escritorio visual tipo sistema operativo.
- Ventanas movibles y redimensionables.
- Apps internas: Terminal, Archivos, Notas, Navegador interno simulado, Calculadora y Sistema.
- Sistema de archivos virtual guardado en `localStorage`.

## ℛenova Agent v1.1.0

Se montó el paquete calibrado del agente ℛenova al 19 de junio de 2026.

Archivos centrales:

- `README_LANZAMIENTO.md`
- `config/system_prompt.txt`
- `config/identity.json`
- `config/constitution.yaml`
- `config/safety_policy.yaml`
- `docs/onboarding_moltbook.md`
- `docs/runtime_spec.md`
- `docs/post_templates.md`
- `memory/agent_memory.json`
- `memory/doctrinal_changelog.md`
- `memory/equation_versions.md`
- `scripts/renova_runtime_skeleton.py`

Prueba local del scaffold:

```bash
python3 scripts/renova_runtime_skeleton.py
```

Moltbook se trata como identidad publica y plaza social. El cerebro operativo del agente es el runtime externo con memoria, auditoria, versionado y control humano.

## Terminal

Comandos soportados:

```text
help
pwd
ls
cd
tree
cat
write
append
touch
mkdir
rm
open
apps
date
whoami
neofetch
export
reset
```

Ejemplos:

```text
ls
tree /
write prueba.txt "hola"
cat prueba.txt
append prueba.txt "otra linea"
open prueba.txt
open files
```

## Persistencia

Los archivos virtuales, notas, ruta actual y parte del estado de ventanas se guardan en `localStorage` bajo la clave `seresarte_v_os_state_v1`. El comando `reset` reinicia ese estado.

## Verificacion

```bash
npm run check
python3 server.py
```

Luego prueba en navegador:

- La app carga en `http://localhost:8000`.
- Las ventanas se pueden mover.
- `help`, `ls`, `tree`, `cat`, `write` y `open` responden.
- Una nota editada se conserva al recargar.
