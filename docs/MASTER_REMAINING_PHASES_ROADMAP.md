# Master Remaining Phases Roadmap — Phases 11.8 through 16

**Document status:** PLANNING ARTIFACT. This roadmap authorizes nothing. Every phase described here requires separate researcher authorization before execution. No phase described here has been implemented, and no claim in this document has been validated by running tests.

**Prepared:** 2026-10-15, by repository inspection (not from memory of prior reports).
**Repository:** `/Users/sayemuddin/Desktop/Train_automation` (branch `main`, HEAD `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`, tracking `origin/main`).

---

## 0. Inspection record — what was verified, what was not

### 0.1 Verified by direct inspection (this planning session)

| Finding | Evidence |
|---|---|
| HEAD is `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b` on `main`, 2026-10-12 | `git log -1` |
| Working tree: 13 tracked files modified-unstaged, 0 staged, ~207 untracked paths | `git status --short --branch` |
| Phase 11.7 governance controls exist in code: `load_authorized_reviewers()`, `compute_media_sha256_pair()`, required `authorized_reviewers` and `media_file_paths` parameters on `validate_for_promotion`, `REVIEWER_NOT_AUTHORIZED` check, live re-hash at promotion | `src/railway_detection/annotation/promotion_gate.py` lines 41–150 |
| Schema version is `8.1.0-stage2.1`; `reviewer_observed_media_hashes` is a **required** field of `Stage21ReviewRecord`; `build_stage2_1_record_from_dict` lists it among required top-level keys | `src/railway_detection/annotation/stage2_1_schema.py` lines 33–40, 281, 363–377 |
| `data/ground_truth/authorized_reviewers.json` exists, contains exactly one reviewer (`raihankabirrahu@gmail.com`) | file read |
| D1 (duration thresholds) and D3 (second-review triggers, 3(c) audit frequency) remain `PENDING` / `PENDING_RESEARCHER_DECISION` — no threshold or mechanism invented | `docs/PHASE11_3_RESEARCHER_DECISIONS.md` v1.2.0; Phase 11.7 report Tasks 1/4 |
| **Phase 11.8 does not exist.** No source, test, script, or doc matches `phase.?11\.8`/`PHASE11_8` in `src/`, `tests/`, `scripts/` (only plot coordinates in `generate_report_figures.py`) | regex search over 924 files |
| The operational review workflow is documentation-only (`docs/PHASE11_3_ANNOTATION_REVIEW_WORKFLOW.md`); no review-session tool calls `compute_media_sha256_pair()` | annotation module file listing; workflow doc |
| 27 legacy review records exist on disk (23 train + 3 no-train + 1 engine) with `reviewer_id: human_researcher_lead`, `adjudication_status: APPROVED` | `data/ground_truth/reviews/.../event_001_review.json` |
| Frozen config intact as documented: audio_v2 prohibited block, `allow_unverified_zero_offset: false`, R04 status `R04_UNRESOLVED_REQUIRES_EMPIRICAL_OFFSETS`, `cross_camera_sync.mode: independent_or_unverified` | `configs/frozen_experiment_v1.yaml` read |
| No Stage-2.1 record exists for any real event; no `docs/implementation_plans/` existed before this roadmap | directory listing |

### 0.2 Discrepancies found between reports and the repository

| # | Discrepancy | Detail | Impact |
|---|---|---|---|
| **DISC-1** | **Legacy record schema version.** Multiple reports (Phase 11.1 audit, Phase 11.6G §1, and the planning brief) state the 27 legacy records carry `schema_version: "7.0.0"`. The actual file (`event_001_review.json`, spot-checked) carries `"schema_version": "6.0.0"`. | Either the reports misstated the legacy version, or "7.0.0" refers to the protocol document version rather than the record field. Behavior is unaffected: `promotion_gate.py` rejects any version other than `8.1.0-stage2.1` via `LEGACY_OR_UNKNOWN_SCHEMA`. But every document that pins "7.0.0" as the legacy record version is inaccurate and must be corrected or annotated before any legacy disposition execution. | Low for logic; **must be reconciled before Phase 11.10/legacy-disposition authorization** so hash-pinned proposals cite the correct field value. |
| **DISC-2** | `docs/PHASE11_3_ANNOTATION_REVIEW_WORKFLOW.md` §6 still says the gate requires `schema_version` exactly `"8.0.0-stage2.1"`. Phase 11.7 bumped it to `8.1.0-stage2.1`. | Stale documentation, exactly the "workflow not connected to the new schema" blocker Phase 11.7 reported. | Confirms Phase 11.8 scope. |
| **DISC-3** | Reported test result "475 passed, 3 pre-existing failures" could **not** be re-verified: `.venv` (Python 3.11) has a broken pytest install (`ImportError: cannot import name '__version__' from '_pytest'`), and system `python3` (3.14) has no pytest. | The test-suite status is **reported-but-unverified**. Environment repair is a prerequisite for every implementation unit. | Blocks all test-gated acceptance criteria until fixed. |
| **DISC-4** | `python` is not on PATH (only `python3`); `.venv/bin/pip` is missing. | Environment fragility. | Implementation plans must pin an explicit interpreter/venv repair step before running tests. |

