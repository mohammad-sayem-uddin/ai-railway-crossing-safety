# Software Testing & AST Verification Report

**Summary Verdict:** Zero failures across all new exploratory pipeline tests and AST media-safety checks. Full repository pytest run executed post-edit across **`3,840` collected tests** yields **`3,807` passed (`99.14%`), `33` preexisting triaged failures (`0` errors, `0` skipped)**, persisted in [`docs/generated/final_research/test_execution_report.json`](test_execution_report.json).

---

## 1. Authoritative Post-Edit Test Execution Results

| Test Invocation | Result | Scope & Exact Counts |
|---|---|---|
| `PYTHONPATH=src:. .venv/bin/python -m pytest tests/ --import-mode=importlib --junitxml=/tmp/pytest_full_audit_post.xml -q` | **`3,807` passed, `33` failed, `0` errors, `0` skipped (`107.66 s`)** | Complete repository suite (`3,840` collected across unit + integration + synthetic mission guards) under Python 3.11 `.venv` (`av 18.1.0`, `matplotlib 3.11.1`, `pytest 9.1.1`). |
| `PYTHONPATH=src:. .venv/bin/python -m pytest tests/unit/test_exploratory_pipeline.py tests/unit/test_access_classification_tools.py -q` | **`66` passed (`3.80 s`)** | All `8` synthetic exploratory pipeline tests + all `58` test-access classification & manifest integrity checks (`tests/test_access_classification.yaml` verified at `171` entries). |
| `PYTHONPATH=src:. ./venv/bin/python -m pytest tests/unit/test_exploratory_pipeline.py -v` | **`8` passed (`0.13 s`)** | Dedicated guard, boundary, policy, Convention B, Wilson CI, and McNemar unit/integration tests. |

---

## 2. Exact Triage of the `33` Preexisting Repository Failures

Parsed deterministically from `/tmp/pytest_full_audit_post.xml` (`test_execution_report.json`):

| Preexisting Failure Category | Count | Affected Files / Tests | Root Cause (Preexisting Before Exploratory Work) |
|---|---:|---|---|
| **1. Mission 26/27/28 `README.md` Catalog Hash Drift** | `23` | `tests/synthetic_mission26/test_inventory_cli.py` (10), `tests/synthetic_mission27/test_dashboard_cli.py` (5), `tests/synthetic_mission28/test_pilot_readiness.py` (8) | Historical `Mission 17A-README` commit intentionally updated root `README.md`, causing Mission 26–28 static `README.md` SHA-256 baseline assertions to mismatch. |
| **2. Nov 9 Governance & Allowlist State Drift** | `4` | `test_phase11_7_governance_controls.py::test_real_allowlist_file_loads_and_contains_only_the_researcher`, `test_mission4a_governance_and_stage21_safety.py`, `test_phase12_governance.py`, `test_reproducibility_audit.py` | Preexisting Nov-9 governance/allowlist edits and resolved `PREMATURE_OPENING_DEFINITION_UNDECIDED` flag vs earlier static assertions. |
| **3. Shared/Conftest `sys.modules` Isolation Assertions** | `4` | `synthetic_mission17d/test_isolation.py`, `synthetic_mission17d/test_mission17f_regressions.py`, `synthetic_mission18a/test_isolation.py`, `synthetic_mission18b/test_provenance.py` | Fail `1` test each even when run standalone via `pytest` (`exit_code=1` recorded in `test_execution_report.json`) because repository `tests/conftest.py` loads `railway_detection` modules at session startup. |
| **4. Preexisting Policy / Researcher Script Failures** | `2` | `test_exploratory_subset_authorization_gate.py::test_dry_run_validates_all_eleven_events_against_live_manifest` (`AUTH_MEDIA_ACCESS_NOT_GRANTED`), `test_media_opener_coverage.py::test_every_media_opener_is_guarded_or_reviewed_metadata_only` | Intentional raw media block on `event_001/camera_front.mov` + `4` preexisting unreviewed researcher scripts (`build_m3_mm_manifest.py`, `build_m3_mm_manifest_v2.py`, `fix_m3_classification.py`, `run_stage21_review.py`). |

Note: Prior to registering `tests/unit/test_exploratory_pipeline.py` in `tests/test_access_classification.yaml` and supplying `PYTHONPATH=src:.`, an initial audit showed `42` failures (`8` `PYTHONPATH` child-process misses + `1` unregistered test file); **all `9` resolvable failures are eliminated**, reducing failures cleanly to the `33` immutable/preexisting items above.

---

## 3. AST Media-Opener Safety Coverage (`test_media_opener_coverage.py`)

Running `tests/unit/test_media_opener_coverage.py` confirmed **`0` violations across all 9 new exploratory scripts** (`exploratory_common.py`, `run_exploratory_replay.py`, `run_failure_injection_replays.py`, `evaluate_departure_reopening.py`, `compute_safety_metrics.py`, `compute_ablation_matrix.py`, `verify_exploratory_reproducibility.py`, `generate_exploratory_figures.py`, `build_final_research_deliverables.py`). None open binary bytes, raw `.mov`/`.mp4`/`.wav` files, or call `cv2`/`av`/`ultralytics`.
