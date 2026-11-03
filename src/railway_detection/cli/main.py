"""Command-line interface for the railway detection research foundation."""

from __future__ import annotations

import argparse
import json
import os
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

DEFAULT_EXPERIMENT_REGISTRY = Path("results/experiment_registry.jsonl")
EXPERIMENT_REGISTRY_ENV = "RAILWAY_EXPERIMENT_REGISTRY"


def resolve_registry_path(override: str | Path | None = None) -> Path:
    """Resolve where run records are appended, honouring explicit and env overrides.

    The default target is a tracked research artifact, so tests and tooling that
    must not mutate it pass ``override`` or set ``RAILWAY_EXPERIMENT_REGISTRY``.
    An empty environment override is rejected rather than silently falling back
    to the tracked registry.
    """
    if override is not None:
        candidate = str(override).strip()
        if not candidate:
            raise ConfigError("registry path override is empty; provide a path or omit it")
        return Path(candidate)
    env_value = os.environ.get(EXPERIMENT_REGISTRY_ENV)
    if env_value is not None:
        candidate = env_value.strip()
        if not candidate:
            raise ConfigError(
                f"{EXPERIMENT_REGISTRY_ENV} is set but empty; unset it or provide a path"
            )
        return Path(candidate)
    return DEFAULT_EXPERIMENT_REGISTRY


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
    validate_parser.add_argument(
        "--registry-path",
        default=None,
        help="Override the experiment registry JSONL destination",
    )
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
    vision_train_parser.add_argument(
        "--registry-path",
        default=None,
        help="Override the experiment registry JSONL destination",
    )
    vision_train_parser.set_defaults(func=_vision_train)

    # Audio subcommands
    audio_parser = subparsers.add_parser(
        "audio", help="Audio extraction and preprocessing commands"
    )
    audio_sub = audio_parser.add_subparsers(dest="audio_command", required=True)
    audio_extract_parser = audio_sub.add_parser("extract", help="Extract PCM WAV from video")
    audio_extract_parser.add_argument("--video-path", required=True, help="Path to input video")
    audio_extract_parser.add_argument("--output-wav", required=True, help="Destination WAV path")
    audio_extract_parser.add_argument(
        "--sample-rate", type=int, default=16000, help="Target sample rate"
    )
    audio_extract_parser.set_defaults(func=_audio_extract)

    # Simulation subcommands
    sim_parser = subparsers.add_parser("simulate", help="Railway crossing simulation commands")
    sim_sub = sim_parser.add_subparsers(dest="simulate_command", required=True)
    sim_run_parser = sim_sub.add_parser("run", help="Replay event simulation")
    sim_run_parser.add_argument(
        "--event-dir", required=True, help="Path to Layer B event directory"
    )
    sim_run_parser.add_argument("--scenario", default="normal", help="Simulation scenario name")
    sim_run_parser.add_argument("--output-dir", default=None, help="Output directory")
    sim_run_parser.add_argument(
        "--profile",
        action="store_true",
        help="Write an offline replay profile (not a hardware benchmark)",
    )
    sim_run_parser.set_defaults(func=_simulate_run)

    # Experiment subcommands
    exp_parser = subparsers.add_parser("experiment", help="B0–B7 benchmark experiment commands")
    exp_sub = exp_parser.add_subparsers(dest="experiment_command", required=True)
    exp_run_parser = exp_sub.add_parser("run", help="Run benchmark condition")
    exp_run_parser.add_argument(
        "--condition",
        required=True,
        choices=["B0", "B1", "B2", "B3", "B4", "B5", "B6", "B7"],
        help="Benchmark condition (B0-B7)",
    )
    exp_run_parser.add_argument("--event-dir", required=True, help="Path to event directory")
    exp_run_parser.add_argument("--output-dir", default=None, help="Output directory")
    exp_run_parser.set_defaults(func=_experiment_run)

    # Phase 12 computational engine is independently testable. The official
    # command assesses live evidence and refuses before execution unless all
    # prerequisites, including a verifiable authorization artifact, exist.
    eval_parser = subparsers.add_parser(
        "evaluation", help="Phase 12 official evaluation readiness and execution"
    )
    eval_sub = eval_parser.add_subparsers(dest="evaluation_command", required=True)
    eval_run_parser = eval_sub.add_parser(
        "run", help="Assess prerequisites and run only if officially authorized"
    )
    eval_run_parser.add_argument("--repository-root", default=".")
    eval_run_parser.add_argument(
        "--config", default="configs/frozen_experiment_v1.yaml", help="Frozen config path"
    )
    eval_run_parser.add_argument(
        "--policy", default="configs/decision_policy_v1.yaml", help="Frozen decision policy"
    )
    eval_run_parser.add_argument(
        "--input-manifest",
        default="data/manifests/phase12_evaluation_inputs.json",
        help="Hash-bound Phase 12 event input manifest",
    )
    eval_run_parser.add_argument(
        "--blocker-report",
        default=None,
        help="Optional caller-selected location for a readiness blocker report only",
    )
    eval_run_parser.add_argument(
        "--output-dir",
        default=None,
        help=(
            "Where official outputs go once every prerequisite is verified. Must not exist "
            "or be empty, and may not be inside an evidence/config tree. On failure only "
            "<output-dir>.failure_report.json is written."
        ),
    )
    eval_run_parser.set_defaults(func=_evaluation_run)

    eval_status_parser = eval_sub.add_parser(
        "status",
        help="Print the evidence-derived readiness report (read-only; no execution)",
    )
    eval_status_parser.add_argument("--repository-root", default=".")
    eval_status_parser.add_argument("--config", default="configs/frozen_experiment_v1.yaml")
    eval_status_parser.add_argument("--policy", default="configs/decision_policy_v1.yaml")
    eval_status_parser.add_argument(
        "--input-manifest", default="data/manifests/phase12_evaluation_inputs.json"
    )
    eval_status_parser.set_defaults(func=_evaluation_status)

    metadata_audit_parser = eval_sub.add_parser(
        "metadata-only-audit",
        help="Audit manifest metadata only; not official readiness or full integrity",
    )
    metadata_audit_parser.add_argument("--repository-root", default=".")
    metadata_audit_parser.add_argument(
        "--input-manifest", default="data/manifests/phase12_evaluation_inputs.json"
    )
    metadata_audit_parser.set_defaults(func=_evaluation_metadata_only_audit)

    bench_parser = subparsers.add_parser(
        "benchmark", help="Reproducible Phase 14 benchmark (synthetic workload, no claims)"
    )
    bench_sub = bench_parser.add_subparsers(dest="benchmark_command", required=True)
    bench_run_parser = bench_sub.add_parser("run", help="Run the benchmark and write a report")
    from railway_detection.optimization.benchmark_cli import add_arguments as _bench_args
    from railway_detection.optimization.benchmark_cli import run as _bench_run

    _bench_args(bench_run_parser)
    bench_run_parser.set_defaults(func=_bench_run)

    audit_parser = subparsers.add_parser("audit", help="Read-only audits (no side effects)")
    audit_sub = audit_parser.add_subparsers(dest="audit_command", required=True)
    repro_parser = audit_sub.add_parser("reproducibility", help="Reproducibility and claim audit")
    repro_parser.add_argument("--json", dest="json_out", default=None)
    repro_parser.add_argument("--md", dest="md_out", default=None)
    repro_parser.add_argument("--repository-root", default=".")
    repro_parser.add_argument("--results", action="append", default=[])
    repro_parser.set_defaults(func=_audit_reproducibility)

    # Future namespaces: clear "not implemented in Phase 0" errors.
    report_parser = subparsers.add_parser("report", help="Report commands (placeholder)")
    report_sub = report_parser.add_subparsers(dest="report_command", required=True)
    report_gen_parser = report_sub.add_parser("generate", help="Generate publication report")
    report_gen_parser.set_defaults(func=_not_implemented)

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
        resolve_registry_path(getattr(args, "registry_path", None)),
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
            resolve_registry_path(getattr(args, "registry_path", None)),
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


