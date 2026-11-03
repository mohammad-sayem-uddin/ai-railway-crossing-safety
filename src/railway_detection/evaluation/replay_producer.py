"""Real-event replay producer for the Phase 12 official evaluation.

Turns the hash-bound, authorized evidence payloads named by the verified input
manifest into decision-engine replays (``EventReplay``), one per *test-split* event.

Guarantees (each covered by tests):

* **No bypass.** ``produce`` re-assesses live readiness (including the recorded,
  hash-bound EVAL-AUTH statement) on every call; it accepts no readiness flag,
  permit or pre-built input. If anything is unmet it raises ``ReplayFailure`` before
  reading a single payload.
* **Verified inputs only.** Payloads come from the manifest (source hashes verified,
  manifest digest equal to the digest EVAL-AUTH binds). Each payload must match its
  manifest identity, decided camera scope, the live frozen configuration and the
  frozen checkpoints (Audio V2 is refused).
* **Identity, split, scope.** Only test-split events are replayed; train/validation
  events never reach the decision engine. Streams outside the decided camera scope are
  refused.
* **Synchronization.** Cameras are never fused on an assumed offset. ``independent_camera``
  replays each stream on its own clock; ``dual_camera`` requires the event to be in the
  researcher's accepted-sync set *and* a ``CALIBRATION_SUPPORTED`` calibration entry whose
  media hashes equal the payload's provenance (via ``load_validated_sync_aligner``).
* **No labels.** Replays run without ground truth; evidence payloads have no label
  channel and must attest ``annotation_labels_used: false``. No threshold is supplied
  here: the frozen configuration alone drives the decision engine.
* **All or nothing.** Any failure raises ``ReplayFailure`` carrying a structured code and
  the event; no partial replay set is returned.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from railway_detection.data.sync import SyncAligner
from railway_detection.data.sync_calibration import (
    CalibrationNotAcceptedError,
    load_validated_sync_aligner,
)
from railway_detection.evaluation.clock_aware import EventReplay, SystemReplay
from railway_detection.evaluation.execution_gate import (
    OfficialExecutionReadiness,
    assess_official_phase12_readiness,
)
from railway_detection.evaluation.input_contracts import (
    EvaluationInputError,
    EvaluationInputSet,
    load_evaluation_input_manifest,
)
from railway_detection.evaluation.replay_evidence import (
    ReplayEvidence,
    ReplayInputError,
    parse_replay_evidence,
)
from railway_detection.experiments.frozen_config import (
    ConfigurationIntegrityError,
    FrozenExperimentConfig,
    TimingIntegrityError,
    load_frozen_config,
    verify_timing_safeguards,
)
from railway_detection.fusion.collector import MultimodalEvidenceCollector
from railway_detection.fusion.evidence import EvidenceRecord
from railway_detection.simulation.runner import EventSimulationRunner

CALIBRATION_MANIFEST_RELATIVE = Path("data/manifests/camera_sync_offsets_candidate.yaml")
# Protocol v9 section 7: alignment status from the measured uncertainty delta (seconds).
ALIGNED_MAX_UNCERTAINTY_S = 0.5
PARTIALLY_ALIGNED_MAX_UNCERTAINTY_S = 2.0
PRODUCER_VERSION = "phase12-replay-producer/1"


class ReplayFailure(RuntimeError):
    """Structured, all-or-nothing production failure."""

    def __init__(
        self, code: str, detail: str, *, event_id: str | None = None, stage: str = "replay"
    ) -> None:
        self.code = code
        self.detail = detail
        self.event_id = event_id
        self.stage = stage
        super().__init__(f"{code}: {detail}" + (f" [event {event_id}]" if event_id else ""))

    def to_blocker(self) -> dict[str, str]:
        return {"code": self.code, "detail": self.detail}


@dataclass(frozen=True)
class ReplayProduction:
    replays: dict[str, EventReplay]
    readiness: OfficialExecutionReadiness
    inputs: EvaluationInputSet
    config: FrozenExperimentConfig
    provenance: dict[str, Any] = field(default_factory=dict)


def _duration_s(records: list[EvidenceRecord]) -> float:
    return max((record.timestamp_s for record in records), default=30.0)


class RealEventReplayProducer:
    """Replays authorized evidence through the frozen decision engine."""

    def __init__(
        self,
        *,
        config_path: Path | str = "configs/frozen_experiment_v1.yaml",
        policy_path: Path | str = "configs/decision_policy_v1.yaml",
        input_manifest_path: Path | str = "data/manifests/phase12_evaluation_inputs.json",
    ) -> None:
        self.config_path = config_path
        self.policy_path = policy_path
        self.input_manifest_path = input_manifest_path

    # ------------------------------------------------------------------ public

    def produce(self, repository_root: Path | str) -> ReplayProduction:
        root = Path(repository_root).resolve()
        readiness = assess_official_phase12_readiness(
            root,
            config_path=self.config_path,
            policy_path=self.policy_path,
            input_manifest_path=self.input_manifest_path,
        )
        if not readiness.ready or readiness.authorization_sha256 is None:
            raise ReplayFailure(
                "OFFICIAL_PREREQUISITES_UNSATISFIED",
                ", ".join(readiness.blocker_codes) or "authorization not verified",
                stage="readiness",
            )
        inputs = self._load_inputs(root, readiness)
        config = self._load_config(root)
        replays: dict[str, EventReplay] = {}
        for event_id in sorted(inputs.partitions["test"]):
            replays[event_id] = self._replay_event(root, inputs, config, event_id)
        provenance = {
            "producer": PRODUCER_VERSION,
            "input_manifest_sha256": inputs.manifest_sha256,
            "frozen_config_sha256": config.canonical_hash,
            "authorization_record_sha256": readiness.authorization_sha256,
            "authorization_attestation_level": readiness.authorization_attestation_level,
            "protocol_profile_sha256": readiness.live_bindings.get("protocol_profile_sha256"),
            "split": {role: list(ids) for role, ids in sorted(inputs.partitions.items())},
            "replayed_event_ids": sorted(replays),
            "events_not_replayed": sorted(
                event_id
                for role in ("train", "val")
                for event_id in inputs.partitions[role]
            ),
        }
        return ReplayProduction(
            replays=replays,
            readiness=readiness,
            inputs=inputs,
            config=config,
            provenance=provenance,
        )

    # ----------------------------------------------------------------- internals

    def _load_inputs(
        self, root: Path, readiness: OfficialExecutionReadiness
    ) -> EvaluationInputSet:
        manifest = Path(self.input_manifest_path)
        if not manifest.is_absolute():
            manifest = root / manifest
        try:
            first = load_evaluation_input_manifest(manifest, verify_sources=True)
            second = load_evaluation_input_manifest(manifest, verify_sources=True)
        except EvaluationInputError as exc:
            raise ReplayFailure(exc.code, exc.detail, stage="inputs") from exc
        if (
            first.manifest_sha256 != second.manifest_sha256
            or first.source_fingerprints != second.source_fingerprints
        ):
            raise ReplayFailure(
                "INPUT_CHANGED_DURING_VALIDATION",
                "manifest or an event source changed while being verified",
                stage="inputs",
            )
        if first.manifest_sha256 != readiness.live_bindings.get("input_manifest_sha256"):
            raise ReplayFailure(
                "MANIFEST_BINDING_MISMATCH",
                "the manifest read for replay differs from the one the authorization binds",
                stage="inputs",
            )
        if first.evidence_classification.value != "real":
            raise ReplayFailure(
                "SYNTHETIC_INPUTS_NOT_OFFICIAL", "official replay requires a real manifest",
                stage="inputs",
            )
        if not first.camera_scope_by_event:
            raise ReplayFailure("CAMERA_SCOPE_MISSING", "manifest declares no camera scope",
                                stage="inputs")
        return first

    def _load_config(self, root: Path) -> FrozenExperimentConfig:
        path = Path(self.config_path)
        if not path.is_absolute():
            path = root / path
        try:
            config = load_frozen_config(path)
            verify_timing_safeguards(config)
        except (OSError, ConfigurationIntegrityError, TimingIntegrityError) as exc:
            raise ReplayFailure("FROZEN_CONFIG_INVALID", str(exc), stage="config") from exc
        return config

    def _evidence(
        self,
        inputs: EvaluationInputSet,
        config: FrozenExperimentConfig,
        event_id: str,
    ) -> ReplayEvidence:
        item = inputs.by_event_id[event_id]
        try:
            return parse_replay_evidence(
                item.source_payload,
                expected_event_id=event_id,
                expected_cohort=item.cohort,
                expected_camera_mode=inputs.camera_scope_by_event[event_id],
                config=config,
            )
        except ReplayInputError as exc:
            raise ReplayFailure(exc.code, exc.detail, event_id=event_id, stage="evidence") from exc

    def _run_system(
        self,
        config: FrozenExperimentConfig,
        evidence: ReplayEvidence,
        system: str,
        stream_names: tuple[str, ...],
        aligner: SyncAligner | None,
    ) -> Any:
        vision: list[EvidenceRecord] = []
        audio: list[EvidenceRecord] = []
        for name in stream_names:
            (audio if name.endswith("audio") else vision).extend(evidence.streams[name])
        cameras = {record.source_id for record in vision}
        if len(cameras) > 1 and aligner is None:
            # Same fail-closed rule the production processor enforces (R04).
            raise TimingIntegrityError(
                f"R04: refusing to fuse {sorted(cameras)} without a validated alignment"
            )
        collector = MultimodalEvidenceCollector(sync_aligner=aligner, window_tolerance_s=0.25)
        collector.add_evidence_batch(vision)
        collector.add_evidence_batch(audio)
        duration = _duration_s(vision + audio)
        frames = collector.generate_frames_from_history(
            0.0, max(duration, 1.0), stride_s=config.timing.tick_s
        )
        runner = EventSimulationRunner(config=config)
        result = runner.run_frames(
            frames=frames,
            event_id=evidence.event_id,
            scenario_name=f"phase12_official_{system}",
            entry_time_s=None,
            clearance_time_s=None,
        )
        return result, len(collector.rejected_observations), len(frames)

    def _replay_event(
        self,
        root: Path,
        inputs: EvaluationInputSet,
        config: FrozenExperimentConfig,
        event_id: str,
    ) -> EventReplay:
        evidence = self._evidence(inputs, config, event_id)
        mode = evidence.camera_mode
        systems: dict[str, SystemReplay] = {}
        calibration: dict[str, Any] = {}
        try:
            if mode == "single_camera":
                plan = [("front", ("front_vision", "front_audio"), {"front": 0.0}, None)]
            elif mode == "independent_camera":
                plan = [
                    ("front", ("front_vision", "front_audio"), {"front": 0.0}, None),
                    ("back", ("back_vision",), {"back": 0.0}, None),
                ]
            else:  # dual_camera -- the gate already required accepted synchronization
                if event_id not in inputs.accepted_sync_events:
                    raise ReplayFailure(
                        "SYNC_NOT_ACCEPTED",
                        "dual-camera replay requires the researcher's accepted synchronization",
                        event_id=event_id,
                        stage="synchronization",
                    )
                try:
                    validated = load_validated_sync_aligner(
                        root / CALIBRATION_MANIFEST_RELATIVE,
                        event_id,
                        repo_root=root,
                        # The calibration manifest carries a candidate status; acceptance is the
                        # researcher's R04 decision (accepted_sync_events), recorded in provenance.
                        allow_candidate_status=True,
                    )
                except (CalibrationNotAcceptedError, FileNotFoundError) as exc:
                    raise ReplayFailure(
                        (
                            exc.code
                            if isinstance(exc, CalibrationNotAcceptedError)
                            else "SYNC_CALIBRATION_REJECTED"
                        ),
                        str(exc), event_id=event_id,
                        stage="synchronization",
                    ) from exc
                media = evidence.provenance["media_sha256"]
                if (
                    media.get("front") != validated.front_sha256
                    or media.get("back") != validated.back_sha256
                ):
                    raise ReplayFailure(
                        "SYNC_MEDIA_MISMATCH",
                        "evidence media hashes differ from the calibrated media",
                        event_id=event_id,
                        stage="synchronization",
                    )
                uncertainty = validated.uncertainty_s
                if isinstance(uncertainty, bool) or not isinstance(uncertainty, int | float):
                    raise ReplayFailure(
                        "SYNC_UNALIGNED",
                        "synchronization uncertainty is unmeasured; protocol v9 section 7 "
                        "excludes unaligned events from joint temporal metrics",
                        event_id=event_id,
                        stage="synchronization",
                    )
                if uncertainty > PARTIALLY_ALIGNED_MAX_UNCERTAINTY_S:
                    raise ReplayFailure(
                        "SYNC_UNALIGNED",
                        f"synchronization uncertainty {uncertainty}s exceeds "
                        f"{PARTIALLY_ALIGNED_MAX_UNCERTAINTY_S}s "
                        "(protocol v9 section 7: unaligned)",
                        event_id=event_id,
                        stage="synchronization",
                    )
                alignment_status = (
                    "aligned" if uncertainty <= ALIGNED_MAX_UNCERTAINTY_S else "partially_aligned"
                )
                calibration = {
                    "alignment_status": alignment_status,
                    "alignment_uncertainty_s": float(uncertainty),
                    "latency_error_bound_s": (
                        float(uncertainty) if alignment_status == "partially_aligned" else None
                    ),
                    "calibration_manifest_version": validated.manifest_version,
                    "calibration_manifest_status": validated.manifest_status,
                    "calibration_verdict": validated.verdict,
                    "acceptance_basis": "researcher R04 decision (accepted_sync_events)",
                }
                plan = [
                    (
                        "fused",
                        ("front_vision", "back_vision", "front_audio"),
                        {"front": validated.front_offset_s, "back": validated.back_offset_s},
                        validated.aligner,
                    )
                ]
            for name, streams, offsets, aligner in plan:
                result, rejected, frame_count = self._run_system(
                    config, evidence, name, streams, aligner
                )
                systems[name] = SystemReplay(
                    name=name,
                    clock_offsets_s=offsets,
                    result=result,
                    details={
                        "streams": list(streams),
                        "frame_count": frame_count,
                        "rejected_observations": rejected,
                        "record_counts": {s: len(evidence.streams[s]) for s in streams},
                    },
                )
        except ReplayFailure:
            raise
        except Exception as exc:  # noqa: BLE001 - converted to a structured failure
            raise ReplayFailure(
                "REPLAY_ERROR", f"{type(exc).__name__}: {exc}", event_id=event_id
            ) from exc
        return EventReplay(
            event_id=event_id,
            cohort=evidence.cohort,
            camera_mode=mode,
            systems=systems,
            provenance={
                "evidence": evidence.provenance,
                "source_sha256": inputs.by_event_id[event_id].source_sha256,
                **calibration,
            },
        )
