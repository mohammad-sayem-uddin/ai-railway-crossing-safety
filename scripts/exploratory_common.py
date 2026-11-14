"""Shared read-only exploratory helpers built strictly on verified precomputed caches.

All real-data outputs produced via this module carry the binding qualification:
"Exploratory evaluation against researcher-adopted AI-assisted reference annotations."

Governance & Safety Boundaries Enforced:
- Never opens, probes, hashes, or decodes raw media (.mov/.mp4/.wav/etc.) under data/raw/.
- Reads ONLY precomputed UTF-8 JSON/JSONL/YAML files within the repository root using
  explicit text mode (`newline=""`) and verifies cryptographic SHA-256 digests before use.
- Enforces `data/manifests/phase12_r04_scope_decision.json`: dual-camera fused execution
  (`DUAL_VISION`, `DUAL_VISION_AUDIO`, and `STATELESS_DUAL_*`) fails closed unless
  the event is in the 11 `accepted_sync_events` with `CALIBRATION_SUPPORTED` metadata.
- Leaves canonical Stage-2.1 descriptive replay gates and `CacheOnlyReplayEngine`
  unmodified and unbypassed.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import yaml

from railway_detection.data.sync import SyncAligner
from railway_detection.experiments.frozen_config import load_frozen_config
from railway_detection.fusion.collector import MultimodalEvidenceCollector, MultimodalFrame
from railway_detection.fusion.decision_engine import MultimodalDecisionEngine
from railway_detection.fusion.decision_engine_v2_candidate import (
    MultimodalDecisionEngineV2Candidate,
)
from railway_detection.fusion.evidence import DecisionRecord, Detection, EvidenceRecord, Modality
from railway_detection.fusion.rules import APPROACH_LABELS, CrossingState, GateState, RuleId
from railway_detection.simulation.runner import EventSimulationRunner, SimulationRunResult

EXPLORATORY_LABEL = (
    "Exploratory evaluation against researcher-adopted AI-assisted reference annotations."
)

FORBIDDEN_MEDIA_SUFFIXES = frozenset(
    {".mov", ".mp4", ".avi", ".mkv", ".wav", ".mp3", ".m4a", ".flac", ".aac", ".pt", ".pth"}
)

DEFAULT_REPO_ROOT = Path(__file__).resolve().parents[1]

MANIFEST_PATHS = {
    "replay_manifest": "data/manifests/m3_multimodal_replay_manifest.json",
    "adoption": "docs/generated/professor_evidence/mission43/RESEARCHER_ANNOTATION_ADOPTION.json",
    "r04_scope": "data/manifests/phase12_r04_scope_decision.json",
    "protocol_decision": "data/manifests/phase12_protocol_decision.json",
    "sync_calibration": "data/manifests/camera_sync_offsets_candidate.yaml",
    "frozen_config": "configs/frozen_experiment_v1.yaml",
    "policy_v2": "configs/decision_policy_v2_candidate.yaml",
    "policy_v1": "configs/decision_policy_v1.yaml",
}

KNOWN_SHA256 = {
    "data/manifests/m3_multimodal_replay_manifest.json": "3c720167ea06b67141beb7cf33bd02ce325db62a3e100819f8aa4ad213d5bbbb",
    "data/manifests/phase12_protocol_decision.json": "163cab437e8070eb99e1a64c8596d289becdeb9187afd4909eddefbd53ef9d4e",
    "data/manifests/phase12_r04_scope_decision.json": "f6eabebaab9a925628c119feb9638ba108b7e0c3fbcb942efdf890c2d6e5fc08",
    "configs/frozen_experiment_v1.yaml": "b8ef5da052f002e75a2da0985add02a72d0d5684936263c14257aa12b0c9ac9a",
    "configs/decision_policy_v2_candidate.yaml": "d90828b2ec37169d663c72ab7de7d86600728c0db170ebef3934b9565abaf07f",
    "configs/decision_policy_v1.yaml": "c87c1432f473f84def46d343429c21bcd5329adcbce6cfdf7933de446a0c8575",
}
CANONICAL_POLICY_V2_SHA256 = "143782d15632d2d840e3c3a1d0437a113cd810356d8ce59757d1b6b97f55ea60"

CONDITION_TO_STREAMS: dict[str, tuple[str, ...]] = {
    "B0": ("front_vision",),
    "BACK_VISION": ("back_vision",),
    "AUDIO_ONLY": ("front_audio",),
    "B2": ("front_vision", "front_audio"),  # Canonical B4 in Protocol V2
    "B4": ("front_vision", "front_audio"),  # Alias for Protocol V2 B4 (front + audio)
    "DUAL_VISION": ("front_vision", "back_vision"),
    "DUAL_VISION_AUDIO": ("front_vision", "back_vision", "front_audio"),
}

DUAL_CONDITIONS = frozenset({"DUAL_VISION", "DUAL_VISION_AUDIO"})

ALL_STATELESS_VISION_LABELS = frozenset({"front", "rear", "side", "train"})


class ExploratoryValidationError(RuntimeError):
    """Fail-closed validation error in the exploratory pipeline."""


def resolve_safe_text_path(repo_root: Path, rel_or_abs: str | Path) -> Path:
    """Resolve a path inside `repo_root`, rejecting escapes, raw dirs, and binary media suffixes."""
    root = repo_root.resolve()
    raw = Path(rel_or_abs)
    candidate = (raw if raw.is_absolute() else (root / raw)).resolve()
    try:
        rel = candidate.relative_to(root)
    except ValueError as exc:
        raise ExploratoryValidationError(f"Path escapes repo_root: {rel_or_abs}") from exc
    if "data/raw" in rel.as_posix().split("/") or rel.as_posix().startswith("data/raw"):
        raise ExploratoryValidationError(f"Access to data/raw is strictly prohibited: {rel}")
    if candidate.suffix.lower() in FORBIDDEN_MEDIA_SUFFIXES:
        raise ExploratoryValidationError(f"Media/checkpoint extension prohibited: {rel}")
    if not candidate.exists() or not candidate.is_file():
        raise ExploratoryValidationError(f"Required text artifact missing: {rel}")
    return candidate


def read_verified_utf8_text(
    repo_root: Path,
    rel_path: str | Path,
    *,
    expected_sha256: str | None = None,
) -> tuple[str, str]:
    """Read UTF-8 text without newline translation and verify its SHA-256 digest."""
    resolved = resolve_safe_text_path(repo_root, rel_path)
    with open(resolved, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if expected_sha256 is not None and digest != expected_sha256.lower():
        raise ExploratoryValidationError(
            f"SHA-256 mismatch for {rel_path}: expected {expected_sha256}, got {digest}"
        )
    return text, digest


@dataclass(frozen=True)
class EventReferenceMetadata:
    """Adopted AI-assisted reference annotations and mapped boundaries for one event."""

    event_id: str
    event_key: str
    cohort: str
    event_type: str
    active_proposal_path: str
    active_proposal_sha256: str
    proposal_schema: str
    train_present: bool
    train_direction: str | None
    train_type: str | None
    trailing_cars_count: int | None
    horn_status: str | None
    horn_onset_s: float | None
    lighting: str | None
    weather: str | None
    front_duration_s: float | None
    back_duration_s: float | None
    is_dual_sync_accepted: bool
    calibration_verdict: str
    back_offset_s: float | None
    back_uncertainty_s: float | None
    # Raw observable values in their annotation camera clock (None if unobservable/inapplicable)
    t0_raw_s: float | None
    t0_cam: str | None
    t0_ambiguity: bool
    t1_raw_s: float | None
    t1_cam: str | None
    t2_raw_s: float | None
    t2_cam: str | None
    t3_raw_s: float | None
    t3_cam: str | None
    t4_raw_s: float | None
    t4_cam: str | None

    def boundaries_for_clock(self, clock_mode: str) -> dict[str, float | None]:
        """Return (t0, t1, t2, t3, t4) mapped onto 'front', 'back', or 'master' clocks.

        Never fabricates cross-camera mapping:
        - 'front': maps boundaries annotated on 'front' (offset=0.0); back-annotated -> None
          (unless mapped in 'master' for accepted sync events).
        - 'back': maps boundaries annotated on 'back' (local offset=0.0); front-annotated -> None.
        - 'master': only valid when `is_dual_sync_accepted` and `back_offset_s is not None`;
          front -> +0.0, back -> +back_offset_s.
        """
        offsets: dict[str, float]
        if clock_mode == "front":
            offsets = {"front": 0.0}
        elif clock_mode == "back":
            offsets = {"back": 0.0}
        elif clock_mode == "master":
            if not self.is_dual_sync_accepted or self.back_offset_s is None:
                raise ExploratoryValidationError(
                    f"Master-clock boundary mapping blocked for uncalibrated event {self.event_id}"
                )
            offsets = {"front": 0.0, "back": float(self.back_offset_s)}
        else:
            raise ValueError(f"Unknown clock_mode: {clock_mode}")

        def _map(val: float | None, cam: str | None) -> float | None:
            if val is None or cam is None or cam not in offsets:
                return None
            return round(float(val) + offsets[cam], 6)

        return {
            "t0": _map(self.t0_raw_s, self.t0_cam),
            "t1": _map(self.t1_raw_s, self.t1_cam),
            "t2": _map(self.t2_raw_s, self.t2_cam),
            "t3": _map(self.t3_raw_s, self.t3_cam),
            "t4": _map(self.t4_raw_s, self.t4_cam),
        }


@dataclass(frozen=True)
class VerifiedExploratoryContext:
    """Validated manifests, configs, event reference metadata, and cryptographic digests."""

    repo_root: Path
    manifest_sha256: str
    manifest_events: dict[str, dict[str, Any]]
    event_order: tuple[str, ...]
    accepted_sync_events: frozenset[str]
    references: dict[str, EventReferenceMetadata]
    calibration_events: dict[str, dict[str, Any]]
    frozen_config: Any
    artifact_hashes: dict[str, str]


def load_verified_context(repo_root: Path | None = None) -> VerifiedExploratoryContext:
    """Load and cryptographically verify all manifests, configs, caches, and 27 proposals."""
    root = (repo_root or DEFAULT_REPO_ROOT).resolve()
    hashes: dict[str, str] = {}

    texts_by_key: dict[str, str] = {}
    for key, rel in MANIFEST_PATHS.items():
        text, digest = read_verified_utf8_text(
            root, rel, expected_sha256=KNOWN_SHA256.get(rel)
        )
        hashes[rel] = digest
        texts_by_key[key] = text

    canonical_v2 = hashlib.sha256(
        json.dumps(
            yaml.safe_load(texts_by_key["policy_v2"]), sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()
    if canonical_v2 != CANONICAL_POLICY_V2_SHA256:
        raise ExploratoryValidationError(
            f"Canonical Policy V2 hash mismatch: expected {CANONICAL_POLICY_V2_SHA256}, got {canonical_v2}"
        )

    manifest = json.loads(texts_by_key["replay_manifest"])
    adoption = json.loads(texts_by_key["adoption"])
    scope = json.loads(texts_by_key["r04_scope"])
    calibration = yaml.safe_load(texts_by_key["sync_calibration"])

    if scope.get("decision_status") != "APPROVED":
        raise ExploratoryValidationError("R04 scope decision is not APPROVED")
    accepted_sync = frozenset(scope.get("accepted_sync_events", []))
    if len(accepted_sync) != 11:
        raise ExploratoryValidationError(
            f"Expected 11 accepted_sync_events, found {len(accepted_sync)}"
        )

    manifest_events: dict[str, dict[str, Any]] = {}
    event_order: list[str] = []
    for entry in manifest["events"]:
        ev_id = entry["event_id"]
        for stream_key in ("front", "audio", "back"):
            cache_rel = entry[f"{stream_key}_cache_path"]
            expected_cache_sha = entry[f"{stream_key}_cache_sha256"]
            _, actual_cache_sha = read_verified_utf8_text(
                root, cache_rel, expected_sha256=expected_cache_sha
            )
            hashes[cache_rel] = actual_cache_sha
        manifest_events[ev_id] = entry
        event_order.append(ev_id)

    if len(manifest_events) != 27:
        raise ExploratoryValidationError(f"Expected 27 manifest events, got {len(manifest_events)}")

    references: dict[str, EventReferenceMetadata] = {}
    cal_events = calibration["events"]
    for item in adoption["adopted_active_annotations"]:
        ev_id = item["event"]
        prop_rel = item["active_proposal_path"]
        prop_text, prop_sha = read_verified_utf8_text(
            root, prop_rel, expected_sha256=item["active_proposal_sha256"]
        )
        hashes[prop_rel] = prop_sha
        prop = json.loads(prop_text)

        meta = prop["proposed_train_metadata"]
        env = prop.get("proposed_environmental_conditions", {})
        ts = prop["proposed_timestamps"]
        durs = {
            im["file_name"]: im.get("duration_s")
            for im in prop.get("ai_assistant_metadata", {}).get("input_media_files", [])
        }
        cal_entry = cal_events[ev_id]
        verdict = str(cal_entry.get("calibration_verdict", "UNKNOWN"))
        in_sync_scope = ev_id in accepted_sync
        back_cal = cal_entry.get("camera_back", {})
        raw_offset = back_cal.get("offset_s")
        raw_unc = back_cal.get("uncertainty_s")
        if in_sync_scope:
            if verdict != "CALIBRATION_SUPPORTED" or raw_offset is None or raw_unc is None:
                raise ExploratoryValidationError(
                    f"Accepted sync event {ev_id} failed calibration validation"
                )

        def _extract_ts(name: str) -> tuple[float | None, str | None, bool]:
            node = ts[name]
            val = node.get("value_s")
            obs = bool(node.get("candidate_observable"))
            amb = bool(node.get("ambiguity_flag", False))
            if obs and val is not None:
                return float(val), node.get("reference_camera"), amb
            return None, node.get("reference_camera"), amb

        t0_val, t0_cam, t0_amb = _extract_ts("T0_first_visible")
        t1_val, t1_cam, _ = _extract_ts("T1_danger_zone_entry")
        t2_val, t2_cam, _ = _extract_ts("T2_crossing_occupancy_start")
        t3_val, t3_cam, _ = _extract_ts("T3_locomotive_unit_clearance")
        t4_val, t4_cam, _ = _extract_ts("T4_tail_clearance")

        cohort = ev_id.split("/")[0]
        references[ev_id] = EventReferenceMetadata(
            event_id=ev_id,
            event_key=manifest_events[ev_id]["event_key"],
            cohort=cohort,
            event_type=str(prop.get("event_type")),
            active_proposal_path=prop_rel,
            active_proposal_sha256=prop_sha,
            proposal_schema=str(prop.get("schema_version")),
            train_present=bool(meta.get("train_present")),
            train_direction=meta.get("train_direction"),
            train_type=meta.get("train_type"),
            trailing_cars_count=meta.get("trailing_cars_count"),
            horn_status=meta.get("horn_status"),
            horn_onset_s=meta.get("horn_onset_s"),
            lighting=env.get("lighting"),
            weather=env.get("weather"),
            front_duration_s=durs.get("camera_front.mov"),
            back_duration_s=durs.get("camera_back.mov"),
            is_dual_sync_accepted=in_sync_scope,
            calibration_verdict=verdict,
            back_offset_s=float(raw_offset) if (in_sync_scope and raw_offset is not None) else None,
            back_uncertainty_s=float(raw_unc) if (in_sync_scope and raw_unc is not None) else None,
            t0_raw_s=t0_val,
            t0_cam=t0_cam,
            t0_ambiguity=t0_amb,
            t1_raw_s=t1_val,
            t1_cam=t1_cam,
            t2_raw_s=t2_val,
            t2_cam=t2_cam,
            t3_raw_s=t3_val,
            t3_cam=t3_cam,
            t4_raw_s=t4_val,
            t4_cam=t4_cam,
        )

    if set(references.keys()) != set(manifest_events.keys()):
        raise ExploratoryValidationError("Mismatch between replay manifest events and adoption index")

    frozen_config = load_frozen_config(resolve_safe_text_path(root, MANIFEST_PATHS["frozen_config"]))
    return VerifiedExploratoryContext(
        repo_root=root,
        manifest_sha256=hashes[MANIFEST_PATHS["replay_manifest"]],
        manifest_events=manifest_events,
        event_order=tuple(event_order),
        accepted_sync_events=accepted_sync,
        references=references,
        calibration_events=cal_events,
        frozen_config=frozen_config,
        artifact_hashes=hashes,
    )


def build_sync_aligner_for_event(ctx: VerifiedExploratoryContext, event_id: str) -> SyncAligner:
    """Build a strictly event-scoped SyncAligner for an accepted dual-camera event."""
    if event_id not in ctx.accepted_sync_events:
        raise ExploratoryValidationError(
            f"Event '{event_id}' is NOT in the 11 accepted sync events; dual-camera fusion blocked."
        )
    ref = ctx.references[event_id]
    if ref.calibration_verdict != "CALIBRATION_SUPPORTED" or ref.back_offset_s is None or ref.back_uncertainty_s is None:
        raise ExploratoryValidationError(f"Event '{event_id}' lacks CALIBRATION_SUPPORTED offsets")
    aligner = SyncAligner()
    aligner.add_source("camera_1", offset_s=0.0, uncertainty_s=0.0)
    aligner.add_source(
        "camera_2",
        offset_s=float(ref.back_offset_s),
        uncertainty_s=float(ref.back_uncertainty_s),
    )
    return aligner


def _parse_detections_list(raw_dets: Any) -> tuple[Detection, ...]:
    parsed: list[Detection] = []
    for d in raw_dets:
        label = str(d.get("label") or d.get("class_name") or "").strip()
        if not label:
            raise ExploratoryValidationError(f"Detection missing label/class_name: {d}")
        conf = float(d["confidence"])
        bbox_raw = d.get("bbox_xyxy")
        bbox = tuple(float(x) for x in bbox_raw) if bbox_raw is not None else None
        meta = dict(d.get("metadata", {}))
        if "class_id" in d and "class_id" not in meta:
            meta["class_id"] = d["class_id"]
        parsed.append(Detection(label=label, confidence=conf, bbox_xyxy=bbox, metadata=meta))
    return tuple(parsed)


def load_event_evidence_records(
    ctx: VerifiedExploratoryContext,
    event_id: str,
    condition: str,
) -> tuple[list[EvidenceRecord], SyncAligner | None, str]:
    """Load verified EvidenceRecords + optional SyncAligner + clock mode for (event_id, condition)."""
    if condition not in CONDITION_TO_STREAMS:
        raise ExploratoryValidationError(f"Unsupported condition: {condition}")
    streams = CONDITION_TO_STREAMS[condition]
    entry = ctx.manifest_events[event_id]

    aligner: SyncAligner | None = None
    if condition in DUAL_CONDITIONS:
        aligner = build_sync_aligner_for_event(ctx, event_id)
        clock_mode = "master"
    elif condition == "BACK_VISION":
        clock_mode = "back"
    else:
        clock_mode = "front"

    records: list[EvidenceRecord] = []

    if "front_vision" in streams:
        text, sha = read_verified_utf8_text(
            ctx.repo_root, entry["front_cache_path"], expected_sha256=entry["front_cache_sha256"]
        )
        prov = {"event_id": event_id, "stream": "front_vision", "sha256": sha}
        for line in text.splitlines():
            if not line.strip():
                continue
            raw = json.loads(line)
            ts = float(raw["timestamp_sec"] if "timestamp_sec" in raw else raw["timestamp_s"])
            dets = _parse_detections_list(raw["detections"])
            meta = dict(raw.get("metadata", {}))
            meta["frame_index"] = int(raw.get("frame_index", meta.get("frame_index", 0)))
            meta["provenance"] = prov
            records.append(
                EvidenceRecord(
                    timestamp_s=ts,
                    source_id="camera_1",
                    modality=Modality.VISION,
                    available=bool(raw.get("available", True)),
                    detections=dets,
                    metadata=meta,
                )
            )

    if "back_vision" in streams:
        text, sha = read_verified_utf8_text(
            ctx.repo_root, entry["back_cache_path"], expected_sha256=entry["back_cache_sha256"]
        )
        prov = {"event_id": event_id, "stream": "back_vision", "sha256": sha}
        for line in text.splitlines():
            if not line.strip():
                continue
            raw = json.loads(line)
            ts = float(raw["timestamp_s"] if "timestamp_s" in raw else raw["timestamp_sec"])
            dets = _parse_detections_list(raw["detections"])
            meta = dict(raw.get("metadata", {}))
            meta["provenance"] = prov
            records.append(
                EvidenceRecord(
                    timestamp_s=ts,
                    source_id="camera_2",
                    modality=Modality.VISION,
                    available=bool(raw.get("available", True)),
                    detections=dets,
                    metadata=meta,
                )
            )

    if "front_audio" in streams:
        text, sha = read_verified_utf8_text(
            ctx.repo_root, entry["audio_cache_path"], expected_sha256=entry["audio_cache_sha256"]
        )
        prov = {"event_id": event_id, "stream": "front_audio", "sha256": sha}
        for line in text.splitlines():
            if not line.strip():
                continue
            raw = json.loads(line)
            end_s = float(raw["end_sec"])
            conf = float(raw["horn_confidence"])
            is_horn = bool(raw["is_horn_detected"])
            dets: tuple[Detection, ...] = ()
            if is_horn and conf > 0.0:
                dets = (
                    Detection(
                        label="train_horn",
                        confidence=conf,
                        metadata={
                            "window_index": int(raw["window_index"]),
                            "start_sec": float(raw["start_sec"]),
                        },
                    ),
                )
            records.append(
                EvidenceRecord(
                    timestamp_s=end_s,
                    source_id="audio_1",
                    modality=Modality.AUDIO,
                    available=True,
                    detections=dets,
                    metadata={
                        "window_index": int(raw["window_index"]),
                        "start_sec": float(raw["start_sec"]),
                        "end_sec": end_s,
                        "is_horn_detected": is_horn,
                        "provenance": prov,
                    },
                )
            )

    records.sort(key=lambda r: (r.timestamp_s, str(r.modality.value), r.source_id))
    return records, aligner, clock_mode


def assemble_frames(
    records: list[EvidenceRecord],
    aligner: SyncAligner | None,
    *,
    stride_s: float = 0.2,
    window_tolerance_s: float = 0.5,
) -> list[MultimodalFrame]:
    """Assemble synchronized master-time MultimodalFrames via MultimodalEvidenceCollector."""
    if not records:
        return []
    collector = MultimodalEvidenceCollector(
        sync_aligner=aligner, window_tolerance_s=float(window_tolerance_s)
    )
    for rec in records:
        collector.add_evidence(rec)
    master_times = [
        aligner.to_master(rec.source_id, rec.timestamp_s)
        if (aligner is not None and rec.source_id in aligner.offsets_s)
        else rec.timestamp_s
        for rec in records
    ]
    t_start = min(master_times)
    t_end = max(master_times)
    return collector.generate_frames_from_history(
        start_time_s=t_start, end_time_s=t_end, stride_s=float(stride_s)
    )


class StatelessThresholdEngine:
    """Zero-memory single-tick comparator using identical inputs and calibrated thresholds.

    Isolates the contribution of the temporal finite-state machine (confirmation counters,
    warning dwell, clearance dwell, sensor-health latching):
    - No consecutive confirmation frames (`confirm_frames = 1` equivalent)
    - No warning dwell (`0.0 s`)
    - No clearance dwell (`0.0 s`)
    - Immediate command to OPEN the moment qualifying detection falls below threshold
    - Supports two explicit modes:
      - `allow_audio_trigger=False`: respects RULE_2 (vision threshold 0.35 governs closure;
        audio never triggers independently)
      - `allow_audio_trigger=True`: stateless OR-union (vision >= 0.35 or audio >= 0.3700)
    """

    def __init__(
        self,
        config: Any | None = None,
        *,
        vision_threshold: float = 0.35,
        audio_threshold: float = 0.3700,
        allow_audio_trigger: bool = False,
        fail_safe_on_all_vision_loss: bool = False,
    ) -> None:
        if config is not None:
            self.vision_threshold = float(config.vision.confidence_threshold_approach)
            self.audio_threshold = float(config.audio.operating_threshold)
            self.config = config
        else:
            self.vision_threshold = float(vision_threshold)
            self.audio_threshold = float(audio_threshold)
            self.config = None
        self.allow_audio_trigger = bool(allow_audio_trigger)
        self.fail_safe_on_all_vision_loss = bool(fail_safe_on_all_vision_loss)
        self.current_state = CrossingState.IDLE
        self.current_gate_state = GateState.OPEN
        self.last_master_time_s = -1.0

    def reset(self, initial_time_s: float = 0.0) -> None:
        del initial_time_s
        self.current_state = CrossingState.IDLE
        self.current_gate_state = GateState.OPEN
        self.last_master_time_s = -1.0

    def evaluate_frame(
        self, frame: MultimodalFrame, scenario_run_id: str = "stateless_run"
    ) -> DecisionRecord:
        t = float(frame.master_timestamp_s)
        prev_state = self.current_state
        prev_gate = self.current_gate_state

        if self.last_master_time_s >= 0.0 and t < self.last_master_time_s - 1e-9:
            return DecisionRecord(
                timestamp_s=t,
                scenario_run_id=scenario_run_id,
                previous_state=prev_state.value,
                resulting_state=prev_state.value,
                previous_gate_state=prev_gate.value,
                resulting_gate_state=prev_gate.value,
                rule_id=RuleId.RULE_8_OUT_OF_ORDER_REJECTION.value,
                explanation="Stateless comparator rejected out-of-order frame",
                fault_status="out_of_order",
                source_availability=dict(frame.source_availability),
                source_health=dict(frame.source_health),
                health_reasons=dict(frame.health_reasons),
                observation_ages=dict(frame.observation_ages),
                gate_command=prev_gate.value,
            )

        self.last_master_time_s = t

        vision_detected = any(
            det.label in ALL_STATELESS_VISION_LABELS and det.confidence >= self.vision_threshold
            for rec in frame.vision_records
            if rec.available
            for det in rec.detections
        )
        audio_detected = any(
            det.label in {"train_horn", "horn", "train", "rail"}
            and det.confidence >= self.audio_threshold
            for rec in frame.audio_records
            if rec.available
            for det in rec.detections
        )

        vision_sources_present = any(
            ("camera" in s or "vision" in s)
            for s in frame.source_availability
        )
        any_vision_avail = any(
            avail
            for src, avail in frame.source_availability.items()
            if ("camera" in src or "vision" in src)
        )
        all_vision_failed = vision_sources_present and not any_vision_avail

        ev_refs = tuple(
            f"{r.source_id}:{r.timestamp_s}"
            for r in (*frame.vision_records, *frame.audio_records)
            if r.available and r.detections
        )

        fault_status = "none"
        if self.fail_safe_on_all_vision_loss and all_vision_failed:
            fault_status = "all_vision_failed"
            next_state = CrossingState.FAULT_FAIL_SAFE
            next_gate = GateState.CLOSED
            rule_id = "STATELESS_FAIL_SAFE_CLAMP"
            explanation = "Stateless comparator fail-safe clamp on all-vision loss"
        elif vision_detected or (self.allow_audio_trigger and audio_detected):
            next_state = CrossingState.TRAIN_PRESENT
            next_gate = GateState.CLOSED
            rule_id = "STATELESS_DETECTION_CLOSE"
            explanation = "Stateless single-tick detection triggered immediate CLOSE"
        else:
            next_state = CrossingState.IDLE
            next_gate = GateState.OPEN
            rule_id = "STATELESS_NO_DETECTION_OPEN"
            explanation = "Stateless single-tick absence triggered immediate OPEN"

        self.current_state = next_state
        self.current_gate_state = next_gate
        return DecisionRecord(
            timestamp_s=t,
            scenario_run_id=scenario_run_id,
            previous_state=prev_state.value,
            resulting_state=next_state.value,
            previous_gate_state=prev_gate.value,
            resulting_gate_state=next_gate.value,
            evidence_references=ev_refs,
            rule_id=rule_id,
            explanation=explanation,
            fault_status=fault_status,
            source_availability=dict(frame.source_availability),
            source_health=dict(frame.source_health),
            health_reasons=dict(frame.health_reasons),
            observation_ages=dict(frame.observation_ages),
            gate_command=next_gate.value,
        )


def make_engine(policy: str, config: Any) -> Any:
    """Instantiate decision engine for policy identifier."""
    if policy == "v2":
        return MultimodalDecisionEngineV2Candidate(config=config)
    if policy == "v1":
        return MultimodalDecisionEngine(config=config)
    if policy == "stateless_vision_rule2":
        return StatelessThresholdEngine(config=config, allow_audio_trigger=False)
    if policy == "stateless_union":
        return StatelessThresholdEngine(config=config, allow_audio_trigger=True)
    raise ValueError(f"Unsupported policy: {policy}")


def simulate_frames(
    frames: list[MultimodalFrame],
    *,
    event_id: str,
    scenario_name: str,
    policy: str,
    config: Any,
    entry_time_s: float | None = None,
    clearance_time_s: float | None = None,
    preserve_arrival_order: bool = False,
) -> tuple[SimulationRunResult, Any]:
    """Run frames through EventSimulationRunner using the specified decision policy."""
    engine = make_engine(policy, config)
    runner = EventSimulationRunner(decision_engine=engine, config=config)
    result = runner.run_frames(
        frames=frames,
        event_id=event_id,
        scenario_name=scenario_name,
        entry_time_s=entry_time_s,
        clearance_time_s=clearance_time_s,
        preserve_arrival_order=preserve_arrival_order,
    )
    return result, engine


def serialize_simulation_result(
    res: SimulationRunResult,
    *,
    event_id: str,
    condition: str,
    policy: str,
    clock_mode: str,
    ref: EventReferenceMetadata,
    mapped_bounds: dict[str, float | None],
    window_tolerance_s: float,
    stride_s: float,
) -> dict[str, Any]:
    """Serialize SimulationRunResult into deterministic, self-contained JSON structure."""
    steps_out = [
        {
            "t": round(float(s.timestamp_s), 6),
            "crossing_state": s.crossing_state,
            "gate_state": s.gate_state,
            "gate_angle_deg": round(float(s.gate_angle_deg), 4),
            "is_passage_blocked": bool(s.is_passage_blocked),
            "rule_id": s.decision.rule_id,
            "fault_status": s.decision.fault_status,
            "gate_command": s.decision.gate_command,
            "evidence_refs": list(s.decision.evidence_references),
            "source_availability": dict(sorted(s.decision.source_availability.items())),
            "source_health": dict(sorted(s.decision.source_health.items())),
            "health_reasons": dict(sorted(s.decision.health_reasons.items())),
        }
        for s in res.steps
    ]
    transitions = []
    for s in res.steps:
        if s.decision.previous_state != s.decision.resulting_state:
            transitions.append(
                {
                    "t": round(float(s.timestamp_s), 6),
                    "from": s.decision.previous_state,
                    "to": s.decision.resulting_state,
                    "gate_state": s.gate_state,
                    "rule_id": s.decision.rule_id,
                }
            )
    rule_counts: dict[str, int] = {}
    for s in res.steps:
        rk = s.decision.rule_id or "NONE"
        rule_counts[rk] = rule_counts.get(rk, 0) + 1

    return {
        "exploratory_label": EXPLORATORY_LABEL,
        "convention_note": (
            "Convention A inline discrete-step execution (EventSimulationRunner): "
            "gate steps at tick t immediately after decision at tick t "
            "(canonical +0.20s offset relative to causal Convention B)."
        ),
        "event_id": event_id,
        "event_key": ref.event_key,
        "cohort": ref.cohort,
        "event_type": ref.event_type,
        "condition": condition,
        "policy": policy,
        "clock_mode": clock_mode,
        "is_dual_sync_accepted": ref.is_dual_sync_accepted,
        "back_offset_s": ref.back_offset_s,
        "window_tolerance_s": window_tolerance_s,
        "stride_s": stride_s,
        "mapped_boundaries": mapped_bounds,
        "total_duration_s": round(float(res.total_duration_s), 6),
        "closed_duration_s": round(float(res.closed_duration_s), 6),
        "warning_lead_time_s": (
            round(float(res.warning_lead_time_s), 6)
            if res.warning_lead_time_s is not None
            else None
        ),
        "premature_opening_detected": bool(res.premature_opening_detected),
        "fault_occurred": bool(res.fault_occurred),
        "step_count": len(res.steps),
        "rejected_step_count": len(res.rejected_steps),
        "final_crossing_state": res.steps[-1].crossing_state if res.steps else None,
        "final_gate_state": res.steps[-1].gate_state if res.steps else None,
        "reached_crossing_clear": any(
            s.crossing_state == CrossingState.CROSSING_CLEAR.value for s in res.steps
        ),
        "reached_gate_opening": any(
            s.crossing_state == CrossingState.GATE_OPENING.value for s in res.steps
        ),
        "rule_counts": dict(sorted(rule_counts.items())),
        "transitions": transitions,
        "steps": steps_out,
    }


def deterministic_json_dumps(obj: Any) -> str:
    """Serialize JSON deterministically for bit-for-bit reproducible hashing."""
    return json.dumps(obj, indent=2, sort_keys=True) + "\n"


def write_verified_json(path: Path, payload: Any) -> str:
    """Write deterministic JSON output and return its UTF-8 SHA-256 hex digest."""
    path.parent.mkdir(parents=True, exist_ok=True)
    text = deterministic_json_dumps(payload)
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def wilson_ci_95(k: int, n: int) -> tuple[float, float, float]:
    """Compute exact 95% Wilson score confidence interval (point, lo, hi)."""
    if n <= 0:
        return (0.0, 0.0, 0.0)
    z = 1.959963984540054
    p = k / n
    denom = 1.0 + (z * z) / n
    center = (p + (z * z) / (2.0 * n)) / denom
    half = (z * math.sqrt((p * (1.0 - p) + (z * z) / (4.0 * n)) / n)) / denom
    return (p, max(0.0, center - half), min(1.0, center + half))
