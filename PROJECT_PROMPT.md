# PROJECT PROMPT: SERESARTE V-OS

Construir y mantener SERESARTE V-OS como ordenador virtual web para RENOVA/SERESARTE.

## Objetivo

Crear una interfaz tipo sistema operativo que funcione en navegador, sin dependencias externas por defecto, con escritorio, ventanas movibles, terminal, archivos, notas, navegador interno simulado, calculadora y panel de sistema.

## Principios

1. Ser honesto: esto es un ordenador virtual web simulado, no una maquina virtual real.
2. Mantener ejecucion simple: `python3 server.py` y `http://localhost:8000`.
3. Guardar el estado localmente con `localStorage`.
4. Evitar dependencias externas salvo necesidad estricta.
5. Priorizar una base clara que pueda crecer hacia v0.2.

## Alcance v0.1

- Pantalla de arranque.
- Escritorio visual.
- Ventanas movibles y redimensionables.
- Terminal con comandos de navegacion y escritura.
- Sistema de archivos virtual.
- Editor de notas.
- Navegador interno para rutas simuladas.
- Calculadora local.
- Panel de sistema con exportacion/importacion de estado.

## Criterio de calidad

Cada cambio debe conservar:

- Carga sin errores de consola.
- Persistencia de archivos al recargar.
- Terminal funcional.
- Notas editables y guardables.
- Ejecucion sin build ni API keys.
