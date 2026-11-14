# Publication Readiness & Scientific Defensibility Report

**Target Publication Venue Tier:** IEEE Transactions / IEEE Access / Transportation Research Part C or Safety-Critical CPS Workshop Paper (conditional on transparent scoping as a **Safety-Critical System Architecture + Exploratory Field Failure & Dataset Audit Study**).

---

## 1. Publication Strengths Already Achieved

1. **Concrete Quantitative Root-Cause Storytelling (`fig01`–`fig14`):**
   - **Data Integrity Diagnosis (`fig11`):** Proves mathematically why naive Vision `99.46% mAP@50` (`705d388743ea`) failed in the field (`87.1%` train-aug in test, `93.1%` 10-min session leakage across `27/29` sessions, `0` negatives) and fixes it constructively via `vision_v1_session_grouped` + `audio_v3_stem_grouped` (`0%` overlap).
   - **Safety-First State Machine Design (`fig02, fig05–09`):** Demonstrates empirically across `Exp A–M` why stateless detectors (`3/3` no-train FP) and disappearance rules (`V2`: `4/11` premature openings) fail, whereas V3 conservative AND-gated clearance holds **`0/11` premature openings** and **`0` unsafe openings** across `18` fault injections (`Exp L`) and `100` stress runs (`Exp Q`).
   - **Road-Horn Confound Quantified Mechanistically (`Exp O`, `fig12`):** Establishes exact run-length persistence (`no_train` `3–9` windows `>=0.37` vs `1` window `>=0.75`), calibration behavior (`ECE 0.2955 -> 0.0709`), and why acoustic detectors must remain strictly non-gating support layers in mixed developing-corridor traffic.
   - **Edge Engineering + Stress Cliff (`Exp P–Q`, `fig13–14`):** Measures exact CPU speedups (`74.91%` weight strip, `2.32×` at `416px`, `0.0391 ms/tick` FSM, `96.6%–98.6%` duty-cycle frame reduction) and reveals a previously undocumented **healthy empty-frame optical attenuation hazard** (`alpha = 0.35 -> 0%` closure without tripping staleness).
2. **Exemplary Negative-Result & Governance Rigor:**
   - Every real-data qualification (`ready: false`, `0` Stage-2.1 reviews, `day/overcast` vs `night/clear` Layer B confound, `pre-db40305` rotation boundary, unmeasured physical RPi hardware) is explicitly disclosed, preventing reviewer pushback over hidden overfitting or overclaiming.
3. **Full Reproducibility Bundle:** Clean codebase, `174`-file access classification, unified CSV/Markdown publication tables (`results/publication_tables/`), SHA-256 hash manifests, and verifiable CLI governance checks.

---

## 2. Publication Submission Gates (What Can Publish Now vs After Raw Media Auth)

| Publication Framing | Readiness Right Now | Blocking Gaps if Claimed Without Remediation |
|---|---|---|
| **Option A (Ready for Submission Now):** *Safety-Critical Four-Layer Finite State Architecture, Forensic Split-Leakage Remediation, Fault/Weather Stress Analysis & Edge Feasibility for Mixed-Traffic Level Crossings* | **READY (with minor formatting/table polish)** — All proofs (`Exp A–Q`, `fig01–14`, 8 verified refs) are reproducible today with honest limitations. | Must frame real-video `Exp A–J, O` explicitly as **exploratory retrospective diagnostics** using AI-assisted adopted references and pre-rotation caches, and frame Vision/Audio clean splits as **prepared remediation** rather than claiming retrained V2/V4 field accuracy. |
| **Option B (Requires Phase R1–R3 Execution Before Top-Tier Journal Validation):** *End-to-End Field-Validated Cross-Weather Autonomous Crossing Protection System* | **BLOCKED** by external prerequisites (`AUTH-MEDIA-ACCESS.json`, Stage 2.1 human labeling, retraining, physical RPi/sensor deployment). | Cannot claim field SOTA accuracy until: (1) Stage 2.1 reviews complete; (2) upright rotated raw frames are re-extracted; (3) Vision/Audio models are retrained on the new session/stem-grouped splits with negative road-horn + rainy/night samples; (4) multi-crossing multi-weather data replaces the single `day/overcast` morning session. |

---

## 3. Reviewer Risk Checklist & Mitigation (Verified Clean)
- *Overclaiming field generalization from `99.46% mAP`?* Mitigated directly (`Table 1` exposes `87.1%` aug + `93.1%` session leakage).
- *Confusing host Apple M1 CPU timing with Raspberry Pi telemetry?* Mitigated directly (`Table 4` & `fig13b` explicitly stamp `ANALYTICAL_PROJECTION_UNMEASURED_HARDWARE`).
- *Unsupported weather numbers (`104 rainy` images)?* Scrubbed completely (`NOT FOUND`).
- *Undisclosed `Convention A` vs `Convention B` simulation timing?* Disclosed with exact `+0.20 s` offset formula.
