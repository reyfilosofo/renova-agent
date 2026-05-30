# Arquitectura

SERESARTE V-OS v0.1 es una single-page app estatica.

## Componentes

- `index.html`: estructura base, boot screen, escritorio, dock, accesos y template de ventana.
- `styles.css`: sistema visual, layout de escritorio, ventanas, terminal y apps.
- `app.js`: runtime completo del V-OS.
- `server.py`: servidor estatico local en `http://localhost:8000`.

## Runtime

`app.js` contiene:

- Gestor de arranque.
- Gestor de ventanas movibles.
- Registro de apps internas.
- Sistema de archivos virtual.
- Terminal `renova-sh`.
- Persistencia con `localStorage`.
- Exportacion/importacion de estado JSON.

## Sistema de archivos virtual

El FS vive como objeto JSON:

```text
{
  "/ruta": {
    "type": "dir",
    "children": []
  },
  "/ruta/archivo.txt": {
    "type": "file",
    "content": "texto"
  }
}
```

La raiz inicial contiene:

```text
/
  home/renova
  apps
  system
  var/log
```

## Persistencia

La clave de `localStorage` es:

```text
seresarte_v_os_state_v1
```

Incluye `cwd`, archivos, nota abierta, ruta del explorador, direccion del navegador interno y estado basico de ventanas.

## Limites

No es una VM real. No emula CPU, kernel, hardware ni ejecuta binarios del sistema. La terminal opera sobre el FS virtual del navegador.
