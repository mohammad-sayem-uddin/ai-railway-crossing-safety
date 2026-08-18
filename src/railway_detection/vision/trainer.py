"""Vision training orchestration.

Creates a unique experiment run directory, resolves the split manifests,
delegates training to a backend adapter, and records a run manifest plus a
training metrics summary. Model selection is validation-only by design; the
test split is never used during training.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from railway_detection.data.split import SplitSummary
from railway_detection.utils.logging import get_logger
from railway_detection.utils.reproducibility import build_run_manifest, write_run_manifest

logger = get_logger("vision.trainer")


@dataclass
class TrainingResult:
    run_id: str
    run_dir: Path
    checkpoint_path: Path | None
    training_metrics: dict[str, Any]
    dry_run: bool = False
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "run_dir": str(self.run_dir),
            "checkpoint_path": str(self.checkpoint_path)
            if self.checkpoint_path is not None
            else None,
            "training_metrics": self.training_metrics,
            "dry_run": self.dry_run,
            "errors": self.errors,
        }


def train_vision(
    config: object,
    split_summary: SplitSummary,
    backend,
    *,
    output_root: Path,
    dry_run: bool = False,
) -> TrainingResult:
    """Orchestrate a training run through a backend adapter.

    ``config`` is a :class:`VisionConfig`-like object; ``backend`` implements
    the :class:`VisionDetectorBackend` protocol.
    """
    run_id = _generate_run_id()
    run_dir = output_root / run_id
    result = TrainingResult(
        run_id=run_id,
        run_dir=run_dir,
        checkpoint_path=None,
        training_metrics={},
        dry_run=dry_run,
    )

    if dry_run:
        run_dir.mkdir(parents=True, exist_ok=True)
        descriptor = _prepare_descriptor(backend, split_summary, run_dir / "descriptor", config)
        resolved = {
            "training": getattr(config, "training", {}),
            "seed": getattr(config, "seed", None),
            "device": getattr(config, "device", None),
            "image_size": getattr(config, "image_size", None),
            "class_mapping": getattr(config, "class_mapping", {}),
            "split_id": split_summary.split_id,
            "descriptor": str(descriptor),
            "dry_run": True,
        }
        (run_dir / "resolved_config.yaml").write_text(
            _to_yaml(resolved), encoding="utf-8"
        )
        logger.info("dry-run: descriptor written to %s", descriptor)
        return result

    run_dir.mkdir(parents=True, exist_ok=True)
    manifest = build_run_manifest(
        command="vision train",
        config=getattr(config, "raw", {}),
        output_dir=run_dir,
        seed=getattr(config, "seed", None),
        dataset_identity=str(getattr(config, "dataset_root", "")),
        mock_data=bool(getattr(config, "mock_data", False)),
        extra={"device": getattr(config, "device", "mps")},
    )
    write_run_manifest(manifest, run_dir)

    descriptor_dir = run_dir / "descriptor"
    descriptor = _prepare_descriptor(backend, split_summary, descriptor_dir, config)

    try:
        checkpoint = backend.train(config, descriptor, run_dir / "checkpoints")
    except Exception as exc:
        result.errors.append(str(exc))
        logger.error("training failed: %s", exc)
        return result

    result.checkpoint_path = checkpoint
    training_metrics = _load_training_metrics(checkpoint)
    result.training_metrics = training_metrics

    (run_dir / "training_metrics.json").write_text(
        json.dumps(training_metrics, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (run_dir / "training_result.json").write_text(
        json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    logger.info(
        "training complete: run_id=%s checkpoint=%s",
        run_id,
        checkpoint,
    )
    return result


def _load_training_metrics(checkpoint_path: Path) -> dict[str, Any]:
    """Read backend-produced metrics when available; never fabricate them."""
    candidates = [
        checkpoint_path.parent.parent / "results.csv",
        checkpoint_path.parent / "metrics.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            return {"metrics_file": str(candidate)}
    return {}


def _generate_run_id() -> str:
    from railway_detection.utils.reproducibility import generate_run_id

    return generate_run_id()


def _prepare_descriptor(
    backend: Any, split_summary: SplitSummary, output_dir: Path, config: object
) -> Path:
    try:
        return backend.prepare_dataset(
            split_summary,
            output_dir,
            dataset_root=getattr(config, "dataset_root", None),
            class_mapping=getattr(config, "class_mapping", None),
        )
    except TypeError:
        return backend.prepare_dataset(split_summary, output_dir)


def _to_yaml(data: dict[str, Any]) -> str:
    import yaml

    return yaml.safe_dump(data, sort_keys=True)