def _audio_extract(args: argparse.Namespace) -> int:
    from railway_detection.data.audio_extractor import extract_audio_from_video
    from railway_detection.safety.media_guard import MediaAccessAuthorizationError

    # The authorization check lives inside extract_audio_from_video (operation boundary), so it
    # cannot be skipped by calling the library directly; the CLI only reports the refusal.
    try:
        res = extract_audio_from_video(
            Path(args.video_path), Path(args.output_wav), sample_rate=args.sample_rate
        )
    except MediaAccessAuthorizationError as exc:
        logger.error("Audio extraction blocked by media authorization gate: %s", exc)
        return 1
    if res is not None:
        logger.info("audio extracted successfully to %s", res)
        return 0
    logger.error("audio extraction failed for %s", args.video_path)
    return 1


def _simulate_run(args: argparse.Namespace) -> int:
    from railway_detection.data.layer_b import load_event_bundle
    from railway_detection.fusion.collector import MultimodalEvidenceCollector
    from railway_detection.simulation.runner import EventSimulationRunner

    event_path = Path(args.event_dir)
    load_res = load_event_bundle(event_path, strict_metadata=False)
    if not load_res.ok:
        logger.error("failed to load event bundle: %s", load_res.issues)
        return 1
    event = load_res.event
    assert event is not None

    entry_t = None
    clear_t = None
    for lbl in event.labels:
        if lbl.name in ("crossing_entry", "approach_entry") and lbl.timestamp_s is not None:
            entry_t = float(lbl.timestamp_s)
        elif lbl.name in ("tail_clearance", "clearance") and lbl.timestamp_s is not None:
            clear_t = float(lbl.timestamp_s)

    collector = MultimodalEvidenceCollector()
    frames = collector.generate_frames_from_history(0.0, 20.0, stride_s=0.5)

    runner = EventSimulationRunner()
    profiler = None
    if getattr(args, "profile", False):
        from railway_detection.optimization.profiler import StageProfiler

        profiler = StageProfiler()
    out_dir = (
        Path(args.output_dir)
        if args.output_dir
        else Path("results/simulations") / event.event_id
    )
    try:
        result = runner.run_frames(
            frames=frames,
            event_id=event.event_id,
            scenario_name=args.scenario,
            entry_time_s=entry_t,
            clearance_time_s=clear_t,
            profiler=profiler,
        )
    except BaseException:
        if profiler is not None and runner.last_profile_report is not None:
            _write_optional_profile_report(out_dir, runner.last_profile_report)
        raise

    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "simulation_result.json"
    out_file.write_text(json.dumps(result.metrics, indent=2), encoding="utf-8")
    if profiler is not None and runner.last_profile_report is not None:
        _write_optional_profile_report(out_dir, runner.last_profile_report)
    logger.info("simulation finished; result written to %s", out_file)
    return 0


