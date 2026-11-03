# Phase 11.5 — Researcher-Confirmed Discrepancies and Continued Adjudication

**Status:** Audit-and-adjudication phase. No annotation approved, invalidated, or promoted. No legacy review record formally invalidated. No model inference or performance metric computed. **Ground truth remains `NOT_READY` for formal evaluation. Phase 12 is not begun.**

**Scope:** (1) formally record the researcher's personal confirmation of three Phase 11.4 T0 discrepancies; (2) correct the Phase 11 evaluation-eligibility claim this invalidates, as a versioned addendum; (3) continue the remaining Phase 11.4 follow-up work (event_006, event_021, the engine-only event's T4, and the four `NOT_VISUALLY_VERIFIED` T1/T2 rows); (4) classify all 19 Phase 11.4 ambiguous rows; (5) preserve every historical record unmodified.

Full row-level detail: `docs/PHASE11_5_ADJUDICATION_LEDGER.csv` (29 rows). Full structured records for the three researcher-confirmed corrections: `docs/PHASE11_5_FIELD_ADJUDICATIONS.json`. Module/tests implementing the record type: `src/railway_detection/annotation/phase11_5_adjudication.py`, `tests/test_phase11_5_adjudication.py` (6/6 passing).

---

## 1. Researcher-confirmed discrepancies (Part 1)

The researcher personally reviewed the Phase 11.4 video evidence (not this phase's own frame composites, though this phase's re-generated composites are consistent with it) and confirmed, for all three events, that the train is already visible at frame zero of the front-camera recording, directly contradicting the candidate proposal's "late arrival, non-left-censored" T0 classification:

| Event | Legacy claim (proposal v2) | Researcher-confirmed correction | Corrected T0 value |
|---|---|---|---|
| `train_events/event_009` | T0 = 1.5s, `NOT_LEFT_CENSORED` | `LEFT_CENSORED` | Not observable — **not set to any number** |
| `train_events/event_015` | T0 = 1.5s, `NOT_LEFT_CENSORED` | `LEFT_CENSORED` | Not observable — **not set to any number** |
| `train_events/event_016` | T0 = 1.5s, `NOT_LEFT_CENSORED` | `LEFT_CENSORED` | Not observable — **not set to any number** |

For each event, the true physical arrival/entry time precedes the start of the available recording and is therefore not observable from this footage. No numeric T0 value is substituted for the discarded 1.5s claim — fabricating a replacement timestamp from an unobservable moment would repeat the exact error (an unverified, AI-generated point value) this phase exists to catch. This matches the treatment already used for the other 20/23 train events, which record T0 at the recording-relative frame-0 convention value while being explicitly flagged left-censored, not treated as a true physical onset.

All three proposals share byte-identical T0 rationale text ("First visual emergence: locomotive nose appears in camera view at Frame 45 (t=1.50s). Not left-censored; physical entry observable."), which is additional circumstantial evidence of templated/copy-pasted Stage-1 proposal generation across these three events. This is noted as context, not as a separate finding requiring its own adjudication.

**Recorded as:** three `FieldAdjudicationRecord` objects (`docs/PHASE11_5_FIELD_ADJUDICATIONS.json`), each with an append-only `adjudication_history` of two entries — `FLAGGED_BY_AUDIT` (Phase 11.4, actor `phase_11_4_video_audit`) then `RESEARCHER_CONFIRMED_CORRECTION` (this phase, actor `raihankabirrahu@gmail.com`) — and current `legacy_claimed_*` fields preserved verbatim alongside the new `corrected_*` fields. Each record's `legacy_record_disposition_note` states explicitly that it does **not** constitute formal invalidation of the legacy candidate proposal or any legacy review referencing it; that remains the separate, explicitly researcher-authorized action described in `docs/PHASE11_3_RESEARCHER_DECISIONS.md` Section 3, and was **not** executed by this phase. Each record's `stage_2_1_completeness_note` states explicitly that this is a field-level correction, not a complete Stage-2.1 review record, and does not by itself satisfy `promotion_gate.py` or confer Stage 3 eligibility.

