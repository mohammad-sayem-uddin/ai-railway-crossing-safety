"""Reusable, synthetic-capable Phase 13 experiment execution infrastructure.

This engine is intentionally separate from the official command. It accepts
injectable data and inference providers, requires explicitly synthetic data,
uses predeclared baseline/treatment conditions and repeat seeds, and writes
only to a caller-chosen isolated directory. It does not load models or research
data itself and never alters ground truth.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from railway_detection import __version__
from railway_detection.evaluation.input_contracts import EvidenceClassification
from railway_detection.evaluation.output_contracts import canonical_json_bytes
from railway_detection.utils.reproducibility import capture_environment, git_revision
from railway_detection.safety.media_guard import require_media_authorization


class ExperimentPlanError(ValueError):
    """Malformed plan, provider, or provenance contract."""


class ExperimentDataProvider(Protocol):
    """Injectable source of per-event replay input and input fingerprints."""

    @property
    def evidence_classification(self) -> EvidenceClassification: ...

    def event_ids(self) -> Sequence[str]: ...

    def load_event(self, event_id: str) -> Any: ...

    def input_sha256(self, event_id: str) -> str: ...


class ExperimentInferenceProvider(Protocol):
    """Injectable condition inference/replay implementation."""

    def __call__(
        self,
        *,
        condition: ExperimentCondition,
        event_id: str,
        event_input: Any,
        seed: int,
    ) -> Mapping[str, float]: ...


@dataclass(frozen=True)
class ExperimentCondition:
    condition_id: str
    role: str
    changed_factors: tuple[str, ...] = ()
    overrides: Mapping[str, Any] = field(default_factory=dict)
    perturbation: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        if not self.condition_id.strip() or self.condition_id != self.condition_id.strip():
            raise ExperimentPlanError("condition_id must be a nonempty trimmed string")
        if self.role not in {"baseline", "treatment"}:
            raise ExperimentPlanError("condition role must be baseline or treatment")
        if len(self.changed_factors) != len(set(self.changed_factors)):
            raise ExperimentPlanError("changed_factors must be unique")
        if self.role == "baseline":
            if self.changed_factors or self.overrides or self.perturbation:
                raise ExperimentPlanError("baseline must not modify config or replay inputs")
        elif len(self.changed_factors) != 1:
            raise ExperimentPlanError("treatment must declare exactly one changed factor")
        if self.perturbation is not None and not isinstance(self.perturbation, Mapping):
            raise ExperimentPlanError("perturbation must be a mapping when provided")

    def to_dict(self) -> dict[str, Any]:
        return {
            "condition_id": self.condition_id,
            "role": self.role,
            "changed_factors": list(self.changed_factors),
            "overrides": dict(self.overrides),
            "perturbation": dict(self.perturbation) if self.perturbation else None,
        }


@dataclass(frozen=True)
class ExperimentPlan:
    plan_id: str
    frozen_config_sha256: str
    policy_sha256: str
    checkpoint_sha256: Mapping[str, str]
    conditions: tuple[ExperimentCondition, ...]
    repeat_seeds: tuple[int, ...]
    input_split_sha256: str

    def __post_init__(self) -> None:
        for label, digest in (
            ("frozen_config_sha256", self.frozen_config_sha256),
            ("policy_sha256", self.policy_sha256),
            ("input_split_sha256", self.input_split_sha256),
        ):
            _validate_sha256(digest, label)
        for checkpoint_name, digest in self.checkpoint_sha256.items():
            if not checkpoint_name.strip():
                raise ExperimentPlanError("checkpoint names must be nonempty")
            _validate_sha256(digest, f"checkpoint {checkpoint_name}")
        if not self.plan_id.strip():
            raise ExperimentPlanError("plan_id must be nonempty")
        if not self.conditions or sum(c.role == "baseline" for c in self.conditions) != 1:
            raise ExperimentPlanError(
                "plan requires exactly one baseline and at least one condition"
            )
        if len({condition.condition_id for condition in self.conditions}) != len(self.conditions):
            raise ExperimentPlanError("condition IDs must be unique")
        for condition in self.conditions:
            if condition.role != "treatment":
                continue
            applied = bool(condition.overrides) + bool(condition.perturbation)
            if applied == 0:
                raise ExperimentPlanError(
                    f"treatment {condition.condition_id!r} declares a changed factor but applies "
                    "no override or perturbation; it would be identical to the baseline"
                )
            if applied > 1:
                raise ExperimentPlanError(
                    f"treatment {condition.condition_id!r} applies both an override and a "
                    "perturbation; that changes more than the one declared factor"
                )
            (factor,) = condition.changed_factors
            if condition.overrides:
                if len(condition.overrides) != 1 or factor not in condition.overrides:
                    raise ExperimentPlanError(
                        f"treatment {condition.condition_id!r} must override exactly its declared "
                        f"factor {factor!r}; got {sorted(condition.overrides)} (hidden "
                        "configuration changes are refused)"
                    )
                _require_plain_finite(condition.overrides[factor], condition.condition_id)
            else:
                kind = condition.perturbation.get("kind") if condition.perturbation else None
                if kind != factor:
                    raise ExperimentPlanError(
                        f"treatment {condition.condition_id!r} perturbation kind {kind!r} does "
                        f"not match its declared factor {factor!r}"
                    )
                for value in condition.perturbation.values():
                    _require_plain_finite(value, condition.condition_id)
        if not self.repeat_seeds or any(
            not isinstance(seed, int) or isinstance(seed, bool) for seed in self.repeat_seeds
        ):
            raise ExperimentPlanError("repeat_seeds must be a nonempty tuple of integer seeds")
        if len(set(self.repeat_seeds)) != len(self.repeat_seeds):
            raise ExperimentPlanError("repeat seeds must be unique")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "phase13-experiment-plan/1",
            "plan_id": self.plan_id,
            "frozen_config_sha256": self.frozen_config_sha256,
            "policy_sha256": self.policy_sha256,
            "checkpoint_sha256": dict(sorted(self.checkpoint_sha256.items())),
            "input_split_sha256": self.input_split_sha256,
            "repeat_seeds": list(self.repeat_seeds),
            "conditions": [condition.to_dict() for condition in self.conditions],
        }


@dataclass(frozen=True)
class ExperimentRunResult:
    status: str
    evidence_classification: EvidenceClassification
    metrics_by_condition: Mapping[str, Mapping[str, float]]
    comparisons_to_baseline: Mapping[str, Mapping[str, float]]
    manifest: Mapping[str, Any]
    output_dir: Path
    failures: tuple[dict[str, Any], ...] = ()


def _atomic_write(path: Path, data: bytes) -> None:
    """Write one artifact without exposing a truncated file to a reader."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _sha256_file(path: Path) -> str:
    require_media_authorization(path, "HASH_RAW_MEDIA")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
