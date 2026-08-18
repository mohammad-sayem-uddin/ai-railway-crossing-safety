"""Unit tests for Research Figure Generation Scripts."""

from __future__ import annotations

from pathlib import Path

from research.scripts.generate_ablation_figures import generate_ablation_figures
from research.scripts.generate_architecture_diagrams import (
    generate_figure_01_system_architecture,
    generate_figure_02_vision_pipeline,
    generate_figure_03_twocamera_crossing_concept,
)
from research.scripts.generate_evaluation_figures import (
    generate_figure_09_normalized_confusion_matrix,
    generate_figure_10_precision_recall_curves,
    generate_figure_11_per_class_metrics_comparison,
    generate_figure_12_confidence_f1_analysis,
    load_evaluation_metrics,
)
from research.scripts.generate_failure_figures import (
    generate_figure_13_failure_distribution,
)
from research.scripts.generate_state_machine_diagram import (
    generate_figure_06_gate_safety_state_machine,
)
from research.scripts.generate_temporal_diagrams import (
    generate_figure_04_multiframe_confirmation,
    generate_figure_05_evidence_persistence,
)
from research.scripts.generate_training_figures import (
    generate_figure_07_training_loss_curves,
    generate_figure_08_model_performance_curves,
    load_training_data,
)


def test_architecture_diagrams_generation(tmp_path: Path):
    generate_figure_01_system_architecture(tmp_path)
    generate_figure_02_vision_pipeline(tmp_path)
    generate_figure_03_twocamera_crossing_concept(tmp_path)

    assert (tmp_path / "fig01_system_architecture.png").exists()
    assert (tmp_path / "fig02_vision_pipeline.png").exists()
    assert (tmp_path / "fig03_twocamera_crossing_concept.png").exists()


def test_temporal_diagrams_generation(tmp_path: Path):
    generate_figure_04_multiframe_confirmation(tmp_path)
    generate_figure_05_evidence_persistence(tmp_path)

    assert (tmp_path / "fig04_multiframe_confirmation.png").exists()
    assert (tmp_path / "fig05_evidence_persistence.png").exists()


def test_state_machine_diagram_generation(tmp_path: Path):
    generate_figure_06_gate_safety_state_machine(tmp_path)
    assert (tmp_path / "fig06_gate_safety_state_machine.png").exists()


def test_training_figures_generation(tmp_path: Path):
    data = load_training_data()
    generate_figure_07_training_loss_curves(data, tmp_path)
    generate_figure_08_model_performance_curves(data, tmp_path)

    assert (tmp_path / "fig07_training_loss_curves.png").exists()
    assert (tmp_path / "fig08_model_performance_curves.png").exists()


def test_evaluation_figures_generation(tmp_path: Path):
    metrics = load_evaluation_metrics()
    generate_figure_09_normalized_confusion_matrix(metrics, tmp_path)
    generate_figure_10_precision_recall_curves(metrics, tmp_path)
    generate_figure_11_per_class_metrics_comparison(metrics, tmp_path)
    generate_figure_12_confidence_f1_analysis(metrics, tmp_path)

    assert (tmp_path / "fig09_confusion_matrix_normalized.png").exists()
    assert (tmp_path / "fig10_precision_recall_curves.png").exists()
    assert (tmp_path / "fig11_per_class_metrics_comparison.png").exists()
    assert (tmp_path / "fig12_confidence_f1_analysis.png").exists()


def test_failure_figures_generation(tmp_path: Path):
    generate_figure_13_failure_distribution(tmp_path)
    assert (tmp_path / "fig13_failure_category_distribution.png").exists()


def test_ablation_template_handling(tmp_path: Path):
    res = generate_ablation_figures(output_dir=tmp_path)
    assert res is False
