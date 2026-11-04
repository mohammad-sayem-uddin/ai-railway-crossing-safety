"""Constructed independent-camera descriptive orchestrator; real path fails closed.

Preserves official/synthetic-only gates. It neither opens caches nor publishes
results. A and B estimators remain separate; M4/M5 below classify the unchanged
A trajectory, not an invented translation of exact B angle to legacy labels.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass

from railway_detection.evaluation.metrics import (
    DescriptiveMetricRow,
    classify_m4,
    summarize_descriptive_rows,
)
from railway_detection.simulation.runner import EventSimulationRunner
from railway_detection.synthetic.convention_b_pipeline import (
    IntegrationRequest,
    _frame,
    _fresh,
    run_pipeline,
)

CONDITIONS = {
    "B0_front": ("front", "VISION"),
    "B2_front": ("front", "VISION_AUDIO"),
    "B0_back": ("back", "VISION"),
    "B1_audio": ("front", "AUDIO_PERCEPTUAL_ONLY"),
}


@dataclass(frozen=True)
class ConstructedDescriptiveJob:
    event_key: str
    camera: str
    condition: str
    request: IntegrationRequest
    constructed_t4_us: int | None
    boundary_evidence: str = "CONSTRUCTED_EXPECTED_CLOCK"


def run_constructed_descriptive(
    jobs: tuple[ConstructedDescriptiveJob, ...], *, expected_controller_json: str
):
    if type(jobs) is not tuple:
        raise ValueError("explicit constructed immutable jobs required")
    receipts, metric_rows, seen = [], [], set()
    for job in jobs:
        if (
            type(job) is not ConstructedDescriptiveJob
            or type(job.request) is not IntegrationRequest
        ):
            raise ValueError("typed constructed job/request required")
        condition = CONDITIONS.get(job.condition)
        if condition is None or condition[0] != job.camera:
            raise ValueError("unadopted/deferred/stateless/fused condition; no silent legacy label")
        key = (job.event_key, job.camera, job.condition)
        if key in seen:
            raise ValueError("duplicate event/camera/condition")
        seen.add(key)
        if job.boundary_evidence != "CONSTRUCTED_EXPECTED_CLOCK":
            raise ValueError("real or purported human evidence cannot enter constructed path")
        if job.constructed_t4_us is not None and (
            type(job.constructed_t4_us) is not int or job.constructed_t4_us < 0
        ):
            raise ValueError("exact constructed local T4 or explicit missing required")
        if job.request.controller_json != expected_controller_json:
            raise ValueError("frozen controller settings mismatch")
        if json.loads(expected_controller_json)["kind"] != "CURRENT_ENGINE":
            raise ValueError("actual current decision engine required for condition replay")
        b = run_pipeline(job.request)
        rows = json.loads(job.request.batch.inputs_json)
        for raw in rows:
            f = _frame(raw)
            if condition[1] == "VISION" and f.audio_records:
                raise ValueError("audio in vision-only condition")
            if condition[1] == "AUDIO_PERCEPTUAL_ONLY" and f.vision_records:
                raise ValueError("vision in audio-only condition")
            for evidence in f.vision_records:
                if job.camera not in evidence.source_id:
                    raise ValueError("camera/source mismatch; no cross-camera clock merge")
        body = json.dumps(asdict(job), sort_keys=True, separators=(",", ":"), allow_nan=False)
        receipt = {
            "event_key": job.event_key,
            "camera": job.camera,
            "condition": job.condition,
            "input_digest": hashlib.sha256(body.encode()).hexdigest(),
            "classification": "CONSTRUCTED_ONLY_NOT_REAL_EVALUATION",
            "B_status": b.status,
            "B_endpoint_seconds": str(b.causal.endpoint_seconds),
            "B_continuous_seconds": str(b.causal.continuous_seconds),
            "B_report_endpoint_seconds": str(b.causal.report_endpoint_seconds),
            "M4_M5_trajectory": "A_unchanged_legacy_semantics",
            "controller_calls_B": b.controller_calls,
        }
        if condition[1] == "AUDIO_PERCEPTUAL_ONLY":
            receipt["gate_metrics"] = "NOT_APPLICABLE_AUDIO_SUPPORT_ONLY"
            receipt["supplied_audio_records"] = sum(len(x["frame"]["audio_records"]) for x in rows)
            receipts.append(receipt)
            continue
        if b.status not in ("EMPTY", "COMPLETE"):
            m4 = m5 = None
            reason = "incomplete_constructed_replay"
        else:
            frames = [_frame(rows[x.input_index]) for x in b.decisions]
            a = EventSimulationRunner(_fresh(expected_controller_json)).run_frames(
                frames, preserve_arrival_order=True
            )
            # A has no arbitrary cutoff extension; do not invent a completed A trajectory.
            t4 = None if job.constructed_t4_us is None else job.constructed_t4_us / 1_000_000
            outcome = classify_m4(a, t4)
            m4, m5, reason = outcome.premature, outcome.never_protected, outcome.reason
            receipt["A_closed_duration_s"] = a.closed_duration_s
            receipt["A_total_duration_s"] = a.total_duration_s
        metric_rows.append(
            DescriptiveMetricRow(
                job.event_key,
                job.camera,
                job.condition,
                "M4",
                m4,
                reason or ("never_protected_companion" if m4 is None else None),
                "synthetic:descriptive:" + receipt["input_digest"],
            )
        )
        metric_rows.append(
            DescriptiveMetricRow(
                job.event_key,
                job.camera,
                job.condition,
                "M5",
                None if m5 is None else int(m5),
                reason if m5 is None else None,
                "synthetic:descriptive:" + receipt["input_digest"],
            )
        )
        receipts.append(receipt)
    return {
        "classification": "CONSTRUCTED_ONLY_NOT_REAL_EVALUATION",
        "runs": tuple(receipts),
        "metrics": summarize_descriptive_rows(tuple(metric_rows)),
        "no_population_claim": True,
        "official_eligibility": False,
    }


def run_real_descriptive(*args, **kwargs):
    raise PermissionError(
        "Real descriptive execution requires canonical scoped grants, "
        "actual promoted GT, resource binding and separately verified live adapter"
    )