_OFFICIAL_RESULT_TREES = ("results", "experiments", "data", "configs", "models")


def _refuse_official_locations(output_dir: Path) -> None:
    """Synthetic experiments may never write where official results or evidence live."""
    from railway_detection.safety import path_identity as pid

    for name in _OFFICIAL_RESULT_TREES:
        try:
            inside = pid.is_within(output_dir, _REPOSITORY_ROOT / name)
        except pid.PathIdentityError as exc:
            raise ExperimentPlanError(
                f"synthetic experiment output path refused ({exc.code})"
            ) from exc
        if inside:
            raise ExperimentPlanError(
                f"synthetic experiment output may not be written under the repository's "
                f"{name}/ tree"
            )


def _require_plain_finite(value: Any, where: str) -> None:
    """Condition parameters must be plain JSON values; floats must be finite."""
    if isinstance(value, float) and not math.isfinite(value):
        raise ExperimentPlanError(f"{where}: non-finite condition parameter {value!r}")
    if isinstance(value, Mapping):
        for item in value.values():
            _require_plain_finite(item, where)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _require_plain_finite(item, where)
    elif value is not None and not isinstance(value, (str, int, float, bool)):
        raise ExperimentPlanError(f"{where}: condition parameter {value!r} is not plain data")


def _validate_sha256(digest: str, field_name: str) -> None:
    if not isinstance(digest, str) or len(digest) != 64 or any(
        char not in "0123456789abcdef" for char in digest
    ):
        raise ExperimentPlanError(f"{field_name} must be lowercase SHA-256")


