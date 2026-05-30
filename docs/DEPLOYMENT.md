# Deployment

## Vercel

1. Push repository to GitHub.
2. Go to Vercel.
3. Import `renova-agent`.
4. Framework preset: Next.js.
5. Build command: `npm run build`.
6. Output: default Next.js.
7. Add environment variables only when real integrations exist.

## Local production check

```bash
npm install
npm run build
npm run start
```

## Production caution

This is a public-facing conceptual prototype. Do not present the API route as a fully autonomous research engine until retrieval, citations, logs and quality checks are implemented.
