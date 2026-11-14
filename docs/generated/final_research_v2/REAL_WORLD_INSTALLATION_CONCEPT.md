# Real-World Installation Concept — From Close-Range Prototype to Protected Field Layout

**Concept Diagram:** [`fig10_real_world_installation_concept.png`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/final_research_v2/figures/fig10_real_world_installation_concept.png)  
**Quantitative Timing Profiles:** [`exp_a_front_detection.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/experiments/exp_a_front_detection.json) (`upstream_camera_distance_engineering_scenarios`)  
**Prototype vs Proposal Boundary:** The prototype dataset contained only **2 trackside cameras (`camera_1`, `camera_2`)** near the crossing, an audio track on `camera_1`, no physical side camera, and no physical crossing occupancy sensor. Every real-world upstream distance below is a **parametric scenario calculation** (`train speeds` and `field distances` are not measured in repository metadata).

---

## 1. Architectural Differences: Prototype vs Proposed Field Layout

| Subsystem | Collected Layer B v2 Prototype | Proposed Four-Layer Field Concept |
| --- | --- | --- |
| **Layer 1 (`camera_front`)** | Single close-range `camera_1` near crossing (`T2` median `~3.6 s`; `0/11` closed before `T2`) | **Upstream approach camera** mounted far enough upstream (`d_req`) along the right-of-way so full gate closure completes *before* arrival `T2` |
| **Layer 2 (`camera_side`)** | Absent (`0/27` physical side cameras; YOLO `side` class proxy only on `cam_1`/`cam_2`) | **Dedicated lateral camera** spanning the crossing box to track train body motion (`MOVING` vs `STOPPED`) and suppress transient glitches |
| **Layer 3 (`audio`)** | Front camera microphone (road traffic vehicle horns scored `0.800–0.826`) | **Directional acoustic sensor** supporting presence & dwell extension — strictly prevented from triggering closure alone or proving clearance |
| **Layer 4 (`camera_back`)** | `camera_2` observing post-crossing departure (`0/27` `last_carriage` detections; manual offsets in `sync11`) | **Downstream exit camera** with NTP/PTP-synced timestamps and tail/end-of-train visibility to verify physical departure past the island |
| **Layer 5 (`occupancy`)** | Absent (`0/27` sensors; `1/27` documentary `T_scene_clear`) | **Dedicated track/island occupancy sensor** (e.g., axle counter / track circuit / shielded radar-LiDAR crossing zone detector) required to establish `OccupancyState.CLEAR` before reopening |
| **Gate Actuator (`GateModel`)** | Software kinematic model (`warning=2.0 s`, `closing=3.0 s`, stroke `0.0 -> 1.0`, fail-safe latch) | **Fail-closed electro-mechanical barrier** with physical limit switches reporting actual `OPEN / CLOSING / CLOSED / OPENING / FAULT` telemetry |

---

## 2. Parametric Upstream Front-Camera Distance Model

From `Exp A` ([`exp_a_front_detection.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/experiments/exp_a_front_detection.json)):

$$
d_{\mathrm{req}}(v_{\mathrm{km/h}}) = \frac{v_{\mathrm{km/h}}}{3.6} \times \bigl(t_{\mathrm{det}} + t_{\mathrm{confirm}} + t_{\mathrm{warning}} + t_{\mathrm{close}} + t_{\mathrm{margin}}\bigr)
$$

where the three evaluated timing budgets are:
- **`fast_close_0s_warning` (`5.6 s`):** $t_{\mathrm{det}}=0.4$, $t_{\mathrm{confirm}}=0.2$, $t_{\mathrm{warning}}=0.0$, $t_{\mathrm{close}}=3.0$, $t_{\mathrm{margin}}=2.0\text{ s}$.
- **`baseline_with_2s_warning` (`7.6 s`):** $t_{\mathrm{det}}=0.4$, $t_{\mathrm{confirm}}=0.2$, $t_{\mathrm{warning}}=2.0$, $t_{\mathrm{close}}=3.0$, $t_{\mathrm{margin}}=2.0\text{ s}$.
- **`conservative_high_margin` (`10.2 s`):** $t_{\mathrm{det}}=0.8$, $t_{\mathrm{confirm}}=0.4$, $t_{\mathrm{warning}}=2.0$, $t_{\mathrm{close}}=4.0$, $t_{\mathrm{margin}}=3.0\text{ s}$.

### Computed Minimum Upstream Sighting / Placement Distances (`m`)

| Assumed Train Speed ($v$) | Speed ($\text{m/s}$) | `fast_close_0s_warning` (`5.6 s`) | `baseline_with_2s_warning` (`7.6 s`) | `conservative_high_margin` (`10.2 s`) |
| --- | --- | --- | --- | --- |
| **`30 km/h`** | `8.33 m/s` | `46.67 m` | `63.33 m` | `85.00 m` |
| **`40 km/h`** | `11.11 m/s` | `62.22 m` | `84.44 m` | `113.33 m` |
| **`60 km/h`** | `16.67 m/s` | `93.33 m` | `126.67 m` | `170.00 m` |
| **`80 km/h`** | `22.22 m/s` | `124.44 m` | `168.89 m` | `226.67 m` |
| **`100 km/h`** | `27.78 m/s` | `155.56 m` | `211.11 m` | `283.33 m` |

### Engineering Interpretation for Bangladesh Rail Corridors
1. **Why prototype `sync11` closed `0/11` before `T2`:** Even with instant `0.0 s` detection, a `7.6 s` baseline budget (`2 s` warning + `3 s` closing + `2 s` safety margin) requires at least `84.4 m` at `40 km/h` and `168.9 m` at `80 km/h`. Prototype close-range cameras only gave `T2` around `2.8–6.5 s`.
2. **Telecom / Fail-Safe Requirement:** Upstream camera links must use deterministic low-jitter transport with heartbeat supervision so loss of the upstream link triggers `FAULT_FAIL_SAFE` (`gate -> CLOSED`) within `temporal_tolerance_s`.
3. **Clearance Coupling:** No camera downstream or upstream is permitted to open a closed barrier alone; safe reopening strictly requires physical L4 departure confirmation paired with dedicated `OccupancyState.CLEAR` hardware.
