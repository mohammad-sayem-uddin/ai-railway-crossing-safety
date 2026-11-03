# Mission 5A.1 — Test Results

All tests are synthetic-only. Environment: `.venv` Python 3.11, run from the repo root with `PYTHONDONTWRITEBYTECODE=1` and `-p no:cacheprovider`. No integration/smoke test, real-inventory test, audio/vision test, official readiness gate, or media-touching test was run.

## 1. Test provenance (production vs test-local)
| File | Exercises production code? |
|---|---|
| `tests/unit/test_mission5a_production.py` | **Yes** — `classify_m4`, `evaluate_run`, `aggregate_cohort`, `resolve_event_cohort`, lead-in screen, proposed-schema module, in-code register, manifest tool. Its protocol-wording class checks document text. |
| `tests/unit/test_mission5a1_audit_regressions.py` (new) | **Yes** — same production functions + the manifest tool + `ExperimentRunner._extract_event_ground_truth`; includes `test_open_*`-style characterization of unresolved decisions. |
| `tests/unit/test_mission4e2_m4_occupancy_contract.py` | Part 1 **yes** (production M4/M5); **Part 2 (occupancy) uses a test-local reference function** — occupancy has no production implementation (deferred); labelled as such. |
| existing metric/arithmetic/event-metric tests | yes (production) |

## 2. Commands and results
| # | Command | Result |
|---|---|---|
| 1 | `.venv/bin/python -m pytest tests/unit/test_mission5a1_audit_regressions.py -p no:cacheprovider -q` | **68 passed** |
| 2 | `.venv/bin/python -m pytest tests/unit/test_mission5a_production.py -p no:cacheprovider -q` | **88 passed** |
| 3 | `.venv/bin/python -m pytest tests/unit/test_mission4e2_m4_occupancy_contract.py -p no:cacheprovider -q` | **57 passed** |
| 4 | `.venv/bin/python -m pytest tests/unit/test_event_metrics.py tests/unit/test_mission2_pipeline_integrity.py tests/unit/test_mission3_reproducibility_and_provenance.py tests/unit/test_mission4a_governance_and_stage21_safety.py tests/unit/test_mission4d_governance_integrity.py tests/unit/test_mission4e2_m4_occupancy_contract.py tests/unit/test_mission5a_production.py tests/unit/test_mission5a1_audit_regressions.py tests/unit/test_phase12_documented_metrics.py tests/unit/test_phase12_metric_arithmetic.py tests/unit/test_phase12_governance.py tests/unit/test_phase12_input_contracts.py tests/unit/test_phase12_official_replay.py tests/unit/test_phase12_evaluation_runner.py tests/unit/test_reproducibility_audit.py tests/unit/test_research_contracts.py tests/unit/test_cache_phase12_adapter.py tests/test_phase12_ground_truth_loader.py tests/test_phase11_12_readiness_gate.py tests/test_phase11_cohort_qualified_identity.py -p no:cacheprovider -q` | **674 passed** (606 at the end of Mission 5A + 68 new) |
| 5 | `.venv/bin/ruff check src/railway_detection/evaluation/metrics.py scripts/mission5a_build_preservation_manifest.py tests/unit/test_mission5a_production.py tests/unit/test_mission5a1_audit_regressions.py --no-cache` | **All checks passed** (ruff 0.16.3 already in `.venv`; nothing installed) |
| 6 | `python3 scripts/mission5a_build_preservation_manifest.py verify --root . --manifest docs/generated/mission_5a/REPRODUCIBILITY_MANIFEST_20261101_M5A.json` | at audit start: 858 ok, clean. At audit end: 855 ok, **exactly 3 changed** (`metrics.py`, the manifest tool, `test_mission5a_production.py`), 0 missing, 0 refused — the three files edited by 5A.1 |

An intermediate run failed (2 tests) when the first draft of the fixes was applied; those failures led to (a) reverting the replay-start fix and (b) correcting a contradictory fixture in my own 5A test. See the change log.

## 3. Pre-fix evidence (scratchpad probes, synthetic only; not repository files)
| Probe | Pre-fix result | Post-fix result |
|---|---|---|
| verify with 6 crafted entries (media-like, binary-like, symlink, `../`, absolute) | **6 files opened**, `changed: 6` | **0 opened**, `refused: 6` |
| train event with `has_train_ground_truth=False` | evaluable no-train record | raises |
| no-train event with `has_train_ground_truth=True` | evaluable train record, M4 EVALUABLE | raises |
| unannotated event, bare id, `cohort=None` (5A regression) | (pre-5A) `ground_truth_missing`; (5A) **raises** | `ground_truth_missing` again |
| 3.6 s derivation ×3 at ticks 0.1/0.2/0.25/0.5; default vs frozen-config runner | 3.6/3.6/3.5/3.5, identical for both runners | unchanged (no change made) |
| old vs new engine routing | see identity audit | unchanged |

## 4. Not run, and why
Integration/smoke tests; `test_real_dataset_inventory`, `test_layer_b_loader`, audio/vision/YOLO/pipeline tests (could read real inventories or media); the official readiness gate; any real replay. Consequently **nothing in this mission verifies behaviour on real events** — in particular the diagnostic runner's real Layer-B ids were not examined.
