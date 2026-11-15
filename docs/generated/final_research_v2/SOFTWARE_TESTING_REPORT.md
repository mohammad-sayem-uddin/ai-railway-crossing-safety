# Software Testing & Verification Report

**V3 Test Module:** [`test_v3_four_layer_system.py`](file:///Users/sayemuddin/Desktop/Train_automation/tests/unit/test_v3_four_layer_system.py) (`15` test functions / `20` parametrized pytest cases, classified `SYNTHETIC_ONLY`) & [`test_exp_r_and_degraded_wakeup.py`](file:///Users/sayemuddin/Desktop/Train_automation/tests/unit/test_exp_r_and_degraded_wakeup.py) (`3` test functions)  
**Access Registry:** [`tests/test_access_classification.yaml`](file:///Users/sayemuddin/Desktop/Train_automation/tests/test_access_classification.yaml) (`179` files indexed)  
**Safe Runner Script:** [`run_synthetic_tests.py`](file:///Users/sayemuddin/Desktop/Train_automation/scripts/run_synthetic_tests.py)

---

## 1. V3 Four-Layer & Safety-Invariant Test Suite (`20 / 20` Passed)

All `15` test functions (`20` parametrized test cases) in [`test_v3_four_layer_system.py`](file:///Users/sayemuddin/Desktop/Train_automation/tests/unit/test_v3_four_layer_system.py) executed without skips, mocks bypassing core logic, or raw-media access:

| Test Function | Verification Scope |
| --- | --- |
| `test_orientation_normalization_all_orthogonal_and_fail_closed` | Parametrized `0°, ±90°, ±180°, ±270°` `ffmpeg` H.264 decode across PyAV and OpenCV `CAP_PROP_ORIENTATION_AUTO` + invalid non-orthogonal rejection |
| `test_video_demo_deferred_writer_matches_oriented_frame_dimensions` | Deferred `VideoWriter` sizing against rotated frame `(H, W)` |
| `test_audio_log_mel_natural_matches_v3_and_differs_from_db` | `compute_log_mel_spectrogram(..., log_scale="natural")` finite shape & scale distinction from dB |
| `test_collector_causality_no_stale_backfill_and_reset_isolation` | Single-consumption snapshot emission (`allow_stale_detection_backfill=False`) + `.reset()` cross-event isolation |
| `test_state_machine_all_11_states_and_illegal_transitions_blocked` | Explicit enum states & blocking of illegal direct state jumps (e.g. direct `TRAIN_PRESENT -> IDLE`) |
| `test_physical_gate_model_kinematics_and_interrupt` | `OPEN -> CLOSING -> CLOSED -> OPENING -> OPEN` stroke timing & mid-opening closure re-interrupt |
| `test_closure_policy_front_independent_and_single_frame_glitch_rejected` | L1 independent closure (`confirm_frames=2`) + single-frame glint suppression (`0` FP) |
| `test_departure_policy_conservative_vs_guarded_and_sparse_dropout` | `V3_CONSERVATIVE_POSITIVE` vs `V3_GUARDED_DISAPPEARANCE` on sparse dropout |
| `test_occupancy_all_five_states_and_contradiction_invariant` | All 5 `OccupancyState` outcomes (`CLEAR, OCCUPIED, UNKNOWN, MISSING, CONTRADICTORY`) & reopening block |
| `test_missing_modalities_and_failed_clearance_source_fail_safe` | Missing/stale L1/L4/occupancy fail-safe closure / hold-closed invariants |
| `test_fault_injection_modes_never_reopen_unsafely` | Stale, OOO/duplicate timestamps, EOF termination, false-clear, inference timeout invariants |
| `test_multi_train_interruption_and_reversal` | Second approaching train & train reversal mid-departure keep gate closed |
| `test_negative_controls_and_side_movement_tracker` | `MOVING` vs `STOPPED` vs `SINGLE_FRAME` vs `UNOBSERVED` side tracking + empty controls |
| `test_full_pipeline_nominal_e2e_and_decision_traceability` | End-to-end 4-layer cycle & structured causal trace fields |
| `test_end_to_end_reproducibility_bit_identical` | Repeated synthetic V3 evaluation yields identical output digests |

---

## 2. Targeted Backward-Compatibility & Core Verification (`77 / 77` Passed)

Executed after final edits (`src/railway_detection/vision/video.py` `raw_coded_size` mock-frame guard and `src/railway_detection/experiments/diagnostic_trace.py` `allow_stale_detection_backfill=True` preservation):

```bash
.venv/bin/python -m pytest tests/unit/test_phase9*.py tests/unit/test_phase10*.py \
  tests/synthetic_mission37/test_source_pts.py tests/synthetic_mission44/test_display_rotation.py \
  tests/unit/test_v3_four_layer_system.py -v --import-mode=importlib
```

- **Result:** **`77 passed in 6.42s`** (`0` failed, `0` skipped).

---

## 3. Classification Registry & Safe Synthetic Runner (`3,285 Passed, 0 Failed`)

1. **`scripts/classify_test_access.py --work-dir /tmp/classify_full_work --check`:**
   - Registry summary (`tests/test_access_classification.yaml`): `179` total test files (`116` `SYNTHETIC_ONLY`, `29` `METADATA_ONLY`, `15` `MODEL_CHECKPOINT_ACCESS`, `5` `PROCESSED_DATA_ACCESS`, `5` `RAW_MEDIA_ACCESS`, `9` subprocess-spawning `UNKNOWN`, `145` `safe_for_synthetic_runner`).
   - `test_v3_four_layer_system.py`, `test_exp_r_and_degraded_wakeup.py`, `test_exp_r_independent_validation.py`, and `test_pi_telemetry.py` are classified `SYNTHETIC_ONLY` (`safe_for_synthetic_runner: True`); `--check` returned `manifest OK` and `test_access_classification_tools.py` passed **`58/58`**.
2. **`PYTHONPATH=src:. .venv/bin/python scripts/run_synthetic_tests.py --report-path /tmp/final_synthetic_report.json`:**
   - **Result:** **`pytest_exit_code: 0` (`status: PASSED`)**, `145` safe files batched cleanly via `--confcutdir` subprocess isolation + lazy `cv2` guard wrapping in `access_guard_plugin.py`, **`3,285 passed, 0 failed, 0 errors, 0 skipped`**, **`guard: {"blocked": 0, ...}`**, **`violations: []`**.

---

## 4. Full Repository Suite Verification (`3,881 Passed, 0 Failed`)

Executed across the entire repository after Mission 3 governance & test isolation completion:

```bash
PYTHONPATH=src:. .venv/bin/pytest -q tests/ --tb=line --import-mode=importlib
```

- **Observed Total:** **`3,881 passed, 0 failed`** (`3,881` executed; `0` V1/V2/V3 regressions, `0` technical defects):

| Outcome / Category | Count | Files Affected | Exact Root Cause Verified |
| --- | --- | --- | --- |
| **Zero-Blocker Remediation (`32 -> 5`)** | `27` fixed | `test_inventory_cli.py`, `test_dashboard_cli.py`, `test_pilot_readiness.py` (`23`), `test_media_opener_coverage.py`, `test_phase11_7_governance_controls.py`, `test_mission4a_governance_and_stage21_safety.py`, `test_phase12_governance.py`, `test_access_classification_tools.py` | Synced `MISSION_26_CATALOG_BINDING.json`, guarded non-media metadata utilities, synced dual-reviewer & Phase-12 assertions, updated `requirements.lock` |
| **Mission 3 AST Isolation Remediation (`5 -> 1`)** | `4` fixed | `synthetic_mission17d/{test_isolation.py, test_mission17f_regressions.py}`, `synthetic_mission18a/test_isolation.py`, `synthetic_mission18b/test_provenance.py` | Replaced process-order-fragile `sys.modules` checks with deterministic AST transitive closure checks via [`_isolation_audit.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/synthetic/_isolation_audit.py) |
| **Mission 3 Fail-Closed Auth Gate Assertion (`1 -> 0`)** | `1` verified | `tests/unit/test_exploratory_subset_authorization_gate.py:69` | Explicitly asserts fail-closed `[AUTH_MEDIA_ACCESS_NOT_GRANTED]` when `AUTH-MEDIA-ACCESS.json` is absent, and asserts all 11 events once authorized |
