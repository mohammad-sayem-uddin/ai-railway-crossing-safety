# Mission 26 — Evidence acquisition and real-data authorization readiness

Prepared 2026-11-05, America/New_York. The metadata inventory, evidence requirements, operation-specific preflight engine and local readiness CLI are implemented. Genuine evidence acquisition and scientific execution remain blocked on actual source, rights, human and authorization evidence.

Mission 25's exact final delivery is `e8a96a15d4d29d92dc009ee1eea98767a09417ad`, verified in Git history. Mission 26's documentary package was committed at `d714c1c`; its preflight engine, CLI, schema and tests were committed at `64d766d81e652c94523433b8e4212946413368e7`. Before final delivery, local `main`, tracking `origin/main` and live remote `main` matched that implementation commit. The containing final documentation commit supplies the acceptance and delivery records; its exact hash is reported after normal push verification.

## Delivered evidence infrastructure

| Area | Delivered artifact or implementation | Current evidence limit |
|---|---|---|
| Dataset/source inventory | `MISSION_26_DATASET_AND_SOURCE_INVENTORY.md`; bound catalog | 27 candidates: 23 train, three no-train, one engine-only. 54 documentary camera references, two excluded duplicate references and seven collection/model references. Physical identity/accessibility and inventory signoff remain unverified. R04 stays exactly 11. |
| Rights/provenance | `MISSION_26_DATA_RIGHTS_AND_PROVENANCE_REGISTER.json` | 63 documentary rows; 62 RIGHTS_UNKNOWN and one RIGHTS_PARTIALLY_DOCUMENTED. Ten distinct use/storage/processing/annotation/training/evaluation/publication/sharing/redistribution/release dimensions retained. Collection rows do not establish complete individual-recording rights. |
| Human participation | `MISSION_26_HUMAN_PARTICIPATION_REQUIREMENTS.md`; six catalog role rows | Actual identities, appointments, qualifications, independence/conflict declarations, participation documentation and current source access remain missing. Researcher status does not confer independent-review qualification. |
| External applicability | `MISSION_26_INSTITUTIONAL_AND_EXTERNAL_APPLICABILITY.md`; nine catalog rows | UNKNOWN_REQUIRES_VERIFICATION against actual project/institution/owners/participants and applicable rules. No universal ethics/railway requirement or exemption is invented. Release and deployment restrictions remain separate. |
| Physical boundaries | `MISSION_26_PHYSICAL_LANDMARK_EVIDENCE_REGISTER.md`; four catalog rows | T1 adopted approach/frog line; T3 adopted locomotive-unit clearance; T4 adopted tail clearance. Physical T2 remains deferred. No geometry, exit landmark, lens-plane substitution or acoustic GT shift. |
| Duration compatibility | `MISSION_26_DURATION_FLOOR_COMPATIBILITY_REPORT.md`; `duration_compatibility` | Active 8.1 canonical plausibility validator retained unchanged. The diagnostic adapter invokes it without constructing a record or padding timing. RD046 scientific sufficiency remains deferred; no new researcher decision is required for this adapter. |
| Operation readiness | `MISSION_26_RESOURCE_OPERATION_PREFLIGHT.json` | Exact 27 historical operation decisions preserved: 21 selected conditionally but blocked; six denied/deferred. No grants, authorized operations or execution. |
| Scientific readiness | `MISSION_26_EXPERIMENT_READINESS_MATRIX.json` | Six planned condition rows, including separately deferred comparator mapping. No experiment was executed. |
| Machine interfaces | `application/preflight/engine.py`, `catalog.py`, `MISSION_26_PREFLIGHT_SCHEMA.json` | Sixteen exact evidence kinds; no executor or genuine verification adapter is supplied. Runtime semantics supplement the structural schema. |
| Dashboard | `MISSION_26_REAL_DATA_READINESS_DASHBOARD.md`, `MISSION_26_READINESS_DASHBOARD.json` | Machine register values, source references, missing prerequisites and distinct selected/authorized/executed states. Fixed-clock replay is diagnostic. |

