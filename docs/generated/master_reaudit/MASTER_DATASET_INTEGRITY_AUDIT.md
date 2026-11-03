# Master Dataset and Data Integrity Audit

**Project:** Train Gate Automation — Bangladesh  
**Auditor:** Independent Principal Research Auditor, Software Architect, Computer Vision Researcher, Security Auditor and Scientific Reproducibility Reviewer  
**Mission:** Master Mission 16A  
**Repository:** `/Users/sayemuddin/Desktop/Train_automation`  
**Standard:** Strict read-only inspection of non-sensitive metadata, schemas, and inventories. Zero raw media or protected processed bytes opened.

---

## 1. Executive Summary

This audit independently evaluates the physical and methodological integrity of the research dataset as an empirical basis for scientific claims:
1. **Cohort Reality:** The physical archive comprises **27 raw recording events** from a single crossing (`crossing_A`) across two capture sessions.
2. **Ground-Truth Vacuum:** There is currently **zero approved Stage-2.1 ground truth** in the repository. All 27 legacy review records claiming `APPROVED` status were invalidated in Phase 11.6 due to identical, fabricated AI timestamps (`2026-10-12T16:51:21Z`).
3. **Severe Sampling & Stratification Limitations:**
   - 23 train events, 3 no-train events, 1 engine event.
   - Heavy left-censoring ($T_0 \le 0.0\,\text{s}$ in 18 out of 23 train events).
   - Only 3 negative control events (insufficient for statistical false-alarm bounds).
   - Single site (`crossing_A`): zero cross-site geographic or physical generalization.
4. **R04 Exploratory Dual-Camera Scope:** Secondary camera synchronization is verified as supported for strictly **11 events**. Claims of full-cohort dual-camera coverage or expanding to 12 events (via `event_010`) are scientifically unsupported.
5. **Scientific Viability:** The dataset supports only **descriptive, single-site exploratory benchmarking**. It cannot support general railway safety claims, operational reliability assertions, or inferential hypothesis tests.

---

## 2. Cohort Verification: Conceptual Taxonomy

To prevent methodological conflation, the audit distinguishes four fundamentally different states of the dataset cohort:

| Conceptual State | Count | Definition in Repository | Current Status |
|---|:---:|---|---|
| **Inventory Claim** | 27 | Historical narrative claim that 27 events were captured in Bangladesh | Verified present in filesystem manifests |
| **Verified Physical Inventory** | 27 | Confirmed existence of raw stream containers across two capture sessions | Verified via non-media metadata (`PHASE11_EVENT_INVENTORY.json`) |
| **Approved Ground-Truth Cohort** | **0** | Events having human-certified, allowlist-signed Stage-2.1 ground truth | **EMPTY** (All 27 legacy records invalidated in Phase 11.6) |
| **Evaluable Research Cohort** | **0** | Events ready for ingestion by official Phase 12 evaluation runner | **EMPTY** (Readiness gate blocks execution without approved GT) |

**Key Finding:** While 27 events physically exist as data bundles, **zero events are currently evaluable** for official scientific benchmark reporting.

---

## 3. Dataset Inventory and Metadata Analysis

Inspection of metadata files (`docs/PHASE11_EVENT_INVENTORY.json`, `docs/PHASE11_EVENT_INVENTORY.csv`) yields the structural characteristics of the 27 events:

### Event Cohort Distribution

| Cohort Name | Count | Event Identifiers | Primary Camera | Secondary Camera (Back) | Notes |
|---|:---:|---|---|---|---|
| `train_events` | 23 | `event_001` through `event_023` | Available (100%) | Available in subset (R04) | Full passenger/freight train passages |
| `no_train_events` | 3 | `event_001`, `event_002`, `event_003` | Available (100%) | Available | Negative controls (road traffic, pedestrians, empty tracks) |
| `engine_events` | 1 | `event_001` | Available (100%) | Available | Isolated locomotive; motive unit is also tail ($T_3 \equiv T_4$) |

### Censoring and Boundary Completeness

Inspection of boundary proposals reveals substantial censoring across the train cohort:
- **Left-Censoring ($T_0 \le 0.0\,\text{s}$):** In **18 of the 23 train events**, the train was already present in the field of view at recording onset ($t = 0.0\,\text{s}$). True arrival and approach detection latency cannot be measured from video onset for these events without bias. Only 5 events (`event_009`, `event_010`, `event_014`, `event_017`, `event_021`) capture the physical arrival into an empty scene.
- **Right-Censoring:** In `train_events/event_005`, the recording terminates before the train completely vacates the danger zone, making $T_4$ (tail clearance) right-censored and unobservable.
- **Boundary Omissions:** In several events, visual obstruction prevents observation of $T_1$ (danger zone entry line) or $T_2$ (crossing roadway line).

---

## 4. Dataset Quality and Methodological Deficits

### 4.1 Class and Event Imbalance
- **Extreme Class Imbalance:** 23 train events versus only 3 no-train events.
- **Statistical Implication for False Alarms:** With $N=3$ negative events, observing 0 false activations yields a Wilson 95% confidence interval of $[0.00, 0.56]$. A system could have an operational false alarm rate exceeding 50% while remaining completely consistent with the observed zero false alarms in this tiny sample.
- **Engine Event Isolation:** With $N=1$, the engine event cannot form a statistically meaningful cohort. It must be evaluated purely as an illustrative case study and excluded from pooled train metrics.

