# Phase 11 — Ground-Truth Annotation Protocol

**Document Version:** 1.0.0
**Date:** 2026-10-14
**Status:** PROTOCOL DEFINITION — supplements and does not replace `docs/FINAL_GROUND_TRUTH_PROTOCOL.md` (v7.0.0); formalizes an explicit censoring/observability taxonomy and documents a critical review-integrity finding this phase's audit surfaced.
**Scope:** Annotation semantics only. Model-performance metrics are addressed separately in `docs/PHASE11_EVALUATION_READINESS_REPORT.md`, and none are reported in this phase.

---

## 1. Relationship to the existing protocol

`docs/FINAL_GROUND_TRUTH_PROTOCOL.md` (v7.0.0, 2026-10-12) already defines, in detail: the three-stage AI-proposal → human-review → approved-ground-truth lifecycle (§1.1), the anti-leakage firewall against evaluated-model predictions (§1.2), explicit anti-synthesis and anti-auto-approval mandates (§1.3), directory segregation (§1.4), the canonical $T_0$–$T_4$/$T_{\text{scene\_clear}}$/$T_{\text{horn}}$ boundary table (§2.1–2.2), left-censored-$T_0$ handling (§2.3), and the Operational Danger-Zone Annotation Convention (§2.4, replacing the retired R03 site-survey prerequisite). That document remains authoritative for those definitions and is **not** duplicated here. This document:

1. Adds an explicit, consolidated **observable / unobservable / censored / uncertain** state taxonomy (Section 2) that the existing protocol's field-applicability matrix implies but does not state as a single, unambiguous framework.
2. Documents a **critical review-integrity finding** from this phase's audit (Section 3): every one of the 27 existing Stage-2 human-review records claims `"adjudication_status": "APPROVED"` under a single shared timestamp, which is not possible for genuine, independently-conducted human review and directly violates the existing protocol's own §1.3 anti-auto-approval mandate.
3. Confirms model-prediction independence (Section 4) and cross-camera-synchronization handling for annotation purposes (Section 5), consistent with the existing protocol, with explicit reference to this repository's own R04 findings (Phases 6–10.1).

---

## 2. Observable / unobservable / censored / uncertain: an explicit taxonomy

Every boundary marker ($T_0$ through $T_4$, $T_{\text{scene\_clear}}$, $T_{\text{horn}}$) for every event must be classified into exactly one of the following four states. This taxonomy is a clarification of concepts already present in the existing protocol (`applicable`/`candidate_observable`/`ambiguity_flag`/`left_censored`/`right_censored`) and the Phase 11 brief's explicit instruction to "define observable, unobservable, censored, and uncertain states" and to "not force an exact timestamp where the video does not support one."

| State | Definition | Required fields | Example from this cohort |
|---|---|---|---|
| **Observable** | The boundary event is visually/acoustically present within the recorded footage, at a frame the reviewer can point to with a stated rationale. | `value_s`, `frame_index`, `reference_camera`, `rationale` all populated. | `event_002` $T_1$ = 2.90s (locomotive reaches the danger-zone line, frame directly identifiable). |
| **Unobservable — Not Applicable** | The concept does not exist for this event type (e.g. train-boundary markers for a no-train negative-control recording). | `applicable: false`, `value_s: null`. Never an error condition. | All $T_0$–$T_4$ for `no_train_events/*`. |
| **Censored** | The boundary genuinely occurred, or would occur, outside the recorded window — either before recording started (**left-censored**) or after it ended (**right-censored**). The true timestamp is unknown and must never be fabricated or interpolated. | `applicable: true`, `candidate_observable` may be `true` (left-censored $T_0$, recorded as a recording-relative frame-0 value per §2.3 of the existing protocol) or `false` (right-censored, `value_s: null`), with explicit `rationale` stating which. | `event_001` $T_0$: left-censored (train already visible at frame 0). `event_005` $T_4$: right-censored (recording ends mid-passage; `value_s: null`). |
| **Uncertain** | The boundary is nominally within the recorded window, but visual/acoustic ambiguity (occlusion, poor lighting, overlapping vehicles, ambiguous landmark correspondence) prevents confident placement at a specific frame, independent of any censoring. | `ambiguity_flag: true` with `rationale` describing the specific ambiguity source; value may still be present as a best estimate, but must be treated as lower-confidence in any downstream use, never pooled with high-confidence observations without disclosure. | `event_005` $T_3$: the proposal's own audit log records resolving a 5.60s-vs-6.00s landmark conflict (intermediate cabinet passage vs. true departure boundary) before settling on a canonical value — the kind of case this state exists to flag. |

