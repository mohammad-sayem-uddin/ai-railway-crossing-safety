# Phase 11.3 — Annotation Review Workflow

**Status:** Documented, not yet operational. **This workflow is NOT ready for production review** until Decisions 1, 2, and 3 in `docs/PHASE11_3_RESEARCHER_DECISIONS.md` are resolved — see the readiness note at the end of each affected section below. No event has been assigned, reviewed, approved, or promoted by this phase.

**Implements, operationally:** the Stage-2.1 schema and promotion gate (`src/railway_detection/annotation/stage2_1_schema.py`, `promotion_gate.py`, Phase 11.2) and the four-state censoring taxonomy (`docs/PHASE11_GROUND_TRUTH_PROTOCOL.md` Section 2).

---

## 1. Event-by-event assignment and reviewer attribution

**Inventory:** `docs/PHASE11_3_REVIEW_INVENTORY.json` / `.csv`, 27 events, `assigned_reviewer: null`, `review_status: "NOT_STARTED"` for every one — this phase assigns nothing.

**Procedure once Decision 2 (reviewer authorization) is resolved:**
1. The researcher assigns each event to a specific, individually-attributable reviewer (never a role label — rejected outright by `REVIEWER_ID_BLOCKLIST`), recording the assignment by updating `assigned_reviewer` in the inventory.
2. Each assignment is one event to one reviewer for the first pass. Whether any event requires a second, independent reviewer by default is Decision 3 (Section 1, part a) — **not resolved**, so no assignment plan in this document assumes an answer.
3. A reviewer must not review an event already carrying a completed (non-`NOT_STARTED`) Stage-2.1 record from a different reviewer without it being an explicit, intentional second review (`second_review_of` set) — never an accidental duplicate.

**Readiness note:** assignment cannot proceed in production until Decision 2 (how reviewers are registered/authorized) is resolved — without it, there is no principled way to decide who is eligible to be assigned.

---

## 2. Access to source footage and the correct proposal version

- Raw footage: `data/raw/layer_b/v2/{cohort}/{event_id}/camera_front.mov` and `camera_back.mov` — paths and independently-verified SHA-256 hashes for all 27 events are in `docs/PHASE11_3_REVIEW_INVENTORY.json`'s `raw_media` field (sourced from `data/manifests/layer_b_v2_annotation_inventory.json`, itself spot-verified against the raw files in Phase 11).
- **Correct proposal version**: the inventory's `active_proposal_file` field names the CURRENTLY ACTIVE (highest-numbered) proposal for each event, resolved fresh by this phase's generation script — directly addressing the Phase 11.1 finding that all 27 legacy reviews referenced a superseded version. A reviewer must open exactly this file, not an older `_v1`/`_v2`/etc. version found by browsing the directory.
- The proposal is Stage 1 evidence — an AI-drafted candidate the reviewer inspects, corrects, or rejects, never one the reviewer accepts without independently re-examining the footage (per the existing three-stage lifecycle, `docs/FINAL_GROUND_TRUTH_PROTOCOL.md` §1.1, unchanged by this phase).

---

## 3. Independent annotation without model predictions

- The reviewer must not view, query, or condition any boundary decision on any YOLOv8n/Audio-V3/decision-engine output, prediction, Phase 8–10.1 result, or evaluation report, per the existing firewall (`docs/FINAL_GROUND_TRUTH_PROTOCOL.md` §1.2) — unchanged, reaffirmed.
- Every Stage-2.1 record must carry a completed `model_independence_attestation` (`attested: true`, a specific non-boilerplate statement, a timestamp) — enforced by the schema itself (`ModelIndependenceAttestation.__post_init__`, Phase 11.2); a record without it fails to construct at all.

---

## 4. Recording uncertainty, censoring, and unobservable boundaries

Every boundary ($T_0$–$T_4$, $T_{\text{scene\_clear}}$) must be classified into exactly one of the four states from `docs/PHASE11_GROUND_TRUTH_PROTOCOL.md` Section 2, now enforced as a formal schema field (`BoundaryAdjudication.state`):

| State | Use when | Schema requirement |
|---|---|---|
| `OBSERVABLE` | The boundary is directly visible/audible at an identifiable frame. | `value_s` and `reference_camera` (`front`/`back`) required. |
| `UNOBSERVABLE_NOT_APPLICABLE` | The concept does not apply to this event type (e.g. train-boundary markers on a no-train recording). | `value_s` must be `None`. |
| `CENSORED` | The boundary genuinely occurred, or would occur, outside the recorded window (left- or right-censored). Never estimate or interpolate a value. | `value_s` must be `None`; `rationale` required, stating which direction and why. |
| `UNCERTAIN` | The boundary is nominally within the window but visually/acoustically ambiguous (occlusion, poor lighting, ambiguous landmark correspondence). | `rationale` required, describing the specific ambiguity. |

