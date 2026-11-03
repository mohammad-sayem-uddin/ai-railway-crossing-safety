# Stage-2.1 Synthetic ID Guard & Real-vs-Synthetic Boundary Audit (Mission 4A)

**Date:** 2026-11-01  
**Mission:** 4A — Governance Reconciliation, Authorization Integrity & Stage-2.1 Safety Verification  
**Repository:** `/Users/sayemuddin/Desktop/Train_automation`  
**Branch / HEAD:** `main` @ `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`  
**Status:** AUDITED & HARDENED (Fail-Closed Across Preparation, Promotion & Readiness Gates)

---

## 1. Executive Summary

Mission 4A Section 6 required a complete architectural audit of the `synthetic_` identifier requirement across the Stage-2.1 human-review pipeline to verify two complementary safety invariants:
1. **Preparation-Time Synthetic Isolation:** Preparation-only utilities (`adjudication_session.py` and `stage21_timing_pilot.py`) must require `synthetic_`-prefixed reviewer/session identifiers and isolated non-canonical output directories so dry-run/pilot exercises can never masquerade as real human reviews.
2. **Promotion-Time & Readiness-Time Anti-Synthetic Rejection:** Canonical ground-truth promotion (`promotion_gate.py`) and evaluation readiness verification (`evaluation_readiness_gate.py`) must **reject** any record carrying `synthetic_` identifiers, synthetic email domains (`@synthetic.`, `@test.example.com`), or temporary/fixture media paths whenever targeting canonical ground-truth directories or when `disallow_synthetic_identifiers=True`.

---

## 2. Module-by-Module Audit & Remediation

### 2.1 `src/railway_detection/annotation/adjudication_session.py`
- **Role:** Interactive/CLI preparation-only session helper (`AdjudicationSession`).
- **Enforced Guards (Lines 45–155):**
  - `_SYNTHETIC_PREFIX = "synthetic_"`.
  - `_FORBIDDEN_REPO_SEGMENTS`: blocks any output under `data/ground_truth/reviews`, `data/ground_truth/approved`, `data/ground_truth/train_events`, `data/ground_truth/no_train_events`, `data/ground_truth/engine_events`, `data/manifests`, `docs`, `results`, `outputs`, `runs`, `configs`.
  - Requires `reviewer_id.startswith("synthetic_")` and `review_session_id.startswith("synthetic_")`; otherwise raises `AdjudicationSessionError`.
  - Hardcodes `adjudication_status = "NEEDS_SECOND_REVIEW"` on every emitted record so preparation outputs are non-promotable even if copied.
  - Verifies event existence and media SHA-256 against the manifest without reading raw media bytes.

### 2.2 `src/railway_detection/annotation/stage21_timing_pilot.py`
- **Role:** 3-event (`train_events/event_001`, `no_train_events/event_001`, `engine_events/event_001`) timing-calibration pilot preparation harness.
- **Enforced Guards (`_require_preparation_isolation`):**
  - Rejects missing or non-`synthetic_`-prefixed `reviewer_id` or `review_session_id` (`PilotWorkflowError`).
  - Rejects output directories inside `data/ground_truth/` or repository canonical paths.
  - Enforces that `PILOT-EXEC` real human timing calibration cannot use this preparation harness to write into `data/ground_truth/reviews/`.

### 2.3 `src/railway_detection/annotation/review_session.py`
- **Role:** Pure library builder (`build_review_record`) for constructing a `Stage21ReviewRecord` (`schema_version = "8.1.0-stage2.1"`) from real human review inputs and computing live media hashes on caller-provided paths.
- **Enforced Guards:**
  - Validates `reviewer_id` against caller-loaded `authorized_reviewers` allowlist and `REVIEWER_ID_BLOCKLIST`.
  - Computes `review_duration_s` strictly from `(review_end_utc - review_start_utc)` and enforces `MIN_PLAUSIBLE_REVIEW_DURATION_S = 30.0`.
  - Does **not** require `synthetic_` prefixes, enabling real named human reviewers (e.g., `dr.rahman@buet.ac.bd`) once `data/ground_truth/authorized_reviewers.json` is populated by the researcher.

