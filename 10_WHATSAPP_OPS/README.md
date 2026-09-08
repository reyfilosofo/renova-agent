# 10_WHATSAPP_OPS — Protocolo operativo

Esta carpeta documenta **reglas, flujos y plantillas no sensibles** para operar WhatsApp Business mediante Peach y ChatGPT/CENTRO.

## Regla cardinal

**No almacenar aquí conversaciones reales, teléfonos, nombres de clientes, OTP, imágenes privadas ni exports crudos.** El repositorio es público.

## Flujo recomendado

1. Leer mensajes directamente desde Peach.
2. Clasificar la conversación: urgente, venta, trabajo, colaboración, soporte, personal o sin acción.
3. Preparar respuesta en ChatGPT.
4. Verificar destinatario, intención y ventana de WhatsApp.
5. Enviar sólo cuando la acción esté autorizada.
6. Confirmar estado de envío cuando la herramienta lo permita.
7. Registrar únicamente decisiones o métricas agregadas sin PII.

## Comandos conceptuales CENTRO

- `CENTRO WhatsApp` — barrido ejecutivo de mensajes recientes.
- `CENTRO WhatsApp ventas` — detectar intención de compra y seguimientos.
- `CENTRO WhatsApp trabajo` — detectar propuestas, empleo, honorarios y colaboraciones.
- `CENTRO WhatsApp pendientes` — identificar hilos que requieren respuesta.
- `CENTRO WhatsApp SERESARTE` — priorizar temas institucionales/editoriales.

## Controles

- OTP/verificación: nunca copiar, publicar ni reenviar.
- Remitentes automatizados: evitar autorespuestas comerciales.
- Stripe: link de pago ≠ pago confirmado.
- Datos privados: permanecer en Peach/Drive u otro sistema privado autorizado.
- GitHub: sólo documentación general, esquemas y decisiones anonimizadas.

## Automatización futura

Antes de activar respuestas autónomas 24/7 deben existir:

- política de opt-in/opt-out;
- límites de envío;
- reglas de escalamiento humano;
- exclusión de contactos personales/sensibles;
- plantillas aprobadas por Meta cuando correspondan;
- pruebas con números controlados;
- registro de errores y rollback.
