# Researcher Decision Register — Remaining Phases (11.8–16)

**Status:** DECISION REGISTER ONLY. Prepared 2026-10-15 from direct repository inspection alongside `docs/MASTER_REMAINING_PHASES_ROADMAP.md`. Nothing below has been decided by any model; every `PENDING_RESEARCHER_DECISION` item requires the researcher's own choice. No threshold, trigger rule, frequency, or policy value is proposed as a default anywhere in this document.

This register deliberately separates the two kinds of remaining work:
- **TECHNICAL** — implementable by an agent once authorized; no researcher judgment required.
- **RESEARCHER-ONLY** — a genuine policy/scientific choice that no agent may make, even provisionally.

---

## 1. RESEARCHER-ONLY decisions (cannot be implemented, defaulted, or proxied)

| ID | Decision | Current state (verified) | Evidence that will exist when it is time to decide | What blocks until decided | Earliest safe moment |
|---|---|---|---|---|---|
| **R-D1** | Exact pilot-derived review-duration floor and upper threshold (Decision 1, option D selected, values unset) | `MIN_PLAUSIBLE_REVIEW_DURATION_S = 30.0` flat floor only; absence test passes | Phase 11.9 pilot timing observations + first genuine 11.11 session durations | Promotion-time reliance on final D1 mechanism (NOT the start of review) | After 11.9 pilot; before first 11.11 promotion |
| **R-D3a** | Concrete second-review trigger rule (Decision 3 part a: options B+C selected conceptually; no rule exists) | No trigger logic anywhere; absence test passes | 11.10 candidate boundary/event-class enumeration | 11.11 disagreement/second-review workflow for triggered events | Before 11.11 reviews trigger-class boundaries |
| **R-D3c** | Clear-case audit mechanism and frequency (Decision 3c) | `PENDING_RESEARCHER_DECISION`; no mechanism built | 11.10 read-only query spec enumerating clear-marked boundaries available to sample | Full protocol closure; promotion of records whose boundaries are all "clear" | Before first promotion, not before first review |
| **R-LEG** | Execute or explicitly decline the prepared 27-record legacy disposition | Prepared, hash-pinned, dry-run-reviewed; execution `NOT_AUTHORIZED` | `docs/PHASE11_6_LEGACY_INVALIDATION_DRY_RUN_PLAN.md`, execution manifest; **plus R-DISC1 reconciliation first** | Positioning new Stage-2.1 records as superseding specific legacy records | Phase 11.10, before mid-11.11 |
| **R-DISC1** | Reconcile the legacy-record schema-version misstatement: reports say `"7.0.0"`, actual files on disk say `"6.0.0"` (verified this session) | Unreconciled; affects every hash-pinned disposition citation | 11.10 Unit 3 read-only audit memo | R-LEG execution authorization (citations must be accurate) | Phase 11.10 |
| **R-ADJ** | Authorize formal Stage 2.1 adjudication (scope: which events, which boundaries, in what order) | Not authorized; zero Stage-2.1 records exist | 11.9 pilot sign-off + 11.10 decision record | Phase 11.11 entirely | After 11.10 |
| **R-SPLIT** | Event-level train/validation/test split for evaluation | Not decided | Phase 12 plan (event-level, never frame-level) | Phase 12 execution | With R-EVAL |
| **R-R04SCOPE** | Which events' dual-camera claims are evaluation-in-scope given R04 (11 supported vs 16 unresolved) | R04 unresolved for 16/27; frozen config `allow_unverified_zero_offset: false` | Phases 6–10.1 evidence already recorded | Phase 12 dual-camera metric scope | With R-EVAL |
| **R-EVAL** | Authorize Phase 12 and name the specific evaluation stage | Not authorized; gate not built | 11.12 readiness gate evidence | Phase 12 entirely | After 11.12 |
| **R-SITE** | Whether/when a physical site survey occurs (14 boundary rows blocked on it) | Logistics only | None producible by an agent | Resolution of those 14 rows (they remain UNCERTAIN/CENSORED meanwhile — a valid scientific state) | Any time; deferrable indefinitely |
| **R-PUB** | Publication venue, co-authorship, and public data-release scope | Not decided | Phase 16 release plan options | Phase 16 release | Phase 16 |

---

## 2. TECHNICAL tasks (agent-implementable once the phase is authorized)

