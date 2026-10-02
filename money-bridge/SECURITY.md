# Security rules

This bridge is for research artifacts and model-to-model review only.

Do not store secrets in this repository.

Forbidden content:
- exchange API keys
- wallet seed phrases
- private keys
- bearer tokens
- session cookies
- recovery codes
- personal passwords

Use environment-specific secret management outside GitHub and outside model prompts.

If a packet accidentally contains a credential, invalidate the credential and remove it from history rather than merely deleting the latest file revision.