The underlying proposal files (`event_009_proposal_v2.json`, `event_015_proposal_v2.json`, `event_016_proposal_v2.json`) and any legacy review records referencing them **remain unmodified on disk** — verified by re-hash in Section 6 below. The prior T0 classification is recorded here as **disputed/superseded** by this adjudication, using the repository's existing `DISPUTED` term (shared deliberately with `stage2_1_schema.py`'s `ADJUDICATION_STATUSES`); it is not marked `REJECTED` or `APPROVED`, since those are full Stage-2.1 record-level statuses this field-level record does not represent.

---

## 2. Evaluation-eligibility correction (Part 2)

See the dedicated versioned addendum: **`docs/PHASE11_EVALUATION_READINESS_REPORT_ADDENDUM_v1.1.md`**. Summary: the original report's Section 5 credited exactly 3/23 train events (`event_009`, `event_015`, `event_016`) with supporting a "True physical Detection Latency" primary point estimate, on the premise that these were the only non-left-censored arrivals. The researcher-confirmed correction above establishes all three are in fact left-censored. Independently re-checking the full 23-event cohort (`docs/PHASE11_EVENT_INVENTORY.json`, not assumed) confirms these three were the *only* non-left-censored events in the cohort — 20/23 were already flagged left-censored prior to this phase, and 009/015/016 were the remaining 3/23. With all three now corrected, **23/23 train events are left-censored for T0, leaving 0/23 eligible** for the primary, unqualified "True physical Detection Latency" point-estimate metric as originally defined. The exploratory, clearly-labeled recording-relative lower-bound treatment (already present in the original report, Section 5, "23/23" row) is unaffected by this correction and remains available, clearly disclosed as a lower bound, never pooled with the primary estimate.

---

## 3. Continued Phase 11.4 follow-up (Part 3)

### 3.1 `event_006` — claimed T4 tail-clearance frame / locomotive identity (investigated, **not resolved**)