### 0.3 Reported-but-unverified items (accepted as context, not as evidence)

- The 27 legacy records being byte-identical to the Phase 11.1 baseline (reported hash-re-verified in Phase 11.7, not re-checked this session).
- The legacy proposal's pinned raw-byte SHA-256 `41cbbba3e9d587b9972c3baca1b39f09d478d408d9c60fd538c249c4600113d4` (stated in the brief; the execution manifest pins per-file hashes such as `3493e125…` — the two are different artifacts and both must be re-verified at execution time, not trusted now).
- The "475 passed / 3 pre-existing failures" suite result (DISC-3).
- Frozen-config and checkpoint hash equality (content read only; hashes not recomputed this session).

### 0.4 Explicitly unresolved research issues (carried forward)

- R04 cross-camera synchronization: unresolved for 16/27 events; restrictions active in frozen config.
- Site-survey-blocked boundaries (14 rows), `event_006` locomotive identity, `event_021` timing discrepancy, `event_011` long static span.
- Legacy disposition execution: prepared, hash-pinned, **not authorized**.
- Stage 3 / Phase 12: not authorized, not begun.

---

## 1. Remaining-phase dependency graph (recommended order)

```
[ENV-REPAIR] ──> 11.8 (workflow↔schema integration)
                     │
                     ▼
                 11.9 (synthetic pilot & workflow audit) ──provides──> D1 duration evidence (partial)
                     │
                     ▼
                 11.10 (researcher decisions & protocol closure)
                     │  (D1, D3(a), D3(c), legacy-disposition execution authorization)
                     ▼
                 11.11 (formal Stage 2.1 adjudication, researcher-led)
                     │
                     ▼
                 11.12 (adjudication closure & evaluation-readiness gate)
                     │  gate: approved ground truth + executed/declined legacy disposition
                     ▼
                 12 (evaluation & benchmarking)
                     │
          ┌──────────┼──────────┐
          ▼          ▼          ▼
        13 (robustness/ablation) 14 (real-time optimization)
                     │
                     ▼
                 15 (controlled validation & hardware, authorization-gated)
                     │
                     ▼
                 16 (publication & release)
```

**Ordering rationale / deviations from the proposed numbering:**

1. **Keep 11.8 → 11.9 → 11.10 → 11.11 → 11.12 as the governance spine; do not merge.** Each closes a distinct failure mode (missing tooling → untested tooling → open policy → unexecuted review → unverified closure). Merging them would let a workflow defect contaminate real adjudication records.
2. **Insert an ENV-REPAIR unit (Unit 0) into Phase 11.8** rather than making it a standalone phase: it is small, mechanical, and everything else depends on a runnable test suite (DISC-3/DISC-4).
3. **Phase 11.10 partially overlaps 11.9** by design: the synthetic pilot produces the usability and timing observations the researcher needs to close D1 and D3(c). Sequence them 11.9 first, then 11.10, but they share evidence.
4. **Legacy disposition execution authorization is attached to 11.10** (not 11.11), because new Stage-2.1 records must not be positioned as replacing legacy ones while the legacy disposition is still "prepared, not executed."
5. **Phases 13 and 14 may run in parallel after Phase 12** (different artifacts, no shared mutable state) — but both must preserve the frozen baseline for comparability. Phase 13 does not strictly require Phase 12's numbers, but its experiment design is far better informed by them.
6. **Phase 15 and 16 are authorization/safety-case gated** and largely planning + external dependencies; they are sequenced last and are not expected to be coding-heavy.

