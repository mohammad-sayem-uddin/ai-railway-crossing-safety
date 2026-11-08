"""Phase 12 computation engine, separated from official authorization.

The engine accepts typed ground-truth records and completed replay results. It
is testable with synthetic fixtures, validates split/source relationships,
computes the project's existing event metrics, and emits deterministic
machine-readable artifacts. Real-data outputs are reachable only through
``Phase12EvaluationRunner.run_official``, which re-assesses the live repository
evidence (including the recorded, hash-bound EVAL-AUTH statement) itself and
loads approved Stage-2.1 ground truth from the repository, never from the
caller. Until that assessment passes, real evidence is refused.
"""

from __future__ import annotations

import hashlib
import math
import os
import shutil
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from railway_detection import __version__
from railway_detection.evaluation.clock_aware import (
    ClockModelError,
    EventReplay,
    evaluate_event_replay,
)
from railway_detection.evaluation.ground_truth_loader import (
    ApprovedEventGroundTruth,
    BoundaryNotComputable,
)
from railway_detection.evaluation.input_contracts import (
    EvaluationInputError,
    EvidenceClassification,
    load_evaluation_input_manifest,
)
from railway_detection.evaluation.metrics import (
    CohortEvaluationSummary,
    EventMetricsCalculator,
    SingleEventEvaluation,
)
from railway_detection.evaluation.output_contracts import (
    EvaluationFailureReport,
    EvaluationProvenance,
    canonical_json_bytes,
)
from railway_detection.research_contracts import (
    ResearchContractError,
    validate_camera_scope,
    validate_event_level_split,
)
from railway_detection.safety import media_guard
from railway_detection.safety import path_identity as pid
from railway_detection.simulation.runner import SimulationRunResult
from railway_detection.utils.logging import get_logger
from railway_detection.utils.reproducibility import capture_environment, git_revision

logger = get_logger("evaluation.evaluation_runner")


class EvaluationRefused(RuntimeError):
    """Raised when an input contract fails before metrics are computed."""

    def __init__(
        self,
        detail: str,
        *,
        code: str = "EVALUATION_REFUSED",
        event_id: str | None = None,
        stage: str = "input_validation",
    ) -> None:
        self.code = code
        self.detail = detail
        self.event_id = event_id
        self.stage = stage
        super().__init__(f"{code}: {detail}")


@dataclass(frozen=True)
class _OfficialPermit:
    """Legacy compatibility shape; never accepted from a public caller.

    Mission 12 deliberately retains this private name so stale integrations fail
    closed rather than silently changing semantics.  Public ``run`` and
    ``run_from_manifest`` reject caller-supplied permits.  Only the private
    ``_VerifiedOfficialAuthorization`` context created after live readiness
    verification can reach the computation core.
    """

    authorization_sha256: str
    attestation_level: str
    manifest_sha256: str


_OFFICIAL_CONTEXT_TOKEN = object()


@dataclass(frozen=True)
class _VerifiedOfficialAuthorization:
    """Authorization context issued only by the verified official path.

    The object is a Python-process trust-boundary mechanism, not a cryptographic
    capability or OS sandbox.  Arbitrary code already executing in this process
    can inspect or monkey-patch Python objects; ordinary public API callers cannot
    establish official authorization merely by constructing a dataclass.
    """

    token: object
    authorization_sha256: str
    attestation_level: str
    manifest_sha256: str


@dataclass
class Phase12EvaluationResult:
    """Outputs of the internal Phase 12 computation engine."""

    cohort_summary: CohortEvaluationSummary
    single_evaluations: list[SingleEventEvaluation]
    tick_logs: dict[str, bytes] = field(default_factory=dict)
    output_dir: Path | None = None
    run_manifest: dict[str, Any] = field(default_factory=dict)
    evidence_classification: EvidenceClassification = EvidenceClassification.SYNTHETIC


def serialize_tick_log(
    sim_result: SimulationRunResult,
    evaluation: SingleEventEvaluation,
) -> bytes:
    """Return canonical JSON bytes for an event replay and computed metrics."""
    payload: dict[str, Any] = {
        "kind": "phase12_tick_log",
        "event_id": sim_result.event_id,
        "scenario_name": sim_result.scenario_name,
        "total_duration_s": sim_result.total_duration_s,
        "closed_duration_s": sim_result.closed_duration_s,
        "warning_lead_time_s": sim_result.warning_lead_time_s,
        "premature_opening_detected": sim_result.premature_opening_detected,
        "fault_occurred": sim_result.fault_occurred,
        "evaluation": {
            "missed_train": evaluation.missed_train,
            "premature_opening": evaluation.premature_opening,
            "warning_lead_time_s": evaluation.warning_lead_time_s,
            "excess_closed_duration_s": evaluation.excess_closed_duration_s,
            "clearance_latency_s": evaluation.clearance_latency_s,
            "total_closed_s": evaluation.total_closed_s,
            "evaluable": evaluation.evaluable,
            "notes": evaluation.notes,
        },
        "steps": [
            {
                "timestamp_s": step.timestamp_s,
                "crossing_state": step.crossing_state,
                "gate_state": step.gate_state,
                "gate_angle_deg": step.gate_angle_deg,
                "is_passage_blocked": step.is_passage_blocked,
            }
            for step in sim_result.steps
        ],
    }
    return canonical_json_bytes(payload)


