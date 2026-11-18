# Forensic Audit of `UNKNOWN`-Classified Test Files (Mission 4, Task 5)

**Access Registry:** [`tests/test_access_classification.yaml`](file:///Users/sayemuddin/Desktop/Train_automation/tests/test_access_classification.yaml)  
**Classifier:** [`scripts/classify_test_access.py`](file:///Users/sayemuddin/Desktop/Train_automation/scripts/classify_test_access.py)  
**Access Guard Plugin:** [`src/railway_detection/safety/access_guard_plugin.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/safety/access_guard_plugin.py)  

---

## 1. Root-Cause Bug Fixed in `access_guard_plugin.py`

During the Task 5 audit of single-file test classification under `access_guard_plugin.py`, [`tests/synthetic_mission22/test_regression_policy.py`](file:///Users/sayemuddin/Desktop/Train_automation/tests/synthetic_mission22/test_regression_policy.py) previously recorded **`tests: {passed: 0, failed: 1}`** inside `tests/test_access_classification.yaml`.

- **Exact Defect:** `guarded_popen_init` passed an inline multi-line `python -c` script argument containing `"data/raw/never_opened"` to `guard.check_read(candidate, "subprocess-arg")`. On macOS, calling `Path(os.path.realpath(os.fspath(path))).is_dir()` directly in `check_read()` raised `OSError: [Errno 63] File name too long` (`ENAMETOOLONG`) before `subprocess.run` could execute.
- **Minimal Non-Weakening Fix:** Added `_Guard._safe_is_dir()` in [`access_guard_plugin.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/safety/access_guard_plugin.py) catching `(OSError, ValueError, TypeError)` only on the `.is_dir()` metadata probe while keeping `categorize()` and `RAW_MEDIA` / `MODEL_CHECKPOINT` / `PROCESSED_DATA` blocking unchanged, plus regression coverage in [`tests/unit/test_access_classification_tools.py`](file:///Users/sayemuddin/Desktop/Train_automation/tests/unit/test_access_classification_tools.py) (`test_guard_handles_long_inline_python_subprocess_args`).
- **Measured Result:** Running `tests/synthetic_mission22/test_regression_policy.py` directly under `-p railway_detection.safety.access_guard_plugin` now passes **`1 passed` (`0` failed)**.

---

## 2. Per-File Verdict Across All `9` `UNKNOWN` Tests

In [`scripts/classify_test_access.py`](file:///Users/sayemuddin/Desktop/Train_automation/scripts/classify_test_access.py), a file may only exit `UNKNOWN` into `SYNTHETIC_ONLY`/`METADATA_ONLY` via `GUARDED_SPAWNERS` if **every child process it launches is a Python test runner loading `access_guard_plugin`**. Reclassifying OS/CLI/native spawners without that runtime guarantee would weaken classification boundaries and is intentionally **not** done.

| # | Test File | Dynamic Blocked Reads | Why `spawns_child_process = True` | Why `UNKNOWN` Is Scientifically Honest | Safe Status in Audit |
|---|---|---|---|---|---|
| 1 | [`tests/synthetic_mission17d/test_isolation.py`](file:///Users/sayemuddin/Desktop/Train_automation/tests/synthetic_mission17d/test_isolation.py) | `0` | Launches fresh interpreter `[sys.executable, "-B", "-c", code]` & references `subprocess.Popen` in IO-denial test | Fresh-interpreter child `python -c` does not load pytest `access_guard_plugin` | `6/6` passed under guard + full pytest; touches `0` real data |
| 2 | [`tests/synthetic_mission18a/test_isolation.py`](file:///Users/sayemuddin/Desktop/Train_automation/tests/synthetic_mission18a/test_isolation.py) | `0` | Launches fresh interpreter `[sys.executable, "-c", code]` & references `subprocess.Popen` in IO-denial test | Fresh-interpreter child `python -c` does not load pytest `access_guard_plugin` | `6/6` passed under guard + full pytest; touches `0` real data |
| 3 | [`tests/synthetic_mission22/test_crash_and_adversarial.py`](file:///Users/sayemuddin/Desktop/Train_automation/tests/synthetic_mission22/test_crash_and_adversarial.py) | `0` | Spawns child Python triggering SQLite trigger `os._exit(73)` crash recovery inside `tmp_path` | `os._exit(73)` requires a real child OS process outside in-process pytest | `15/15` passed under guard + full pytest; `tmp_path` SQLite only |
| 4 | [`tests/synthetic_mission22/test_regression_policy.py`](file:///Users/sayemuddin/Desktop/Train_automation/tests/synthetic_mission22/test_regression_policy.py) | `0` | Spawns child `python -c` with custom `sitecustomize.py` testing `mission22_policy` | Exercises child OS `sitecustomize` + `PYTHONPATH=''` refusal | **`1/1` passed** (was `0/1` before `access_guard_plugin.py` fix); `tmp_path` only |
| 5 | [`tests/synthetic_mission22/test_workflow.py`](file:///Users/sayemuddin/Desktop/Train_automation/tests/synthetic_mission22/test_workflow.py) | `0` | Spawns CLI `scripts/run_mission22_demo.py` (`--interrupt-after` / `--resume`) + `python -c` | Verifies genuine standalone CLI signal/process restart | `25/25` passed under guard + full pytest; writes strictly to `tmp_path` |
| 6 | [`tests/synthetic_mission24/test_application.py`](file:///Users/sayemuddin/Desktop/Train_automation/tests/synthetic_mission24/test_application.py) | `0` | Spawns CLI `python -m railway_detection application demo` (`--interrupt-after` / `--resume`) | Verifies production CLI entrypoint interruption recovery | `25/25` passed under guard + full pytest; `tmp_path` only |
| 7 | [`tests/synthetic_mission25/test_integration.py`](file:///Users/sayemuddin/Desktop/Train_automation/tests/synthetic_mission25/test_integration.py) | `0` | Spawns CLI `python -m railway_detection application review` (`interface`/`demo`/`verify`/`dashboard`) | Verifies CLI exit codes & refused duplicate execution cleanly | `31/31` passed under guard + full pytest; `tmp_path` only |
| 8 | [`tests/synthetic_mission44/test_display_rotation.py`](file:///Users/sayemuddin/Desktop/Train_automation/tests/synthetic_mission44/test_display_rotation.py) | `0` (`configs/` read) | Spawns native binary `ffmpeg -display_rotation:v:0 ...` on synthetic PyAV `.mp4` in `tmp_path` | Native C binary `ffmpeg` cannot execute under Python pytest plugin | `9/9` passed under guard + full pytest; generated pixels only |
| 9 | [`tests/synthetic_tooling/test_restored_mypy.py`](file:///Users/sayemuddin/Desktop/Train_automation/tests/synthetic_tooling/test_restored_mypy.py) | `0` (`pyproject.toml`, `requirements.lock` reads) | Spawns `[sys.executable, "-m", "mypy", ...]` & `.venv/bin/mypy` on synthetic `valid.py`/`invalid.py` in `tmp_path` | Native/CLI typechecker process runs outside Python pytest plugin | `15/15` passed under guard + full pytest; `tmp_path` files only |

**Conclusion:** All `9/9` `UNKNOWN` classifications pass `100%` of their tests (`133/133` tests across the 9 files, `0` failed, `0` blocked reads), operate strictly on `tmp_path` fixtures or safe metadata, and legitimately retain `UNKNOWN` status in `tests/test_access_classification.yaml` rather than diluting `GUARDED_SPAWNERS`.
