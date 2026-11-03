# Phase 11.6 — Readiness Decision Report

**Status:** Resolution-planning and governance-closure phase. Not a model-evaluation phase. No inference run, no metric computed, no annotation approved, no legacy record invalidated, no promotion to Stage 3. **Ground truth remains `NOT_READY` for formal evaluation. Phase 12 is not begun.**

Supporting artifacts: `docs/PHASE11_6_OPEN_ISSUE_REGISTER.csv` (29 rows, 6 closed / 23 open), `docs/PHASE11_3_RESEARCHER_DECISIONS.md` v1.1.0 (4 recommendations added, 0 decisions made), `docs/PHASE11_6_LEGACY_RECORD_DISPOSITION.md` (prepared, not executed).

---

## 1. Findings resolved (6 of 29 catalogued issues)

| Issue | Resolution |
|---|---|
| `event_009`, `event_015`, `event_016` T0 | Researcher-confirmed `LEFT_CENSORED` (Phase 11.5). **Preserved unchanged this phase** — not reopened, not downgraded. |
| `event_016` T1, T2 | Verified match via direct footage inspection (Phase 11.5) — genuine sequential motion observed. |
| Engine-only event T4 | Closed with no correction needed: the active proposal (v3, confirmed still the only/highest version on disk — unchanged since Phase 11.4/11.5) already self-corrects the exact error the invalidated legacy review made. |

The corrected **0/23** eligibility figure for the primary, unqualified "True physical Detection Latency" point estimate (`docs/PHASE11_EVALUATION_READINESS_REPORT_ADDENDUM_v1.1.md`) is **preserved unchanged this phase** — no new admissible evidence bearing on any other event's T0 observability was found, so no re-adjudication is warranted.

## 2. Findings unresolved because evidence is insufficient (23 of 29)

Full detail and per-row reasoning: `docs/PHASE11_6_OPEN_ISSUE_REGISTER.csv`. None of these were downgraded or closed to improve apparent readiness; each carries an explicit `resolvable_with_existing_footage` assessment and `reason_blocked`.

- **14 rows — genuinely blocked on missing evidence (site survey / landmark reference), not reviewer effort.** Events 004, 006, 007, 009, 011, 013, 015, 018's front-camera T1/T2 boundaries all show the same "minimal visible progression" pattern: the footage itself does not contain enough visual change to independently verify a distinct entry/occupancy moment. No amount of further video re-inspection is expected to change this; a physical site survey establishing fixed distance/landmark references at the actual crossing does not currently exist in this repository.
- **2 rows — `event_006` locomotive identity** (T4 + dependent `T_scene_clear`): Phase 11.5's new evidence (other stationary rolling stock visible from the start of the recording) **corroborates but does not conclusively establish** that the anomalous locomotive is a separate/stationary object rather than a genuine rear banking locomotive. Explicitly assessed and retained as unresolved per this phase's instruction — not closed on partial evidence.
- **3 rows — `event_021` timing**: the T3 mistiming finding (claimed t=3.6s, actual content ~t=8-14s) is documented as a *suspected* discrepancy, evaluated against available evidence, with **no corrected timestamp invented and no claim that camera synchronization has been established** — event_021 is one of 16/27 events with no validated R04 offset. The separate, unexamined T4 (t=60.1s)/`T_scene_clear` region remains open with no new evidence.
- **4 rows — `event_011`'s long static span** (T4/T_scene_clear-adjacent and T1/T2): distinguished in the register as a *different category* from the 14 site-survey-blocked rows above — this one may be resolvable through more rigorous existing-footage analysis (frame-by-frame differencing across the full 29.4–36.9s window, not yet attempted) rather than requiring genuinely missing data. Flagged as a concrete next step, not claimed as resolved.

## 3. Governance decisions pending (4 of 4 — none approved)

`docs/PHASE11_3_RESEARCHER_DECISIONS.md` v1.1.0. For each of the four decisions (minimum review-session duration, reviewer authorization, disagreement/adjudication rules, media-hash verification depth), this phase added an explicit recommended option with rationale, practical implications, and unresolved trade-offs. **Every `Selected option` field remains `PENDING_RESEARCHER_DECISION`** — no recommendation was recorded as approved on the researcher's behalf. These recommendations are a starting point for the researcher's own review, not a substitute for it.

## 4. Legacy-record disposition pending (27 of 27 — none invalidated)

`docs/PHASE11_6_LEGACY_RECORD_DISPOSITION.md` consolidates all 27 affected record identifiers (file paths + SHA-256 hashes), both evidence threads (Thread 1: process-integrity defects from Phase 11.1, applying identically to all 27; Thread 2: content-level evidence from Phase 11.5, applying specifically to events 009/015/016), the proposed full-scope invalidation, the proposed non-destructive mechanism, and a preservation strategy. **Decision-maker, date, scope-confirmation, and mechanism-selection fields are blank and must be completed by the researcher personally.** Nothing was invalidated, moved, or modified — re-confirmed by re-hash, 27/27 byte-identical, at the end of this phase.

