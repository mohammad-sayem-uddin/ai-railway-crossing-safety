"""Comprehensive synthetic unit, safety-invariant, fault-injection, and E2E integration tests
for the V3 Four-Layer Multimodal Railway Crossing Protection System.

Strictly SYNTHETIC_ONLY: reads no raw media, weights, results, or data files and spawns no
subprocesses so ``scripts/classify_test_access.py`` verifies clean sandbox isolation.
"""

from __future__ import annotations

import hashlib
import json
import math
from fractions import Fraction
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from railway_detection.audio.features import compute_log_mel_spectrogram
from railway_detection.config.exceptions import ConfigError
from railway_detection.demo import video_demo
from railway_detection.fusion.collector import MultimodalEvidenceCollector
from railway_detection.fusion.decision_engine_v3_four_layer import (
    MultimodalDecisionEngineV3FourLayer,
)
from railway_detection.fusion.evidence import (
    Detection,
    EvidenceRecord,
    EvidenceStatus,
    Modality,
    OccupancyEvidence,
    OccupancyState,
    classify_evidence_status,
)
from railway_detection.fusion.occupancy import OccupancyVerifier
from railway_detection.fusion.rules import CrossingState, GateState
from railway_detection.fusion.rules_v3_four_layer import (
    DeparturePolicyMode,
    RuleIdV3,
    SideMovementTracker,
)
from railway_detection.simulation.gate_model import PhysicalGateModel
from railway_detection.simulation.runner import EventSimulationRunner
from railway_detection.simulation.state_machine import (
    ALLOWED_TRANSITIONS,
    CrossingStateMachine,
    InvalidTransitionError,
)
from railway_detection.vision.video import (
    apply_display_rotation,
    frame_generator,
    normalize_orthogonal_rotation,
)


def _det(
    label: str,
    conf: float = 0.85,
    bbox: tuple[float, float, float, float] | None = None,
) -> Detection:
    return Detection(label=label, confidence=conf, bbox_xyxy=bbox)


def _rec(
    t: float,
    source_id: str,
    modality: Modality,
    dets: tuple[Detection, ...] = (),
    *,
    available: bool = True,
    metadata: dict | None = None,
) -> EvidenceRecord:
    return EvidenceRecord(
        timestamp_s=round(float(t), 3),
        source_id=source_id,
        modality=modality,
        available=available,
        detections=list(dets),
        metadata=metadata or {},
    )


def _occ(
    t: float,
    state: OccupancyState,
    *,
    source_id: str = "occ_sensor_1",
    available: bool = True,
    metadata: dict | None = None,
) -> OccupancyEvidence:
    return OccupancyEvidence(
        timestamp_s=round(float(t), 3),
        source_id=source_id,
        state=state,
        available=available,
        confidence=0.95 if available and state in (OccupancyState.CLEAR, OccupancyState.OCCUPIED) else None,
        metadata=metadata or {},
    )


def _build_nominal_streams(
    *,
    duration_s: float = 24.0,
    dt_s: float = 0.2,
    include_back_rear: bool = True,
    include_occ: bool = True,
    include_side: bool = True,
    include_audio: bool = True,
    include_tail: bool = False,
) -> tuple[list[EvidenceRecord], list[OccupancyEvidence]]:
    """Construct a complete, physically consistent 4-layer crossing event on [0, duration_s]."""
    recs: list[EvidenceRecord] = []
    occs: list[OccupancyEvidence] = []
    n_steps = int(round(duration_s / dt_s))
    for i in range(n_steps + 1):
        t = round(i * dt_s, 3)

        # Layer 1: front camera active during approach [1.0, 5.0]
        front_dets = [_det("front", 0.90, (20.0, 40.0, 120.0, 140.0))] if 1.0 <= t <= 5.0 else []
        recs.append(_rec(t, "camera_1", Modality.VISION, tuple(front_dets)))

        # Layer 2: dedicated side camera moving laterally during crossing [4.0, 11.4]
        if include_side:
            if 4.0 <= t <= 11.4:
                shift = (t - 4.0) * 18.0
                side_dets = [_det("side", 0.88, (40.0 + shift, 50.0, 140.0 + shift, 150.0))]
            else:
                side_dets = []
            recs.append(_rec(t, "camera_side", Modality.VISION, tuple(side_dets)))

        # Layer 3: audio horn bursts on 0.5 s hop intervals ([1.5, 4.5] and [6.0, 9.5])
        if include_audio and (round(t * 10) % 5 == 0):
            horn_active = (1.5 <= t <= 4.5) or (6.0 <= t <= 9.5)
            a_dets = [_det("train", 0.82 if horn_active else 0.08)]
            recs.append(_rec(t, "audio_1", Modality.AUDIO, tuple(a_dets)))

        # Layer 4: back camera observes carriage [8.0, 11.0], rear/tail [11.2, 12.6], clear afterwards
        if 8.0 <= t <= 11.0:
            shift_b = (t - 8.0) * 18.0
            b_dets = [_det("side", 0.85, (10.0 + shift_b, 40.0, 110.0 + shift_b, 140.0))]
        elif include_back_rear and 11.2 <= t <= 12.6:
            b_dets = [_det("rear", 0.90, (30.0, 40.0, 110.0, 140.0))]
            if include_tail and 12.0 <= t <= 12.6:
                b_dets.append(_det("last_carriage", 0.87, (35.0, 45.0, 105.0, 135.0)))
        else:
            b_dets = []
        recs.append(_rec(t, "camera_2", Modality.VISION, tuple(b_dets)))

        # Occupancy sensor: OCCUPIED while train occupies crossing [4.0, 12.8], CLEAR otherwise
        if include_occ:
            occ_state = OccupancyState.OCCUPIED if 4.0 <= t <= 12.8 else OccupancyState.CLEAR
            occs.append(_occ(t, occ_state))

    return recs, occs


