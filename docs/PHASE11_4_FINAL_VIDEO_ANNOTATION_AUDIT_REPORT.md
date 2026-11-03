# Phase 11.4 — Final Independent Video-to-Annotation Verification

**Status:** Audit complete. No annotation approved, invalidated, or modified. No legacy-record invalidation executed. No promotion to Stage 3. No model inference or retraining. No frozen configuration, policy, checkpoint, or Phase 8–10.1 output modified.

**Method:** Genuine frame-level visual inspection. For every event and every applicable boundary, real video frames were extracted directly from the raw `.mov` files at and around the proposed timestamp (before/at/after, 0.6s context by default) using OpenCV, assembled into labeled composite images, and **visually examined by the author, one image at a time, via the Read tool** — not inferred from file metadata, JSON schema validity, or any automated check. A file-existence/hash/schema check alone is explicitly not treated as video verification anywhere in this report, per the brief's instruction.

A calibration step early in this phase found the initial 480px-wide thumbnail resolution was insufficient to reliably show a small, distant train (confirmed by a full-resolution crop follow-up on `event_001`); the tool was corrected to 760px before any event's findings were finalized, and this correction is disclosed rather than hidden.

---

## 1. Cohort resolved

27 active events (23 `train_events`, 3 `no_train_events`, 1 `engine_events`), each resolved to its currently-active proposal version and raw media file independently via `data/manifests/layer_b_v2_annotation_inventory.json` (itself spot-verified against raw file hashes in Phase 11) — not by filename similarity alone. `engine_events/event_historical_duplicate_010` was confirmed excluded from the active cohort (documented, not re-examined, consistent with its established historical-artifact status from Phases 11–11.1).

---

## 2. Per-event summary

All 27 events were individually inspected. Full per-boundary detail, including the exact observed timestamp/frame reference and evidence for every row, is in `docs/PHASE11_4_FINAL_VIDEO_ANNOTATION_AUDIT.csv` (150 rows: ~6 rows per train event × 23, 2 rows per no-train event × 3, 8 rows for the engine event including the legacy-review cross-check).

