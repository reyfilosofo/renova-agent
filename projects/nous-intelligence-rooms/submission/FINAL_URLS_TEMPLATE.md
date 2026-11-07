# NOUS Intelligence Rooms — verified links and external delivery tracker

Status reviewed: 2026-11-02. Keep PR #19 (https://github.com/reyfilosofo/renova-agent/pull/19) **open and unmerged** until the owner completes final review.

## Repository and demonstrator references

- Public source repository: https://github.com/reyfilosofo/renova-agent
- Project branch: https://github.com/reyfilosofo/renova-agent/tree/codex/nous-intelligence-rooms-build-week-2026/projects/nous-intelligence-rooms
- PR: https://github.com/reyfilosofo/renova-agent/pull/19
- Product finalization commit: 388964c8089c5db8b767904b97311bb02fa2a175
- Public deployment record commit: 9935c80e69ec80b01656a7c916a63921c3a677bc
- Primary static demo: https://nous-intelligence-rooms.edgeone.dev/
- Public static mirror: https://nous-intelligence-rooms-seresarte.netlify.app/
- Owner-only Sites mirror (NOT suitable for judges): https://nous-intelligence-rooms-2026.seresarte.chatgpt.site

The two public demo endpoints were last documented as anonymously accessible on 2026-07-28. This is historical evidence, not a new availability claim.

## External completion gates

| Gate | Status as of 2026-11-02 | Evidence needed to mark resolved |
|---|---|---|
| Live OpenAI Responses run | **PENDING**; previous attempt failed with HTTP 429 / insufficient_quota | Project quota restored; one actual successful run with model, date, HTTP outcome, locally validated JSON and sanitized trace |
| Docker | **RESOLVED IN CI on 2026-11-02** | Run 41490321825: Python suite, Docker image build and container /api/health + curated /api/analyze smoke succeeded |
| Hosted captioned video | **UNVERIFIED / URL MISSING** | Public video URL and review of audio, captions and accessibility |
| Devpost project | **UNVERIFIED / URL MISSING** | Owner-account confirmation of original entry or submission record and public link |
| Master ZIP + SHA-256 | **RESOLVED FOR AUDITED COMMIT d525f114** | Run 41490321825 uploaded artifact 13164346265 with master ZIP and SHA256SUMS.txt; digest e7cb65971075dafd8210104579be2c9a4f6c8adbbc7e4308a81bf2e2cf0dd90b and member-level integrity verified |
| Codex session/share reference (if required) | **UNVERIFIED / URL MISSING** | Actual share URL and independent accessibility check |

Validated run (34/34 tests, Docker and archive): https://github.com/reyfilosofo/renova-agent/actions/runs/41490321825

Workflow and subsequent executions: https://github.com/reyfilosofo/renova-agent/actions/workflows/nous-intelligence-rooms.yml

CI workflow artifacts expire after 30 days; download and preserve the verified package and its checksum in controlled storage when a durable archive is required. The cited digest is tied to commit d525f114051b62964909f1c15acbc2d7b7f586d1; later commits must use their own generated digest.

## Competition timing and provenance

The recorded Build Week submission deadline was **2026-07-21, 17:00 PDT**. This date is past. A post-deadline build or artifact may serve archival/product release purposes, but must not be described as evidence of an on-time Devpost submission. The owner must check their Devpost account for any pre-deadline submission and preserve that original evidence. Do not fabricate a Devpost URL or overwrite UNVERIFIED without a real, accessible destination.

## Build the master archive locally

From the project directory, execute the following commands in order:

    python3 submission/build_master_archive.py
    cd submission/dist
    sha256sum -c SHA256SUMS.txt

This creates NOUS_Intelligence_Rooms_MASTER_DELIVERY.zip and SHA256SUMS.txt; the ZIP includes a member-level MANIFEST_SHA256.txt. It excludes the generated dist directory, bytecode and real .env files. It is not the older demo-only deployment/artifacts/NOUS_Intelligence_Rooms_STATIC_DROP_DEPLOY.zip, and it is not proof of Devpost submission.
