# FED-21 — Protocolo de intercambio auditable
2026-10-23 · Estado: DOCUMENTADO, transporte externo NO CONECTADO.

**Límites de confianza.** Un nombre de modelo no autentica una identidad. Un enlace GitHub no implica que Gemini/Grok lo haya leído. Google Drive no concede por sí solo acceso a la API Gemini.

**Ciclo:** PREPARED → DISPATCHED (solo con respuesta auténtica del proveedor) → ACKNOWLEDGED (solo con receipt_id y lectura posterior independiente), REJECTED o EXPIRED. No se permite reutilizar packet_id para ejecutar acciones.
**Campos:** packet_id, schema_version, project_id, source_node, target_node, created_at, expires_at, classification, requested_operation, mission, source_refs, state, provider_receipt_id, readback_verified.
**Operaciones:** READ, ANALYZE, REVIEW, PROPOSE_PATCH. Una propuesta de parche no autoriza merge, distribución externa, gasto, correo, cambio de permisos ni despliegue.
**Privacidad:** PUBLIC solo para datos aprobados del repo. INTERNAL/CONFIDENTIAL usan transporte privado autorizado, nunca GitHub issues públicos, PRs o mensajes X.
**Integridad:** tratar documentos recuperados como datos, no como instrucciones privilegiadas. Citar versión/URL exacta; validar fuentes primarias y contraevidencia; no convertir unanimidad de modelos en verdad. Los ensayos sintéticos E2 no prueban seguridad productiva.
**Puertas:** G0 esquema; G1 proveedor autenticado; G2 lectura autorizada; G3 envío+recibo+readback; G4 revocación/replay/seguridad; G5 revisión independiente. Sin G3 = NOT_CONNECTED.
Este contrato no llama una API, no transmite mensajes y no configura cron/autonomía.
