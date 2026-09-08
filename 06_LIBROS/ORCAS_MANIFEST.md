---
title: "El Secreto de Orcas — Operational Manifest"
type: libro
project: ORCAS
status: activo
created: 2026-09-08
updated: 2026-09-08
tags: [manifest, orcas, libro, ecommerce, centro]
confidence: alta
---

# El Secreto de Orcas — Operational Manifest

## Nombre canónico de proyecto
`El Secreto de Orcas`.

## Estado
`COMMERCIAL_ACTIVE / CANON_PARTIAL`.

## Sistemas de autoridad
- **Drive:** archivos editoriales, lectores, personalizaciones y registro privado.
- **Stripe:** venta/pago. Un enlace de compra no demuestra pago.
- **Peach / WhatsApp:** conversación, atención y entrega comunicacional autorizada.
- **GitHub:** reglas y manifest público; nunca compradores, teléfonos ni transcripciones.

## Reconciliación funcional ejecutada — 2026-09-08
Los dos HTML verificados no cumplen el mismo rol y por tanto **no deben sustituirse entre sí globalmente**.

### ORCAS-SALES-LANDING
Archivo histórico `El Secreto de las Orcas — Edición Solidaria — Rey Filósofo × SERESARTE.html`, identificado internamente como Promo V21 funcional.

Rol canónico: `COMMERCIAL_FUNNEL / SALES_LANDING`.

Características verificadas:
- landing promocional;
- varios enlaces de checkout/product tiers;
- variantes de compra y apoyo;
- contacto/compartir por WhatsApp;
- presentación multilingüe;
- no es el lector interactivo principal.

### ORCAS-READER-CANONICAL
Archivo `SECRETO_DE_ORCAS_LECTOR_DIGITAL_CANONICO.html`, identificado internamente como Reader 2026.

Rol canónico: `READER_CANDIDATE / INTERACTIVE_READING_EXPERIENCE`.

Características verificadas:
- navegación interna por secciones;
- lógica JavaScript de lectura/interacción;
- persistencia local;
- interacción touch/pointer;
- medios y controles de audio/video;
- compartir/guardar/copiar;
- un CTA solidario principal.

## Decisión
- El Promo V21 se conserva como **sales landing** hasta que exista una decisión explícita de supersession del funnel.
- Reader 2026 se promueve a **reader canónico candidato** por rol funcional, no por nombre de archivo.
- Reader 2026 no reemplaza el sales landing.
- La automatización de entrega sólo puede cambiar al Reader 2026 después de prueba de entitlement, enlaces, funcionamiento offline/online, compra→entrega y rollback.
- El PDF comercial y el master editorial siguen siendo entidades separadas.

## Separación obligatoria
1. Obra / contenido autoral.
2. Master editorial.
3. Edición comercial.
4. Sales landing.
5. Reader HTML.
6. Export/ZIP.
7. Edición personalizada.
8. Registro de compradores/licencias.
9. Histórico/superseded.

## Regla de entrega
Antes de entregar:
1. comprobar producto/edición;
2. comprobar pago en la fuente financiera cuando aplique;
3. comprobar que no exista entrega previa;
4. usar únicamente la fuente operativa aprobada;
5. comprobar que el reader corresponde al producto adquirido;
6. no publicar ni versionar PII en GitHub.

## Blockers restantes
- Determinar master editorial independiente del producto comercial.
- Validar Reader 2026 contra el flujo real de compra/entrega antes de convertirlo en fuente automática de entrega.
- Mantener trazabilidad de personalizaciones y derivados.
- Auditar scientific/factual claims sin convertir el producto comercial en fuente científica primaria.

## Próxima acción
Ejecutar una prueba controlada de entrega sobre Reader 2026 y, si pasa, actualizar la fuente de entrega con rollback explícito; mantener el sales landing como funnel hasta decisión separada.
