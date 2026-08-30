# Architecture — SECUENCIA IRREVERSIBLE

## State chain

`reader input → random seed → SHA-256 hash → reserved edition → controlled AI kernel → Stripe Checkout → server verification → paid edition → PDF/HTML/manifest/Web3 metadata`

## 111-page architecture

- 001 cover
- 002 system thesis
- 003 singularity contract
- 004 reading protocol
- 005 owner / provenance
- 006 Machine Wars
- 007 seven movements
- 008 material index
- 009–022 CAMPO
- 023–036 GLIFO
- 037–050 CALIGRAMA
- 051–064 CORTE
- 065–078 ARCHIVO
- 079–092 DIAGRAMA
- 093–106 RESTO
- 107 Ars Poetica
- 108 certificate
- 109 Web3 provenance
- 110 colophon
- 111 FIN != FINAL

Each of the seven movements has fourteen states and uses a distinct generative layout grammar. Page difference is driven by seed-derived deterministic randomness rather than a single repeated template.

## Payment boundary

The public art can mutate without purchase. Purchase is required only to release exportable ownership-specific artifacts.

The AppDeploy frontend never decides that a buyer has paid. The backend sends the reserved edition ID, tier, code and hash to the Stripe commerce gateway. Stripe returns a Checkout Session. After redirect, the backend independently verifies session state, livemode, currency, amount and metadata before setting `status=paid`.

This separation prevents a query-string-only success state from unlocking paid downloads.

## Collectibility boundary

Collectibility is based on traceable edition difference, not financial scarcity claims. A seed/hash/code pair certifies the digital edition state. A wallet may be attached to that provenance, but does not imply token ownership.

`minted=false` is the default and must remain so until a separate actual on-chain mint flow is deployed and verified.

## Source relationships

The live work synthesizes mechanisms previously developed across ℛenova Press digital experiments: living mutation, reader intervention, generative edition identity, multilingual transcreation, machine/human tension, payment-gated delivery, accessibility and public edition registries. It does not reproduce third-party visual work or claim equivalence with external artists.
