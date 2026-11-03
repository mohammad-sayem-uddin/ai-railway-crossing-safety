# MISSION 17B: EVENT-GROUPED COMPUTER-VISION SPLIT DESIGN

**Project:** Train Gate Automation — Bangladesh
**Subsystem:** Computer Vision Data Partitioning & Leakage Prevention
**Target Architecture:** Stratified Event-Grouped Cross-Validation (Stratified GroupKFold)
**Document ID:** `MISSION-17B-DELIV-03`
**Execution Authority:** NONE (Implementation Pending PI Approval of Decision D-07) **17C-0: corrected requirements are in the appended correction history; original body retained.**
**Governance Invariants:** RD-006, RD-024, RD-025, RD-032, RD-033, RD-037
**Audited Sources:** [`split_summary.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/splits/705d388743ea/split_summary.json), [`split.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/data/split.py), [`test_split.py`](file:///Users/sayemuddin/Desktop/Train_automation/tests/unit/test_split.py), Missions 16E, 16F, 17A
**Date:** 2026-11-03

---

## 1. Executive Summary & Defect Statement

This document specifies a scientifically defensible, leakage-resistant dataset partitioning methodology for the computer-vision object detection pipeline (YOLOv8).

### 1.1 The Historical Split Defect (`705d388743ea`)
Inspection of [`data/splits/705d388743ea/split_summary.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/splits/705d388743ea/split_summary.json) revealed critical leakage flags:
```json
{
  "split_id": "705d388743ea",
  "split_type": "development_fallback",
  "leakage_risk": true,
  "group_field": "crossing_id",
  "require_grouping": true,
  "allow_ungrouped_fallback": true
}
```

### 1.2 Root Cause of Historical Leakage
1. **Single-Site Data Collection:** All 27 recorded events were captured at a single geographic level crossing in Bangladesh.
2. **Flawed Grouping Key:** Setting `group_field: "crossing_id"` caused all samples to belong to the exact same group (`crossing_id = 1`). Under strict group disjointness, 100% of samples would be assigned to a single partition, making train/val/test splitting impossible.
3. **Silent Fallback to Per-Image Splitting:** To avoid an empty split error, [`split.py:100-112`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/data/split.py#L100-L112) enabled `allow_ungrouped_fallback: true`, which randomly distributed individual video frames across train, validation, and test sets.
4. **Severe Temporal Data Leakage:** Because consecutive video frames (sampled at 5.0 Hz or extracted from video) are separated by fractions of a second, nearly identical images appeared simultaneously in training and test sets.
5. **Diagnostic Qualification:** Consequently, historical YOLO test metrics ($mAP_{50} = 0.98$) reflect model memorization of near-duplicate frames rather than true out-of-sample physical generalization. All historical YOLO metrics must remain strictly classified as **preliminary and diagnostic only**.

---

## 2. Event-Grouped Partitioning Architecture

To eliminate temporal and visual data leakage, data partitioning must be grouped strictly by **physical passage event** (`event_id`), not by geographic site (`crossing_id`) or individual video frame.

```
┌────────────────────────────────────────────────────────────────────────┐
│                   27 Physical Level-Crossing Events                    │
├───────────────────────┬────────────────────────┬───────────────────────┤
│ 23 Full Train Passes  │  3 No-Train Controls   │  1 Engine-Only Pass   │
│ (event_001..event_027)│ (event_003, 009, 016)  │     (event_021)       │
└───────────┬───────────┴───────────┬────────────┴───────────┬───────────┘
            │                       │                        │
            ▼                       ▼                        ▼
┌───────────────────────┐┌───────────────────────┐┌───────────────────────┐
│ Stratified GroupKFold ││ Negative Calibration  ││ Case Study Evaluation │
│ (5 Folds: Train/Val)  ││ (False-Alarm Screen)  ││ (Zero-Shot Generaliz.)│
│ Strict Event Isolation││ (RD-025 Governance)   ││ (RD-024 Governance)   │
└───────────────────────┘└───────────────────────┘└───────────────────────┘
```

### 2.1 Grouping Key Specification
- **Primary Group Key:** `event_id` (e.g., `event_001`, `event_002`, ..., `event_027`).
- **Strict Disjointness Constraint:**
  $$\mathcal{E}_{\text{train}} \cap \mathcal{E}_{\text{val}} \cap \mathcal{E}_{\text{test}} = \emptyset$$
  Every single frame, bounding box, crop, and feature derived from `event_i` must reside exclusively within exactly one partition.
- **Zero Fallback Invariant:**
  `allow_ungrouped_fallback: false` must be enforced fail-closed. If an image lacks an associated `event_id`, partition generation must halt with an error.

### 2.2 Stratification Strategy & Strata Definition
The 27 events must be stratified across key environmental and physical operational attributes to ensure balanced representation across folds:

1. **Weather Stratum:**
   - Clear / Sunny
   - Overcast / Rain / Wet lens
   - Low Visibility / Fog
2. **Lighting / Diurnal Stratum:**
   - Daylight (High illumination, sharp shadows)
   - Dusk / Dawn (Low ambient light, high contrast)
   - Night (Artificial illumination, glare, headlight bloom)
3. **Train Direction & Speed Stratum:**
   - Towards camera (expanding bounding box)
   - Away from camera (receding bounding box)
   - Low speed / High speed

---

## 3. Small-Sample Limitations & Rare-Class Governance

With only 27 recorded events, standard 5-fold cross-validation presents mathematical constraints that must be handled with scientific integrity:

### 3.1 Rare-Class Constraints
- **Engine-Only Pass (`event_021`):** Exactly 1 event in the entire repository represents an isolated locomotive pass without passenger/freight cars.
  - *Constraint:* A singleton class cannot be distributed across 5 folds without introducing severe fold imbalance.
  - *Governance Rule (RD-024):* `event_021` must be **excluded from training folds** and reserved as an independent **Generalization Case Study** evaluating out-of-distribution model robustness.
- **No-Train Negative Controls (`event_003`, `event_009`, `event_016`):** Exactly 3 events capture road traffic, pedestrians, and animals with zero train presence.
  - *Constraint:* 3 events cannot be split equally across 5 folds.
  - *Governance Rule (RD-025):* Negative control events must be evaluated specifically for false-alarm rate (FAR per exposure hour) rather than mixed into standard precision-recall curves.

### 3.2 5-Fold Partition Sizing
For the remaining 23 full-train passage events:
- 5 folds will contain approximately 4 to 5 events each.
- In each cross-validation iteration:
  - **Training Partition (4 folds):** $\approx 18\text{--}19$ events ($\approx 80\%$).
  - **Validation / Hold-Out Partition (1 fold):** $\approx 4\text{--}5$ events ($\approx 20\%$).
- Out-of-fold predictions will provide a truly leakage-safe estimate of object detection generalization.

---

## 4. Proposed Split Manifest Schema (`cv-event-grouped-split/1.0`)

The proposed split manifest defines the exact data contract for future partition generation:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "CVEventGroupedSplitManifest",
  "version": "1.0.0",
  "split_id": "b4_cv_stratified_kfold_v1",
  "generated_at_utc": "2026-11-03T00:00:00Z",
  "algorithm": "StratifiedGroupKFold",
  "random_seed": 42,
  "group_field": "event_id",
  "leakage_risk": false,
  "allow_ungrouped_fallback": false,
  "summary_metrics": {
    "total_events": 27,
    "training_eligible_events": 23,
    "reserved_negative_controls": 3,
    "reserved_case_studies": 1,
    "num_folds": 5
  },
  "folds": [
    {
      "fold_index": 0,
      "train_events": ["event_001", "event_004", "event_006", "..."],
      "val_events": ["event_002", "event_005", "event_011", "..."],
      "train_image_count": 1840,
      "val_image_count": 460,
      "weather_distribution": {
        "train": {"clear": 12, "rain": 4, "fog": 2},
        "val": {"clear": 3, "rain": 1, "fog": 1}
      }
    }
  ],
  "reserved_events": {
    "negative_controls": ["event_003", "event_009", "event_016"],
    "engine_only_case_study": ["event_021"]
  },
  "hash_bindings": {
    "source_manifest_sha256": "4b8f...",
    "manifest_self_sha256": "c71a..."
  }
}
```

---

## 5. Algorithmic Specification: Stratified Event Splitter

The following algorithm specifies the partition generation procedure to be implemented in `src/railway_detection/data/grouped_split.py`:

```python
"""Stratified event-grouped CV split generator specification."""

from typing import List, Dict, Any
import hashlib
import numpy as np


class EventGroupedSplitter:
    """Generates leakage-safe cross-validation folds grouped by event_id."""

    def __init__(
        self,
        num_folds: int = 5,
        seed: int = 42,
        group_field: str = "event_id",
        allow_ungrouped_fallback: bool = False,
    ):
        self.num_folds = num_folds
        self.seed = seed
        self.group_field = group_field
        self.allow_ungrouped_fallback = allow_ungrouped_fallback

    def generate_splits(
        self,
        event_metadata: List[Dict[str, Any]],
        image_annotations: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        # Step 1: Enforce fail-closed check on ungrouped images
        for img in image_annotations:
            if self.group_field not in img or not img[self.group_field]:
                if not self.allow_ungrouped_fallback:
                    raise ValueError(
                        f"LEAKAGE_GUARD_VIOLATION: Image {img.get('id')} has no {self.group_field}!"
                    )

        # Step 2: Separate reserved events per RD-024 and RD-025
        trainable_events = []
        negative_controls = []
        engine_only = []

        for ev in event_metadata:
            eid = ev["event_id"]
            if eid == "event_021":
                engine_only.append(eid)
            elif ev.get("event_type") == "no_train" or eid in ("event_003", "event_009", "event_016"):
                negative_controls.append(eid)
            else:
                trainable_events.append(ev)

        # Step 3: Stratified Group assignment on trainable events
        strata_labels = [
            f"{e['weather']}_{e['lighting']}_{e['direction']}"
            for e in trainable_events
        ]

        # Sort deterministically before shuffling
        sorted_events = sorted(trainable_events, key=lambda x: x["event_id"])
        rng = np.random.RandomState(self.seed)

        # Allocate events to folds balancing strata
        folds = [[] for _ in range(self.num_folds)]
        # (Stratified bin allocation logic mapping event_ids to fold indices)
        ...

        # Step 4: Strict Disjointness Verification
        self.verify_zero_leakage(folds, image_annotations)

        return self.build_manifest(folds, negative_controls, engine_only)

    def verify_zero_leakage(self, folds: List[List[str]], annotations: List[Dict[str, Any]]) -> None:
        """Verify absolute pairwise disjointness across all folds."""
        for i in range(len(folds)):
            for j in range(i + 1, len(folds)):
                set_i = set(folds[i])
                set_j = set(folds[j])
                overlap = set_i.intersection(set_j)
                if overlap:
                    raise RuntimeError(f"DATASET_LEAKAGE_ERROR: Folds {i} and {j} share events: {overlap}")
```

---

## 6. Comprehensive Synthetic Validation Test Plan

Before running model retraining, the split generator must pass the following synthetic validation test matrix:

| Test ID | Test Name | Synthetic Dataset Setup | Expected Outcome | Failure Condition |
| :---: | :--- | :--- | :--- | :--- |
| **TEST-SPLIT-01** | `test_zero_event_overlap` | 23 synthetic events, 500 images; generate 5 folds. | Pairwise intersection of event sets across all folds is strictly empty ($\emptyset$). | Any shared `event_id` between train and val. |
| **TEST-SPLIT-02** | `test_deterministic_reproducibility` | Run split generator twice with identical `seed=42`. | Partition assignments and hashes match $100\%$ bit-for-bit. | Any variance in fold assignment across identical runs. |
| **TEST-SPLIT-03** | `test_ungrouped_fallback_rejection` | Insert 5 synthetic images lacking `event_id`. | Generator raises `LEAKAGE_GUARD_VIOLATION` and halts immediately. | Images assigned pseudo-randomly; warning ignored. |
| **TEST-SPLIT-04** | `test_reserved_engine_only_isolation` | Include synthetic `event_021` (engine pass). | `event_021` assigned to `reserved_case_study`; present in 0 training folds. | `event_021` appears in any training fold. |
| **TEST-SPLIT-05** | `test_reserved_negative_control_isolation` | Include synthetic `event_003`, `event_009`, `event_016`. | Events assigned to `reserved_negative_controls`; evaluated for false alarms only. | Negative controls mixed into PR training sets. |
| **TEST-SPLIT-06** | `test_strata_distribution_balance` | Synthetic events with 3 weather types (clear, rain, fog). | Each fold contains at least 1 event of each weather stratum where available. | Clumping of all rain events into a single fold. |
| **TEST-SPLIT-07** | `test_duplicate_image_hash_leakage` | Inject identical synthetic image hashes into two different events. | Split validator detects cross-event duplicate image hash and flags warning. | Silent acceptance of duplicate raw frames. |
| **TEST-SPLIT-08** | `test_manifest_schema_compliance` | Generate partition manifest JSON. | Manifest passes 100% schema validation against `cv-event-grouped-split/1.0`. | Missing schema keys or malformed structure. |

---

## 7. Acceptance Criteria for Future CV Implementation

The future CV partitioning workflow must satisfy:
1. `split_summary.json` reports `leakage_risk: false` and `allow_ungrouped_fallback: false`.
2. Group field is verified to be `event_id`.
3. 5-fold cross-validation is conducted on out-of-fold event evaluation.
4. Historical YOLO development metrics are preserved as preliminary; new event-grouped metrics are reported with standard deviation across folds ($\mu \pm \sigma$).

---
*End of Mission 17B Deliverable 3.*

---

## Mission 17C-0 correction history — superseding split requirements

**2026-11-03; documentation correction only; D-07 remains PENDING.** Original §§1–7 are retained as historical wording. This appendix supersedes their conflicting corpus/ID claims, pseudocode, equations, schema and test expectations. Evidence: `MISSION_17C0_VERIFICATION_MATRIX.md` C034–C045; F05–F10. No real split manifest, training or evaluation is authorized or generated.

### Correct corpus and leakage evidence

- Split 705d388743ea concerns3,157 V1 Roboflow development images. The preserved summary contains 1,315 `source:*` group assignments, partitions2218/467/472 and no warnings; the `crossing_id` label does not prove that grouping collapsed to one crossing group. `generate_group_split` uses each sample's `split_group_id`, not lookup of the group_field string. Grouping hints are source-image names with augmentation suffixes removed.
- `leakage_risk:true`, `development_fallback` and `allow_ungrouped_fallback:true` are real summary fields. They qualify scientific claims but do not prove per-image random fallback actually occurred, shared physical-event frame leakage, duplicate content or model memorization. Metadata source-name inspection finds zero cross-partition identical source hints. This is not proof of event independence or absence of near-duplicates; raw images were not inspected/hashed.
- Historical artifact `experiments/vision/39f402dfe460/evaluation/metrics.json` records mAP50=.9946. The original .98 quotation has no identified matching source here. Report historical diagnostic provenance only; no metric is re-evaluated or certified.
- The27-event LayerB v2 video corpus is a separate descriptive evaluation cohort, not an established training source for these V1 images. No verified image-to-physical-event join was located. Do not construct a CV dataset from held-out evaluation footage, infer event IDs from file-name numerals, or treat this document as approval to change RD-039's full-cohort evaluation design.

### Cohort identity and grouping invariants

- Canonical identities are `train_events/event_001` through `train_events/event_023`, `no_train_events/event_001` through `no_train_events/event_003`, and `engine_events/event_001`. In particular, train_events/event_021 is not the engine and train_events/event_003/009/016 are not no-train controls.
- Bare event ID is not globally unique. Define an approved development physical-event key with source-dataset/version/cohort provenance; multiple camera views, segments, re-exports, crops and augmented derivatives of the same physical recording/pass must share a group. The engine's versions/historical duplicate must not become independent groups. Larger session/duplicate-lineage connected components may be required where the same physical event is represented more than once.
- For each outer fold require pairwise train∩validation=empty, train∩test=empty, validation∩test=empty where these roles exist. Empty triple intersection is insufficient. Across outer validation folds require pairwise group disjointness and exactly-once coverage of every eligible group. Training sets naturally overlap across CV iterations; do not require all folds' training sets to be mutually disjoint.
- **No ungrouped random fallback under any flag.** Reject construction/configuration with fallback=True. Reject absent/blank/unknown/ambiguous group identities, inconsistent cohort/type joins, orphan annotations, duplicate IDs with conflicting provenance, missing eligible coverage and cross-role derivative leakage. Fold-event disjointness alone cannot validate image assignments; verify the complete source-image/annotation/derivative-to-group join.
- Use already authorized metadata/content fingerprints if available. A prohibited media hash is not required or performed by this audit; absence of trustworthy identity must block claims of verified identity. Cross-event exact duplicates or unresolved same-source lineage must block certified splitting or be merged into an approved common group; a warning alone cannot establish leakage safety.
- RD-024 excludes engine-only events from pooled M4/M5/occupancy/train aggregates. It does not by itself mandate a detector-training prohibition or establish zero-shot out-of-distribution evaluation. Any reserved-case-study/training policy needs an explicit corpus-specific PI decision. RD-025 requires confirmed no-train status and event/exposure reporting, not an hourly-rate or training approval.

### Feasible cross-validation, calibration and reporting

- Five folds are a proposal.23 verified eligible physical groups could have validation sizes5,5,5,4,4 (training18/19), but23 is not established as the development corpus's number of groups. No complete weather/lighting/direction labels were found in the available V1 summary; none of those keys exists at top level of the 27-event inventory. Speed strata are also not established. Unknown/unverified metadata must remain unknown.
- For a required joint stratum to appear in every validation fold, at least K distinct eligible groups must carry that stratum; this is a necessary count condition, not general proof of feasible balanced bin packing with mixed labels/unequal frames. Singleton engine or three controls cannot cover five folds. Do not assert environmental coverage that data do not support. Publish counts and constraints before choosing K; if infeasible, stop for PI choice of fewer folds/coarser strata or a different grouped design. Group disjointness is never relaxed.
- Build aligned group/label records in one deterministic sort before labeling/allocation. Specify actual deterministic allocation, tie breaking, frame/group weighting objective and library/version; the ellipsis in the original algorithm is not an implemented StratifiedGroupKFold procedure. Model-class balance and nuisance environmental stratification are different objectives. Check label support and actual output invariants even when using a library.
- Negative controls cannot be both tuned-on calibration material and independent evaluation controls. Choose disjoint calibration/development and held-out control roles prospectively; reuse must be disclosed as exploratory. Three short control recordings do not justify FAR/hour or a permanent train-free claim. Keep event counts, blocked seconds, episodes and per-camera exposure under the adopted profile.
- Outer-fold validation/evaluation must not select thresholds, early stopping, hyperparameters or model checkpoints. Use group-disjoint inner validation or a prospectively frozen tuning rule; fit preprocessing only on training data. Record fresh-training/initialization provenance and any prior exposure of pretrained models to held-out groups. A valid partition cannot undo historical training exposure.
- Event grouping limits direct event leakage; same-session/site background still limits independence. Report within-site descriptive performance and denominators, not cross-site generalization. Fold mean/SD and pooled OOF metrics answer different aggregation questions; define weighting and never call SD a confidence interval or inferential validation under RD-023.

### Manifest contract and corrected verification requirements

- Original §4 is an illustrative JSON instance, not a validating JSON Schema. Its timestamps/counts/hashes/folds are placeholders, not actual results. No `leakage_risk:false` declaration proves leakage absence. Build an actual typed/required-key schema before implementation acceptance.
- Manifest requirements: approved corpus and version; physical-group mapping/derivative lineage; source/label/eligibility/metadata/code/config digests; approved operation and decision references; algorithm/library version, deterministic tie break and seed; stable sorted assignments; train/inner-validation/outer-test roles; all image/annotation/group counts; class and nuisance-stratum distributions including unknown; reserved/calibration roles and exclusion reasons; pairwise/coverage/join verification receipts; limitations and prior model exposure.
- Define canonical serialization and self hash over the payload excluding the self-hash field (and explicitly defined nondeterministic receipt fields), or use a detached digest. Keep deterministic assignment content separate from generated-time receipt so reproducibility assertions are meaningful. Full 64-hex digests only; no fabricated hash or generation time.
- TEST-SPLIT06 may demand a stratum in every fold only after group-count feasibility is proven. TEST-SPLIT07 must fail closed on unresolved cross-group duplicate identity; no claim of duplicate checking from a warning-only stub. Add fallback=True rejection, unknown/cohort-colliding IDs, missing coverage, orphan annotations, camera/version derivatives, rare joint strata, input-order permutation, calibration reuse and inner/outer leakage checks. Eight proposed cases are not eight executed tests.
