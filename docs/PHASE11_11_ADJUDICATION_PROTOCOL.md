# Phase 11.11 — Formal Stage 2.1 Adjudication Protocol

**Status:** PROTOCOL DRAFT; synthetic-only engineering runner exists, but research decisions, ADJ-AUTH, and genuine adjudication remain unresolved.
**Original date:** 2026-10-15. **Status corrected:** 2026-10-16.
**Repository:** `/Users/sayemuddin/Desktop/Train_automation`.

**CRITICAL:** This protocol is a preparation artifact. No adjudication session has been conducted. No Stage-2.1 record exists. No model of any kind has drafted boundary values for researcher confirmation.

---

## 1. Prerequisites (NOT YET MET)

| Prerequisite | Status |
|---|---|
| Phase 11.8 workflow integrated | ✅ Complete |
| Phase 11.9 pilot audited | ✅ Complete |
| Phase 11.10 decision package delivered | ❌ Missing; see `docs/PHASE11_10_RECONCILIATION.md` |
| Researcher ADJ-AUTH authorization | ❌ NOT GRANTED |
| D1/D3(a) closed or explicitly deferred | ❌ NOT RESOLVED |
| Legacy disposition decided (LEG-EXEC) | ❌ NOT RESOLVED |

---

## 2. Recommended Review Sequence

When ADJ-AUTH is granted, the recommended order is:

1. **engine_events/event_001** (simplest: single-camera-shaped case, 1 event).
2. **no_train_events** (negative controls: 3 events, verify UNOBSERVABLE_NOT_APPLICABLE handling).
3. **train_events** (23 events, shortest-to-longest by media duration).

Rationale: start with the simplest case to validate the tooling, then negative controls to verify the schema handles "no train" correctly, then the main cohort in increasing complexity.

---

## 3. Reviewer Responsibilities

The researcher (or authorized reviewer) personally:
1. Opens the raw media files (front and back camera).
2. Reviews frame-by-frame using ffmpeg or equivalent.
3. Independently determines each boundary (T0–T4, T_scene_clear) without consulting any model output.
4. Records the boundary state using the four-state taxonomy.
5. Provides a rationale for every boundary decision.
6. Attests to model independence.
7. Confirms the record before it is written.

---

## 4. Four-State Boundary Decision Procedure

For each boundary (T0, T1, T2, T3, T4, T_scene_clear):

| State | When to use | Required fields |
|---|---|---|
| `OBSERVABLE` | The boundary is clearly visible/audible in the footage | `value_s`, `reference_camera`, rationale |
| `UNOBSERVABLE_NOT_APPLICABLE` | The boundary does not apply (e.g., no train in no-train events) | rationale only |
| `CENSORED` | The recording ends before the boundary occurs | rationale only |
| `UNCERTAIN` | The footage is insufficient to determine the boundary | rationale only |

**Censoring direction:** For left-censored T0 (train already present at recording start), record as CENSORED with rationale "Train already present at recording start; T0 is left-censored."

---

## 5. Evidence Capture Format

For each OBSERVABLE boundary:
- `value_s`: time in seconds from event start.
- `reference_camera`: "front" or "back".
- `frame_index`: (optional) the specific frame number.
- `rationale`: a specific, non-boilerplate explanation (e.g., "Cowcatcher crosses the painted landmark at frame 29").

---

## 6. Stop Conditions

STOP the session and escalate if:
- Media hash mismatch is detected mid-review (integrity incident).
- The reviewer invokes UNCERTAIN on >50% of boundaries in a batch.
- Any tooling defect could have allowed a model output into the session.
- The researcher withdraws authorization.

---

## 7. Session Runner Interface (Synthetic Engineering Only)

The session runner (`src/railway_detection/annotation/adjudication_session.py`) is
implemented only for synthetic engineering fixtures. It is not authorized or
capable of genuine event review: it rejects non-`synthetic_` event IDs and paths
outside OS temporary storage. Its passing tests verify software behavior only;
they do not constitute human review or approved ground truth. The runner:
1. Load one event from the inventory.
2. Verify media hashes live via `compute_media_sha256_pair()`.
3. Start/stop the session clock.
4. Collect boundary adjudications keyed by the researcher.
5. Build the record via Phase 11.8 helpers (`build_review_record()`).
6. Write ONLY after the researcher confirms.
7. Every write is one record per event, individually timestamped.

**Model firewall:** The runner will refuse to open any file path matching model output patterns (`results/`, `experiments/`, `*.pt`, `predictions*`).

---

## 8. What This Phase Has Prepared (Without ADJ-AUTH)

| Artifact | Status |
|---|---|
| Protocol document (this file) | ✅ Written |
| Phase 11.8 record-construction helper | Implemented; see source/tests; no real record approval implied |
| Phase 11.9 pilot verification | Synthetic-only verification; not human review |
| Review-order manifest template | ✅ Designed (not created — requires ADJ-AUTH) |
| Session runner | ✅ Synthetic-only engineering implementation; genuine-review use remains blocked |

---

## 9. Blocked Operations

| Operation | Blocker |
|---|---|
| Genuine-event session runner implementation/use | Requires missing decisions and separate ADJ-AUTH; current runner is synthetic-only |
| Review-order manifest creation | Requires ADJ-AUTH |
| Any actual review session | Requires ADJ-AUTH + researcher participation |
| Record writes to `data/ground_truth/reviews/` | Requires ADJ-AUTH + researcher confirmation |

---

## 10. Safety Invariants

- No auto-approval. No batch stamping.
- No copying a value from a proposal without the researcher's own frame-level observation.
- Legacy records never edited.
- No promotion writes in this phase (promotion is 11.12's gate).
- Model firewall enforced: no prediction files opened by the runner.