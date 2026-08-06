---
title: "Repository hardening and complete verification baseline"
type: decision
project: META
status: aprobado
author: "Carlos Jonathan González Rodríguez"
created: 2026-07-10
updated: 2026-07-10
tags: [github, ci, seguridad, renova-core, web3, pages]
related: ["[[MANIFEST]]", "[[SECURITY]]", "[[CHANGELOG]]"]
confidence: alta
---

# Repository hardening and complete verification baseline

## Resumen ejecutivo

La auditoría del commit `2bd55dd` confirmó que los checks verdes no cubrían todo el repositorio. Se reprodujeron cuatro fallos prioritarios: la CLI documentada no se ejecutaba, el IRG podía producir valores fuera de 0–100, el servidor local exponía la raíz completa del repositorio y Web3 no compilaba con las dependencias resueltas.

## Desarrollo

Se decidió crear una rama aislada y corregir el sistema como una sola unidad verificable:

- validación estricta de evaluaciones IRG y pesos;
- CLI ejecutable, errores concisos y pruebas de todos los subcomandos;
- servidor local limitado a hosts loopback y assets públicos allowlisted;
- Page Agent desactivado por defecto, con consentimiento de sesión, SRI y CSP;
- parser aritmético local sin `eval` ni `Function`;
- artefacto Pages generado en `_site/` sin bóveda, configuración, memoria o dependencias;
- Web3 migrado a Hardhat 3.9.1 con versiones bloqueadas, compilador local Solidity 0.8.30, auditoría npm sin hallazgos, pruebas y despliegue local efímero;
- CI con permisos mínimos, SHAs fijados, matriz Python, cobertura, Web3 y frontera pública;
- escaneo preventivo de patrones comunes de credenciales.

## Relaciones conceptuales

La decisión aplica el principio LUCEM de que una afirmación de funcionamiento debe corresponder a evidencia reproducible. Un workflow verde deja de considerarse prueba suficiente cuando omite módulos declarados por el propio repositorio.

## Decisiones

1. `npm run verify` será el contrato de verificación del núcleo.
2. `npm run verify:all` añadirá Web3 y la construcción pública de Pages.
3. Ningún servidor o artifact debe publicar la raíz de la bóveda.
4. Toda integración de agente externo será opt-in y declarará su frontera de privacidad.
5. Las evaluaciones parciales solo serán válidas con pesos explícitos y se rotularán como personalizadas.

## Pendientes

- Requiere decisión del propietario: convertir el repositorio completo en privado o separar una bóveda privada de un repositorio público.
- Requiere configuración administrativa en GitHub: habilitar Pages con GitHub Actions como fuente.
- Requiere configuración administrativa en GitHub: ruleset de `main` con PR obligatorio, checks y revisión humana apropiada para una cuenta individual.
- Requiere decisión jurídica: licencia del código raíz y licencia cultural separada.

## Fuentes internas

- `AGENTS.md`
- `.github/workflows/*.yml`
- `server.py`
- `renova_core/`
- `web3-starter/`
- evidencia de pruebas de la rama `codex/repository-hardening-20260710`

## Fuentes externas verificables

- Documentación oficial de GitHub Pages y permisos de Actions.
- Releases oficiales de GitHub Actions, Solidity y OpenZeppelin verificadas el 2026-07-10.
