# STAGE-2.1 HUMAN REVIEW READINESS — MISSION 2 (2026-11-01)

- **Document ID**: `STAGE21_HUMAN_REVIEW_READINESS_20261101_M2`
- **Mission**: `MISSION 2 — PIPELINE INTEGRITY VERIFICATION, SAFE REMEDIATION & STAGE-2.1 READINESS`

---

## 1. Current Repository Stage-2.1 State (Read-Only Audit)

- **Active Review Schema Version Required**: `8.1.0-stage2.1` (`src/railway_detection/annotation/stage2_1_schema.py`)
- **Existing Records in `data/ground_truth/reviews/`**: `27` legacy files (`20` `train_events`, `6` `no_train_events`, `1` `engine_events`), all at `schema_version: "7.0.0"` with blocklisted placeholder `reviewer_id: "human_researcher_lead"` and shared batch timestamps (`2026-03-27T01:40:25Z` / `2026-03-27T01:40:26Z`).
- **Valid `8.1.0-stage2.1` Records Present**: `0`
- **Promotion-Eligible Records Present**: `0`
- **Promotion Receipt (`data/governance/stage21_promotion_receipt.json`)**: **Absent** (`STAGE21_PROMOTION_RECEIPT_MISSING`)
- **Authorized Reviewers Allowlist (`data/ground_truth/authorized_reviewers.json`)**: Present (`["sayem_uddin"]`)
- **Safety Confirmation**: Mission 2 did **not** create, modify, invalidate, or promote any ground-truth record, proposal, allowlist, or receipt.

---

## 2. Architecture of the Stage-2.1 Review & Promotion Toolchain

| Module | File Path | Responsibility |
| :--- | :--- | :--- |
| **Schema Validator** | `src/railway_detection/annotation/stage2_1_schema.py` | Enforces `schema_version == "8.1.0-stage2.1"`, `REVIEWER_ID_BLOCKLIST`, `MIN_PLAUSIBLE_REVIEW_DURATION_S = 30.0`, `ModelIndependenceAttestation` (`>= 20` chars), `ReviewerObservedMediaHashes`, 6 canonical boundaries under the 4-state taxonomy, and chronological `adjudication_history`. |
| **Promotion Gate** | `src/railway_detection/annotation/promotion_gate.py` | Enforces `load_authorized_reviewers`, active proposal SHA-256 currency (`STALE_PROPOSAL_REFERENCE`), live media SHA-256 re-verification (`compute_media_sha256_pair`) against both `media_sha256_registry` and `reviewer_observed_media_hashes`, and resolved `APPROVED` status. |
| **Batch Integrity Safeguard** | `src/railway_detection/annotation/integrity_safeguard.py` | Detects shared review timestamps without plausible duration (`IDENTICAL_TIMESTAMP_NO_PLAUSIBLE_DURATION`), missing session provenance (`APPROVED_WITHOUT_PROVENANCE`), and overlapping review windows by the same reviewer (`OVERLAPPING_REVIEW_SESSIONS`). |
| **Review Record Builder** | `src/railway_detection/annotation/review_session.py` | `build_review_record(...)` checks reviewer authorization first, computes live media SHA-256 hashes from `front_media_path` and `back_media_path`, derives `review_duration_s` via `build_stage2_1_record_from_dict`, and returns a schema-validated dict without writing to `data/ground_truth/reviews/`. |
| **Evaluation Readiness Gate & CLI** | `src/railway_detection/annotation/evaluation_readiness_gate.py`, `src/railway_detection/annotation/readiness_cli.py` | Evaluates corpus readiness across all required cohorts (`train_events`, `no_train_events`, `engine_events`), excuses legacy `7.0.0` records **only** after verified invalidation notices (`LEG-EXEC`) are present, and writes `data/governance/stage21_promotion_receipt.json` (`phase12-stage21-promotion-receipt/2`) only when `ready=True` (`exit_code == 0`). |

---

## 3. Practical Step-by-Step Workflow for Human Stage-2.1 Review

### Step 0 — Prerequisite Legacy Invalidation (`LEG-EXEC`)
Before `readiness_cli.py` can return `READY` on a newly reviewed corpus, the 27 invalidated `schema_version: "7.0.0"` records in `data/ground_truth/reviews/` must either be excused by running the researcher-authorized `LEG-EXEC` invalidation notice writer (bound to `docs/PHASE11_6_LEGACY_INVALIDATION_DRY_RUN_PROPOSAL.json`, SHA-256 `41cbbba3e9d587b9972c3baca1b39f09d478d408d9c60fd538c249c4600113d4`) or reviewed in a clean reviews directory.

### Step 1 — Select an Event from the Annotation Inventory
Inspect `data/manifests/layer_b_v2_annotation_inventory.json` and the corresponding active candidate proposal in `data/ground_truth/proposals/{cohort}/{event_id}_proposal_v{N}.json` (using the highest version `v{N}` present for that event).

### Step 2 — Inspect Raw Media Outside Model Outputs (Model Firewall)
- Inspect raw video/audio (`camera_front.mov`, `camera_back.mov`) using an external frame-accurate player/tool (e.g., `ffmpeg` / `ffplay` / `mpv` + spectral audio viewer).
- **Do not** consult model outputs, checkpoints, or Phase 8–10.1 experiment artifacts during boundary adjudication.

