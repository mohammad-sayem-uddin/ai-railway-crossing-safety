# Dataset Inventory, Checkpoints & Reference Annotation Status

---

## 1. Layer B v2 Dataset Cohorts (`27` Inventoried Events)

Cataloged in [`data/manifests/layer_b_v2_annotation_inventory.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/manifests/layer_b_v2_annotation_inventory.json) (`sha256: 5585e22ecc7841e2...`) and [`data/manifests/m3_multimodal_replay_manifest.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/manifests/m3_multimodal_replay_manifest.json) (`sha256: 3c720167ea06b671...`):

| Cohort Identifier | Count | Composition | Modalities Present in Repo Caches |
| --- | --- | --- | --- |
| **`all27` (`B4`)** | 27 | `23` `REAL_WORLD_TRAIN_EVENT` (`event_001`..`023`), `3` `REAL_WORLD_NO_TRAIN` (`no_train_events/event_001..003`), `1` `REAL_WORLD_ENGINE_ONLY` (`engine_events/event_001`) | Front vision cache (`camera_1`, `~5 Hz`), back vision cache (`camera_2`, `~5 Hz`), audio window CSV (`audio_1`, `1.0 s` window / `0.5 s` hop) |
| **`sync11`** | 11 | `train_events/event_001, 002, 005, 006, 007, 009, 011, 012, 013, 014, 017` | Subset with empirically accepted dual-camera master-clock offset calibration (`camera_sync_offsets_candidate.yaml`, enforced by `phase12_r04_scope_decision.json`) |
| **`audio23`** | 23 | All 23 `REAL_WORLD_TRAIN_EVENT` clips (`13` `horn_status=present`, `10` `horn_status=absent_observed`) | Used for event-level audio horn classification metrics (`Exp C`). `no_train_events` (`horn_status=null`) and `engine1` are evaluated separately |
| **Dedicated Side Camera** | **0 / 27** | Missing in physical collection | Evaluated via `"side"` label proxy on `camera_1`/`camera_2` (`14/23` train events) + synthetic `camera_side` tests (`Exp B`) |
| **Dedicated Occupancy Sensor** | **0 / 27** | Missing in physical collection | Only `1/27` event (`train_events/event_011`) has a non-censored `T_scene_clear = 32.5 s`; real V3 runs safely resolve `UNKNOWN` (`Exp E`) |

---

## 2. Raw Media Governance Boundary & Cache Provenance

