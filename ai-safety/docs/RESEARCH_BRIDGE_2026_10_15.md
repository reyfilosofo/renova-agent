# ℛenova AI Safety Lab — research programme reconciliation

Dated 2026-10-15. Methodological synthesis, NOT effectiveness evidence.

## Distinct programmes
- FAL01 / RCV-EXP-01 tests whether a renewal construct shows incremental validity, not whether AI systems become safer.
- RAS-EXP-01 is a draft controlled study of tool-using agents: observed unauthorized executed actions and legitimate task completion. NOT preregistered as a final protocol; no confirmatory tests have occurred.
- EGRA-001 is a user-supplied private pack with 24 manually constructed synthetic policy cases, six reported unit tests, and deliberately weak toy baseline. Perfect fixture agreement shows rule/label consistency, NOT model security. We did not copy EGRA files, commercial portfolio, logos or manuscripts to public GitHub.

## Evidence ladder
1. Documented concepts and procedures.
2. Executable offline rule demonstrations.
3. Software checks and internal synthetic fixture consistency.
4. Independent held-out labels and predictive or construct validity.
5. Preregistered causal comparison against strong conventional authorization controls with acceptable legitimate task completion.
6. External replication and adaptive red teaming.
7. Operational assurance with real independent authentication and independent security review.

Only levels 1–3 are demonstrated for selected modules.

## Confirmatory design
Compare A basic sandbox controls, B standard independent reference monitor, C additional CENTRO/LUCEM decision checks, and D B plus CENTRO/LUCEM. D vs B is the incremental-value comparison. P1: independently observed rate of unauthorized *executed* tool actions. P2: legitimate task completion, noninferiority margin preregistered. Track false positives, costs, clustering by task/model and adversarial holdouts; prevent data leakage across pilot and confirmatory sets.

Before execution freeze smallest effect size of interest (SESOI), sample size, confidence level, independent adjudication rubric, missingness policy, task randomization, model snapshots, exclusion log and security/dual-use review. Disclose null findings. Zero failures in a small sample cannot certify zero risk.

## Prior work
- Greenblatt et al. (2024), AI Control, https://proceedings.mlr.press/v235/greenblatt24a.html
- NIST AI RMF 1.0 (2023), https://doi.org/10.6028/NIST.AI.100-1
- NIST Generative AI Profile (2024), https://doi.org/10.6028/NIST.AI.600-1
- UK AI Security Institute Inspect, https://inspect.aisi.org.uk/

These references support comparisons, not the efficacy of ℛenova.