def serialize_replay_tick_log(replay: EventReplay, evaluation: SingleEventEvaluation) -> bytes:
    """Canonical JSON bytes for a multi-system real-event replay and its metrics."""
    return canonical_json_bytes(
        {
            "kind": "phase12_replay_tick_log",
            "event_id": replay.event_id,
            "camera_mode": replay.camera_mode,
            "systems": {
                name: {
                    "clock_offsets_s": dict(sorted(system.clock_offsets_s.items())),
                    "details": dict(system.details),
                    "total_duration_s": system.result.total_duration_s,
                    "closed_duration_s": system.result.closed_duration_s,
                    "steps": [
                        {
                            "timestamp_s": step.timestamp_s,
                            "crossing_state": step.crossing_state,
                            "gate_state": step.gate_state,
                            "gate_angle_deg": step.gate_angle_deg,
                            "is_passage_blocked": step.is_passage_blocked,
                        }
                        for step in system.result.steps
                    ],
                }
                for name, system in sorted(replay.systems.items())
            },
            "evaluation": {
                "missed_train": evaluation.missed_train,
                "premature_opening": evaluation.premature_opening,
                "warning_lead_time_s": evaluation.warning_lead_time_s,
                "excess_closed_duration_s": evaluation.excess_closed_duration_s,
                "clearance_latency_s": evaluation.clearance_latency_s,
                "metric_exclusions": dict(sorted(evaluation.metric_exclusions.items())),
                "notes": evaluation.notes,
            },
        }
    )


