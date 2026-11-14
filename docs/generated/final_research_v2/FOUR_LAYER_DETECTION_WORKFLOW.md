# Four-Layer Detection & Clearance Workflow

**Visual References:**
- [Figure 2: Four-Layer FSM](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/final_research_v2/figures/fig02_four_layer_workflow.png)
- [Figure 3: Replay Gate Timelines](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/final_research_v2/figures/fig03_gate_closure_timeline.png)
- [Figure 4: Departure & Occupancy Workflow](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/final_research_v2/figures/fig04_departure_and_clearance_workflow.png)

---

## 1. Layer 1 — Front Approach Camera (Independent Early Closure)

- **Designated Sources:** `_is_front_source()` matches `camera_1`, `cam_1`, `front`, `approach`, or generic `camera` [`rules_v3_four_layer.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/fusion/rules_v3_four_layer.py#L51-L56).
- **Extraction (`extract_layer1_front_evidence`):** Inspects only fresh, available vision records at master timestamp `t`. Under default `allow_any_front_camera_label=True`, any canonical train label (`front`, `side`, `rear`, `train`) from an upstream camera qualifies at `confidence >= approach_threshold` (`0.35`); setting `False` restricts to `FRONT_APPROACH_LABELS` (`front`, `train_front`).
- **Closure Independence Invariant:** Entering `TRAIN_APPROACHING` -> `WARNING` -> `GATE_CLOSING` depends **exclusively** on Layer 1 (`confirm_frames=2` consecutive front ticks) or a critical `FAULT_FAIL_SAFE` condition. Closure never waits for Layer 2 side confirmation, Layer 3 horn detection, or Layer 4 back camera activity.
- **Glitch Rejection:** A single isolated detection followed by a clean negative frame triggers `RULE_L1_APPROACH_UNCONFIRMED_RESET` back to `IDLE`.

---

## 2. Layer 2 — Side Crossing View (Presence & Movement Tracking)

- **Designated Sources:** `_is_side_source()` matches `camera_side`, `cam_side`, `camera_3`, `cam_3`, or any ID containing `side`. Because Layer B v2 lacks a physical dedicated side camera, `Exp B` also evaluates `camera_1`/`camera_2` `"side"` class labels as a hardware-gap proxy.
- **Tracker (`SideMovementTracker`):** Tracks consecutive available side observations, bounding-box centroid displacement `speed_px_s`, and relative box area change `area_delta` ([`rules_v3_four_layer.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/fusion/rules_v3_four_layer.py#L175-L283)):
  - `UNOBSERVED`: No qualifying side detection at current tick.
  - `SINGLE_FRAME`: First consecutive observation (not yet confirmed as continuous passage).
  - `MOVING`: Centroid displacement `>= stopped_displacement_px_per_s` (`2.0 px/s`) or `area_delta >= 0.03`. Confirms active zone traversal (`RULE_L2_SIDE_MOVEMENT_CONFIRMED`).
  - `STOPPED`: Continuous presence with displacement `< 2.0 px/s` and `area_delta < 0.03` persisting for `>= stopped_min_duration_s`. Emits `RULE_L2_SIDE_STOPPED_HOLD`, latching presence and blocking premature departure progression.

---

## 3. Layer 3 — Trackside Acoustic Horn (Supporting Evidence Only)

- **Signal Processing:** [`audio.features.compute_log_mel_spectrogram`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/audio/features.py#L101-L149) computes `log(mel_spec + eps)` (`log_scale="natural"`) at `16 kHz`, `n_fft=512`, `hop=256`, `64` Mel filters, matching the V3 `CompactTrainHornCNN` training transform (`[64, 61]` shape per `1.0 s` window, `0.5 s` hop).
- **Extractor (`extract_layer3_audio_evidence`):** Flags `horn_detected=True` when any available audio record reports `AUDIO_TRAIN_LABELS` (`train`, `horn`, `rail`, `train_horn`) at `confidence >= 0.3700`.
- **Two Strict Architectural Rules:**
  1. **Zero Closure Triggering in `IDLE`:** Audio horn alone never closes the gate (`exp_k`: `audio_only_no_vision_sync11` and `exp_c` `no_train` events scoring `0.800–0.826` produce `0` gate closures).
  2. **Non-Suppression & Dwell Extension Only:** Audio absence never clears an occupied or uncertain crossing, while active audio during `REAR_CONFIRMED` / `CROSSING_CLEAR` extends the quiet clearance timer by `audio_hold_s=1.5 s` (`RULE_L3_AUDIO_DWELL_HOLD`) to guard against nearby approaching horns.

---

## 4. Layer 4 — Back Exit Camera (Conservative vs Guarded Departure)

- **Designated Sources:** `_is_back_source()` matches `camera_2`, `cam_2`, `back`, `rear`, or `departure`.
- **`DeparturePolicyMode.CONSERVATIVE_POSITIVE` (Default):**
  - Requires positive qualifying detections from `REAR_DEPARTURE_LABELS` (`rear`, `train_rear`) for `rear_confirm_frames=2` observations (`RULE_L4_BACK_POSITIVE_DEPARTURE`), and optionally `LAST_CARRIAGE_LABELS` (`last_carriage`, `train_tail`, `tail`, `end_of_train`) when `require_last_carriage=True` (`RULE_L4_BACK_LAST_CARRIAGE_CONFIRMED`).
  - Simple disappearance of generic train/`side` detections **never** advances to `REAR_CONFIRMED`.
- **`DeparturePolicyMode.GUARDED_DISAPPEARANCE` (Experimental Comparator Only):**
  - Permits disappearance clearance only when all four safety guards hold simultaneously: (1) back camera observed `>= guarded_min_back_frames` (`2`) positive passage frames, (2) passage lasted `>= guarded_min_passage_s` (`1.0 s`), (3) back camera stayed healthy & explicitly negative for `>= guarded_negative_hold_s` (`1.0 s`–`2.0 s`), and (4) Layer 1 & Layer 2 report no train activity (`RULE_L4_BACK_GUARDED_DISAPPEARANCE`). If sparse dropout causes brief non-detection, holds closed (`RULE_L4_BACK_SPARSE_DROPOUT_HOLD`).
- **Train Reversal Protection (`RULE_L4_REVERSAL_HOLD`):** If `front` or crossing-zone `side` re-engages after `rear` onset during departure, progression backtracks/holds closed immediately.

---

## 5. Layer 5 / Final Clearance — `OccupancyVerifier` & Reopening AND-Gate

Implemented in [`occupancy.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/fusion/occupancy.py):

| Resolved `OccupancyState` | Trigger Condition | Gate Decision |
| --- | --- | --- |
| `OCCUPIED` | Explicit dedicated occupancy sensor reports `OCCUPIED` or crossing-zone vision detects active train | Hold closed / re-close |
| `CLEAR` | Fresh, available dedicated occupancy sensor reports `CLEAR` AND no active crossing-zone visual detection (`camera_side`, `camera_2`, `side`/`rear`/`last_carriage`, or `in_crossing_zone=True`) contradicts it | Eligible for `CROSSING_CLEAR` dwell |
| `CONTRADICTORY` | Dedicated sensor reports `CLEAR` simultaneously with active crossing-zone vision detections (`RULE_L5_OCCUPANCY_CONTRADICTION_ABORT`) | Hold closed / fault fail-safe |
| `UNKNOWN` | No dedicated occupancy sensor present (all 27 real Layer B v2 events when `require_occupancy_for_reopen=True`) | Hold closed (`RULE_L5_OCCUPANCY_HOLD_UNKNOWN_OR_MISSING`) |
| `MISSING` | Occupancy sensor present but stale or `available=False` | Hold closed (`RULE_L5_OCCUPANCY_HOLD_UNKNOWN_OR_MISSING`) |

Notice an important refinement verified in unit and synthetic E2E testing: upstream `front` detections on `camera_1` and distant `audio_1` horn scores during approach do **not** falsely mark `OccupancyState.CLEAR` as `CONTRADICTORY` while an approaching train has not yet entered the crossing footprint; only crossing-zone vision evidence triggers `CONTRADICTORY`.

Once `CONSERVATIVE_POSITIVE` departure is confirmed, `OccupancyVerifier == CLEAR`, all required clearance sources (`camera_2` and occupancy) are healthy (no `STALE` / `MISSING` / `UNAVAILABLE` faults on inter-sample or full horizons), zero contradictions occurred, and `clearance_dwell_s` elapses horn-free, the arbiter transitions `REAR_CONFIRMED -> CROSSING_CLEAR -> GATE_OPENING -> IDLE`, remaining continuously interruptible by any new L1 approach or `OCCUPIED` detection (`RULE_L5_MULTI_TRAIN_INTERRUPT`).
