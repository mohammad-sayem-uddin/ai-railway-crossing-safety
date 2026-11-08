
import pytest
from PIL import Image

from railway_detection.data.validator import validate_vision_dataset


@pytest.fixture
def valid_dataset(tmp_path):
    images = tmp_path / "images"
    labels = tmp_path / "labels"
    images.mkdir()
    labels.mkdir()
    for _idx, (name, class_id, coords) in enumerate(
        [
            ("img_front", 0, "0.5 0.5 0.4 0.4"),
            ("img_side", 1, "0.5 0.5 0.4 0.4"),
            ("img_rear", 2, "0.5 0.5 0.4 0.4"),
        ]
    ):
        Image.new("RGB", (32, 32), color=(10, 10, 10)).save(images / f"{name}.jpg")
        (labels / f"{name}.txt").write_text(f"{class_id} {coords}\n", encoding="utf-8")
    return images, labels


def test_valid_dataset(valid_dataset):
    images, labels = valid_dataset
    report = validate_vision_dataset(
        images, labels, {"front": 0, "side": 1, "rear": 2}
    )
    assert report.passed
    assert report.image_count == 3
    assert report.annotation_count == 3
    assert report.class_distribution == {"front": 1, "side": 1, "rear": 1}


def test_corrupted_image(valid_dataset):
    images, labels = valid_dataset
    Image.new("RGB", (32, 32)).save(images / "broken.jpg")
    (images / "broken.jpg").write_bytes(b"not a real image")
    report = validate_vision_dataset(images, labels, {"front": 0, "side": 1, "rear": 2})
    assert not report.passed
    assert any(issue.code == "unreadable_image" for issue in report.issues)


def test_missing_label(valid_dataset):
    images, labels = valid_dataset
    Image.new("RGB", (32, 32)).save(images / "no_label.jpg")
    report = validate_vision_dataset(images, labels, {"front": 0, "side": 1, "rear": 2})
    assert report.passed  # missing label is a warning, not error
    assert any(issue.code == "missing_label" for issue in report.issues)


def test_invalid_class(valid_dataset):
    images, labels = valid_dataset
    Image.new("RGB", (32, 32)).save(images / "bad_class.jpg")
    (labels / "bad_class.txt").write_text("9 0.5 0.5 0.4 0.4\n", encoding="utf-8")
    report = validate_vision_dataset(images, labels, {"front": 0, "side": 1, "rear": 2})
    assert not report.passed
    assert any(issue.code == "unknown_class" for issue in report.issues)


def test_invalid_bbox(valid_dataset):
    images, labels = valid_dataset
    Image.new("RGB", (32, 32)).save(images / "bad_box.jpg")
    (labels / "bad_box.txt").write_text("0 2.0 0.5 0.4 0.4\n", encoding="utf-8")
    report = validate_vision_dataset(images, labels, {"front": 0, "side": 1, "rear": 2})
    assert not report.passed
    assert any(issue.code == "box_out_of_range" for issue in report.issues)


def test_nonfinite_coordinate(valid_dataset):
    images, labels = valid_dataset
    Image.new("RGB", (32, 32)).save(images / "nan_box.jpg")
    (labels / "nan_box.txt").write_text("0 nan 0.5 0.4 0.4\n", encoding="utf-8")
    report = validate_vision_dataset(images, labels, {"front": 0, "side": 1, "rear": 2})
    assert not report.passed
    assert any(issue.code == "non_finite_coordinate" for issue in report.issues)


def test_zero_box_size(valid_dataset):
    images, labels = valid_dataset
    Image.new("RGB", (32, 32)).save(images / "zero_box.jpg")
    (labels / "zero_box.txt").write_text("0 0.5 0.5 0.0 0.4\n", encoding="utf-8")
    report = validate_vision_dataset(images, labels, {"front": 0, "side": 1, "rear": 2})
    assert not report.passed
    assert any(issue.code == "invalid_box_size" for issue in report.issues)


def test_duplicate_filename(tmp_path):
    images = tmp_path / "images"
    labels = tmp_path / "labels"
    images.mkdir()
    labels.mkdir()
    nested = images / "nested"
    nested.mkdir()
    Image.new("RGB", (32, 32)).save(images / "dup.jpg")
    Image.new("RGB", (32, 32)).save(nested / "dup.jpg")
    (labels / "dup.txt").write_text("0 0.5 0.5 0.4 0.4\n", encoding="utf-8")
    report = validate_vision_dataset(images, labels, {"front": 0, "side": 1, "rear": 2})
    assert report.duplicate_basenames
