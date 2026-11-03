# Overnight Implementation Report — 2026-10-16

**Written for:** the researcher, on return. **Repository:** `/Users/sayemuddin/Desktop/Train_automation`, Git HEAD `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b` (unchanged; nothing staged, committed, pushed, reset or cleaned).
**Session window:** 2026-10-16 ~19:58Z onward. Additive: no historical report was overwritten.

---

## 1. Executive summary

- **Official readiness is still blocked (36 blockers).** Every blocker is missing human evidence or an undecided research decision; none is a verifier defect. No official or real-data evaluation, ablation, benchmark-as-claim or field activity was run or created.
- **The test suite is green for the first time: 1151 passed, 0 failed** (start of session: 931 passed, 3 failed — the brief's "862 passed" was stale). The 3 old failures were missing historical artifacts; they were restored byte-for-byte from the researcher's own iCloud shadow copy after content cross-checks (§6, `docs/HISTORICAL_ARTIFACT_RESTORATION_20261016.md`, with undo commands). Review this call; it is easy to reverse.
- **A real defect would have blocked a genuine corpus:** `event_001` exists in three cohorts, but the readiness gate, readiness CLI, promotion lookups and ground-truth loader keyed per-event data by the bare id (duplicate-approved-record refusal; media/proposal entries overwritten). Fixed with cohort-qualified identity and regression tests built from the corpus shape.
- **"Real" is no longer self-declared:** manifest events must be inventory identities with matching cohort, test events need approved records, and payload media hashes must equal the media the approved reviewer observed.
- **The premature-opening definition is never defaulted:** the evaluator does not compute it unless an explicit, implemented window is supplied; the gate blocks until the researcher chooses.
- **Policy-hash "discrepancy" resolved:** `051c908d…` is the canonical-content hash of the unchanged file whose raw hash is `c87c1432…` (§7).
- New tooling: read-only ground-truth audit with a LEG-EXEC preflight, receipt v2, reproducible benchmark command, capture-session v2 with a fail-closed checklist, and a reproducibility/claim audit that fails the 2026-08-31 progress report on overclaims.

## 2. Files changed and why

**Tracked file edited:** `src/railway_detection/cli/main.py` (new `benchmark run` and `audit reproducibility` commands; previously dirty, now +46 lines of diff).

**Source (new or edited; most live in already-untracked directories, so `git status` shows only the directories):**

| File | Why |
|---|---|
| `annotation/receipt.py` (new) | Shared receipt v2: content-addressed binding of records, allowlist, inventory, active proposals |
| `annotation/readiness_cli.py` | Cohort-qualified inventory/proposal keys; receipt v2 writer |
| `annotation/promotion_gate.py`, `evaluation_readiness_gate.py` | Qualified lookups; duplicate detection per (cohort, event) |
| `annotation/readiness_audit.py` (new) | Read-only audit + LEG-EXEC preflight (verification only, zero writes) |
| `evaluation/execution_gate.py` | Blocker diagnostics (`cause_class`, `insufficient_because`, `verification_evidence`), manifest identity cross-checks, R04 supported-event check, protocol profile and record hashes exposed |
| `evaluation/governance.py` | Receipt v2 verification, `calibration_supported_events`, `documented_r04_candidates` |
| `evaluation/ground_truth_loader.py` | Hash-while-parsing loader; reviewed-media hashes carried |
| `evaluation/evaluation_runner.py` | Undecided-window plumbing, race check on records, media-vs-reviewed check, contract versions in manifests |
| `evaluation/metrics.py`, `clock_aware.py` | `premature_opening_window` has no default; cohort summary states the definition used |
| `evaluation/experiment_engine.py` | Single-variable strictness, input-mutation detection, strict metric-set equality, output-location guard |
| `experiments/runner.py` | Legacy B0–B7 diagnostic runner passes its historical window explicitly, labelled as unaccepted |
| `optimization/benchmark.py`, `benchmark_suite.py`, `benchmark_cli.py` (new) | Reproducible benchmark command, claim discipline, equivalence with property checks |
| `field_validation/capture_session_v2.py` (new) + `__init__` | Capture-session v2, schema, custody, drift, accounting, checklist |
| `reproducibility/audit.py`, `__init__.py` (new) | Reproducibility and manuscript-claim audit |
| `scripts/audit_ground_truth_readiness.py`, `audit_reproducibility.py` (new), `run_phase14_benchmark.py` | Thin wrappers that refuse to write inside repository trees |

**Tests (new/edited):** `tests/test_phase11_cohort_qualified_identity.py`; `tests/unit/`: `official_workspace.py` (fixture), `test_readiness_audit.py`, `test_phase12_governance.py`, `test_phase12_official_replay.py`, `test_phase12_metric_arithmetic.py`, `test_phase12_documented_metrics.py`, `test_event_metrics.py`, `test_phase13_experiment_engine.py`, `test_phase14_benchmark_suite.py`, `test_phase15_capture_session_v2.py`, `test_reproducibility_audit.py`.

**Docs:** this report; `HISTORICAL_ARTIFACT_RESTORATION_20261016.md`; `POLICY_HASH_PROVENANCE.md`; `schemas/phase15-capture-session-2.schema.json`; `generated/` (ground-truth audit, reproducibility audit, synthetic benchmark — all from the commands above); additive sections in `OFFICIAL_REPLAY_PRODUCER.md`, `PHASE11_ENGINEERING_STATUS.md`, `PHASE12_EVALUATION_REPORT.md`, `PHASE13_…`, `PHASE14_PROFILING_INFRASTRUCTURE.md`, `PHASE15_VALIDATION_PROTOCOL.md`, `PHASE16_MANUSCRIPT_DRAFT.md`.

**Data/artifact additions (restoration only):** two JSON reports and four symlinks (§6).

Caution: I ran `ruff --fix` on a few pre-existing untracked files (e.g. `annotation/promotion_gate.py`, `experiments/runner.py`). It applies only mechanical fixes (import order and similar), the suite is green, but those directories have no Git baseline to diff against.

## 3. Phase work completed

**Phase 11.** Blocker diagnostics; cohort-qualified identity fix; receipt v2 with stale/forged-receipt refusal; manifest identity cross-checks; read-only audit tool; LEG-EXEC preflight (pinned hash `41cbbba3…` verified, 27 sources, 28 outputs all `WOULD_WRITE`, zero writes, `execution_authorized: false`); adversarial tests (stale receipts, altered inputs, duplicate ids, unlisted/blocklisted reviewers, forged manifest approvals, relabelled legacy schema strings). The 27 legacy records are byte-identical.

**Phase 12.** Verified (by test) that train/validation payloads are never parsed, payload bytes are hashed and parsed from one read, config/checkpoints/thresholds/provenance are bound, replays receive no labels, and failures leave no partial result. Added the fake-backend scenarios the brief lists (single-event and multi-event cohorts, missing/corrupted/mis-hashed payloads, unsupported camera modes, wrong config/checkpoint, invalid alignment, replay exception, write failure, staging cleanup, failure-report integrity, determinism), hand-calculated metric tests, the undecided-window rule, run-manifest contract versions, and a race table (`OFFICIAL_REPLAY_PRODUCER.md` §7). The CLI exit codes (3 blocked, 5 failed, 0 success, 2 usage) are tested.

**Phase 13.** Strict single-variable treatments, immutable per-call inputs, full-grid and identical-metric-set comparison gating, deterministic run ids, durable failure manifests, no writes into official trees; official execution remains blocked.

**Phase 14.** `benchmark run` command and report schema v2 (§ in `PHASE14_PROFILING_INFRASTRUCTURE.md`); claim discipline; equivalence checker. The frozen vision model could not be timed: the virtualenv's `ultralytics` directory has no `__init__.py`, so the report records `status: unavailable` instead of numbers. Measured (synthetic replay, development host Apple M1, not a claim): see `docs/generated/PHASE14_SYNTHETIC_BENCHMARK_20261016.json`.

**Phase 15.** Capture-session v2, JSON Schema, software-provenance capture, disk re-verification of hashes; fails closed when safety-case limits are absent; never marks authorization verified.

**Phase 16.** Reproducibility audit command (JSON + Markdown) and tests proving it flags unsupported numbers, overclaim language, count mismatches and broken evidence tags; evidence-class ledger in the manuscript draft (audit-clean).

## 4. Tests executed

| Run | Result | Time |
|---|---|---|
| Baseline, start of session | 931 passed, 3 failed | 19.8 s |
| After restoring historical artifacts (same code) | 934 passed, 0 failed | 19.7 s |
| **Final full suite** | **1151 passed, 0 failed, 1 warning** (`cgi` deprecation in the demo server) | **23.5 s** |

Focused files (final): cohort identity 6 (0.03 s); readiness audit 18 (1.3 s); governance 77 (0.8 s); official replay 88 (6.2 s); metric arithmetic 16; documented metrics 6; phase 13 engine 29; benchmark 18 + suite 35 (1.4 s); capture session 31 + v2 65; reproducibility audit 22 (1.7 s); event metrics 8; legacy reconciliation 5.

Targeted Ruff and `compileall` over all 36 Python files touched: compile OK; Ruff reports 43 findings, all `E501` on pre-existing long lines in `experiments/runner.py` and `annotation/promotion_gate.py`. Repository-wide Ruff (≈776) was not touched.

CLI smoke tests run against the real repository: `evaluation status` (exit 3, 36 blockers), `evaluation run --output-dir …` (blocked, nothing created), `annotation.readiness_cli` (exit 2, 30 blockers = 27 legacy + 3 cohorts), `audit reproducibility`, ground-truth audit script, `benchmark run`.

## 5. New tests and the defects they catch

- **Cohort-qualified identity** — same `event_id` in three cohorts must be ready; a true in-cohort duplicate is still refused; stale proposal in one cohort doesn't affect others; loaders keep cohorts apart. *Catches the corpus-refusal defect.*
- **Receipt lifecycle** — inventory/proposal/allowlist change, a new proposal version, edited fields, recomputed self-hash, future/garbage timestamps, old schema. *Catches silent reuse of a receipt after inputs change.*
- **Manifest identity** — relabelled cohort, unqualified ids, missing inventory, test event without an approved record, media hashes not the reviewed media. *Catches self-declared "real".*
- **Undecided window** — premature opening not computed without a window; unimplemented windows refused; mixed windows in a cohort refused.
- **Metric arithmetic** — Wilson intervals (0/1, 0/3, 3/3, 2/4), nearest-step missed-train matching, excess closure, clearance latency, cohort means/denominators/nuisance totals, no hourly rate.
- **Producer scenarios** (§3) — each failure code, no partial output, report integrity, determinism, race on review records.
- **Phase 13** — hidden config keys, non-finite/non-plain parameters, input mutation, input leakage between conditions, differing metric sets, single-cell failure, run-id sensitivity, no official-tree writes.
- **Phase 14** — exact stage/throughput arithmetic with a stepped clock, deterministic reports, nondeterministic workload abort, non-finite/decreasing clock, claim matrix (real inputs × target × criterion × samples × fingerprints), stale/altered checkpoints, byte-different outputs, property violations, self-comparison.
- **Phase 15** — 55 parametrized defects (missing metadata, corrupted/mismatched hashes, clock drift, recording gaps, invalid durations, unsupported camera configurations, absent safety-case limits), disk-hash verification, schema/validator agreement.
- **Reproducibility audit** — scanner categories, evidence tags, real-repository expectations, result-provenance mutations, CLI write refusal.
- Mutation checks: ten deliberate breakages of the new guards (receipt binding, manifest identity cross-check, qualified lookups, record-hash race check, undecided-window rule, capture-session custody/accounting, Phase 13 mutation and metric-set guards) were applied during the session; all were caught.

## 6. Full-suite failures and evidence

None remain. The three earlier failures were missing artifacts, not code defects:

1. `RUN_20261008_AUDIO_V2/metrics/v1_vs_v2_comparison.json` and 2. `RUN_20261008_AUDIO_V3_ESC50/reports/forensic_analysis.json` — never committed; present only in `~/Library/Mobile Documents/com~apple~CloudDocs/Desktop/Train_automation/`. Their figures equal the working tree's own `metrics.json` files and the archived audio reports.
3. `data/raw/audio/train_horn/positive/{43..46}.mp3` — symlinks to the misnamed `.pdf` files, present in the same shadow copy.

They were restored with `cp -pn` / `ln -s` (additive, nothing overwritten; hashes recorded). The prohibited Audio V2 checkpoint was not touched. If you prefer the strict tests to stay red until you regenerate these yourself, run the undo commands in the restoration document.

## 7. Policy-hash investigation

Resolved — see `docs/POLICY_HASH_PROVENANCE.md`. Raw `c87c1432…` vs canonical `051c908d…` for `decision_policy_v1.yaml`; same pattern for the frozen config (`b8ef5da0…` / `999a7970…`) and the v2 candidate (`d90828b2…` / `143782d1…`). The file's mtime (2026-10-13T17:18:26Z) precedes the Phase 5 run; the policy file was not changed and a regression test pins both conventions. (Note: the brief's v2-candidate raw hash is missing one character; the file hashes to `d90828b2ec37169d663c72ab7de7d86600728c0db170ebef3934b9565abaf07f`.)

