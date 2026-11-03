# Proposed Stage-2.1 Schema and Review-Governance Preparation (RD-012, 013, 042–048)

> **PROPOSED — INACTIVE — NOT APPROVED — NOT AUTHORIZATION TO REVIEW.** No review record, reviewer identity, signature or pilot exists or was created. The historical schema `8.1.0-stage2.1` (`stage2_1_schema.py`) and all legacy records are unchanged. No review may be conducted under this schema.

## 1. The proposed schema (`src/railway_detection/annotation/stage2_1_schema_proposed.py`)
Version string `8.2.0-stage2.1-proposed` — it can never satisfy the active `8.1.0-stage2.1` requirement. No gate, loader, promotion or readiness code imports it (asserted by a test).

| Concept | Representation |
|---|---|
| Boundary states | `OBSERVABLE`, `UNCERTAIN`, `CENSORED`, `NOT_OBSERVABLE` (+ `not_observable_reason`: `not_applicable_for_cohort` \| `not_visible_in_recording` \| `landmark_not_defined`). *Legacy mapping:* `UNOBSERVABLE_NOT_APPLICABLE` splits into `NOT_OBSERVABLE` with a reason. |
| Censoring | `censoring_direction` `LEFT`/`RIGHT`, **required** iff `CENSORED` (today it lives only in free-text rationale) |
| Timestamp uncertainty | `timestamp_uncertainty_s`, nullable. **Review tolerance is DEFERRED (RD-012)** — `None` is valid; no default value exists |
| Onset provenance | `onset_provenance{basis, landmark_description}` on T1/T2 only; `OBSERVABLE` T1/T2 requires a human visual landmark; replay-/first-blocked-/model-derived bases are rejected |
| Direction | per-event `DirectionObservation`; a value only when `OBSERVABLE`; never copied from candidates (RD-010) |
| Reference camera, frame index, rationale, evidence status | `reference_camera` (`front`/`back`), `frame_index`, non-empty `rationale`, `evidence_status` (`PRESENT`/`MISSING`/`INSUFFICIENT`) |
| Reviewer identity / status | `reviewer_id` supplied by the caller (never defaulted); `review_status` ∈ `DRAFT, SUBMITTED, NEEDS_SECOND_REVIEW, DISPUTED, ADJUDICATED_UNCERTAIN, ADJUDICATED_RESOLVED` — **no `APPROVED`/`PROMOTED` value exists** |
| Independence | one `FIRST` and optionally one `SECOND` entry, distinct reviewers, each with its own observations and a canonical `entry_sha256`; a mismatch is rejected |
| Adjudication | separate `AdjudicationEntry` referencing entry hashes; may only resolve to `OBSERVABLE` (with value) or `UNCERTAIN`; never rewrites reviewer observations (tested) |
| Identity | `event_id` must be cohort-qualified and match `cohort` |

The physical entry landmark stays free text and **deferred (RD-006)**.

## 2. Review-governance preparation (all proposals)

| Decision | Prepared position | State |
|---|---|---|
| RD-013 blind first pass | For the pilot, T1/T2/T4 first-pass observations are made **without** candidate annotations; candidates may be compared afterwards (`blind_first_pass=True` flag on the entry) | proposal |
| RD-042 external audit | Prefer an independent external audit reviewer for a sample *if one can be appointed*; **no identity is named or added**; the allowlist (`authorized_reviewers.json`) is unchanged | pending identity |
| RD-043 second-review triggers (risk-based, mandatory) | (1) explicit `DISPUTED`/`NEEDS_SECOND_REVIEW`; (2) any `UNCERTAIN` boundary; (3) engine-event T3/T4 interpretation; (4) front/back conflict; (5) missing/inconsistent media hashes; (6) a boundary corrected from a candidate. `CENSORED` alone and `NOT_OBSERVABLE` alone are not triggers | proposal; register id `GOV-REVIEW-SECOND-REVIEW-TRIGGERS` PENDING |
| RD-044 clear-boundary audit | Risk-based sampling criteria (e.g. boundaries near occlusion/low contrast, first-time landmark use, reviewer-corrected values); **no fixed percentage is set** | proposal; `GOV-REVIEW-CLEAR-BOUNDARY-AUDIT` PENDING |
| RD-045 disagreement | Researcher may adjudicate through a separate recorded entry; unresolved stays `UNCERTAIN`; original observations immutable | encoded in schema |
| RD-046 review-duration floor | **Deferred** until pilot timing exists (flat 30 s floor stays) | deferred |
| RD-048 boundary priority | T1/T2/T3/T4 prioritized; horn truth only if acoustic analysis will be reported | proposal |
| RD-050 media access | **Prohibited** in this mission; authorization is a future mission | prohibited |

## 3. Hard-case pilot proposal (RD-047) — NOT executed, NOT authorized
The earlier pilot sheet (`train_events/event_001`, `no_train_events/event_001`, `engine_events/event_001`) contains no hard case. Candidates for the researcher to choose from, selected **from existing documents only** (no media inspected):

| Candidate | Why (source, second-hand) | Hard-case type |
|---|---|---|
| `train_events/event_005` | documented dual-ended censoring: front T1/T2 left-censored, back T4 right-censored [`DATASET_ANNOTATION_QUALITY_AUDIT.md`] | likely censored |
| `train_events/event_021` | documented night conditions; small distant object makes T4 ambiguous [`PHASE11_4_FINAL_VIDEO_ANNOTATION_AUDIT_REPORT.md`] | night |
| `engine_events/event_001` | `T3 ≡ T4` special interpretation; mandatory second-review trigger (3) | engine edge case |
| a clean train event and a no-train event | baseline contrast for timing | control |

Success criteria to be stated by the researcher before any pilot: timing capture, six-state assignment with rationale, schema usability defects, stop conditions. Prerequisites (all pending): bound D1, reviewer identities, media-access authorization, pilot authorization (`AUTH-PILOT-EXEC`), release of this or another schema.

## 4. What this proposal does not do
Create a record, name a reviewer, set a tolerance, promote anything, or change the active schema or any gate.