### 2.4 `src/railway_detection/annotation/promotion_gate.py` (Hardened in Mission 4A)
- **Gap Identified in Audit:** Previously, if a researcher or test accidentally added a `synthetic_...` reviewer ID to an allowlist file, `validate_for_promotion()` and `promote_record()` did not have a dedicated check rejecting `synthetic_` identifiers or temporary media paths at the canonical promotion boundary.
- **Remediation Implemented in Mission 4A:**
  - Added `_is_real_repository_ground_truth_path(path)` and `validate_non_synthetic_record(record_dict, *, media_file_paths=None) -> list[PromotionViolation]`.
  - Emits `PromotionViolation(code="SYNTHETIC_RECORD_NOT_PROMOTABLE")` if:
    1. Any of `review_id`, `reviewer_metadata.reviewer_id`, `reviewer_metadata.review_session_id`, `second_review_of`, or `adjudication_history[*].by` starts with `synthetic_` or contains `@synthetic.` / `@test.example.com`.
    2. Any media file path in `media_file_paths` for the event resolves to a temporary/pytest fixture directory (`/tmp/`, `/var/folders/`, `pytest-of-`, `fixture_blobs`, `synthetic`).
  - Added `disallow_synthetic_identifiers: bool = False` to `validate_for_promotion()`, `validate_batch_for_promotion()`, and `promote_record()`, and **automatically enables** this guard whenever `approved_output_dir` or `reviews_dir` resolves inside the real repository's `data/ground_truth` tree.

### 2.5 `src/railway_detection/annotation/evaluation_readiness_gate.py` (Hardened in Mission 4A)
- **Remediation Implemented in Mission 4A:**
  - Added `disallow_synthetic_identifiers: bool = False` to `evaluate_readiness()`, auto-enabled whenever `reviews_dir` resolves inside the real repository's `data/ground_truth` tree, and forwarded to `validate_batch_for_promotion()`.

---

## 3. End-to-End Boundary Matrix: Synthetic Pilot vs Real Human Review

| Pipeline Component | Synthetic Pilot / Dry-Run (`synthetic_*` IDs, `tmp_path`) | Real Human Review (`dr.name@domain`, `data/ground_truth/`) | Cross-Contamination Attempt (Synthetic Record -> Canonical Promotion) |
|---|---|---|---|
| `AdjudicationSession` (`adjudication_session.py`) | **ALLOWED** (writes `NEEDS_SECOND_REVIEW` to isolated dir) | **REFUSED** (`AdjudicationSessionError` on non-`synthetic_` ID or canonical dir) | Blocked (`NEEDS_SECOND_REVIEW` + `SYNTHETIC_RECORD_NOT_PROMOTABLE`) |
| `stage21_timing_pilot.py` | **ALLOWED** (isolated pilot workspace only) | **REFUSED** (`PilotWorkflowError` on canonical dir or non-`synthetic_` ID) | Blocked (`SYNTHETIC_RECORD_NOT_PROMOTABLE`) |
| `build_review_record` (`review_session.py`) | **ALLOWED** in isolated unit tests | **ALLOWED** when reviewer is in `authorized_reviewers.json` and duration >= `30.0s` | Blocked at promotion gate if any ID/media is synthetic |
| `validate_for_promotion` / `promote_record` (`promotion_gate.py`) | **ALLOWED** in unit tests when `disallow_synthetic_identifiers=False` in `tmp_path` | **ALLOWED** when all 6 Stage-2.1 checks + non-synthetic checks pass | **REFUSED** (`SYNTHETIC_RECORD_NOT_PROMOTABLE`) |
| `evaluate_readiness` (`evaluation_readiness_gate.py`) | **ALLOWED** in unit tests when `disallow_synthetic_identifiers=False` in `tmp_path` | **ALLOWED** only when all 27 events have valid non-synthetic Stage-2.1 reviews | **REFUSED** (`SYNTHETIC_RECORD_NOT_PROMOTABLE`, `ready_for_promotion=False`) |

---

## 4. Regression Test Verification

Verified in `tests/unit/test_mission4a_governance_and_stage21_safety.py`:
- `test_adjudication_session_and_timing_pilot_enforce_synthetic_and_path_isolation`
- `test_promotion_and_readiness_gates_reject_synthetic_records_when_enforced`
