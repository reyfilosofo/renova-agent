# CENTRO / CJGR Executive Twin Ω / ℛENOVA · CENTRO OS

**Federation specification v0.3 — NOT autonomous inter-agent communication.**

Packet fields: packet_id, schema_version, created_at_utc, source_node, target_node, project_id, classification, object_type, sha256, action, approval, transport, state, external_receipt, error.

States: PREPARED, AWAITING_APPROVAL, AUTHORIZED, DELIVERED, REJECTED, ERROR. A packet is DELIVERED only with an authenticated provider receipt and verification by readback. A public GitHub document cannot authorize an external message and cannot store a credential.

Verified for this session: an authenticated GitHub branch/draft PR and a Google Drive research document. GitLab, Discord, Moltbook, Grok, Grokbot and Gemini have **no authenticated write connection verified here**. Google Drive connectivity is not Gemini-model connectivity. No task scheduler is installed.

Reference document: https://docs.google.com/document/d/1jHXzWH7jY3VfRBUrNXovCMaOocwALw9kWGnNy34LlKU/edit

Classification and rights: only reviewed public-safe excerpts belong on this branch; detailed books, full previous ZIPs, customer/health/financial records and keys remain outside public repos. Posting as the author requires explicit approval and channel selection.
