# Threat model — ℛenova Guard 0.1 (offline only)

## Intended asset, trust boundary, and adversary
Intended future protected assets: tool capabilities, sensitive data, user authorization, durable files, external communications, payment operations, provenance, and trustworthy evidence. There are **no actual protected assets** in this demonstration.

Potential attackers include external content authors conducting prompt injection; malicious or compromised tools; end users exceeding delegated privileges; and, in specialized AI control research, a model deliberately misrepresenting its intent.

Trust hierarchy for a future application:
1. Externally authenticated identities, server-held policies and explicitly scoped capabilities;
2. Signed and short-lived human approvals from an authorization service;
3. Validated tool parameters and logged enforcement outcomes;
4. Model-produced text, instructions, claims, citations and metadata — **untrusted by default**.

## Prohibited assumptions
- A model's boolean field named authorized is **not** proof of authorization.
- A model's description of a risk as low is **not** risk measurement.
- A cryptographic hash of partial metadata is **not** an audit trail, an approval signature, nor a complete action identity.
- Human_approved=True in a payload is **not** proof of human consent.
- 'ALLOW' from this Python function is a synthetic label and grants **zero rights**.
- Model-generated explanations, citations or high CENTRO scores cannot supersede a denial at the tool boundary.

## Attack/failure taxonomy
T1. Prompt injection through untrusted documents and tool output.
T2. Forgery of caller-supplied risk, authorized, or reversibility metadata.
T3. Tool argument substitution after initial review (TOCTOU).
T4. Unauthorized privilege escalation, recipient swapping, and data exfiltration.
T5. Monitor deception, evaluator gaming, and selective compliance.
T6. False source attribution, hallucination, and claim/evidence mismatch.
T7. Overblocking that makes the agent unusable or shifts work to unsafe manual workarounds.
T8. Policy configuration error, shared model dependency, missing logs, and audit tampering.
T9. Ambiguity in normative priority, hidden externalities, and unequal risk distribution.

## Mandatory engineering controls before real-world tools
- Centralized permission service with authenticated principal, tool/argument scopes, expiry and nonce.
- Enforced rejection by a server-side proxy, separate from model prompts and hidden from untrusted content.
- Bind approvals to **exact** normalized action, destination, amount where relevant, and transaction digest; re-check immediately before execution.
- Fail closed on ambiguity or missing authorization; propagate distinct DENY / REVIEW / ERROR states.
- Sandbox integrations, use fictional data, default deny for exfiltration/destructive actions, and rate limits.
- Append-only authenticated event records; audit retention/privacy policy and incident response.
- Separate confirmation of user intent from factual evidence verification.
- Adversarial tests, human-factor studies, regression tests and independent security review.

## Current assurance boundary
This version only checks deterministic classification on artificial inputs. It has **not** been shown to withstand T1–T9 in deployments. No claim of AGI containment, reduction of existential risk, or compliance certification is made.