---

## 2. Phase summary table

| Phase | Objective | Hard prerequisites | Recommended model | Risk |
|---|---|---|---|---|
| 11.8 | Wire the review workflow to schema `8.1.0-stage2.1`: capture reviewer-observed media hashes, session validation, reviewer authorization, promotion-failure testing | ENV-REPAIR; Phase 11.7 code intact | **Qwen 3.8 Max** | High (touches governance-critical schema boundary) |
| 11.9 | Synthetic pilot: exercise the full workflow with synthetic records/media; audit usability, validation, append-only history, recovery | 11.8 complete & tested | **Gemini 3.8 Flash** (Opus review) | Medium |
| 11.10 | Inventory and prepare closure of pending researcher decisions; no invented values | 11.9 evidence | **Claude Opus 4.8** (decision support; researcher decides) | Low (documentation) but blocks adjudication |
| 11.11 | Formal Stage 2.1 adjudication of the 27-event inventory, researcher-led | 11.10 decisions recorded; workflow tested; researcher authorization | Opus protocol + Gemini tooling; **researcher executes** | High (creates ground truth) |
| 11.12 | Adjudication closure + evaluation-readiness gate | 11.11 complete | **Qwen 3.8 Max** | High (gate logic must fail closed) |
| 12 | Evaluation & benchmarking against approved ground truth only | 11.12 gate passed + separate authorization | **Qwen 3.8 Max** | High (leakage risk) |
| 13 | Robustness & ablation studies | 12 baselines | Gemini Flash (bounded) / Qwen (failure injection) | Medium |
| 14 | Real-time optimization, preserving frozen-baseline comparability | 12 baselines | **Qwen 3.8 Max** | Medium-high |
| 15 | Controlled validation & hardware integration (authorization-gated) | 14; external authorization & safety case | Opus planning; no live railway control | High (safety claims) |
| 16 | Publication & research release | 12–15 evidence | Gemini Flash + Opus review | Medium (overclaim risk) |

---

## 3. Cross-phase scientific and safety invariants (binding on every plan)

1. No evaluation metrics against unapproved ground truth.
2. No model-generated labels presented as researcher-approved labels.
3. No retroactive ground-truth changes driven by model performance.
4. No cross-camera temporal merging on an unverified zero offset; no bypass of the R04 restriction.
5. No silent changes to frozen experiment configurations or thresholds (hash-guarded).
6. No use of the prohibited Audio V2 checkpoint.
7. No unsupported real-world safety claims; simulated gate behavior is not railway safety evidence.
8. No overwrite/delete of the original 27 legacy review records.
9. No legacy invalidation execution without separate explicit researcher authorization covering the pinned proposal, source records, and outputs.
10. No real Stage-2.1 record creation/promotion before workflow + governance prerequisites are satisfied.
11. No Stage 3 / Phase 12 execution without separate authorization and readiness evidence.
12. No staging/committing unless explicitly authorized; inspect the worktree before and after each phase.

---

## 4. Decision register (concise)

### 4.1 Decisions only the researcher can make

| ID | Decision | Evidence needed | Blocks | Deferrable? |
|---|---|---|---|---|
| **D1** | Exact pilot-derived review-duration floor/upper thresholds (option D selected, values unset) | Timed genuine review sessions (from 11.9 pilot tooling + first 11.11 sessions): per-event durations, event complexity, interruptions | Formal 11.11 promotion reliance; not starting review | Yes — flat 30.0s floor suffices to begin |
| **D3(a)** | Second-review trigger rule (options B+C selected conceptually; no concrete rule exists) | Definition of which boundary/event classes require mandatory second review | 11.11 disagreement workflow | Partially — review can start for non-trigger boundaries |
| **D3(c)** | Clear-case audit mechanism & frequency | Researcher's acceptable audit burden; sample of clear-marked boundaries | Full protocol closure (11.10) | Yes, before first promotion |
| **LEG-EXEC** | Authorize (or explicitly decline) legacy 27-record disposition execution | Review of `docs/PHASE11_6D…` package, the pinned proposal hash, and DISC-1 reconciliation | Positioning new records as superseding legacy ones | Yes, but before mid-11.11 |
| **ADJ-AUTH** | Authorize start of formal Stage 2.1 adjudication | 11.9 pilot sign-off; 11.10 decision record | 11.11 | No |
| **EVAL-AUTH** | Authorize Phase 12 evaluation + name the evaluation stage | 11.12 readiness gate evidence | 12 | No |
| **SITE-SURVEY** | Whether/when a physical site survey happens (14 blocked boundary rows) | Logistics | Resolution of 14 UNCERTAIN rows | Yes (they remain UNCERTAIN/CENSORED meanwhile) |
| **DISC-1 reconciliation** | Confirm the true legacy schema version statement (6.0.0 vs 7.0.0) before any disposition execution | Re-read of records vs audit docs | LEG-EXEC | No (must precede LEG-EXEC) |