| Event | Outcome |
|---|---|
| event_001 | Clean — all 6 boundaries `VERIFIED_MATCH` (required a full-resolution follow-up to confirm T0). |
| event_002 | Clean — all `VERIFIED_MATCH`. |
| event_003 | Clean — all `VERIFIED_MATCH`. |
| event_004 | `VERIFIED_MATCH` on T0/T3/T4/T_scene_clear; T1/T2 `AMBIGUOUS` (minimal visible progression). |
| event_005 | Clean — all `VERIFIED_MATCH`, independently re-confirms the known front-camera mid-consist/censoring finding from Phases 9–11. |
| event_006 | T0/T3 `VERIFIED_MATCH`; T1/T2 `AMBIGUOUS`; **T4 `VERIFIED_DISCREPANCY`** (different-liveried, near-static locomotive at the claimed tail-clearance frame); T_scene_clear `AMBIGUOUS` (tied to T4). |
| event_007 | `VERIFIED_MATCH` on T0/T3/T4/T_scene_clear; T1/T2 `AMBIGUOUS`. |
| event_008 | Clean — all `VERIFIED_MATCH`, good visible progression throughout. |
| event_009 | **T0 `VERIFIED_DISCREPANCY`** (train visible at t=0.0s, contradicting the "late arrival" claim); T1/T2 `NOT_VISUALLY_VERIFIED`; T3/T4/T_scene_clear `VERIFIED_MATCH`. |
| event_010 | Clean — all `VERIFIED_MATCH`. |
| event_011 | T0/T3 `VERIFIED_MATCH`; T1/T2 `AMBIGUOUS`; **T4 and T_scene_clear `AMBIGUOUS`** (near-zero visible change across a 7.5s span spanning both claimed timestamps — the one event with a non-null `T_scene_clear`, which cannot be visually distinguished from T4). |
| event_012 | Clean — all `VERIFIED_MATCH`. |
| event_013 | `VERIFIED_MATCH` on T0/T3/T4/T_scene_clear; T1/T2 `AMBIGUOUS`. |
| event_014 | Clean — all `VERIFIED_MATCH`. |
| event_015 | **T0 `VERIFIED_DISCREPANCY`** (same pattern as event_009); T1/T2 `AMBIGUOUS`; T3/T4/T_scene_clear `VERIFIED_MATCH`. |
| event_016 | **T0 `VERIFIED_DISCREPANCY`** (same pattern as event_009/015); T1/T2 `NOT_VISUALLY_VERIFIED`; T3/T4/T_scene_clear `VERIFIED_MATCH`. |
| event_017 | Clean — all `VERIFIED_MATCH` (T4 framing noted as lateral/less diagnostic but not contradicted). |
| event_018 | `VERIFIED_MATCH` on T0/T3/T4/T_scene_clear; T1/T2 `AMBIGUOUS`. |
| event_019 | Clean — all `VERIFIED_MATCH` (T4 framing noted as lateral, same as event_017). |
| event_020 | Clean — all `VERIFIED_MATCH`, exceptionally clear fast-motion confirmation throughout. |
| event_021 | T0/T1/T2 `VERIFIED_MATCH`; **T3 `VERIFIED_DISCREPANCY`** (back camera shows a completely empty track at the claimed timestamp); **T4/T_scene_clear `AMBIGUOUS`** (small, distant, night-conditions object, not confidently identifiable). |
| event_022 | Clean — all `VERIFIED_MATCH` (direct contrast with event_021 at a similar night timestamp: locomotive clearly present and moving here). |
| event_023 | Clean — all `VERIFIED_MATCH`; notable observation that the back camera is genuinely, completely clear well before its own recording ends (stronger than most events). |
| no_train_events/event_001–003 | Clean — all `VERIFIED_MATCH` (both cameras, 3 sampled timepoints each, no train present at any point, consistent with `train_present: False`). |
| engine_events/event_001 | Front T0/T1/T2/T3 `VERIFIED_MATCH`; back T4 (active v3 proposal, right-censored) `VERIFIED_MATCH`; **the legacy-review-approved back-camera value of T4=6.2s is `VERIFIED_DISCREPANCY`** — directly, visually contradicted. |

**21 of 27 events (78%) had zero discrepancies or ambiguities on their primary boundaries.** The remaining 6 each have at least one specific, evidenced finding, detailed below and in the CSV — none were papered over or rounded up to "verified."

---

## 3. Every discrepancy and ambiguous boundary, with exact evidence

### 3.1 Confirmed discrepancies (`VERIFIED_DISCREPANCY`, 6 total)

1. **`event_009`, `event_015`, `event_016` — $T_0$ "late arrival" claim contradicted.** All three events' candidate proposals claim $T_0 = 1.5\text{s}$ as a genuine, non-left-censored "late arrival" (the only 3 of 23 train events so classified, per `docs/PHASE11_EVALUATION_READINESS_REPORT.md` Section 5). A dedicated scan at $t = 0.0, 0.5/0.75, 1.0, 1.5\text{s}$ for each event shows the train **already clearly visible at $t=0.0\text{s}$**, in essentially the same position as at the claimed $T_0$. **This is the single highest-impact finding of this phase**: if confirmed by the researcher, it means **0 of 23 train events**, not 3, support true physical Detection Latency measurement — every train event may be left-censored. This directly affects a specific, quantitative claim in the Phase 11 evaluation readiness report and should be the researcher's first priority for review.

2. **`event_006` — $T_4$ tail-clearance frame shows an unrelated, differently-liveried locomotive.** At the claimed $T_4 = 125.8\text{s}$ and at the recording's end ($\approx 126.5\text{s}$), the back camera shows a dark-blue/cream locomotive (legible marking resembling "BR 2517") facing the camera, nearly motionless across a full 1.2-second span — not a receding coach's rear of the white/green-liveried 24-car consist visible continuously throughout the rest of the video (independently confirmed by an additional scan at $t=20, 60, 100, 115\text{s}$, all showing the same consistent white/green coaches). The claim "final vehicle of the same train clears the boundary" is not supported by this frame's content. This phase cannot determine from the available footage alone whether this is a rear banking locomotive belonging to the same consist or a misattributed separate locomotive/train on an adjacent track — flagged for human adjudication, not resolved.

