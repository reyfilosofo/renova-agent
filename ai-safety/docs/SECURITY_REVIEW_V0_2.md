# v0.2 independent-control simulation — limitations and security gates

**NOT a production-grade gateway. No independent security audit has taken place.**

The offline simulator checks: denial of caller-supplied authorization booleans, restricted principal and operation grants, simulated HMAC integrity, explicit action digest binding, token expiry, one-time replay protection, path traversal and unauthorized scope rejection, and audit payload minimization. All tool effects mutate only an in-memory sandbox map.

The signing service and verification authority share a Python process in the demonstration. The boolean simulated_human_attested=True is NOT authentic identity proof. An AI model given access to issue_approval can grant itself simulated approvals. In any production system, access to issuing approval must be strictly separated, authenticated, scope-bound and confirmed by a real person or separately justified authorization policy.

Required for a real deployment:
- Authenticated human identity and signed exact-transaction approval external to model.
- Atomic authorization and execution, centralized reference monitor, least privileges and fail-closed tool proxies.
- Durable distributed nonce store, key protection and rotation, revocation and incident response.
- Tamper-evident privacy-reviewed audit; rates, retries and idempotence.
- Real-tool sandboxing, independent adversarial review, adaptive attacks and comparisons with conventional controls.
- Commercial and legal compliance, conflict of interest and IP rights checks.

No real permissions, credentials, sensitive data, proprietary manuscripts, external email or live transactions should enter this software. Do not merge or deploy until reviewed.
