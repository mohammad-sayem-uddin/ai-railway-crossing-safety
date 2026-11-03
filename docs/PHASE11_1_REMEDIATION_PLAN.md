# Phase 11.1 — Ground-Truth Remediation Plan

**Status:** Proposed workflow only. Nothing in this document has been executed. No live record has been modified, approved, or rejected. Implementing any part of this plan is the researcher's decision.

**Depends on:** `docs/PHASE11_1_ANNOTATION_INTEGRITY_AUDIT.md` (the investigation this plan responds to), `docs/PHASE11_GROUND_TRUTH_PROTOCOL.md` (the four-state observable/unobservable/censored/uncertain taxonomy this plan reuses unchanged), `docs/PHASE11_EVALUATION_READINESS_REPORT.md` (the eligibility/censoring rules this plan does not alter).

---

## 1. Principle: additive, never destructive

Every step below creates new files or new fields; none deletes, overwrites, or silently repairs `data/ground_truth/reviews/*/event_XXX_review.json`. The 27 live records remain exactly as they are until the researcher personally decides to archive or supersede them. This phase has already produced one concrete, additive artifact consistent with this principle:

**`docs/PHASE11_1_PROPOSED_REMEDIATION_STATUS.json`** — a new, separate file mapping all 27 events to a `proposed_status: "INTEGRITY_UNVERIFIED"`, each entry carrying the live file's path, its SHA-256 at the time of this audit, and the rationale. **This file does not modify the live records it describes** (re-verified: all 27 live files are byte-identical to the Phase 11.1 preservation baseline, Section 1 of the audit document). It is a proposal the researcher may choose to act on.

---

## 2. Step 1 — Formal invalidation marker (no deletion)

**Action for the researcher to take** (not performed by this phase): create `data/ground_truth/reviews/_INTEGRITY_NOTICE.md`, a single new file in the `reviews/` directory (sibling to, not inside, the cohort subdirectories) stating plainly that every file in this directory as of 2026-10-12 is integrity-unverified per `docs/PHASE11_1_ANNOTATION_INTEGRITY_AUDIT.md`, and must not be treated as evidence of human review until superseded by a Stage-2.1 record (Section 4). This is a pure addition — it does not touch any of the 27 files, and anyone opening the directory sees the notice immediately regardless of which individual file they open next.

**Alternative, if the researcher prefers a stronger separation**: move (not delete) the 27 files to `data/ground_truth/reviews/_archived_unverified_20261012/`, preserving their original relative cohort structure, and leave `data/ground_truth/reviews/{cohort}/` empty pending genuine review. Either approach satisfies "preserve the original records and their provenance, without modifying the live records" — moving a file preserves its content byte-for-byte; this phase does not perform either action, since choosing between them, and executing the move, is a decision for the researcher, not an unprompted action for an AI assistant to take on repository state.

---

## 3. Step 2 — The new Stage-2.1 schema (genuine re-review)