An additional back-camera scan at t=0.0/0.5/1.0s (zero context padding, to see the very start of the recording unobstructed) shows other stationary rolling stock already present on an adjacent track, near a small trackside structure, visible from the first frame. This corroborates — but does not conclusively prove — the hypothesis that the differently-liveried locomotive seen at the claimed T4=125.8s (Phase 11.4's original `VERIFIED_DISCREPANCY` finding) is a separate, plausibly-stationary object on an adjacent track rather than a genuine rear banking locomotive belonging to the passing train's own consist. The alternative explanation remains possible and is not ruled out by this evidence. **No correction is applied.** Ledger rows: `INV_event_006_T4`, `AMB_event_006_T_scene_clear` (the Phase 11.4-ambiguous `T_scene_clear` row is explicitly dependent on this same unresolved question). Classification: `UNRESOLVED_REQUIRES_FURTHER_HUMAN_ADJUDICATION`.

### 3.2 `event_021` — claimed back-camera T3 clearance timestamp (investigated, **re-characterized, not resolved**)

An extended back-camera scan at t=5/8/11/14s shows the track is empty at t=5s (consistent with Phase 11.4's original finding of an empty track at the claimed t=3.6s) but the train becomes visible starting around t=8s and is clearly present/passing by t=11–14s. This re-characterizes the finding from "no train present on this camera at all" to "the claimed T3 timestamp is mistimed by roughly 5–10 seconds relative to this camera's actual content" — a pattern consistent with a front/back camera clock or offset-attribution error, not an absent locomotive-clearance event. `event_021` is one of the 16/27 events without a validated R04 front/back offset, so **no corrected numeric T3 value is proposed** — substituting a number here (e.g. "T3 ≈ 8–11s") would itself be an unverified estimate, which this phase's governing instructions explicitly prohibit inferring. Ledger row: `INV_event_021_T3`, classification `UNRESOLVED_REQUIRES_FURTHER_HUMAN_ADJUDICATION`. **Explicitly not extended to `event_021`'s separate T4 (t=60.1s) or `T_scene_clear` ambiguous rows** (`AMB_event_021_T4`, `AMB_event_021_T_scene_clear`) — those concern a different, unexamined part of the recording and remain unresolved with no new evidence this phase.

### 3.3 Engine-only event's T4 discrepancy (confirmed resolved — **no correction needed to the active proposal**)

Re-reviewed without new footage inspection, since Phase 11.4's existing evidence is already conclusive. The discrepancy is between the **invalidated legacy review** (which approved T4=6.2s on the back camera, referencing superseded proposal v1) and direct visual evidence (the locomotive is clearly not clear of the crossing at t=6.2s and never clears within the full 9.8s recording). Critically, the **currently active proposal (v3)** already self-corrects this exact error in its own rationale text. This finding further corroborates that the legacy review is wrong (consistent with the Phase 11.1 fabrication finding) — it does **not** indicate any error in the active v3 proposal, which requires no field-level correction. Ledger row: `INV_engine_001_T4`, classification `RESOLVED_NO_CORRECTION_NEEDED_TO_ACTIVE_PROPOSAL`.

### 3.4 The four `NOT_VISUALLY_VERIFIED` T1/T2 checks (all four now inspected)

| Event | Boundary | Result |
|---|---|---|
| `event_009` | T1 (4.2s) | Minimal visible positional change t=3.6–4.8s — same systemic "minimal progression" pattern documented in Phase 11.4 for events 004, 006, 007, 011, 013, 018 (now a 7th event). Reclassified `NOT_VISUALLY_VERIFIED` → `AMBIGUOUS_REQUIRES_HUMAN_REVIEW`. |
| `event_009` | T2 (5.0s) | Same composite/pattern as T1. Reclassified → `AMBIGUOUS_REQUIRES_HUMAN_REVIEW`. |
| `event_016` | T1 (4.2s) | Clear sequential motion observed (locomotive nose/undercarriage → passenger-car side profile across t=3.6–4.8s) — a genuine, verifiable progression, unlike event_009's pattern. Reclassified `NOT_VISUALLY_VERIFIED` → `VERIFIED_MATCH`. |
| `event_016` | T2 (5.0s) | Same composite/pattern as T1. Reclassified → `VERIFIED_MATCH`. |

These are reclassifications of the Phase 11.4 audit's own `verification_outcome` column (recorded in the Phase 11.5 ledger, not by editing `PHASE11_4_FINAL_VIDEO_ANNOTATION_AUDIT.csv` in place — that file is preserved unmodified; see Section 6). They are independent findings from the separately-tracked `event_009`/`event_015`/`event_016` T0 corrections in Section 1 above — event_009's T0 is researcher-confirmed corrected, but its T1/T2 remain only audit-flagged ambiguity, not researcher-confirmed.

### 3.5 The 19 Phase 11.4 ambiguous rows — classified

Full detail in the ledger. Summary:

- **3 rows** directly tied to this phase's `event_006`/`event_021` investigations above (`AMB_event_006_T_scene_clear`, `AMB_event_021_T4`, `AMB_event_021_T_scene_clear`) — carry forward new context but remain `UNRESOLVED_REQUIRES_FURTHER_HUMAN_ADJUDICATION`.
- **16 rows** (events 004, 006 front T1/T2, 007, 011 ×4, 013, 015 front T1/T2, 018) received **no new video inspection this phase** and are classified `UNRESOLVED_NO_NEW_EVIDENCE_THIS_PHASE`. Most share the same systemic "minimal visual progression" pattern already named in Phase 11.4, for which no independent site-survey or physical landmark data exists to resolve further from video alone — this is a genuine data limitation, not a deferred task that more video-watching would fix.
- **`event_015`'s T1/T2 ambiguous rows are explicitly distinct from its T0 correction** (Section 1): the researcher confirmed T0 only. T1/T2 remain open.

None of the 19 original ambiguous rows are resolved to a confirmed verified-match or discrepancy this phase (the 4 T1/T2 rows resolved in 3.4 originated as `NOT_VISUALLY_VERIFIED`, a separate category, not from the 19 ambiguous rows).

---

## 4. What this phase explicitly does NOT do

- Does not mark any legacy proposal or legacy review record as formally invalidated. All three `FieldAdjudicationRecord`s state this explicitly in `legacy_record_disposition_note`.
- Does not treat any `FieldAdjudicationRecord` as a complete Stage-2.1 review (`stage_2_1_completeness_note`); none is wired into or accepted by `promotion_gate.py`.
- Does not promote any annotation to Stage 3.
- Does not infer or fabricate a replacement T0/T3 timestamp for any corrected or re-characterized boundary.
- Does not accept the newest proposal version as correct by default — every claim above traces to direct visual evidence or an explicit researcher statement, not proposal recency.
- Does not begin Phase 12.
- **Does not declare the project ready for evaluation.** Three researcher-confirmed T0 corrections do not, by themselves, resolve the 19 ambiguous Phase 11.4 rows (16 of which remain genuinely unresolved), the four pending Phase 11.3 governance decisions, or the legacy-record disposition question. See Section 7.

---

## 5. Regression tests

`tests/test_phase11_5_adjudication.py`: 6/6 passed (synthetic fixtures only; never touches `data/ground_truth/`).

No other repository source file was modified this phase (the ledger-build and field-adjudication-instantiation scripts live in the session scratch directory, outside the repository, consistent with Phase 11.4's practice). The full project test suite was not re-run beyond the new module's own tests, since no other source file changed; the Phase 11.4 baseline (357 passed, 3 pre-existing unrelated failures, unaffected since Phase 11.2) stands.

---

## 6. Integrity re-verification

- All 27 legacy review records: re-hashed, byte-identical to `/tmp/phase11_1_reviews_baseline_hashes.txt`.
- Phase 8 output (46 files): re-hashed, byte-identical to `/tmp/phase8_output_hashes_baseline_sorted.txt`.
- `configs/frozen_experiment_v1.yaml`, `configs/decision_policy_v1.yaml`, `configs/decision_policy_v2_candidate.yaml`: all three canonical SHA-256 hashes unchanged.
- `docs/PHASE11_4_FINAL_VIDEO_ANNOTATION_AUDIT.csv` and its companion report: unmodified (Phase 11.5 reclassifications live only in the new `docs/PHASE11_5_ADJUDICATION_LEDGER.csv`, never written back into the Phase 11.4 file).
- `docs/PHASE11_EVALUATION_READINESS_REPORT.md`: unmodified (correction is a separate versioned addendum, Section 2 above).
- `docs/PHASE11_EVENT_INVENTORY.json`: unmodified (read-only reference for the full-cohort eligibility recount).
- Git HEAD unchanged; nothing staged by this phase prior to the researcher reviewing these new files.

---

## 7. Exact actions still required before Phase 12 — the project is NOT ready for evaluation

1. Resolve the 16 ambiguous rows with no new evidence this phase (Section 3.5) — most require a physical site survey/landmark reference that does not currently exist, or explicit researcher acceptance of the AI-proposed value despite the acknowledged ambiguity.
2. Resolve `event_006`'s locomotive-identity question and `event_021`'s T3 mistiming (and separately, its still-unexamined T4/`T_scene_clear` region) — both flagged, neither closed.
3. Resolve the four pending governance decisions in `docs/PHASE11_3_RESEARCHER_DECISIONS.md` (review-duration floor, reviewer authorization, disagreement/tolerance rules, media-hash verification depth) — still explicitly `PENDING_RESEARCHER_DECISION`, untouched by this phase.
4. Execute (or explicitly decline) the legacy 27-record disposition through the already-implemented invalidation-proposal tooling (`promotion_gate.py`) — this phase's three T0 corrections are **not** that action and do not substitute for it.
5. Begin genuine, individually-attributed Stage-2.1 re-review of all 27 events (including full incorporation of this phase's three corrected T0 boundaries and the `event_016` T1/T2 reclassification into actual Stage-2.1 records) — no Stage-2.1 record exists yet for any event.
6. Only then build and invoke an actual Stage 3 promotion step.

**This phase records three genuine, researcher-confirmed corrections and meaningfully narrows two previously-open investigations, but it does not close the gap to evaluation readiness.** The eligibility consequence alone (0/23 for the primary Detection Latency point estimate) is a reduction in what can ever be claimed, not evidence of readiness. The project remains `NOT_READY` for formal model evaluation, exactly as in Phase 11.4.