## 5. Requirements for beginning genuine review

1. Resolve (or explicitly accept as a standing limitation) the four governance decisions in `docs/PHASE11_3_RESEARCHER_DECISIONS.md` — Decisions 1–3 in particular are already marked as blocking production use of the review workflow (`docs/PHASE11_3_ANNOTATION_REVIEW_WORKFLOW.md`).
2. Execute, or explicitly and in writing decline, the legacy 27-record disposition (`docs/PHASE11_6_LEGACY_RECORD_DISPOSITION.md`) — genuine review cannot proceed while 27 fabricated-process records remain in a state where their status relative to any future genuine review is undefined.
3. Begin individually-attributed Stage-2.1 review using the existing, unused tooling (`stage2_1_schema.py`, `promotion_gate.py`), incorporating the three already-researcher-confirmed T0 corrections and the `event_016` T1/T2 verified-match findings as a starting point, not re-litigating them from scratch.

## 6. Requirements for later evaluation readiness

Evaluation readiness does **not** require every event to become fully observable — many of the open issues above (the 14 site-survey-blocked rows, `event_021`'s unresolved timing) are structural recording/data limitations, not defects to be engineered away. Instead:

- Each metric in `docs/PHASE11_EVALUATION_READINESS_REPORT.md` Section 5 already defines its own eligible-event denominator (e.g. "$T_1$ observable: 22/23"); an event or boundary that remains censored, ambiguous, or unresolved is **excluded from that specific metric's denominator**, not treated as a blocker to evaluating every other metric that does not depend on it.
- The corrected 0/23 Detection Latency eligibility (Addendum v1.1) is one such example: it does not block MTR, POR, Warning Lead Time, Clearance Latency, Excess Closed Duration, Gate Chatter Count, or the no-train nuisance-rate metric, none of which depend on T0 left-censoring status.
- The 23 open issues in this phase's register each map to a specific boundary on a specific event; once Stage-2.1 re-review formally records each boundary's resolved value **or** its formally-accepted censored/uncertain status (per the four-state taxonomy already defined in `docs/PHASE11_GROUND_TRUTH_PROTOCOL.md`), the existing Phase 11 evaluation protocol (Section 6) already specifies how to handle each state — no new protocol rule is required by this phase's findings, only genuine review applying the existing rules.
- A future phase should recompute the full Section 5 eligibility table once genuine Stage-2.1 review (not Phase 11.4/11.5's independent audit, which is evidentiary input, not a substitute for the researcher's own attributed sign-off) exists for all 27 events.

## 7. What this phase explicitly does not claim

- Does not claim `event_006`'s locomotive identity or `event_021`'s T3/T4 timing is resolved — both remain open with an honest insufficient-evidence assessment.
- Does not claim camera synchronization has been established for `event_021` or any of the other 15/27 events without a validated R04 offset.
- Does not claim any of the four governance decisions have been made — all four remain pending, with only non-binding recommendations added.
- Does not claim the legacy 27-record disposition has been authorized or executed.
- Does not claim every event must become fully observable before evaluation can proceed (Section 6 above) — but does not claim evaluation is ready today either, since no event currently has a genuine Stage-2.1 record at all.
- **Does not claim evaluation readiness.** The project's readiness status is unchanged from Phase 11.5: `NOT_READY`.

---

## Verification summary

- `tests/test_phase11_5_adjudication.py`: 6/6 passed (unaffected, re-confirmed).
- Full suite (same exclusions as every phase since Phase 9 — `test_audio_leakage_and_preprocessing.py`, `test_audio_training.py` fail to collect, missing `railway_detection.audio.training`): **405 passed, 3 failed** (`test_audio_v2_pipeline.py::test_v2_figures_and_report_artifacts`, `test_audio_v3_pipeline.py::test_v3_publication_figures_and_reports`, `test_real_dataset_inventory.py::test_audio_extension_anomaly_tracking` — the same pre-existing, confirmed-unrelated failures since Phase 9). No change from Phase 11.5 (no source file modified this phase, only `docs/` and one new `docs/`-level CSV).
- All 27 legacy review records: re-hashed byte-identical to the Phase 11.1 baseline.
- Phase 8 exploratory-run output (46 files, `results/r04_sync_estimation/exploratory_live_run_20261013T194806Z/`): re-hashed byte-identical.
- Three canonical config hashes (`frozen_experiment_v1.yaml` `999a7970...`, `decision_policy_v1.yaml` `051c908d...`, `decision_policy_v2_candidate.yaml` `143782d1...`): re-verified via the project's own `compute_canonical_config_hash`/`load_frozen_config` functions — **not** via raw file-byte SHA-256, which Phase 11.5 found does not match these baselines for reasons unrelated to any actual change (these files' canonical hash is computed over the parsed/normalized YAML content, not raw bytes).
- Git HEAD unchanged at `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`; nothing staged by this phase.

**Phase 12 is not begun.**
