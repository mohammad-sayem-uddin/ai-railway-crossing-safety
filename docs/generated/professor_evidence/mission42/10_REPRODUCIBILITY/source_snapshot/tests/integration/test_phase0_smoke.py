
from railway_detection.config.loader import ConfigLoader
from railway_detection.data.split import generate_group_split, verify_group_disjointness
from railway_detection.data.validator import validate_vision_dataset
from railway_detection.utils.reproducibility import (
    append_registry_record,
    build_run_manifest,
    write_run_manifest,
)
from tests.fixtures.mock_data import make_mock_vision_dataset


def test_phase0_end_to_end(tmp_path):
    """Mock data -> config validation -> dataset validation -> split -> manifest -> output."""
    fixture = make_mock_vision_dataset(tmp_path / "data")

    config_path = tmp_path / "vision.yaml"
    config_path.write_text(
        f"""
adapter: yolo
mock_data: true
dataset_root: {fixture['images_root']}
annotations_root: {fixture['labels_root']}
metadata_path: {fixture['metadata_path']}
class_mapping: {{front: 0, side: 1, rear: 2}}
seed: 42
output_root: {tmp_path}/results/dataset_validation
split_output_root: {tmp_path}/data/splits
split:
  ratios: {{train: 0.7, val: 0.15, test: 0.15}}
  group_field: crossing_id
  require_grouping: true
""",
        encoding="utf-8",
    )

    loader = ConfigLoader(tmp_path)
    config = loader.load_vision(config_path)

    report = validate_vision_dataset(
        config.dataset_root,
        config.annotations_root,
        config.class_mapping,
        mock_data=config.mock_data,
        metadata=fixture["metadata"],
    )
    assert report.passed

    metadata = fixture["metadata"]
    samples = []
    for image_id, record in metadata.items():
        samples.append(
            type(
                "Sample",
                (),
                {"sample_id": image_id, "split_group_id": record["split_group_id"]},
            )()
        )
    split = generate_group_split(
        samples,
        group_field="crossing_id",
        ratios=config.split["ratios"],
        seed=config.seed,
        require_grouping=True,
    )
    assert split.ok
    assert verify_group_disjointness(split)["disjoint"]

    output_dir = config.split_output_root / split.split_id
    manifest = build_run_manifest(
        command="data split",
        config=config.raw,
        output_dir=output_dir,
        seed=config.seed,
        dataset_identity=str(config.dataset_root),
        mock_data=True,
    )
    write_run_manifest(manifest, output_dir)
    append_registry_record(
        {"run_id": manifest["run_id"], "mock_data": True},
        tmp_path / "registry.jsonl",
    )

    assert (output_dir / "run_manifest.json").exists()
    assert (tmp_path / "registry.jsonl").exists()
