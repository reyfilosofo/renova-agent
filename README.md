# SERESARTE V-OS

SERESARTE V-OS es una primera version funcional de ordenador virtual web para RENOVA/SERESARTE. Corre como aplicacion estatica y no requiere dependencias externas.

## Ejecutar

```bash
python3 server.py
```

Abre:

```text
http://localhost:8000
```

Tambien puedes usar:

```bash
./run.sh
npm start
```

## Incluye

- Pantalla de arranque.
- Escritorio visual tipo sistema operativo.
- Ventanas movibles y redimensionables.
- Apps internas: Terminal, Archivos, Notas, Navegador interno simulado, Calculadora y Sistema.
- Sistema de archivos virtual guardado en `localStorage`.

## Terminal

Comandos soportados:

```text
help
pwd
ls
cd
tree
cat
write
append
touch
mkdir
rm
open
apps
date
whoami
neofetch
export
reset
```

Ejemplos:

```text
ls
tree /
write prueba.txt "hola"
cat prueba.txt
append prueba.txt "otra linea"
open prueba.txt
open files
```

## Persistencia

Los archivos virtuales, notas, ruta actual y parte del estado de ventanas se guardan en `localStorage` bajo la clave `seresarte_v_os_state_v1`. El comando `reset` reinicia ese estado.

## Verificacion

```bash
npm run check
python3 server.py
```

Luego prueba en navegador:

- La app carga en `http://localhost:8000`.
- Las ventanas se pueden mover.
- `help`, `ls`, `tree`, `cat`, `write` y `open` responden.
- Una nota editada se conserva al recargar.
