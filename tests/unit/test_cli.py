
from railway_detection.cli.main import main


def test_cli_help():
    assert main(["--help"]) == 0


def test_cli_version():
    assert main(["--version"]) == 0


def test_cli_not_implemented_command():
    assert main(["vision", "train"]) == 2


def test_cli_invalid_config(tmp_path):
    path = tmp_path / "vision.yaml"
    path.write_text("not: valid: yaml: [", encoding="utf-8")
    assert main(["data", "validate", "--config", str(path)]) == 2


def test_cli_dry_run_valid_config(tmp_path):
    path = tmp_path / "vision.yaml"
    path.write_text(
        """
adapter: yolo
dataset_root: data/raw/vision/images
annotations_root: data/raw/vision/labels
class_mapping: {front: 0, side: 1, rear: 2}
seed: 42
output_root: results/dataset_validation
split_output_root: data/splits
split:
  ratios: {train: 0.7, val: 0.15, test: 0.15}
""",
        encoding="utf-8",
    )
    assert main(["data", "validate", "--config", str(path), "--dry-run"]) == 0
