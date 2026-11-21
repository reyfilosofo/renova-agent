# Public static deployment

This directory contains the demo-only drop-deploy build of
**NOUS Intelligence Rooms** by NOUS by SERESARTE.

## Public URLs

- Primary — EdgeOne: <https://nous-intelligence-rooms.edgeone.dev/>
- Mirror — Netlify: <https://nous-intelligence-rooms-seresarte.netlify.app/>

EdgeOne assigned the current production domain under `edgeone.dev`; the
platform did not assign an `edgeone.app` hostname.

An additional owner-only mirror exists at
<https://nous-intelligence-rooms-2026.seresarte.chatgpt.site>. The Sites
workspace blocks internet-public access, so that URL is not intended for
judges.

## Contents

- `static-demo/` — deployable directory with `index.html` at its root.
- `artifacts/NOUS_Intelligence_Rooms_STATIC_DROP_DEPLOY.zip` — identical
  no-wrapper ZIP for drag-and-drop hosts.

ZIP SHA-256:

```text
eb32251f599de1d7a23f5b310be765cd1334156fe669089fc0a72052fe2d5da1
```

The public export has no backend, API key, API route or POST request. It loads
the fixed SERESARTE case from `demo_analysis.json`; selected files remain in the
browser and are never uploaded. The live Responses API implementation remains
in the canonical application and is intentionally not part of this public
static build.