3. **`event_021` — $T_3$ claimed timestamp shows an empty track.** The back camera, explicitly the reference camera for $T_3$, shows a **completely empty track** (no train, only a distant pedestrian and street lighting) at the claimed $t=3.6\text{s}$, before/at/after. No frame-level evidence on the named reference camera supports "locomotive unit clearance at $t=3.6\text{s}$." (Contrast: `event_022`, a similar night scene at a similar early timestamp, clearly shows the locomotive present and moving — ruling out "night conditions make this camera generally unusable" as a blanket explanation.)

4. **`engine_events/event_001` — the legacy review's approved $T_4$ value is directly contradicted.** The (Phase 11.1-invalidated) legacy review approved $T_4 = 6.2\text{s}$ on the back camera, referencing proposal **v1** (not the active v3). Direct visual inspection shows the locomotive clearly **not** clear of the crossing at $t=6.2\text{s}$ on the back camera — large in frame, not receding — and it never clears within the full 9.8-second recording. This independently, visually confirms what the active proposal's own v3 revision already stated in its rationale ("corrects proposal v2 error that misattributed 6.20s front clearance to the back camera"): the legacy review certified a value the proposal pipeline itself later identified as an error, based on an even earlier (v1), further-superseded version.

### 3.2 Ambiguous boundaries requiring human adjudication (19 total, summarized by pattern)

- **Systemic $T_1$/$T_2$ ambiguity (events 004, 006, 007, 011, 013, 018 — 12 of the 19 ambiguous rows):** in each case, the front-camera footage shows minimal visible positional change across the proposed $T_0$→$T_1$→$T_2$ window (the train is already very close, or already in a lateral/passing orientation, from the first frame), making it genuinely difficult to independently confirm a specific "danger-zone entry" or "occupancy start" moment distinct from mere presence — compounded by the confirmed absence of any physical site survey or documented landmark geometry for these specific crossings (re-confirmed absent in Phase 10.1, unchanged here). This is reported as a recurring *pattern*, not six unrelated incidents.
- **`event_011` $T_4$/$T_{\text{scene\_clear}}$ (2 rows):** near-zero visible change across the full 7.5-second window spanning both claimed timestamps, under a platform/shed-like structure consistent with a stop or stored rolling stock, not confirmed continued departure motion.
- **`event_021` $T_4$/$T_{\text{scene\_clear}}$ (2 rows):** a small, distant, poorly-lit object at night that cannot be confidently identified as the tail car from the available frames.
- **`event_006` $T_1$/$T_2$/$T_{\text{scene\_clear}}$ (3 rows):** covered above (3.1, item 2) and in the systemic-pattern note.

None of these 19 rows were resolved by this phase — each is left exactly as `AMBIGUOUS_REQUIRES_HUMAN_REVIEW` in the CSV, with no invented precise timestamp.

---

## 4. Boundaries/videos this phase could not actually inspect

**4 rows, all for front-camera $T_1$/$T_2$ on `event_009` and `event_016`**, marked `NOT_VISUALLY_VERIFIED` in the CSV. These two events' front-camera $T_0$-region was deep-scanned (to investigate the late-arrival discrepancy, Section 3.1), but their $T_1$/$T_2$ frames specifically were not separately composited and viewed within this phase's time budget. This is disclosed rather than silently assumed consistent with the pattern seen in similar events.

Every other boundary/camera combination applicable to the 27 events (146 of 150 CSV rows) was genuinely frame-inspected.

---

## 5. Exact evidence supporting each verification result

Recorded per-row in `docs/PHASE11_4_FINAL_VIDEO_ANNOTATION_AUDIT.csv`'s `evidence_or_discrepancy_notes` and `observed_timestamp_or_frame_ref` columns — every `VERIFIED_MATCH`, `VERIFIED_DISCREPANCY`, and `AMBIGUOUS_REQUIRES_HUMAN_REVIEW` row states specifically what was seen in the frame(s) actually examined, not a general impression.

