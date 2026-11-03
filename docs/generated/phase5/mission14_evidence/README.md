# Mission 14 evidence

* `mission14_synthetic_test_report.json` — safe-runner report (status PASSED, 2,198 tests, 100 files, 0 blocked).
* `probe_before_mission14.txt` / `probe_after_mission14.txt` — the Mission 13 synthetic probes
  (`../mission13_probes/*.py`) run against (a) a scratch copy of `src/` with the Mission 14 pre-edit
  backups swapped in and (b) the repository as it is now. In the "before" file the case-variant
  lines of `probe_case` are not meaningful: the scratch copy's `REAL_REPO_ROOT` is the scratch
  directory. The Mission 13 report holds the original case-variant observation. In the "after"
  file `probe_media.py` ends in a traceback at its `H1` case: the validator now *propagates* the
  denial instead of swallowing it (F13-07), which is the intended new behavior.
* All probes use synthetic temporary trees and fake repository paths only.
* `../mission14_tools/smoke_http_dashboard.py` is the real-socket dashboard smoke test (synthetic tree).