class Phase12EvaluationRunner:
    """Synthetic-capable event-level computation engine (not an auth system)."""

    def run_from_manifest(self, **kwargs: Any) -> Phase12EvaluationResult:
        """Public synthetic manifest entry point.

        Public callers may evaluate synthetic fixtures.  REAL evidence is
        deliberately refused here; only ``run_official`` can call the private
        verified path after independently checking on-disk authorization.
        """
        classification = kwargs.get("evidence_classification", EvidenceClassification.SYNTHETIC)
        try:
            is_real = EvidenceClassification(classification) is EvidenceClassification.REAL
        except (TypeError, ValueError) as exc:
            raise EvaluationRefused(
                "invalid evidence classification", code="EVIDENCE_CLASSIFICATION_INVALID"
            ) from exc
        has_context = kwargs.get("_authorization_context") is not None
        has_permit = kwargs.get("_permit") is not None
        if is_real or has_context or has_permit:
            detail = (
                "a permit cannot be applied to synthetic evidence"
                if has_permit and not is_real and not has_context
                else "real-evidence execution is available only through run_official after "
                "independently verified authorization"
            )
            raise EvaluationRefused(detail, code="OFFICIAL_AUTHORIZATION_CONTEXT_REQUIRED")
        # Mission 14 (F13-02): the kwarg is caller-controlled and proves nothing.  Decide from the
        # manifest's *location* (no read) and then from its header (the one small control file; no
        # event source is opened or hashed) before the private path may touch any source.
        manifest_path = kwargs.get("manifest_path")
        self._refuse_protected_manifest_location(manifest_path)
        self._refuse_real_manifest_header(manifest_path)
        return self._run_from_manifest_verified(**kwargs)

    @staticmethod
    def _refuse_protected_manifest_location(manifest_path: Path | str | None) -> None:
        """The public synthetic API never reads a manifest from the repository's evidence trees."""
        if manifest_path is None:
            return
        try:
            for zone in media_guard.PROTECTED_OUTPUT_ZONES:
                if pid.is_within(manifest_path, Path(media_guard.REAL_REPO_ROOT) / zone):
                    raise EvaluationRefused(
                        "the public synthetic API does not read manifests from the repository's "
                        f"{zone}/ tree; real-evidence runs go through run_official",
                        code="OFFICIAL_MANIFEST_LOCATION_REFUSED",
                    )
        except pid.PathIdentityError as exc:
            raise EvaluationRefused(
                f"manifest path refused ({exc.code})", code="MANIFEST_PATH_REFUSED"
            ) from exc

    @staticmethod
    def _refuse_real_manifest_header(manifest_path: Path | str | None) -> None:
        """Read the manifest header only (no source opened); refuse a REAL classification."""
        if manifest_path is None:
            return
        try:
            header = load_evaluation_input_manifest(manifest_path, verify_sources=False)
        except EvaluationInputError as exc:
            raise EvaluationRefused(exc.detail, code=exc.code) from exc
        if header.evidence_classification is EvidenceClassification.REAL:
            raise EvaluationRefused(
                "the manifest declares real evidence; real-evidence execution is available only "
                "through run_official after independently verified authorization",
                code="OFFICIAL_AUTHORIZATION_CONTEXT_REQUIRED",
            )

    def _run_from_manifest_verified(
        self,
        *,
        manifest_path: Path | str,
        ground_truth: Sequence[ApprovedEventGroundTruth],
        simulation_results: Mapping[str, SimulationRunResult | EventReplay],
        evidence_classification: EvidenceClassification | None = None,
        frozen_config_sha256: str = "",
        decision_policy_sha256: str = "",
        checkpoint_sha256: Mapping[str, str] | None = None,
        seed: int = 42,
        output_dir: Path | str | None = None,
        command: str | None = None,
        premature_opening_window: str | None = None,
        replay_provenance: Mapping[str, Any] | None = None,
        _permit: _OfficialPermit | None = None,
        _authorization_context: _VerifiedOfficialAuthorization | None = None,
    ) -> Phase12EvaluationResult:
        """Evaluate only event IDs and metadata declared by a validated manifest.

        Replay results and approved typed ground truth remain injectable so tests
        can run without media.  The manifest is authoritative for split, source
        fingerprints, evidence class, camera scope, and event membership; caller
        values cannot replace those fields.
        """
        # Mission 14 (F13-02): header first, with no source opened.  A REAL manifest must already
        # carry the private verified context before a single event source is read or hashed.
        try:
            header = load_evaluation_input_manifest(manifest_path, verify_sources=False)
        except EvaluationInputError as exc:
            raise EvaluationRefused(exc.detail, code=exc.code) from exc
        if header.evidence_classification is EvidenceClassification.REAL:
            self._require_official_context(
                _permit, _authorization_context, header.manifest_sha256
            )
        try:
            inputs = load_evaluation_input_manifest(manifest_path, verify_sources=True)
        except EvaluationInputError as exc:
            raise EvaluationRefused(exc.detail, code=exc.code) from exc
        # Re-validate immediately before consuming injected replay results.  A
        # manifest/source replacement between the first load and this point is
        # detected.  The remaining limitation is an unavoidable filesystem race
        # after this final check; callers must use immutable snapshots or an
        # OS-level file lock for stronger guarantees.
        try:
            inputs_again = load_evaluation_input_manifest(manifest_path, verify_sources=True)
        except EvaluationInputError as exc:
            raise EvaluationRefused(exc.detail, code=exc.code) from exc
        if (
            inputs_again.manifest_sha256 != inputs.manifest_sha256
            or inputs_again.source_fingerprints != inputs.source_fingerprints
        ):
            raise EvaluationRefused(
                "manifest or source changed between validation and consumption",
                code="INPUT_CHANGED_DURING_VALIDATION",
            )
        classification = inputs.evidence_classification
        if (
            evidence_classification is not None
            and EvidenceClassification(evidence_classification) != classification
        ):
            raise EvaluationRefused(
                "caller evidence classification does not match manifest",
                code="MANIFEST_BINDING_MISMATCH",
            )
        if not inputs.camera_scope_by_event:
            raise EvaluationRefused(
                "manifest must declare camera_scope_by_event", code="CAMERA_SCOPE_MISSING"
            )
        manifest_cohorts = {
            item.event_id: item.cohort for item in inputs.events
        }
        truth_by_event = {item.event_id: item for item in ground_truth}
        for event_id, cohort in manifest_cohorts.items():
            truth = truth_by_event.get(event_id)
            if truth is not None and truth.cohort != cohort:
                raise EvaluationRefused(
                    f"manifest cohort does not match validated ground truth for {event_id}",
                    code="MANIFEST_COHORT_MISMATCH",
                )
        return self._run_verified(
            event_split=inputs.partitions,
            camera_scope=inputs.camera_scope_by_event,
            accepted_sync_events=set(inputs.accepted_sync_events),
            ground_truth=ground_truth,
            simulation_results=simulation_results,
            evidence_classification=classification,
            source_sha256_by_event=inputs.source_fingerprints,
            source_path_by_event={
                item.event_id: str(item.source_path) for item in inputs.events
            },
            input_manifest_sha256=inputs.manifest_sha256,
            input_manifest_path=str(inputs.manifest_path),
            frozen_config_sha256=frozen_config_sha256,
            decision_policy_sha256=decision_policy_sha256,
            checkpoint_sha256=checkpoint_sha256,
            seed=seed,
            output_dir=output_dir,
            command=command,
            premature_opening_window=premature_opening_window,
            replay_provenance=replay_provenance,
            _permit=_permit,
            _authorization_context=_authorization_context,
        )

    @staticmethod
    def _checked_output_dir(root: Path, output_dir: Path | str) -> Path:
        """Official outputs may not target evidence/config trees or a non-empty directory.

        Containment is judged by filesystem identity (Mission 14, F13-04), so a case-variant or
        symlinked spelling of a protected tree is refused exactly like the canonical spelling.
        """
        try:
            destination = pid.canonical_path(output_dir)
            base = pid.canonical_path(root)
            protected = (
                "data/ground_truth",
                "data/raw",
                "data/processed",
                "data/manifests",
                "data/splits",
                "data/governance",
                "configs",
                "models",
                "experiments",
                "results/experiment_registry.jsonl",
            )
            for item in protected:
                if pid.is_within(destination, base / item):
                    raise EvaluationRefused(
                        f"output directory may not be inside protected path {item}",
                        code="OUTPUT_DIR_PROTECTED",
                        stage="output",
                    )
        except pid.PathIdentityError as exc:
            raise EvaluationRefused(
                f"output directory refused ({exc.code})",
                code="OUTPUT_DIR_PROTECTED",
                stage="output",
            ) from exc
        if destination.exists() and (not destination.is_dir() or any(destination.iterdir())):
            raise EvaluationRefused(
                f"output directory {destination} exists and is not empty; official outputs are "
                "never merged into existing files",
                code="OUTPUT_DIR_NOT_EMPTY",
                stage="output",
            )
        return destination

    def run_official(
        self,
        *,
        repository_root: Path | str,
        config_path: Path | str = "configs/frozen_experiment_v1.yaml",
        policy_path: Path | str = "configs/decision_policy_v1.yaml",
        input_manifest_path: Path | str = "data/manifests/phase12_evaluation_inputs.json",
        seed: int = 42,
        output_dir: Path | str | None = None,
        command: str | None = None,
    ) -> Phase12EvaluationResult:
        """The only path to real-evidence output.

        Nothing is accepted from the caller except paths: replays are produced by the
        replay producer from the verified, authorized manifest; ground truth is loaded
        from the repository's Stage-2.1 records; readiness (including the recorded,
        hash-bound EVAL-AUTH) is re-assessed by the producer on every call. Outputs are
        written only after every event succeeded, atomically, so a failure leaves no
        partial official result.
        """
        from railway_detection.evaluation.ground_truth_loader import (
            GroundTruthLoadError,
            load_approved_ground_truth_with_hashes,
        )
        from railway_detection.evaluation.replay_producer import (
            RealEventReplayProducer,
            ReplayFailure,
        )

        root = Path(repository_root).resolve()
        destination = self._checked_output_dir(root, output_dir) if output_dir else None
        producer = RealEventReplayProducer(
            config_path=config_path,
            policy_path=policy_path,
            input_manifest_path=input_manifest_path,
        )
        try:
            production = producer.produce(root)
        except ReplayFailure as exc:
            raise EvaluationRefused(
                exc.detail, code=exc.code, event_id=exc.event_id, stage=exc.stage
            ) from exc
        readiness = production.readiness
        assert readiness.authorization_sha256 is not None
        try:
            all_truth, loaded_hashes = load_approved_ground_truth_with_hashes(
                root / "data/ground_truth/reviews", qualify_event_ids=True
            )
        except GroundTruthLoadError as exc:
            raise EvaluationRefused(
                str(exc), code="GROUND_TRUTH_REFUSED", stage="ground_truth"
            ) from exc
        if loaded_hashes != readiness.review_record_sha256:
            raise EvaluationRefused(
                "review records changed between readiness verification and loading",
                code="INPUT_CHANGED_DURING_VALIDATION",
                stage="ground_truth",
            )
        test_ids = set(production.inputs.partitions["test"])
        # Approved records for train/validation events are never consumed.
        ground_truth = [item for item in all_truth if item.event_id in test_ids]
        self._check_evidence_matches_reviewed_media(production.replays, ground_truth)
        manifest = Path(input_manifest_path)
        if not manifest.is_absolute():
            manifest = root / manifest
        authorization_context = _VerifiedOfficialAuthorization(
            token=_OFFICIAL_CONTEXT_TOKEN,
            authorization_sha256=readiness.authorization_sha256,
            attestation_level=str(readiness.authorization_attestation_level),
            manifest_sha256=production.inputs.manifest_sha256,
        )
        per_event = {
            event_id: {
                "camera_mode": replay.camera_mode,
                "systems": {
                    name: {
                        "clock_offsets_s": dict(sorted(system.clock_offsets_s.items())),
                        **{k: v for k, v in sorted(system.details.items())},
                    }
                    for name, system in sorted(replay.systems.items())
                },
                **{k: v for k, v in sorted(replay.provenance.items())},
            }
            for event_id, replay in sorted(production.replays.items())
        }
        return self._run_from_manifest_verified(
            manifest_path=manifest,
            ground_truth=ground_truth,
            simulation_results=production.replays,
            frozen_config_sha256=production.config.canonical_hash,
            decision_policy_sha256=readiness.live_bindings.get("decision_policy_sha256") or "",
            checkpoint_sha256={
                "vision": production.config.checkpoints.vision.expected_sha256,
                "audio_v3": production.config.checkpoints.audio_v3.expected_sha256,
            },
            seed=seed,
            output_dir=destination,
            command=command,
            premature_opening_window=(readiness.protocol_profile or {}).get(
                "premature_opening_window"
            ),
            replay_provenance={
                **production.provenance,
                "protocol_profile": dict(sorted((readiness.protocol_profile or {}).items())),
                "events": per_event,
            },
            _authorization_context=authorization_context,
        )

    @staticmethod
    def _check_evidence_matches_reviewed_media(
        replays: Mapping[str, EventReplay], ground_truth: Sequence[ApprovedEventGroundTruth]
    ) -> None:
        """Tie "real" to independent evidence: the replayed media is the media the reviewer saw.

        A manifest and its payloads can call themselves real. What they cannot forge is the
        reviewer-observed full-file media hash inside an approved Stage-2.1 record.
        """
        by_event = {item.event_id: item for item in ground_truth}
        for event_id, replay in sorted(replays.items()):
            truth = by_event.get(event_id)
            if truth is None:
                continue  # missing ground truth is refused by ``run`` with its own code
            evidence = replay.provenance.get("evidence", {})
            media = evidence.get("media_sha256", {}) if isinstance(evidence, dict) else {}
            for side, digest in sorted(media.items()):
                if truth.reviewed_media_sha256.get(side) != digest:
                    raise EvaluationRefused(
                        f"{side} media hash in the evidence differs from the media the "
                        "approved reviewer observed",
                        code="EVIDENCE_MEDIA_NOT_REVIEWED_MEDIA",
                        event_id=event_id,
                        stage="evidence",
                    )

    def run_official_safe(
        self,
        *,
        failure_report_path: Path | str | None = None,
        **kwargs: Any,
    ) -> Phase12EvaluationResult | EvaluationFailureReport:
        """Like ``run_official`` but returns a structured failure report instead of raising.

        The failure report is the only file written on failure; official outputs are never
        left behind.
        """
        try:
            return self.run_official(**kwargs)
        except EvaluationRefused as exc:
            code, detail, event_id, stage = exc.code, exc.detail, exc.event_id, exc.stage
        except (EvaluationInputError, ClockModelError) as exc:
            code, detail, event_id, stage = exc.code, exc.detail, None, "evaluation"
        except Exception as exc:  # noqa: BLE001 - structured API boundary
            code = "EVALUATION_RUNTIME_ERROR"
            detail = f"{type(exc).__name__}: {exc}"
            event_id, stage = None, "evaluation"
        report = EvaluationFailureReport(
            schema_version="phase12-failure-report/1",
            status="FAILED",
            evidence_classification=EvidenceClassification.REAL,
            blockers=({"code": code, "detail": detail},),
            partial_outputs_written=False,
            failure_stage=stage,
            failure_event_id=event_id,
        )
        if failure_report_path is not None:
            report.write(failure_report_path)
        return report

    def run_safe(
        self,
        *,
        failure_report_path: Path | str | None = None,
        **kwargs: Any,
    ) -> Phase12EvaluationResult | EvaluationFailureReport:
        """Return a machine-readable failure instead of raising input refusals."""
        try:
            return self.run(**kwargs)
        except (EvaluationRefused, EvaluationInputError) as exc:
            code = getattr(exc, "code", "EVALUATION_REFUSED")
            detail = getattr(exc, "detail", str(exc))
        except Exception as exc:  # pragma: no cover - defensive API boundary
            code = "EVALUATION_RUNTIME_ERROR"
            detail = f"{type(exc).__name__}: {exc}"
        try:
            classification = EvidenceClassification(
                kwargs.get("evidence_classification", EvidenceClassification.SYNTHETIC)
            )
        except (TypeError, ValueError):
            classification = EvidenceClassification.SYNTHETIC
        if "code" in locals():
            report = EvaluationFailureReport(
                schema_version="phase12-failure-report/1",
                status="BLOCKED",
                evidence_classification=classification,
                blockers=({"code": code, "detail": detail},),
                failure_stage="input_validation",
            )
            if failure_report_path is not None:
                report.write(failure_report_path)
            return report
        raise AssertionError("unreachable failure-report branch")

    def run(self, **kwargs: Any) -> Phase12EvaluationResult:
        """Public synthetic computation entry point; REAL evidence is refused."""
        classification = kwargs.get("evidence_classification", EvidenceClassification.SYNTHETIC)
        try:
            is_real = EvidenceClassification(classification) is EvidenceClassification.REAL
        except (TypeError, ValueError) as exc:
            raise EvaluationRefused(
                "invalid evidence classification", code="EVIDENCE_CLASSIFICATION_INVALID"
            ) from exc
        has_context = kwargs.get("_authorization_context") is not None
        has_permit = kwargs.get("_permit") is not None
        if is_real or has_context or has_permit:
            detail = (
                "a permit cannot be applied to synthetic evidence"
                if has_permit and not is_real and not has_context
                else "real-evidence execution is available only through run_official after "
                "independently verified authorization"
            )
            raise EvaluationRefused(detail, code="OFFICIAL_AUTHORIZATION_CONTEXT_REQUIRED")
        return self._run_verified(**kwargs)

    def _run_verified(
        self,
        *,
        event_split: Mapping[str, Sequence[str]],
        camera_scope: Mapping[str, str],
        accepted_sync_events: set[str] | frozenset[str],
        ground_truth: Sequence[ApprovedEventGroundTruth],
        simulation_results: Mapping[str, SimulationRunResult | EventReplay],
        evidence_classification: EvidenceClassification = EvidenceClassification.SYNTHETIC,
        source_sha256_by_event: Mapping[str, str] | None = None,
        input_manifest_sha256: str | None = None,
        frozen_config_sha256: str = "",
        decision_policy_sha256: str = "",
        checkpoint_sha256: Mapping[str, str] | None = None,
        seed: int = 42,
        output_dir: Path | str | None = None,
        input_manifest_path: str | None = None,
        source_path_by_event: Mapping[str, str] | None = None,
        command: str | None = None,
        premature_opening_window: str | None = None,
        replay_provenance: Mapping[str, Any] | None = None,
        _permit: _OfficialPermit | None = None,
        _authorization_context: _VerifiedOfficialAuthorization | None = None,
    ) -> Phase12EvaluationResult:
        """Validate all inputs, compute metrics, then optionally serialize outputs.

        Real evidence requires the private context issued by ``run_official``
        after live readiness verification.  A caller-supplied permit, manifest
        digest, or authorization-looking object is never sufficient.
        """
        try:
            classification = EvidenceClassification(evidence_classification)
        except (TypeError, ValueError) as exc:
            raise EvaluationRefused(
                "invalid evidence classification", code="EVIDENCE_CLASSIFICATION_INVALID"
            ) from exc
        if classification is EvidenceClassification.REAL:
            self._require_official_context(_permit, _authorization_context, input_manifest_sha256)
        elif _permit is not None or _authorization_context is not None:
            raise EvaluationRefused("authorization context cannot be applied to synthetic evidence")
        if not isinstance(seed, int) or isinstance(seed, bool):
            raise EvaluationRefused("seed must be an integer")
        try:
            validate_event_level_split(event_split)
            validate_camera_scope(camera_scope, accepted_sync_events=accepted_sync_events)
        except ResearchContractError as exc:
            raise EvaluationRefused(f"event split or camera scope refused: {exc}") from exc

        if not ground_truth:
            raise EvaluationRefused("no approved Stage-2.1 ground truth supplied")
        truth_by_event: dict[str, ApprovedEventGroundTruth] = {}
        for truth in ground_truth:
            if not isinstance(truth, ApprovedEventGroundTruth):
                raise EvaluationRefused("ground-truth inputs must be validated typed records")
            if not truth.event_id.strip() or truth.event_id in truth_by_event:
                raise EvaluationRefused(
                    f"empty or duplicate ground-truth event_id {truth.event_id!r}"
                )
            truth_by_event[truth.event_id] = truth

        test_events = list(event_split["test"])
        test_set = set(test_events)
        missing_truth = sorted(test_set - set(truth_by_event))
        extra_truth = sorted(set(truth_by_event) - test_set)
        if missing_truth:
            raise EvaluationRefused(f"test events lack approved ground truth: {missing_truth}")
        if extra_truth:
            raise EvaluationRefused(f"ground truth outside test split: {extra_truth}")
        missing_replays = sorted(test_set - set(simulation_results))
        extra_replays = sorted(set(simulation_results) - test_set)
        if missing_replays:
            raise EvaluationRefused(f"test events lack simulation replays: {missing_replays}")
        if extra_replays:
            raise EvaluationRefused(f"simulation replays outside test split: {extra_replays}")

        for event_id, entry in simulation_results.items():
            if isinstance(entry, EventReplay):
                if entry.event_id != event_id:
                    raise EvaluationRefused(f"misbound event replay for {event_id}")
                try:
                    entry.validate()
                except ClockModelError as exc:
                    raise EvaluationRefused(exc.detail, code=exc.code, event_id=event_id) from exc
                results = [system.result for system in entry.systems.values()]
            else:
                results = [entry]
            for result in results:
                if not isinstance(result, SimulationRunResult) or result.event_id != event_id:
                    raise EvaluationRefused(f"invalid or misbound simulation result for {event_id}")
                if any(
                    not math.isfinite(value) or value < 0
                    for value in (result.total_duration_s, result.closed_duration_s)
                ):
                    raise EvaluationRefused(
                        f"invalid duration in simulation result for {event_id}"
                    )
                if result.warning_lead_time_s is not None and not math.isfinite(
                    result.warning_lead_time_s
                ):
                    raise EvaluationRefused(f"invalid warning lead time for {event_id}")
                timestamps = [step.timestamp_s for step in result.steps]
                if any(not math.isfinite(value) or value < 0 for value in timestamps) or any(
                    right <= left for left, right in zip(timestamps, timestamps[1:], strict=False)
                ):
                    raise EvaluationRefused(
                        f"invalid or unordered simulation steps for {event_id}"
                    )

        # A manifest-bound run must carry every declared source identity, not a
        # caller-selected subset.  The manifest loader already checked each
        # digest before payload consumption; this check prevents in-memory runs
        # from being relabeled as manifest-bound with incomplete provenance.
        declared_events = {
            event_id for ids in event_split.values() for event_id in ids
        }
        if input_manifest_sha256 is not None:
            if not source_sha256_by_event or set(source_sha256_by_event) != declared_events:
                raise EvaluationRefused(
                    "manifest-bound execution requires source fingerprints for every "
                    "declared event",
                    code="SOURCE_FINGERPRINTS_INCOMPLETE",
                )

        source_fingerprints = dict(sorted((source_sha256_by_event or {}).items()))
        for event_id, fingerprint in source_fingerprints.items():
            if event_id not in declared_events:
                raise EvaluationRefused(f"source fingerprint outside manifest: {event_id}")
            if not isinstance(fingerprint, str) or len(fingerprint) != 64 or any(
                char not in "0123456789abcdef" for char in fingerprint
            ):
                raise EvaluationRefused(f"invalid source SHA-256 for event {event_id}")

        evaluations: list[SingleEventEvaluation] = []
        tick_logs: dict[str, bytes] = {}
        for event_id in sorted(test_events):
            truth = truth_by_event[event_id]
            replay_entry = simulation_results[event_id]
            if isinstance(replay_entry, EventReplay):
                if truth.cohort != replay_entry.cohort:
                    raise EvaluationRefused(
                        f"replay cohort {replay_entry.cohort!r} differs from ground-truth "
                        f"cohort {truth.cohort!r}",
                        code="MANIFEST_COHORT_MISMATCH",
                        event_id=event_id,
                    )
                try:
                    evaluation = evaluate_event_replay(
                        replay_entry, truth, premature_opening_window=premature_opening_window
                    )
                except ClockModelError as exc:
                    raise EvaluationRefused(
                        exc.detail, code=exc.code, event_id=event_id, stage="evaluation"
                    ) from exc
                if truth.cohort not in {"train_events", "no_train_events"}:
                    evaluation.evaluable = False
                    evaluation.notes = "engine_event_excluded"
                evaluations.append(evaluation)
                tick_logs[event_id] = serialize_replay_tick_log(replay_entry, evaluation)
                continue
            entry_time_s, clearance_time_s = self._ground_truth_times(truth)
            sim_result = replay_entry
            has_train = truth.cohort == "train_events"
            evaluation = EventMetricsCalculator.evaluate_run(
                sim_result,
                entry_time_s=entry_time_s,
                clearance_time_s=clearance_time_s,
                has_train_ground_truth=has_train,
                exclusion_reasons=self._exclusion_reasons(truth),
                premature_opening_window=premature_opening_window,
                cohort=truth.cohort,
            )
            if truth.cohort not in {"train_events", "no_train_events"}:
                evaluation.evaluable = False
                evaluation.notes = "engine_event_excluded"
            evaluations.append(evaluation)
            tick_logs[event_id] = serialize_tick_log(sim_result, evaluation)
        summary = EventMetricsCalculator.aggregate_cohort(evaluations)

        provenance = EvaluationProvenance(
            schema_version="phase12-provenance/1",
            phase="12",
            evidence_classification=classification,
            input_manifest_sha256=input_manifest_sha256
            or "",
            source_sha256_by_event=source_fingerprints,
            frozen_config_sha256=frozen_config_sha256
            or "",
            decision_policy_sha256=decision_policy_sha256
            or "",
            checkpoint_sha256=dict(sorted((checkpoint_sha256 or {}).items())),
            seed=seed,
            git_commit=git_revision(Path.cwd()),
            official_authorization_verified=(
                classification is EvidenceClassification.REAL
                and _authorization_context is not None
                and _authorization_context.token is _OFFICIAL_CONTEXT_TOKEN
            ),
            input_manifest_path=input_manifest_path,
            source_path_by_event=dict(sorted((source_path_by_event or {}).items())),
            split_identity={role: tuple(sorted(ids)) for role, ids in event_split.items()},
            software_version=__version__,
            environment=capture_environment(),
            command=command,
        )
        run_id = hashlib.sha256(
            canonical_json_bytes({
                "manifest": input_manifest_sha256,
                "events": sorted(test_events),
                "event_split": {
                    role: sorted(ids) for role, ids in event_split.items()
                },
                "camera_scope": dict(sorted(camera_scope.items())),
                "accepted_sync_events": sorted(accepted_sync_events),
                "seed": seed,
                "sources": source_fingerprints,
                "frozen_config_sha256": frozen_config_sha256,
                "decision_policy_sha256": decision_policy_sha256,
                "checkpoint_sha256": dict(sorted((checkpoint_sha256 or {}).items())),
            })
        ).hexdigest()[:12]
        manifest = {
            "schema_version": "phase12-run-manifest/1",
            "phase": "12",
            "evidence_classification": classification.value,
            "authorization_status": (
                f"verified:{_authorization_context.attestation_level}"
                if _authorization_context is not None
                else "not_verified"
            ),
            "authorization_record_sha256": (
                _authorization_context.authorization_sha256
                if _authorization_context is not None
                else None
            ),
            "event_split": {role: sorted(ids) for role, ids in event_split.items()},
            "source_sha256_by_event": source_fingerprints,
            "provenance": provenance.to_dict(),
            "test_event_ids": sorted(test_events),
            "test_event_count": len(test_events),
            "eligible_event_count": summary.eligible_events,
            "seed": seed,
            "run_id": run_id,
            "command": command,
            "metrics": summary.to_dict(),
            "premature_opening_window": premature_opening_window or "undecided",
            "contract_versions": {
                "run_manifest": "phase12-run-manifest/1",
                "provenance": "phase12-provenance/1",
                "input_manifest": "phase12-evaluation-inputs/1",
                "replay_evidence": "phase12-replay-evidence/1",
                "eval_authorization": "phase12-eval-authorization/1",
                "promotion_receipt": "phase12-stage21-promotion-receipt/2",
                "failure_report": "phase12-failure-report/1",
                "replay_producer": "phase12-replay-producer/1",
            },
            "replay_provenance": dict(replay_provenance) if replay_provenance else None,
        }
        resolved_out: Path | None = None
        if output_dir is not None:
            resolved_out = Path(output_dir)
            self._write_outputs(resolved_out, summary, evaluations, tick_logs, manifest)
        return Phase12EvaluationResult(
            cohort_summary=summary,
            single_evaluations=evaluations,
            tick_logs=tick_logs,
            output_dir=resolved_out,
            run_manifest=manifest,
            evidence_classification=classification,
        )

    @staticmethod
    def _require_official_context(
        permit: _OfficialPermit | None,
        context: _VerifiedOfficialAuthorization | None,
        manifest_sha256: str | None,
    ) -> None:
        """REAL evidence needs the private context ``run_official`` issues; nothing else counts."""
        if (
            permit is not None
            or context is None
            or context.token is not _OFFICIAL_CONTEXT_TOKEN
            or manifest_sha256 is None
            or context.manifest_sha256 != manifest_sha256
            or not context.authorization_sha256
            or not context.attestation_level
        ):
            raise EvaluationRefused(
                "real-evidence execution is available only through run_official after "
                "independently verified authorization; caller permits and manifest digests "
                "are insufficient",
                code="OFFICIAL_AUTHORIZATION_CONTEXT_REQUIRED",
            )

    @staticmethod
    def _exclusion_reasons(truth: ApprovedEventGroundTruth) -> dict[str, str]:
        """Why T1/T4 are not usable values for this event (never defaulted)."""
        reasons: dict[str, str] = {}
        for name in ("T1_danger_zone_entry", "T4_tail_clearance"):
            if name in truth.observable_boundaries:
                continue
            if name in truth.censored_boundaries:
                reasons[name] = "censored"
            elif name in truth.uncertain_boundaries:
                reasons[name] = "uncertain"
            else:
                reasons[name] = "not_applicable_or_unknown"
        return reasons

    @staticmethod
    def _ground_truth_times(
        truth: ApprovedEventGroundTruth,
    ) -> tuple[float | None, float | None]:
        entry_t: float | None = None
        clearance_t: float | None = None
        try:
            entry_t = truth.observable_value("T1_danger_zone_entry")
        except BoundaryNotComputable:
            pass
        try:
            clearance_t = truth.observable_value("T4_tail_clearance")
        except BoundaryNotComputable:
            pass
        return entry_t, clearance_t

    @staticmethod
    def _write_outputs(
        output_dir: Path,
        summary: CohortEvaluationSummary,
        evaluations: list[SingleEventEvaluation],
        tick_logs: dict[str, bytes],
        manifest: dict[str, Any],
    ) -> None:
        """Write every output into a staging directory, then move it into place.

        A failure at any point removes the staging directory, so a run never leaves a
        partial result set behind.
        """
        output_dir = Path(output_dir)
        if output_dir.exists() and (not output_dir.is_dir() or any(output_dir.iterdir())):
            raise EvaluationRefused(
                f"output directory {output_dir} exists and is not empty",
                code="OUTPUT_DIR_NOT_EMPTY",
                stage="output",
            )
        output_dir.parent.mkdir(parents=True, exist_ok=True)
        staging = output_dir.parent / f".{output_dir.name}.partial"
        shutil.rmtree(staging, ignore_errors=True)
        staging.mkdir()
        try:
            (staging / "run_manifest.json").write_bytes(canonical_json_bytes(manifest))
            (staging / "cohort_summary.json").write_bytes(
                canonical_json_bytes(summary.to_dict())
            )
            rows = [
                {
                    "event_id": item.event_id,
                    "scenario_name": item.scenario_name,
                    "missed_train": item.missed_train,
                    "premature_opening": item.premature_opening,
                    "warning_lead_time_s": item.warning_lead_time_s,
                    "excess_closed_duration_s": item.excess_closed_duration_s,
                    "clearance_latency_s": item.clearance_latency_s,
                    "total_closed_s": item.total_closed_s,
                    "evaluable": item.evaluable,
                    "notes": item.notes,
                    "exclusion_reasons": dict(sorted(item.exclusion_reasons.items())),
                    "metric_exclusions": dict(sorted(item.metric_exclusions.items())),
                    "per_system_closed_s": dict(sorted(item.per_system_closed_s.items())),
                    "blocked_seconds": item.blocked_seconds,
                    "closure_episodes": item.closure_episodes,
                    "exposure_s": item.exposure_s,
                }
                for item in evaluations
            ]
            (staging / "single_evaluations.json").write_bytes(canonical_json_bytes(rows))
            tick_dir = staging / "tick_logs"
            tick_dir.mkdir()
            for event_id, blob in sorted(tick_logs.items()):
                safe_name = event_id.replace("/", "__")
                (tick_dir / f"{safe_name}.ticklog.json").write_bytes(blob)
            if output_dir.exists():
                output_dir.rmdir()
            os.replace(staging, output_dir)
        except BaseException:
            shutil.rmtree(staging, ignore_errors=True)
            raise
        logger.info("Phase 12 internal outputs written to %s", output_dir)