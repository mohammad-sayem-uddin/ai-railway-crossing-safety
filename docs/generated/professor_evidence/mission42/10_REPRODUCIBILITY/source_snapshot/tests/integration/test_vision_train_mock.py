"""Integration test: split manifests -> vision training with mock backend."""

from __future__ import annotations

import json

from railway_detection.cli.main import main


def test_vision_train_mock_end_to_end(tmp_path):
    """CLI `vision train --mock` completes without network or GPU."""
    split_root = tmp_path / "splits"
    split_id = "s_mock"
    split_dir = split_root / split_id
    split_dir.mkdir(parents=True)
    (split_dir / "split_summary.json").write_text(
        json.dumps(
            {
                "split_id": split_id,
                "group_field": "crossing_id",
                "seed": 42,
                "ratios": {"train": 0.7, "val": 0.15, "test": 0.15},
                "require_grouping": True,
                "allow_ungrouped_fallback": False,
                "partitions": {"train": ["a1"], "val": ["b1"], "test": ["c1"]},
                "group_assignments": {"a": "train", "b": "val", "c": "test"},
                "warnings": [],
            }
        ),
        encoding="utf-8",
    )
    for name in ("train", "val", "test"):
        (split_dir / f"{name}.jsonl").write_text(
            '{"sample_id": "x"}\n', encoding="utf-8"
        )

    config_path = tmp_path / "vision.yaml"
    config_path.write_text(
        f"""
adapter: yolo
mock_data: true
dataset_root: {tmp_path}/raw
annotations_root: {tmp_path}/raw
class_mapping: {{front: 0, side: 1, rear: 2}}
seed: 42
device: cpu
image_size: [640, 640]
training:
  model_name: yolov8n.pt
  epochs: 1
  batch_size: 2
output_root: {tmp_path}/results
split_output_root: {split_root}
experiment_root: {tmp_path}/experiments
split:
  ratios: {{train: 0.7, val: 0.15, test: 0.15}}
""",
        encoding="utf-8",
    )

    exit_code = main(
        ["vision", "train", "--config", str(config_path), "--mock"]
    )
    assert exit_code == 0

    run_dir = next((tmp_path / "experiments").iterdir())
    assert (run_dir / "run_manifest.json").exists()
    assert (run_dir / "training_metrics.json").exists()
    assert (run_dir / "training_result.json").exists()

    result = json.loads(
        (run_dir / "training_result.json").read_text(encoding="utf-8")
    )
    assert result["checkpoint_path"] is not None
    assert not result["errors"]


def test_vision_train_dry_run(tmp_path):
    """Dry run builds the descriptor without training."""
    split_root = tmp_path / "splits"
    split_dir = split_root / "s_dry"
    split_dir.mkdir(parents=True)
    (split_dir / "split_summary.json").write_text(
        json.dumps(
            {
                "split_id": "s_dry",
                "group_field": "crossing_id",
                "seed": 1,
                "ratios": {"train": 0.7, "val": 0.15, "test": 0.15},
                "require_grouping": True,
                "allow_ungrouped_fallback": False,
                "partitions": {"train": ["a1"], "val": [], "test": []},
                "group_assignments": {"a": "train"},
                "warnings": [],
            }
        ),
        encoding="utf-8",
    )

    config_path = tmp_path / "vision.yaml"
    config_path.write_text(
        f"""
adapter: yolo
mock_data: true
dataset_root: {tmp_path}/raw
annotations_root: {tmp_path}/raw
class_mapping: {{front: 0}}
seed: 1
output_root: {tmp_path}/results
split_output_root: {split_root}
experiment_root: {tmp_path}/experiments
split:
  ratios: {{train: 0.7, val: 0.15, test: 0.15}}
""",
        encoding="utf-8",
    )

    exit_code = main(
        ["vision", "train", "--config", str(config_path), "--mock", "--dry-run"]
    )
    assert exit_code == 0

    run_dir = next((tmp_path / "experiments").iterdir())
    assert (run_dir / "resolved_config.yaml").exists()


def test_vision_train_missing_split(tmp_path):
    """Training fails cleanly when no split exists."""
    config_path = tmp_path / "vision.yaml"
    config_path.write_text(
        f"""
adapter: yolo
mock_data: true
dataset_root: {tmp_path}/raw
annotations_root: {tmp_path}/raw
class_mapping: {{front: 0}}
seed: 1
output_root: {tmp_path}/results
split_output_root: {tmp_path}/splits_missing
experiment_root: {tmp_path}/experiments
split:
  ratios: {{train: 0.7, val: 0.15, test: 0.15}}
""",
        encoding="utf-8",
    )
    exit_code = main(
        ["vision", "train", "--config", str(config_path), "--mock"]
    )
    assert exit_code == 1
