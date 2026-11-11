# ℛENOVA PRESS · ENSAYO & TRATADO Ω
## Editorial Philosophy & Critical Prose Operating System — 1.0.0

Sistema complementario y **diferente** de los complementos existentes para poesía, artbooks, DAO, Orcas y creación general de libros. Este plugin delimita la colección de **ensayos filosóficos, tratados, monografías, crítica cultural, textos académicos, discursos filosóficos y prosa transdisciplinaria** de Carlos Jonathan González Rodríguez, firma Rey Filósofo.

### Núcleo editorial
- Corpus privado: archivos históricos, originales, versiones, variantes y linaje textual.
- Estilo y pensamiento: reconstrucción argumental, polilinealidad controlada, sátira e ironía como procedimientos, citas comprobadas.
- Producción: 6 × 9 pulgadas, serif editorial, justificación real, interlineado contenido, párrafos largos sin espaciados arbitrarios; variantes digital/impresión, si se solicitan.
- Cuatro niveles de evidencia separados: archivo del autor, fuente primaria, literatura científica, inferencia del sistema.
- Auditoría con verificaciones reales, veto de citas/DOI/ISBN inventados y prohibición de llamar «final» a una simple maqueta.
- Conservación del original, numeración de versiones y liberación únicamente con autorización autoral.

### Comandos reales de terminal (offline)
```bash
python scripts/editorial_engine.py index /ruta/privada/corpus --out build/corpus_index.json
python scripts/editorial_engine.py style /ruta/privada/corpus --out build/estilo.json
python scripts/editorial_engine.py typeset /ruta/ensayo.docx --out build/ensayo_prueba_6x9.docx
python scripts/editorial_engine.py render build/ensayo_prueba_6x9.docx --out-dir build/impresion
python scripts/editorial_engine.py audit build/ensayo_prueba_6x9.docx --out build/auditoria.json
```
`python-docx` y `PyMuPDF` son necesarios; LibreOffice es opcional para render PDF, pero indispensable para ese comando. La CLI genera **pruebas**; la revisión académica y comercial no está automatizada en su totalidad.

### Integración autorizada, por conectores
Drive: **archivo maestro**, fuente documental y ediciones privadas. GitHub: **código, esquemas, issues, pruebas y publicaciones técnicas sin manuscritos**. El plugin puede convocar los conectores ya vinculados por el usuario, pero instalarlo **no crea una sincronización continua ni credenciales OAuth**. Para cada operación se requiere acceso efectivo del conector, confirmación de destino y lectura de resultado. No copiar textos completos del corpus a un repositorio público.

### Puertas de control
`INGESTADO → CLASIFICADO → INVESTIGADO → EDICIÓN-1 → EDICIÓN-2 → PRUEBA → AUDITORÍA → APROBACIÓN DEL AUTOR → PUBLICABLE`. No hay autoliberación.

### Archivos
`skills/*/SKILL.md`: procedimientos conversacionales, `scripts/editorial_engine.py`: herramientas locales, `docs`: manuales, `config`: enlace lógico de rutas, `templates`: esquemas y matrices. `AGENTS.md`: gobierno. `tests`: pruebas ejecutables.
