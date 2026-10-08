# MONEY Ω — AppDeploy credit incident and two deployment candidates
Date: 2026-10-08, America/Mexico_City.

## Platform verified
AppDeploy reports CREDITS_USAGE_LIMIT_REACHED on daily and weekly Free tier: no new deployments. Daily reset 2026-10-09T00:00:00Z; weekly reset 2026-10-12T00:00:00Z. Do not retry deployment before restored quota or explicit plan change.
Existing canonical app money-z6epdn status READY, yet money-five-minute-cuts cron now DISABLED with disabled_reason=credits_exhausted. Latest pre-disable run had success. Do not label market quotes LIVE without source-tick and running collector proof.
Secondary historic app money-umvfi9 status READY.

## Code prepared in user conversation (NOT deployed or uploaded to GitHub)
Website bundle: MONEY_OMEGA_WEBSITE_APPDEPLOY_2026-10-08.zip; SHA256 586b148bde62a9c9dfd470c2188d23de2a23ed59de5dc4f609f62504d163faee.
Operations app: MONEY_OMEGA_OPERATIONS_APP_APPDEPLOY_2026-10-08.zip; SHA256 d18635a8631d148811d8fefca73cfed03a99733fc17596938dc35e886d0910c5.
Combined bundle: MONEY_OMEGA_WEB_Y_APP_LISTOS_APPDEPLOY_2026-10-08.zip; SHA256 77f352ad368b42235f8b6a1a2edca36b1a3e5120401b7a62d97ef79452267c47.
These ZIPs are downloads available in the current ChatGPT conversation. Codex does not automatically have access to the file bytes.

## Scope of deliverables
Website: responsive MONEY Ω institutional introduction, market-research architecture and external canonical site link.
Operations: independent read-only browser app, 5 views: overview, 28 historical resources from Oct 7 (all revalidate), market contract check, EV net calculator, sources/packets. Browser-local state and CSV/JSON export. No wallet connection, API secrets, fills or orders.
Local unit tests: 5/5 PASS. Static HTML/test-spec checks: PASS. AppDeploy E2E testing: NOT RUN due credit blocker.

## Site comparison / access states
Existing main MONEY AppDeploy frontend: https://money-z6epdn.v2.appdeploy.ai/ — code and app metadata verified.
Grok URL: https://themoney.grok.me/ — public content not accessible in current web audit; ACCESS PARTIAL.
Separate ChatGPT Sites URL: ACCESS UNAVAILABLE; do not fabricate or pretend comparison. User can identify from private ChatGPT Sites list.
Codex GitHub folder and AGENTS.md: ACCESS VERIFIED; Codex Cloud authenticated session project ID unverified.
Operating Bridge v2.1 vs money-app/README older plugin v1.0/Binance source: version drift needing reconciliation by Codex.

## Acceptance gate
Once deployment service unblocked, use AppDeploy get_deploy_instructions (frontend-only / html-static), deploy website and operations app as separate new app IDs, include their tests/tests.json, poll until READY, review mobile and desktop QA. Do not replace MONEY market backend accidentally. Restore the old collector only after quota status and quote timestamps verified. Keep execution READ_ONLY/PAPER.