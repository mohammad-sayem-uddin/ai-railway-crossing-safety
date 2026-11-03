"""Reproducible, claim-disciplined benchmark reports for Phase 14.

``benchmark.py`` supplies the measurement procedure. This module wraps it with what a
reproducible record needs: the exact code revision, artifact fingerprints (frozen config,
decision policy, checkpoints -- raw *and* canonical hashes), host/dependency details,
per-stage per-frame latency, throughput, memory high-water marks, an output
fingerprint, an explicit input classification, and a stated list of limitations.

Rules enforced here (each has a regression test):

* Inputs are classified ``synthetic`` or ``real``. Synthetic runs are never empirical
  railway performance. ``real`` requires provenance, and still is not safety evidence.
* A checkpoint whose bytes differ from the frozen configuration's pinned hash makes the
  report ``fingerprints_verified: false`` and invalidates any target-hardware claim.
* ``real_time_claim_permitted`` is true only when ALL hold: real inputs, a documented
  acceptance criterion, a declared target platform that equals the measuring host, enough
  samples, and the observed statistic within the criterion. Otherwise measured values are
  reported with no compliance claim.
* Timing values must be finite and non-negative; anything else aborts the report.
* Optimizations are judged by ``check_candidate_equivalence``: identical input set,
  identical outputs byte-for-byte, and caller-supplied property checks -- never merely
  "ran without error".

Nothing here changes weights, thresholds or the frozen configuration.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import math
import os
import platform
import resource
import subprocess
import sys
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from railway_detection.experiments.frozen_config import (
    compute_canonical_config_hash,
    load_frozen_config,
)
from railway_detection.optimization.benchmark import (
    ACCEPTANCE_STATISTICS,
    INPUT_CLASSIFICATIONS,
    MIN_TARGET_EVIDENCE_SAMPLES,
    BenchmarkProtocol,
    BenchmarkProtocolError,
    _target_match,
    host_fingerprint,
)
from railway_detection.optimization.profiler import StageProfiler
from railway_detection.safety.media_guard import require_media_authorization

REPORT_SCHEMA = "phase14-benchmark-report/2"
TRACKED_PACKAGES = ("torch", "ultralytics", "numpy", "opencv-python", "PyYAML", "Pillow")

LIMITATIONS = (
    "Wall-clock timings of the wrapped callables on the measuring host only.",
    "Percentiles are sample statistics, not worst-case execution-time bounds.",
    "Synthetic inputs exercise code paths; they say nothing about railway scenes.",
    "No safety, real-time or deployment claim follows from this report.",
    "Process peak RSS is a lifetime high-water mark and includes model loading.",
)


# --------------------------------------------------------------------------- environment


def _sysctl(name: str) -> str | None:
    try:
        out = subprocess.run(
            ["sysctl", "-n", name], capture_output=True, text=True, check=False, timeout=5
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip() or None if out.returncode == 0 else None


def _cpu_model() -> str:
    if sys.platform == "darwin":
        return _sysctl("machdep.cpu.brand_string") or platform.processor() or "unknown"
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.lower().startswith("model name"):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor() or "unknown"


def _ram_bytes() -> int | None:
    if sys.platform == "darwin":
        raw = _sysctl("hw.memsize")
        return int(raw) if raw and raw.isdigit() else None
    try:
        return int(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES"))
    except (ValueError, OSError, AttributeError):
        return None


def _accelerators() -> dict[str, Any]:
    """Accelerator availability, without forcing a torch import to succeed."""
    try:
        import torch  # noqa: PLC0415 - optional heavy dependency

        mps = getattr(torch.backends, "mps", None)
        return {
            "torch_importable": True,
            "cuda_available": bool(torch.cuda.is_available()),
            "cuda_device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
            "mps_available": bool(mps and mps.is_available()),
        }
    except Exception as exc:  # noqa: BLE001 - recorded, never fatal
        return {"torch_importable": False, "error": f"{type(exc).__name__}: {exc}"}


def _git(root: Path, *args: str) -> str | None:
    try:
        out = subprocess.run(
            ["git", *args], cwd=root, capture_output=True, text=True, check=False, timeout=30
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip() if out.returncode == 0 else None


def collect_host_environment(root: Path | str) -> dict[str, Any]:
    """Everything needed to say *where* and *with what* a number was measured."""
    base = Path(root).resolve()
    status = _git(base, "status", "--porcelain")
    packages: dict[str, str | None] = {}
    for name in TRACKED_PACKAGES:
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    return {
        **host_fingerprint(),
        "cpu_model": _cpu_model(),
        "ram_bytes": _ram_bytes(),
        "accelerators": _accelerators(),
        "python_implementation": platform.python_implementation(),
        "python_executable": sys.executable,
        "packages": packages,
        "code_revision": _git(base, "rev-parse", "HEAD"),
        "worktree_dirty": bool(status) if status is not None else None,
        "dirty_entry_count": len(status.splitlines()) if status else 0,
    }


# ------------------------------------------------------------------------- fingerprints


def _sha256_file(path: Path) -> str:
    require_media_authorization(path, "HASH_RAW_MEDIA")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def artifact_fingerprints(
    root: Path | str,
    *,
    config_path: str = "configs/frozen_experiment_v1.yaml",
    policy_path: str = "configs/decision_policy_v1.yaml",
) -> dict[str, Any]:
    """Raw-file and canonical-content hashes of config/policy, and checkpoint verification.

    The two hash conventions are both recorded because they answer different questions:
    the raw hash identifies bytes; the canonical hash identifies parsed content and is
    what the frozen-config safeguards and Phase 5 reports cite.
    """
    base = Path(root).resolve()
    config_file, policy_file = base / config_path, base / policy_path
    config = load_frozen_config(config_file)
    policy = yaml.safe_load(policy_file.read_text(encoding="utf-8"))
    checkpoints: dict[str, Any] = {}
    for label, entry in (
        ("vision", config.checkpoints.vision),
        ("audio_v3", config.checkpoints.audio_v3),
    ):
        path = base / entry.path
        actual = _sha256_file(path) if path.is_file() else None
        checkpoints[label] = {
            "path": entry.path,
            "expected_sha256": entry.expected_sha256,
            "actual_sha256": actual,
            "matches_frozen_config": actual == entry.expected_sha256,
        }
    prohibited = config.checkpoints.prohibited_audio_v2
    checkpoints["prohibited_audio_v2_used"] = any(
        item["actual_sha256"] == prohibited.sha256
        for item in checkpoints.values()
        if isinstance(item, dict)
    )
    return {
        "frozen_config": {
            "path": config_path,
            "raw_sha256": _sha256_file(config_file),
            "canonical_sha256": config.canonical_hash,
        },
        "decision_policy": {
            "path": policy_path,
            "raw_sha256": _sha256_file(policy_file),
            "canonical_sha256": compute_canonical_config_hash(policy),
        },
        "checkpoints": checkpoints,
        "verified": all(
            item["matches_frozen_config"] for item in checkpoints.values() if isinstance(item, dict)
        )
        and not checkpoints["prohibited_audio_v2_used"],
    }


# ---------------------------------------------------------------------- staged measurement


def _finite_nonneg(value: float, what: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise BenchmarkProtocolError(f"{what} must be a number, got {value!r}")
    if not math.isfinite(value) or value < 0:
        raise BenchmarkProtocolError(f"{what} must be finite and non-negative, got {value!r}")
    return float(value)


def canonical_output_bytes(value: Any) -> bytes:
    """Deterministic serialization used for output fingerprints."""
    if isinstance(value, bytes):
        return value
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=_reject
    ).encode()


def _reject(obj: Any) -> Any:
    raise BenchmarkProtocolError(
        f"output of type {type(obj).__name__} has no canonical serialization; "
        "provide a serializer"
    )


def _summary(samples: Sequence[float]) -> dict[str, float | int]:
    profiler = StageProfiler()
    for value in samples:
        profiler.record("x", _finite_nonneg(value, "timing sample"))
    return profiler.summarize()["x"].to_dict()


@dataclass(frozen=True)
class InputDescription:
    classification: str
    description: str
    provenance: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.classification not in INPUT_CLASSIFICATIONS:
            raise BenchmarkProtocolError(
                f"input classification must be one of {INPUT_CLASSIFICATIONS}"
            )
        if not isinstance(self.description, str) or not self.description.strip():
            raise BenchmarkProtocolError("input description is required")
        if self.provenance is not None and not isinstance(self.provenance, Mapping):
            raise BenchmarkProtocolError("input provenance must be a mapping when supplied")
        if self.classification == "real":
            if not self.provenance:
                raise BenchmarkProtocolError(
                    "real inputs require provenance (e.g. manifest hash); none was given"
                )
            # A source label alone is not provenance.  Require at least one
            # stable locator/digest so the report can be reproduced later.
            stable_keys = {
                "manifest_sha256",
                "capture_session_manifest_sha256",
                "source_sha256_by_event",
                "manifest_path",
            }
            if not stable_keys.intersection(self.provenance):
                raise BenchmarkProtocolError(
                    "real input provenance needs a manifest/source digest or manifest_path"
                )
            manifest_sha = self.provenance.get("manifest_sha256")
            if manifest_sha is not None and (
                not isinstance(manifest_sha, str)
                or len(manifest_sha) != 64
                or any(char not in "0123456789abcdefABCDEF" for char in manifest_sha)
            ):
                raise BenchmarkProtocolError(
                    "manifest_sha256 must be a 64-character hexadecimal digest"
                )

    def to_dict(self) -> dict[str, Any]:
        provenance = dict(self.provenance) if self.provenance else None
        if self.classification == "synthetic":
            provenance_status = "not_applicable"
            evidence_boundary = "synthetic_code_path_measurement_only"
        elif provenance and provenance.get("verified") is True:
            provenance_status = "declared_verified_not_independently_verified"
            evidence_boundary = "real_input_engineering_measurement_not_safety_evidence"
        else:
            provenance_status = "declared_unverified"
            evidence_boundary = "real_input_source_declared_but_not_independently_verified"
        return {
            "classification": self.classification,
            "description": self.description,
            "provenance": provenance,
            "provenance_status": provenance_status,
            "evidence_boundary": evidence_boundary,
            "empirical_railway_performance": False,
        }


def assess_acceptance(
    latency: Mapping[str, float | int],
    protocol: BenchmarkProtocol,
    *,
    target_evidence: bool,
    inputs: InputDescription,
) -> dict[str, Any]:
    """Compare the observed statistic with a *documented* criterion -- descriptively.

    ``claim_permitted`` additionally needs target-hardware evidence and real inputs; a
    criterion alone never licenses a claim.
    """
    criterion = protocol.acceptance_criterion
    if criterion is None:
        return {
            "status": "not_assessed_no_documented_criterion",
            "claim_permitted": False,
            "claim_blockers": ["no documented acceptance criterion"],
            "note": "No acceptance criterion is documented; measured values stand alone.",
        }
    stat, limit = criterion["statistic"], float(criterion["limit_ms"])
    observed = float(latency[stat])
    within = observed <= limit
    claim = bool(within and target_evidence and inputs.classification == "real")
    blockers = []
    if not target_evidence:
        blockers.append("not target-hardware evidence")
    if inputs.classification != "real":
        blockers.append("inputs are synthetic")
    return {
        "status": "observed_within_criterion" if within else "observed_exceeds_criterion",
        "statistic": stat,
        "limit_ms": limit,
        "observed_ms": observed,
        "criterion_documented_in": criterion["documented_in"],
        "claim_permitted": claim,
        "claim_blockers": blockers,
        "note": "Descriptive comparison of a sample statistic; not a worst-case bound.",
    }


def run_staged_benchmark(
    name: str,
    stages: Sequence[tuple[str, Callable[[Any], Any]]],
    inputs: Sequence[Any],
    protocol: BenchmarkProtocol,
    description: InputDescription,
    *,
    root: Path | str,
    clock: Callable[[], float] = time.perf_counter,
    host: Mapping[str, Any] | None = None,
    serializer: Callable[[Any], bytes] = canonical_output_bytes,
    fingerprints: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Time each stage per input and assemble a full report.

    One *item* = one pass of every stage over one input. Warm-up passes run over the same
    inputs and are discarded. The output fingerprint covers the final stage's output for
    every input, in order, from the first measured repetition; later repetitions must
    reproduce it exactly or the benchmark aborts (a non-deterministic workload cannot be
    fingerprinted).
    """
    if not stages or any(not callable(fn) for _, fn in stages):
        raise BenchmarkProtocolError("stages must be a nonempty sequence of (name, callable)")
    if len({n for n, _ in stages}) != len(stages):
        raise BenchmarkProtocolError("stage names must be unique")
    if not inputs:
        raise BenchmarkProtocolError("at least one input is required")
    observed_host = dict(host) if host is not None else host_fingerprint()

    def one_item(item: Any, record: dict[str, list[float]] | None) -> Any:
        value = item
        item_start = clock()
        for stage_name, fn in stages:
            start = clock()
            value = fn(value)
            end = clock()
            if record is not None:
                record.setdefault(stage_name, []).append(
                    _finite_nonneg((end - start) * 1000.0, f"{stage_name} duration")
                )
        item_end = clock()
        if record is not None:
            record.setdefault("item_total", []).append(
                _finite_nonneg((item_end - item_start) * 1000.0, "item duration")
            )
        return value

    for _ in range(protocol.warmup_iterations):
        for item in inputs:
            one_item(item, None)

    samples: dict[str, list[float]] = {}
    fingerprints_by_repetition: list[str] = []
    wall_ms: list[float] = []
    for _ in range(protocol.repetitions):
        digest = hashlib.sha256()
        rep_start = clock()
        for _ in range(protocol.measured_iterations):
            for index, item in enumerate(inputs):
                output = one_item(item, samples)
                digest.update(f"{index}:".encode() + hashlib.sha256(serializer(output)).digest())
        wall_ms.append(_finite_nonneg((clock() - rep_start) * 1000.0, "repetition wall time"))
        fingerprints_by_repetition.append(digest.hexdigest())
    if len(set(fingerprints_by_repetition)) != 1:
        raise BenchmarkProtocolError(
            "workload output differs between repetitions; refusing to fingerprint it"
        )

    frames = protocol.repetitions * protocol.measured_iterations * len(inputs)  # items
    total_wall_s = sum(wall_ms) / 1000.0
    latency = {stage: _summary(values) for stage, values in samples.items()}
    matches, mismatches = _target_match(protocol.target_platform, observed_host)
    item_stats = latency["item_total"]
    target_evidence = bool(
        matches and item_stats["sample_count"] >= MIN_TARGET_EVIDENCE_SAMPLES
    )
    fp = dict(fingerprints) if fingerprints is not None else artifact_fingerprints(root)
    target_evidence = target_evidence and bool(fp.get("verified", False))
    acceptance = assess_acceptance(
        item_stats, protocol, target_evidence=target_evidence, inputs=description
    )
    peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return {
        "report_type": "phase14_benchmark_report",
        "schema_version": REPORT_SCHEMA,
        "benchmark": name,
        "protocol": protocol.to_dict(),
        "inputs": {**description.to_dict(), "input_count": len(inputs)},
        "environment": collect_host_environment(root) if host is None else dict(observed_host),
        "fingerprints": fp,
        "fingerprints_verified": bool(fp.get("verified", False)),
        "stage_latency_ms": latency,
        "item_count": frames,
        "throughput_items_per_s": frames / total_wall_s if total_wall_s > 0 else None,
        "repetition_wall_ms": wall_ms,
        "memory": {
            "process_peak_rss_bytes": int(peak_rss * (1 if sys.platform == "darwin" else 1024)),
            "note": LIMITATIONS[4],
        },
        "output_fingerprint_sha256": fingerprints_by_repetition[0],
        "target_platform_declared": protocol.target_platform is not None,
        "host_matches_declared_target": matches,
        "target_mismatches": mismatches,
        "is_target_hardware_evidence": target_evidence,
        "acceptance": acceptance,
        "real_time_claim_permitted": bool(acceptance["claim_permitted"]),
        "is_safety_evidence": False,
        "limitations": list(LIMITATIONS),
    }


