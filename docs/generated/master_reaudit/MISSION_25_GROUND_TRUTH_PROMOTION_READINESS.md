# Mission 25 — Ground-truth promotion readiness

Prepared 2026-11-05, America/New_York. Metadata/software infrastructure only; no genuine reviewer, observation, adjudication, source access or promotion established.

| Status | Meaning |
|---|---|
| CONSTRUCTED_NON_PROMOTABLE | Any fixture, irrespective of software completeness. |
| INCOMPLETE_REVIEW_BATCH | Missing complete review, current qualified authorization, second review or unresolved required resolution. |
| REVIEW_COMPLETE_PENDING_VERIFICATION | Structurally complete but source/protocol/schema/boundary/history/lineage/human/signoff verification missing. |
| PROMOTION_ELIGIBLE_PENDING_AUTHORIZATION | Genuine verified complete metadata; separate exact current promotion authorization and receipt still required. |
| PROMOTED_WITH_VALID_RECEIPT | An externally supplied receipt has passed complete-content, issuer, current authorization and authentic receipt verification. This validator never issues it. |

Readiness reports precise event-level missing reasons. Source identity and human statements are rechecked through the external verifier; protocol/schema/boundary adoption, canonical-schema acceptance, immutable-history attestation, lineage and batch signoff bind the exact complete history. Permissions are checked at use, including expiry/revocation, actor, purpose/environment and batch/event/operation scope. No unknown fact becomes zero or an approval flag.

Receipt validation binds batch digest, history digest, complete object digest, lineage, issuer and authorization reference. All batch events must be covered. Exact duplicate validation is idempotent; substituted IDs or another receipt for the published batch refuse. No live issuer/publisher implementation is enabled. PROMOTED_WITH_VALID_RECEIPT describes authenticated external publication evidence, not an agent-created promotion.

Existing promotion_gate.py, canonical receipt guards, source hashing requirements and active schema validators remain intact. Constructed records cannot enter them as genuine evidence. Live durable intake, schema compatibility acceptance and create-only authenticated publication must be connected and tested with actual evidence before real operation. All genuine-positive promotion behavior remains unexecuted; constructed negatives prove refusal only.
