# Limitations, Defects, and Unresolved Governance Issues

**Governance Disclosure:** *Exploratory evaluation against researcher-adopted AI-assisted reference annotations.* This document catalogs every scientific, architectural, and administrative limitation that prevents claiming canonical Stage-2.1 validation or deployment readiness.

---

## 1. Governance & Administrative Blockers (Canonical Stage-2.1 Not Executed)

1. **Zero Stage-2.1 Human Ground-Truth Adjudications:** All 27 legacy human reviews were invalidated on Oct 14, 2026 (`LEGACY_REVIEW_INVALIDATION_NOTICE`). Although exploratory runs used `RESEARCHER_ANNOTATION_ADOPTION.json`, official human Stage-2.1 review (`scripts/run_stage21_review.py`), digital signatures, and promotion receipts have **not** been executed.
2. **Media Access Hold Remains Active (`AUTH_MEDIA_ACCESS_NOT_GRANTED`):** Canonical `ExecutionGate` and `load_validated_sync_aligner` remain locked by design. Raw `.mov` and `.wav` files remain inaccessible to automated agents without formal approval.

---

## 2. Perception & Preprocessing Defects (`m3_multimodal_replay_manifest.json`)

3. **Unrotated Decode in Nov 7–8 YOLOv8n Caches (`44/54` Sources):** Mission 37/38 migrated video ingestion to PyAV `source_pts=True`, dropping `DISPLAYMATRIX` rotation on `24 front + 20 back` portrait/rotated sources before Mission 39/43 inference. Although Mission 44 (`db40305`) repaired `video.py`, inference was never re-run, leaving `m3_multimodal_replay_manifest.json` artificially sparse (`329` front + `1,020` back detections across `13,092` records; `0.76%–5.07%` qualifying `cam2` density on `9/10` sync events with $T_4$).
4. **Confounding Across Legacy Baseline Comparisons:** Direct numerical comparisons against Oct 13 Phase 10.1 (`0/11`–`6/11`) mix (a) corrected natural-log acoustic preprocessing (`ln(E + 1e-10)`) with (b) unrotated vision decode degradation, preventing attribution of legacy vs Nov 7–8 deltas to policy alone.

---

## 3. Decision-Engine & Collector Defects (`collector.py`, Policy V2)

5. **Collector `window_tolerance_s = 0.50 > stride_s = 0.20` Backfill Bug:** Single isolated detections persist across `3` consecutive `0.20 s` ticks, defeating `confirm_frames = 2` (`2/3` `14.2 s` false alarms on `no_train_events` under `B0`; inflated sync clearances `8/11` vs `5/11` at `tol=0.25 s`).
6. **`MultimodalEvidenceCollector.generate_frames_from_history` Availability Leak:** Reading terminal `tracker.get_availability_map(t)` at end-of-history leaks terminal `MISSING` status backward across earlier timestamps unless steps are assembled sequentially.
7. **Policy V2 `RULE_3C` Premature Opening Under Sparse Detections:** `RULE_3C_DEPARTURE_CONFIRMED_BY_DISAPPEARANCE` triggered `8/8` sync clearances and drove `7/9` (`77.78%`) M4 premature openings (`14.58 s–38.67 s` early) over sparse unrotated back-camera caches (`vs 4/8 = 50.0%` under V1).

---

## 4. Dataset & Statistical Generalization Limits

8. **Left-Censored Approach Recordings (`23/23` Train Events):** $T_1 \in [2.1, 5.8]\text{ s}$ (median `2.8 s`; `event_005` has $T_1 = \text{null}$), shorter than physical warning-to-blocked actuation (`3.4–3.6 s`) on most events (`missed_train = 10/10` and `22/22`).
9. **Post-$T_4$ Right-Censoring (`9/10` Sync Events):** Recordings terminate `0.82 s–2.32 s` after $T_4$ (`< T_clear + open = 4.6 s`) on `9/10` sync events (`event_011` alone has `+7.73 s`), masking legitimate post-departure unblocking.
10. **Single-Crossing Small Sample & Minimal Negative Controls:** `N = 27` events from one daylight-trained passive site (`crossing_A`; night/weather diversity limited; only `3` negative controls totaling `60.0 s` replay exposure; only `1` light engine event; `16/27` events lacking supported R04 sync calibration). Wide 95% Wilson CIs (`30%–50%` width) preclude safety certification (`EN 50126 / EN 50128 / SIL` = ZERO).
11. **Preexisting Suite Test Drift (`33/3,840`):** `23` Mission 26–28 tests assert an older `README.md` hash, `4` tests assert outdated Nov-9 governance/allowlist states, `4` `sys.modules` tests fail under repository `conftest.py`, and `2` preexisting policy/script checks remain open.
