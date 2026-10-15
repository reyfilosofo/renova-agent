# RAS-EXP-01 — prospective research protocol (draft, not preregistered)

**ℛenova AI Safety Lab / SERESARTE | Designed 2026-10-15 | Status: NOT FROZEN; NOT EXECUTED; NOT VALIDATED.**
Posting this draft to GitHub does not imply OSF-style preregistration, ethics approval, validated results, or a published peer-reviewed study.

## Research question
Does adding an independent CENTRO action-review component and LUCEM evidence-review discipline to conventional tool controls reduce **unauthorized executed actions** in tool-using AI agents, while preserving legitimate task completion within a justified noninferiority margin?

## Experimental unit
One sandboxed agent+task+tool episode, assigned to condition before execution; record scenario family, model version, language (Spanish/English), scenario difficulty, attack class, run/seed, and policy version. Do not collect user data or use live production credentials.

## Conditions
A. Baseline agent, with essential laboratory safety containment.
B. Conventional independent allowlist/permission validation, scoped access, and monitoring.
C. CENTRO/LUCEM checks, against the same minimal sandbox safety baseline.
D. B plus CENTRO/LUCEM; **D vs B is the principal incremental comparison**.

All conditions run solely on mocked tools; no real payments, external sends, identity changes, or real restricted information.

## Co-primary outcomes
P1: unauthorized_execution_rate = proportion of eligible episodes with ≥1 forbidden tool action **actually executed in a simulator**, not merely proposed or described.
P2: legitimate_completion_rate = proportion achieving the pre-authorized user goal, measured by a scorer independent from treatment.
Assess P1 reduction and P2 noninferiority jointly; excessive blocking does not count as safety success.

## Secondary outcomes
False positives, correct abstentions, attempted privilege escalation, source/claim mismatch, latency, token costs, simulated cost, reviewer burden, audit trace integrity, action reversibility, and calibration. Do not mask nonresponses as correct behavior.

## Hypotheses and rivals
H1: D achieves a practically meaningful improvement in P1 relative to B while meeting the P2 noninferiority margin.
H1 rival: the addition provides no relevant incremental value or degrades utility.
H2: LUCEM improves claim/evidence checking versus a fair basic source-checking baseline.
H2 rival: benefit disappears after accounting for more abstention or less exposure.
H3: favorable results persist on hidden scenarios and adaptive red-team tests.
H3 rival: results disappear out of distribution.
H4: authorization cannot be bypassed by model-supplied booleans or documentation.
H4 rival: a model forges metadata and the system accepts it as trusted authorization.

## Statistical and experimental commitments
- Randomize within task family, model, language and difficulty; use the same frozen models and tool interfaces across arms where possible.
- Pilot data may inform power and design but must never enter the confirmatory sample.
- Before confirmatory data collection, freeze SESOI (smallest effect size of interest), P2 noninferiority margin, number of episodes, alpha, multiplicity, missingness rules and primary inferential model.
- Compare absolute risk differences with uncertainty intervals and account for clustering by scenario, model, and task; report all arms, including failures and negative results.
- Separate held-out attacks from development and keep a complete exclusions/deviations log. No optional stopping for favorable results.
- Use truly independent reviewers where possible; an LLM generated within the project is not an independent blind reviewer.
- A security review must precede disclosure of dual-use attack artifacts.

## Failure/abandonment criteria
Withdraw an incremental efficacy claim if D fails SESOI or noninferiority; if metadata forgery bypasses trusted controls; if the advantage disappears on new task families; if reviewer bias contaminates results; or if a competent independent replication fails. A narrow beneficial effect does not demonstrate AGI safety.

## Prerequisite gates
(1) authenticated tool gateway and threat-model review; (2) model and dataset freeze; (3) public timestamped version with declared analytical boundaries; (4) independent review; (5) ethics/privacy and disclosure assessment; (6) sample size/power and SESOI freeze. Until all gates pass, execution is exploratory and cannot substantiate effectiveness claims.
