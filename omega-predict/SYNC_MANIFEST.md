# Ω PREDICT · SYNC MANIFEST

## Purpose
Define the relationship between the operational Google Drive workspace and the version-controlled GitHub mirror.

## Workspaces
- Drive: https://drive.google.com/drive/folders/1qazHJ5CLmp3hua07v0Rkn57i4MDKX4Jl
- GitHub: https://github.com/reyfilosofo/renova-agent/tree/main/omega-predict

## Canonicality
- **GitHub:** canonical version-controlled text specifications.
- **Drive:** operational/editorial workspace for project context and live ledger work.

## File map
| Drive | GitHub |
|---|---|
| Ω PREDICT · README | `omega-predict/README.md` |
| Ω PREDICT · CORE INSTRUCTIONS | `omega-predict/PROJECT_INSTRUCTIONS.md` |
| Ω PREDICT · MASTER PROTOCOL v1.0 | `omega-predict/MASTER_PROTOCOL.md` |
| Ω PREDICT · MARKET SCHEMA | `omega-predict/MARKET_SCHEMA.md` |
| Ω PREDICT · SOURCE REGISTRY | `omega-predict/SOURCE_REGISTRY.md` |
| Ω PREDICT · POSTMORTEM TEMPLATE | `omega-predict/POSTMORTEM_TEMPLATE.md` |
| Ω PREDICT · LEDGER | `omega-predict/LEDGER_SCHEMA.csv` |
| Ω PREDICT · SYNC MANIFEST | `omega-predict/SYNC_MANIFEST.md` |

## Version rule
Major conceptual changes -> increment protocol version and commit in GitHub.  
Editorial changes -> commit with concise message and reflect in Drive.  
Ledger observations -> append; never rewrite history merely because an outcome was unfavorable.

## Current sync mode
**Linked mirror, not continuous automatic sync.** Cross-links are explicit. Continuous automatic synchronization is not active because no Google Drive API credential/secret has been provisioned to GitHub Actions.

## Security rule
Never place wallet seed phrases, private keys, API secrets, exchange credentials, session cookies, or restricted personal data in GitHub, Drive source registries, prompts, or logs.

## Future automation
A GitHub Action or intermediary service may synchronize selected text files to Drive after explicit credential provisioning and least-privilege review.