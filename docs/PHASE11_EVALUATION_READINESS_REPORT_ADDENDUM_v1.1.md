# Addendum v1.1 to `docs/PHASE11_EVALUATION_READINESS_REPORT.md`

**Date:** 2026-10-14. **Phase:** 11.5. **Type:** versioned correction addendum — does not replace, overwrite, or edit the original report, which remains on disk unmodified and is the authoritative historical record of what was claimed in Phase 11. This addendum documents a correction discovered after that report was written. **No model inference or performance metric is introduced by this addendum.**

---

## 1. The original claim

`docs/PHASE11_EVALUATION_READINESS_REPORT.md`, Section 5 (per-event metric-support table):

> | True physical Detection Latency | $T_0$ NOT left-censored | **3/23** (`event_009`, `event_015`, `event_016` — the only non-left-censored arrivals) |

Restated in Section 8 (readiness summary):

> True physical Detection Latency: only 3/23 events (the rest require the exploratory, clearly-disclosed lower-bound treatment).

This claim rested on the premise that `event_009`, `event_015`, and `event_016` were genuine, non-left-censored "late arrival" events — i.e. the train's physical entry into the recorded scene was observed to occur at the recording's proposed T0 (1.5s in all three cases), with footage available from before that arrival.

---

## 2. Confirmation that this premise is false

Phase 11.4's independent frame-level video audit found, for all three events, that the train is already visible at the very first frame of the recording (t=0.0s), in essentially the same position as at the claimed T0=1.5s — directly contradicting the "late arrival" premise (`docs/PHASE11_4_FINAL_VIDEO_ANNOTATION_AUDIT.csv`, `VERIFIED_DISCREPANCY` rows for all three events' `T0_first_visible` boundary).

In Phase 11.5, the researcher personally reviewed this video evidence and **confirmed** the discrepancy for all three events: the train is already visible at frame zero; the existing late-arrival/non-left-censored classification is incorrect; T0 must be treated as left-censored. This is recorded as a formal, attributed adjudication in `docs/PHASE11_5_FIELD_ADJUDICATIONS.json` and `docs/PHASE11_5_ADJUDICATION_LEDGER.csv` (rows `T0_CORR_event_009`, `T0_CORR_event_015`, `T0_CORR_event_016`), each citing the specific source video, active proposal version, and researcher-confirmation timestamp.

---

## 3. Revised conclusion

`event_009`, `event_015`, and `event_016` **cannot support an uncensored "True physical Detection Latency" point estimate**. In each case, the true physical arrival time precedes the start of the available recording and is not observable from it — the same structural limitation already affecting the other 20/23 train events, not an exception to it.

---

## 4. Revised eligibility count — checked against the full cohort, not assumed

Per this addendum's governing instructions, the revised count is **not** asserted as 0/23 merely because the three previously-credited events are disqualified. It is independently re-derived by checking all 23 train events in `docs/PHASE11_EVENT_INVENTORY.json` (not re-reading only the three affected events):

```
train_events cohort size:        23
already left_censored (pre-11.5): 20
non-left-censored (pre-11.5):      3  ->  event_009, event_015, event_016
                                        (confirmed as the ONLY 3 non-left-censored events in the full cohort)
```

With all three of the only non-left-censored events now confirmed left-censored, and no other train event in the 23-event cohort disputed on this boundary, the protocol's eligibility condition for this metric (`$T_0$ NOT left-censored`, Section 5 of the original report) is satisfied by **zero** events in the cohort.

**Revised eligible count: 0/23.**

This matches the number the Phase 11.4 report flagged as a possible consequence, but it is derived here, not assumed, per the full-cohort check above.

---

## 5. What is unaffected

- **Exploratory recording-relative Detection Latency (lower bound only)** — Section 5's separate "23/23" row, already explicitly labeled exploratory and required never to be pooled with the primary estimate. Unaffected by this correction; still 23/23, still exploratory-only.
- **Every other metric row in Section 5** (MTR, POR, Warning Lead Time, Clearance Latency, Excess Closed Duration, Gate Chatter Count, no-train nuisance rate, engine-only metrics) — none depends on the T0 left-censoring status of these three events in the way the primary Detection Latency metric does. Not recomputed or re-asserted here; this addendum's scope is Section 5's Detection Latency row only.
- The engine-only event's separate, already-documented `0/1` T4-anchored eligibility (Section 3/5 of the original report) — unrelated to this correction.

---

## 6. Remaining limitations and unresolved eligibility decisions

- This addendum corrects a **count**, not a **conclusion about readiness**. The original report's overall recommendation (Section 8: "Ground truth is not ready for approval-gated evaluation... No formal performance claim should be made before both steps are complete") already governed this metric and every other; this correction does not change that governing recommendation, it reinforces it.
- `event_009` and `event_016`'s T1/T2 boundaries (unaffected by the T0 correction, but previously `NOT_VISUALLY_VERIFIED`) are now visually inspected per Phase 11.5 — see `docs/PHASE11_5_ADJUDICATION_REPORT.md` Section 3.4 — and do not change any Section 5 eligibility figure, since T1/T2 ambiguity does not gate the Detection Latency metric.
- 16 of the Phase 11.4 audit's 19 ambiguous boundary rows remain unresolved with no new evidence as of this addendum (Section 3.5 of the Phase 11.5 report) — some of these affect the `MTR`/`Warning Lead Time`/`Clearance Latency` eligibility rows in Section 5 of the original report (which depend on T1/T4 observability), and **this addendum makes no claim about those rows**; a future, separately-scoped correction would be required if any of them are found to affect those counts.
- No Stage-2.1-approved ground truth exists for any of the 23 train events as of this addendum. This correction updates what the eligibility count *would be* under the original protocol's rules, applied to currently-available (not yet Stage-3-promoted) candidate annotations — it is not itself a statement that any annotation is now approved or evaluation-ready.

---

## 7. Disposition

This addendum supersedes Section 5's "True physical Detection Latency: 3/23" figure and Section 8's restatement of it, for the purpose of any future reference to that specific figure. The original report file is preserved unmodified on disk as the historical record of what was originally claimed and why. Any future citation of the Detection Latency eligibility count should cite **this addendum (0/23)**, not the original report's Section 5/8 figures, and should note that even 0/23 is a structural recording limitation (left-censoring), not a model or system deficiency.
