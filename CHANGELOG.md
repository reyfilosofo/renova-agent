# CHANGELOG

## 2026-07-10

### Fixed

- Activated the documented `python -m renova_core.cli` entrypoint and added concise CLI errors.
- Enforced finite, non-negative IRG weights and explicit weights for partial assessments.
- Added accent-insensitive concept matching and medical, legal and financial cautions.
- Restricted the local server to loopback hosts and allowlisted public assets.
- Replaced calculator `Function()` evaluation with a tested arithmetic parser.
- Migrated the Web3 starter to Hardhat 3.9.1 and Solidity 0.8.30 with a local locked compiler.
- Added the missing Web3 deployment script and contract tests.

### Security

- Made the Page Agent demo opt-in per session and added SRI, CSP and privacy disclosure.
- Replaced the full-repository Pages artifact with a generated `_site/` allowlist.
- Added repository credential-pattern checks, security policy and Dependabot configuration.
- Pinned GitHub Actions to verified commit SHAs with read-only permissions.
- Reduced the locked Web3 dependency audit from 43 findings to 0.

### Verification

- Expanded Python tests from 2 cases to coverage-enforced tests across index, CLI, agent, corpus, ontology, lab and server.
- Added Node calculator tests, Web3 compile/tests/deployment smoke test and a Python version matrix.

## 2026-07-09

### Added

- Repository hygiene files: `.gitignore`, `.env.example` and `docs/security-secrets.md`.
- RSR issue template and structure CI workflow.
- `labs/renova-nous-rsr-lab/` foundation with manifesto, architecture, methodology, products, LUCEM protocol, NOUS sprint and Codex task list.
- SERESARTE Brain base folder indexes from `00_INBOX/` to `09_META/`.
- Master taxonomy, master glossary, Codex prompt, ChatGPT prompt and reusable Markdown templates.
- Decision log entry for PR cleanup and vault initialization.

### Changed

- Updated `README.md` with RSR lab, verification and security instructions.
- Updated `MANIFEST.md` with repository inventory and PR resolution notes.

### Closed

- PR #5 was integrated manually into `main` and closed.
- PR #2 was closed as superseded to avoid replacing the current architecture.

### Notes

- GitHub Actions should be checked after workflow completion.
- A full recursive tree audit should be run from Codex/local GitHub once repository checkout is available.