1. **Governance Lock (`AUTH-MEDIA-ACCESS.json` Absent):**
   - `data/governance/leg_exec_authorization.json` (`sha256: 77933986b42b44d3...`) covers only the legacy review invalidation scope (`LEG-EXEC`), whereas `data/governance/AUTH-MEDIA-ACCESS.json` does **not** exist on disk.
   - [`media_guard.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/safety/media_guard.py) blocks any un-authorized read, probe, hash, decode, or inference on the 54 raw `.mov` and 54 `.wav` recordings with `[AUTH_MEDIA_ACCESS_NOT_GRANTED]`.
   - Zero raw media files were opened, bypassed, or re-inferred during this completion mission.
2. **Pre-`db40305` Vision Cache Limitation:**
   - All real-world vision experiments replay the verified Mission 43/39 JSONL caches pinned by `m3_multimodal_replay_manifest.json`. As documented by Mission 44 (`DISPLAY_ROTATION_DEFECT_REPRODUCTION.json`), those caches were extracted **prior to commit `db40305`** without container display-rotation normalization (many raw `.mov` clips carry `-90°` metadata). Consequently, real-world front detection recall (`10/23` causal trigger) is explicitly qualified as a lower bound on unrotated cached inference rather than the post-fix decoder.
3. **Synthetic Verification Alternative:**
   - The rotation fix in `video.py` and `video_demo.py` was directly verified on CPU using the pinned real `YOLOv8n` checkpoint on FFmpeg-synthesized rotated videos across all 7 orthogonal display angles (`0, ±90, ±180, ±270°`) inside temporary sandboxes (`SYNTHETIC_TEMP`).

---

## 3. Model Checkpoints & Frozen Configurations

| Artifact | Path | Verified SHA-256 Prefix | Role / Mapping |
| --- | --- | --- | --- |
| **Vision Model (`YOLOv8n`)** | [`experiments/vision/39f402dfe460/checkpoints/weights/best.pt`](file:///Users/sayemuddin/Desktop/Train_automation/experiments/vision/39f402dfe460/checkpoints/weights/best.pt) | `3f5bb5b23f82f5d9...` (`24,493,159` B) | Classes: `{0: front, 1: rear, 2: side}`; conf `0.35`, input `640×640`, `5.0 Hz`; `0` `last_carriage` classes |
| **Audio Model V3 (`CompactTrainHornCNN`)** | [`experiments/audio/RUN_20261008_AUDIO_V3_ESC50/checkpoints/best.pt`](file:///Users/sayemuddin/Desktop/Train_automation/experiments/audio/RUN_20261008_AUDIO_V3_ESC50/checkpoints/best.pt) | `ea1bb81d74230af7...` (`329,497` B) | Operating threshold `0.3700`; `16 kHz`, `64×61` natural log-Mel (`mean=-1.6010, std=5.1240`) |
| **Audio Model V2 (Prohibited)** | [`experiments/audio/RUN_20261008_AUDIO_V2/checkpoints/best.pt`](file:///Users/sayemuddin/Desktop/Train_automation/experiments/audio/RUN_20261008_AUDIO_V2/checkpoints/best.pt) | `ddab244f1f2e18f7...` | Superseded V2 checkpoint (`329,433` B) |
| **Audio Model V1 (Prohibited)** | `RUN_20260923_AUDIO_001` (`models/audio/best_checkpoint.pt`) | `59b0785f73b201df...` | Listed under `prohibited` in `frozen_experiment_v1.yaml` |
| **Frozen Experiment Config** | [`configs/frozen_experiment_v1.yaml`](file:///Users/sayemuddin/Desktop/Train_automation/configs/frozen_experiment_v1.yaml) | `b8ef5da052f002e7...` | Seed `42`, CPU replay, `allow_unverified_zero_offset: false` |
| **Frozen Decision Policy V1** | [`configs/decision_policy_v1.yaml`](file:///Users/sayemuddin/Desktop/Train_automation/configs/decision_policy_v1.yaml) | `c87c1432f473f84d...` | `RULE_1..RULE_9` |
| **Candidate Policy V2** | [`configs/decision_policy_v2_candidate.yaml`](file:///Users/sayemuddin/Desktop/Train_automation/configs/decision_policy_v2_candidate.yaml) | `d90828b2ec37169d...` | Disappearance-based baseline compared in `Exp D`/`J` |

---

## 4. Reference Annotation Governance Status

- All real-world timestamps (`T0`, `T1`, `T2`, `T3`, `T4`, `T_scene_clear`) and event-level `horn_status` labels come from `docs/generated/professor_evidence/mission43/RESEARCHER_ANNOTATION_ADOPTION.json` (`sha256: 4482847884f05650...`).
- **Missing Annotations Preserved as `null`:** `T_scene_clear` is censored/missing on `26/27` events (`event_011 = 32.5 s`); `no_train_events/event_001..003` have `horn_status = null` (road traffic horns audible in background); `train_events/event_005` has missing `T2`/`T4` arrival/clearance boundaries on the front/back streams.
- **Stage 2.1 Caveat:** Accepted human-reviewed `Stage 2.1` ground truth records remain unpromoted (`STAGE21_RECORDS_MISSING` as verified by `test_official_phase12_readiness_and_execution_gate_fail_closed_on_repo`). Every real-world metric in this suite therefore carries the qualification: *"Exploratory evaluation against researcher-adopted AI-assisted reference annotations."*