def _run_v3(
    recs: list[EvidenceRecord],
    occs: list[OccupancyEvidence] | None = None,
    *,
    duration_s: float = 24.0,
    dt_s: float = 0.2,
    engine: MultimodalDecisionEngineV3FourLayer | None = None,
    event_id: str = "syn_event",
    allow_stale_backfill: bool = False,
):
    collector = MultimodalEvidenceCollector(
        window_tolerance_s=0.5,
        event_id=event_id,
        allow_stale_detection_backfill=allow_stale_backfill,
    )
    collector.add_evidence_batch(recs)
    for o in occs or ():
        collector.add_occupancy(o)
    frames = collector.generate_frames_from_history(0.0, duration_s, stride_s=dt_s)
    eng = engine or MultimodalDecisionEngineV3FourLayer()
    runner = EventSimulationRunner(decision_engine=eng)
    res = runner.run_frames(frames, event_id=event_id, scenario_name="unit")
    return collector, frames, eng, res


# ---------------------------------------------------------------------------
# Category 1: Video orientation normalization
# ---------------------------------------------------------------------------


def test_orientation_normalization_all_orthogonal_and_fail_closed(monkeypatch, tmp_path):
    for deg in (0, 90, -90, 180, -180, 270, -270, 360, -360):
        assert normalize_orthogonal_rotation(deg) == deg

    for bad in (45, -45, 91, True, False, None, 90.0, "90"):
        with pytest.raises(ConfigError):
            normalize_orthogonal_rotation(bad)

    # Quadrant-marked raw raster rotated by every orthogonal angle reproduces expected k*90 rot90
    raw = np.zeros((24, 40, 3), dtype=np.uint8)
    raw[:12, :20] = [10, 20, 230]
    raw[:12, 20:] = [20, 230, 10]
    raw[12:, :20] = [230, 10, 20]
    raw[12:, 20:] = [200, 200, 20]
    for deg in (0, 90, -90, 180, -180, 270, -270):
        out = apply_display_rotation(raw, deg)
        expected = np.ascontiguousarray(np.rot90(raw, k=(deg // 90) % 4))
        np.testing.assert_array_equal(out, expected)
        assert out.flags.c_contiguous

    # Verify source_pts PyAV path applies rotation and preserves metadata
    import av

    fake_path = tmp_path / "rot_test.mp4"
    fake_path.write_bytes(b"synthetic")
    fake_frame = SimpleNamespace(
        pts=120,
        time_base=Fraction(1, 600),
        rotation=-90,
        to_ndarray=lambda **kw: raw,
    )
    fake_stream = SimpleNamespace(index=0, start_time=120)

    class _FakeContainer:
        streams = SimpleNamespace(video=[fake_stream])

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def decode(self, *_args):
            return iter([fake_frame])

    monkeypatch.setattr(av, "open", lambda *a, **k: _FakeContainer())
    yielded = list(frame_generator(fake_path, source_pts=True))
    assert len(yielded) == 1
    vf = yielded[0]
    assert vf.display_rotation_deg == -90
    assert vf.orientation_applied is True
    assert vf.raw_coded_size == (40, 24)
    assert vf.image.shape == (40, 24, 3)


# ---------------------------------------------------------------------------
# Category 2: video_demo deferred writer matches rotated decoded frames
# ---------------------------------------------------------------------------


def test_video_demo_deferred_writer_matches_oriented_frame_dimensions(monkeypatch, tmp_path):
    cv2 = pytest.importorskip("cv2")
    import sys

    input_vid = tmp_path / "syn_input.mp4"
    input_vid.write_bytes(b"placeholder")
    model_pt = tmp_path / "dummy_model.pt"
    model_pt.write_bytes(b"placeholder")
    out_dir = tmp_path / "demo_out"
    out_dir.mkdir()

    # Simulate CAP_PROP reporting unrotated landscape 80x48 while ORIENTATION_AUTO decodes upright 48x80
    rotated_frames = [np.full((80, 48, 3), 128, dtype=np.uint8) for _ in range(3)]

    class _FakeCap:
        def __init__(self):
            self._idx = 0

        def isOpened(self):
            return True

        def set(self, prop, val):
            return True

        def get(self, prop):
            if prop == cv2.CAP_PROP_FRAME_WIDTH:
                return 80
            if prop == cv2.CAP_PROP_FRAME_HEIGHT:
                return 48
            if prop == cv2.CAP_PROP_FPS:
                return 10.0
            if prop == cv2.CAP_PROP_FRAME_COUNT:
                return len(rotated_frames)
            return 0.0

        def read(self):
            if self._idx >= len(rotated_frames):
                return False, None
            f = rotated_frames[self._idx]
            self._idx += 1
            return True, f

        def release(self):
            return None

    class _FakeYOLO:
        names = {0: "front"}

        def __init__(self, _path):
            pass

        def predict(self, source=None, **_kwargs):
            # Confirm image handed to YOLO has upright (80, 48, 3) shape
            assert source.shape == (80, 48, 3)
            return [SimpleNamespace(boxes=None)]

    fake_ultralytics = SimpleNamespace(YOLO=_FakeYOLO)
    monkeypatch.setitem(sys.modules, "ultralytics", fake_ultralytics)
    monkeypatch.setattr(cv2, "VideoCapture", lambda _p: _FakeCap())

    summary = video_demo.process_video(
        input_vid, out_dir, model_path=model_pt, device="cpu"
    )
    assert summary.width == 48
    assert summary.height == 80
    assert summary.processed_frames == 3
    out_mp4 = out_dir / "processed_video.mp4"
    assert out_mp4.is_file() and out_mp4.stat().st_size > 0


# ---------------------------------------------------------------------------
# Category 3: Audio feature transformation (natural vs db log-Mel)
# ---------------------------------------------------------------------------


def test_audio_log_mel_natural_matches_v3_and_differs_from_db():
    sr = 16000
    t = np.linspace(0.0, 1.0, sr, endpoint=False)
    horn = 0.5 * np.sin(2.0 * math.pi * 440.0 * t) + 0.3 * np.sin(2.0 * math.pi * 660.0 * t)
    silence = np.zeros(sr, dtype=np.float64)

    mel_nat = compute_log_mel_spectrogram(horn, sample_rate=sr, log_scale="natural")
    mel_db = compute_log_mel_spectrogram(horn, sample_rate=sr, log_scale="db")
    mel_sil = compute_log_mel_spectrogram(silence, sample_rate=sr, eps=1e-10, log_scale="natural")

    assert mel_nat.shape == mel_db.shape == mel_sil.shape
    assert mel_nat.shape[0] == 64
    assert np.all(np.isfinite(mel_nat))
    assert np.all(np.isfinite(mel_sil))
    # For pure zeros, natural scale equals ln(1e-10), whereas db scale equals 10*log10(1e-10)=-100
    assert np.allclose(mel_sil, math.log(1e-10), atol=1e-9)
    assert not np.allclose(mel_nat, mel_db)
    # Peak ratio over silence is positive in natural log-Mel
    assert float(mel_nat.max() - mel_sil.max()) > 10.0

    with pytest.raises(ValueError, match="log_scale"):
        compute_log_mel_spectrogram(horn, log_scale="invalid")


# ---------------------------------------------------------------------------
# Category 4 & Category 12 & Invariant 1: Causal Collector, Timestamp & Leakage Isolation
# ---------------------------------------------------------------------------


def test_collector_causality_no_stale_backfill_and_reset_isolation():
    collector = MultimodalEvidenceCollector(
        window_tolerance_s=0.5,
        event_id="ev_alpha",
        allow_stale_detection_backfill=False,
    )
    # Cross-event leakage attempt must be rejected
    collector.add_evidence(
        _rec(1.0, "camera_1", Modality.VISION, (_det("front", 0.9),), metadata={"event_id": "ev_beta"})
    )
    collector.add_occupancy(_occ(1.0, OccupancyState.CLEAR, metadata={"event_id": "ev_beta"}))
    assert len(collector.rejected_observations) == 2

    # Valid detection only at t=1.0, plus negative frame at t=1.2 and gap up to t=5.0
    collector.add_evidence(_rec(1.0, "camera_1", Modality.VISION, (_det("front", 0.9),)))
    collector.add_evidence(_rec(1.2, "camera_1", Modality.VISION, ()))
    # Future observation at t=6.0 must never influence t<=5.0 frames
    collector.add_evidence(_rec(6.0, "camera_1", Modality.VISION, (_det("front", 0.95),)))

    frames = collector.generate_frames_from_history(0.0, 6.0, stride_s=0.2)
    early_with_det = [f.master_timestamp_s for f in frames if f.vision_records and any(r.detections for r in f.vision_records)]
    # Only snapshot t=1.0 consumes the t=1.0 detection; it is NOT backfilled onto t=1.2, 1.4 or before t=6.0
    assert early_with_det == [pytest.approx(1.0), pytest.approx(6.0)]
    for f in frames:
        if f.master_timestamp_s < 6.0:
            for r in f.vision_records:
                assert r.timestamp_s <= f.master_timestamp_s

    # Duplicate and out-of-order rejection
    collector.add_evidence(_rec(6.0, "camera_1", Modality.VISION, ()))
    collector.add_evidence(_rec(5.0, "camera_1", Modality.VISION, ()))
    reasons = [r["reason"] for r in collector.rejected_observations]
    assert "duplicate_observation" in reasons and "out_of_order_observation" in reasons

    # Reset clears all state
    collector.reset(event_id="ev_gamma")
    assert collector.event_id == "ev_gamma"
    assert collector.rejected_observations == []
    assert collector.generate_frames_from_history(0.0, 1.0, stride_s=0.5)[0].vision_records == ()

    # Guard on SourceTracker get_age sentinel inf at t=0.0
    assert (
        classify_evidence_status(
            fresh_record=_rec(0.0, "camera_1", Modality.VISION, ()),
            health="healthy",
            age_s=float("inf"),
            stale_after_s=2.0,
        )
        == EvidenceStatus.NEGATIVE
    )


# ---------------------------------------------------------------------------
# Category 5: State-machine transition matrix (11 states) & legality
# ---------------------------------------------------------------------------


def test_state_machine_all_11_states_and_illegal_transitions_blocked():
    sm = CrossingStateMachine()
    assert sm.current_state == CrossingState.IDLE
    legal_sequence = [
        CrossingState.TRAIN_APPROACHING,
        CrossingState.WARNING,
        CrossingState.GATE_CLOSING,
        CrossingState.TRAIN_PRESENT,
        CrossingState.CROSSING_OCCUPIED,
        CrossingState.TRAIN_DEPARTING,
        CrossingState.REAR_CONFIRMED,
        CrossingState.CROSSING_CLEAR,
        CrossingState.GATE_OPENING,
        CrossingState.IDLE,
        CrossingState.FAULT_FAIL_SAFE,
        CrossingState.IDLE,
    ]
    t = 0.0
    for nxt in legal_sequence:
        t += 0.5
        sm.transition(nxt, t, reason="test_legal")
        assert sm.current_state == nxt

    # Reopening directly from CROSSING_OCCUPIED or IDLE without approach is illegal
    sm.reset(CrossingState.CROSSING_OCCUPIED, 0.0)
    for forbidden in (CrossingState.GATE_OPENING, CrossingState.IDLE, CrossingState.CROSSING_CLEAR):
        assert forbidden not in ALLOWED_TRANSITIONS[CrossingState.CROSSING_OCCUPIED]
        with pytest.raises(InvalidTransitionError):
            sm.transition(forbidden, 1.0, reason="illegal")


# ---------------------------------------------------------------------------
# Category 6: Physical gate model kinematics
# ---------------------------------------------------------------------------


def test_physical_gate_model_kinematics_and_interrupt():
    gate = PhysicalGateModel(closing_duration_s=3.0, opening_duration_s=2.0)
    assert gate.is_fully_open and not gate.is_passage_blocked

    # Halfway at 1.5s -> 45.0 deg -> blocked threshold reached
    gate.step(1.5, GateState.CLOSING)
    assert math.isclose(gate.current_angle_deg, 45.0, abs_tol=1e-6)
    assert gate.is_passage_blocked is True
    assert gate.current_state == GateState.CLOSING

    # Complete closing at +1.5s -> 0.0 deg
    gate.step(1.5, GateState.CLOSED)
    assert gate.is_fully_closed is True
    assert gate.current_state == GateState.CLOSED

    # Start opening and interrupt mid-travel on re-close command
    gate.step(1.0, GateState.OPENING)
    assert math.isclose(gate.current_angle_deg, 45.0, abs_tol=1e-6)
    gate.step(0.5, GateState.CLOSING)
    assert gate.current_angle_deg < 45.0
    assert gate.current_state == GateState.CLOSING


# ---------------------------------------------------------------------------
# Category 7 & Invariant 2: Closure policy (front independent; never waits on back/audio)
# ---------------------------------------------------------------------------


def test_closure_policy_front_independent_and_single_frame_glitch_rejected():
    # Front-only closing without audio or back camera detections
    recs: list[EvidenceRecord] = []
    for i in range(40):
        t = round(i * 0.2, 3)
        f_dets = [_det("front", 0.85)] if 1.0 <= t <= 3.0 else []
        recs.append(_rec(t, "camera_1", Modality.VISION, tuple(f_dets)))
    _, _, _, res = _run_v3(
        recs,
        duration_s=7.8,
        engine=MultimodalDecisionEngineV3FourLayer(
            require_healthy_back_for_reopen=False,
            require_occupancy_for_reopen=False,
        ),
    )
    assert any(s.crossing_state == CrossingState.GATE_CLOSING.value for s in res.steps)
    assert any(s.crossing_state == CrossingState.TRAIN_PRESENT.value for s in res.steps)
    assert res.steps[-1].gate_state in (GateState.CLOSING.value, GateState.CLOSED.value)

    # Single-frame isolated front glitch must reset to IDLE without closing gate
    glitch_recs = [
        _rec(round(i * 0.2, 3), "camera_1", Modality.VISION, (_det("front", 0.9),) if i == 5 else ())
        for i in range(30)
    ]
    _, _, _, g_res = _run_v3(glitch_recs, duration_s=5.8)
    assert not any(s.gate_state in ("CLOSING", "CLOSED") for s in g_res.steps)
    assert g_res.steps[-1].crossing_state == CrossingState.IDLE.value


# ---------------------------------------------------------------------------
# Category 8 & Invariant 4: Departure policy (Conservative vs Guarded Disappearance)
# ---------------------------------------------------------------------------


def test_departure_policy_conservative_vs_guarded_and_sparse_dropout():
    # Build nominal stream but drop positive rear/tail from back camera (disappearance only)
    recs, occs = _build_nominal_streams(include_back_rear=False, include_occ=True)

    # Under CONSERVATIVE_POSITIVE: disappearance alone CANNOT open gate
    _, _, _, cons_res = _run_v3(
        recs,
        occs,
        engine=MultimodalDecisionEngineV3FourLayer(departure_mode=DeparturePolicyMode.CONSERVATIVE_POSITIVE),
    )
    assert not any(s.gate_state == "OPENING" for s in cons_res.steps)
    assert cons_res.steps[-1].gate_state == "CLOSED"

    # Now inject sparse dropout (single false dropout at t=9.0 during side occupation)
    dropout_recs: list[EvidenceRecord] = []
    for i in range(121):
        t = round(i * 0.2, 3)
        f_d = [_det("front", 0.9)] if 1.0 <= t <= 5.0 else []
        s_d = [_det("side", 0.88, (40.0 + t * 5, 50.0, 140.0 + t * 5, 150.0))] if (4.0 <= t <= 12.0 and abs(t - 9.0) > 1e-6) else []
        # Back camera blinks off transiently around t=9.6..10.4 then sees train again [10.6..12.6]
        if 8.0 <= t <= 9.4 or 10.6 <= t <= 12.6:
            b_d = [_det("side", 0.86)]
        else:
            b_d = []
        dropout_recs.extend([
            _rec(t, "camera_1", Modality.VISION, tuple(f_d)),
            _rec(t, "camera_side", Modality.VISION, tuple(s_d)),
            _rec(t, "camera_2", Modality.VISION, tuple(b_d)),
        ])
    dropout_occs = [_occ(round(i * 0.2, 3), OccupancyState.OCCUPIED if 4.0 <= round(i * 0.2, 3) <= 13.0 else OccupancyState.CLEAR) for i in range(121)]
    # GUARDED_DISAPPEARANCE must NOT open prematurely during transient dropout before t=13.0
    _, _, _, guard_res = _run_v3(
        dropout_recs,
        dropout_occs,
        engine=MultimodalDecisionEngineV3FourLayer(
            departure_mode=DeparturePolicyMode.GUARDED_DISAPPEARANCE,
            guarded_negative_hold_s=2.0,
        ),
    )
    premature = [s for s in guard_res.steps if 8.0 <= s.timestamp_s < 13.0 and s.gate_state in ("OPENING", "OPEN")]
    assert premature == []

    # When require_last_carriage=True, 'rear' alone without 'last_carriage' holds closed; adding tail allows reopen
    recs_rear_only, occs_ro = _build_nominal_streams(include_back_rear=True, include_tail=False)
    _, _, _, no_tail_res = _run_v3(
        recs_rear_only,
        occs_ro,
        engine=MultimodalDecisionEngineV3FourLayer(require_last_carriage=True),
    )
    assert not any(s.gate_state == "OPENING" for s in no_tail_res.steps)

    recs_with_tail, occs_wt = _build_nominal_streams(include_back_rear=True, include_tail=True)
    _, _, _, with_tail_res = _run_v3(
        recs_with_tail,
        occs_wt,
        engine=MultimodalDecisionEngineV3FourLayer(require_last_carriage=True),
    )
    assert any(s.gate_state == "OPENING" for s in with_tail_res.steps)


# ---------------------------------------------------------------------------
# Category 9 & Invariants 5, 7: OccupancyVerifier 5 states & reopening gate
# ---------------------------------------------------------------------------


def test_occupancy_all_five_states_and_contradiction_invariant():
    # Direct unit test of OccupancyVerifier across OCCUPIED, CLEAR, UNKNOWN, MISSING, CONTRADICTORY
    verifier = OccupancyVerifier()
    recs, occs = _build_nominal_streams()
    collector = MultimodalEvidenceCollector(window_tolerance_s=0.5, allow_stale_detection_backfill=False)
    collector.add_evidence_batch(recs)
    for o in occs:
        collector.add_occupancy(o)
    frames = collector.generate_frames_from_history(0.0, 24.0, stride_s=0.2)

    # Frame at t=1.6 (upstream front + CLEAR occ): must remain CLEAR, NOT CONTRADICTORY
    f_approach = next(f for f in frames if math.isclose(f.master_timestamp_s, 1.6))
    a_app = verifier.evaluate(f_approach)
    assert a_app.state == OccupancyState.CLEAR

    # Frame at t=8.0 (OCCUPIED): OCCUPIED
    f_occ = next(f for f in frames if math.isclose(f.master_timestamp_s, 8.0))
    assert verifier.evaluate(f_occ).state == OccupancyState.OCCUPIED

    # Frame at t=15.0 (CLEAR, no crossing detections): CLEAR
    f_clr = next(f for f in frames if math.isclose(f.master_timestamp_s, 15.0))
    assert verifier.evaluate(f_clr).state == OccupancyState.CLEAR

    # Contradiction: crossing-zone camera_side detects train while occ says CLEAR -> CONTRADICTORY
    col_c = MultimodalEvidenceCollector(window_tolerance_s=0.5, allow_stale_detection_backfill=False)
    col_c.add_evidence(_rec(5.0, "camera_side", Modality.VISION, (_det("side", 0.9),)))
    col_c.add_occupancy(_occ(5.0, OccupancyState.CLEAR))
    f_contra = col_c.generate_frames_from_history(5.0, 5.0, stride_s=0.2)[0]
    assert verifier.evaluate(f_contra).state == OccupancyState.CONTRADICTORY

    # No sensor -> UNKNOWN; sensor with available=False -> MISSING
    col_u = MultimodalEvidenceCollector(window_tolerance_s=0.5, allow_stale_detection_backfill=False)
    f_u = col_u.generate_frames_from_history(1.0, 1.0, stride_s=0.2)[0]
    assert verifier.evaluate(f_u).state == OccupancyState.UNKNOWN

    col_m = MultimodalEvidenceCollector(window_tolerance_s=0.5, allow_stale_detection_backfill=False)
    col_m.add_occupancy(_occ(1.0, OccupancyState.UNKNOWN, available=False))
    f_m = col_m.generate_frames_from_history(1.0, 1.0, stride_s=0.2)[0]
    assert verifier.evaluate(f_m).state == OccupancyState.MISSING

    # Engine invariant: never opens while OCCUPIED, UNKNOWN, MISSING, or CONTRADICTORY
    for bad_state in (OccupancyState.OCCUPIED, OccupancyState.UNKNOWN, OccupancyState.MISSING, OccupancyState.CONTRADICTORY):
        recs_b, _ = _build_nominal_streams(include_occ=False)
        occs_b = [
            _occ(round(i * 0.2, 3), OccupancyState.OCCUPIED if round(i * 0.2, 3) < 13.0 else bad_state)
            for i in range(121)
        ]
        _, _, _, r_b = _run_v3(recs_b, occs_b)
        assert not any(s.gate_state == "OPENING" for s in r_b.steps)


# ---------------------------------------------------------------------------
# Category 10 & Invariants 3, 6: Missing modalities & failed clearance sources
# ---------------------------------------------------------------------------


def test_missing_modalities_and_failed_clearance_source_fail_safe():
    # Missing back camera during departure -> holds closed (failed source != negative)
    recs_nb, occs_nb = _build_nominal_streams()
    recs_nb = [r for r in recs_nb if not (r.source_id == "camera_2" and r.timestamp_s >= 9.0)]
    _, _, _, res_nb = _run_v3(recs_nb, occs_nb)
    assert not any(s.gate_state == "OPENING" for s in res_nb.steps)
    assert res_nb.steps[-1].gate_state == "CLOSED"

    # Missing audio -> nominal cycle unaffected; audio silence cannot keep gate open or prove absence
    recs_na, occs_na = _build_nominal_streams(include_audio=False)
    _, _, _, res_na = _run_v3(recs_na, occs_na)
    assert any(s.gate_state == "CLOSED" for s in res_na.steps)
    assert any(s.gate_state == "OPENING" for s in res_na.steps)
    assert res_na.steps[-1].crossing_state == CrossingState.IDLE.value

    # Missing occupancy -> holds closed under require_occupancy_for_reopen=True
    recs_no, _ = _build_nominal_streams(include_occ=False)
    _, _, _, res_no = _run_v3(recs_no, [])
    assert not any(s.gate_state == "OPENING" for s in res_no.steps)

    # Horn absence cannot establish absence of occupied train (audio absent while front/side present keeps closed)
    recs_no_horn_occ, occs_ho = _build_nominal_streams(include_audio=False)
    # Remove rear so train lingers without departure confirmation
    recs_no_horn_occ = [
        _rec(r.timestamp_s, r.source_id, r.modality, tuple(d for d in r.detections if d.label != "rear"))
        for r in recs_no_horn_occ
    ]
    _, _, _, res_ho = _run_v3(recs_no_horn_occ, occs_ho)
    assert res_ho.steps[-1].gate_state == "CLOSED"


# ---------------------------------------------------------------------------
# Category 11: Fault-injection matrix (timeouts, stale, EOF, contradictory, false-clear)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "fault_mode",
    [
        "front_timeout",
        "stale_side",
        "contradictory_occ",
        "stream_eof",
        "false_clear_with_side",
        "stopped_train",
    ],
)
def test_fault_injection_modes_never_reopen_unsafely(fault_mode: str):
    recs, occs = _build_nominal_streams()
    if fault_mode == "front_timeout":
        recs = [r for r in recs if r.source_id != "camera_1"]
        # Unavailable front record at start with persistent camera outage
        recs = [_rec(0.0, "camera_1", Modality.VISION, (), available=False)] + recs
    elif fault_mode == "stale_side":
        recs = [r for r in recs if not (r.source_id == "camera_side" and r.timestamp_s >= 10.0)]
    elif fault_mode == "contradictory_occ":
        occs = [_occ(o.timestamp_s, OccupancyState.CLEAR) for o in occs]
    elif fault_mode == "stream_eof":
        recs = [r for r in recs if not (r.source_id == "camera_2" and r.timestamp_s >= 10.2)]
    elif fault_mode == "false_clear_with_side":
        occs = [_occ(o.timestamp_s, OccupancyState.CLEAR if o.timestamp_s >= 7.0 else o.state) for o in occs]
    elif fault_mode == "stopped_train":
        # Keep side bbox motionless from t=5.0..18.0 and remove rear
        new_recs = []
        for r in recs:
            if r.source_id == "camera_side" and 4.0 <= r.timestamp_s <= 18.0:
                new_recs.append(_rec(r.timestamp_s, "camera_side", Modality.VISION, (_det("side", 0.9, (60.0, 50.0, 160.0, 150.0)),)))
            elif r.source_id == "camera_2" and r.timestamp_s >= 11.2:
                new_recs.append(_rec(r.timestamp_s, "camera_2", Modality.VISION, ()))
            else:
                new_recs.append(r)
        recs = new_recs

    _, _, _, res = _run_v3(recs, occs)
    assert res.premature_opening_detected is False
    # None of these faults should permit GATE_OPENING while train/fault active
    if fault_mode != "stale_side":
        # Note: in all faults where clearance cannot be verified, gate remains CLOSED
        assert res.steps[-1].gate_state in ("CLOSING", "CLOSED")


# ---------------------------------------------------------------------------
# Category 13: Multi-train interruption & reversal handling
# ---------------------------------------------------------------------------


def test_multi_train_interruption_and_reversal():
    # Multi-train: train 1 clears -> GATE_OPENING around 14.6 -> train 2 approaches at t=14.8!
    recs1, occs1 = _build_nominal_streams()
    recs_mt: list[EvidenceRecord] = []
    occs_mt: list[OccupancyEvidence] = []
    for r in recs1:
        if r.source_id == "camera_1" and 14.8 <= r.timestamp_s <= 20.0:
            recs_mt.append(_rec(r.timestamp_s, "camera_1", Modality.VISION, (_det("front", 0.92),)))
        elif r.source_id == "camera_side" and 16.0 <= r.timestamp_s <= 24.0:
            recs_mt.append(_rec(r.timestamp_s, "camera_side", Modality.VISION, (_det("side", 0.88, (40.0 + (r.timestamp_s - 16.0) * 15, 50.0, 140.0 + (r.timestamp_s - 16.0) * 15, 150.0)),)))
        else:
            recs_mt.append(r)
    for o in occs1:
        if 15.2 <= o.timestamp_s <= 24.0:
            occs_mt.append(_occ(o.timestamp_s, OccupancyState.OCCUPIED))
        else:
            occs_mt.append(o)

    _, _, _, res_mt = _run_v3(recs_mt, occs_mt)
    open_steps = [s.timestamp_s for s in res_mt.steps if s.gate_state == "OPENING"]
    later_reclose = [s.timestamp_s for s in res_mt.steps if s.timestamp_s >= 15.0 and s.gate_state in ("CLOSING", "CLOSED")]
    assert open_steps != [] and later_reclose != []
    assert res_mt.steps[-1].gate_state == "CLOSED"

    # Train reversal: rear appears then front/side reappears -> RULE_L4_REVERSAL_HOLD holds closed
    recs_rev, occs_rev = _build_nominal_streams()
    recs_rev = [
        _rec(r.timestamp_s, r.source_id, r.modality, (_det("front", 0.88),))
        if (r.source_id == "camera_1" and 13.0 <= r.timestamp_s <= 18.0)
        else r
        for r in recs_rev
    ]
    _, _, _, res_rev = _run_v3(recs_rev, occs_rev)
    assert res_rev.steps[-1].gate_state == "CLOSED"


# ---------------------------------------------------------------------------
# Category 14: Negative controls & SideMovementTracker classification
# ---------------------------------------------------------------------------


def test_negative_controls_and_side_movement_tracker():
    # Sub-threshold audio + vision scores never close gate
    recs = []
    occs = []
    for i in range(50):
        t = round(i * 0.2, 3)
        recs.append(_rec(t, "camera_1", Modality.VISION, (_det("front", 0.20),)))
        recs.append(_rec(t, "camera_side", Modality.VISION, (_det("side", 0.15),)))
        recs.append(_rec(t, "camera_2", Modality.VISION, ()))
        if round(t * 10) % 5 == 0:
            recs.append(_rec(t, "audio_1", Modality.AUDIO, (_det("train", 0.30),)))
        occs.append(_occ(t, OccupancyState.CLEAR))
    _, _, _, res = _run_v3(recs, occs, duration_s=9.8)
    assert not any(s.gate_state != "OPEN" for s in res.steps)
    assert res.steps[-1].crossing_state == CrossingState.IDLE.value

    # SideMovementTracker distinguishes SINGLE_FRAME, MOVING, STOPPED
    tracker = SideMovementTracker(stopped_min_duration_s=1.0)
    col = MultimodalEvidenceCollector(window_tolerance_s=0.5, allow_stale_detection_backfill=False)
    col.add_evidence(_rec(1.0, "camera_side", Modality.VISION, (_det("side", 0.9, (10.0, 10.0, 110.0, 110.0)),)))
    col.add_evidence(_rec(1.2, "camera_side", Modality.VISION, (_det("side", 0.9, (30.0, 10.0, 130.0, 110.0)),)))
    for t_s in (2.0, 2.6, 3.2):
        col.add_evidence(_rec(t_s, "camera_side", Modality.VISION, (_det("side", 0.9, (30.0, 10.0, 130.0, 110.0)),)))
    fs = col.generate_frames_from_history(1.0, 3.2, stride_s=0.2)
    f_by_t = {round(f.master_timestamp_s, 1): f for f in fs}
    assert tracker.update(f_by_t[1.0]).movement_state == "SINGLE_FRAME"
    assert tracker.update(f_by_t[1.2]).movement_state == "MOVING"
    assert tracker.update(f_by_t[2.0]).movement_state == "MOVING"
    assert tracker.update(f_by_t[3.2]).movement_state == "STOPPED"


# ---------------------------------------------------------------------------
# Category 15 & Invariant 8: Full end-to-end 4-layer pipeline + audio dwell + auditability
# ---------------------------------------------------------------------------


def test_full_pipeline_nominal_e2e_and_decision_traceability():
    recs, occs = _build_nominal_streams()
    _, frames, _, res = _run_v3(recs, occs)
    states = [s.crossing_state for s in res.steps]
    assert CrossingState.IDLE.value in states
    assert CrossingState.TRAIN_APPROACHING.value in states
    assert CrossingState.WARNING.value in states
    assert CrossingState.GATE_CLOSING.value in states
    assert CrossingState.TRAIN_PRESENT.value in states
    assert CrossingState.CROSSING_OCCUPIED.value in states
    assert CrossingState.TRAIN_DEPARTING.value in states
    assert CrossingState.REAR_CONFIRMED.value in states
    assert CrossingState.CROSSING_CLEAR.value in states
    assert CrossingState.GATE_OPENING.value in states
    assert res.steps[-1].crossing_state == CrossingState.IDLE.value
    assert res.steps[-1].gate_state == GateState.OPEN.value
    assert res.fault_occurred is False
    assert res.premature_opening_detected is False
    # Every step's DecisionRecord traces cleanly to master timestamp + non-empty explanation
    for step in res.steps:
        assert math.isfinite(step.timestamp_s)
        assert step.decision.explanation
        assert isinstance(step.decision.evidence_references, tuple)
    assert any(s.decision.rule_id is not None for s in res.steps)

    # Verify all state transitions follow ALLOWED_TRANSITIONS
    for a, b in zip(states, states[1:]):
        assert CrossingState(b) in ALLOWED_TRANSITIONS[CrossingState(a)]

    # Verify late horn inside CLEAR dwell extends reopening delay
    recs_horn, occs_horn = _build_nominal_streams()
    recs_horn.append(_rec(13.5, "audio_1", Modality.AUDIO, (_det("train", 0.85),)))
    _, _, _, res_horn = _run_v3(recs_horn, occs_horn)
    open_nom = next(s.timestamp_s for s in res.steps if s.gate_state == "OPENING")
    open_ext = next(s.timestamp_s for s in res_horn.steps if s.gate_state == "OPENING")
    assert open_ext > open_nom


# ---------------------------------------------------------------------------
# Category 16: Reproducibility & deterministic hashing
# ---------------------------------------------------------------------------


def test_end_to_end_reproducibility_bit_identical():
    def _digest() -> str:
        recs, occs = _build_nominal_streams()
        _, _, _, res = _run_v3(recs, occs, event_id="repro_ev")
        payload = [
            {
                "t": s.timestamp_s,
                "cs": s.crossing_state,
                "gs": s.gate_state,
                "ang": round(s.gate_angle_deg, 6),
                "rule": s.decision.rule_id,
                "src": list(s.decision.evidence_references),
            }
            for s in res.steps
        ]
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()

    assert _digest() == _digest()
