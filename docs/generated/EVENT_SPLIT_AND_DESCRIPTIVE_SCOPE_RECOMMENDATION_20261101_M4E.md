# Event Split and Descriptive Evaluation Scope Recommendation

**Date:** 2026-11-01  
**Mission:** 4E — Researcher Decision Finalization  
**Status:** RECOMMENDATION ONLY — NOT APPROVED  
**Decision identifier:** `AUTH-EVENT-SPLIT`  
**Approval field:** ______________________________

## Event Inventory

| Cohort | Count | Role |
|---|---:|---|
| `train_events` | 23 | Primary evaluation cohort |
| `no_train_events` | 3 | Negative controls |
| `engine_events` | 1 | Isolated case study |
| **Total** | **27** | |

## Current State

- All 27 events have legacy review records (schema 6.0.0, invalidated).
- All 27 have verified invalidation notices.
- 0 genuine Stage-2.1 records exist.
- Review inventory: all `NOT_STARTED`, no assigned reviewers.
- No official split decision file exists (`data/splits/phase12_event_split_decision.json` absent).

## Train Event Eligibility

| Condition | Count | Notes |
|---|---:|---|
| Total train events | 23 | |
| Left-censored at T0 | 20 | Train visible at recording start |
| Observable T4 | 22 | |
| Right-censored T_scene_clear | 21 | Recording ends before scene clear |
| CALIBRATION_SUPPORTED (R04) | 12 | Eligible for dual-camera |
| PROVISIONAL (R04) | 5 | Not eligible for dual-camera |
| AMBIGUOUS (R04) | 6 | Not eligible for dual-camera |

## No-Train Event Eligibility

- 3 events, all negative controls.
- All boundaries should be UNOBSERVABLE_NOT_APPLICABLE.
- Used for false-alarm counting only.
- Never pooled with train events.

## Engine Event Isolation

- 1 event (`engine_events/event_001`).
- Isolated case study (approved decision).
- Never in train-event denominators.
- Never in negative-control denominators.
- Special T3≡T4 semantics.

## Split Considerations

### Leakage Risk
- All events from one crossing (`crossing_A`).
- Two collection sessions.
- Splitting by session prevents temporal leakage.
- Splitting by event within session risks shared-condition leakage.

### Sample Size
- 23 train events is very small for train/test split.
- 3-fold CV may be more appropriate than fixed split.
- Descriptive reporting may be more appropriate than inferential statistics.

### Fixed-Site Limitation
- Single crossing limits generalization.
- No cross-site validation possible.
- Results are descriptive of THIS crossing only.

## Descriptive Evaluation Scope

The approved `GOV-D3-DESCRIPTIVE-MODE` decision permits:
- Fixed-site descriptive summaries.
- Per-event metric reporting.
- Explicit limitation statements.
- No inferential claims.
- No cross-site generalization.

## Recommendation

**For this 27-event single-crossing dataset, recommend descriptive-only evaluation with per-event reporting rather than a traditional train/test split.**

**Confidence:** HIGH

**Rationale:**
1. 23 train events is insufficient for statistically meaningful train/test split.
2. Single crossing eliminates cross-site generalization.
3. Descriptive mode is already approved (GOV-D3-DESCRIPTIVE-MODE).
4. Per-event reporting preserves all information.
5. If a split is required for future confirmatory work, it should be session-based.

**If a split IS required:**
- Split by recording session (not individual events).
- Ensure no session leakage between partitions.
- Engine event excluded from split (case study only).
- No-train events excluded from train split (negative controls).

**This recommendation is NOT an approval.**

## Researcher Response

**Split approach:** ______________________________  
**Descriptive-only confirmed?** ______________________________  
**Session-based split (if applicable):** ______________________________  
**Decision-maker:** ______________________________  
**Date (UTC):** ______________________________
