# Full Research Execution Plan — Train Gate Automation

**Date:** 2026-10-29 UTC
**Repository:** `/Users/sayemuddin/Desktop/Train_automation`
**HEAD:** `d4db94d` / `main`
**Status:** EXECUTION PLAN — Active workstreams identified

## Executive Summary

The project has substantial completed engineering and diagnostic experimentation. The path to
research completion requires resolving 4 researcher decisions, completing human ground-truth
adjudication, and then executing the official evaluation pipeline. This plan identifies all
work that can proceed NOW versus work gated on decisions or evidence.

---

## A. ALREADY COMPLETE (Verified)

| Item | Evidence | Status |
|---|---|---|
| Cache-only replay engine | `cache_only_engine.py`, 82 tests | `VERIFIED` |
| Phase 12 adapter (synthetic) | `cache_phase12_adapter.py`, 18 tests | `TESTED_SYNTHETICALLY` |
| Descriptive-only aggregator | `descriptive_only.py`, 18 tests | `IMPLEMENTED_SYNTHETIC_ONLY` |
| Diagnostic experiments B0–B7c | `results/experiments/`, 14 conditions × 27 events | `COMPLETE` (diagnostic) |
| Cache artifacts (108 JSONL) | `results/experiments/cache/` | `COMPLETE` (diagnostic) |
| Statistical analysis | `comprehensive_statistics.json` | `COMPLETE` (diagnostic) |
| Vision model trained | YOLOv8n, mAP50=0.782 | `COMPLETE` |
| Audio model trained | CompactTrainHornCNN, F1=0.869, AUC=0.961 | `COMPLETE` |
| R04 calibration evidence | 12 CALIBRATION_SUPPORTED events | `COMPLETE` (candidate) |
| Protocol documents | v8/v6 committed, v9/v7 worktree | `COMPLETE` (conflict unresolved) |
| Paper draft skeleton | 412 lines, 14 placeholders | `COMPLETE` (needs results) |
| Research figures | 24 figures generated | `COMPLETE` |
| Governance infrastructure | Schemas, validators, gates | `COMPLETE` |
| Synthetic test suite | 476 tests collected | `COMPLETE` |

---

## B. AGENT CAN COMPLETE AUTONOMOUSLY NOW

| Task | Deliverable | Blocked? |
|---|---|---|
| Populate paper Results section from B0–B7c data | Updated `PAPER_DRAFT` | No |
| Generate results tables (main, ablation, robustness) | Markdown/JSON tables | No |
| Complete error analysis from existing per-event data | Error taxonomy doc | No |
| Validate metric arithmetic with synthetic fixtures | Test results | No |
| Prepare reproducibility appendix | Documentation | No |
| Create experiment matrix document | This deliverable | No |
| Dataset completion plan | This deliverable | No |
| Evaluation pipeline validation | This deliverable | No |
| Decision materials for D1–D4 | Response sheet | No |
| Prepare review queue forms for Stage-2.1 | Checklist/forms | No |
| Validate all configs and schemas | Check results | No |

---

## C. RESEARCHER DECISION REQUIRED

| ID | Decision | Options | Recommendation | Blocks |
|---|---|---|---|---|
| D1 | Protocol authority | HEAD v8/v6 vs worktree v9/v7 | v9/v7 (R03 retired, operational convention) | Protocol-bound artifacts, EVAL-AUTH |
| D2 | Premature-opening profile | v9 vs M4 | M4 (fewer boundary deps, back-clock only) | Official metric computation |
| D3 | Descriptive vs official split | Preserve split / separate descriptive / amend / defer | Separate descriptive contract | Descriptive mode activation |
| D4 | R04 camera scope | Per-event modes + accepted-sync set | 12 CALIBRATION_SUPPORTED as dual; rest single/independent | Input manifest, official replay |

---

## D. EVIDENCE OR AUTHORIZATION REQUIRED

| Item | Missing | Who | Can agent prepare? |
|---|---|---|---|
| Stage-2.1 human reviews (27 events) | Genuine frame-by-frame adjudication | Researcher (human) | Yes: forms, queues, validation tools |
| Promotion receipt | Valid reviews + media hash verification | Researcher + authorized workflow | Yes: readiness CLI exists |
| Event-split decision | Researcher-authored partition or descriptive mode | Researcher | Yes: options documented |
| R04 scope decision | Per-event mode selection | Researcher | Yes: evidence matrix prepared |
| Protocol decision | Version selection | Researcher | Yes: comparison prepared |
| Input manifest | Derived from decisions + payloads | Engineering (after decisions) | Yes: builder exists |
| EVAL-AUTH | All 7 live bindings | Researcher (after all above) | Yes: checklist prepared |
| Official evaluation | EVAL-AUTH + readiness gate pass | Researcher authorization | No: must not bypass |
| Real cache provenance | Frozen config/checkpoint binding | Engineering (after authorization) | Partially: schema defined |

---

## E. ORDERED EXECUTION SEQUENCE

### Phase 1: Immediate (no decisions needed)
1. ✅ Populate results tables from B0–B7c
2. ✅ Complete paper Results/Discussion sections
3. ✅ Generate final figures
4. ✅ Validate evaluation pipeline end-to-end with synthetic data
5. ✅ Prepare Stage-2.1 review queue
6. ✅ Prepare D1–D4 decision materials

### Phase 2: After D1+D2 decisions
7. Record protocol decision artifact
8. Bind metric profile
9. Update paper methodology section

### Phase 3: After D3+D4 decisions
10. Record split/R04 decisions
11. Build input manifest (engineering)
12. Validate cache provenance

### Phase 4: After Stage-2.1 human review
13. Validate promotion receipt
14. Verify cohort coverage
15. Final readiness check

### Phase 5: After EVAL-AUTH
16. Official evaluation execution
17. Final results and paper completion

---

## F. CRITICAL PATH

```
D1+D2 decisions → Protocol artifact → Profile binding
                                         ↓
D3+D4 decisions → Split/R04 artifacts → Input manifest
                                         ↓
Human Stage-2.1 → Promotion receipt → Cohort approval
                                         ↓
                              All 7 EVAL-AUTH bindings
                                         ↓
                              Official evaluation
```

Longest path: Human Stage-2.1 review (27 events × ~5 min each = ~2.5 hours minimum).

---

## G. WHAT IS NOT BLOCKED

The following can proceed REGARDLESS of D1–D4 decisions:
- Paper writing (Results, Discussion, Limitations, Related Work)
- Figure generation from existing B0–B7c results
- Error analysis and failure case documentation
- Reproducibility appendix
- Synthetic test maintenance
- Configuration validation
- Documentation updates
- Descriptive-only component testing