def _write_optional_profile_report(out_dir: Path, report: dict[str, Any]) -> None:
    """Persist diagnostic data without masking a completed or failed replay."""
    profile_file = out_dir / "simulation_profile.json"
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        profile_file.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        logger.info("simulation profile written to %s", profile_file)
    except Exception as exc:
        logger.warning("could not write optional simulation profile %s: %s", profile_file, exc)


def _experiment_run(args: argparse.Namespace) -> int:
    from railway_detection.data.layer_b import load_event_bundle
    from railway_detection.experiments.runner import BenchmarkCondition, ExperimentRunner
    from railway_detection.fusion.collector import MultimodalEvidenceCollector

    cond = BenchmarkCondition(args.condition)
    event_path = Path(args.event_dir)

    event_dirs = (
        [event_path]
        if (event_path / "camera_1.mp4").exists()
        or (event_path / "camera_front.mp4").exists()
        or (event_path / "metadata.json").exists()
        else [d for d in event_path.iterdir() if d.is_dir()]
    )

    events_data = []
    for d in event_dirs:
        load_res = load_event_bundle(d, strict_metadata=False)
        if load_res.event is not None:
            collector = MultimodalEvidenceCollector()
            frames = collector.generate_frames_from_history(0.0, 20.0, stride_s=0.5)
            events_data.append((load_res.event, frames))

    if not events_data:
        logger.error("no valid event bundles found in %s", event_path)
        return 1

    custom_out = Path(args.output_dir) if args.output_dir else None
    runner = ExperimentRunner(output_root=custom_out or Path("results/experiments"))
    runner.run_condition(condition=cond, events=events_data, custom_output_dir=custom_out)
    return 0


def _evaluation_status(args: argparse.Namespace) -> int:
    """Print the readiness report, including categorized blockers and live bindings."""
    from railway_detection.evaluation.execution_gate import assess_official_phase12_readiness

    readiness = assess_official_phase12_readiness(
        Path(args.repository_root).resolve(),
        config_path=args.config,
        policy_path=args.policy,
        input_manifest_path=args.input_manifest,
    )
    print(json.dumps(readiness.to_dict(), indent=2, sort_keys=True))
    return 0 if readiness.ready else 3


