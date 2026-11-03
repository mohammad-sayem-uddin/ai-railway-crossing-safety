# Minimum Required Decisions — Researcher Action Items

**Date:** 2026-10-29 UTC
**Status:** AWAITING RESEARCHER RESPONSE
**Total decisions required:** 4 (D1–D4)
**Total human review required:** 27 events (~2–3 hours)
**Total authorizations required:** 2 (promotion + EVAL-AUTH, sequential)

---

## DECISION FORM

### D1 — Protocol Authority

**Question:** Which protocol document set governs this study?

**Options:**
- [ ] A: HEAD set (protocol v8.0.0, GT v6.0.0, data-flow v6.0.0, ablation v6.0.0)
- [ ] B: Worktree set (protocol v9.0.0, GT v7.0.0, data-flow v7.0.0, ablation v7.0.0)
- [ ] C: Other (specify): _______________

**Recommendation:** B (worktree v9/v7). Rationale: R03 site-survey is retired as a separate
blocker (replaced by operational danger-zone convention), reducing annotation prerequisites
without changing R04 synchronization requirements. All downstream contracts reference v9
semantics in the working tree.

**Consequences of A:** R03 remains a formal prerequisite; site survey documentation required.
**Consequences of B:** R03 retired; operational convention governs; R04 unchanged.

**Researcher response:** _______________
**Rationale:** _______________
**Date:** _______________

---

### D2 — Premature-Opening Metric Profile

**Question:** Which premature-opening definition governs official evaluation?

**Options:**
- [ ] A: v9 `t1_entry_to_t4_clearance` (T1≤t<T4, needs T1+T4 on fused timeline)
- [ ] B: M4 `first_blocked_to_t4_clearance` (t_blocked<t<T4, needs T4 only)
- [ ] C: Defer (no premature-opening metric in this study)

