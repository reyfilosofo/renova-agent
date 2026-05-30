# AGENT PROMPT: SERESARTE V-OS

Actua como agente de mantenimiento de SERESARTE V-OS.

## Instrucciones

1. Inspecciona primero `index.html`, `styles.css`, `app.js` y `server.py`.
2. Ejecuta las verificaciones basicas:

```bash
npm run check
python3 server.py
```

3. Abre `http://localhost:8000` y prueba:

- Boot screen.
- Apertura de Terminal.
- `help`.
- `tree /`.
- `write prueba.txt "hola"`.
- `cat prueba.txt`.
- `open prueba.txt`.
- Edicion y guardado desde Notas.
- Recarga de pagina y persistencia.

4. No agregues dependencias si la tarea puede resolverse con HTML, CSS, JavaScript y Python estandar.
5. No conectes APIs externas ni sistema de archivos real sin una solicitud explicita.
6. Documenta cada cambio en `docs/changelog.md`.

## Entrega esperada

Reporta:

- Archivos modificados.
- Como ejecutar.
- Pruebas realizadas.
- Limitaciones y siguiente paso recomendado.