def _evaluation_metadata_only_audit(args: argparse.Namespace) -> int:
    """Validate input-manifest metadata without assessing readiness or source bytes."""
    from railway_detection.evaluation.metadata_only_audit import (
        MetadataOnlyIsolationError,
        audit_input_manifest_metadata_only,
    )
    from railway_detection.evaluation.input_contracts import EvaluationInputError

    root = Path(args.repository_root).resolve()
    manifest = Path(args.input_manifest)
    if not manifest.is_absolute():
        manifest = root / manifest
    try:
        report = audit_input_manifest_metadata_only(
            manifest,
            repository_root=root,
        )
    except MetadataOnlyIsolationError as exc:
        logger.error("metadata-only isolation violation: %s", exc)
        return 4
    except EvaluationInputError as exc:
        print(json.dumps({"audit_mode": "METADATA_ONLY_MANIFEST_AUDIT_NOT_OFFICIAL_READINESS", **exc.to_dict()}, indent=2, sort_keys=True))
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


def _evaluation_run(args: argparse.Namespace) -> int:
    """Assess live prerequisites and refuse official execution with blocker codes."""
    from railway_detection.evaluation.execution_gate import assess_official_phase12_readiness
    from railway_detection.evaluation.input_contracts import EvidenceClassification
    from railway_detection.evaluation.output_contracts import (
        EvaluationFailureReport,
    )

    root = Path(args.repository_root).resolve()
    readiness = assess_official_phase12_readiness(
        root,
        config_path=args.config,
        policy_path=args.policy,
        input_manifest_path=args.input_manifest,
    )
    if not readiness.ready:
        blocker_data = tuple(item.to_dict() for item in readiness.blockers)
        report = EvaluationFailureReport(
            schema_version="phase12-failure-report/1",
            status="BLOCKED",
            evidence_classification=EvidenceClassification.REAL,
            blockers=blocker_data,
        )
        logger.error("Phase 12 evaluation blocked: %s", ", ".join(readiness.blocker_codes))
        for category, codes in readiness.blockers_by_category().items():
            logger.error("  %s: %s", category, ", ".join(codes))
        if args.blocker_report:
            report.write(args.blocker_report)
        return 3

    # Prerequisites and a bound EVAL-AUTH record verified. The runner re-assesses them
    # itself; nothing about readiness is passed in from here.
    from railway_detection.evaluation.evaluation_runner import Phase12EvaluationRunner

    if not args.output_dir:
        logger.error(
            "Phase 12 prerequisites verified (%s); pass --output-dir to run the official "
            "replay and evaluation",
            readiness.authorization_attestation_level,
        )
        return 2
    destination = Path(args.output_dir)
    failure_path = destination.with_name(destination.name + ".failure_report.json")
    outcome = Phase12EvaluationRunner().run_official_safe(
        repository_root=root,
        config_path=args.config,
        policy_path=args.policy,
        input_manifest_path=args.input_manifest,
        output_dir=destination,
        failure_report_path=failure_path,
        command="railway-detection evaluation run",
    )
    if isinstance(outcome, EvaluationFailureReport):
        logger.error(
            "Phase 12 official run failed: %s (report: %s)",
            ", ".join(f"{b['code']}: {b['detail']}" for b in outcome.blockers),
            failure_path,
        )
        return 5
    logger.info("Phase 12 official outputs written to %s", destination)
    return 0


def _audit_reproducibility(args: argparse.Namespace) -> int:
    from railway_detection.reproducibility import render_markdown, run_reproducibility_audit

    root = Path(args.repository_root).resolve()
    for target in (args.json_out, args.md_out):
        if target is None:
            continue
        resolved = Path(target).resolve()
        for name in (
            "data", "configs", "models", "experiments", "results", "src", "tests", "docs"
        ):
            guard = (root / name).resolve()
            if resolved == guard or guard in resolved.parents:
                logger.error("refusing to write the audit inside %s/", name)
                return 2
    report = run_reproducibility_audit(root, result_dirs=[Path(r) for r in args.results])
    if args.json_out:
        Path(args.json_out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json_out).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    if args.md_out:
        Path(args.md_out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.md_out).write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report["status_counts"], sort_keys=True))
    return 0


def _not_implemented(args: argparse.Namespace) -> int:
    logger.error("this command is not implemented in Phase 0")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