A reviewer must never force a numeric value where the footage does not support one, per the Phase 11.3 brief's explicit instruction, reaffirming `docs/PHASE11_GROUND_TRUTH_PROTOCOL.md` Section 2's hard rule.

---

## 5. Review completion and disagreement handling

- A review session is **completed** when `review_end_utc` is recorded and exceeds `review_start_utc` by at least `MIN_PLAUSIBLE_REVIEW_DURATION_S` (currently 30.0s, **Decision 1, pending** — see Section 1 of the decisions register; this floor may change).
- **Approval** (`adjudication_status: "APPROVED"`) is a separate, later step from completion — a reviewer can complete a session and still mark the event `NEEDS_SECOND_REVIEW` or `DISPUTED` rather than `APPROVED`, if their own review surfaces genuine uncertainty requiring a second opinion.
- **Disagreement**: if a second, independent review of the same event reaches different boundary values, the event is `DISPUTED` until the researcher personally adjudicates a final value — **no automated resolution (averaging, majority vote, or defaulting to either reviewer) exists anywhere in this codebase**, confirmed by `test_no_automated_tie_breaking_function_exists` (Phase 11.2) and re-confirmed this phase (Section 5 below).
- `adjudication_history` must be appended to, never overwritten, at every status change — enforced by the schema's chronological-order and status-consistency checks.

**Readiness note:** disagreement handling cannot proceed in production until Decision 3 (when a second reviewer is required, and what numeric tolerance if any defines "agreement") is resolved.

---

## 6. Required provenance and media-hash checks

Every record intended for promotion must pass `validate_for_promotion()` (`promotion_gate.py`), which requires, at minimum:
- Schema version exactly `"8.1.0-stage2.1"` (any other version, including all 27 legacy records and the superseded `"8.0.0-stage2.1"` format, is rejected outright). Updated in Phase 11.8 to reflect the Phase 11.7 schema bump adding `reviewer_observed_media_hashes`.
- A proposal reference matching the CURRENTLY ACTIVE proposal version at promotion time (not just at review time — a proposal could in principle be revised between review and promotion; the gate always checks against the live state).
- A complete `media_sha256_registry` entry (`front` and `back`) for the event — **the exact verification depth (manifest-trust vs. fresh re-hash) is Decision 4, pending.**
- A resolved (`APPROVED` or `REJECTED`, never `NEEDS_SECOND_REVIEW`/`DISPUTED`) adjudication status.
- No `invalidation` marker present.

**Readiness note:** promotion itself can be exercised today against synthetic data (and is, in Phase 11.2's test suite), but should not be run against real review output in production until Decision 4 is resolved, since the appropriate media-hash verification depth affects what "passing" the gate actually certifies.

---

## 7. Conditions under which an annotation remains ineligible for promotion

Exhaustive list, matching `promotion_gate.py`'s rejection codes exactly:

| Condition | Code |
|---|---|
| Wrong or legacy schema version | `LEGACY_OR_UNKNOWN_SCHEMA` |
| Explicit invalidation marker present | `RECORD_INVALIDATED` |
| Any schema-level defect (missing field, blocklisted reviewer ID, implausible session duration, failed/boilerplate attestation, malformed boundary state, malformed or inconsistent adjudication history) | `SCHEMA_VALIDATION_FAILED` |
| References a proposal version that is not currently active | `STALE_PROPOSAL_REFERENCE` |
| No media hash registry entry for the event | `MISSING_MEDIA_IDENTITY` |
| Media hash registry entry missing a camera | `INCOMPLETE_MEDIA_IDENTITY` |
| Status is `NEEDS_SECOND_REVIEW` or `DISPUTED` | `UNRESOLVED_DISAGREEMENT` |
| Status is `REJECTED` (a final, resolved, but non-approving outcome) | `NOT_APPROVED` |
| Batch shares an implausible timestamp pattern with other records being promoted together | `BATCH_IDENTICAL_TIMESTAMP_NO_PLAUSIBLE_DURATION` / `BATCH_APPROVED_WITHOUT_PROVENANCE` |

An event failing any of these remains ineligible for promotion regardless of how confident the reviewer or researcher is about its content — the gate does not accept an override.

---

## 8. Overall readiness note

This workflow is procedurally complete but **operationally blocked** pending Decisions 1–3 (Decision 4 is less blocking but should be resolved before real promotion). No event in `docs/PHASE11_3_REVIEW_INVENTORY.json` has been assigned, and none should be, until those decisions are recorded with an actual selected option (not `PENDING_RESEARCHER_DECISION`) in `docs/PHASE11_3_RESEARCHER_DECISIONS.md`.

---

## 9. Document change log

- **v1.0.0 (2026-10-14):** Initial Phase 11.3 review workflow. Documents assignment, access, independence, censoring, completion/disagreement, provenance, and ineligibility conditions. Explicitly marked not production-ready pending open decisions.
