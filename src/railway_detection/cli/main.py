"""Command-line interface for the railway detection research foundation."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from railway_detection import __version__
from railway_detection.config.exceptions import ConfigError
from railway_detection.config.loader import ConfigLoader
from railway_detection.data.manifest import (
    build_vision_manifest,
    write_manifest,
)
from railway_detection.data.split import generate_group_split, verify_group_disjointness
from railway_detection.data.validator import validate_vision_dataset
from railway_detection.utils.logging import configure_logging, get_logger
from railway_detection.utils.reproducibility import (
    append_registry_record,
    build_run_manifest,
    write_run_manifest,
)

logger = get_logger("cli")


def main(argv: Sequence[str] | None = None) -> int:
    configure_logging()
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code or 0)
    if not hasattr(args, "func"):
        parser.print_help()
        return 0
    try:
        return int(args.func(args))
    except ConfigError as exc:
        logger.error("configuration error: %s", exc)
        return 2
    except KeyboardInterrupt:
        logger.warning("interrupted")
        return 130
    except Exception as exc:  # pragma: no cover - last-resort CLI boundary
        logger.exception("unexpected error: %s", exc)
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="railway_detection",
        description="Railway-crossing train detection research foundation (simulation only).",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command")

    data_parser = subparsers.add_parser("data", help="Dataset validation and split commands")
    data_sub = data_parser.add_subparsers(dest="data_command", required=True)

    validate_parser = data_sub.add_parser("validate", help="Validate a vision dataset")
    validate_parser.add_argument("--config", required=True, help="Path to vision.yaml")
    validate_parser.add_argument("--dry-run", action="store_true", help="Validate config only")
    validate_parser.add_argument("--output-dir", default=None, help="Override output directory")
    validate_parser.set_defaults(func=_data_validate)

    split_parser = data_sub.add_parser("split", help="Generate a group-aware split")
    split_parser.add_argument("--config", required=True, help="Path to vision.yaml")
    split_parser.add_argument("--metadata", default=None, help="Path to a JSON/JSONL metadata file")
    split_parser.add_argument("--dry-run", action="store_true", help="Validate config only")
    split_parser.add_argument(
        "--allow-ungrouped",
        action="store_true",
        help="Explicitly allow fallback splitting",
    )
    split_parser.set_defaults(func=_data_split)

    vision_parser = subparsers.add_parser("vision", help="Vision training commands")
    vision_sub = vision_parser.add_subparsers(dest="vision_command", required=True)

    vision_train_parser = vision_sub.add_parser(
        "train", help="Train a vision model from split manifests"
    )
    vision_train_parser.add_argument("--config", required=True, help="Path to vision.yaml")
    vision_train_parser.add_argument(
        "--split-id",
        default=None,
        help="Split id under data/splits/<id>/ (latest if omitted)",
    )
    vision_train_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build descriptors and resolve config without training",
    )
    vision_train_parser.add_argument(
        "--mock",
        action="store_true",
        help="Force a mock backend (tests only)",
    )
    vision_train_parser.set_defaults(func=_vision_train)

    # Future namespaces: clear "not implemented in Phase 0" errors.
    for name in ("audio", "simulate", "experiment", "report"):
        sub = subparsers.add_parser(name, help=f"{name} commands (Phase 0 placeholder)")
        sub_sub = sub.add_subparsers(dest=f"{name}_command", required=True)
        for action in ("train", "evaluate", "infer", "run", "generate"):
            action_parser = sub_sub.add_parser(action, help="Not implemented in Phase 0")
            action_parser.add_argument("--config", required=False)
            action_parser.add_argument("--checkpoint", required=False)
            action_parser.add_argument("--source", required=False)
            action_parser.add_argument("--source-id", required=False)
            action_parser.add_argument("--scenario", required=False)
            action_parser.set_defaults(func=_not_implemented)

    return parser


def _data_validate(args: argparse.Namespace) -> int:
    loader = ConfigLoader()
    config = loader.load_vision(args.config)

    if args.dry_run:
        logger.info("dry-run: config valid; no dataset validation performed")
        return 0

    output_dir = Path(args.output_dir) if args.output_dir else config.output_root
    manifest = build_run_manifest(
        command="data validate",
        config=_config_dict(config),
        output_dir=output_dir,
        seed=config.seed,
        dataset_identity=str(config.dataset_root),
        mock_data=config.mock_data,
    )
    write_run_manifest(manifest, output_dir)

    report = validate_vision_dataset(
        config.dataset_root,
        config.annotations_root,
        config.class_mapping,
        mock_data=config.mock_data,
        detect_duplicate_hashes=config.detect_duplicate_hashes,
    )
    report_path = output_dir / "report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report.to_dict(), indent=2) + "\n", encoding="utf-8")
    logger.info("validation report written to %s", report_path)

    if report.passed:
        metadata = _load_metadata_mapping(config.metadata_path)
        manifest_result, manifest_summary = build_vision_manifest(
            config.dataset_root,
            config.annotations_root,
            config.class_mapping,
            metadata=metadata,
        )
        manifest_path = write_manifest(
            manifest_result,
            output_dir,
            metadata={"dataset_identity": str(config.dataset_root)},
        )
        logger.info(
            "dataset manifest written to %s (%d records)",
            manifest_path,
            manifest_summary.sample_count,
        )
        for warning in manifest_result.warnings:
            logger.warning("%s", warning)

    append_registry_record(
        {
            "run_id": manifest["run_id"],
            "command": "data validate",
            "dataset_root": str(config.dataset_root),
            "mock_data": config.mock_data,
            "passed": report.passed,
            "error_count": report.error_count,
            "warning_count": report.warning_count,
            "report_path": str(report_path),
        },
        Path("results/experiment_registry.jsonl"),
    )

    if not report.passed:
        logger.error(
            "validation failed with %d error(s) and %d warning(s)",
            report.error_count,
            report.warning_count,
        )
        return 1
    logger.info(
        "validation passed: %d image(s), %d annotation(s), %d warning(s)",
        report.image_count,
        report.annotation_count,
        report.warning_count,
    )
    return 0


def _data_split(args: argparse.Namespace) -> int:
    loader = ConfigLoader()
    config = loader.load_vision(args.config)

    if args.dry_run:
        logger.info("dry-run: config valid; no split generated")
        return 0

    samples = _load_samples(args.metadata, config)
    split = generate_group_split(
        samples,
        group_field=config.split.get("group_field", "crossing_id"),
        ratios=config.split["ratios"],
        seed=config.seed,
        require_grouping=bool(config.split.get("require_grouping", True)),
        allow_ungrouped_fallback=args.allow_ungrouped
        or bool(config.split.get("allow_ungrouped_fallback", False)),
    )

    output_dir = config.split_output_root / split.split_id
    manifest = build_run_manifest(
        command="data split",
        config=_config_dict(config),
        output_dir=output_dir,
        seed=config.seed,
        dataset_identity=str(config.dataset_root),
        mock_data=config.mock_data,
        extra={"split_summary": split.to_dict()},
    )
    write_run_manifest(manifest, output_dir)

    for name, ids in split.partitions.items():
        path = output_dir / f"{name}.jsonl"
        path.write_text(
            "\n".join(json.dumps({"sample_id": i}) for i in ids) + "\n",
            encoding="utf-8",
        )

    summary_path = output_dir / "split_summary.json"
    summary_path.write_text(json.dumps(split.to_dict(), indent=2) + "\n", encoding="utf-8")

    for warning in split.warnings:
        logger.warning("%s", warning)

    if split.error:
        logger.error("split failed: %s", split.error)
        return 1

    disjoint = verify_group_disjointness(split)
    if not disjoint["disjoint"]:
        logger.error("split is not group-disjoint: %s", disjoint["overlapping_groups"])
        return 1

    logger.info("split written to %s (group-disjoint: yes)", output_dir)
    return 0


def _vision_train(args: argparse.Namespace) -> int:
    loader = ConfigLoader()
    config = loader.load_vision(args.config)

    split_id = args.split_id or _latest_split_id(config.split_output_root)
    if split_id is None:
        logger.error(
            "no split found under %s; run `data split` first",
            config.split_output_root,
        )
        return 1
    split_dir = config.split_output_root / split_id
    summary_path = split_dir / "split_summary.json"
    if not summary_path.exists():
        logger.error("split summary not found at %s", summary_path)
        return 1
    split_summary = json.loads(summary_path.read_text(encoding="utf-8"))
    from railway_detection.data.split import SplitSummary

    summary = SplitSummary(
        split_id=split_summary["split_id"],
        group_field=split_summary["group_field"],
        seed=split_summary["seed"],
        ratios=split_summary["ratios"],
        require_grouping=split_summary["require_grouping"],
        allow_ungrouped_fallback=split_summary["allow_ungrouped_fallback"],
        partitions=split_summary["partitions"],
        group_assignments=split_summary["group_assignments"],
        warnings=split_summary["warnings"],
    )

    if args.mock:
        from railway_detection.vision.trainer import train_vision

        class MockBackend:
            backend_name = "mock"

            def prepare_dataset(self, split_summary, output_dir):
                output_dir.mkdir(parents=True, exist_ok=True)
                return output_dir / "data.yaml"

            def train(self, config, data_descriptor, output_dir):
                output_dir.mkdir(parents=True, exist_ok=True)
                return output_dir / "best.pt"

            def evaluate(self, checkpoint_path, split_manifest):
                return {}

            def load(self, checkpoint_path):
                pass

            def predict(self, image, conf, iou):
                return []

            def predict_batch(self, images, conf, iou):
                return [[] for _ in images]

        result = train_vision(
            config,
            summary,
            MockBackend(),
            output_root=config.experiment_root,
            dry_run=args.dry_run,
        )
    else:
        from railway_detection.vision.trainer import train_vision
        from railway_detection.vision.yolo_adapter import UltralyticsYOLOAdapter

        result = train_vision(
            config,
            summary,
            UltralyticsYOLOAdapter(),
            output_root=config.experiment_root,
            dry_run=args.dry_run,
        )

    if result.errors:
        logger.error("training failed: %s", result.errors[0])
        return 1
    if args.dry_run:
        logger.info("dry-run complete: run_id=%s", result.run_id)
    else:
        logger.info("training complete: run_id=%s", result.run_id)
        append_registry_record(
            {
                "run_id": result.run_id,
                "command": "vision train",
                "dataset_root": str(config.dataset_root),
                "mock_data": bool(args.mock or config.mock_data),
                "checkpoint_path": str(result.checkpoint_path)
                if result.checkpoint_path
                else None,
                "split_id": summary.split_id,
                "device": getattr(config, "device", "mps"),
            },
            Path("results/experiment_registry.jsonl"),
        )
    return 0


def _latest_split_id(split_output_root: Path) -> str | None:
    if not split_output_root.exists():
        return None
    candidates = [
        path.name for path in split_output_root.iterdir() if path.is_dir()
    ]
    if not candidates:
        return None
    return sorted(candidates, key=lambda name: _mtime(split_output_root / name))[-1]


def _mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def _load_metadata_mapping(metadata_path: Path | None) -> dict[str, Any] | None:
    """Load a per-image metadata mapping, or None when unavailable.

    Dataset-level summary files (like the Roboflow V1 metadata sheet) are not
    per-image records and are treated as absent, so grouping falls back to the
    documented inferred-source hint.
    """
    if metadata_path is None or not metadata_path.exists():
        return None
    try:
        data = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        logger.warning("metadata file %s is not valid JSON; ignoring", metadata_path)
        return None
    if not isinstance(data, dict):
        return None
    records = data.get("records")
    if isinstance(records, dict):
        return records
    if data.get("dataset_version") is not None and not any(
        isinstance(value, dict) for value in data.values() if value not in (None,)
    ):
        return None
    if all(isinstance(value, dict) for value in data.values()):
        return data
    return None


def _load_samples(metadata_path: str | None, config: object) -> list[Any]:
    """Load normalized samples from a JSON/JSONL metadata file or manifest."""
    from dataclasses import dataclass

    @dataclass
    class Sample:
        sample_id: str
        split_group_id: str | None

    candidate_paths: list[Path] = []
    if metadata_path:
        candidate_paths.append(Path(metadata_path))
    cfg_meta = getattr(config, "metadata_path", None)
    if cfg_meta:
        candidate_paths.append(Path(cfg_meta))
    cfg_out = getattr(config, "output_root", None)
    if cfg_out:
        candidate_paths.append(Path(cfg_out) / "dataset_manifest.jsonl")

    for path in candidate_paths:
        if not path.exists() or not path.is_file():
            continue
        try:
            samples: list[Any] = []
            text = path.read_text(encoding="utf-8")
            for line in text.splitlines():
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                if not isinstance(record, dict):
                    continue
                sample_id = record.get("image_id") or record.get("clip_id")
                if not sample_id:
                    continue
                group_id = record.get("split_group_id")
                samples.append(Sample(sample_id=sample_id, split_group_id=group_id))
            if samples:
                return samples
        except Exception:
            continue
    return []


def _config_dict(config: object) -> dict[str, object]:
    return getattr(config, "raw", {})


def _not_implemented(args: argparse.Namespace) -> int:
    logger.error("this command is not implemented in Phase 0")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
