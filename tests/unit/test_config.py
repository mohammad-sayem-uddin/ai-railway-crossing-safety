import pytest

from railway_detection.config.exceptions import ConfigError
from railway_detection.config.loader import ConfigLoader


def _write(tmp_path, name, text):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def test_valid_vision_config(tmp_path):
    path = _write(
        tmp_path,
        "vision.yaml",
        """
adapter: yolo
mock_data: true
dataset_root: data/raw/vision/images
annotations_root: data/raw/vision/labels
class_mapping:
  front: 0
  side: 1
  rear: 2
seed: 42
output_root: results/dataset_validation
split_output_root: data/splits
split:
  ratios:
    train: 0.7
    val: 0.15
    test: 0.15
""",
    )
    loader = ConfigLoader(tmp_path)
    config = loader.load_vision(path)
    assert config.class_mapping == {"front": 0, "side": 1, "rear": 2}
    assert config.seed == 42


def test_vision_missing_required_field(tmp_path):
    path = _write(tmp_path, "vision.yaml", "dataset_root: x\n")
    loader = ConfigLoader(tmp_path)
    with pytest.raises(ConfigError):
        loader.load_vision(path)


def test_duplicate_class_mapping(tmp_path):
    path = _write(
        tmp_path,
        "vision.yaml",
        """
adapter: yolo
dataset_root: d
annotations_root: a
class_mapping:
  front: 0
  side: 0
  rear: 2
seed: 1
output_root: out
split_output_root: splits
split:
  ratios: {train: 0.7, val: 0.15, test: 0.15}
""",
    )
    loader = ConfigLoader(tmp_path)
    with pytest.raises(ConfigError):
        loader.load_vision(path)


def test_invalid_threshold(tmp_path):
    path = _write(
        tmp_path,
        "fusion.yaml",
        """
policy_version: "0.0.0"
source_roles: {}
confidence_thresholds:
  front: -1
temporal: {}
opening_criteria:
  audio_cannot_authorize_opening: true
""",
    )
    loader = ConfigLoader(tmp_path)
    with pytest.raises(ConfigError):
        loader.load_fusion(path)


def test_fusion_requires_audio_opening_guard(tmp_path):
    path = _write(
        tmp_path,
        "fusion.yaml",
        """
policy_version: "0.0.0"
source_roles: {}
confidence_thresholds: {}
temporal: {}
opening_criteria:
  audio_cannot_authorize_opening: false
""",
    )
    loader = ConfigLoader(tmp_path)
    with pytest.raises(ConfigError):
        loader.load_fusion(path)


def test_split_ratios_must_sum_to_one(tmp_path):
    path = _write(
        tmp_path,
        "vision.yaml",
        """
adapter: yolo
dataset_root: d
annotations_root: a
class_mapping: {front: 0}
seed: 1
output_root: out
split_output_root: splits
split:
  ratios: {train: 0.5, val: 0.5, test: 0.5}
""",
    )
    loader = ConfigLoader(tmp_path)
    with pytest.raises(ConfigError):
        loader.load_vision(path)