**Recommendation:** B (M4). Rationale:
- Requires only T4 (back camera), not T1+T4 on a common timeline.
- More events potentially evaluable (doesn't need T1 observability).
- Paired with M5 `never_protected` for transparency.
- Already implemented and tested in `metrics.py:105-122`.
- Aligns with researcher's stated preference.

**Consequences of A:** Requires accepted dual-camera sync for T1+T4 comparison.
**Consequences of B:** Requires T4 evidence; events without blocked step are M5.
**Consequences of C:** Premature-opening metric excluded from official results.

**Researcher response:** _______________
**Rationale:** _______________
**Date:** _______________

---

### D3 — Analysis Framing / Event Split

**Question:** How should the 27 events be framed for evaluation?

**Options:**
- [ ] A: Preserve official split contract (provide train/val/test event partition)
- [ ] B: Authorize separate descriptive-only contract (full-cohort, no split)
- [ ] C: Amend official contract to support full-cohort mode
- [ ] D: Defer until multi-crossing data available

**Recommendation:** B (separate descriptive contract). Rationale:
- Single crossing with 2 sessions cannot support leakage-safe generalization claims.
- Full-cohort descriptive is scientifically honest for fixed-site characterization.
- Preserves official split contract unchanged for future multi-site work.
- Descriptive-only component already implemented and tested (synthetic).
- Aligns with researcher's stated preference.

**Consequences of A:** Must provide a valid 3-way partition; limits descriptive scope.
**Consequences of B:** No held-out claims; separate reporting path; no official Phase 12.
**Consequences of C:** Highest governance risk; changes official semantics.
**Consequences of D:** No evaluation until new data collected.

**Researcher response:** _______________
**Rationale:** _______________
**Date:** _______________

---

### D4 — R04 Camera Scope and Synchronization

**Question:** Which events use dual-camera (fused) mode, and which use single/independent?

**Options:**
- [ ] A: Accept all 12 CALIBRATION_SUPPORTED events as dual_camera; remaining 15 as single_camera
- [ ] B: Accept subset of 12 (specify): _______________
- [ ] C: All events single_camera (no dual-camera evaluation)
- [ ] D: All events independent_camera (separate clocks, no fusion)

**Recommendation:** A. Rationale:
- 12 events have CALIBRATION_SUPPORTED verdicts with measured offsets and uncertainties.
- Visual landmark corroboration exists for these events.
- Remaining 15 events lack sufficient calibration quality for fused replay.
- single_camera for remaining events preserves front-camera-only analysis.
- Aligns with researcher's per-event evidence-based preference.

**Accepted-sync events (if A or B selected):**
```
engine_events/event_001, train_events/event_001, train_events/event_002,
train_events/event_005, train_events/event_006, train_events/event_007,
train_events/event_009, train_events/event_010, train_events/event_011,
train_events/event_012, train_events/event_013, train_events/event_014
```

**Researcher response:** _______________
**Rationale:** _______________
**Date:** _______________

---

## HUMAN REVIEW REQUIRED

### Stage-2.1 Ground-Truth Adjudication

**What:** Frame-by-frame visual and audio review of 27 events.
**Who:** Researcher (or authorized reviewer on allowlist).
**Time estimate:** 3–5 minutes per event = 80–135 minutes total.
**Tool:** Existing review workflow (`annotation.review_session` / `adjudication_session`).
**Output:** 27 valid `8.1.0-stage2.1` records with APPROVED status.

**Cannot be automated.** Requires genuine human visual/audio inspection.

### Engine Event Treatment

**Question:** Should `engine_events/event_001` be pooled with train_events or isolated?

**Recommendation:** Isolate as case study (Table 4 in paper). Rationale: single locomotive,
zero trailing cars, T3≡T4 coincidence makes it an edge case that would skew aggregate statistics.

**Researcher response:** _______________

---

## AUTHORIZATIONS REQUIRED (Sequential)

### Auth-1: Ground-Truth Promotion

**Prerequisite:** All 27 Stage-2.1 records APPROVED.
**Action:** Run `railway_detection.annotation.readiness_cli --receipt-path data/governance/stage21_promotion_receipt.json`
**Note:** This command opens media for hash verification. Requires separate media-access authorization.

### Auth-2: EVAL-AUTH

**Prerequisite:** All 7 live bindings populated (protocol, split, R04, manifest, config, policy, receipt).
**Action:** Researcher records `data/governance/eval_authorization.json` with exact schema.
**Note:** Cannot be created until all upstream artifacts exist and validate.

---

## WHAT IS ALREADY COMPLETE (No Action Needed)

- [x] All diagnostic experiments (B0–B7c) executed and results stored.
- [x] Cache artifacts generated (108 JSONL files).
- [x] Statistical analysis computed.
- [x] Model training complete (vision + audio).
- [x] R04 calibration evidence collected (12 supported).
- [x] Protocol documents written (both versions).
- [x] Paper draft skeleton complete (14 sections).
- [x] Research figures generated (24 figures).
- [x] Governance infrastructure implemented and tested.
- [x] Evaluation pipeline validated end-to-end (synthetic).
- [x] 476 tests passing.
- [x] Decision materials prepared (this document).

---

## SUMMARY: What I Need From You

| # | Item | Time | Blocks |
|---|---|---|---|
| 1 | Answer D1 (protocol) | 2 min | Protocol artifact |
| 2 | Answer D2 (metric) | 2 min | Profile binding |
| 3 | Answer D3 (framing) | 2 min | Split/descriptive path |
| 4 | Answer D4 (R04 scope) | 2 min | Camera manifest |
| 5 | Review 27 events (Stage-2.1) | ~2 hours | Ground truth |
| 6 | Authorize promotion (after #5) | 5 min | Receipt |
| 7 | Record EVAL-AUTH (after all above) | 5 min | Official evaluation |

**Total researcher time: ~2.5 hours** (dominated by Stage-2.1 review).

