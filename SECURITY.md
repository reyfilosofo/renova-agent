# Security policy

## Supported branch

Security fixes target the current `main` branch. This repository is an educational and cultural technology prototype; the included smart contracts and agent integrations are not audited for production use with money, credentials or confidential records.

## Reporting a vulnerability

Do not publish credentials, private records or exploit details in a public issue. Contact the repository owner privately through the verified contact channel in the GitHub profile and include:

- the affected file and version;
- reproducible steps that do not expose third-party data;
- likely impact;
- a suggested mitigation, when available.

## Public-repository boundary

This repository is public. Never commit client files, private intelligence, contracts containing confidential terms, medical or legal records, personal identifiers, `.env` files, wallet secrets, seed phrases, API keys, access tokens, private keys or unpublished financial information.

Any file committed to this repository should be treated as publicly disclosed.

## External integrations

Third-party agents, publishing bridges and Web3 components must use least-privilege credentials, explicit opt-in where applicable, pinned dependencies and human review before production use.
