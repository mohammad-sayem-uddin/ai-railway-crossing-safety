# Mission 21 — Detailed phase execution log

Each commit/push receipt is filled after normal delivery and carried in the next phase documentation commit. No report can embed its own final commit hash.

## WP01

Status: PASS_SYNTHETIC_INTEGRATION. Parent: `e72f248d42668f7d33eaac439c91cd73dc91432a`. Commit: `79fa0ce5af2e5ada1dbc7e38efe4740c2f3b2496`. Remote verified: True.

Implemented explicit EventSimulationRunner.run_frames_convention_b, typed constructed snapshot/request/result, real existing-controller and scripted numerical fixtures, native rejection correspondence, ARRIVAL/OFFLINE ordering, exact clock/angle, cutoffs/prefixes, NONE watchdog, exact event/continuous/fixed estimators via existing actuator, full deterministic detached-candidate replay and8192-frame envelope. Existing A implementation unchanged. Initial run44 passed/3 failed because native missing-sensor age infinity could not be canonicalized; explicit nonfinite-age sentinel fixed that production adapter bug. Final62 integration cases and238 original cases pass; original suite emits5 existing JUnit record_property warnings.

Exact files: src/railway_detection/simulation/runner.py, src/railway_detection/synthetic/convention_b_pipeline.py, tests/synthetic_mission18a/conftest.py, tests/synthetic_mission18a/test_convention_b_integration.py, tests/synthetic_mission18a/test_isolation.py
Tests: [{"xml": "/tmp/mission21_wp01.xml", "command": "PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest --confcutdir=tests/synthetic_mission18a -p no:cacheprovider --import-mode=importlib tests/synthetic_mission18a -q --junitxml=/tmp/mission21_wp01.xml", "tests": 62, "failures": 0, "errors": 0, "skipped": 0}, {"xml": "/tmp/mission21_wp01_legacy.xml", "command": "PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest --confcutdir=tests/synthetic_mission17d -p no:cacheprovider --import-mode=importlib tests/synthetic_mission17d -q --junitxml=/tmp/mission21_wp01_legacy.xml", "tests": 238, "failures": 0, "errors": 0, "skipped": 0}]
Static: Python3.11.15; AST5 files; Ruff new pipeline/tests passes. Full legacy runner check reports one pre-existing E501 at original rejected-step lambda, outside R02-A B-entrypoint-only edit scope. No Mypy pass; R14-A adopted for bounded engineering.
Remaining: Constructed-origin envelope and code_identity are retained caller assertions, not external authentication. Full replay shares producer logic and is supplemented by exact independent geometric tests. No hardware clock, protected controller data, scientific GT, operational safety or OS sandbox claim. Missing/future/caller-substituted trusted expectations are outside cooperative trust. Historical two18A blocker reports among the seven preserved files remain unchanged; this current report supplies superseding engineering acceptance.
Next phase: WP02 grouped-CV fitted-artifact and OOF provenance

## WP02

Status: PASS_CONSTRUCTED_REGISTRY_ADAPTER. Parent: `79fa0ce5af2e5ada1dbc7e38efe4740c2f3b2496`. Commit: `None`. Remote verified: False.

Added immutable versioned registry/expected-context/receipt interfaces, existing physical-event/allocation/role recomputation, complete iterative artifact ancestry, FIT/SELECT/initialization and fitted asset-producer exposure, exact event/asset/vocabulary/fold/score binding, coverage/duplicate and unresolved-near-duplicate denial, NONE/inner-OOF/reserved-calibration/frozen-refit compositions and detached receipt verification. Existing helper APIs and their unverified-OOF denial remain unchanged; no live splitter/backend is wired. Strict boolean receipt rejection prevents Python True==1 equality laundering. Corrected WP01 lint receipt: the new pipeline/tests pass Ruff, while the legacy runner has one baseline E501 outside the allowed B-only change.

Exact files: src/railway_detection/experiments/provenance_registry.py, tests/synthetic_mission18b/conftest.py, tests/synthetic_mission18b/test_provenance.py
Tests: [{"xml": "/tmp/mission21_wp02.xml", "command": "PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest --confcutdir=tests/synthetic_mission18b -p no:cacheprovider --import-mode=importlib tests/synthetic_mission18b -q --junitxml=/tmp/mission21_wp02.xml", "tests": 26, "failures": 0, "errors": 0, "skipped": 0}]
Static: Ruff new module/new tests passes; Python3.11.15; standard-library+existing pure grouped_cv imports; no Mypy pass yet
Remaining: Pure constructed metadata verifier, not authentication, actual fit/prediction/calibration, official split, real corpus eligibility, provenance discovery or model independence certification. Actual scientific registry/exposure evidence remains missing; no real backend adapter activated. Synthetic expected-context ownership remains cooperative.
Next phase: WP03 blind human-review domain and synthetic player
