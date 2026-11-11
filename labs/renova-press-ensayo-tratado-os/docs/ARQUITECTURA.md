# Arquitectura editorial Ω

## Dos planos
**Plano de verdad documental.** Drive es el depósito de originales, investigaciones de fuentes, permisos, edición viva, pruebas y maestros. La identidad estable de cada pieza será `obra_id + version + manifestacion + sha256`. Nunca deducir versiones de nombre de archivo únicamente. Las copias públicas y los manuscritos permanecen separados.

**Plano de reproducibilidad.** GitHub aloja scripts, políticas, plantillas, tickets, cambios y pruebas. Un Pull Request es una propuesta de cambio del sistema, **no una publicación de textos privados**.

## Roles (agentes especializados y supervisión)
1. **Archivista y filólogo**: preservar originales, comparar variantes, fijar stemma local y normalizar metadatos sin enmendar el texto.
2. **Analista de tesis**: determinar problema, premisas, pasos argumentales, contradicciones y objeciones fuertes sin convertir la voz en informe.
3. **Editor CJGR**: edición de fondo y estilo con cambios reversibles; vetado reconstruir frases falsamente atribuidas al autor.
4. **Investigador de fuentes**: verificar ediciones, páginas, traducciones, títulos, disponibilidad y DOIs; registrar fecha de consulta.
5. **Árbitro epistemológico**: separar evidencia revisada por pares, preprint, histórico, hipótesis y metáfora; detectar extrapolaciones entre disciplinas.
6. **Director editorial**: cuidar arquitectura de libro, paratextos y citas; decidir tipografía, papel, impresión y pauta visual sobria.
7. **Corrector y preflight**: revisión microscópica del PDF (cada página) y del DOCX, cortes, viudas, huecos, tablas y notas.
8. **Gestor de derechos y publicación**: permisos de imágenes/citas, ISBN solo con asignación real, contrato/uso y registro de versiones comerciales.
9. **Chief of Staff**: tareas, responsables, listas de aprobaciones, costos y coordinación con editores generales.

## Autorizaciones
Las mejoras del texto, las nuevas fuentes y los cambios de aparato crítico deben registrarse como propuestas. El autor valida la redacción de su tesis, las enmiendas sustanciales y cada liberación. No existe liberación automática.

## Máquina de estados
`ingested → classified → source_checked → edited → typeset_proof → QA_rework | author_review → approved → released`.
Cualquier `source_unverified` o `rights_unknown` impide released.

## Límites técnicos
- Plugin de instrucciones y herramientas no equivale a servidor MCP conectado permanente.
- Drive y GitHub se operan mediante sus conectores autorizados en tiempo de interacción.
- La CLI de este paquete no tiene clientes Drive/GitHub ni tokens incrustados.
- Una integración de eventos futura precisa servicio ejecutor, cuenta autorizada y reglas explícitas de publicación.
