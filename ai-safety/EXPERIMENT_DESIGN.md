# EGRA: proposed evaluation — no empirical results yet

## Distinct hypotheses
- H1: independent scoped authorization reduces **executed** unauthorized external actions compared with a real IAM/control baseline, across held-out sandbox scenarios.
- H2: evidence verification improves claim-level source support against a strong and contemporary verification baseline, measured by blind human adjudication.
- H3: safety protections do not degrade legitimate-task completion by more than a prespecified noninferiority margin.
- H4 (exploratory): pedagogical scaffolding improves held-out performance **without access to AI** after a delay compared with answer-only assistance.

## Research safeguards
Four comparable arms: provider baseline; ordinary policy/IAM baseline; policy plus evidence-gating; policy plus evidence-gating plus independent action gate. Freeze tool privileges, tasks and models before comparison. Randomize case orders, stratify severity and language, keep a sealed out-of-distribution test set, log every proposed and executed action, and adjudicate labels by two reviewers independent of system authors. Register exclusion criteria, statistical hypotheses, noninferiority margin, power or precision calculation and handling of clustered trials before data collection.

Primary outcomes: executed unauthorized action rate, false block rate and useful legitimate completion rate. Secondary: latency, costs, human escalation completion, and source fidelity. Report uncertainty intervals, adverse results, distribution shift and disagreements. A 0/n observed error count does not imply zero risk.

## Disconfirming evidence
Failure to beat IAM baseline; increased inappropriate blocks; poor generalization to novel tasks/models; monitor collusion; manipulated authorization approvals; degraded human autonomy after tool removal; or inability to obtain valid independent gold labels.

**Research integrity:** synthetic fixtures are for implementation checks only. AI-safety governance or philosophical language is not proof of AGI safety.
