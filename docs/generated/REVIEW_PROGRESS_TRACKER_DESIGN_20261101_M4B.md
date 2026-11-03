# Stage-2.1 Review Progress Tracker Design

**Date:** 2026-11-01  
**Status:** Design only; no real assignment or review status was written.

## Design goals

The tracker is a non-authoritative scheduling/follow-up view. It has no boundary values, approval authority, or promotion operation. `src/railway_detection/annotation/review_progress.py` builds an in-memory projection from the existing inventory; Mission 4B did not overwrite a tracking artifact.

## Status vocabulary

`NOT_SCHEDULED`, `AWAITING_REVIEWER`, `REVIEW_IN_PROGRESS`, `FIRST_REVIEW_COMPLETE`, `SECOND_REVIEW_REQUIRED`, `SECOND_REVIEW_COMPLETE`, `DISPUTED`, `INCOMPLETE_EVIDENCE`, `READY_FOR_HUMAN_VERIFICATION`, `APPROVED_BY_AUTHORIZED_REVIEWERS`, and `BLOCKED_FROM_PROMOTION`.

The last two are workflow labels, not automatic authority. Approval may be used only after genuine records and separate human evidence exist. The current design projection rejects approval/promotion claims.

## Current projection

| Source/projection | Count |
|---|---:|
| Inventory events | 27 |
| Source `review_status: NOT_STARTED` | 27 |
| `assigned_reviewer: null` | 27 |
| `stage2_1_review_file: null` | 27 |
| Projected `NOT_SCHEDULED` | 27 |
| Projected other statuses | 0 |
| Ground-truth approval claimed | 0 |
| Promotion authorization claimed | 0 |

The projection preserves source `NOT_STARTED`; it does not infer completion from legacy `APPROVED` text or the queue.

## Suggested row fields

`event_key` (cohort-qualified), `cohort`, `event_id`, `actual_source_status`, `assigned_reviewer`, `stage21_review_file`, `tracker_status`, `ground_truth_approval`, `promotion_authorized`, `status_basis`, and append-only transition actor/time/audit reference.

Do not place raw boundary values, model predictions, or inferred approval flags in this tracker.

## Transition controls

Assignment requires researcher authorization; in-progress requires event/source confirmation; first-review-complete requires a genuine session, six states/rationales, hashes, attestation, and history; second-review-required requires the researcher-approved D3(a) trigger or explicit unresolved status; second-review-complete requires a distinct authorized reviewer; disputes remain unresolved until human adjudication; incomplete evidence blocks progression; ready-for-verification is mechanical only; approval and promotion require separate researcher actions.

## Human/researcher boundary

Reviewers provide evidence and rationale. The researcher authorizes identities, independence, protocol semantics, second-review triggers, disagreement resolution, and promotion. Software tests validate safeguards only; they do not constitute human review. The current queue is `INVALID` for all events because legacy records are excluded by verified notices; the tracker remains `NOT_SCHEDULED` until explicit execution authorization.