"""Master Research Figure & Artifact Generator.

Executes all publication figure generation scripts in a single deterministic pass.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from research.scripts.generate_ablation_figures import generate_ablation_figures  # noqa: E402
from research.scripts.generate_architecture_diagrams import (  # noqa: E402
    generate_figure_01_system_architecture,
    generate_figure_02_vision_pipeline,
    generate_figure_03_twocamera_crossing_concept,
)
from research.scripts.generate_evaluation_figures import (  # noqa: E402
    generate_figure_09_normalized_confusion_matrix,
    generate_figure_10_precision_recall_curves,
    generate_figure_11_per_class_metrics_comparison,
    generate_figure_12_confidence_f1_analysis,
    load_evaluation_metrics,
)
from research.scripts.generate_failure_figures import (  # noqa: E402
    generate_figure_13_failure_distribution,
)
from research.scripts.generate_qualitative_figures import (  # noqa: E402
    generate_figure_14_qualitative_detections,
    generate_figure_15_failure_examples,
)
from research.scripts.generate_state_machine_diagram import (  # noqa: E402
    generate_figure_06_gate_safety_state_machine,
)
from research.scripts.generate_temporal_diagrams import (  # noqa: E402
    generate_figure_04_multiframe_confirmation,
    generate_figure_05_evidence_persistence,
)
from research.scripts.generate_training_figures import (  # noqa: E402
    generate_figure_07_training_loss_curves,
    generate_figure_08_model_performance_curves,
    load_training_data,
)
from research.scripts.generate_video_progression_figure import (  # noqa: E402
    generate_video_progression_figure,
)


def main() -> None:
    print("=" * 65)
    print("AI RAILWAY CROSSING SAFETY — RESEARCH VISUALIZATION GENERATOR")
    print("=" * 65)

    # 1. Architecture Diagrams
    print("\n[1/8] Generating System Architecture Diagrams...")
    generate_figure_01_system_architecture()
    generate_figure_02_vision_pipeline()
    generate_figure_03_twocamera_crossing_concept()

    # 2. Temporal Logic Diagrams
    print("\n[2/8] Generating Temporal Evidence & Logic Diagrams...")
    generate_figure_04_multiframe_confirmation()
    generate_figure_05_evidence_persistence()

    # 3. State Machine Diagram
    print("\n[3/8] Generating Safety State Machine Diagram...")
    generate_figure_06_gate_safety_state_machine()

    # 4. Training Visualizations
    print("\n[4/8] Generating Training Curves from Real Logs...")
    train_data = load_training_data()
    generate_figure_07_training_loss_curves(train_data)
    generate_figure_08_model_performance_curves(train_data)

    # 5. Evaluation Visualizations
    print("\n[5/8] Generating Evaluation Figures from Held-Out Test Metrics...")
    metrics = load_evaluation_metrics()
    generate_figure_09_normalized_confusion_matrix(metrics)
    generate_figure_10_precision_recall_curves(metrics)
    generate_figure_11_per_class_metrics_comparison(metrics)
    generate_figure_12_confidence_f1_analysis(metrics)

    # 6. Failure Analysis Visualization
    print("\n[6/8] Generating Failure Mode Distribution...")
    generate_figure_13_failure_distribution()

    # 7. Qualitative Examples & Video Progression
    print("\n[7/8] Generating Qualitative Detection Panels & Temporal Sequences...")
    generate_figure_14_qualitative_detections()
    generate_figure_15_failure_examples()
    generate_video_progression_figure()

    # 8. Ablation Study Verification
    print("\n[8/8] Checking Ablation Study Artifacts...")
    generate_ablation_figures()

    print("\n" + "=" * 65)
    print("RESEARCH VISUALIZATION SYSTEM GENERATION COMPLETE")
    print("All figures output to: research/figures/ (PNG, SVG, PDF)")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
