# SERESARTE Web Lab

Sistema maestro para organizar, versionar y desplegar los landings, webs, paginas interactivas, experiencias digitales y juegos ligeros de SERESARTE, Fundacion SERESARTE, SERESARTE Media, SERESARTE Experiences, ReyFilosofo y Renova.

Este modulo convierte GitHub en archivo vivo, tablero tecnico y fuente unica de verdad para el ecosistema digital SERESARTE.

## Proposito

SERESARTE Web Lab evita proyectos dispersos, archivos finales duplicados, landings dificiles de editar y piezas interactivas sin control de versiones. Cada sitio debe vivir como codigo, contenido, diseno documentado y ruta de despliegue.

## Principios de operacion

1. Todo landing o web debe tener carpeta propia.
2. Todo experimento interactivo debe tener nombre, estado, responsable, ruta y notas de despliegue.
3. Toda pieza debe poder editarse, auditarse, duplicarse y desplegarse sin rehacer el proyecto desde cero.
4. Los textos institucionales, artisticos y comerciales deben pasar por revision editorial antes de publicarse.
5. Las imagenes pesadas deben optimizarse antes de integrarse al repositorio.
6. Los proyectos comerciales o estrategicos deben iniciar en rama de trabajo y pasar por pull request antes de llegar a main.

## Estructura

seresarte-web-lab/ contiene el hub, estilos, datos de proyectos y documentacion operativa.

## Familias de proyectos

- Landings institucionales: Fundacion SERESARTE, SERESARTE Group, SERESARTE Media, SERESARTE Experiences, ReyFilosofo x SERESARTE, Renova Press y SERESARTE Editions.
- Landings comerciales: voluntariado corporativo, RSE/RCE, Entra al Lienzo, Mural Colectivo, 27NoDiceMucho, Natura Movil, Art Collectibles y SERESARTE HTML.
- Experiencias interactivas: galeria viva, archivo de artistas, mapa de impacto, simulador de voluntariado, generador de propuestas, coleccion SERESARTE HTML.
- Juegos y prototipos: memoria visual, trazo y color, juegos educativos, microjuegos de arte relacional y experiencias filosoficas.

## Estados

idea, brief, prototype, review, deploy-ready, live, archive.

## Estandar visual

Negro profundo, blanco editorial, marfil, dorado, cobalto y rojo SERESARTE; margenes amplios; alto contraste; tipografia elegante; espacio negativo; imagen artistica; jerarquia clara; interaccion precisa.

## Flujo

1. Registrar el proyecto en data/projects.json.
2. Crear carpeta propia cuando pase de idea a prototipo.
3. Trabajar en rama feat/nombre-del-proyecto.
4. Revisar texto, visual, responsive y accesibilidad.
5. Abrir pull request contra main.
6. Desplegar en Vercel, Netlify, Cloudflare Pages, EdgeOne Pages o GitHub Pages.
7. Registrar URL publica, fecha y version.
