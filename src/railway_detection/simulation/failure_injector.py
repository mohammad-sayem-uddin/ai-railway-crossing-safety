"""Deterministic sensor failure and fault injection engine.

Supports robustness testing and ablation studies (experiments B5–B7) by injecting
sensor dropouts, packet drops, timestamp latency/jitter, out-of-order frames, and false detections.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field, replace
from enum import StrEnum
from typing import Any

from railway_detection.fusion.collector import MultimodalFrame
from railway_detection.fusion.evidence import Detection, EvidenceRecord, Modality
from railway_detection.utils.logging import get_logger

logger = get_logger("simulation.failure_injector")


class FailureMode(StrEnum):
    CAMERA_1_DROPOUT = "camera_1_dropout"
    CAMERA_2_DROPOUT = "camera_2_dropout"
    DUAL_CAMERA_DROPOUT = "dual_camera_dropout"
    AUDIO_DROPOUT = "audio_dropout"
    STALE_TIMESTAMPS = "stale_timestamps"
    OUT_OF_ORDER_FRAMES = "out_of_order_frames"
    FALSE_DETECTION = "false_detection"
    DROPPED_FRAMES = "dropped_frames"


@dataclass
class FailureSchedule:
    """Defines a time-bounded fault injection event."""

    mode: FailureMode
    start_time_s: float = 0.0
    end_time_s: float = float("inf")
    target_source: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)


class FailureInjector:
    """Applies configured failure schedules to a stream of MultimodalFrames."""

    def __init__(self, schedules: list[FailureSchedule] | None = None) -> None:
        self.schedules: list[FailureSchedule] = list(schedules) if schedules is not None else []
        self.last_injection_stats: dict[str, Any] = {
            "total_frames": 0,
            "frames_in_drop_window": 0,
            "dropped_frame_indices": [],
            "dropped_frame_timestamps": [],
            "actual_drop_rate": 0.0,
        }

    def add_schedule(self, schedule: FailureSchedule) -> None:
        self.schedules.append(schedule)

    @staticmethod
    def _validate_stale_timestamps_schedule(
        sched: FailureSchedule, known_sources: set[str] | None = None
    ) -> tuple[float, str]:
        delay_s = sched.parameters.get("delay_s")
        if isinstance(delay_s, bool) or not isinstance(delay_s, (int, float)):
            raise ValueError("STALE_TIMESTAMPS requires numeric delay_s")
        delay_val = float(delay_s)
        if not math.isfinite(delay_val) or delay_val <= 0.0:
            raise ValueError("STALE_TIMESTAMPS requires finite positive delay_s")
        target_source = sched.target_source or sched.parameters.get("target_source")
        if not isinstance(target_source, str) or not target_source.strip():
            raise ValueError("STALE_TIMESTAMPS requires target_source")
        target_source = target_source.strip()
        if known_sources:
            if target_source not in known_sources:
                raise ValueError(
                    f"STALE_TIMESTAMPS unknown target_source '{target_source}'; "
                    f"known sources: {sorted(known_sources)}"
                )
        return delay_val, target_source

    @staticmethod
    def _shift_record_timestamp(record: EvidenceRecord, delay_s: float) -> EvidenceRecord:
        orig_ts = float(record.metadata.get("original_timestamp_s", record.timestamp_s))
        new_meta = dict(record.metadata)
        new_meta["original_timestamp_s"] = orig_ts
        new_meta["stale_timestamp_delay_s"] = delay_s
        return replace(
            record,
            timestamp_s=orig_ts - delay_s,
            metadata=new_meta,
        )

    def inject_failures(self, frames: list[MultimodalFrame]) -> list[MultimodalFrame]:
        """Apply all active failure schedules to the frame list, returning mutated frames."""
        if not self.schedules:
            return list(frames)

        known_sources: set[str] = set()
        for f in frames:
            known_sources.update(r.source_id for r in f.vision_records)
            known_sources.update(r.source_id for r in f.audio_records)
            known_sources.update(f.source_availability.keys())
            known_sources.update(f.active_sources)
            known_sources.update(f.missing_sources)

        for sched in self.schedules:
            if sched.mode == FailureMode.STALE_TIMESTAMPS:
                self._validate_stale_timestamps_schedule(sched, known_sources)

        if not frames:
            return list(frames)

        # Seed PRNG deterministically if drop schedules exist
        drop_scheds = [s for s in self.schedules if s.mode == FailureMode.DROPPED_FRAMES]
        seed = 42
        if drop_scheds and "seed" in drop_scheds[0].parameters:
            seed = int(drop_scheds[0].parameters["seed"])
        rng = random.Random(seed)

        dropped_indices: list[int] = []
        dropped_timestamps: list[float] = []

        mutated_frames: list[MultimodalFrame] = []
        for frame_idx, frame in enumerate(frames):
            t = frame.master_timestamp_s
            active_scheds = [
                s for s in self.schedules if s.start_time_s <= t <= s.end_time_s
            ]

            if not active_scheds:
                mutated_frames.append(frame)
                continue

            # Check if frame itself should be dropped
            active_drop_scheds = [
                s for s in active_scheds if s.mode == FailureMode.DROPPED_FRAMES
            ]
            if active_drop_scheds:
                drop_rate = active_drop_scheds[0].parameters.get("drop_rate", None)
                # When drop_rate is not specified or >= 1.0, drop 100% of frames in active interval (window dropout)
                if drop_rate is None or float(drop_rate) >= 1.0:
                    should_drop = True
                else:
                    should_drop = (rng.random() < float(drop_rate))

                if should_drop:
                    dropped_indices.append(frame_idx)
                    dropped_timestamps.append(t)
                    continue

            new_v_records = list(frame.vision_records)
            new_a_records = list(frame.audio_records)
            new_avail = dict(frame.source_availability)

            for sched in active_scheds:
                if sched.mode == FailureMode.CAMERA_1_DROPOUT:
                    new_v_records = [
                        EvidenceRecord(
                            timestamp_s=r.timestamp_s,
                            source_id=r.source_id,
                            modality=Modality.VISION,
                            available=False,
                            detections=(),
                            metadata=dict(r.metadata),
                        )
                        if "camera_1" in r.source_id or "front" in r.source_id
                        else r
                        for r in new_v_records
                    ]
                    for src in list(new_avail.keys()):
                        if "camera_1" in src or "front" in src:
                            new_avail[src] = False

                elif sched.mode == FailureMode.CAMERA_2_DROPOUT:
                    new_v_records = [
                        EvidenceRecord(
                            timestamp_s=r.timestamp_s,
                            source_id=r.source_id,
                            modality=Modality.VISION,
                            available=False,
                            detections=(),
                            metadata=dict(r.metadata),
                        )
                        if "camera_2" in r.source_id or "rear" in r.source_id
                        else r
                        for r in new_v_records
                    ]
                    for src in list(new_avail.keys()):
                        if "camera_2" in src or "rear" in src:
                            new_avail[src] = False

                elif sched.mode == FailureMode.DUAL_CAMERA_DROPOUT:
                    new_v_records = [
                        EvidenceRecord(
                            timestamp_s=r.timestamp_s,
                            source_id=r.source_id,
                            modality=Modality.VISION,
                            available=False,
                            detections=(),
                            metadata=dict(r.metadata),
                        )
                        for r in new_v_records
                    ]
                    for src in list(new_avail.keys()):
                        if "camera" in src or "vision" in src or "front" in src or "rear" in src:
                            new_avail[src] = False

                elif sched.mode == FailureMode.STALE_TIMESTAMPS:
                    delay_s, target_source = self._validate_stale_timestamps_schedule(
                        sched, known_sources
                    )
                    new_v_records = [
                        self._shift_record_timestamp(r, delay_s)
                        if r.source_id == target_source
                        else r
                        for r in new_v_records
                    ]
                    new_a_records = [
                        self._shift_record_timestamp(r, delay_s)
                        if r.source_id == target_source
                        else r
                        for r in new_a_records
                    ]

                elif sched.mode == FailureMode.AUDIO_DROPOUT:
                    new_a_records = [
                        EvidenceRecord(
                            timestamp_s=r.timestamp_s,
                            source_id=r.source_id,
                            modality=Modality.AUDIO,
                            available=False,
                            detections=(),
                            metadata=dict(r.metadata),
                        )
                        for r in new_a_records
                    ]
                    for src in list(new_avail.keys()):
                        if "audio" in src or "microphone" in src:
                            new_avail[src] = False

                elif sched.mode == FailureMode.FALSE_DETECTION:
                    target_label = sched.parameters.get("label", "front")
                    target_conf = float(sched.parameters.get("confidence", 0.85))
                    new_v_records.append(
                        EvidenceRecord(
                            timestamp_s=t,
                            source_id="camera_1",
                            modality=Modality.VISION,
                            available=True,
                            detections=(Detection(label=target_label, confidence=target_conf),),
                            metadata={"injected_fault": True},
                        )
                    )

            active_sources = tuple(s for s, a in new_avail.items() if a)
            missing_sources = tuple(s for s, a in new_avail.items() if not a)

            mutated_frames.append(
                MultimodalFrame(
                    master_timestamp_s=t,
                    vision_records=tuple(new_v_records),
                    audio_records=tuple(new_a_records),
                    source_availability=new_avail,
                    active_sources=active_sources,
                    missing_sources=missing_sources,
                )
            )

        # Check for OUT_OF_ORDER_FRAMES
        ooo_scheds = [s for s in self.schedules if s.mode == FailureMode.OUT_OF_ORDER_FRAMES]
        if ooo_scheds and len(mutated_frames) >= 2:
            # Swap adjacent frames in window
            for s in ooo_scheds:
                for idx in range(len(mutated_frames) - 1):
                    if s.start_time_s <= mutated_frames[idx].master_timestamp_s <= s.end_time_s:
                        mutated_frames[idx], mutated_frames[idx + 1] = (
                            mutated_frames[idx + 1],
                            mutated_frames[idx],
                        )
                        break

        total_in_drop_window = sum(
            1 for f in frames
            if any(s.start_time_s <= f.master_timestamp_s <= s.end_time_s for s in drop_scheds)
        )
        actual_rate = (len(dropped_indices) / total_in_drop_window) if total_in_drop_window > 0 else 0.0
        self.last_injection_stats = {
            "total_frames": len(frames),
            "frames_in_drop_window": total_in_drop_window,
            "dropped_frame_indices": dropped_indices,
            "dropped_frame_timestamps": dropped_timestamps,
            "actual_drop_rate": actual_rate,
        }

        return mutated_frames
