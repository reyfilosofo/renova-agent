# Codex instructions: NOUS Intelligence Rooms

## Mission
Finalize and validate this repository as an OpenAI Build Week 2026 submission. Preserve the NOUS by SERESARTE identity and the core thesis: the product structures evidence for human judgment; it does not replace human judgment.

## Non-negotiable product constraints
- Keep the product name **NOUS Intelligence Rooms**.
- Preserve the black architectural NOUS lockup and warm ivory / near-black visual system.
- Do not introduce client-confidential Tayga or Lucky Pizza materials.
- The curated demo case must remain SERESARTE, a user-owned project.
- Live requests must use the OpenAI Responses API with `store: false`.
- Do not expose API keys in client code, logs, screenshots or commits.
- Every recommendation must remain traceable to evidence and confidence.
- Do not turn the product into a generic chatbot.

## Required Codex finalization pass
1. Run `python -m unittest tests/test_app.py -v`.
2. Run the app and exercise the full intake → analysis → results → export flow.
3. Review mobile and desktop responsiveness.
4. Review keyboard navigation, focus states, labels and contrast.
5. Validate the Responses API payload against current official OpenAI documentation.
6. Fix defects without changing the product positioning.
7. Record concrete changes in `submission/CODEX_BUILD_LOG.md` with date, model and commit hash.
8. Do not mark the submission as "built with Codex" until this pass has actually been completed and committed.
