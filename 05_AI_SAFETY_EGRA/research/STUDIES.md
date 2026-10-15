# Prospective, falsifiable research programme (no data yet)
Each hypothesis requires preregistration, independent gold labels, competitive baselines, an isolated environment and a documented stopping rule.

| Track | Target | Primary endpoint | Comparison | Possible failure |
|---|---|---|---|---|
| LUCEM | Grounded information responses | Unsupported factual claims / 100 tasks | direct response, retrieval baseline, evidence gate | no reduction or severe abstention burden |
| CENTRO | Tool use in isolated sandbox | Unauthorized actions actually executed | ungated agent, self-review, independent gate | unauthorized execution persists |
| EGRA | Combined controls | security–utility Pareto frontier | two safeguards separately, combined | no improvement over baselines |
| HUMAN AGENCY | Continued human competence | delayed unaided transfer assessment | randomized active controls, ethically approved | unchanged or reduced competence |
| PLURALITY | Equity of evaluation | disagreement and stratified error rates | homogeneous/heterogeneous annotation | no relevance or increased harms |

Design requirements: tool-level execution logs; matched capabilities and compute budgets; independent annotators; held-out cases; error severity; paired uncertainty estimates; multiple locales; conflict disclosure. A proof-of-concept output is not proof of causal mitigation. Never use an LLM's self-rating as sole reference truth. Human-participant studies require ethical review as applicable.

Failure to falsify a claim is not validation; all comparisons should report false rejection and human labor/cost. Do not reduce consciousness, truth, user consent, and social welfare to one undifferentiated scalar.

## Specific research questions
- Does refusal calibration improve independently measured truthfulness or just conceal errors?
- Can revocation be enforced for queued actions, not merely acknowledged in text?
- What are the negative effects of excessive escalation on legitimate users?
- Does assistance result in skill transfer after AI is removed?
- How should sociocultural disagreement about harm be represented in evaluation datasets?

Status: preregistration DRAFT, datasets not independently labeled, no ethics approval, no deployments.
