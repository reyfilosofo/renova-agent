# MANIFEST — SERESARTE Brain

Estado inicial creado el 2026-06-29. Última actualización: 2026-07-09.

## Función

Este archivo debe mantenerse como inventario vivo del repositorio. Codex debe actualizarlo después de cada auditoría, reorganización o carga significativa de archivos.

## Criterios de inventario

Cada entrada debe incluir:

- ruta;
- tipo probable;
- proyecto asociado;
- conceptos principales;
- estado editorial;
- acción recomendada;
- riesgos o dudas.

## Estados editoriales

- `inbox`: material recibido sin clasificar.
- `activo`: material en uso o desarrollo.
- `aprobado`: material validado como referencia.
- `archivado`: material preservado sin uso inmediato.
- `requiere_revision`: material ambiguo, contradictorio o incompleto.
- `requiere_verificacion`: material que necesita fuente externa.

## Inventario operacional

| Ruta | Tipo | Proyecto | Conceptos principales | Estado | Acción recomendada | Riesgos o dudas |
|---|---|---|---|---|---|---|
| `README.md` | documentación técnica | SERESARTE V-OS / Renova Agent | arranque, verificación, Page Agent, RSR | activo | Mantener actualizado con cada nueva capa | Ninguno crítico |
| `AGENTS.md` | constitución operativa | SERESARTE Brain / Codex | reglas, roles, seguridad editorial | aprobado | Respetar antes de cualquier edición | No borrar ni simplificar sin decisión registrada |
| `MANIFEST.md` | inventario vivo | SERESARTE Brain | auditoría, trazabilidad, clasificación | activo | Actualizar después de cambios significativos | Inventario no sustituye escaneo completo de árbol |
| `SERESARTE_BRAIN_START_HERE.md` | guía de inicio | SERESARTE Brain | bóveda, Obsidian, flujo Codex | aprobado | Usar como onboarding | Ninguno crítico |
| `.gitignore` | configuración técnica | Repo hygiene | secretos, Node, Python, editores | aprobado | Mantener estricto contra secretos | Revisar si aparecen nuevos artefactos |
| `.env.example` | plantilla segura | Repo hygiene / CI | variables, secretos, entorno | aprobado | Agregar solo nombres, nunca valores | Alto riesgo si se copia con secretos reales |
| `docs/security-secrets.md` | política de seguridad | Repo hygiene / LUCEM | secretos, rotación, límites | aprobado | Citar en PRs que toquen credenciales | Ninguno crítico |
| `.github/workflows/verify.yml` | CI | Repo hygiene | pruebas, Node, Python | activo | Mantener como validación general | Requiere que dependencias dev instalen correctamente |
| `.github/workflows/pages.yml` | despliegue GitHub Pages | SERESARTE V-OS | Pages, artifact, deploy | activo | Validar configuración de Pages en Settings | Puede requerir `PAGES_ADMIN_TOKEN` si Pages no está habilitado |
| `.github/workflows/renova-rsr-ci.yml` | CI estructural | Renova / NOUS RSR Lab | estructura, verificación, laboratorio | activo | Mantener junto con el laboratorio | No reemplaza pruebas funcionales |
| `.github/ISSUE_TEMPLATE/renova-rsr-task.yml` | template de issue | Renova / NOUS RSR Lab | tareas, revisión humana, LUCEM | activo | Usar para nuevas tareas RSR | Crear labels si GitHub no los tiene |
| `index.html` | interfaz estática | SERESARTE V-OS | escritorio virtual, Page Agent | activo | Mantener accesible y sin secretos cliente | CDN externo de Page Agent es demo público |
| `styles.css` | estilos frontend | SERESARTE V-OS | UI, escritorio, estética | activo | Revisar contraste y responsive | Requiere prueba visual |
| `app.js` | lógica frontend | SERESARTE V-OS | filesystem virtual, apps, terminal | activo | Ejecutar `node --check app.js` tras cambios | Riesgo de regresión si se edita sin pruebas manuales |
| `page-agent-bridge.js` | integración frontend | SERESARTE V-OS / Page Agent | GUI agent, bridge, panel | activo | Ejecutar `node --check page-agent-bridge.js` | El demo no debe recibir secretos |
| `server.py` | servidor local | SERESARTE V-OS | HTTP local, no cache | activo | Validar con `python3 -m py_compile server.py` | Puerto fijo 8000 |
| `package.json` | scripts Node/Python | Repo hygiene | check, test, verify, Ruflo, Codex | activo | Mantener scripts mínimos y claros | No instalar dependencias sin decisión |
| `pyproject.toml` | empaquetado Python | Renova Core | paquete, dev extras, pytest | activo | Mantener dependencias mínimas | Compatibilidad Python >=3.10 |
| `renova_core/__init__.py` | módulo Python | Renova Core | exports, versión | activo | Sincronizar versión con pyproject | Ninguno crítico |
| `renova_core/agent.py` | agente local | Renova Agent | respuestas, cautions, ontology | activo | Mantener sin llamadas de red por defecto | No vender como LLM autónomo |
| `renova_core/corpus.py` | utilidades corpus | Renova Open Corpus | JSON, glosario, búsqueda | activo | Añadir validaciones si crece corpus | Ninguno crítico |
| `renova_core/cli.py` | CLI | Renova Core | index, agent, ontology, canvas | activo | Probar comandos del README | Manejo limitado de errores de usuario |
| `renova_core/index.py` | motor IRG | Renova Index | score, dimensiones, reporte | activo | Conservar aviso no clínico/legal/financiero | No usar como diagnóstico profesional |
| `renova_core/lab.py` | canvas | Renova Lab Kit | prompts, taller, acción | activo | Expandir con plantillas de sesión | Ninguno crítico |
| `renova_core/ontology.py` | grafo conceptual | Renovagrama | conceptos, relaciones, búsqueda | activo | Agregar nodos con trazabilidad | Riesgo de deriva conceptual |
| `tests/test_index.py` | pruebas | Renova Index | IRG, buckets | activo | Ampliar cobertura para CLI y ontology | Cobertura parcial |
| `data/sample_assessment.json` | dato demo | Renova Index | evaluación, muestra | activo | Mantener sin datos personales reales | No usar como caso real |
| `data/glossary_min.json` | dato demo | Renova Open Corpus | términos, definiciones | activo | Expandir con fuentes internas | Requiere verificación si se publican claims |
| `docs/RENOVA_OPEN_SYSTEM.md` | documentación | Renova Open System | arquitectura pública | activo | Revisar con LUCEM antes de publicación | Requiere verificación externa si agrega claims técnicos |
| `docs/RENOVA_INDEX.md` | documentación | Renova Index | IRG, dimensiones | activo | Mantener límites explícitos | Riesgo de sobreinterpretación |
| `docs/RENOVA_AGENT.md` | documentación | Renova Agent | agente local, límites | activo | Mantener sin promesas de autonomía | Ninguno crítico |
| `docs/RENOVAGRAMA.md` | documentación | Renovagrama | ontología, grafo | activo | Vincular a `renova_core/ontology.py` | Ninguno crítico |
| `docs/RENOVA_LAB_KIT.md` | documentación | Renova Lab Kit | taller, canvas | activo | Añadir ejemplos de sesiones | Ninguno crítico |
| `docs/OPEN_CORPUS.md` | documentación | Renova Open Corpus | corpus, glosario | activo | Mantener trazabilidad de fuentes | Requiere expansión curada |
| `labs/renova-nous-rsr-lab/README.md` | documentación base | Renova / NOUS RSR Lab | RSR, ecosistema, flujo | activo | Usar como fuente del laboratorio | No presentar como AGI autónoma |
| `labs/renova-nous-rsr-lab/docs/00-manifiesto.md` | manifiesto | Renova / NOUS RSR Lab | inteligencia recursiva, cultura | activo | Desarrollar como white paper | Requiere fuentes externas si se vuelve académico |
| `labs/renova-nous-rsr-lab/docs/01-arquitectura.md` | arquitectura | Renova / NOUS RSR Lab | capas, LUCEM, Codex/GitHub | activo | Convertir en diagrama | Ninguno crítico |
| `labs/renova-nous-rsr-lab/docs/02-metodologia-rsr.md` | metodología | Renova / NOUS RSR Lab | observar, diagnosticar, archivar | activo | Crear checklist operativo | Ninguno crítico |
| `labs/renova-nous-rsr-lab/docs/03-productos.md` | catálogo | NOUS / SERESARTE | productos, entregables | activo | Convertir en fichas comerciales | Validar precios/alcance antes de vender |
| `labs/renova-nous-rsr-lab/docs/04-lucem-verification-protocol.md` | protocolo | LUCEM | fuentes, claims, riesgo | activo | Usar como gate editorial | Ninguno crítico |
| `labs/renova-nous-rsr-lab/products/nous-recursive-intelligence-sprint.md` | ficha de producto | NOUS | sprint, diagnóstico, límites | activo | Convertir en one-pager comercial | Validar alcance legal/fiscal/financiero |
| `labs/renova-nous-rsr-lab/tasks/codex-ready-tasks.md` | backlog | Codex / RSR Lab | landing, white paper, producto | activo | Convertir tareas a issues | Ninguno crítico |

## Pull requests resueltos manualmente

| PR | Estado de auditoría | Decisión |
|---|---|---|
| `#5 Add Renova NOUS Lab foundation` | contenido documental seguro; rama 74 commits detrás de `main` | integrado manualmente en `main` y cerrado como completado |
| `#2 Bootstrap RENOVA Agent technical scaffold` | scaffold Next.js raíz; rama 102 commits detrás de `main`; conflicto arquitectónico con SERESARTE V-OS actual | cerrado como superseded; no se fusionó para evitar sobrescribir la arquitectura vigente |

## Próxima auditoría

Codex debe ejecutar un escaneo completo del árbol real del repositorio y comparar este inventario contra GitHub para detectar archivos omitidos, duplicados, carpetas vacías, workflows obsoletos y documentación sin backlinks.