| Phase | Task | Requires which researcher decision(s) first |
|---|---|---|
| 11.8 Unit 0 | Repair `.venv` pytest (broken `_pytest.__version__` import; system python3 has no pytest) and re-verify the reported 475-pass / 3-known-failure baseline | None (but phase authorization required) |
| 11.8 Units 1–4 | Review-session helper calling `compute_media_sha256_pair()`; authorization binding; dry-run promotion; workflow-doc sync to `8.1.0-stage2.1` | Phase 11.8 authorization |
| 11.9 | Synthetic pilot end-to-end; duration observations for R-D1; defect register | 11.8 complete |
| 11.10 | Decision inventory, evidence assembly, R-DISC1 memo, closure package (documentation only; nothing filled in) | 11.9 complete |
| 11.11 tooling | Session runner, four-state enforcement, disagreement workflow per R-D3a | R-ADJ (+ R-D3a for the disagreement path) |
| 11.12 | Reconciliation, unresolved-boundary register, fail-closed readiness gate | R-LEG resolved (for `supersedes` records); R-D3c for clear-boundary promotion |
| 12 | Approved-records-only loader; pre-registered censoring-aware metrics; leakage controls | R-EVAL, R-SPLIT, R-R04SCOPE |
| 13 | Ablation matrix + perturbation suite against approved ground truth | Phase 12 complete + scope authorization |
| 14 | Latency profiling + behavioral-equivalence optimizations | Phase 12 complete + authorization |
| 15 | Validation protocol, safety-case draft, hardware requirements (planning only; no field deployment) | External site authorization + researcher go/no-go |
| 16 | Manuscript, evidence audit, reproducibility statement, release plan | R-PUB |

---

## 3. Standing prohibitions (reaffirmed; unchanged by any phase plan)

1. No evaluation against unapproved ground truth; no model output ever presented as an approved label.
2. No Audio V2 checkpoint use (prohibited block in `configs/frozen_experiment_v1.yaml`).
3. No cross-camera merging on an unverified zero offset; the R04 restriction (`allow_unverified_zero_offset: false`) stands.
4. No frozen-config or threshold modification.
5. No legacy-record overwrite/delete; no invalidation execution without R-LEG.
6. No real Stage-2.1 record before 11.8–11.10 prerequisites; no Stage 3 / Phase 12 before R-EVAL.
7. No git staging/committing/pushing without explicit authorization.
8. No real-world safety claims from simulated gate behavior.

---

## 4. Recommended decision sequence for the researcher

1. Review `docs/MASTER_REMAINING_PHASES_ROADMAP.md` and the ten phase plans in `docs/implementation_plans/`; authorize Phase 11.8.
2. After 11.9: review pilot timing evidence → decide R-D1 values (or defer, with the 30.0s interim floor documented as the operative rule).
3. In 11.10: decide R-DISC1 first, then R-LEG; specify the R-D3a rule and the R-D3c mechanism/frequency.
4. Issue R-ADJ with scope; conduct 11.11 reviews personally using the audited workflow.
5. After 11.12 gate evidence: issue R-EVAL together with R-SPLIT and R-R04SCOPE.
6. Phases 13–16: authorize incrementally as evidence accumulates; R-PUB last.

---

## 5. Verification snapshot taken when this register was written (2026-10-15)

| Artifact | SHA-256 (recomputed fresh this session) |
|---|---|
| `data/ground_truth/reviews/train_events/event_001_review.json` | `a0edd4a670e1706391309392661559e93a310d5c9f39d17cf094173cfb5e1cc6` |
| `data/ground_truth/reviews/no_train_events/event_001_review.json` | `7387acbf17e6ca2eda6b814e3d9f30683aecffe863b14637cc4ff4bf51015243` |
| `data/ground_truth/reviews/engine_events/event_001_review.json` | `3493e125e86c7642d47dca13ddfe3a91fad926b6e6d0fd9e9662968d1bca3edd` |
| `configs/frozen_experiment_v1.yaml` | `b8ef5da052f002e75a2da0985add02a72d0d5684936263c14257aa12b0c9ac9a` |

Git state when written: HEAD `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`, 13 pre-existing modified-unstaged tracked files, **0 staged**. This session created only new, untracked planning documents (`docs/MASTER_REMAINING_PHASES_ROADMAP.md`, `docs/RESEARCHER_DECISION_REGISTER_REMAINING_PHASES.md`, `docs/implementation_plans/*.md`) and the now-empty `docs/implementation_plans/` directory; no tracked file was modified and nothing was staged or committed.