class Phase13ExperimentEngine:
    """Run planned conditions on synthetic providers and report paired metrics."""

    @staticmethod
    def _write_failure_manifest(
        destination: Path,
        *,
        status: str,
        plan: ExperimentPlan,
        classification: EvidenceClassification,
        fingerprints: Mapping[str, str],
        failures: Sequence[Mapping[str, Any]],
        completed_cells: Mapping[str, int],
        expected_cells: int,
        run_id: str,
        reason: str,
        command: str | None,
        cell_keys_by_condition: Mapping[str, Sequence[str]] | None = None,
    ) -> None:
        """Persist what is known about an aborted run; never aggregate partial rows."""
        destination.mkdir(parents=True, exist_ok=True)
        manifest = {
            "schema_version": "phase13-experiment-manifest/1",
            "phase": "13",
            "status": status,
            "reason": reason,
            "evidence_classification": classification.value,
            "empirical_performance_claim": False,
            "authorization_status": "not_authorized",
            "plan": plan.to_dict(),
            "input_sha256_by_event": dict(fingerprints),
            "expected_cells_per_condition": expected_cells,
            "completed_cells_by_condition": dict(sorted(completed_cells.items())),
            "cell_keys_by_condition": {
                key: sorted(values)
                for key, values in sorted((cell_keys_by_condition or {}).items())
            },
            "metrics_by_condition": {},
            "comparisons_to_baseline": {},
            "failures": [dict(item) for item in failures],
            "run_id": run_id,
            "command": command,
            "software_version": __version__,
        }
        _atomic_write(destination / "experiment_manifest.json", canonical_json_bytes(manifest))

    def run(
        self,
        *,
        plan: ExperimentPlan,
        data_provider: ExperimentDataProvider,
        inference_provider: ExperimentInferenceProvider,
        output_dir: Path | str,
        continue_on_error: bool = False,
        command: str | None = None,
        resume: bool = False,
        retry_failed: bool = True,
    ) -> ExperimentRunResult:
        destination = Path(output_dir)
        _refuse_official_locations(destination)
        if destination.exists() and not destination.is_dir():
            raise ExperimentPlanError(f"experiment output path is not a directory: {destination}")
        if destination.exists() and any(destination.iterdir()) and not resume:
            raise ExperimentPlanError(
                f"experiment output directory {destination} exists and is not empty; "
                "use resume=True only with a matching checkpoint"
            )
        classification = EvidenceClassification(data_provider.evidence_classification)
        if classification is not EvidenceClassification.SYNTHETIC:
            raise ExperimentPlanError(
                "internal experiment engine accepts synthetic inputs only; "
                "official execution requires gate"
            )
        event_ids = tuple(data_provider.event_ids())
        if not event_ids or any(
            not isinstance(item, str) or not item.strip() or "|" in item for item in event_ids
        ):
            raise ExperimentPlanError("data provider must return nonempty event IDs without '|'")
        if len(event_ids) != len(set(event_ids)):
            raise ExperimentPlanError("data provider returned duplicate event IDs")
        fingerprints = {
            event_id: data_provider.input_sha256(event_id) for event_id in sorted(event_ids)
        }
        for event_id, digest in fingerprints.items():
            _validate_sha256(digest, f"input {event_id}")
        run_id = hashlib.sha256(
            canonical_json_bytes(
                {
                    "plan": plan.to_dict(),
                    "inputs": fingerprints,
                }
            )
        ).hexdigest()[:12]

        # A checkpoint is deliberately a small, canonical JSON object.  It is
        # validated against the current plan and input fingerprints before any
        # cell is skipped; an altered input can therefore never be resumed.
        checkpoint_path = destination / "cell_results.json"
        prior_cells: dict[str, dict[str, float]] = {}
        condition_ids = {condition.condition_id for condition in plan.conditions}
        if resume:
            manifest_path = destination / "experiment_manifest.json"
            if not manifest_path.is_file() or not checkpoint_path.is_file():
                raise ExperimentPlanError(
                    "resume requires experiment_manifest.json and cell_results.json"
                )
            try:
                prior_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise ExperimentPlanError(f"resume checkpoint is unreadable: {exc}") from exc
            if (
                prior_manifest.get("run_id") != run_id
                or prior_manifest.get("plan") != plan.to_dict()
                or prior_manifest.get("input_sha256_by_event") != fingerprints
            ):
                raise ExperimentPlanError(
                    "resume checkpoint does not match plan or input fingerprints"
                )
            recorded_checkpoint_hash = prior_manifest.get("cell_results_sha256")
            if recorded_checkpoint_hash and recorded_checkpoint_hash != _sha256_file(
                checkpoint_path
            ):
                raise ExperimentPlanError("resume cell checkpoint hash does not match manifest")
            if not retry_failed and prior_manifest.get("failures"):
                raise ExperimentPlanError("resume contains failed cells and retry_failed=False")
            if not isinstance(checkpoint, dict) or checkpoint.get("run_id") != run_id:
                raise ExperimentPlanError("resume cell checkpoint identity does not match run")
            raw_cells = checkpoint.get("cells", {})
            if not isinstance(raw_cells, dict):
                raise ExperimentPlanError("resume cell checkpoint has invalid cells")
            for key, value in raw_cells.items():
                if not isinstance(key, str) or not isinstance(value, dict) or not value:
                    raise ExperimentPlanError("resume cell checkpoint contains an invalid cell")
                parts = key.split("|", 2)
                if len(parts) != 3 or parts[0] not in condition_ids:
                    raise ExperimentPlanError(f"resume checkpoint contains unknown cell {key!r}")
                try:
                    checkpoint_seed = int(parts[1])
                except ValueError as exc:
                    raise ExperimentPlanError(
                        f"resume checkpoint contains invalid seed in {key!r}"
                    ) from exc
                if checkpoint_seed not in plan.repeat_seeds or parts[2] not in event_ids:
                    raise ExperimentPlanError(
                        f"resume checkpoint contains out-of-plan cell {key!r}"
                    )
                try:
                    prior_cells[key] = {
                        name: float(metric) for name, metric in value.items()
                    }
                except (TypeError, ValueError) as exc:
                    raise ExperimentPlanError(
                        "resume cell checkpoint contains nonnumeric metrics"
                    ) from exc

        rows: dict[str, list[dict[str, float]]] = {
            condition.condition_id: [] for condition in plan.conditions
        }
        cell_keys: dict[str, set[str]] = {
            condition.condition_id: set() for condition in plan.conditions
        }
        for key, metrics in prior_cells.items():
            condition_id, seed_text, event_id = key.split("|", 2)
            if condition_id not in rows or event_id not in event_ids:
                raise ExperimentPlanError(f"resume checkpoint contains unknown cell {key!r}")
            cell_keys[condition_id].add(key)
            rows[condition_id].append(metrics)
        failures: list[dict[str, Any]] = []
        _atomic_write(
            checkpoint_path,
            canonical_json_bytes(
                {
                    "schema_version": "phase13-cell-checkpoint/1",
                    "run_id": run_id,
                    "cells": prior_cells,
                }
            ),
        )
        # Stable iteration order makes result serialization independent of
        # provider ordering and dictionary insertion behavior.
        for condition in sorted(plan.conditions, key=lambda item: item.condition_id):
            for seed in plan.repeat_seeds:
                for event_id in sorted(event_ids):
                    expected_fingerprint = fingerprints[event_id]
                    cell_key = f"{condition.condition_id}|{seed}|{event_id}"
                    if cell_key in cell_keys[condition.condition_id]:
                        continue
                    try:
                        # Providers may be backed by mutable files.  Re-check the
                        # provider fingerprint after loading so a change between
                        # identity capture and consumption cannot be silently used.
                        event_input = data_provider.load_event(event_id)
                        consumed_fingerprint = data_provider.input_sha256(event_id)
                        if consumed_fingerprint != expected_fingerprint:
                            raise ExperimentPlanError(
                                f"input fingerprint changed during consumption for {event_id}"
                            )
                        # Each call gets its own copy, and a call that edits its input is a
                        # failure: a mutation could otherwise leak into a later condition and
                        # make "identical inputs" untrue.
                        working_copy = copy.deepcopy(event_input)
                        raw_metrics = inference_provider(
                            condition=condition,
                            event_id=event_id,
                            event_input=working_copy,
                            seed=seed,
                        )
                        if working_copy != event_input:
                            raise ExperimentPlanError(
                                f"inference mutated its input for {event_id} under "
                                f"{condition.condition_id}"
                            )
                    except Exception as exc:
                        failure = {
                            "condition_id": condition.condition_id,
                            "event_id": event_id,
                            "seed": seed,
                            "error_type": type(exc).__name__,
                            "detail": str(exc),
                        }
                        failures.append(failure)
                        if continue_on_error:
                            continue
                        self._write_failure_manifest(
                            Path(output_dir),
                            status="FAILED",
                            plan=plan,
                            classification=classification,
                            fingerprints=fingerprints,
                            failures=failures,
                            completed_cells={k: len(v) for k, v in rows.items()},
                            expected_cells=len(event_ids) * len(plan.repeat_seeds),
                            run_id=run_id,
                            reason="inference failed with continue_on_error disabled",
                            command=command,
                cell_keys_by_condition=cell_keys,
                        )
                        raise ExperimentPlanError(
                            f"inference failed for {condition.condition_id}/{event_id}: {exc}"
                        ) from exc
                    if not isinstance(raw_metrics, Mapping) or not raw_metrics:
                        error = ExperimentPlanError(
                            f"inference returned no metrics for {condition.condition_id}/{event_id}"
                        )
                        if continue_on_error:
                            failures.append({
                                "condition_id": condition.condition_id,
                                "event_id": event_id,
                                "seed": seed,
                                "error_type": type(error).__name__,
                                "detail": str(error),
                            })
                            continue
                        raise error
                    normalized: dict[str, float] = {}
                    for name, value in raw_metrics.items():
                        if not isinstance(name, str) or not name.strip():
                            raise ExperimentPlanError("metric names must be nonempty strings")
                        if isinstance(value, bool) or not isinstance(value, (int, float)):
                            error = ExperimentPlanError(f"metric {name} must be numeric")
                            if continue_on_error:
                                failures.append({
                                    "condition_id": condition.condition_id,
                                    "event_id": event_id,
                                    "seed": seed,
                                    "error_type": type(error).__name__,
                                    "detail": str(error),
                                })
                                normalized = {}
                                break
                            raise error
                        if not math.isfinite(float(value)):
                            error = ExperimentPlanError(f"metric {name} must be finite")
                            if continue_on_error:
                                failures.append({
                                    "condition_id": condition.condition_id,
                                    "event_id": event_id,
                                    "seed": seed,
                                    "error_type": type(error).__name__,
                                    "detail": str(error),
                                })
                                normalized = {}
                                break
                            raise error
                        normalized[name] = float(value)
                    if normalized:
                        rows[condition.condition_id].append(normalized)
                        cell_keys[condition.condition_id].add(cell_key)
                        prior_cells[cell_key] = normalized
                        _atomic_write(
                            checkpoint_path,
                            canonical_json_bytes({
                                "schema_version": "phase13-cell-checkpoint/1",
                                "run_id": run_id,
                                "cells": prior_cells,
                            }),
                        )

        failed_conditions = {failure["condition_id"] for failure in failures}
        metrics_by_condition: dict[str, dict[str, float]] = {}
        for condition_id, metric_rows in sorted(rows.items()):
            if metric_rows and condition_id not in failed_conditions:
                metrics_by_condition[condition_id] = _aggregate_metric_rows(metric_rows)
        baseline = next(c.condition_id for c in plan.conditions if c.role == "baseline")
        expected_cells = len(event_ids) * len(plan.repeat_seeds)
        completed_cells = {key: len(value) for key, value in rows.items()}
        baseline_problem = None
        if baseline in failed_conditions:
            baseline_problem = "baseline has failed runs; comparisons are unavailable"
        elif metrics_by_condition.get(baseline) is None:
            baseline_problem = "baseline has no successful metric rows"
        if baseline_problem is not None:
            self._write_failure_manifest(
                Path(output_dir),
                status="FAILED_BASELINE",
                plan=plan,
                classification=classification,
                fingerprints=fingerprints,
                failures=failures,
                completed_cells=completed_cells,
                expected_cells=expected_cells,
                run_id=run_id,
                reason=baseline_problem,
                command=command,
                cell_keys_by_condition=cell_keys,
            )
            raise ExperimentPlanError(baseline_problem)
        baseline_metrics = metrics_by_condition[baseline]
        comparisons: dict[str, dict[str, float]] = {}
        comparison_status: dict[str, str] = {}
        for condition in sorted(plan.conditions, key=lambda item: item.condition_id):
            if condition.role == "baseline":
                continue
            if condition.condition_id in failed_conditions:
                comparison_status[condition.condition_id] = "unavailable_failed_condition"
                continue
            treatment = metrics_by_condition.get(condition.condition_id)
            if treatment is None:
                comparison_status[condition.condition_id] = "unavailable_no_successful_rows"
                continue
            # Comparable only when treatment and baseline cover the identical
            # event x seed grid; a difference of means over different cells is
            # not a paired contrast.
            if (
                completed_cells[condition.condition_id] != expected_cells
                or completed_cells[baseline] != expected_cells
            ):
                comparison_status[condition.condition_id] = "unavailable_incomplete_coverage"
                continue
            treatment_grid = {
                key.split("|", 1)[1] for key in cell_keys[condition.condition_id]
            }
            baseline_grid = {key.split("|", 1)[1] for key in cell_keys[baseline]}
            if treatment_grid != baseline_grid:
                comparison_status[condition.condition_id] = "unavailable_incompatible_cell_grid"
                continue
            if set(treatment) != set(baseline_metrics):
                # A difference over a partly different metric set is not a comparison.
                comparison_status[condition.condition_id] = "unavailable_incompatible_metrics"
                continue
            comparisons[condition.condition_id] = {
                metric: treatment[metric] - baseline_metrics[metric]
                for metric in sorted(baseline_metrics)
            }
            comparison_status[condition.condition_id] = "available"

        manifest = {
            "schema_version": "phase13-experiment-manifest/1",
            "phase": "13",
            "status": "PARTIAL" if failures else "SYNTHETIC_ENGINEERING_ONLY",
            "evidence_classification": classification.value,
            "empirical_performance_claim": False,
            "authorization_status": "not_authorized",
            "plan": plan.to_dict(),
            "input_sha256_by_event": fingerprints,
            "condition_count": len(plan.conditions),
            "event_count": len(event_ids),
            "repeat_count": len(plan.repeat_seeds),
            "metrics_by_condition": metrics_by_condition,
            "comparisons_to_baseline": comparisons,
            "comparison_status": comparison_status,
            "expected_cells_per_condition": expected_cells,
            "completed_cells_by_condition": dict(sorted(completed_cells.items())),
            "cell_keys_by_condition": {
                key: sorted(values) for key, values in sorted(cell_keys.items())
            },
            "checkpoint": "cell_results.json",
            "resume_supported": True,
            "cell_results_sha256": _sha256_file(checkpoint_path),
            "condition_status": {
                condition.condition_id: (
                    "failed" if condition.condition_id in failed_conditions else "complete"
                )
                for condition in sorted(plan.conditions, key=lambda item: item.condition_id)
            },
            "failures": failures,
            "run_id": run_id,
            "command": command,
            "software_version": __version__,
            "git_commit": git_revision(Path.cwd()),
            "environment": capture_environment(),
        }
        destination.mkdir(parents=True, exist_ok=True)
        _atomic_write(destination / "experiment_manifest.json", canonical_json_bytes(manifest))
        _atomic_write(
            destination / "metrics_by_condition.json", canonical_json_bytes(metrics_by_condition)
        )
        _atomic_write(
            destination / "comparisons_to_baseline.json", canonical_json_bytes(comparisons)
        )
        return ExperimentRunResult(
            status=manifest["status"],
            evidence_classification=classification,
            metrics_by_condition=metrics_by_condition,
            comparisons_to_baseline=comparisons,
            manifest=manifest,
            output_dir=destination,
            failures=tuple(failures),
        )


def _aggregate_metric_rows(rows: Sequence[Mapping[str, float]]) -> dict[str, float]:
    if not rows:
        raise ExperimentPlanError("cannot aggregate an empty metric result set")
    metric_names = set(rows[0])
    if any(set(row) != metric_names for row in rows[1:]):
        raise ExperimentPlanError("inference metric names must match across all repeats/events")
    return {
        name: sum(row[name] for row in rows) / len(rows)
        for name in sorted(metric_names)
    }