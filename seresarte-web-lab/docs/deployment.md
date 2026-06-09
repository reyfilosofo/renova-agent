# Guia de despliegue SERESARTE Web Lab

Esta guia define como publicar landings, webs, paginas interactivas y juegos desde GitHub.

## Modelo recomendado

GitHub funciona como fuente unica de verdad. La plataforma de despliegue toma el codigo desde la rama principal o desde una rama de preview.

Plataformas compatibles:

- Vercel
- Netlify
- Cloudflare Pages
- EdgeOne Pages
- GitHub Pages

## Flujo de despliegue

1. Crear proyecto o carpeta dentro de `seresarte-web-lab`.
2. Registrar el proyecto en `data/projects.json`.
3. Probar localmente.
4. Abrir pull request contra `main`.
5. Revisar texto, visual, accesibilidad y responsive.
6. Conectar plataforma de despliegue al repositorio.
7. Publicar y registrar la URL.

## Despliegue estatico simple

Para sitios HTML/CSS/JS sin dependencias:

- Build command: dejar vacio o usar `echo static`.
- Output directory: carpeta del sitio, por ejemplo `seresarte-web-lab`.
- Root directory: raiz del repositorio o `seresarte-web-lab` segun la plataforma.

## Variables y secretos

Nunca subir al repositorio:

- Tokens
- Claves API
- Contrasenas
- Datos bancarios
- Documentos sensibles sin version publica
- Datos privados de clientes, menores o aliados

Las variables privadas deben guardarse solo en la plataforma de despliegue.

## Convencion de ramas

- `main`: version estable.
- `feat/nombre-proyecto`: nueva landing o experiencia.
- `fix/nombre-problema`: correccion tecnica.
- `content/nombre-proyecto`: ajustes editoriales.
- `design/nombre-proyecto`: ajustes visuales.

## Convencion de commits

- `Add landing for Fundacion SERESARTE`
- `Add project registry for SERESARTE Web Lab`
- `Update copy for Entra al Lienzo`
- `Fix responsive gallery layout`
- `Optimize project images`

## Checklist antes de publicar

- Titulo y descripcion SEO.
- Open Graph basico.
- Imagen social optimizada.
- Footer con contacto.
- Responsive movil.
- Contraste legible.
- No hay datos privados.
- Textos revisados.
- Imagenes comprimidas.
- URL registrada en el proyecto.

## Siguiente decision tecnica

Definir plataforma principal. Para velocidad editorial se recomienda Vercel o Netlify. Para continuidad con pruebas previas tambien puede usarse EdgeOne Pages.
