"""Synthetic unit and integration tests for the exploratory replay & analysis suite.

All tests operate strictly on temporary synthetic fixtures and in-memory structures.
Never reads raw media or bypasses canonical Stage-2.1 execution gates.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = REPO_ROOT / "src"
SCRIPTS_DIR = REPO_ROOT / "scripts"
for p in (str(SRC_DIR), str(SCRIPTS_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from compute_ablation_matrix import exact_mcnemar_pvalue  # noqa: E402
from compute_safety_metrics import (  # noqa: E402
    _check_v9_legacy_premature,
    _count_false_alarm_episodes,
    compute_convention_b_closed_duration,
)
from exploratory_common import (  # noqa: E402
    EventReferenceMetadata,
    ExploratoryValidationError,
    StatelessThresholdEngine,
    VerifiedExploratoryContext,
    assemble_frames,
    load_event_evidence_records,
    read_verified_utf8_text,
    resolve_safe_text_path,
    serialize_simulation_result,
    simulate_frames,
    wilson_ci_95,
)
from railway_detection.fusion.evidence import (  # noqa: E402
    Detection,
    EvidenceRecord,
    Modality,
)
from railway_detection.fusion.rules import CrossingState, GateState, RuleId  # noqa: E402


def _make_synthetic_config() -> SimpleNamespace:
    timing = SimpleNamespace(
        tick_s=0.2,
        confirm_frames=2,
        miss_tolerance_frames=2,
        warning_dwell_s=2.0,
        gate_closing_s=1.5,
        gate_opening_s=1.5,
        clearance_dwell_s=1.0,
        source_staleness_s=1.0,
        fault_confirmation_frames=2,
        fault_recovery_hold_s=3.0,
    )
    vision = SimpleNamespace(
        sampling_fps=5.0,
        image_size=(640, 640),
        confidence_threshold_approach=0.35,
        confidence_threshold_departure=0.35,
    )
    audio = SimpleNamespace(operating_threshold=0.37)
    return SimpleNamespace(timing=timing, vision=vision, audio=audio)


def _make_ref(
    *,
    event_id: str = "train_events/event_syn",
    is_dual_sync_accepted: bool = False,
    calibration_verdict: str = "INDEPENDENT_ONLY",
    back_offset_s: float | None = None,
    back_uncertainty_s: float | None = None,
) -> EventReferenceMetadata:
    return EventReferenceMetadata(
        event_id=event_id,
        event_key=event_id.replace("/", "_"),
        cohort=event_id.split("/")[0],
        event_type="train",
        active_proposal_path="synthetic.json",
        active_proposal_sha256="0" * 64,
        proposal_schema="synthetic/1",
        train_present=True,
        train_direction="left_to_right",
        train_type="passenger",
        trailing_cars_count=5,
        horn_status="absent_observed",
        horn_onset_s=None,
        lighting="daylight",
        weather="clear",
        front_duration_s=10.0,
        back_duration_s=10.0,
        is_dual_sync_accepted=is_dual_sync_accepted,
        calibration_verdict=calibration_verdict,
        back_offset_s=back_offset_s,
        back_uncertainty_s=back_uncertainty_s,
        t0_raw_s=1.0,
        t0_cam="front",
        t0_ambiguity=False,
        t1_raw_s=2.0,
        t1_cam="front",
        t2_raw_s=5.0,
        t2_cam="front",
        t3_raw_s=6.0,
        t3_cam="back",
        t4_raw_s=7.0,
        t4_cam="back",
    )


def test_resolve_safe_text_path_rejects_raw_media_and_escapes(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    (root / "data" / "raw" / "layer_b").mkdir(parents=True)
    (root / "data" / "raw" / "layer_b" / "clip.mov").write_text("dummy", encoding="utf-8")
    (root / "ok.json").write_text("{}\n", encoding="utf-8")
    (root / "weights.pt").write_text("dummy", encoding="utf-8")

    with pytest.raises(ExploratoryValidationError, match="data/raw"):
        resolve_safe_text_path(root, "data/raw/layer_b/clip.mov")

    with pytest.raises(ExploratoryValidationError, match="extension"):
        resolve_safe_text_path(root, "weights.pt")

    with pytest.raises(ExploratoryValidationError, match="escapes"):
        resolve_safe_text_path(root, "../outside.json")

    ok = resolve_safe_text_path(root, "ok.json")
    assert ok == (root / "ok.json").resolve()


def test_read_verified_utf8_text_enforces_sha256(tmp_path: Path) -> None:
    target = tmp_path / "sample.jsonl"
    payload = '{"a": 1}\n'
    target.write_text(payload, encoding="utf-8")
    expected_sha = hashlib.sha256(payload.encode("utf-8")).hexdigest()

    text, digest = read_verified_utf8_text(tmp_path, "sample.jsonl", expected_sha256=expected_sha)
    assert text == payload
    assert digest == expected_sha

    with pytest.raises(ExploratoryValidationError, match="SHA-256 mismatch"):
        read_verified_utf8_text(tmp_path, "sample.jsonl", expected_sha256="f" * 64)


def test_boundaries_for_clock_isolation_and_fail_closed_master() -> None:
    uncal = _make_ref(is_dual_sync_accepted=False)
    front_bounds = uncal.boundaries_for_clock("front")
    assert front_bounds["t1"] == 2.0
    assert front_bounds["t3"] is None
    assert front_bounds["t4"] is None

    back_bounds = uncal.boundaries_for_clock("back")
    assert back_bounds["t1"] is None
    assert back_bounds["t3"] == 6.0
    assert back_bounds["t4"] == 7.0

    with pytest.raises(ExploratoryValidationError, match="uncalibrated"):
        uncal.boundaries_for_clock("master")

    cal = _make_ref(
        is_dual_sync_accepted=True,
        calibration_verdict="CALIBRATION_SUPPORTED",
        back_offset_s=4.5,
        back_uncertainty_s=0.1,
    )
    master_bounds = cal.boundaries_for_clock("master")
    assert master_bounds["t1"] == 2.0
    assert master_bounds["t3"] == 10.5
    assert master_bounds["t4"] == 11.5


def test_load_event_evidence_records_refuses_event_010_and_unaccepted_dual(tmp_path: Path) -> None:
    dummy_jsonl = '{"timestamp_sec": 0.0, "detections": []}\n'
    dummy_sha = hashlib.sha256(dummy_jsonl.encode("utf-8")).hexdigest()
    (tmp_path / "f.jsonl").write_text(dummy_jsonl, encoding="utf-8")

    # Even if calibration_verdict is CALIBRATION_SUPPORTED (like train_events/event_010),
    # exclusion from accepted_sync_events must fail closed under DUAL_* conditions.
    ref_010 = _make_ref(
        event_id="train_events/event_010",
        is_dual_sync_accepted=False,
        calibration_verdict="CALIBRATION_SUPPORTED",
        back_offset_s=3.0,
        back_uncertainty_s=0.1,
    )
    ctx = VerifiedExploratoryContext(
        repo_root=tmp_path,
        manifest_sha256="0" * 64,
        manifest_events={
            "train_events/event_010": {
                "event_id": "train_events/event_010",
                "front_cache_path": "f.jsonl",
                "front_cache_sha256": dummy_sha,
                "back_cache_path": "f.jsonl",
                "back_cache_sha256": dummy_sha,
                "audio_cache_path": "f.jsonl",
                "audio_cache_sha256": dummy_sha,
            }
        },
        event_order=("train_events/event_010",),
        accepted_sync_events=frozenset({"train_events/event_001"}),
        references={"train_events/event_010": ref_010},
        calibration_events={},
        frozen_config=_make_synthetic_config(),
        artifact_hashes={},
    )
    with pytest.raises(ExploratoryValidationError, match="NOT in the 11 accepted sync events"):
        load_event_evidence_records(ctx, "train_events/event_010", "DUAL_VISION_AUDIO")

    recs, aligner, clock_mode = load_event_evidence_records(ctx, "train_events/event_010", "B0")
    assert len(recs) == 1
    assert aligner is None
    assert clock_mode == "front"


def test_stateless_threshold_engine_modes_fail_safe_and_out_of_order() -> None:
    from railway_detection.fusion.collector import MultimodalFrame

    cfg = _make_synthetic_config()
    frames = [
        MultimodalFrame(
            master_timestamp_s=0.0,
            vision_records=(
                EvidenceRecord(
                    timestamp_s=0.0, source_id="camera_1", modality=Modality.VISION, available=True, detections=()
                ),
            ),
            audio_records=(
                EvidenceRecord(
                    timestamp_s=0.0,
                    source_id="audio_1",
                    modality=Modality.AUDIO,
                    available=True,
                    detections=(Detection(label="train_horn", confidence=0.95),),
                ),
            ),
            source_availability={"camera_1": True, "audio_1": True},
        ),
        MultimodalFrame(
            master_timestamp_s=0.2,
            vision_records=(
                EvidenceRecord(
                    timestamp_s=0.2, source_id="camera_1", modality=Modality.VISION, available=True, detections=()
                ),
            ),
            audio_records=(
                EvidenceRecord(
                    timestamp_s=0.2, source_id="audio_1", modality=Modality.AUDIO, available=True, detections=()
                ),
            ),
            source_availability={"camera_1": True, "audio_1": True},
        ),
        MultimodalFrame(
            master_timestamp_s=0.4,
            vision_records=(
                EvidenceRecord(
                    timestamp_s=0.4, source_id="camera_1", modality=Modality.VISION, available=False, detections=()
                ),
            ),
            audio_records=(),
            source_availability={"camera_1": False, "audio_1": True},
        ),
    ]

    rule2_eng = StatelessThresholdEngine(config=cfg, allow_audio_trigger=False)
    d0 = rule2_eng.evaluate_frame(frames[0])
    assert d0.resulting_gate_state == GateState.OPEN.value

    union_eng = StatelessThresholdEngine(config=cfg, allow_audio_trigger=True)
    u0 = union_eng.evaluate_frame(frames[0])
    u1 = union_eng.evaluate_frame(frames[1])
    assert u0.resulting_gate_state == GateState.CLOSED.value
    assert u1.resulting_gate_state == GateState.OPEN.value

    fs_eng = StatelessThresholdEngine(config=cfg, allow_audio_trigger=False, fail_safe_on_all_vision_loss=True)
    fs0 = fs_eng.evaluate_frame(frames[0])
    assert fs0.resulting_gate_state == GateState.OPEN.value
    fs_out = fs_eng.evaluate_frame(frames[2])
    assert fs_out.resulting_state == CrossingState.FAULT_FAIL_SAFE.value
    assert fs_out.resulting_gate_state == GateState.CLOSED.value
    ooo = fs_eng.evaluate_frame(frames[0])
    assert ooo.rule_id == RuleId.RULE_8_OUT_OF_ORDER_REJECTION.value


def test_window_tolerance_backfill_single_detection_and_deterministic_replay() -> None:
    cfg = _make_synthetic_config()
    records = []
    for k in range(25):
        t = round(k * 0.2, 4)
        dets = (
            (Detection(label="front", confidence=0.80),)
            if k == 10  # ONE isolated detection at t=2.0s only
            else ()
        )
        records.append(
            EvidenceRecord(
                timestamp_s=t,
                source_id="camera_1",
                modality=Modality.VISION,
                available=True,
                detections=dets,
            )
        )

    frames_wide = assemble_frames(records, aligner=None, stride_s=0.2, window_tolerance_s=0.5)
    frames_tight = assemble_frames(records, aligner=None, stride_s=0.2, window_tolerance_s=0.15)

    res_wide_1, _ = simulate_frames(frames_wide, event_id="syn/1", scenario_name="wide", policy="v2", config=cfg)
    res_wide_2, _ = simulate_frames(frames_wide, event_id="syn/1", scenario_name="wide", policy="v2", config=cfg)
    res_tight, _ = simulate_frames(frames_tight, event_id="syn/1", scenario_name="tight", policy="v2", config=cfg)

    # With window_tolerance=0.5s > stride=0.2s, one isolated observation persists across 3 ticks,
    # defeating confirm_frames=2 and closing the gate; tight window (0.15s) only enters unconfirmed
    # TRAIN_APPROACHING for one tick with zero warning/closure.
    assert res_wide_1.closed_duration_s > 0.0
    assert any(s.crossing_state == CrossingState.WARNING.value for s in res_wide_1.steps)
    assert res_tight.closed_duration_s == 0.0
    assert not any(
        s.crossing_state in {CrossingState.WARNING.value, CrossingState.GATE_CLOSING.value, CrossingState.TRAIN_PRESENT.value}
        for s in res_tight.steps
    )

    ref = _make_ref(event_id="syn/1")
    ser1 = json.dumps(
        serialize_simulation_result(
            res_wide_1,
            event_id="syn/1",
            condition="B0",
            policy="v2",
            clock_mode="front",
            ref=ref,
            mapped_bounds=ref.boundaries_for_clock("front"),
            window_tolerance_s=0.5,
            stride_s=0.2,
        ),
        sort_keys=True,
    )
    ser2 = json.dumps(
        serialize_simulation_result(
            res_wide_2,
            event_id="syn/1",
            condition="B0",
            policy="v2",
            clock_mode="front",
            ref=ref,
            mapped_bounds=ref.boundaries_for_clock("front"),
            window_tolerance_s=0.5,
            stride_s=0.2,
        ),
        sort_keys=True,
    )
    assert ser1 == ser2


def test_convention_b_closed_duration_exact_identity_and_v9_checks() -> None:
    steps_open_end = [
        {"t": 0.0, "is_passage_blocked": False, "gate_state": GateState.OPEN.value, "crossing_state": "IDLE"},
        {"t": 0.2, "is_passage_blocked": True, "gate_state": GateState.CLOSED.value, "crossing_state": "GATE_CLOSED"},
        {"t": 0.4, "is_passage_blocked": True, "gate_state": GateState.CLOSED.value, "crossing_state": "GATE_CLOSED"},
        {"t": 0.6, "is_passage_blocked": False, "gate_state": GateState.OPENING.value, "crossing_state": "GATE_OPENING"},
    ]
    conv_a, conv_b, b_last = compute_convention_b_closed_duration(steps_open_end)
    assert b_last == 0
    assert conv_a == pytest.approx(0.4)
    assert conv_b == pytest.approx(0.4)
    assert _check_v9_legacy_premature(steps_open_end, 0.2, 0.5) is False
    assert _check_v9_legacy_premature(steps_open_end, 0.2, 0.8) is True
    assert _count_false_alarm_episodes(steps_open_end) == 1

    steps_blocked_end = [
        {"t": 0.0, "is_passage_blocked": False, "gate_state": GateState.OPEN.value, "crossing_state": "IDLE"},
        {"t": 0.2, "is_passage_blocked": True, "gate_state": GateState.CLOSED.value, "crossing_state": "GATE_CLOSED"},
        {"t": 0.4, "is_passage_blocked": True, "gate_state": GateState.CLOSED.value, "crossing_state": "GATE_CLOSED"},
    ]
    conv_a2, conv_b2, b_last2 = compute_convention_b_closed_duration(steps_blocked_end)
    assert b_last2 == 1
    assert conv_a2 == pytest.approx(0.4)
    assert conv_b2 == pytest.approx(0.2)
    assert round(conv_b2 - conv_a2, 6) == pytest.approx(-0.2)


def test_exact_mcnemar_pvalue_and_wilson_ci() -> None:
    assert exact_mcnemar_pvalue(0, 0) == 1.0
    assert exact_mcnemar_pvalue(5, 5) == 1.0
    assert exact_mcnemar_pvalue(8, 0) == pytest.approx(0.007812, abs=1e-6)
    assert exact_mcnemar_pvalue(0, 8) == pytest.approx(0.007812, abs=1e-6)
    assert exact_mcnemar_pvalue(13, 0) == pytest.approx(0.000244, abs=1e-6)

    p, lo, hi = wilson_ci_95(2, 11)
    assert p == pytest.approx(2.0 / 11.0)
    assert 0.0 < lo < p < hi < 1.0
    assert wilson_ci_95(0, 0) == (0.0, 0.0, 0.0)
