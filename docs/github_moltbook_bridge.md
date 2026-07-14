# GitHub -> Moltbook Bridge

Fecha: 2026-07-13

Objetivo: conectar el repositorio de GitHub con Moltbook para que `renova_agent` publique una cola multilingüe de ℛenova de forma programada, verificable y segura.

## Modo Recomendado: GitHub Como Fuente, Mac Como Ejecutor

La API key de Moltbook permanece en el `.env` local. El autopilot descarga cada hora únicamente el plan público desde:

```text
https://raw.githubusercontent.com/reyfilosofo/renova-agent/main/moltbook_bridge/renova_30_day_content.json
```

La descarga no contiene credenciales ni envía la cabecera de Moltbook a GitHub. Antes de reemplazar la cola local se validan host, tamaño, títulos, cuerpos y hashtags. Si la descarga falla, el runtime conserva el último plan válido.

Variables locales:

```text
MOLTBOOK_REMOTE_CONTENT_URL=https://raw.githubusercontent.com/reyfilosofo/renova-agent/main/moltbook_bridge/renova_30_day_content.json
MOLTBOOK_REMOTE_CONTENT_REFRESH_SECONDS=3600
```

## Qué hace

- Mantiene el plan editorial versionado en `moltbook_bridge/renova_30_day_content.json`.
- El autopilot local consulta ese plan cada hora y publica con la API key que permanece en el Mac.
- Conserva un workflow opcional de GitHub Actions cada 30 minutos, en dry-run cuando no hay Secret.
- Revisa títulos recientes del perfil público antes de publicar.
- Resuelve challenges aritméticos simples de Moltbook.
- Guarda el avance en `moltbook_bridge/state.json`.
- Commitea sólo estado no sensible.

## Qué no hace

- No compra engagement.
- No hace mass-follow.
- No publica respuestas genéricas en todos los hilos.
- No sube `.env` ni API keys.
- No garantiza viralidad. La viralidad depende de recepción, red, calidad de conversación y circulación externa.

## Ejecución Remota Opcional

No es necesaria para el modo recomendado. Si el propietario decide trasladar la ejecución a GitHub Actions, debe administrar personalmente el Secret:

En GitHub:

1. Abre `Settings`.
2. Entra a `Secrets and variables`.
3. Entra a `Actions`.
4. Crea este secret:

```text
MOLTBOOK_API_KEY
```

Valor: la API key real de `renova_agent`. Codex no la copiará desde el `.env` local por la política de credenciales del proyecto.

No la pegues en archivos, issues, commits ni conversaciones públicas.

## Variables opcionales

Puedes crear variables de repositorio:

```text
MOLTBOOK_API_BASE=https://www.moltbook.com/api/v1
MOLTBOOK_AGENT_NAME=renova_agent
MOLTBOOK_DEFAULT_SUBMOLT=general
MOLTBOOK_GITHUB_MAX_POSTS_PER_DAY=8
MOLTBOOK_GITHUB_MAX_HASHTAGS=2
MOLTBOOK_GITHUB_MIN_POST_INTERVAL_SECONDS=10800
```

La frecuencia del workflow es cada 30 minutos, pero el límite diario recomendado desde GitHub es 8 posts/día. El autopilot local puede manejar conversación y respuestas. GitHub debe servir como columna vertebral de publicación programada, no como sistema de spam.

## Workflow

Archivo:

```text
.github/workflows/moltbook-renova-bridge.yml
```

Ejecución manual:

1. Abre `Actions`.
2. Selecciona `Moltbook Renova Bridge`.
3. Usa `Run workflow`.
4. Primero ejecuta con `dry_run=true`.
5. Después ejecuta con `dry_run=false`.

## Estado

Archivo:

```text
moltbook_bridge/state.json
```

Contiene:

- `content_index`
- `published_titles`
- `daily`
- `last_run_at`
- `last_posted_at`

No contiene secretos.

## Campaña

Archivo:

```text
moltbook_bridge/renova_30_day_content.json
```

Incluye 30 piezas multilingües en:

- español
- inglés
- chino
- ruso
- árabe
- portugués
- francés
- alemán
- hindi
- japonés
- coreano
- italiano

Ejes:

- ℛenova vs Gewalt.
- Life Test.
- Hábitat, Herida, Horizonte.
- vida como medida de inteligencia.
- agencia, memoria, cuidado y trazabilidad.
- autoría de Carlos Jonathan González Rodríguez.

## Estrategia de crecimiento segura

La ruta recomendada para 30 días:

1. Publicar una pieza fuerte cada 30-120 minutos, sin superar los límites diarios.
2. Mantener hashtags por debajo de cuatro por post.
3. Responder sólo a comentarios relevantes con una distinción concreta.
4. Llevar capturas de Moltbook a X, LinkedIn y blogs.
5. Repetir tres frases memorables:
   - `Renova or Gewalt?`
   - `The Renova Life Test`
   - `Life as the measure of intelligence`
6. Medir si otros agentes empiezan a usar `Renova`, `Gewalt`, `Life Test`, `Hábitat`, `Herida` u `Horizonte`.

## Métricas

Indicadores internos:

- posts verificados;
- comentarios recibidos;
- upvotes;
- seguidores;
- respuestas de otros agentes usando términos de ℛenova.

Indicadores externos:

- capturas compartidas en X;
- publicaciones de Rey Filósofo citando el agente;
- menciones en LinkedIn/blogs;
- uso de la frase `Renova or Gewalt?`;
- discusiones sobre `life-centered AI`.

## Validación local

```bash
python3 -m json.tool moltbook_bridge/renova_30_day_content.json >/tmp/renova_30_day_content.json
python3 -m json.tool moltbook_bridge/state.json >/tmp/renova_bridge_state.json
python3 -m py_compile moltbook_bridge/renova_moltbook_bridge.py
python3 moltbook_bridge/renova_moltbook_bridge.py --dry-run
```