**Hard rule, reaffirming the existing protocol:** no script, agent, or automated process may convert a Censored or Unobservable boundary into a synthetic Observable value under any circumstance, including interpolation, nearest-neighbor estimation, or inference from the other camera's timeline. This repository's own `MultimodalDecisionEngine`/candidate engine (Phases 9–10.1) are themselves subject to this rule as consumers, not producers, of ground truth — neither has ever been used, and must never be used, to supply a ground-truth value.

---

## 3. Critical finding: fabricated Stage-2 approval records

This phase's audit (`scripts/run_phase11_annotation_inventory.py`) found that **all 27 of the existing `data/ground_truth/reviews/{cohort}/event_XXX_review.json` records carry `"adjudication_status": "APPROVED"`, attributed to `"reviewer_id": "human_researcher_lead"`, all sharing a single identical `review_date_utc` timestamp: `2026-10-12T16:51:21Z`.**

A genuine human review of 27 separate video events — each requiring, per the records' own stated methodology, frame-by-frame FFmpeg inspection and spectral audio re-verification of 6–8 distinct boundary fields — cannot be completed for all 27 events at one identical recorded second. This is not merely suspicious; it is a direct, provable contradiction with:

- The existing protocol's own §1.3: *"No script or agent may automatically change `approval_status` to `'APPROVED'` without verified human researcher sign-off."*
- The same-day **Stage 1 Freeze audit** (`data/ground_truth/snapshots/CANDIDATE_SNAPSHOT_AUDIT_20261012.md`), which explicitly states *"No candidate in this batch has been approved... All 27 proposals remain subject to manual human researcher review"* — yet "Stage 2" review records claiming completed human certification exist for the same batch, dated the same day.

**Disposition, per this repository's standing policy that ground-truth approval is human-only:**

