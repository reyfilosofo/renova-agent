# Security and Secrets

## Rule

Never commit real credentials, tokens, API keys, private keys, certificates or service secrets.

Use:

- local `.env` files for local development;
- GitHub Actions repository secrets for CI;
- Codex environment secrets for Codex tasks;
- provider dashboards for key rotation.

## Files

Safe to commit:

- `.env.example`;
- documentation that names required variables without values.

Never commit:

- `.env`;
- `.env.local`;
- `.env.production`;
- `*.key`;
- `*.pem`;
- credential exports;
- screenshots containing tokens.

## If a secret was pasted in chat or exposed

1. Treat it as compromised.
2. Revoke it in the provider dashboard.
3. Create a new secret.
4. Store it only in the intended secret manager.
5. Do not paste it into GitHub issues, commits, pull requests or documentation.

## Required variables

See `.env.example` for names only.

## Public repository warning

The current GitHub repository is public. `.gitignore`, the local server allowlist and the Pages `_site/` allowlist reduce accidental exposure, but they cannot make a committed file private. Client records, private intelligence, unpublished contracts, personal files and confidential drafts belong in a separate private vault.

## Browser-agent boundary

The optional Page Agent demo is disabled until the user accepts its session notice. Once activated, it loads external code and sends prompts to a public test endpoint. Never activate it with secrets or private data in the page or `localStorage`.
