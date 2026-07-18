# NOUS Intelligence Rooms

**OpenAI Build Week 2026 submission**<br>
**Creator:** Carlos Jonathan González Rodríguez · NOUS by SERESARTE

NOUS Intelligence Rooms turns fragmented organizational material into an evidence-backed decision architecture: executive synthesis, scored strategic signals, prioritized decisions, a 30/60/90-day roadmap and a traceable evidence ledger.

> **Verification status — 2026-07-17:** the curated SERESARTE flow, security regressions, request contract, structured output validation, desktop/mobile interface, keyboard flow, JSON export and print/PDF export were verified. The existing server-side key can access the official `gpt-5.6-terra` model record, but a real Responses API generation returned `429 insufficient_quota`; therefore a successful live analysis is **not** claimed. Docker and public deployment remain unverified because those facilities were unavailable in this pass.

## Product flow

1. Define the organization and decision to enable.
2. Add controlled context and, in live mode, up to three evidence files.
3. Generate a structured strategic diagnosis.
4. Review signals, priorities, evidence references and confidence.
5. Export JSON or a printable executive brief.

**Method:** Observe → Verify → Analyze → Convert → Produce

NOUS does not replace human judgment. It structures the evidence required to exercise it.

## Requirements

- Python 3.9 or newer.
- A modern browser.
- Optional: a server-side OpenAI API key with available project quota for live analysis.
- Optional: Docker for containerized execution.

The application has no third-party Python dependencies.

## Run locally

From `projects/nous-intelligence-rooms`:

```bash
./run.sh
```

Open <http://127.0.0.1:8000>. Stop the server with `Ctrl+C`.

Equivalent explicit command:

```bash
cd app
python3 server.py
```

The default bind address is `127.0.0.1`. To use another local port:

```bash
PORT=8080 ./run.sh
```

## Curated demo mode

Demo mode requires no key and always returns the fixed SERESARTE case in `app/demo_analysis.json`. It is deliberately deterministic so judges can review the complete product without an external service.

For transparency:

- Intake changes do not alter the curated diagnosis.
- Selected files remain in the browser and are not uploaded in demo mode.
- The demonstration observations are a controlled product example, not independently verified claims about SERESARTE.
- No Tayga or Lucky Pizza confidential material is included.

## Live Responses API mode

Export a key into the server process, start the app and enable **Use live GPT-5.6 analysis**:

```bash
read -s OPENAI_API_KEY
export OPENAI_API_KEY
export OPENAI_MODEL=gpt-5.6-terra
./run.sh
```

The live implementation keeps the key server-side and uses:

- OpenAI Responses API.
- Official model ID `gpt-5.6-terra` by default.
- Structured Outputs via strict JSON Schema.
- `input_image` and data-URL `input_file` content.
- `reasoning: {"effort": "medium"}`.
- `store: false`.
- A 12,000-token output ceiling.
- Local schema and semantic validation before data reaches the interface.

Every top item, signal, decision and roadmap action must include confidence plus valid `evidence_refs`. A failed live request returns an explicit error; it never substitutes curated data.

Official references: [GPT-5.6 Terra](https://developers.openai.com/api/docs/models/gpt-5.6-terra), [Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs), [file inputs](https://developers.openai.com/api/docs/guides/file-inputs), [image inputs](https://developers.openai.com/api/docs/guides/images-vision) and [API data controls](https://developers.openai.com/api/docs/guides/your-data).

## Environment variables

| Variable | Required | Default | Purpose |
|---|---:|---|---|
| `OPENAI_API_KEY` | Live mode only | empty | Server-side OpenAI credential. |
| `OPENAI_MODEL` | No | `gpt-5.6-terra` | Responses API model. |
| `HOST` | No | `127.0.0.1` | HTTP bind address. Docker sets `0.0.0.0`. |
| `PORT` | No | `8000` | HTTP port. |

The app does not load `.env` files. Inject values through the process or deployment environment. Never commit a key.

## Privacy and security

- Demo mode does not call OpenAI and does not upload selected browser files.
- Live mode sends submitted text and accepted file content to the Responses API.
- `store: false` disables persistence of the response object for later retrieval. It is not a promise of zero retention or an exemption from current OpenAI abuse-monitoring and data-control policies.
- Static paths are contained inside `app/static`; traversal attempts return 404.
- Model and user strings are rendered as text, not inserted as HTML.
- Accepted file types, MIME declarations, Base64 payloads, file counts and decoded sizes are validated server-side.
- API errors are mapped to bounded public messages; provider bodies and credentials are not returned.
- Security headers include CSP, frame denial, MIME sniffing protection, a restrictive permissions policy and no-referrer behavior.

For a public live deployment, add platform-level authentication, rate limiting and spending controls. A public demo-only deployment should omit `OPENAI_API_KEY`.

## Tests and verified checks

Run from the project directory:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests/test_app.py -v
```

Verified on 2026-07-17 with Python 3.9.6:

- 26/26 unit and HTTP integration tests passed.
- Full local output schema and semantic evidence references passed.
- Raw and encoded static path traversal returned 404.
- Invalid MIME, Base64, size, count and JSON requests were rejected.
- Responses API request shape, `store: false`, Structured Outputs and multimodal data URLs passed contract tests.
- Live failures remained explicit and provider details were not exposed.
- `python3 -m py_compile app/server.py` passed.
- `git diff --check` passed.
- Desktop and 390 px mobile flows had no horizontal overflow or console errors.
- Keyboard tabs, focus transfer, labels, error states and evidence links were exercised.
- The prior filename/model-output XSS reproduction no longer executed.
- Exported JSON parsed successfully and retained evidence references.
- Browser print export produced an 8-page Letter PDF.
- The 22-page master dossier PDF was separately rendered and found free of clipping; a viewer preview had produced the earlier false alarm.

### Live verification outcome

- Model metadata access: **verified** for `gpt-5.6-terra`.
- Real Responses API generation: **attempted but not successful**.
- Provider result: HTTP 429, `insufficient_quota`.
- Application result: HTTP 503, `openai_quota_exhausted`, with no analysis or curated fallback.

Add quota to the configured OpenAI project, restart the server and repeat the live workflow before claiming successful GPT-5.6 analysis.

## Docker

```bash
docker build -t nous-intelligence-rooms .
docker run --rm -p 127.0.0.1:8000:8000 nous-intelligence-rooms
```

For controlled live mode:

```bash
docker run --rm \
  -p 127.0.0.1:8000:8000 \
  -e OPENAI_API_KEY \
  -e OPENAI_MODEL=gpt-5.6-terra \
  nous-intelligence-rooms
```

Docker was not installed in the validation environment, so the image remains unverified.

## Repository and external delivery status

- Project branch: [`codex/nous-intelligence-rooms-build-week-2026`](https://github.com/reyfilosofo/renova-agent/tree/codex/nous-intelligence-rooms-build-week-2026/projects/nous-intelligence-rooms)
- Pull request: [#19](https://github.com/reyfilosofo/renova-agent/pull/19)
- Final URL tracker: [`submission/FINAL_URLS_TEMPLATE.md`](submission/FINAL_URLS_TEMPLATE.md)
- Codex verification record: [`submission/CODEX_BUILD_LOG.md`](submission/CODEX_BUILD_LOG.md)

Before Devpost submission: restore OpenAI API quota and record one successful live run, deploy and verify a public URL, host the video, complete the Devpost page, and regenerate the master ZIP so it contains this final code rather than the pre-audit source snapshot.

## License

See [`LICENSE`](LICENSE). The project uses an evaluation license; it is not MIT-licensed.