A new review schema, versioned separately from the existing `schema_version: "7.0.0"` review records so the two are never confused, capturing every field the Phase 11.1 brief requires:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "review_id": "review_event_001_v2_20261101",
  "schema_version": "8.0.0-stage2.1",
  "event_id": "event_001",
  "supersedes": "data/ground_truth/reviews/train_events/event_001_review.json",
  "supersedes_sha256": "a3915f02bc56...",
  "supersedes_invalidation_reason": "INTEGRITY_UNVERIFIED -- see docs/PHASE11_1_ANNOTATION_INTEGRITY_AUDIT.md",

  "proposal_reference": {
    "proposal_file": "data/ground_truth/proposals/train_events/event_001_proposal_v6.json",
    "proposal_sha256": "<sha256 of the CURRENTLY ACTIVE proposal file -- checked by check_proposal_currency() before this record can be accepted>"
  },

  "reviewer_metadata": {
    "reviewer_id": "<the researcher's own, individually attributable identifier -- never a role label like 'human_researcher_lead'>",
    "review_session_id": "<a fresh UUID or session token per sitting, so two records can never silently share one implicitly>",
    "review_start_utc": "2026-11-01T14:02:10Z",
    "review_end_utc": "2026-11-01T14:19:47Z",
    "review_duration_s": 1057.0,
    "inspection_tool": "<the actual tool/command used, e.g. an ffmpeg invocation the reviewer ran>",
    "model_prediction_independence_attestation": {
      "attested": true,
      "statement": "I did not view, query, or condition any boundary decision on any YOLOv8n/Audio-V3/decision-engine output, prediction, or evaluation result while performing this review.",
      "attested_at_utc": "2026-11-01T14:19:47Z"
    }
  },

  "field_adjudications": {
    "<same per-field structure as the existing schema -- decision, verified value, rationale -- unchanged>"
  },

  "adjudication_status": "APPROVED | REJECTED | NEEDS_SECOND_REVIEW",
  "adjudication_history": [
    {"event": "created", "by": "<reviewer_id>", "at_utc": "2026-11-01T14:19:47Z", "status_set": "APPROVED"}
  ]
}
```

Key differences from the invalidated schema, each tied directly to a Phase 11.1 brief requirement:

| Requirement | New field(s) |
|---|---|
| Reviewer identity | `reviewer_metadata.reviewer_id` — must be an individual, not a role label; `review_session_id` additionally distinguishes separate sittings even by the same reviewer. |
| Review time | `review_start_utc` **and** `review_end_utc` (not just one instant), from which `review_duration_s` is derived — directly falsifiable against implausibly short sessions. |
| Annotation version | `proposal_reference.proposal_file`/`proposal_sha256`, validated against the *currently active* proposal (Section 5) — fixes the 27/27 stale-reference finding. |
| Media identifier/hash | Unchanged from the existing schema — already present (`proposal_reference` chains to the proposal, which embeds `input_media_files[].sha256`); re-affirmed here, not re-invented. |
| Uncertainty | Unchanged `ambiguity_flag`/rationale per boundary field (existing protocol), plus this plan's reaffirmation of the Phase 11 four-state taxonomy (Section 6). |
| Adjudication history | `adjudication_history`: an **append-only** list, never overwritten — a second review, a disagreement, or a status change all add a new entry rather than replacing the record's story. |
| Model-prediction independence | `model_prediction_independence_attestation` — an explicit, timestamped, individually-attributable statement, not merely a markdown banner the reviewer reads past. |
| Supersession chain | `supersedes`/`supersedes_sha256`/`supersedes_invalidation_reason` — makes the relationship to the invalidated record explicit and auditable, rather than silently replacing it. |

---

## 4. Step 3 — The promotion gate (specified, not implemented)

No Stage 3 promotion code exists today (confirmed in the audit, Section 3.1). This plan specifies what one **must** check before it is built, reusing the prototype safeguard this phase already wrote and tested (`src/railway_detection/annotation/integrity_safeguard.py`) rather than inventing a second mechanism:

A promotion script (future work, not built in this phase) must, for every event, before writing anything to `data/ground_truth/{train_events,no_train_events,engine_events}/`:

1. Load the Stage-2.1 review record (Section 3's schema) — **not** any `schema_version: "7.0.0"` record, which must be categorically ineligible for promotion regardless of its `adjudication_status` value, until and unless the researcher explicitly re-certifies it under the new schema.
2. Run `check_review_batch_integrity()` across the full batch being promoted (even a batch of one) — reject if any `IDENTICAL_TIMESTAMP_NO_PLAUSIBLE_DURATION` or `APPROVED_WITHOUT_PROVENANCE` violation is found.
3. Run `check_proposal_currency()` against the live `data/ground_truth/proposals/` directory at promotion time — reject if the reviewed proposal is not the currently active version for that event.
4. Verify `model_prediction_independence_attestation.attested == true`.
5. Verify `adjudication_status == "APPROVED"` **and** that no unresolved entry exists in `adjudication_history` with `status_set: "NEEDS_SECOND_REVIEW"` more recent than the final `"APPROVED"` entry (Section 5 covers the second-review flow itself).
6. Only then write the Stage 3 file, with its own SHA-256 recorded into a (also not-yet-existing) `ground_truth_manifest.json`.

Any promotion attempt failing any of 1–5 must halt with a specific, named reason (mirroring the existing `assert_proposal_approval_firewall`'s pattern of raising `SchemaValidationError` with a precise message) — never silently skip or warn-and-continue.

---

## 5. Disagreement and second-review support

For events where a genuine re-review disagrees with the (invalidated) original candidate proposal's values beyond simple acceptance/correction, or where two independent reviewers reach different conclusions:

1. The first reviewer's record is written with `adjudication_status: "NEEDS_SECOND_REVIEW"` and a `field_adjudications` entry explaining which field(s) are contested and why (e.g. an ambiguous landmark correspondence, per the Uncertain state in the Phase 11 taxonomy).
2. A second, independent reviewer (a different `reviewer_id`) produces their own complete Stage-2.1 record for the same event, referencing the first via a new `second_review_of` field.
3. If the two agree (within whatever numeric tolerance the researcher deems appropriate for annotation-level agreement — **not** the Phase 11 evaluation protocol's ±0.4s system-resolution tolerance, which is a model-evaluation concept and must not be reused here as an annotation-agreement threshold without a separately stated rationale), the second record's `adjudication_status` becomes `"APPROVED"` and both records' `adjudication_history` are updated (appended, not overwritten) to reflect resolution.
4. If they disagree beyond that tolerance, the event is marked `"DISPUTED"` and excluded from Stage 3 promotion until the researcher personally adjudicates a final value — this plan does not propose any automated tie-breaking (majority vote, averaging, or preferring either reviewer by default), since doing so would itself be a form of synthetic ground-truth generation the existing protocol already prohibits (§1.3).

---

## 6. Left/right censoring and unobservable timestamps — reused unchanged

Every Stage-2.1 record must classify every boundary field into exactly one of the four states defined in `docs/PHASE11_GROUND_TRUTH_PROTOCOL.md` Section 2 (Observable / Unobservable-Not-Applicable / Censored / Uncertain). This plan introduces no new censoring category and does not relax the existing rule that a Censored or Unobservable value must never be converted into a synthetic Observable one. The per-event censoring facts already established in `docs/PHASE11_EVENT_INVENTORY.json` (e.g. `event_005`'s right-censored $T_4$, the near-universal right-censoring of $T_{\text{scene\_clear}}$) are expected to persist through genuine re-review — a human reviewer re-watching `event_005`'s back camera will find the same recording ending at the same moment; this plan does not anticipate or require those facts to change, only the review *process* around them.

---

## 7. What this plan does not do

- Does not mark any of the 27 live records `INTEGRITY_UNVERIFIED` in place — see Section 2's two proposed options, neither executed.
- Does not invent, infer, or imply that any genuine human review occurred for any event.
- Does not auto-convert any existing `schema_version: "7.0.0"` review into the new Stage-2.1 schema — every Stage-2.1 record must be the product of an actual new review action by the researcher.
- Does not build the promotion script specified in Section 4 — it is specified, not implemented, consistent with this phase's investigation-and-plan scope.
- Does not change any eligibility, censoring, or tolerance rule from `docs/PHASE11_EVALUATION_READINESS_REPORT.md`.

---

## 8. Researcher action checklist (for execution outside this phase)

1. Decide between Step 1's notice-file or archive-and-move approach (Section 2) for the 27 invalidated records.
2. Begin genuine, individually-timestamped, individually-attributed re-review of all 27 events using the Stage-2.1 schema (Section 3), starting wherever priority dictates (e.g. the 11 R04-validated events first, if Phase 12 work depends on them).
3. Implement the promotion gate (Section 4) as real code, with tests, before any Stage 3 file is ever written.
4. Only after genuine Stage-2.1 `"APPROVED"` records exist and pass the promotion gate: generate `ground_truth_manifest.json` and populate `data/ground_truth/{train_events,no_train_events,engine_events}/`.
5. Only then does `docs/PHASE11_EVALUATION_READINESS_REPORT.md`'s evaluation protocol become applicable to real, approved ground truth.

---

## 9. Document change log

- **v1.0.0 (2026-10-14):** Initial Phase 11.1 remediation plan. Proposes the Stage-2.1 schema, the promotion-gate specification, disagreement/second-review handling, and reaffirms the Phase 11 censoring taxonomy unchanged. No part executed.