## 8. Official readiness and remaining blockers (36)

27 × `LEGACY_OR_UNKNOWN_GROUND_TRUTH_SCHEMA` (invalid evidence), 3 × `COHORT_APPROVAL_MISSING` (derived), `STAGE21_RECORDS_MISSING`, `MANIFEST_MISSING` (missing human evidence), `EVENT_SPLIT_DECISION_MISSING`, `R04_SCOPE_DECISION_MISSING`, `PREMATURE_OPENING_DEFINITION_UNDECIDED` (research decisions), `EVAL_AUTH_NOT_GRANTED` (authorization). Also surfaced by the reproducibility audit (not gate blockers): dependency-lock drift (15 locked packages differ from installed) and the unusable `ultralytics` install.

## 9. Blocked by missing decisions or authorization

Premature-opening window; event-level split; R04 scope record; valid Stage-2.1 records and the promotion receipt; the input manifest (derivable once the split exists); EVAL-AUTH recording (transcribable from your earlier statement once the above exist); LEG-EXEC (inputs verified, operation-specific authorization absent); D1 numeric thresholds and D3(c) audit; target platform and acceptance criterion for any performance claim; site authorization and safety case for any field session. Nothing was chosen to reduce blocker counts.

## 10. Hashes before / after

| Item | Before | After |
|---|---|---|
| 166 files under `data/ground_truth`, `configs`, `data/splits`, `data/manifests`, `models`, plus `yolov8n.pt` and the registry | baseline | **all identical** |
| 27 legacy review records (combined digest) | `851d2b6d…` | `851d2b6d…` |
| 13 checkpoints (`*.pt` etc.) | baseline | **all identical** |
| `results/experiment_registry.jsonl` | `ea4d7dfbb5842604fa468a1d93a3de885e4a52329a2d0b47b9553645332173ef` | same |
| `configs/frozen_experiment_v1.yaml` (raw) | `b8ef5da052f002e75a2da0985add02a72d0d5684936263c14257aa12b0c9ac9a` | same |
| `configs/decision_policy_v1.yaml` (raw) | `c87c1432f473f84def46d343429c21bcd5329adcbce6cfdf7933de446a0c8575` | same |
| `configs/decision_policy_v2_candidate.yaml` (raw) | `d90828b2ec37169d663c72ab7de7d86600728c0db170ebef3934b9565abaf07f` | same |
| Vision checkpoint | `3f5bb5b23f82f5d963d23dc8f3f1896a83532424d8e4ef70a406b6abfba18ebd` | same |
| Audio V3 checkpoint | `ea1bb81d74230af71ba22b6d534a2ac550bca05833d1532e223376926c512782` | same |
| Audio V2 (prohibited, never used) | `59b0785f73b201dfd2fb335b98f6ddb764c8544d1ca5fc9e8aa326d74ffcf7d5` | same |

