# Limitations & Future Work

This document states the verified technical, dataset, hardware, and governance limitations observed in this research prototype and outlines concrete next engineering steps.

---

## 1. Current Verified Limitations

### A. Raw Media Access & `pre-db40305` Unrotated Caches
- **Boundary:** `data/governance/AUTH-MEDIA-ACCESS.json` does not exist in the repository; [`media_guard.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/safety/media_guard.py) blocks opening any raw `.mov` or `.wav` file (`[AUTH_MEDIA_ACCESS_NOT_GRANTED]`).
- **Impact:** Although container display-rotation normalization (`0, ±90°, ±180°, ±270°`) is now fixed and verified end-to-end with `YOLOv8n` on synthetic videos, real-data `Exp A`–`Exp N` metrics rely on pre-existing Mission 43/39 JSONL caches generated prior to commit `db40305` on unrotated video frames (many `-90°` rotated), driving the `13/23` (`7` zero-detection + `6` sparse/late) B4 missed closures and `0/11` before-`T2` closures.

### B. Missing Dedicated Hardware Modalities in Collected Data
1. **Layer 2 Side Camera (`0 / 27` events):** No physical lateral crossing camera was recorded. Real experiments could only observe YOLO `side` class proxy emissions from `camera_1`/`camera_2`.
2. **Layer 5 Crossing Occupancy Sensor (`0 / 27` events):** No track circuit, axle counter, or zone-clearance sensor exists (`1/27` has documentary `T_scene_clear` on `event_011`). Because `V3_CONSERVATIVE_POSITIVE` refuses to fabricate `CLEAR` from `UNKNOWN`, real `sync11` closures hold safely `CLOSED` / `FAULT_FAIL_SAFE` rather than demonstrating automated real-world reopening.
3. **Layer 4 Tail / End-of-Train Detection (`0 / 27` `last_carriage` labels):** The current `YOLOv8n` checkpoint produced zero `last_carriage` predictions across all `27` back streams (`30` `rear` detections total, mostly outside `sync11`), preventing real-data verification of positive tail departure.

### C. Small Cohorts & Unsynced / Unlabeled Granularity
- Only `11 / 23` train events possess candidate synchronization offsets (`sync11`), limiting closed-loop `cam_1 + cam_2` evaluation and yielding wide Wilson CIs and conservative exact McNemar power (`p = 0.125` for `4 vs 0` premature openings; `p = 0.25` for `3 vs 0` false closures on `n=3` `no_train` clips).
- `audio23` adopted horn labels are event-level (`present` vs `absent_observed`) without horn onset/offset timestamps, and road vehicle horns in Bangladesh mixed traffic (`no_train` max scores `0.800–0.826`, `audio23` `0/10` specificity at `0.37`) prevent audio from acting as an independent closure or absence detector.

### D. Repository Pre-Existing Test & Governance State
- `41` pre-existing failures remain in `pytest tests/` outside V3 deliverables (`23` stale `README.md` catalog hashes, `8` child-process `PYTHONPATH=src` failures, `4` same-process import-order isolation checks, and `6` pre-existing repo allowlist / `AUTH-MEDIA-ACCESS` / legacy-hash-opener / Mission 4A governance checks).

---

## 2. Roadmap for Future Engineering & Research

1. **Authorized Re-Extraction on Upright Frames:** Upon researcher provisioning of `AUTH-MEDIA-ACCESS.json`, run the corrected PyAV/OpenCV decoder over all `27` `.mov` pairs to obtain upright `YOLOv8n` detection caches and measure true upright approach recall vs `pre-db40305` `10/23`.
2. **Dataset Expansion & Tail-Class Re-Training:** Collect upstream (`60–280 m`), dedicated side, and rear-facing multi-angle sequences containing clear `last_carriage` annotations (end-of-train marker/coupler/caboose), trained with event-grouped cross-validation splits (preventing frame leakage across train events).
3. **Physical Occupancy Sensor Hardware Integration:** Couple V3 `OccupancyVerifier` to real dual-channel crossing sensors (e.g., track circuits / radar + loop) with hardware fault diagnostics before any field trial.
4. **Window-Level Audio-Visual Contrastive Labeling:** Annotate horn onset/offset intervals and locomotive vs road-horn acoustically separated classes to suppress `0.80+` road-traffic horn false alarms.
5. **Independent Upstream Camera Synchronization:** Replace manual candidate YAML offsets with hardware PTP/NTP or GPS PPS frame timestamps across all trackside nodes.
6. **Repository Governance Consolidation:** Refresh documentary catalog hashes (`mission26/27/28`), configure editable test environments (`pyproject.toml` / `PYTHONPATH=src`), and resolve pre-existing unguarded raw-hash helpers in legacy manifest scripts separately under PI approval.
