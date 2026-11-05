# Mission 24 — Unified constructed application

Prepared 2026-11-05, America/New_York. One application namespace wraps the existing WP01–WP10 coordinator. It does not add a parallel simulation, provenance engine, review store or authority ledger.

`ApplicationRequest` binds schema, crossing_A, synthetic event/fixture, deterministic seed and producing Git identity. `EvidenceClass` distinguishes CONSTRUCTED_SYNTHETIC_INPUT, CONSTRUCTED_REVIEW_FIXTURE, UNVERIFIED_EXTERNAL_INPUT and GENUINE_EVIDENCE_PENDING. Only the first enters constructed execution. None of those labels authenticates genuine evidence; the genuine-service boundary refuses all until a real service exists.

`ExistingWorkflowAdapter` consumes the existing coordinator's canonical wire data and emits immutable camera, metric, review, authority and workflow contracts. Arbitrary legacy dictionaries stay within that compatibility adapter. Two exact camera sources preserve origins0/100000µs and independently timed streams; source/config/event identities are retained. Native Convention B retains logical command, applied command, exact rational angle and strict blocked≤45 separately. The typed summary preserves boolean/null M4 and integer0/1/null NEVER_PROTECTED_M5, with reasons for unavailable metrics. Detailed sampled reason/censor/provenance fields remain in the bound nested workflow execution. Separate A diagnostics are not relabeled as B outcomes.

The coordinator now accepts injected review/broker factories, retaining its original implementations as defaults. The application injects typed ports that delegate to those existing transactional services. WP07/WP02 identity, parent/group/role and transitive-exposure joins, WP08 explicit source snapshot, and WP09 results-absent reporting execute unchanged. The declared score and all observations are constructed fixtures; no model fitting/prediction or real human observation is performed.

The public receipt `CONSTRUCTED_APPLICATION/1` binds both camera summaries, metrics, service classifications, inactive comparator outcomes, lineage digest and full workflow execution digest. Application request/result/completion markers form an outer filesystem boundary; the existing workflow owns its nine-artifact set and SQLite transaction/history boundaries. Typed dependency injection permits test/service substitution while output contracts reject construction/event/schema mismatches.

## Commands

Run from the source checkout using the existing virtual environment; no installation or dependency upgrade is needed:

```sh
PYTHONPATH=src:. PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m railway_detection application demo --output /tmp/mission24-application
PYTHONPATH=src:. PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m railway_detection application verify --output /tmp/mission24-application
PYTHONPATH=src:. PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m railway_detection application receipt --output /tmp/mission24-application
PYTHONPATH=src:. PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m railway_detection application architecture
PYTHONPATH=src:. PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m railway_detection application synthetic-test --output /tmp/mission24-application-tests
PYTHONPATH=src:. PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m railway_detection application acceptance --output /tmp/mission24-profile-a
```

Use new explicit output directories outside the checkout. Demo supports exact `--resume`, optional deterministic `--seed` and explicit source `--code-identity`. Default code identity is current Git HEAD; resume after changing HEAD requires retaining the original explicit identity and compatible code. These are cooperative reproducibility labels, not authenticated source attestations.

`synthetic-test` executes only current classified Mission24 application cases, lists the other selected cases outside that command's scope, and reports protected exclusions separately. `acceptance` delegates to the existing resource-free runner with a Mission24 source-bound register. Both reject stale/unknown classification rather than weakening the original Mission23 register or guards. Exit0 means successful declared scope;2 is refusal,3 untrusted classification,75 controlled incomplete execution. Native engine/security/history error receipts retain their own exact reason.

There is no flag for genuine records, comparator activation, back audio, production model/cache/media access, promotion or physical actuation. Application receipt/verify inspects and fully replays constructed output; it is not an independent live DB/authority health audit. Stronger real service/identity/time/storage/OS controls and genuine human evidence remain external work.

Inspect an acceptance execution receipt without claiming current-source or independent attestation:

```sh
PYTHONPATH=src:. PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m railway_detection application validation --receipt docs/generated/master_reaudit/MISSION_24_RESOURCE_FREE_EXECUTION_RECEIPT.json
```

The inspection accepts only named execution metadata, rejects protected-root aliases before reading, verifies exact integer group/totals and inconsistent pass claims, and preserves exclusion counts. It reports internal consistency only. The separate acceptance command validates current source bindings and actually executes selected cases.

## Regression found during complete integration

A complete guarded run exposed an unrelated pre-existing flaky benchmark fixture: the report-equality test injected a stepped clock and host metadata but left lifetime peak RSS measured from the live process. The two reports differed only in that memory field. The fixture now controls RSS too, retaining its full report-equality assertion. A companion application test injects two different RSS readings and verifies that the unchanged benchmark implementation still reports the differing memory values with identical synthetic workload/timing outputs and no performance or safety claim. This is a test-fixture correction, not suppression of measured fields or a new benchmark result.
