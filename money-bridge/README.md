# Ω PREDICT × MONEY — Research Bridge v1

This directory defines a shared, versioned research handoff between the ChatGPT project Ω PREDICT and Grok Bot MONEY.

## Purpose
- Standardize how research packets are exchanged.
- Preserve timestamps, uncertainty, supporting evidence and counter-evidence.
- Make disagreements between models explicit.
- Keep a durable audit trail.
- Avoid storing credentials or private secrets.

## Roles
Ω PREDICT produces structured research packets.
MONEY independently reviews those packets.
The human operator remains the final decision-maker.

## Canonical flow
1. Ω PREDICT creates an intelligence packet.
2. Packet is validated against the JSON schema.
3. MONEY reviews freshness, identifiers, evidence and conflicts.
4. MONEY returns a review packet.
5. Outcome can be archived for postmortem and calibration.

## Storage split
- GitHub: schemas, prompts, version history and non-secret examples.
- Google Drive: private human-readable archive and reports.
- Credentials/API secrets/private keys: never stored here.

## Versioning
Every packet has a packet_id, created_at_utc, expires_at_utc and schema_version.
Material methodology changes receive a new strategy_id/version instead of rewriting history.

## Security
Never commit:
- API keys
- seed phrases
- private keys
- access tokens
- session cookies
- personally sensitive account credentials