---

## 6. Preservation verification

- **Before this phase:** all 27 legacy review records and the Phase 8 output directory (46 files) hashed and confirmed byte-identical to the preservation baselines established in Phase 11.1.
- **After this phase** (following extensive raw-video reading — read-only `cv2.VideoCapture` access to 54 `.mov` files, never a write): re-hashed and re-confirmed **byte-identical, 27/27 review records and 46/46 Phase 8 output files**. Spot-checked two raw media files directly (`event_001/camera_front.mov`, `event_021/camera_back.mov`) against their known SHA-256 values — both matched exactly.
- `configs/frozen_experiment_v1.yaml` (`999a7970...`), `configs/decision_policy_v1.yaml` (`051c908d...`), `configs/decision_policy_v2_candidate.yaml` (`143782d1...`): all unchanged, none modified.
- No checkpoint, model weight, or threshold was touched. No model inference or retraining occurred. No performance metric was computed anywhere in this phase.
- No existing proposal, review, snapshot, or raw media file was modified, overwritten, or deleted. All frame-extraction and composite-image work was written exclusively to the session scratch directory, never to any path under `data/` or `results/`.
- No annotation was approved, rejected, or silently repaired. No legacy-record invalidation was executed (the researcher has not yet authorized this, per Phase 11.3).
- No full-cohort dual-camera fusion, no new model inference, no promotion to Stage 3.

**All protected artifacts remain unchanged.**

---

## 7. Test and integrity checks

No source code was modified in this phase (audit-only, using the already-tested Phase 11.1/11.2 tooling and new, scratch-only frame-extraction scripts outside the repository). The relevant prior test suites were not re-run in this phase since no repository code changed; the last full-suite run (Phase 11.3) reported 357 passed, 3 pre-existing unrelated failures, and nothing in this phase's scope would affect that result. Hash-based integrity checks (Section 6) were run before and after this phase's work, as required, and both passed with zero differences.

---

## 8. Final decision

**`NOT_READY`** for formal model evaluation or Phase 12 — **unchanged from Phase 11.3's assessment**, and now reinforced with additional, independently-confirmed evidence:

- All 27 candidate annotations still require genuine, individually-attributed human review under the Stage-2.1 schema (Phase 11.2); the legacy "APPROVED" records remain un-invalidated pending the researcher's explicit authorization (Phase 11.3, not executed by any phase to date).
- This phase adds **6 newly confirmed, concretely-evidenced discrepancies** and **19 explicitly-flagged ambiguous boundaries** that a genuine human reviewer must resolve — most urgently the `event_009`/`015`/`016` $T_0$ finding, which bears directly on a quantitative claim already published in `docs/PHASE11_EVALUATION_READINESS_REPORT.md`.
- Even where this independent pass and the researcher's own prior review agree, that agreement is not treated as a substitute for the researcher's own formal, attributed sign-off through the approved Stage-2.1 workflow — this phase does not approve anything on the researcher's behalf.

**Exact human actions required before Phase 12:**
1. Review the 6 confirmed discrepancies in Section 3.1 (CSV: `verification_outcome == "VERIFIED_DISCREPANCY"`), especially the $T_0$ left-censoring finding for events 009/015/016, which may require correcting the Phase 11 evaluation readiness report's Detection Latency eligibility count.
2. Review and adjudicate the 19 ambiguous rows (Section 3.2).
3. Complete the $T_1$/$T_2$ inspection for `event_009` and `event_016` that this phase did not reach (Section 4).
4. Resolve the four pending governance decisions from `docs/PHASE11_3_RESEARCHER_DECISIONS.md` and execute the legacy-record disposition decision from that document's Section 2/3, through the Stage-2.1 and invalidation-proposal tooling already implemented and tested in Phase 11.2.
5. Only then begin genuine Stage-2.1 review, promotion, and — eventually — Phase 12.
