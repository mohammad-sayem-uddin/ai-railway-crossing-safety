"""Synchronized multimodal evidence timeline generator for audit and research visualization."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from railway_detection.fusion.collector import MultimodalFrame
from railway_detection.simulation.runner import SimulationRunResult


def generate_event_timeline(
    sim_result: SimulationRunResult, frames: list[MultimodalFrame]
) -> list[dict[str, Any]]:
    """Build a complete 9-column synchronized timeline record for an event replay."""
    frame_map = {round(f.master_timestamp_s, 3): f for f in frames}
    timeline_records: list[dict[str, Any]] = []

    for step in sim_result.steps:
        t_key = round(step.timestamp_s, 3)
        frame = frame_map.get(t_key)

        front_dets: list[dict[str, Any]] = []
        back_dets: list[dict[str, Any]] = []
        audio_dets: list[dict[str, Any]] = []

        if frame is not None:
            for vr in frame.vision_records:
                if vr.available:
                    target_list = front_dets if ("camera_1" in vr.source_id or "front" in vr.source_id) else back_dets
                    for d in vr.detections:
                        target_list.append({"label": d.label, "confidence": round(d.confidence, 4)})

            for ar in frame.audio_records:
                if ar.available:
                    for d in ar.detections:
                        audio_dets.append({
                            "label": d.label,
                            "confidence": round(d.confidence, 4),
                            "safety_role": ar.metadata.get("audio_safety_role", "supporting_only"),
                        })

        timeline_records.append({
            "timestamp_s": round(step.timestamp_s, 3),
            "front_camera_evidence": front_dets,
            "back_camera_evidence": back_dets,
            "audio_evidence": audio_dets,
            "temporal_evidence": {
                "has_front": bool(front_dets),
                "has_back": bool(back_dets),
                "has_audio": bool(audio_dets),
            },
            "fusion_state": {
                "active_sources": list(frame.active_sources) if frame else [],
                "missing_sources": list(frame.missing_sources) if frame else [],
                "fault_status": step.decision.fault_status,
            },
            "decision": {
                "rule_id": step.decision.rule_id,
                "previous_state": step.decision.previous_state,
                "resulting_state": step.decision.resulting_state,
                "explanation": step.decision.explanation,
            },
            "crossing_state": step.crossing_state,
            "gate_state": {
                "state": step.gate_state,
                "angle_deg": round(step.gate_angle_deg, 2),
                "is_passage_blocked": step.is_passage_blocked,
            },
            "synchronization_status": "EXPLORATORY_UNVERIFIED_ZERO_OFFSET",
            "r04_compliance": "UNRESOLVED_REQUIRES_EMPIRICAL_CALIBRATION",
        })

    return timeline_records


def export_timeline_json(timeline: list[dict[str, Any]], output_path: Path | str) -> Path:
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(timeline, indent=2), encoding="utf-8")
    return out


def export_timeline_csv(timeline: list[dict[str, Any]], output_path: Path | str) -> Path:
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "timestamp_s",
        "front_camera_evidence",
        "back_camera_evidence",
        "audio_evidence",
        "temporal_evidence",
        "fusion_state",
        "decision",
        "crossing_state",
        "gate_state",
        "synchronization_status",
        "r04_compliance",
    ]
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for rec in timeline:
            writer.writerow({
                "timestamp_s": rec["timestamp_s"],
                "front_camera_evidence": json.dumps(rec["front_camera_evidence"]),
                "back_camera_evidence": json.dumps(rec["back_camera_evidence"]),
                "audio_evidence": json.dumps(rec["audio_evidence"]),
                "temporal_evidence": json.dumps(rec["temporal_evidence"]),
                "fusion_state": json.dumps(rec["fusion_state"]),
                "decision": json.dumps(rec["decision"]),
                "crossing_state": rec["crossing_state"],
                "gate_state": json.dumps(rec["gate_state"]),
                "synchronization_status": rec.get("synchronization_status", "EXPLORATORY_UNVERIFIED_ZERO_OFFSET"),
                "r04_compliance": rec.get("r04_compliance", "UNRESOLVED_REQUIRES_EMPIRICAL_CALIBRATION"),
            })
    return out
