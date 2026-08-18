# Research Visualization & Empirical Artifact System

**Document Version:** 1.0.0  
**Authority:** AI Railway Crossing Safety Research Project  
**Repository:** `ai-railway-crossing-safety`  
**Compliance Standard:** Strictly omits raw dataset image quantities, instance totals, and partition sample sizes.

---

## 1. Directory Structure

```text
research/
├── figures/
│   ├── architecture/        # System and optical pipeline block diagrams (Figs 1–3)
│   ├── training/            # Real training and validation convergence curves (Figs 7–8)
│   ├── evaluation/          # Empirical metrics, confusion matrix, PR curves, failure distribution (Figs 9–13)
│   ├── temporal/            # Temporal multi-frame confirmation & persistence dynamics (Figs 4–5)
│   ├── system/              # Railway gate safety state machine & decision logic (Fig 6)
│   └── qualitative/         # Qualitative detection panels & temporal video progression (Figs 14–16)
│       └── failures/        # Qualitative failure mode & edge-case panels (Fig 15)
│
├── scripts/                 # Standalone, reproducible figure generation scripts
│   ├── generate_all_figures.py
│   ├── generate_architecture_diagrams.py
│   ├── generate_temporal_diagrams.py
│   ├── generate_state_machine_diagram.py
│   ├── generate_training_figures.py
│   ├── generate_evaluation_figures.py
│   ├── generate_failure_figures.py
│   ├── generate_qualitative_figures.py
│   ├── generate_video_progression_figure.py
│   └── generate_ablation_figures.py
│
├── templates/               # Reusable ablation and experiment templates
│   └── ablation_template.csv
│
├── FIGURE_REGISTRY.md       # Master registry and metadata for all paper figures
└── README.md                # System documentation and usage guidelines
```

---

## 2. Master Generation Command

To regenerate the entire suite of publication figures in one deterministic pass:

```bash
python research/scripts/generate_all_figures.py
```

All figures are automatically exported in dual formats:
- **PNG:** High-resolution raster format ($\ge 300\text{ DPI}$) for draft compilation.
- **SVG & PDF:** Vector formats for publication quality.

---

## 3. Figure Classification & Data Sources

### A. Empirical Experimental Figures (Real Data Only)
These figures are generated directly from verified baseline training logs and held-out evaluation outputs:

- **Figure 7 (`fig07_training_loss_curves`):** Bounding box regression loss and viewpoint classification loss across training epochs from `experiments/vision/39f402dfe460/checkpoints/results.csv`.
- **Figure 8 (`fig08_model_performance_curves`):** Trajectory of Precision, Recall, mAP@50, and mAP@50:95 across training epochs from `results.csv`.
- **Figure 9 (`fig09_confusion_matrix_normalized`):** Row-normalized confusion matrix (0.0–1.0 detection rates) from `experiments/vision/39f402dfe460/evaluation/metrics.json`.
- **Figure 10 (`fig10_precision_recall_curves`):** Precision-Recall curves for `FRONT`, `REAR`, and `SIDE` viewpoint classes from `metrics.json`.
- **Figure 11 (`fig11_per_class_metrics_comparison`):** Grouped bar chart comparing Precision, Recall, and AP@50 across classes from `metrics.json`.
- **Figure 12 (`fig12_confidence_f1_analysis`):** Operating characteristic curves relating confidence thresholds to F1 scores and optimal operating points from `metrics.json`.
- **Figure 13 (`fig13_failure_category_distribution`):** Relative percentage breakdown of observed failure modes from `experiments/vision/39f402dfe460/evaluation/failure_analysis.json`.
- **Figure 14 (`fig14_qualitative_detections`):** 2×3 annotated detection grid on representative test frames using trained weights `best.pt`.
- **Figure 15 (`fig15_failure_examples`):** Visual diagnostic examples of low-confidence approach and trackside clutter false alarms.
- **Figure 16 (`fig16_video_progression_sequence`):** Multi-frame progression sequence illustrating transitions across detection zones (Approach $\to$ Passage $\to$ Departure).
- **Figure 18 (`fig18_roc_auc_curves`):** Receiver Operating Characteristic (ROC) curves and Area Under Curve (AUC) scores per class and macro-average from `metrics.json`.

### B. Conceptual Architecture & Logic Diagrams
These figures define the theoretical system architecture, sensor layouts, and formal decision mechanisms:

- **Figure 1 (`fig01_system_architecture`):** Multimodal system block diagram combining optical detection, acoustic horn evidence, and central decision logic.
- **Figure 2 (`fig02_vision_pipeline`):** Sequential frame extraction, neural detection, and temporal evidence buffering pipeline.
- **Figure 3 (`fig03_twocamera_crossing_concept`):** Spatial layout of upstream approach (Camera 1) and downstream clearance (Camera 2) monitoring zones.
- **Figure 4 (`fig04_multiframe_confirmation`):** Conceptual multi-frame confirmation logic distinguishing persistent signals from single-frame noise glitches.
- **Figure 5 (`fig05_evidence_persistence`):** Dynamic simulation illustrating persistence bridging temporary occlusions and graceful evidence decay.
- **Figure 6 (`fig06_gate_safety_state_machine`):** Formal 8-state gate control state machine implementing the core safety invariant.

### C. Future Experiment Placeholders
- **Figure 17 (`fig17_ablation_comparison`):** Multi-system ablation comparison framework (`B0`–`B4`). When future experimental benchmarks are logged into `research/templates/ablation_template.csv`, running `generate_ablation_figures.py` automatically produces the comparison chart without fabricated numbers.

---

## 4. Individual Script Execution

| Task | Command | Output Files |
|:---|:---|:---|
| Architecture Figures | `python research/scripts/generate_architecture_diagrams.py` | `fig01`, `fig02`, `fig03` |
| Temporal Logic Figures | `python research/scripts/generate_temporal_diagrams.py` | `fig04`, `fig05` |
| Gate State Machine | `python research/scripts/generate_state_machine_diagram.py` | `fig06` |
| Training Curves | `python research/scripts/generate_training_figures.py` | `fig07`, `fig08` |
| Evaluation Metrics | `python research/scripts/generate_evaluation_figures.py` | `fig09`, `fig10`, `fig11`, `fig12` |
| Failure Mode Distribution | `python research/scripts/generate_failure_figures.py` | `fig13` |
| Qualitative Visual Panels | `python research/scripts/generate_qualitative_figures.py` | `fig14`, `fig15` |
| Video Temporal Sequence | `python research/scripts/generate_video_progression_figure.py` | `fig16` |
| Ablation Study Processing | `python research/scripts/generate_ablation_figures.py` | `fig17` (when populated) |

---

## 5. Academic Presentation & Integrity Rules
1. **Zero Dataset Quantity Exposure:** No raw image counts, bounding box totals, or partition sizes are displayed in labels, axes, or annotations.
2. **Strict Empirical Honesty:** No imaginary curves or fabricated metrics are used. All quantitative plots map strictly to verified experiment run `39f402dfe460`.
3. **Explicit Conceptual Distinction:** Conceptual diagrams and theoretical simulations are clearly demarcated from empirical evaluations.
