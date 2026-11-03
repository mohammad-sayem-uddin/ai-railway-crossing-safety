"""Mission 2 comprehensive synthetic regression suite.

Verifies:
1. Objective A1: B7d arrival-order preservation, Rule 8 rejection, and simulation runner
   monotonic step isolation without weakening EventMetricsCalculator.
2. Objective A2: B7e (STALE_TIMESTAMPS) fail-closed parameter validation, exact source
   matching, original timestamp traceability, and idempotent non-compounding application.
3. Objective A3 & C: Ground-truth state distinction (confirmed train, confirmed no-train,
   engine, missing, unknown, censored, unobservable, uncertain, not_applicable) and
   strict cohort/engine_events isolation.
4. Objective B: 14-field ControlledCacheProvenance identity, deterministic key/digest
   generation, fail-closed verification, and historical diagnostic cache isolation.
5. Objective D: Descriptive-only evaluation fixed-site claim enforcement, engine-event
   isolation, historical-vs-controlled separation, and rejection by official validators.
6. Objective E: Stage-2.1 schema, promotion gate, batch integrity, and readiness checks
   using synthetic fixtures only.

Never opens, decodes, or hashes raw repository media (.mov, .mp4, .wav).
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from railway_detection.annotation.evaluation_readiness_gate import evaluate_readiness
from railway_detection.annotation.integrity_safeguard import check_review_batch_integrity
from railway_detection.annotation.promotion_gate import validate_for_promotion
from railway_detection.annotation.schemas import SchemaValidationError
from railway_detection.annotation.stage2_1_schema import (
    STAGE_2_1_SCHEMA_VERSION,
    build_stage2_1_record_from_dict,
)
from railway_detection.data.contracts import EventLabel, LayerBEvent
from railway_detection.evaluation.clock_aware import (
    EventReplay,
    SystemReplay,
    evaluate_event_replay,
)
from railway_detection.evaluation.descriptive_only import (
    DescriptiveOnlyInput,
    DescriptiveOnlyRefusal,
    aggregate_descriptive_only,
)
from railway_detection.evaluation.ground_truth_loader import ApprovedEventGroundTruth
from railway_detection.evaluation.input_contracts import (
     EvaluationInputError,
    EvidenceClassification,
    load_evaluation_input_manifest,
)
from railway_detection.evaluation.metrics import (
    EventMetricsCalculator,
    SingleEventEvaluation,
)
from railway_detection.experiments.cache_provenance import (
    CONTROLLED_CACHE_SCHEMA_VERSION,
    HISTORICAL_DIAGNOSTIC_CACHE_CLASS,
    REQUIRED_PROVENANCE_FIELDS,
    CacheProvenanceError,
    ControlledCacheProvenance,
    load_controlled_cache_jsonl,
    load_historical_diagnostic_cache_jsonl,
    validate_controlled_cache_provenance,
    write_controlled_cache_jsonl,
)
from railway_detection.experiments.layer_b_processor import LayerBEventProcessor
from railway_detection.experiments.runner import BenchmarkCondition, ExperimentRunner
from railway_detection.fusion.collector import (
    MultimodalEvidenceCollector,
    MultimodalFrame,
)
from railway_detection.fusion.evidence import Detection, EvidenceRecord, Modality
from railway_detection.fusion.rules import RuleId
from railway_detection.simulation.failure_injector import (
    FailureInjector,
    FailureMode,
    FailureSchedule,
)
from railway_detection.simulation.runner import (
    EventSimulationRunner,
    SimulationRunResult,
    SimulationStep,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_dual_source_frames() -> list[MultimodalFrame]:
    frames: list[MultimodalFrame] = []
    for idx in range(10):
        t = float(idx) * 1.0
        v1 = EvidenceRecord(
            timestamp_s=t,
            source_id="camera_1",
            modality=Modality.VISION,
            available=True,
            detections=(Detection(label="front", confidence=0.88),),
            metadata={"frame_index": idx},
        )
        v2 = EvidenceRecord(
            timestamp_s=t,
            source_id="camera_2",
            modality=Modality.VISION,
            available=True,
            detections=(Detection(label="rear", confidence=0.81),),
            metadata={"frame_index": idx},
        )
        aud = EvidenceRecord(
            timestamp_s=t,
            source_id="audio_1",
            modality=Modality.AUDIO,
            available=True,
            detections=(Detection(label="train_horn", confidence=0.79),),
            metadata={"audio_safety_role": "supporting_only"},
        )
        frames.append(
            MultimodalFrame(
                master_timestamp_s=t,
                vision_records=(v1, v2),
                audio_records=(aud,),
                source_availability={"camera_1": True, "camera_2": True, "audio_1": True},
                active_sources=("camera_1", "camera_2", "audio_1"),
            )
        )
    return frames


def _make_provenance(**overrides: object) -> ControlledCacheProvenance:
    defaults: dict[str, object] = {
        "cohort": "train_events",
        "event_id": "event_001",
        "source_id": "camera_1",
        "modality": "vision",
        "model_architecture": "yolov8n",
        "checkpoint_sha256": "a" * 64,
        "preprocessing_config": {"sampling_fps": 5.0, "conf": 0.35},
        "experiment_config_sha256": "b" * 64,
        "failure_injector": "none",
        "injector_parameters": {},
        "timing_config": {"tick_s": 0.2, "gate_closing_s": 3.0, "gate_opening_s": 3.0},
        "cache_schema_version": CONTROLLED_CACHE_SCHEMA_VERSION,
        "software_version": "0.1.0",
        "run_id": "synthetic-controlled-run-001",
    }
    defaults.update(overrides)
    return ControlledCacheProvenance(**defaults)  # type: ignore[arg-type]


# ===========================================================================
# 1. OBJECTIVE A1: B7d Arrival-Order Preservation & Rule 8 Safe Rejection
# ===========================================================================


class TestB7dEndToEnd:
    def test_injector_to_runner_to_rule8_to_metrics_end_to_end(self) -> None:
        frames = _make_dual_source_frames()
        injector = FailureInjector(
            [
                FailureSchedule(
                    mode=FailureMode.OUT_OF_ORDER_FRAMES,
                    start_time_s=4.0,
                    end_time_s=6.0,
                )
            ]
        )
        reordered = injector.inject_failures(frames)
        # Frames at index 4 (4.0s) and 5 (5.0s) are swapped -> [..., 5.0, 4.0, 6.0, ...]
        assert [f.master_timestamp_s for f in reordered] == [
            0.0, 1.0, 2.0, 3.0, 5.0, 4.0, 6.0, 7.0, 8.0, 9.0,
        ]

        runner = EventSimulationRunner()
        sim_result = runner.run_frames(
            reordered,
            event_id="train_events/event_001",
            scenario_name="B7d",
            entry_time_s=3.0,
            clearance_time_s=8.0,
            preserve_arrival_order=True,
        )

        # 1. Rule 8 rejected the out-of-order frame (t=4.0 arriving after t=5.0)
        assert sim_result.fault_occurred is True
        assert len(sim_result.rejected_steps) == 1
        rejected = sim_result.rejected_steps[0]
        assert rejected.timestamp_s == 4.0
        assert rejected.decision.rule_id == RuleId.RULE_8_OUT_OF_ORDER_REJECTION.value
        assert rejected.decision.fault_status == "out_of_order"
        assert sim_result.metrics["rejected_step_count"] == 1
        assert sim_result.metrics["out_of_order_rejected_count"] == 1

        # 2. Accepted timeline steps remain strictly monotonic (t=4.0 excluded from steps)
        accepted_ts = [s.timestamp_s for s in sim_result.steps]
        assert accepted_ts == [0.0, 1.0, 2.0, 3.0, 5.0, 6.0, 7.0, 8.0, 9.0]
        assert all(b > a for a, b in zip(accepted_ts, accepted_ts[1:], strict=False))

        # 3. Closed duration never exceeds total duration (prev_t was not regressed to 4.0)
        assert sim_result.closed_duration_s <= sim_result.total_duration_s

        # 4. Downstream metric layer evaluates cleanly without crashing
        evaluation = EventMetricsCalculator.evaluate_run(
            sim_result,
            entry_time_s=3.0,
            clearance_time_s=8.0,
            has_train_ground_truth=True,
        )
        assert evaluation.fault_occurred is True
        assert evaluation.evaluable is True

    def test_default_preserve_arrival_order_false_sorts_frames(self) -> None:
        frames = _make_dual_source_frames()
        reordered = FailureInjector(
            [FailureSchedule(mode=FailureMode.OUT_OF_ORDER_FRAMES, start_time_s=4.0, end_time_s=6.0)]
        ).inject_failures(frames)

        runner = EventSimulationRunner()
        sim_result = runner.run_frames(
            reordered,
            event_id="train_events/event_001",
            scenario_name="B4_default_sort",
            preserve_arrival_order=False,
        )
        assert len(sim_result.rejected_steps) == 0
        assert [s.timestamp_s for s in sim_result.steps] == [float(i) for i in range(10)]

    def test_collector_batch_preserve_arrival_order_triggers_rejection(self) -> None:
        r1 = EvidenceRecord(1.0, "camera_1", Modality.VISION, True, ())
        r2 = EvidenceRecord(3.0, "camera_1", Modality.VISION, True, ())
        r3 = EvidenceRecord(2.0, "camera_1", Modality.VISION, True, ())

        # Default sorts first
        c_sorted = MultimodalEvidenceCollector()
        c_sorted.add_evidence_batch([r1, r2, r3], preserve_arrival_order=False)
        assert len(c_sorted.rejected_observations) == 0

        # Arrival order preserved -> r3 (2.0 < 3.0) rejected by collector
        c_arrival = MultimodalEvidenceCollector()
        c_arrival.add_evidence_batch([r1, r2, r3], preserve_arrival_order=True)
        assert len(c_arrival.rejected_observations) == 1
        assert c_arrival.rejected_observations[0]["reason"] == "out_of_order_observation"
        assert c_arrival.rejected_observations[0]["local_timestamp_s"] == 2.0

    def test_metric_validator_not_weakened_on_raw_unsorted_steps(self) -> None:
        bad_result = SimulationRunResult(
            event_id="train_events/bad",
            scenario_name="bad",
            steps=[
                SimulationStep(2.0, "IDLE", "OPEN", 90.0, False, None),  # type: ignore[arg-type]
                SimulationStep(1.0, "IDLE", "OPEN", 90.0, False, None),  # type: ignore[arg-type]
            ],
            total_duration_s=2.0,
            closed_duration_s=0.0,
        )
        with pytest.raises(ValueError, match="strictly increasing"):
            EventMetricsCalculator.evaluate_run(bad_result)


# ===========================================================================
# 2. OBJECTIVE A2: B7e Delayed Timestamp Hardening
# ===========================================================================


class TestB7eDelayedTimestamps:
    @pytest.mark.parametrize(
        "bad_delay",
        [None, 0.0, -1.0, False, True, float("nan"), float("inf"), float("-inf"), "1.5"],
    )
    def test_invalid_or_missing_delay_rejected(self, bad_delay: object) -> None:
        frames = _make_dual_source_frames()
        params = {} if bad_delay is None else {"delay_s": bad_delay}
        sched = FailureSchedule(
            mode=FailureMode.STALE_TIMESTAMPS,
            start_time_s=2.0,
            end_time_s=5.0,
            target_source="camera_1",
            parameters=params,
        )
        with pytest.raises(ValueError, match="delay_s"):
            FailureInjector([sched]).inject_failures(frames)

    @pytest.mark.parametrize("bad_source", ["", "   ", None, 123])
    def test_missing_or_invalid_target_source_rejected(self, bad_source: object) -> None:
        frames = _make_dual_source_frames()
        params: dict[str, object] = {"delay_s": 1.5}
        if bad_source is not None:
            params["target_source"] = bad_source
        sched = FailureSchedule(
            mode=FailureMode.STALE_TIMESTAMPS,
            start_time_s=2.0,
            end_time_s=5.0,
            parameters=params,
        )
        with pytest.raises(ValueError, match="target_source"):
            FailureInjector([sched]).inject_failures(frames)

    @pytest.mark.parametrize("unknown_source", ["camera_99", "camera", "front", "unknown_mic"])
    def test_unknown_or_ambiguous_substring_source_rejected(self, unknown_source: str) -> None:
        frames = _make_dual_source_frames()
        sched = FailureSchedule(
            mode=FailureMode.STALE_TIMESTAMPS,
            start_time_s=2.0,
            end_time_s=5.0,
            target_source=unknown_source,
            parameters={"delay_s": 1.5},
        )
        with pytest.raises(ValueError, match="unknown target_source"):
            FailureInjector([sched]).inject_failures(frames)

    def test_valid_delay_shifts_only_target_source_and_preserves_content_and_trace(self) -> None:
        frames = _make_dual_source_frames()
        sched = FailureSchedule(
            mode=FailureMode.STALE_TIMESTAMPS,
            start_time_s=2.0,
            end_time_s=4.0,
            target_source="camera_1",
            parameters={"delay_s": 1.25},
        )
        injector = FailureInjector([sched])
        mutated1 = injector.inject_failures(frames)
        mutated2 = injector.inject_failures(frames)

        # Deterministic across runs
        assert mutated1 == mutated2

        # Repeated invocation does not compound delay
        re_mutated = injector.inject_failures(mutated1)
        assert re_mutated == mutated1

        for orig_f, mut_f in zip(frames, mutated1, strict=True):
            t = orig_f.master_timestamp_s
            assert mut_f.master_timestamp_s == t
            orig_c1 = next(r for r in orig_f.vision_records if r.source_id == "camera_1")
            orig_c2 = next(r for r in orig_f.vision_records if r.source_id == "camera_2")
            orig_a1 = orig_f.audio_records[0]

            mut_c1 = next(r for r in mut_f.vision_records if r.source_id == "camera_1")
            mut_c2 = next(r for r in mut_f.vision_records if r.source_id == "camera_2")
            mut_a1 = mut_f.audio_records[0]

            # Two-source isolation: camera_2 and audio_1 untouched
            assert mut_c2 == orig_c2
            assert mut_a1 == orig_a1

            # Detection content & availability preserved on camera_1
            assert mut_c1.detections == orig_c1.detections
            assert mut_c1.available == orig_c1.available
            assert mut_c1.modality == orig_c1.modality

            if 2.0 <= t <= 4.0:
                assert math.isclose(mut_c1.timestamp_s, t - 1.25)
                assert mut_c1.metadata["original_timestamp_s"] == t
                assert mut_c1.metadata["stale_timestamp_delay_s"] == 1.25
            else:
                assert mut_c1 == orig_c1

    def test_experiment_runner_b7e_without_schedule_fails_closed_before_simulation(
        self, tmp_path: Path
    ) -> None:
        event = LayerBEvent(
            event_id="train_events/event_001",
            labels=(EventLabel("crossing_entry", 3.0, "observed"),),
        )
        runner = ExperimentRunner(output_root=tmp_path / "exp")
        with pytest.raises(ValueError, match="B7e requires explicit FailureSchedule"):
            runner.run_condition(
                BenchmarkCondition.B7,
                [(event, _make_dual_source_frames())],
                sub_condition="B7e",
            )


# ===========================================================================
# 3. OBJECTIVE B: 14-Field Cache Provenance & Historical Isolation
# ===========================================================================


class TestCacheProvenance:
    def test_all_14_identity_fields_present_and_affect_cache_key(self) -> None:
        base = _make_provenance()
        assert set(base.identity_dict().keys()) == set(REQUIRED_PROVENANCE_FIELDS)
        assert len(REQUIRED_PROVENANCE_FIELDS) == 14

        mutations: dict[str, object] = {
            "cohort": "no_train_events",
            "event_id": "event_002",
            "source_id": "camera_2",
            "modality": "audio",
            "model_architecture": "yolov8s",
            "checkpoint_sha256": "c" * 64,
            "preprocessing_config": {"sampling_fps": 10.0, "conf": 0.35},
            "experiment_config_sha256": "d" * 64,
            "failure_injector": "B7e_stale_timestamps",
            "injector_parameters": {"delay_s": 1.0, "target_source": "camera_1"},
            "timing_config": {"tick_s": 0.1, "gate_closing_s": 3.0, "gate_opening_s": 3.0},
            "software_version": "0.2.0",
            "run_id": "synthetic-controlled-run-002",
        }
        for field_name, new_val in mutations.items():
            mutated = _make_provenance(**{field_name: new_val})
            assert mutated.provenance_sha256() != base.provenance_sha256(), field_name
            assert mutated.cache_key() != base.cache_key(), field_name
            with pytest.raises(CacheProvenanceError, match="PROVENANCE_MISMATCH"):
                validate_controlled_cache_provenance(mutated, base)

        # Schema version mismatch rejected at construction
        with pytest.raises(CacheProvenanceError, match="PROVENANCE_SCHEMA_VERSION_INVALID"):
            _make_provenance(cache_schema_version="legacy/1.0")

    def test_write_and_load_controlled_cache_roundtrip_and_mismatch_rejection(
        self, tmp_path: Path
    ) -> None:
        prov = _make_provenance()
        records = [
            EvidenceRecord(
                timestamp_s=0.0,
                source_id="camera_1",
                modality=Modality.VISION,
                available=True,
                detections=(Detection("front", 0.9, (1.0, 2.0, 3.0, 4.0)),),
                metadata={"frame_index": 0},
            )
        ]
        cache_file = write_controlled_cache_jsonl(tmp_path, prov, records)
        loaded = load_controlled_cache_jsonl(cache_file, prov)
        assert loaded == records

        # Loading with a different checkpoint or config fails closed
        wrong_ckpt = _make_provenance(checkpoint_sha256="9" * 64)
        with pytest.raises(CacheProvenanceError, match="PROVENANCE_MISMATCH"):
            load_controlled_cache_jsonl(cache_file, wrong_ckpt)

    def test_historical_unverified_cache_rejected_in_controlled_mode(
        self, tmp_path: Path
    ) -> None:
        legacy_file = tmp_path / "train_events_event_001_camera_front_camera_1_vision.jsonl"
        legacy_file.write_text(
            json.dumps(
                {
                    "timestamp_s": 0.0,
                    "source_id": "camera_1",
                    "modality": "vision",
                    "available": True,
                    "detections": [],
                    "metadata": {},
                }
            )
            + "\n",
            encoding="utf-8",
        )

        # Controlled loader rejects headerless historical file
        with pytest.raises(
            CacheProvenanceError, match="HISTORICAL_UNVERIFIED_CACHE_REJECTED"
        ):
            load_controlled_cache_jsonl(legacy_file, _make_provenance())

        # LayerBEventProcessor rejects headerless historical file by default
        proc = LayerBEventProcessor(cache_dir=tmp_path)
        fake_video = tmp_path / "train_events" / "event_001" / "camera_front.mov"
        with pytest.raises(
            CacheProvenanceError, match="HISTORICAL_UNVERIFIED_CACHE_REJECTED"
        ):
            proc.run_vision_inference(
                video_path=fake_video,
                checkpoint_path=Path("models/vision/best.pt"),
                source_id="camera_1",
                use_cache=True,
            )

        # Explicit historical diagnostic opt-in loads and marks records as historical_diagnostic
        hist_records = proc.run_vision_inference(
            video_path=fake_video,
            checkpoint_path=Path("models/vision/best.pt"),
            source_id="camera_1",
            use_cache=True,
            allow_historical_unverified_cache=True,
        )
        assert len(hist_records) == 1
        assert (
            hist_records[0].metadata["cache_classification"]
            == HISTORICAL_DIAGNOSTIC_CACHE_CLASS
        )
        assert hist_records[0].metadata["controlled_run_verified"] is False
        assert hist_records[0].metadata["official_evaluation_eligible"] is False

    def test_raw_media_reference_in_provenance_rejected(self) -> None:
        with pytest.raises(CacheProvenanceError, match="RAW_MEDIA_REFERENCE_FORBIDDEN"):
            _make_provenance(preprocessing_config={"source_video": "camera_front.mov"})


# ===========================================================================
# 4. OBJECTIVE A3 & C: Ground-Truth States & Cohort/Engine Isolation
# ===========================================================================


class TestGroundTruthAndCohortIsolation:
    def test_missing_ground_truth_neither_positive_train_nor_negative_control(
        self, tmp_path: Path
    ) -> None:
        missing_event = LayerBEvent(event_id="train_events/event_missing", labels=())
        runner = ExperimentRunner(output_root=tmp_path / "exp")
        summary = runner.run_condition(
            BenchmarkCondition.B4, [(missing_event, _make_dual_source_frames())]
        )
        assert summary.total_events == 1
        assert summary.eligible_events == 0
        assert summary.no_train_events == 0
        assert summary.false_alarm_evaluable_count == 0
        assert summary.engine_events == 0
        single = summary.single_events[0]
        assert single.evaluable is False
        assert single.has_train_ground_truth is False
        assert single.notes == "ground_truth_missing"
        assert single.exclusion_reasons == {"ground_truth": "missing"}

    @pytest.mark.parametrize(
        "non_obs_status",
        ["censored", "uncertain", "unobservable", "not_applicable", "unknown"],
    )
    def test_non_observable_boundary_states_never_fabricated_into_timestamps(
        self, tmp_path: Path, non_obs_status: str
    ) -> None:
        event = LayerBEvent(
            event_id=f"train_events/event_{non_obs_status}",
            labels=(
                EventLabel("crossing_entry", 3.0, non_obs_status),
                EventLabel("tail_clearance", 8.0, non_obs_status),
            ),
        )
        runner = ExperimentRunner(output_root=tmp_path / "exp")
        summary = runner.run_condition(
            BenchmarkCondition.B4, [(event, _make_dual_source_frames())]
        )
        assert summary.eligible_events == 0
        assert summary.no_train_events == 0
        single = summary.single_events[0]
        assert single.evaluable is False
        assert single.warning_lead_time_s is None
        assert single.excess_closed_duration_s is None
        assert single.clearance_latency_s is None
        assert single.exclusion_reasons["T1_danger_zone_entry"] == non_obs_status
        assert single.exclusion_reasons["T4_tail_clearance"] == non_obs_status

    def test_cohort_separation_train_notrain_engine_and_missing(
        self, tmp_path: Path
    ) -> None:
        frames = _make_dual_source_frames()
        train_ev = LayerBEvent(
            event_id="train_events/event_001",
            train_type="passenger",
            labels=(
                EventLabel("crossing_entry", 3.0, "observed"),
                EventLabel("tail_clearance", 8.0, "observed"),
            ),
        )
        no_train_ev = LayerBEvent(
            event_id="no_train_events/event_001",
            train_type="no_train",
            labels=(EventLabel("no_train", None, "observed"),),
        )
        engine_ev = LayerBEvent(
            event_id="engine_events/event_001",
            train_type="engine",
            labels=(EventLabel("T3_locomotive_unit_clearance", 6.0, "observed"),),
        )
        missing_ev = LayerBEvent(
            event_id="train_events/event_unlabeled",
            labels=(),
        )

        runner = ExperimentRunner(output_root=tmp_path / "exp")
        summary = runner.run_condition(
            BenchmarkCondition.B4,
            [
                (train_ev, frames),
                (no_train_ev, frames),
                (engine_ev, frames),
                (missing_ev, frames),
            ],
        )
        assert summary.total_events == 4
        assert summary.eligible_events == 1  # only train_events/event_001
        assert summary.no_train_events == 1  # only no_train_events/event_001
        assert summary.false_alarm_evaluable_count == 1
        assert summary.engine_events == 1  # only engine_events/event_001

        by_id = {e.event_id: e for e in summary.single_events}
        assert by_id["engine_events/event_001"].notes == "engine_event_excluded"
        assert by_id["engine_events/event_001"].evaluable is False
        assert by_id["train_events/event_unlabeled"].notes == "ground_truth_missing"
        assert by_id["train_events/event_unlabeled"].evaluable is False

    def test_clock_aware_evaluate_event_replay_isolates_engine_event(self) -> None:
        step0 = SimulationStep(0.0, "IDLE", "OPEN", 90.0, False, None)  # type: ignore[arg-type]
        step1 = SimulationStep(1.0, "TRAIN_PRESENT", "CLOSED", 0.0, True, None)  # type: ignore[arg-type]
        sim = SimulationRunResult(
            event_id="engine_events/event_001",
            scenario_name="s",
            steps=[step0, step1],
            total_duration_s=1.0,
            closed_duration_s=1.0,
        )
        replay = EventReplay(
            event_id="engine_events/event_001",
            cohort="engine_events",
            camera_mode="single_camera",
            systems={"front": SystemReplay("front", {"front": 0.0}, sim)},
        )
        truth = ApprovedEventGroundTruth(
            event_id="engine_events/event_001",
            cohort="engine_events",
            review_id="r1",
            reviewer_id="rev1",
            observable_boundaries={"T3_locomotive_unit_clearance": 0.8},
            censored_boundaries=(),
            uncertain_boundaries=(),
            not_applicable_boundaries=("T4_tail_clearance",),
            boundary_cameras={"T3_locomotive_unit_clearance": "front"},
        )
        ev = evaluate_event_replay(replay, truth)
        assert ev.notes == "engine_event_excluded"
        assert ev.evaluable is False
        assert ev.has_train_ground_truth is False

        summary = EventMetricsCalculator.aggregate_cohort([ev])
        assert summary.engine_events == 1
        assert summary.eligible_events == 0
        assert summary.no_train_events == 0
        assert summary.false_alarm_evaluable_count == 0


# ===========================================================================
# 5. OBJECTIVE D: Descriptive-Only vs Official Evaluation Isolation
# ===========================================================================


class TestDescriptiveOfficialIsolation:
    def test_descriptive_only_rejects_cross_site_and_official_claims(self) -> None:
        ev = SingleEventEvaluation(
            event_id="train_events/event_001",
            scenario_name="desc",
            has_train_ground_truth=True,
            missed_train=False,
        )
        for bad_claim in (
            "demonstrates cross-site generalization across Bangladesh",
            "official test-set benchmark performance",
            "held-out test accuracy",
        ):
            inp = DescriptiveOnlyInput(
                event_evaluations=(ev,),
                population_label="fixed_site_population",
                provenance={"source": "synthetic"},
                limitations=("fixed-site only",),
                permitted_claims=(bad_claim,),
            )
            with pytest.raises(DescriptiveOnlyRefusal, match="FORBIDDEN_CLAIM_SCOPE"):
                aggregate_descriptive_only(inp)

    def test_descriptive_only_isolates_engine_case_study_and_blocks_pooling(self) -> None:
        train_ev = SingleEventEvaluation(
            event_id="train_events/event_001",
            scenario_name="desc",
            has_train_ground_truth=True,
            missed_train=False,
            evaluable=True,
        )
        bad_engine_ev = SingleEventEvaluation(
            event_id="engine_events/event_001",
            scenario_name="desc",
            has_train_ground_truth=True,
            missed_train=False,
            evaluable=True,
        )
        with pytest.raises(DescriptiveOnlyRefusal, match="ENGINE_EVENT_POOLING_REFUSED"):
            aggregate_descriptive_only(
                DescriptiveOnlyInput(
                    event_evaluations=(train_ev, bad_engine_ev),
                    population_label="fixed_site",
                    provenance={"source": "synthetic"},
                    limitations=("fixed-site only",),
                    permitted_claims=("fixed-site descriptive summary",),
                )
            )

        isolated_engine_ev = SingleEventEvaluation(
            event_id="engine_events/event_001",
            scenario_name="desc",
            has_train_ground_truth=False,
            missed_train=False,
            evaluable=False,
            notes="engine_event_excluded",
        )
        report = aggregate_descriptive_only(
            DescriptiveOnlyInput(
                event_evaluations=(train_ev, isolated_engine_ev),
                population_label="fixed_site",
                provenance={"source": "synthetic"},
                limitations=("fixed-site only", "no cross-site generalization"),
                permitted_claims=("fixed-site descriptive summary",),
            )
        )
        assert report.official_evaluation_eligible is False
        assert report.engine_case_study_ids == ("engine_events/event_001",)
        assert report.summary.eligible_events == 1
        assert report.summary.engine_events == 1
        assert report.summary.no_train_events == 0

    def test_descriptive_only_blocks_historical_masquerading_as_controlled(self) -> None:
        ev = SingleEventEvaluation(
            event_id="train_events/event_001",
            scenario_name="desc",
            has_train_ground_truth=True,
            missed_train=False,
        )
        with pytest.raises(DescriptiveOnlyRefusal, match="HISTORICAL_AS_CONTROLLED_REFUSED"):
            aggregate_descriptive_only(
                DescriptiveOnlyInput(
                    event_evaluations=(ev,),
                    population_label="fixed_site",
                    provenance={
                        "source_category": "historical_diagnostic",
                        "claimed_category": "controlled_experimental",
                    },
                    limitations=("fixed-site only",),
                    permitted_claims=("fixed-site descriptive summary",),
                )
            )

    def test_official_manifest_loader_rejects_descriptive_only_report(
        self, tmp_path: Path
    ) -> None:
        ev = SingleEventEvaluation(
            event_id="train_events/event_001",
            scenario_name="desc",
            has_train_ground_truth=True,
            missed_train=False,
        )
        report = aggregate_descriptive_only(
            DescriptiveOnlyInput(
                event_evaluations=(ev,),
                population_label="fixed_site",
                provenance={"source": "synthetic"},
                limitations=("fixed-site only",),
                permitted_claims=("fixed-site descriptive summary",),
            )
        )
        desc_path = tmp_path / "descriptive_report.json"
        desc_path.write_text(json.dumps(report.to_dict()), encoding="utf-8")
        with pytest.raises(EvaluationInputError):
            load_evaluation_input_manifest(desc_path, verify_sources=False)


# ===========================================================================
# 6. OBJECTIVE E: Stage-2.1 Human Review Validation (Synthetic Only)
# ===========================================================================


class TestStage21SyntheticValidation:
    @staticmethod
    def _make_stage21_record(
        tmp_path: Path,
        *,
        event_id: str = "event_001",
        cohort: str = "train_events",
        reviewer_id: str = "dr_rahman_reviewer",
        start_offset_s: int = 0,
        duration_s: int = 120,
    ) -> tuple[dict, dict, dict, Path]:
        t0 = datetime(2026, 11, 1, 10, 0, 0, tzinfo=UTC) + timedelta(seconds=start_offset_s)
        t_start = t0.isoformat().replace("+00:00", "Z")
        t_end = (t0 + timedelta(seconds=duration_s)).isoformat().replace("+00:00", "Z")

        front = tmp_path / f"{cohort}_{event_id}_front.bin"
        back = tmp_path / f"{cohort}_{event_id}_back.bin"
        front.write_bytes(f"synthetic-front-{cohort}-{event_id}".encode())
        back.write_bytes(f"synthetic-back-{cohort}-{event_id}".encode())
        f_sha = hashlib.sha256(front.read_bytes()).hexdigest()
        b_sha = hashlib.sha256(back.read_bytes()).hexdigest()
        prop_sha = "e" * 64

        allowlist_path = tmp_path / "authorized_reviewers.json"
        allowlist_path.write_text(
            json.dumps({"authorized_reviewers": ["dr_rahman_reviewer"]}),
            encoding="utf-8",
        )

        record = {
            "schema_version": STAGE_2_1_SCHEMA_VERSION,
            "review_id": f"rev_{cohort}_{event_id}",
            "event_id": event_id,
            "cohort": cohort,
            "proposal_reference": {
                "proposal_file": f"proposals/{cohort}/{event_id}_proposal_v6.json",
                "proposal_sha256": prop_sha,
            },
            "reviewer_metadata": {
                "reviewer_id": reviewer_id,
                "review_session_id": f"sess_{cohort}_{event_id}",
                "review_start_utc": t_start,
                "review_end_utc": t_end,
                "inspection_tool": "ffmpeg frame-by-frame manual inspection",
            },
            "model_independence_attestation": {
                "attested": True,
                "statement": "Reviewed raw media independently without model predictions.",
                "attested_at_utc": t_end,
            },
            "reviewer_observed_media_hashes": {
                "front_sha256": f_sha,
                "back_sha256": b_sha,
                "observed_at_utc": t_start,
            },
            "boundary_adjudications": {
                "T0_first_visible": {
                    "state": "OBSERVABLE",
                    "rationale": "Visible at frame 10",
                    "value_s": 2.0,
                    "reference_camera": "front",
                },
                "T1_danger_zone_entry": {
                    "state": "OBSERVABLE",
                    "rationale": "Enters danger zone at frame 30",
                    "value_s": 6.0,
                    "reference_camera": "front",
                },
                "T2_crossing_occupancy_start": {
                    "state": "OBSERVABLE",
                    "rationale": "Crosses plane at frame 35",
                    "value_s": 7.0,
                    "reference_camera": "front",
                },
                "T3_locomotive_unit_clearance": {
                    "state": "OBSERVABLE",
                    "rationale": "Loco clears at frame 60",
                    "value_s": 12.0,
                    "reference_camera": "back",
                },
                "T4_tail_clearance": {
                    "state": "OBSERVABLE",
                    "rationale": "Tail clears at frame 100",
                    "value_s": 20.0,
                    "reference_camera": "back",
                },
                "T_scene_clear": {
                    "state": "CENSORED",
                    "rationale": "Clip ends before scene clear",
                    "value_s": None,
                    "reference_camera": None,
                },
            },
            "adjudication_status": "APPROVED",
            "adjudication_history": [
                {
                    "event": "created",
                    "by": reviewer_id,
                    "at_utc": t_end,
                    "status_set": "APPROVED",
                }
            ],
        }
        key = f"{cohort}/{event_id}"
        registry = {key: {"front": f_sha, "back": b_sha}}
        paths = {key: {"front": str(front), "back": str(back)}}
        return record, registry, paths, allowlist_path

    def test_overlapping_sessions_and_media_tampering_rejected(
        self, tmp_path: Path
    ) -> None:
        r1, reg1, paths1, allowlist = self._make_stage21_record(
            tmp_path, event_id="event_001", cohort="train_events", start_offset_s=0, duration_s=120
        )
        # r2 overlaps r1 [0s, 120s] by starting at 60s under the same reviewer
        r2, reg2, paths2, _ = self._make_stage21_record(
            tmp_path, event_id="event_002", cohort="train_events", start_offset_s=60, duration_s=120
        )
        violations = check_review_batch_integrity([r1, r2])
        assert any(v.code == "OVERLAPPING_REVIEW_SESSIONS" for v in violations)

        # Tampering with live media file after review is caught at promotion
        Path(paths1["train_events/event_001"]["front"]).write_bytes(b"tampered-bytes")
        promo_violations = validate_for_promotion(
            r1,
            active_proposal_sha256_by_event={"train_events/event_001": "e" * 64},
            media_sha256_registry=reg1,
            authorized_reviewers=frozenset({"dr_rahman_reviewer"}),
            media_file_paths=paths1,
        )
        codes = {v.code for v in promo_violations}
        assert "MEDIA_HASH_CHANGED_SINCE_REGISTRY" in codes
        assert "MEDIA_HASH_CHANGED_SINCE_REVIEW" in codes
