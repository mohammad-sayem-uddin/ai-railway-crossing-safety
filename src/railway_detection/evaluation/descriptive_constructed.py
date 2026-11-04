"""Constructed independent-camera descriptive orchestrator; real path fails closed.

Preserves official/synthetic-only gates. It neither opens caches nor publishes
results. A and B estimators remain separate; M4/M5 below classify the unchanged
A trajectory, not an invented translation of exact B angle to legacy labels.
"""

from __future__ import annotations

import hashlib
import json
import re
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
    vision_source_id: str | None = None
    audio_source_id: str | None = None


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
        cohort, separator, identifier = job.event_key.partition("/")
        limits = {"train_events": 23, "no_train_events": 3, "engine_events": 1}
        if (
            cohort not in limits
            or separator != "/"
            or not re.fullmatch(r"event_[0-9]{3}", identifier)
            or not 1 <= int(identifier[6:]) <= limits[cohort]
        ):
            raise ValueError("qualified documented cohort event required")
        for source in (job.vision_source_id, job.audio_source_id):
            if source is not None and (
                type(source) is not str or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_:.-]*", source)
            ):
                raise ValueError("explicit neutral constructed source identity required")
        if job.vision_source_id is not None and job.vision_source_id == job.audio_source_id:
            raise ValueError("vision/audio source identities must be distinct")
        if (condition[1] == "VISION" and job.audio_source_id is not None) or (
            condition[1] == "AUDIO_PERCEPTUAL_ONLY" and job.vision_source_id is not None
        ):
            raise ValueError("source binding outside selected modality scope")
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
        rows = json.loads(job.request.batch.inputs_json)
        for raw in rows:
            f = _frame(raw)
            if condition[1] == "VISION" and f.audio_records:
                raise ValueError("audio in vision-only condition")
            if condition[1] == "AUDIO_PERCEPTUAL_ONLY" and f.vision_records:
                raise ValueError("vision in audio-only condition")
            permitted_sources = {
                x for x in (job.vision_source_id, job.audio_source_id) if x is not None
            }
            for evidence in f.vision_records:
                if (
                    evidence.source_id != job.vision_source_id
                    or evidence.modality.value != "vision"
                ):
                    raise ValueError("exact vision source/modality binding mismatch")
            for evidence in f.audio_records:
                if evidence.source_id != job.audio_source_id or evidence.modality.value != "audio":
                    raise ValueError("exact audio source/modality binding mismatch")
            for name in (
                "source_availability",
                "active_sources",
                "missing_sources",
                "source_health",
                "health_reasons",
                "observation_ages",
            ):
                if not set(getattr(f, name)) <= permitted_sources:
                    raise ValueError("source metadata outside exact condition binding")
        b = run_pipeline(job.request)
        body = json.dumps(asdict(job), sort_keys=True, separators=(",", ":"), allow_nan=False)
        input_digest = hashlib.sha256(body.encode()).hexdigest()
        receipt = {
            "event_key": job.event_key,
            "camera": job.camera,
            "condition": job.condition,
            "input_digest": input_digest,
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
        reason: str | None
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
                "synthetic:descriptive:" + input_digest,
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
                "synthetic:descriptive:" + input_digest,
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