# --------------------------------------------------------------- equivalence for optimizations


def check_candidate_equivalence(
    reference: Callable[[Any], Any],
    candidate: Callable[[Any], Any],
    inputs: Sequence[Any],
    *,
    property_checks: Mapping[str, Callable[[Any, Any], bool]] | None = None,
    serializer: Callable[[Any], bytes] = canonical_output_bytes,
) -> dict[str, Any]:
    """Judge a candidate optimization against its baseline on the SAME input set.

    Accepted only if, for every input: both run without error, the serialized outputs are
    byte-identical, and every named ``property_check(reference_out, candidate_out)`` holds.
    A candidate identical to the reference is refused as evidence (it proves nothing).
    """
    if not inputs:
        raise BenchmarkProtocolError("equivalence requires at least one input")
    input_digest = hashlib.sha256(
        b"".join(hashlib.sha256(serializer(item)).digest() for item in inputs)
    ).hexdigest()
    checks = dict(property_checks or {})
    failures: list[dict[str, Any]] = []
    for index, item in enumerate(inputs):
        try:
            expected, actual = reference(item), candidate(item)
            expected_bytes, actual_bytes = serializer(expected), serializer(actual)
        except Exception as exc:  # noqa: BLE001 - recorded as a failure
            failures.append({"index": index, "error": f"{type(exc).__name__}: {exc}"})
            continue
        if expected_bytes != actual_bytes:
            pairs = zip(expected_bytes, actual_bytes, strict=False)
            first = next(
                (i for i, (a, b) in enumerate(pairs) if a != b),
                min(len(expected_bytes), len(actual_bytes)),
            )
            failures.append({"index": index, "output_differs_at_byte": first})
            continue
        for label, check in sorted(checks.items()):
            try:
                holds = bool(check(expected, actual))
            except Exception as exc:  # noqa: BLE001
                failures.append({"index": index, "property": label, "error": str(exc)})
                continue
            if not holds:
                failures.append({"index": index, "property": label, "violated": True})
    identical = candidate is reference
    return {
        "report_type": "phase14_equivalence_report",
        "input_count": len(inputs),
        "input_set_sha256": input_digest,
        "property_checks": sorted(checks),
        "candidate_is_reference": identical,
        "equivalent": not failures and not identical,
        "failures": failures,
        "note": (
            "A candidate that is the reference object is not evidence of equivalence."
            if identical
            else "Equivalence holds only for the listed input set and checks."
        ),
    }


