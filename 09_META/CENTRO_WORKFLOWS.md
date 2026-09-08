# CENTRO — Workflows cruzados

## 1. WhatsApp Executive Inbox

**Entrada:** mensajes recientes en Peach.

**Secuencia:**
1. Leer sólo el periodo solicitado.
2. Clasificar: urgente, venta, trabajo, colaboración, soporte, personal, sin acción.
3. Detectar hilos con inbound posterior al último outbound.
4. Separar hechos de inferencias.
5. Proponer respuesta.
6. Enviar sólo cuando corresponda a la instrucción del usuario o a un workflow previamente aprobado.
7. No persistir transcripciones en GitHub.

**Salida:** resumen ejecutivo + acciones sugeridas + respuestas listas.

## 2. Lead de venta editorial

**Entrada:** interés recibido por WhatsApp, correo u otro canal.

**Secuencia:**
1. Identificar producto exacto y versión.
2. Verificar precio/fuente de pago en el sistema canónico.
3. No confundir Payment Link con pago confirmado.
4. Enviar copy o enlace correcto.
5. Si existe pago confirmado, localizar master de entrega en Drive.
6. Verificar versión, idioma, licencia y acciones posventa antes de entregar.
7. Registrar sólo métricas o decisiones no sensibles en GitHub.

## 3. Publicación / entrega editorial

**Entrada:** master aprobado en Drive.

**Secuencia:**
1. Confirmar archivo maestro y versión.
2. Verificar naming, metadatos y estado editorial.
3. Generar o actualizar componentes técnicos en GitHub cuando correspondan.
4. Producir entregable final.
5. Guardar master y output en Drive.
6. Registrar decisión/versionado en GitHub.

## 4. Cambio de arquitectura o automatización

**Entrada:** nueva integración, agente, workflow o cambio estructural.

**Secuencia:**
1. Inventariar estado actual.
2. Identificar riesgos y datos afectados.
3. Diseñar cambio reversible.
4. Implementar en commits pequeños.
5. Verificar lectura/escritura.
6. Documentar en `07_DECISION_LOG/`.

## 5. Investigación / dossier

**Entrada:** pregunta o proyecto de investigación.

**Secuencia:**
1. Buscar primero material canónico interno en Drive/GitHub.
2. Distinguir hechos internos, fuentes externas y propuestas.
3. Investigar externamente cuando sea necesario.
4. Guardar masters y papers/documentos en Drive si corresponde.
5. Registrar síntesis, ontologías y prompts reutilizables en GitHub cuando sean aptos para publicación.

## 6. Regla de oro de sincronización

No sincronizar sistemas completos entre sí.

Usar eventos y artefactos concretos:

- `Drive master aprobado` → posible release/documentación en GitHub.
- `GitHub release` → posible snapshot/entregable en Drive.
- `WhatsApp lead` → acción comercial; no exportación masiva.
- `Pago confirmado` → flujo de entrega, no inferencia desde un link.
- `Decisión estratégica` → Decision Log anonimizado.

## Criterio de autonomía

La autonomía debe crecer por capas:

- Nivel 0: lectura y análisis.
- Nivel 1: borradores y propuestas.
- Nivel 2: writes internos reversibles.
- Nivel 3: mensajes externos autorizados.
- Nivel 4: automatización por eventos con límites, opt-out, logging y rollback.

No saltar directamente al Nivel 4 sin pruebas controladas.