The installed Ultralytics, PyTorch, torchvision, NumPy, OpenCV and PyYAML license metadata contains nine retained license-file references. Their actual local text digests were independently reverified. Upstream [ESC-50 license documentation](https://github.com/karolpiczak/ESC-50#license), [Creative Commons terms](https://creativecommons.org/licenses/by-nc/3.0/) and [Ultralytics license text](https://github.com/ultralytics/ultralytics/blob/main/LICENSE) support the existing documentary findings. Software terms and upstream collection terms do not establish the identity, rights or permitted purpose of this project's exact field recordings or checkpoints.

## Reproducible commands and enforcement

Generate the current readiness report without opening any source resource:

```sh
PYTHONPATH=src:. PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m railway_detection application readiness report --now 0
```

Add `--format json` for all source rights, role, landmark, external, operation and experiment rows. The explicit clock value `0` supports deterministic comparison; it is not an authorization date or trusted time service. Report generation exits zero while all real operations remain blocked.

Inspect one exact documentary resource and operation:

```sh
PYTHONPATH=src:. PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m railway_detection application readiness check --operation M19-PERM-02 --resource doc:v2:train_events/event_001:front:video --now 0
```

The current check exits 3 with explicit blockers. An unknown operation/resource or filesystem resource path exits 2. A documentary row digest checks metadata consistency; it is never represented as a freshly verified media identity. Dashboard operation rows explicitly label their example source as diagnostic and leave each actual operation-resource package null.

The engine checks source identity, rights, actor, role, purpose, environment, permission basis, validity/expiry, revocation, technical and human prerequisites, protocol, schema, provenance, logging and output. A complete constructed checklist can reach PREFLIGHT_READY_FOR_AUTHORIZATION_REVIEW and then AUTHORIZATION_REVIEW_PENDING. It cannot issue permission or execute anything. AUTHORIZED_NOT_EXECUTED and EXECUTION_COMPLETED_WITH_VALID_RECEIPT require separately verified existing canonical authorization/receipt evidence through an external adapter; the shipped configuration has no such adapter. Every executor call refuses. Existing point-of-use guards and canonical validators remain authoritative.

First-review and pilot preparation require their prospective qualified actor/assignment/access evidence, without a circular requirement for future completed GT. Adjudication requires the actual independent review parents; promotion and evaluation require completed actual GT. Active canonical review-record consumption also requires unchanged duration/schema acceptance. Fixtures never become human evidence.

## Validation and its limits

Exact counts and commands are in `MISSION_26_FINAL_VALIDATION.json` and the bound receipts. Final selected acceptance contains each case once; previous runs and included WP01–WP10/Mission subsets are never added together. The retained complete guarded audit and current selected run bind the same unchanged implementation and metadata inputs.

| Validation scope | Cases | Passed | Failed | Setup errors | Skipped | Not executed |
|---|---:|---:|---:|---:|---:|---:|
| Complete guarded audit, 160 modules | 3,646 | 3,528 | 87 | 31 | 0 | 0 |
| Final selected resource-free acceptance | 3,528 | 3,528 | 0 | 0 | 0 | 118 protected dependencies |
| New constructed Mission 26 suite, included above | 98 | 98 | 0 | 0 | 0 | 0 |

All 3,430 Mission 25 selected cases and the exact previous 118 protected case IDs are preserved. The Mission 26 source-bound register has zero unknown classifications, stale bindings or missing modules. The legacy YAML inventory remains a separate conservative source inventory; it is not used to claim Mission 26 executed acceptance. The full guarded audit is nonpassing, and unavailable protected cases do not establish whole-repository acceptance.

The first delivery run encountered operating-system restrictions on constructed localhost sockets and a native macOS Matplotlib abort: 3,376 passed, three failed, and one 149-case process produced no JUnit results. Those missing results are not passes. The final complete selected run used approved escalation, with the inherited Python deny policy, temporary fixture isolation and child-process checks still installed. No test, guard or classification was weakened. The first run remains development evidence under `/private/tmp/m26_delivery_profile_20261105`; the final receipt comes from `/private/tmp/m26_delivery_profile_loopback_20261105`. Python audit hooks are cooperative regression guards, not an OS security claim.

Ruff and AST syntax checks pass on eight implementation/test files; scoped Mypy passes on five sources using the established `--follow-imports=silent --ignore-missing-imports` options. An initial broader import-following check reported 52 errors in 14 preserved imported modules; these were not repaired or represented as type-clean. Six relevant source-module imports and `pip check` pass. No package installation or canonical-validator change was needed. Git connectivity validation passes; existing dangling objects remain preserved.

`MISSION_26_ADVERSARIAL_CASE_RECEIPT.json` records all 98 case expectations/assertions, actual outcomes and boundaries. Cases cover missing or conflicting rights; altered identities/manifests; wrong actor/role/purpose; expiry/revocation; absent external, human, independence/conflict and physical-landmark evidence; lens-plane/acoustic substitutions; schema/duration/provenance; stale receipts; duplicate requests; output/log restrictions; constructed evidence promotion; and incomplete batches. Successful refusals are engineering evidence, never successful real-data execution.

The actual CLI demonstration receipt records two identical JSON reports, the Markdown report, blocked conditional/denied checks and invalid-path refusal with expected exits `0,0,0,3,3,2`, and zero policy denials. Acceptance also exercises deterministic workflow/journal replay and metadata tampering refusals.

## Remaining genuine evidence prerequisites

1. Establish each exact source/resource manifest and provenance chain through separately authorized verification. Supply individual member identities and rights for incomplete collection references; retain candidate-only status and excluded duplicates until genuine signoff.
2. Supply actual owner/license documentation for each intended right and operation, with restrictions, permitted storage/output/recipients and current validity/revocation evidence. Resolve conflicting terms without treating repository presence or earlier experimental use as permission.
3. Establish the actual institutional, participant, site-owner and privacy circumstances; obtain scoped applicable evidence or attributable non-applicability determinations from the relevant actual authority. Maintain R-PUB and denied raw release independently.
4. Appoint actual qualified reviewers, independent second reviewers and adjudicators where required; verify identity, qualifications, conflicts, consent/applicable documentation, scope, expiry and revocation. Connect authenticated/blinding-aware source-player, evidence, persistence and publication adapters before genuine review. Preserve original observations and unresolved UNCERTAIN states.
5. Acquire physical T2 landmark evidence and actual source/camera calibration/uncertainty/adoption support before physical-entry or occupancy claims. Keep all deferred geometry and measurements unknown until supported.
6. Bind the adopted protocol/schema/configuration, complete human/GT and per-metric eligibility evidence, exact source/model/cache identities, current operation-specific canonical authority, logging and output policy before each scientific operation. Preserve descriptive single-site scope, M4 primary/M5 integer companion, MTR censoring limitations, independent-camera primary analysis and exploratory fusion/supporting audio restrictions. Do not activate comparator mapping, inferential tests, all-weather/cross-site claims or performance/safety improvements.

The seven pre-existing researcher work files and all 70 retained Mission 21–25 artifacts remain byte-identical and unstaged. No raw media was opened, previewed, decoded, hashed or played; no production checkpoint/cache or real review corpus was accessed. No training, calibration, real inference/replay/evaluation, official split, human annotation/adjudication, GT promotion, external release or physical deployment was performed.