# ------------------------------------------------------------- optional vision-model workload


def vision_inference_stage_timings(
    root: Path | str,
    *,
    image_size: tuple[int, int] = (1080, 1920),
    iterations: int = 20,
    warmup: int = 3,
    seed: int = 0,
) -> dict[str, Any]:
    """Time the frozen YOLO checkpoint on a seeded random image, split by Ultralytics stage.

    The input is deterministic noise (``synthetic``): detections are meaningless and no
    accuracy is implied. Ultralytics reports preprocess / inference / postprocess
    milliseconds per image, which this returns as separate distributions. The checkpoint is
    hash-verified against the frozen configuration first and only read, never modified.
    """
    import numpy as np  # noqa: PLC0415

    base = Path(root).resolve()
    fp = artifact_fingerprints(base)
    if not fp["checkpoints"]["vision"]["matches_frozen_config"]:
        raise BenchmarkProtocolError("vision checkpoint differs from the frozen configuration")
    try:
        from ultralytics import YOLO  # noqa: PLC0415
    except ImportError as exc:
        # Recorded, not hidden: no model timing exists when the dependency is unusable.
        return {
            "status": "unavailable",
            "reason": f"ultralytics cannot be imported in this environment: {exc}",
            "input_classification": "synthetic",
            "fingerprints": fp,
        }

    config = load_frozen_config(base / "configs/frozen_experiment_v1.yaml")
    model = YOLO(str(base / config.checkpoints.vision.path))
    rng = np.random.default_rng(seed)
    image = rng.integers(0, 256, size=(*image_size, 3), dtype=np.uint8)
    conf = config.vision.confidence_threshold_approach
    for _ in range(warmup):
        model.predict(image, conf=conf, verbose=False)
    stages: dict[str, list[float]] = {"preprocess": [], "inference": [], "postprocess": []}
    detections = 0
    for _ in range(iterations):
        result = model.predict(image, conf=conf, verbose=False)[0]
        for stage in stages:
            stages[stage].append(_finite_nonneg(float(result.speed[stage]), stage))
        detections += 0 if result.boxes is None else len(result.boxes)
    return {
        "status": "measured",
        "workload": "ultralytics_predict_on_seeded_noise",
        "input_classification": "synthetic",
        "image_size_hw": list(image_size),
        "warmup": warmup,
        "iterations": iterations,
        "confidence_threshold": conf,
        "stage_latency_ms": {name: _summary(values) for name, values in stages.items()},
        "total_detections_on_noise": detections,
        "fingerprints": fp,
        "acceptance_statistic_options": list(ACCEPTANCE_STATISTICS),
    }
