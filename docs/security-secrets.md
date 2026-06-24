# Security and Secrets

## Rule

Never commit real credentials, tokens, API keys, private keys, certificates or service secrets.

Use:

- local `.env` files for local development
- GitHub Actions repository secrets for CI
- Codex environment secrets for Codex tasks
- provider dashboards for key rotation

## Files

Safe to commit:

- `.env.example`
- documentation that names required variables without values

Never commit:

- `.env`
- `.env.local`
- `.env.production`
- `*.key`
- `*.pem`
- credential exports
- screenshots containing tokens

## If a secret was pasted in chat or exposed

1. Treat it as compromised.
2. Revoke it in the provider dashboard.
3. Create a new secret.
4. Store it only in the intended secret manager.
5. Do not paste it into GitHub issues, commits, pull requests or documentation.

## Required variables

See `.env.example` for names only.