### Step 3 — Record Reviewer Metadata and Session Timestamps
- `reviewer_id`: Must be present in `data/ground_truth/authorized_reviewers.json` (currently `"sayem_uddin"`) and not on `REVIEWER_ID_BLOCKLIST`.
- `review_session_id`: Unique session identifier per event review (e.g., `"session_20261102_train_event_001"`).
- `review_start_utc` and `review_end_utc`: Timezone-aware UTC ISO-8601 timestamps (`Z` or `+00:00`) recording the actual start and end of the human review session:
  - Must satisfy `(review_end_utc - review_start_utc) >= 30.0` seconds.
  - Sessions by the same `reviewer_id` across different events must **not** overlap in time (`OVERLAPPING_REVIEW_SESSIONS`).
- `inspection_tool`: Specific description of the inspection tool/workflow used.

### Step 4 — Record Live Media SHA-256 Observations
- Compute full-file SHA-256 hashes of `camera_front.mov` and `camera_back.mov` at review time (handled automatically by `build_review_record` via `compute_media_sha256_pair`) and record `observed_at_utc`.

### Step 5 — Adjudicate All 6 Canonical Boundaries Under the 4-State Taxonomy
Every record must contain all 6 keys in `boundary_adjudications`:
1. `T0_first_visible`
2. `T1_danger_zone_entry`
3. `T2_crossing_occupancy_start`
4. `T3_locomotive_unit_clearance`
5. `T4_tail_clearance`
6. `T_scene_clear`

Each boundary must be assigned one of the four states:
- `OBSERVABLE`: Requires finite `value_s` (`float`), `reference_camera` in `("front", "back")`, and non-empty `rationale`.
- `UNOBSERVABLE_NOT_APPLICABLE`: Requires `value_s: null`, `reference_camera: null`, and non-empty `rationale`.
- `CENSORED`: Requires `value_s: null`, `reference_camera: null`, and non-empty `rationale` (e.g., recording starts after boundary or ends before clearance).
- `UNCERTAIN`: Requires `value_s: null`, `reference_camera: null`, and non-empty `rationale`.

### Step 6 — Special Cohort Rules
- **`engine_events/event_001`**:
  - `cohort`: `"engine_events"`
  - `T3_locomotive_unit_clearance`: Adjudicated as `OBSERVABLE` (with `value_s` and `reference_camera`) when the single locomotive clears the crossing.
  - `T4_tail_clearance`: Must be adjudicated as `UNOBSERVABLE_NOT_APPLICABLE` (`value_s: null`, `reference_camera: null`) with rationale explaining that the event is a single locomotive without trailing coaches.
- **`no_train_events` (`event_001`..`event_006`)**:
  - `cohort`: `"no_train_events"`
  - All six train boundaries (`T0_first_visible` through `T_scene_clear`) must be adjudicated as `UNOBSERVABLE_NOT_APPLICABLE` (`value_s: null`, `reference_camera: null`) after verifying that no train enters the scene in either camera stream.

### Step 7 — R04 Camera Synchronization Classification Awareness
Each boundary in `Stage21ReviewRecord` is recorded in **camera-local time** along with its `reference_camera` (`"front"` or `"back"`). Reviewers do **not** manually add cross-camera offsets to `value_s`.
- Current R04 evidence classification across the 27 events (`data/manifests/camera_sync_offsets_candidate.yaml` and `docs/generated/R04_EVENT_EVIDENCE_MATRIX_20261029.md`) remains preserved:
  - **`CALIBRATION_SUPPORTED`**: `12` events (`train_events/event_001`, `003`, `005`, `008`, `009`, `010`, `011`, `013`, `015`, `016`, `017`, `020`)
  - **`PROVISIONAL`**: `7` events (`train_events/event_002`, `004`, `006`, `007`, `018`, `019`, `engine_events/event_001`)
  - **`AMBIGUOUS`**: `8` events (`train_events/event_012`, `014`, `no_train_events/event_001`..`006`)
- Cross-camera clock alignment (`front` vs. `back`) is applied downstream only if and when the researcher records `data/manifests/phase12_r04_scope_decision.json` (Decision D4).

### Step 8 — Validate Records and Check Promotion Readiness
1. Validate an individual record dict in Python via `build_stage2_1_record_from_dict(record_dict)` and `validate_for_promotion(...)`.
2. Run the read-only metadata audit (does not touch media):
   ```bash
   PYTHONPATH=src .venv/bin/python -c "from railway_detection.annotation.readiness_audit import audit_ground_truth_readiness, render_markdown; print(render_markdown(audit_ground_truth_readiness('.')))"
   ```
3. When human review is complete and the researcher is ready to verify live media hashes and issue the Stage-2.1 promotion receipt:
   ```bash
   PYTHONPATH=src .venv/bin/python -m railway_detection.annotation.readiness_cli \
     --report-path results/readiness_report.json \
     --markdown-path results/readiness_report.md \
     --receipt-path data/governance/stage21_promotion_receipt.json
   ```
   - Exit code `2` (`NOT_READY`): Blockers remain; no promotion receipt is written.
   - Exit code `0` (`READY`): All mechanical checks passed and `data/governance/stage21_promotion_receipt.json` is written. Official Phase 12 evaluation still requires separate human `EVAL-AUTH` (`data/governance/eval_authorization.json`).
