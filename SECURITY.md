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

This repository is currently public. Never commit client files, private intelligence, contracts containing confidential terms, medical or legal records, personal identifiers, `.env` files, wallet secrets, seed phrases, API keys, access tokens, private keys or unpublished financial information.

The local server and GitHub Pages build use explicit public allowlists. That boundary does not make tracked GitHub files private: any file committed to this repository should be treated as publicly disclosed.

## External Page Agent demo

The Page Agent demo is disabled by default and requires session-specific consent. Activating it loads a version-pinned, integrity-checked script from jsDelivr and sends instructions to a public test service. Do not activate it while confidential information is present in the page or browser storage.