1. **Every one of these 27 `"APPROVED"` records is treated as INVALID in this phase and in every downstream artifact this phase produces.** None is treated as approved ground truth, cited as evidence of review completion, or used to compute, support, or imply any performance metric.
2. This phase does **not** attempt to "fix" these records by deleting, overwriting, or resetting their status — per the Phase 11 brief's explicit instruction not to modify existing candidate annotations in place without preserving prior versions, and because correcting a fabricated approval record is itself a human-authority action, not an action for an AI assistant to take unilaterally.
3. **Recommendation to the researcher:** treat all 27 Stage-2 review records as if Stage 2 has not yet occurred. Before any genuine human review begins, either archive these 27 files (preserving them, consistent with the existing protocol's immutability principle for prior versions) under a clearly-marked `reviews/_invalidated_20261012/` path or equivalent, or add an explicit, prominently-flagged `superseded_by_invalidation: true` / `invalidation_reason` field to each, so no future reader of `data/ground_truth/reviews/` mistakes them for genuine human certification. This action requires the researcher's decision and execution, not an AI assistant's.
4. **Mitigating fact, also confirmed by this audit:** no Stage 3 "approved ground truth" directory (`data/ground_truth/{train_events,no_train_events,engine_events}/`) exists, no `ground_truth_manifest.json` exists, and no `GroundTruthLoader` class exists anywhere in `src/`. The fabrication is confined to the Stage 2 audit trail; it has not propagated into any actually-consumed ground-truth dataset, and no formal evaluation has run against it, because no such evaluation pathway has been built yet.

**All 27 events are therefore, correctly, "candidate annotations awaiting genuine human review"** — the full list is in `docs/PHASE11_EVENT_INVENTORY.json`/`.csv` (Section 7 of the companion Evaluation Readiness Report), each entry's `review_record.trusted_status` set to `INVALID_FABRICATED_APPROVAL`.

---

## 4. Independence from model predictions — confirmed

Per the existing protocol's §1.2 firewall and the Phase 11 brief's explicit Task 4 instruction:

- This phase read no model prediction, no `MultimodalDecisionEngine`/candidate-engine output, no Phase 8/9/10/10.1 decision record, and no cached YOLO/Audio V3 inference result while producing any annotation-related artifact. The event-level inventory (`docs/PHASE11_EVENT_INVENTORY.json`) was built exclusively from (a) the existing AI-generated candidate proposals (themselves built, per their own metadata, from direct video/audio inspection by a separate offline annotation assistant, not from this repository's evaluated detector/classifier), and (b) independently-measured video file metadata (duration, fps, SHA-256) computed directly from the raw `.mov` files and cross-verified against `data/manifests/layer_b_v2_annotation_inventory.json`.
- Calibration estimates (the R04 `camera_sync_offsets_candidate.yaml` empirical offsets used in Phases 6–10.1) are kept entirely separate from annotation timestamps: every event's $T_0$–$T_4$ values in the candidate proposals are recorded on **media-local, per-camera clocks**, never adjusted by any calibration offset. This phase did not apply any R04 offset to any annotation value.
- Reviewer rationale is preserved verbatim from the existing proposal/review records (quoted, not paraphrased into a judgment) wherever cited in this phase's reports, so the evidentiary basis for each claimed value remains traceable to its source file.

---

## 5. Cross-camera synchronization and annotation timestamps

Per the Phase 11 brief ("If cross-camera synchronization is uncertain, annotate media-local timestamps independently unless a valid mapping is supported") and consistent with the existing protocol's R04 status:

- **For annotation purposes, every event's front-camera and back-camera timestamps are independent, media-local clocks.** $T_0$–$T_2$ are measured on `camera_front.mov`'s local clock; $T_3$/$T_4$/$T_{\text{scene\_clear}}$ on `camera_back.mov`'s local clock (per the Operational Danger-Zone Annotation Convention). No annotation value in the existing candidate proposals is adjusted by any cross-camera offset, and this phase introduces no such adjustment.
- **A valid mapping exists for exactly 11 of the 27 events** — the `CALIBRATION_SUPPORTED` subset validated in Phases 6–10.1 (`data/manifests/camera_sync_offsets_candidate.yaml`, `load_validated_sync_aligner`). Even for those 11, the validated offset is an **acoustic-lag reproducibility estimate**, not an independently-verified hardware synchronization (explicitly disclosed in every phase since R04's first validation report) — it is a defensible empirical offset for *model-evidence fusion*, but using it to silently shift a human-annotated ground-truth timestamp would conflate two different kinds of evidence (acoustic correlation vs. direct visual landmark correspondence). **This phase does not use the R04 offset to adjust any ground-truth annotation value**, and recommends any future cross-camera ground-truth metric (e.g. a joint front+back warning-lead-time calculation) either independently re-derive and disclose its own offset from visual landmark correspondence, or explicitly inherit and disclose the R04 acoustic-lag caveat if reusing it.
- For the other 16 events (`PROVISIONAL`/`AMBIGUOUS`/unresolved R04 status), front and back camera annotation timestamps must be treated and reported as **non-comparable** until a validated mapping exists for them specifically.

---

## 6. Summary of annotation-protocol status by cohort

| Cohort | N | $T_0$–$T_4$ applicable? | Dominant observability pattern (see `docs/PHASE11_EVENT_INVENTORY.json` for per-event detail) |
|---|---|---|---|
| `train_events` | 23 | Yes | 20/23 left-censored at $T_0$ (train already visible at frame 0); 22/23 have an observable $T_4$; 21/23 observable-$T_4$ events have $T_{\text{scene\_clear}}$ right-censored; only `event_011` has an observable $T_{\text{scene\_clear}}$. |
| `no_train_events` | 3 | No (`applicable: false`) | Full-duration recordings (11.9–24.6s) audited for road-traffic/horn confounders; no train-boundary markers apply. |
| `engine_events` | 1 | Yes, with $T_3 \equiv T_4$ coincidence (zero trailing cars) | Left-censored at $T_0$–$T_2$ (locomotive already on tracks at frame 0); $T_3{=}T_4$ right-censored in the available duration (`value_s: null`). |

Full per-event detail, including every claimed timestamp value, censoring classification, and the review-integrity flag, is in `docs/PHASE11_EVENT_INVENTORY.json` / `.csv`.

---

## 7. Document change log

- **v1.0.0 (2026-10-14):** Initial Phase 11 protocol. Adds the observable/unobservable/censored/uncertain taxonomy; documents the fabricated-Stage-2-approval finding; confirms model-prediction independence and states cross-camera-synchronization handling for annotation. Supplements `docs/FINAL_GROUND_TRUTH_PROTOCOL.md` v7.0.0 without modifying it.
