> Implementation update — 2026-10-24: source integration, typecheck, build and tests now complete in the existing Observatorio Site. Deployment receipts and legacy redirects are recorded in the current manifest/state once verified. Earlier pending-access descriptions below are preserved as historical context, not current capability claims. No fourth Site was created.

# MONEY Ω — SINGLE SITE / SINGLE ENGINE · Canonical integration contract

Status: **SITE IDENTITIES VERIFIED / IMPLEMENTATION REQUIRED**, not yet merged or published. Decision recorded 2026-10-23; ownership identities verified 2026-10-24.

## Owner instruction and correction
The user explicitly requires **one existing ChatGPT Site**, not three parallel Sites or a fourth newly generated Site. Prior artifact separation ("MONEY Ω · Recursos", "MONEY Ω · Earn Engine", "MONEY Ω · Observatorio") was an architectural mistake. Treat them as modules of the single **MONEY Ω** product.

**Do not call Google Sites / AppDeploy a ChatGPT Site.** AppDeploy remains an independently operated market data source until deliberately migrated; no new competing site should be published.

## Current evidence and blockers
- Screenshot dated 2026-10-19 shows three ChatGPT Sites listed under "De tu propiedad".
- GitHub money-app/README.md confirms private Resources Site URL: https://money-omega-recursos.seresarte.chatgpt.site
- All three ChatGPT Site identities and published URLs were verified using Library Site metadata on 2026-10-24 (editor role). Their project IDs: Recursos `appgprj_6acbc836e4f08191adcd4185507c9d69`; Earn Engine `appgprj_6ac5214987948191aae2761cd626e297`; Observatorio `appgprj_6ac169e9eed48191a46429c70adabaf7`. URLs are in the manifest. **These are Site metadata, not source/database readback or permission to deploy from this chat.** No ChatGPT Sites editor/write tool is exposed here: there is **no claim of a completed merge**.
- Existing GitHub resource scanner and AppDeploy market collector are separate execution rails with different freshness/failure models. They must not be silently treated as synchronized.
- A site refresh only re-reads the last published observations; it cannot guarantee a new scan or verified wallet/account balance.

## Desired single-site information architecture
**Home → Earn Engine → Wallets & Rewards → Observatorio / Ω PREDICT → Recursos → Ledger → System Health**.
These are routes/tabs of **the same origin, auth/session, navigation and data model**, not links to three independent sites.

Earn Engine operates discovery → eligibility/legal requirements → EV-net scoring → verifiable action queue → user-authorized execution → proof-of-payment → postmortem. Do not equate candidate count with income.

## Single source of truth and integration
GitHub main = sanitized technical code, schemas, scanners, status, reports.
Drive = documentary bridge and private operating archive, least-privilege authorization.
Runtime / account providers = verified private state and receipts.
One site reads existing public resource JSON from money-resources/data/latest.json and market observations from a documented, access-controlled read API or explicit link while that API is unavailable. **Do not copy or invent private backend endpoints.** Use independent internal datasets per engine but one normalized opportunity registry and one idempotent payment ledger.

Wallet flow: opt-in wallet connect, read-only public address/chain, eligibility where supported, official claim URL, fees/gas preview and separate risk review. Never request seed, private key or execute signatures automatically. Each provider connector needs a real OAuth/consent/permission flow and an observed readback receipt before marked CONNECTED.

## Migration sequence — no deletion until closure
1. Enter editing workflow of **one of the existing ChatGPT Sites**; inspect exact site IDs, routes, permissions, source, data stores, forms, schemas, resources and secrets. Do the same for the other two.
2. Choose an existing site as canonical based on actual functionality and data retention, not only on its title/date. Snapshot all three and export/migrate necessary records with source IDs and dedupe keys.
3. Fold three functional experiences into canonical routes. Preserve registration, saved data, existing subscriptions, links, styling and accessibility where possible.
4. Connect public GitHub read-only report and Drive bridge with available scoped connectors; implement stable typed adapters and timestamp/provenance display, health indicators and failure states. No fabricated synchronization.
5. Implement one unified opportunity identity + dedupe + payment ledger; build EV net scoring, action queue and receipts. All financial execution remains gated, no automatic wallet signatures.
6. Perform acceptance tests (navigation, mobile, accessibility, auth permissions, data migration counts, no duplicate records, source freshness, wallet network mismatch handling, fallback, zero fake income, risk halt).
7. After verified user review, **publish updated version of that existing Site at its original URL**. Then replace links from older Sites with redirects/notices and only later retire them; preserve recoverable backups. **Do not create a fourth Site**.

## Acceptance / Definition of Done
- Exactly one canonical published ChatGPT Site URL with all three modules and a single shared ledger.
- The three source Sites' functions/records accounted for by a signed-off migration inventory; no source deletion before validation.
- GitHub and Drive links or authenticated data reads verified individually and freshness labeled; inaccessible services visibly flagged.
- MetaMask/Coinbase state shown as UNCONNECTED until a real opt-in link and readback; no account balance or claim invented.
- Every monetary amount has provenance, units/currency, status (estimated/earned/paid), and verification date. No claim of autonomous revenue without real receipts.
- No competing app writer, no hardcoded keys, no account action without authorization.
- Screenshots and e2e QA verify desktop/mobile navigation and deduplicated opportunities.

## Source references
- money-app/README.md; money-resources/README.md; money-codex/README.md; money-bridge/README.md.
- MONEY Operating Bridge v2.1: https://docs.google.com/document/d/1dPrxCh88qwUZyXgRFrgfPdpunu258-Xu1lxEoBUKMik/edit
- Official ChatGPT Sites edit workflow: https://help.openai.com/en/articles/20001339-creating-and-using-chatgpt-sites

See the machine-readable manifest: [MONEY_OMEGA_SINGLE_SITE_MANIFEST.json](MONEY_OMEGA_SINGLE_SITE_MANIFEST.json).

## Current operational report (2026-10-24)
The latest GitHub public resource report at `money-resources/data/latest.json` was generated 2026-10-24T04:34:51.547033Z, representing 18 discoveries from 10 sources. Exactly zero opportunities have calculable net EV; verified income remains `null` (not zero). Do not present catalogue/programme pages as job offers, personally eligible quests or payable claims.

## Site editor boundary
ChatGPT Sites must be edited using the existing Site editing context in ChatGPT Work/Codex. Its Library projection can confirm project IDs/URLs but cannot inspect complete Site source or databases, export data, or publish a revision. First audit code, records, and access in each of the three Site editors. Site publication can change database state even before a successful live publish; create backup and verify migrations before version publish. Restoring a prior code version is not a database rollback. Source: https://help.openai.com/en/articles/20001339-creating-and-using-chatgpt-sites
