# Mission 26 — Real-data readiness dashboard

Metadata-only readiness. No new permission, real operation, human observation or result.

Candidate inventory: 27 = 23+3+1; 54 current camera references; R04 exact 11. Documentary consistency verified; physical/source identity and signoff remain unverified.

| Operation | Selection | State | Missing prerequisite count |
|---|---|---|---:|
| M19-PERM-01 — READ_RAW_MEDIA / preview | A | PREFLIGHT_BLOCKED | 33 |
| M19-PERM-02 — READ_RAW_MEDIA / playback/decode | A | PREFLIGHT_BLOCKED | 33 |
| M19-PERM-03 — READ_RAW_MEDIA / playback/decode | A | PREFLIGHT_BLOCKED | 33 |
| M19-PERM-04 — MEDIA_PROBE | A | PREFLIGHT_BLOCKED | 33 |
| M19-PERM-05 — HASH_RAW_MEDIA | A | PREFLIGHT_BLOCKED | 33 |
| M19-PERM-06 — FRAME_EXTRACTION / named preprocessing | A | PREFLIGHT_BLOCKED | 33 |
| M19-PERM-07 — READ_PROCESSED_DATA / validate metadata and derived arrays | A | PREFLIGHT_BLOCKED | 33 |
| M19-PERM-08 — READ_CACHE / replay cache bytes | A | PREFLIGHT_BLOCKED | 33 |
| M19-PERM-09 — HASH_CHECKPOINT | A | PREFLIGHT_BLOCKED | 33 |
| M19-PERM-10 — LOAD_CHECKPOINT / read parameters | A | PREFLIGHT_BLOCKED | 33 |
| M19-PERM-11 — INFERENCE | A | PREFLIGHT_BLOCKED | 33 |
| M19-PERM-12 — TRAIN_MODEL / fit preprocessor | B | EXECUTION_NOT_PERMITTED | 1 |
| M19-PERM-13 — FIT_CALIBRATOR / threshold selection | B | EXECUTION_NOT_PERMITTED | 1 |
| M19-PERM-14 — REPLAY_REAL_DATA | A | PREFLIGHT_BLOCKED | 33 |
| M19-PERM-15 — EVALUATE_DESCRIPTIVE_REAL | A | PREFLIGHT_BLOCKED | 34 |
| M19-PERM-16 — EVALUATE_OFFICIAL | B | EXECUTION_NOT_PERMITTED | 1 |
| M19-PERM-17 — CREATE_MANIFEST / version metadata | A | PREFLIGHT_BLOCKED | 33 |
| M19-PERM-18 — CREATE_OFFICIAL_SPLIT | B | EXECUTION_NOT_PERMITTED | 1 |
| M19-PERM-19 — HUMAN_REVIEW | A | PREFLIGHT_BLOCKED | 33 |
| M19-PERM-20 — ADJUDICATE | A | PREFLIGHT_BLOCKED | 34 |
| M19-PERM-21 — PROMOTE_GT | A | PREFLIGHT_BLOCKED | 34 |
| M19-PERM-22 — EXPORT_METADATA | A | PREFLIGHT_BLOCKED | 33 |
| M19-PERM-23 — PUBLIC_SHARE / RELEASE | A | PREFLIGHT_BLOCKED | 33 |
| M19-PERM-24 — PUBLIC_RAW_MEDIA_RELEASE | B | EXECUTION_NOT_PERMITTED | 1 |
| M19-PERM-25 — PRODUCTION_DEPLOYMENT / physical actuation | B | EXECUTION_NOT_PERMITTED | 1 |
| M19-PERM-26 — EXECUTE_HUMAN_PILOT | A | PREFLIGHT_BLOCKED | 33 |
| M19-PERM-27 — ANNOTATE | A | PREFLIGHT_BLOCKED | 33 |

Source rights, participation, landmark, external applicability and experiment details remain in the bound JSON dashboard/catalog. Unknown is distinct from denied. Selected is distinct from authorized; authorized is distinct from executed.

Authorized-but-not-executed operations: 0. Completed operations: 0. This readiness command cannot execute an operation.

Reproduce the current documentary report from the checkout:

```sh
PYTHONPATH=src:. PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m railway_detection application readiness report --now 0
```

Clock0 is an explicit reproducible diagnostic input, not a permission/decision date or trusted authority clock. Use `--format json` for the full source rights, human roles, landmarks, external requirements, operations and experiment matrix with original references. To inspect an exact selected source without executing it:

```sh
PYTHONPATH=src:. PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m railway_detection application readiness check --operation M19-PERM-02 --resource doc:v2:train_events/event_001:front:video --now 0
```

The blocked check exits3; invalid operation/resource/metadata exits2; report generation exits0 without certifying any operation. No arbitrary resource filesystem path is accepted. Catalog/document hashes are cooperative consistency checks, not independent identity, license or consent authentication. Unknown rights stay unknown; a project denied/deferred release remains denied independently of possible owner license terms.

The engine has no execution backend. All sixteen prerequisite evidence kinds must bind exact request, operation, resource, actor, purpose, environment, protocol/schema/provenance/log/output and current time/revocation. Genuine evidence requires a separately supplied authoritative verifier; no such adapter ships. Existing canonical authorization/receipt validators must be implemented behind that verifier; this engine neither replaces them nor issues a global token. Constructed successful checklists can only queue a constructed authorization-review request. They cannot create genuine authorization, execution, review, adjudication or GT.

First review, annotation and pilot require their prospective qualified actor/assignment/access/procedure evidence; they do not require a future completed GT batch. Adjudication requires its independent review parents. Promotion/evaluation require completed actual GT. Canonical duration compatibility applies when an active8.1 record is consumed; pilot/read-only metadata can explicitly state that no canonical review record is involved, without inventing a scientific floor.

Lifecycle: PREFLIGHT_NOT_STARTED → PREFLIGHT_BLOCKED or PREFLIGHT_READY_FOR_AUTHORIZATION_REVIEW → AUTHORIZATION_REVIEW_PENDING. Externally verified canonical exact-operation authorization may be recorded as AUTHORIZED_NOT_EXECUTED; independently verified execution receipts require the exact current authorization parent before reporting EXECUTION_COMPLETED_WITH_VALID_RECEIPT. The shipped configuration can never take those genuine-positive transitions. EXECUTION_NOT_PERMITTED applies to the six B selections and any attempted executor call. Authorization/execution receipt metadata is not an instruction to execute; actual services retain every point-of-use guard.

Snapshot fields are inspected without dereferencing source paths. The63 documentary rows comprise54 current camera references,2 excluded camera references and7 collection/model references; they are not63 verified physical sources. Complete individual-source rights/member registries for the collection rows remain missing.