## 11. Git state

HEAD `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`; 0 staged. The 16 tracked-modified files are the same 16 as at session start (only `cli/main.py` changed further). New untracked artifacts are listed in §2. One incident: while developing a CLI test I briefly wrote `docs/audit_should_not_exist.json` (the CLI guard then omitted `docs/`); it was deleted at once and `docs/` was added to the guard. The restored audio files and four symlinks are untracked additions.

## 12. Next actions for the researcher

1. **Decide the premature-opening window** (`docs/PREMATURE_OPENING_DECISION_EVIDENCE.md`) — one line in `data/manifests/phase12_protocol_decision.json`.
2. **Provide or point to the Stage-2.1 records** you consider approved (`data/ground_truth/reviews/<cohort>/…`); otherwise run the review tooling. Then run the readiness CLI with `--receipt-path`.
3. **Record the event-level split** and the **R04 scope** (`docs/generated/GROUND_TRUTH_READINESS_AUDIT_20261016.md` and `governance.documented_r04_candidates` list the 11 calibration-supported events as evidence, not a decision).
4. Then the input manifest can be derived and EVAL-AUTH transcribed from your standing statement; no new approval is needed for that.
5. Review the restoration of the three historical artifacts (keep, or undo).
6. Repair the virtualenv (`ultralytics`) and reconcile `requirements.lock` before any model-latency work; declare a target platform and a documented acceptance criterion if a performance claim is ever to be made.
7. Rewrite or tag the overreaching sentences in `Railway_Crossing_Automation_Research_Report.docx` before reuse (list in `docs/generated/REPRODUCIBILITY_AUDIT_20261016.md`).
8. Optional: LEG-EXEC (separate, operation-specific authorization naming hash `41cbbba3…`, 27 sources, 28 outputs, and the write).
