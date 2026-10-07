# T-051 validator fixtures

The validator is deterministic and must fail closed.

## Expected PASS fixture
Export the six canonical tabs from ASSET-VAL-004 as CSV without editing. Run:
`python validate_asset_val_004.py ./canonical_csv/`
Expected: PASS, provided exported values match the frozen schema.

## Required FAIL mutations
Each mutation is tested separately and must yield FAIL:
1. Set a pilot Case_ID Confirmatory_Eligible=YES → PILOT_LEAK.
2. Set R1_Novelty_0_4=5 → SCORE_RANGE.
3. Set Abstain=YES with blank Abstain_Reason → ABSTAIN_REASON.
4. Mark ChatGPT Rater_Independent=YES → AUTHOR_INDEPENDENCE.
5. Remove Actor_Group from an R5 row → R5_INCOMPLETE.
6. Use exclusion reason ADVERSE-RESULT → EXCLUSION_REASON.
7. Set Proposed_Before_Outcome=NO → POST_OUTCOME_EXCLUSION.
8. Delete MV-028 → MULTIVERSE_IDS/MULTIVERSE_COUNT.
9. Set MV-026 Allowed=YES before numeric SESOI freeze → EXECUTABLE_BRANCH_COUNT/BLOCKED_BRANCH_SET.
10. Add RCV_Total column → AGGREGATE_SCORE_FORBIDDEN.
11. Remove DENIED gate token → GATE_TOKEN_MISSING.
12. Add rating for unknown Case_ID → ORPHAN_RATING.

A PASS is a schema/gate result only. It is not empirical validation.