### 4.2 Session and Environmental Imbalance
- All data originates from **two recording sessions** conducted at a single geographical site (`crossing_A`).
- **Weather Strata:** Predominantly daylight, clear weather. Rain, heavy fog, and severe adverse weather conditions are entirely unrepresented.
- **Night / Low-Light Conditions:** Only a minimal fraction of events occurred under twilight/night conditions; headlight glare and optical bloom are insufficiently sampled.
- **Selection Bias:** Capture sessions were scheduled during periods of active operational recording; long quiet periods without train activity were not captured continuously.

### 4.3 Leakage and Contamination Risks
- The YOLOv8n detector was originally trained on Layer A images and fine-tuned on early Layer B samples.
- **Firewall Integrity:** The frozen evaluation contracts (`input_contracts.py`) strictly enforce separation between evaluation replays and model weights. However, historical splits (e.g. `development_fallback`) must be audited to ensure that frames from the 23 test events were not included in the pre-training set.

---

## 5. R04 Dual-Camera Exploratory Scope Audit

### 5.1 The 11-Event Supported Boundary
The secondary (departure/back-stream) camera was uncalibrated at capture time. R04 represents the effort to establish empirical inter-camera time offsets ($\Delta t = t_{\text{back}} - t_{\text{front}}$).

`configs/exploratory_dual_camera_v1_supported_subset.yaml` and `docs/R04_CALIBRATION_VALIDATION_REPORT.md` establish that cross-camera time alignment is valid only for **11 events**:
- Included (11): `train_events/event_001`, `event_002`, `event_005`, `event_006`, `event_007`, `event_009`, `event_011`, `event_012`, `event_013`, `event_014`, `event_017`.
- Provisional Excluded (7): `engine_events/event_001`, `no_train_events/event_003`, `train_events/event_003`, `event_016`, `event_018`, `event_019`, `event_021`.
- Ambiguous Excluded (9): `no_train_events/event_001`, `event_002`, `train_events/event_004`, `event_008`, `event_010`, `event_015`, `event_020`, `event_022`, `event_023`.

### 5.2 Prohibition on Expanding to 12 Events (`event_010`)
Historical documents noted an attempt to add `event_010` to the dual-camera subset to report $N=12$.
**Auditor Finding:** `event_010` exhibits significant acoustic/visual feature ambiguity, yielding conflicting offset estimates across calibration passes. It is explicitly classified under `excluded_events_ambiguous` in the canonical configuration. Silently expanding R04 to 12 events violates the frozen experiment specification and is scientifically invalid.

---

## 6. Dataset Limitations & Scientific Claim Support Matrix

| Potential Research Claim | Evaluated Dataset Support | Classification | Methodological Justification |
|---|---|---|---|
| **Descriptive single-site benchmark at `crossing_A`** | The 27 events provide a structured set of historical recordings for comparative offline pipeline analysis. | **Supported** | Scope is strictly confined to the observed sample without generalization claims. |
| **Train detection evaluation (Front Camera)** | 23 train events cover various train speeds and consist lengths under primary visual perspective. | **Supported** | Sufficient for descriptive detection evaluation, subject to left-censoring adjustments. |
| **No-train false-alarm rate evaluation** | Only 3 no-train events exist in the cohort ($N=3$). | **Partially Supported (Severe Limitation)** | Cannot establish a low false-alarm rate; confidence interval upper bound is 56%. Must be disclosed as exploratory. |
| **Premature-opening evaluation (M4/M5)** | Tail clearance ($T_4$) is observable in 22 of 23 train events. | **Supported (Pending Approved GT)** | Well-supported once human ground truth verifies physical tail clearance boundaries. |
| **Missed-train rate (MTR)** | 18 events are left-censored; feasibility screen screens out events with $< 3.6\,\text{s}$ lead-in. | **Supported (with Feasibility Screen)** | Must apply `lead_in_screen.py` to avoid penalizing system for recording cutoffs. |
| **Dual-camera cross-stream comparison** | Back-stream calibration supported for only 11 events. | **Exploratory Only ($N=11$)** | Cannot be generalized to full cohort; restricted subset reporting mandatory. |
| **Weather robustness claims (Rain/Fog)** | Zero rain or fog events exist in the dataset. | **UNSUPPORTED** | No empirical data exists to support weather robustness claims. Must be removed from paper. |
| **Night performance claims** | Negligible low-light sample size. | **UNSUPPORTED** | Insufficient sample size for night performance claims. |
| **General railway crossing safety certification (SIL)** | Single crossing in Bangladesh, 27 events, zero independent site testing. | **UNSUPPORTED** | Scientific fraud to claim operational safety certification or cross-site validity. |

---

## 7. Audit Conclusion

The dataset is a valuable but strictly limited exploratory research corpus. It can validly support a descriptive offline benchmark of front-camera multimodal architectures on 27 events, provided all claims of general safety, weather robustness, and full-cohort dual-camera fusion are rigorously excluded.

**Dataset Integrity Audit Status: AUDITED — SEVERE METHODOLOGICAL LIMITATIONS IDENTIFIED.**
