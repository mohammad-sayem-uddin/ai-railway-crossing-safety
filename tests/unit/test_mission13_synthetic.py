"""Synthetic unit tests for Mission 13 generalization & evaluator forensic properties.

100% synthetic tensors and bounding boxes; touches zero repository data files.
"""

from __future__ import annotations

import torch

from railway_detection.audio.model import CompactTrainHornCNN
from railway_detection.vision.evaluator import (
    GroundTruthBox,
    PredictionBox,
    evaluate_detection,
)


def test_compact_train_horn_cnn_parameter_count_and_bn_eval_behavior() -> None:
    """Verify exact parameter count (25,697) and BatchNorm inference stability on synthetic inputs."""
    torch.manual_seed(42)
    model = CompactTrainHornCNN(in_channels=1, dropout=0.30)
    total_params = sum(p.numel() for p in model.parameters())
    assert total_params == 25_697

    x_batch = torch.randn(8, 1, 64, 32)
    model.train()
    out_train = model(x_batch)
    assert out_train.shape == (8,)

    model.eval()
    x_single = x_batch[:1]
    out_eval = model(x_single)
    assert out_eval.shape == (1,)
    assert torch.isfinite(out_eval).all()


def test_evaluator_counts_low_conf_preds_in_confusion_matrix_even_above_threshold() -> None:
    """Reproduce the Mission 13 finding that evaluate_detection ignores confidence_threshold inside confusion_matrix."""
    gts = [
        GroundTruthBox(image_id="syn_0", label="front", bbox_xyxy=(10.0, 10.0, 50.0, 50.0)),
        GroundTruthBox(image_id="syn_0", label="side", bbox_xyxy=(100.0, 100.0, 160.0, 160.0)),
    ]
    preds = [
        PredictionBox(image_id="syn_0", label="front", confidence=0.85, bbox_xyxy=(10.0, 10.0, 50.0, 50.0)),
        PredictionBox(image_id="syn_0", label="side", confidence=0.80, bbox_xyxy=(100.0, 100.0, 160.0, 160.0)),
        # Low-confidence background false positive below confidence_threshold=0.50
        PredictionBox(image_id="syn_0", label="side", confidence=0.05, bbox_xyxy=(60.0, 60.0, 90.0, 90.0)),
    ]
    res = evaluate_detection(gts, preds, ["front", "rear", "side"], iou_threshold=0.5, confidence_threshold=0.5)
    # Filtered precision ignores the conf=0.05 box (1.0), whereas confusion_matrix + total_fp include it!
    assert res.per_class_precision["side"] == 1.0
    assert res.per_class_precision["front"] == 1.0
    assert res.confusion_matrix["background"]["side"] == 1
    assert res.total_fp == 1
    assert res.total_tp == 2
