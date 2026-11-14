# Software Testing & Verification Report

**V3 Test Module:** [`test_v3_four_layer_system.py`](file:///Users/sayemuddin/Desktop/Train_automation/tests/unit/test_v3_four_layer_system.py) (`15` test functions / `20` parametrized pytest cases, classified `SYNTHETIC_ONLY`)  
**Access Registry:** [`tests/test_access_classification.yaml`](file:///Users/sayemuddin/Desktop/Train_automation/tests/test_access_classification.yaml) (`172` files indexed)  
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

## 3. Classification Registry & Safe Synthetic Runner (`1,857 Passed, 1 Pre-Existing Metadata Failure`)

1. **`scripts/classify_test_access.py --work-dir /tmp/classify_v3_check --check`:**
   - Registry summary (`tests/test_access_classification.yaml`): `172` total test files (`77` `SYNTHETIC_ONLY`, `17` `METADATA_ONLY`, `94` `safe_for_synthetic_runner`).
   - `test_v3_four_layer_system.py` classified `SYNTHETIC_ONLY` (`safe_for_synthetic_runner: True`, `blocked_attempts: {}`, `passed: 20`). `--check` returned `manifest OK`.
2. **`PYTHONPATH=src .venv/bin/python scripts/run_synthetic_tests.py --report-path /tmp/synthetic_runner_v3_report.json`:**
   - **Result:** `pytest_exit_code: 1` (`status: TESTS_FAILED`), `94` files selected (`78` excluded), **`1,857` passed, `1` failed** (`0` errors, `0` skipped), **`guard: {"blocked": 0, "events": 2531, "metadata_reads": 2527}`**, **`violations: []`**.
   - **Sole failure (pre-existing on `main`):** `tests/test_phase11_7_governance_controls.py::test_real_allowlist_file_loads_and_contains_only_the_researcher` (`METADATA_ONLY`), failing because `data/ground_truth/authorized_reviewers.json` contains both `'elaf85777@gmail.com'` and `'raihankabirrahu@gmail.com'`. All `77/77` `SYNTHETIC_ONLY` test files and `16/17` `METADATA_ONLY` test files passed without any access violations.

---

## 4. Full Repository Suite Triage (`3,819 Passed, 41 Failed`)

Executed across the entire repository after final edits:

```bash
.venv/bin/python -m pytest tests/ -q --tb=line --import-mode=importlib
```

- **Observed Total:** **`3,819 passed, 41 failed in 139.55s`** (`3,860` executed).
- **Regression Check:** **`0` regressions** in any V1/V2/V3 runtime, vision, audio, fusion, simulation, or synthetic module. Every single one of the `41` failures is an explicitly verified pre-existing condition on baseline `main` (`d1032756de80963130e1cbd3d2334cb32139b996`):

| Failure Subgroup | Count | Files Affected | Exact Root Cause Verified |
| --- | --- | --- | --- |
| **Stale `README.md` catalog hash in documentary preflight tests** | `23` | `synthetic_mission26/test_inventory_cli.py` (`10`), `synthetic_mission27/test_dashboard_cli.py` (`5`), `synthetic_mission28/test_pilot_readiness.py` (`8`) | Pre-existing `ValueError: stale source-document manifest: README.md` from Mission 17A-README update on `main` |
| **Unexported `PYTHONPATH=src` in child-process tests** | `8` | `synthetic_mission22/test_crash_and_adversarial.py` (`1`), `test_workflow.py` (`1`), `synthetic_mission24/test_application.py` (`5`), `synthetic_mission25/test_integration.py` (`1`) | Subprocess `.venv/bin/python` calls without editable install / `PYTHONPATH=src` raise `ModuleNotFoundError: No module named 'railway_detection'` |
| **Same-process import-order isolation checks** | `4` | `synthetic_mission17d/test_isolation.py` (`1`), `test_mission17f_regressions.py` (`1`), `synthetic_mission18a/test_isolation.py` (`1`), `synthetic_mission18b/test_provenance.py` (`1`) | `railway_detection.cli.main` / `torch` already in `sys.modules` from earlier tests collected in the same pytest process |
| **Pre-existing repo governance, allowlist, & legacy-opener checks** | `6` | `test_phase11_7_governance_controls.py` (`1`), `test_exploratory_subset_authorization_gate.py` (`1`), `test_media_opener_coverage.py` (`1`), `test_mission4a_governance_and_stage21_safety.py` (`1`), `test_phase12_governance.py` (`1`), `test_reproducibility_audit.py` (`1`) | Allowlist contains both `elaf85777@gmail.com` & `raihankabirrahu@gmail.com`; `AUTH-MEDIA-ACCESS.json` absent; pre-existing legacy hash openers in `build_m3_mm_manifest*.py` / `run_stage21_review.py`; `PREMATURE_OPENING_DEFINITION_UNDECIDED` / `PASS` resolved on `main` |
| **Total Pre-Existing Failures** | **`41`** | **`17` files** | **`0` failures attributable to `exp/four-layer-completion` edits** |