### 4.2 Decisions that can be deferred

- D1 numeric thresholds (flat floor is a safe interim).
- D3(c) audit frequency (before first promotion, not before first review).
- Publication venue/format choices (Phase 16).
- Hardware vendor selection (Phase 15).

### 4.3 Actions explicitly NOT authorized by this roadmap

- Executing legacy invalidation.
- Creating/promoting any real Stage-2.1 record.
- Starting Stage 3 or Phase 12.
- Any git staging/committing/pushing.
- Any modification to checkpoints, frozen configs, Phase 8 outputs, or `data/ground_truth/reviews/`.
- Any live railway deployment or unsupervised field testing.

---

## 5. Highest-risk blockers

1. **Broken test environment (DISC-3/DISC-4).** Nothing can be acceptance-tested until `.venv` pytest works. Cheapest verification: rebuild/repair the venv and re-run the Phase 11.7 suites to confirm the reported 475/3 baseline.
2. **D1/D3 unresolved.** Formal adjudication can start on the flat floor, but promotion-time reliance and second-review mechanics stay incomplete until the researcher decides.
3. **DISC-1 (legacy schema version misstatement).** Must be reconciled before any legacy disposition execution authorization, because the disposition package cites record attributes.
4. **Ground truth does not exist yet.** Every downstream phase (12–16) is blocked on 11.11/11.12 success; there is no shortcut.
5. **R04 unresolved (16/27 events).** Caps any dual-camera evaluation claim; Phase 12 must be designed around it, not despite it.

---

## 6. Model-efficiency notes

- Implementation calls receive **only the exact files listed in each plan's §5**, not the whole repository or all reports.
- Where Gemini Flash and Qwen Max could both do a task (e.g., 11.9 test expansion), run a small pilot unit on each and compare: (a) test pass rate, (b) diff scope discipline, (c) negative-test quality. Record the outcome; do not assert a ranking without it.
- Opus is reserved for: this roadmap, 11.10 decision framing, 11.11 protocol, 11.12 gate design review, 12 leakage-control design, 15 safety-case structure, 16 claims review.

## 7. First bounded implementation task (recommended start point)

**Phase 11.8, Unit 0+1** (after researcher review of this roadmap): repair the test environment, re-verify the Phase 11.7 test baseline, then build the minimal review-session helper that calls `compute_media_sha256_pair()` and constructs a schema-`8.1.0-stage2.1`-valid synthetic record — with no writes to `data/ground_truth/reviews/`. See `docs/implementation_plans/PHASE11_8_IMPLEMENTATION_PLAN.md`.

---

## 8. Plan index

- `docs/implementation_plans/PHASE11_8_IMPLEMENTATION_PLAN.md`
- `docs/implementation_plans/PHASE11_9_IMPLEMENTATION_PLAN.md`
- `docs/implementation_plans/PHASE11_10_IMPLEMENTATION_PLAN.md`
- `docs/implementation_plans/PHASE11_11_IMPLEMENTATION_PLAN.md`
- `docs/implementation_plans/PHASE11_12_IMPLEMENTATION_PLAN.md`
- `docs/implementation_plans/PHASE12_IMPLEMENTATION_PLAN.md`
- `docs/implementation_plans/PHASE13_IMPLEMENTATION_PLAN.md`
- `docs/implementation_plans/PHASE14_IMPLEMENTATION_PLAN.md`
- `docs/implementation_plans/PHASE15_IMPLEMENTATION_PLAN.md`
- `docs/implementation_plans/PHASE16_IMPLEMENTATION_PLAN.md`
