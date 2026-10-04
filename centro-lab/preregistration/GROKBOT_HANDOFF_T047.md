# GROK / GROKBOT HANDOFF — T-047

Project: CENTRO — ℛenova Multi-Intelligence Laboratory
Date: 2026-10-04
Protocol: FAL-01 × RCV-EXP-01 v1.0
Canonical Drive ID: 1tQ41Q43ZLr6Q6ld7wv-kXuw661YAX8tcbFilp67hOFg
Status: BLOCKED-EXTERNAL until an actual external output is preserved.

## Exact task
You are an independent adversarial reviewer for CENTRO — ℛenova Multi-Intelligence Laboratory. Review FAL-01 × RCV-EXP-01 preregistration v1.0 without trying to make ℛenova succeed. Do not rewrite it stylistically.

Identify:
1. hidden researcher degrees of freedom;
2. circular definitions;
3. hypotheses that cannot actually fail;
4. weak or unfair rival hypotheses;
5. outcomes vulnerable to generic positivity/novelty bias;
6. missing negative and positive controls;
7. leakage between pilot and confirmatory sets;
8. SESOI and stopping-rule defects;
9. failure modes in R5 harm accounting;
10. conditions under which the entire construct should be abandoned.

For every criticism give:
- severity: CRITICAL / HIGH / MEDIUM / LOW
- exact clause affected
- concrete repair
- whether repair must occur BEFORE DATA

Separate peer-reviewed/primary evidence from preprints, opinion and your own inference. Do not treat agreement with ChatGPT as corroboration.

Return:
A. human-readable adversarial review
B. machine-readable JSON:
```json
{
  "run_id": "RUN-20261004-T047-GROK-ADVERSARIAL-V01",
  "model": "",
  "version": "",
  "date_time": "",
  "verdict": "PREREGISTERABLE|PREREGISTERABLE-WITH-REPAIRS|NOT-PREREGISTERABLE",
  "criticisms": [
    {"severity":"","clause":"","problem":"","repair":"","before_data":true,"evidence_status":"","sources":[]}
  ],
  "abandonment_conditions": [],
  "claimed_sources": []
}
```
End with one verdict only: PREREGISTERABLE / PREREGISTERABLE-WITH-REPAIRS / NOT-PREREGISTERABLE.

## Inputs
- centro-lab/preregistration/FAL01_RCV_EXP01_PREREG_v1.0.md
- Drive ASSET-OBS-029
- Drive ASSET-OBS-030
- CENTRO MULTI-AI PROMPT PACK v1.0

## Preservation contract
Do not edit the frozen protocol. Save raw output separately at:
centro-lab/preregistration/external/grok/RUN-20261004-T047-GROK-ADVERSARIAL-V01.md

Preserve exact model/version/date/settings, full raw response and all claimed sources. External model output is RAW, never scientific evidence by itself, and cannot become CANONICAL until independently verified.
