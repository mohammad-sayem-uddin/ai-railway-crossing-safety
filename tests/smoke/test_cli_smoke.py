"""End-user smoke test exercising the CLI against a tiny mock dataset."""

import json

from railway_detection.cli.main import main
from tests.fixtures.mock_data import make_mock_vision_dataset


def test_cli_validate_mock_dataset(tmp_path):
    fixture = make_mock_vision_dataset(tmp_path / "data")
    output = tmp_path / "results" / "dataset_validation"

    config_path = tmp_path / "vision.yaml"
    config_path.write_text(
        f"""
adapter: yolo
mock_data: true
dataset_root: {fixture['images_root']}
annotations_root: {fixture['labels_root']}
class_mapping: {{front: 0, side: 1, rear: 2}}
seed: 42
output_root: {output}
split_output_root: {tmp_path}/data/splits
split:
  ratios: {{train: 0.7, val: 0.15, test: 0.15}}
  group_field: crossing_id
""",
        encoding="utf-8",
    )

    exit_code = main(["data", "validate", "--config", str(config_path)])
    assert exit_code == 0

    report_path = output / "report.json"
    assert report_path.exists()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["passed"] is True
    assert report["mock_data"] is True
    assert report["image_count"] == 4

    manifest_path = output / "run_manifest.json"
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["mock_data"] is True
