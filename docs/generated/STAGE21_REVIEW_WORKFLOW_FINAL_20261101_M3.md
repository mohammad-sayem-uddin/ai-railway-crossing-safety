# STAGE-2.1 HUMAN REVIEW WORKFLOW & SOFTWARE READINESS — MISSION 3 (`2026-11-01`)

**Repository:** `/Users/sayemuddin/Desktop/Train_automation`  
**Schema Version:** `8.1.0-stage2.1` (`src/railway_detection/annotation/stage2_1_schema.py`)  
**Inspection Scope:** Actual code verification of Stage-2.1 schemas, session builders, promotion gate, batch integrity safeguard, and readiness CLI (no human review records, promotion receipts, or invalidation notices were created or modified).

---

## 1. Software Verification of Stage-2.1 Infrastructure

Mission 3 inspected and synthetically tested the complete Stage-2.1 software stack:

| Component | Module | Status | Verified Capabilities & Fail-Closed Guards |
|---|---|---|---|
| **Stage-2.1 Record Schema** | `src/railway_detection/annotation/stage2_1_schema.py` | **OPERATIONAL** | Enforces `schema_version == "8.1.0-stage2.1"`, rejects legacy `7.0.0` records, blocks placeholder reviewer IDs (`REVIEWER_ID_BLOCKLIST`), enforces `MIN_PLAUSIBLE_REVIEW_DURATION_S = 30.0`, requires `ModelIndependenceAttestation` ($\ge 20$ chars), requires `ReviewerObservedMediaHashes` (`front_sha256`, `back_sha256`, `observed_at_utc`), and validates all 6 `CANONICAL_TIMESTAMPS` (`T0_first_visible`, `T1_danger_zone_entry`, `T2_crossing_occupancy_start`, `T3_locomotive_unit_clearance`, `T4_tail_clearance`, `T_scene_clear`) across the 4-state taxonomy (`OBSERVABLE`, `UNOBSERVABLE_NOT_APPLICABLE`, `CENSORED`, `UNCERTAIN`). |
| **Review Record Builder** | `src/railway_detection/annotation/review_session.py` (`build_review_record`) | **OPERATIONAL** | Checks `reviewer_id in authorized_reviewers` before any record assembly (`REVIEWER_NOT_AUTHORIZED`), computes live media SHA-256 pairs via `compute_media_sha256_pair`, and validates the assembled dict through `build_stage2_1_record_from_dict`. |
| **Promotion Gate** | `src/railway_detection/annotation/promotion_gate.py` (`validate_for_promotion`, `promote_record`) | **OPERATIONAL** | Fails closed on legacy schema, invalidation markers, unauthorized reviewers, stale proposal SHA-256, missing/mismatched media SHA-256 registry, live media file hash mismatch, unresolved adjudication statuses (`NEEDS_SECOND_REVIEW`, `DISPUTED`), and `SECOND_REVIEW_REQUIRED` when any boundary is `CENSORED` or `UNCERTAIN` without a distinct second reviewer. |
| **Batch Integrity Safeguard** | `src/railway_detection/annotation/integrity_safeguard.py` (`check_review_batch_integrity`) | **OPERATIONAL** | Detects and rejects overlapping review sessions, implausibly short sessions, or automated batch-generation patterns across a corpus of review records. |
| **Evaluation Readiness Gate & CLI** | `src/railway_detection/annotation/evaluation_readiness_gate.py`, `readiness_cli.py` | **OPERATIONAL** | Evaluates all 6 mechanical conditions (`>= 1` approved record per required cohort, schema validity, promotion validity, no unresolved records, no duplicate approved records, batch integrity pass). Currently returns `NOT_READY` fail-closed. |

---

## 2. Two Operational Bottlenecks Identified for Human Execution

While the schema, record builder (`build_review_record`), and promotion gate (`validate_for_promotion` / `promote_record`) are complete and verified, Mission 3 identified two operational prerequisites that the human researcher must execute or unlock when starting real Stage-2.1 adjudication:

1. **Legacy `7.0.0` Invalidation Notice Prerequisite (`LEG-EXEC`)**:
   - `data/ground_truth/reviews/` currently contains the 27 historical `schema_version: "7.0.0"` records without companion `*.invalidation_notice.json` files.
   - `_load_review_records` in `evaluation_readiness_gate.py` only excuses legacy `7.0.0` records in `data/ground_truth/reviews/` when each has a verified `*.invalidation_notice.json` written by `invalidation_notice_writer.py` (which requires explicit researcher authorization `LEG-EXEC`), or if Stage-2.1 reviews are written to a clean Stage-2.1 directory.
2. **Interactive CLI Wrapper (`AdjudicationSession`) Synthetic Lock**:
   - While `review_session.py::build_review_record` accepts real event IDs (`event_001`..`event_035`) and real paths when called by a researcher script, the interactive wrapper class `AdjudicationSession` in `src/railway_detection/annotation/adjudication_session.py` (lines 125–141) still carries a Phase 10B safety lock (`_SYNTHETIC_ID_RE = re.compile(r"^synthetic_[A-Za-z0-9_-]+$")` and `_require_temp_path` restricting output to `tempfile.gettempdir()`).
   - Therefore, when the human reviewer conducts real Stage-2.1 reviews, they should either invoke `review_session.build_review_record` + `promotion_gate.promote_record` directly or authorize lifting the `synthetic_` prefix lock in `adjudication_session.py`.

---

## 3. Concise Step-by-Step Human Review Workflow

1. **Step 1 — Maintain Authorized Reviewer Allowlist**:
   - Confirm `data/ground_truth/authorized_reviewers.json` lists the specific human reviewer identifiers (e.g., `sayem_primary_reviewer`, `independent_reviewer_2`) and zero blocklisted placeholders.
2. **Step 2 — Execute Legacy Record Disposition (`LEG-EXEC`)**:
   - Authorize and run `invalidation_notice_writer.py` so the 27 legacy `7.0.0` records in `data/ground_truth/reviews/` receive verified `*.invalidation_notice.json` files (preserving the historical files intact while excluding them from Stage-2.1 loading).
3. **Step 3 — Independent Blind Media Inspection & Record Creation**:
   - For each event across `train_events`, `no_train_events`, and `engine_events`, the authorized human reviewer inspects `camera_front.mov` and `camera_back.mov` independently of model outputs ($\ge 30\text{ s}$ per event) and records each of the 6 canonical boundaries (`T0_first_visible`, `T1_danger_zone_entry`, `T2_crossing_occupancy_start`, `T3_locomotive_unit_clearance`, `T4_tail_clearance`, `T_scene_clear`) as `OBSERVABLE` (with `value_s` and `reference_camera`), `UNOBSERVABLE_NOT_APPLICABLE`, `CENSORED`, or `UNCERTAIN` with a non-empty `rationale`.
   - Assemble the `8.1.0-stage2.1` record via `build_review_record(...)`, which binds the live SHA-256 of both video files and the active proposal SHA-256.
4. **Step 4 — Second Independent Review for `CENSORED` / `UNCERTAIN` Boundaries**:
   - Any event containing a `CENSORED` or `UNCERTAIN` boundary requires a second independent review record (`second_review_of=<primary_review_id>`) by a distinct authorized reviewer before promotion is permitted.
5. **Step 5 — Promotion Gate & Batch Integrity Verification**:
   - Run `promote_record(...)` (`promotion_gate.py`) and `readiness_cli.py` to verify all records pass schema validation, live media hash re-verification, proposal currency, dual-review rules, and `check_review_batch_integrity`, producing canonical ground-truth records and promotion receipts in `data/ground_truth/canonical/`.
