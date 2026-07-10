# Changelog

## 0.2.0 - 2026-07-10

- Restringe el servidor local a una lista explícita de assets públicos y hosts loopback.
- Añade CSP y cabeceras de seguridad; Page Agent queda desactivado hasta consentimiento explícito y usa SRI.
- Sustituye la evaluación dinámica de la calculadora por un parser aritmético local probado.
- Añade pruebas de aislamiento del servidor y de la calculadora.
- Construye GitHub Pages desde `_site/` mediante allowlist, nunca desde la raíz de la bóveda.
- Migra Web3 a Hardhat 3.9.1 y Solidity 0.8.30 con lockfile y auditoría npm en cero.

## 0.1.0 - 2026-05-30

- Crea primera version funcional de SERESARTE V-OS.
- Agrega `index.html`, `styles.css`, `app.js` y `server.py`.
- Agrega boot screen, escritorio, dock, accesos directos y ventanas movibles.
- Agrega apps internas: Terminal, Archivos, Notas, Navegador interno, Calculadora y Sistema.
- Implementa sistema de archivos virtual persistente en `localStorage`.
- Implementa comandos de terminal: `help`, `pwd`, `ls`, `cd`, `tree`, `cat`, `write`, `append`, `touch`, `mkdir`, `rm`, `open`, `apps`, `date`, `whoami`, `neofetch`, `export` y `reset`.
- Agrega documentacion de arquitectura, roadmap, prompts y ejecucion local.
