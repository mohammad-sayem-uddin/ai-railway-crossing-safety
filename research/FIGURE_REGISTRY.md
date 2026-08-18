# Research Figure & Visualization Registry

**Document Version:** 1.0.0  
**Authority:** AI Railway Crossing Safety Research Project  
**Repository:** `ai-railway-crossing-safety`  
**Privacy Compliance:** Strictly omits raw dataset image quantities, class instance totals, and split partition sample sizes.

This registry indexes all research figures, diagrams, and empirical artifacts prepared for publication.

---

## Registry Index

| Figure ID | File Basename | Figure Title / Description | Category | Empirical Data Source | Generation Script |
|:---|:---|:---|:---:|:---|:---|
| **FIGURE 01** | `fig01_system_architecture` | Multimodal AI Railway Crossing Safety Architecture | Conceptual Architecture | Research Protocol Specification | [`generate_architecture_diagrams.py`](file:///Users/sayemuddin/Desktop/Train_automation/research/scripts/generate_architecture_diagrams.py) |
| **FIGURE 02** | `fig02_vision_pipeline` | Frame-by-Frame Neural Vision & Temporal Buffer Pipeline | Conceptual Pipeline | Neural Vision Architecture | [`generate_architecture_diagrams.py`](file:///Users/sayemuddin/Desktop/Train_automation/research/scripts/generate_architecture_diagrams.py) |
| **FIGURE 03** | `fig03_twocamera_crossing_concept` | Two-Camera Dual-Zone Railway Crossing Layout | Conceptual Architecture | Trackside Geometry Specification | [`generate_architecture_diagrams.py`](file:///Users/sayemuddin/Desktop/Train_automation/research/scripts/generate_architecture_diagrams.py) |
| **FIGURE 04** | `fig04_multiframe_confirmation` | Multi-Frame Confirmation & Noise Suppression Logic | Conceptual Dynamics | Temporal Evidence Algorithm ($N=3$) | [`generate_temporal_diagrams.py`](file:///Users/sayemuddin/Desktop/Train_automation/research/scripts/generate_temporal_diagrams.py) |
| **FIGURE 05** | `fig05_evidence_persistence` | Temporal Evidence Persistence & Dropout Recovery | Conceptual Simulation | Buffer Filter Dynamics | [`generate_temporal_diagrams.py`](file:///Users/sayemuddin/Desktop/Train_automation/research/scripts/generate_temporal_diagrams.py) |
| **FIGURE 06** | `fig06_gate_safety_state_machine` | Railway Crossing Gate Safety State Machine | Formal State Machine | Safety-First Decision Logic | [`generate_state_machine_diagram.py`](file:///Users/sayemuddin/Desktop/Train_automation/research/scripts/generate_state_machine_diagram.py) |
| **FIGURE 07** | `fig07_training_loss_curves` | Training & Validation Box/Class Loss Curves | **Real Empirical Data** | `experiments/vision/39f402dfe460/checkpoints/results.csv` | [`generate_training_figures.py`](file:///Users/sayemuddin/Desktop/Train_automation/research/scripts/generate_training_figures.py) |
| **FIGURE 08** | `fig08_model_performance_curves` | Model Performance Trajectory (Precision, Recall, mAP) | **Real Empirical Data** | `experiments/vision/39f402dfe460/checkpoints/results.csv` | [`generate_training_figures.py`](file:///Users/sayemuddin/Desktop/Train_automation/research/scripts/generate_training_figures.py) |
| **FIGURE 09** | `fig09_confusion_matrix_normalized` | Normalized Viewpoint Confusion Matrix | **Real Empirical Data** | `experiments/vision/39f402dfe460/evaluation/metrics.json` | [`generate_evaluation_figures.py`](file:///Users/sayemuddin/Desktop/Train_automation/research/scripts/generate_evaluation_figures.py) |
| **FIGURE 10** | `fig10_precision_recall_curves` | Precision-Recall Curves per Viewpoint Class | **Real Empirical Data** | `experiments/vision/39f402dfe460/evaluation/metrics.json` | [`generate_evaluation_figures.py`](file:///Users/sayemuddin/Desktop/Train_automation/research/scripts/generate_evaluation_figures.py) |
| **FIGURE 11** | `fig11_per_class_metrics_comparison` | Per-Class Performance Comparison (P, R, AP@50) | **Real Empirical Data** | `experiments/vision/39f402dfe460/evaluation/metrics.json` | [`generate_evaluation_figures.py`](file:///Users/sayemuddin/Desktop/Train_automation/research/scripts/generate_evaluation_figures.py) |
| **FIGURE 12** | `fig12_confidence_f1_analysis` | F1-Score vs Confidence Threshold Operating Curves | **Real Empirical Data** | `experiments/vision/39f402dfe460/evaluation/metrics.json` | [`generate_evaluation_figures.py`](file:///Users/sayemuddin/Desktop/Train_automation/research/scripts/generate_evaluation_figures.py) |
| **FIGURE 13** | `fig13_failure_category_distribution` | Diagnostic Failure Mode Relative Distribution (%) | **Real Empirical Data** | `experiments/vision/39f402dfe460/evaluation/failure_analysis.json` | [`generate_failure_figures.py`](file:///Users/sayemuddin/Desktop/Train_automation/research/scripts/generate_failure_figures.py) |
| **FIGURE 14** | `fig14_qualitative_detections` | Qualitative Detection Panels (FRONT, SIDE, REAR) | **Real Empirical Inference** | Model `best.pt` on Test Frames | [`generate_qualitative_figures.py`](file:///Users/sayemuddin/Desktop/Train_automation/research/scripts/generate_qualitative_figures.py) |
| **FIGURE 15** | `fig15_failure_examples` | Qualitative Boundary & Failure Examples | **Real Empirical Inference** | Model `best.pt` on Test Frames | [`generate_qualitative_figures.py`](file:///Users/sayemuddin/Desktop/Train_automation/research/scripts/generate_qualitative_figures.py) |
| **FIGURE 16** | `fig16_video_progression_sequence` | Temporal Passage Progression (Approach $\to$ Passage $\to$ Departure) | **Real Empirical Inference** | Test Video Stream / Sequential Frames | [`generate_video_progression_figure.py`](file:///Users/sayemuddin/Desktop/Train_automation/research/scripts/generate_video_progression_figure.py) |
| **FIGURE 17** | `fig17_ablation_comparison` | Multi-System Ablation Safety Evaluation | *Future Experiment Placeholder* | `research/templates/ablation_template.csv` | [`generate_ablation_figures.py`](file:///Users/sayemuddin/Desktop/Train_automation/research/scripts/generate_ablation_figures.py) |
| **FIGURE 18** | `fig18_roc_auc_curves` | Receiver Operating Characteristic (ROC) & AUC Curves | **Real Empirical Data** | `experiments/vision/39f402dfe460/evaluation/metrics.json` | [`generate_evaluation_figures.py`](file:///Users/sayemuddin/Desktop/Train_automation/research/scripts/generate_evaluation_figures.py) |

---

## Categorization Breakdown

1. **Empirical Results (8 Figures):** Figures 7, 8, 9, 10, 11, 12, 13, 18
2. **Empirical Qualitative Inference (3 Figures):** Figures 14, 15, 16
3. **Conceptual Architecture & System Logic (6 Figures):** Figures 1, 2, 3, 4, 5, 6
4. **Future Experiment Placeholders (1 Figure / Template):** Figure 17
