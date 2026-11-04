"""Independent constructed integration cases; no model/data resources."""

from dataclasses import replace
from fractions import Fraction

import pytest

from railway_detection.fusion.collector import MultimodalFrame
from railway_detection.fusion.decision_engine import MultimodalDecisionEngine
from railway_detection.fusion.evidence import Detection, EvidenceRecord, Modality
from railway_detection.simulation.runner import EventSimulationRunner
from railway_detection.synthetic.convention_b_pipeline import (
    ConstructedBatch,
    ConstructedInput,
    IntegrationRequest,
    ScriptedDecisions,
    run_pipeline,
    verify_result,
)


def batch(times, *, frame_offset=0, evidence=False):
    rows = []
    for i, t in enumerate(times):
        seconds = t / 1_000_000 if type(t) is int else float(t or 0)
        recs = (
            (
                EvidenceRecord(
                    seconds, "camera_front", Modality.VISION, True, (Detection("front", 0.99),)
                ),
            )
            if evidence
            else ()
        )
        rows.append(
            ConstructedInput(
                f"synthetic:event:{i}", t, MultimodalFrame(float(seconds + frame_offset), recs)
            )
        )
    return ConstructedBatch.build(
        "synthetic:integration", tuple(rows), provenance="CONSTRUCTED_IN_MEMORY"
    )


def request(times, commands=None, **kw):
    c = ScriptedDecisions(tuple(commands or ["LOWER"] * len(times)))
    return IntegrationRequest.prepare(
        batch(times), c, mode=kw.pop("mode", "ARRIVAL"), code_identity="synthetic:code:21v1", **kw
    )


@pytest.mark.parametrize("dt", [1, 200000, 500000, 1500000, 3000000, 4000000])
def test_causal_oracle_and_three_estimators(dt):
    q = request([0, dt], report_step_us=200000)
    r = run_pipeline(q)
    assert r.causal.final_angle == max(0, 90 - Fraction(30 * dt, 1000000))
    assert r.causal.continuous_seconds == max(0, Fraction(dt, 1000000) - Fraction(3, 2))
    assert r.causal.endpoint_seconds == (Fraction(dt, 1000000) if dt >= 1500000 else 0)
    assert r.causal.report_grid_us[-1] == dt
    assert r.controller_calls == 2
    assert r.causal.intervals[0].origin_event_id == "synthetic:event:0"
    assert r.causal.issues[1].timestamp_us == dt
    assert verify_result(r, expected_request=q)


def test_new_command_never_applies_retroactively():
    r = run_pipeline(request([0, 1000000, 2000000], ["HOLD", "LOWER", "RAISE"]))
    assert [x.post_angle for x in r.causal.intervals] == [90, 60]
    assert r.causal.final_angle == 60


@pytest.mark.parametrize("mode", ["ARRIVAL", "OFFLINE"])
def test_native_rejections_and_original_indices(mode):
    c = MultimodalDecisionEngine()
    q = IntegrationRequest.prepare(
        batch([0, 200000, 200000, 100000, 400000], evidence=True),
        c,
        mode=mode,
        code_identity="synthetic:code:21v1",
    )
    r = EventSimulationRunner(c).run_frames_convention_b(q)
    assert r.controller_calls == 5
    rejected = [x for x in r.decisions if not x.accepted]
    assert len(rejected) == (2 if mode == "ARRIVAL" else 1)
    assert all(x.command is None for x in rejected)
    assert len(r.causal.issues) == 5 - len(rejected)
    assert verify_result(r, expected_request=q)


@pytest.mark.parametrize(
    "times,cutoff,expected",
    [
        ([], None, None),
        ([0], None, 0),
        ([1000000], 1000000, 1000000),
        ([0, 1000000], 500000, 500000),
        ([0, 1000000], 2000000, 2000000),
    ],
)
def test_horizon_empty_single_partial_extended(times, cutoff, expected):
    r = run_pipeline(request(times, cutoff=cutoff))
    assert r.causal.horizon_us == expected
    assert r.controller_calls == sum(1 for t in times if cutoff is None or t <= cutoff)
    assert r.status == ("EMPTY" if not times else "COMPLETE")


def test_cutoff_before_origin_rejects_and_no_future_decision():
    with pytest.raises(ValueError, match="cutoff precedes"):
        run_pipeline(request([1000000], cutoff=0))
    assert run_pipeline(request([0, 1000000], cutoff=0)).controller_calls == 1


@pytest.mark.parametrize("mode", ["ARRIVAL", "OFFLINE"])
def test_invalid_future_clock_mode_failure_prefix(mode):
    q = request([0, 1000000], mode=mode)
    raw = q.batch.inputs_json.replace('"timestamp":1000000', '"timestamp":null')
    r = run_pipeline(replace(q, batch=replace(q.batch, inputs_json=raw), cutoff=500000))
    assert r.status == "INCOMPLETE"
    assert r.controller_calls == (1 if mode == "ARRIVAL" else 0)
    assert r.causal.report_endpoint_seconds is None


@pytest.mark.parametrize("clock", [None, True, -1, 0.2, "0.0000001"])
def test_invalid_exact_clocks(clock):
    q = request([0])
    import json

    data = json.loads(q.batch.inputs_json)
    data[0]["timestamp"] = clock
    from railway_detection.synthetic.convention_b_pipeline import canonical

    r = run_pipeline(replace(q, batch=replace(q.batch, inputs_json=canonical(data))))
    assert r.status == "INCOMPLETE"
    assert r.controller_calls == 0


def test_float_boundary_mismatch():
    c = MultimodalDecisionEngine()
    q = IntegrationRequest.prepare(
        batch([200000], frame_offset=1e-5), c, mode="ARRIVAL", code_identity="synthetic:code:21v1"
    )
    assert run_pipeline(q).status == "INCOMPLETE"


@pytest.mark.parametrize(
    "field,value",
    [
        ("mode", "AUTO"),
        ("closing_seconds", "0"),
        ("initial_angle", "91"),
        ("report_times", [0]),
        ("report_times", (0, 0)),
        ("report_step_us", True),
        ("cutoff", 3600000001),
    ],
)
def test_invalid_configuration(field, value):
    with pytest.raises(ValueError):
        run_pipeline(replace(request([0]), **{field: value}))


def test_incomplete_command_prefix_not_success():
    r = run_pipeline(request([0, 1000000], ["LOWER", "bad"]))
    assert r.status == "INCOMPLETE"
    assert r.causal.status == "INCOMPLETE"
    assert r.causal.report_endpoint_seconds is None
    assert r.controller_calls == 2


@pytest.mark.parametrize(
    "field,value",
    [
        ("status", "EMPTY"),
        ("controller_calls", 12),
        ("code_identity", "synthetic:code:swapped"),
        ("reason", "invented"),
        ("decisions", ()),
    ],
)
def test_full_detached_result_substitutions(field, value):
    q = request([0, 2000000])
    r = run_pipeline(q)
    assert not verify_result(replace(r, **{field: value}), expected_request=q)


def test_swapped_trajectory_and_request_fail_verification():
    q = request([0, 2000000])
    r = run_pipeline(q)
    for changes in [
        dict(final_angle=Fraction(89)),
        dict(endpoint_seconds=Fraction(99)),
        dict(continuous_seconds=Fraction(10)),
    ]:
        assert not verify_result(
            replace(r, causal=replace(r.causal, **changes)), expected_request=q
        )
    assert not verify_result(r, expected_request=replace(q, opening_seconds="6"))
    assert not verify_result(r, expected_request=replace(q, code_identity="synthetic:other"))


def test_input_nested_mutation_and_effective_settings_reset():
    metadata = {"nested": {"value": 1}}
    ev = EvidenceRecord(
        0.0, "camera_front", Modality.VISION, True, (Detection("front", 0.9, metadata=metadata),)
    )
    b = ConstructedBatch.build(
        "synthetic:owned",
        (ConstructedInput("synthetic:first", 0, MultimodalFrame(0.0, (ev,))),),
        provenance="CONSTRUCTED_IN_MEMORY",
    )
    c = MultimodalDecisionEngine()
    q = IntegrationRequest.prepare(b, c, mode="ARRIVAL", code_identity="synthetic:code:21v1")
    r = run_pipeline(q, c)
    metadata["nested"]["value"] = 7
    assert run_pipeline(q, c).canonical_json() == r.canonical_json()
    c.audio_threshold = 0.9
    with pytest.raises(ValueError, match="settings differ"):
        run_pipeline(q, c)


def test_actual_controller_a_compatibility_and_different_motion():
    b = batch([0, 200000, 2200000, 3200000, 4200000], evidence=True)
    c = MultimodalDecisionEngine()
    q = IntegrationRequest.prepare(b, c, mode="ARRIVAL", code_identity="synthetic:code:21v1")
    runner = EventSimulationRunner(c)
    import json

    from railway_detection.synthetic.convention_b_pipeline import _frame

    frames = [_frame(x) for x in json.loads(b.inputs_json)]
    a_before = runner.run_frames(frames)
    out = runner.run_frames_convention_b(q)
    a_after = runner.run_frames(frames)
    assert a_before == a_after
    assert [x.decision.resulting_gate_state for x in a_before.steps] == [
        json.loads(x.decision_json)["resulting_gate_state"] for x in out.decisions
    ]
    assert [x.gate_angle_deg for x in a_before.steps][1:] != [
        x.post_angle for x in out.causal.intervals
    ]


def test_exact_threshold_and_noop_subdivision():
    for angle, blocked in [("45", True), ("45.000001", False), ("44.999999", True)]:
        r = run_pipeline(replace(request([0, 1000000], ["HOLD", "HOLD"]), initial_angle=angle))
        assert r.causal.intervals[0].blocked is blocked
    a = run_pipeline(request([0, 2000000], report_step_us=200000))
    b = run_pipeline(request([0, 1000000, 2000000], report_step_us=200000))
    assert a.causal.continuous_seconds == b.causal.continuous_seconds
    assert a.causal.report_endpoint_seconds == b.causal.report_endpoint_seconds


def test_8192_frames_scale_and_limits():
    q = request([i * 200000 for i in range(8192)])
    r = run_pipeline(q)
    assert r.controller_calls == 8192 and len(r.causal.intervals) == 8191
    with pytest.raises(ValueError, match="report workload"):
        run_pipeline(replace(q, report_step_us=1))
    with pytest.raises(ValueError):
        batch([0] * 8193)


@pytest.mark.parametrize("times", [[2000000, 0, 1000000], [0, 0, 1000000]])
def test_offline_reorder_and_stable_duplicate_priority(times):
    r = run_pipeline(request(times, mode="OFFLINE"))
    assert r.processing_mode == "OFFLINE"
    assert r.reordered == (times != sorted(times))
    accepted = [x.input_index for x in r.decisions if x.accepted]
    assert accepted[0] == times.index(min(times))


@pytest.mark.parametrize("fixed", [(1, 1000000), (0, 999999), (), (0, 500000, 1000000)])
def test_fixed_grid_exact_spanning(fixed):
    q = request([0, 1000000], report_times=fixed)
    if fixed == (0, 500000, 1000000):
        assert run_pipeline(q).causal.report_grid_us == fixed
    else:
        with pytest.raises(ValueError):
            run_pipeline(q)


@pytest.mark.parametrize("initial,down,up", [("0", "3", "6"), ("45", "6", "3"), ("90", "6", "3")])
def test_asymmetric_motion_oracle(initial, down, up):
    q = replace(
        request([0, 2000000, 4000000], ["LOWER", "RAISE", "HOLD"]),
        initial_angle=initial,
        closing_seconds=down,
        opening_seconds=up,
    )
    r = run_pipeline(q)
    middle = max(Fraction(0), Fraction(initial) - 180 / Fraction(down))
    assert r.causal.final_angle == min(Fraction(90), middle + 180 / Fraction(up))


@pytest.mark.parametrize(
    "setting,value",
    [
        ("confirm_frames", True),
        ("fault_confirm_frames", 0),
        ("audio_threshold", 1.1),
        ("source_staleness_s", -1),
    ],
)
def test_invalid_effective_controller_settings(setting, value):
    c = MultimodalDecisionEngine()
    setattr(c, setting, value)
    with pytest.raises(ValueError):
        IntegrationRequest.prepare(
            batch([0]), c, mode="ARRIVAL", code_identity="synthetic:code:21v1"
        )


def test_engine_reset_once_per_production_run(monkeypatch):
    c = MultimodalDecisionEngine()
    original = c.reset
    resets = []

    def counted(initial_time_s=0.0):
        resets.append(initial_time_s)
        return original(initial_time_s)

    monkeypatch.setattr(c, "reset", counted)
    q = IntegrationRequest.prepare(
        batch([1000000, 2000000], evidence=True),
        c,
        mode="ARRIVAL",
        code_identity="synthetic:code:21v1",
    )
    out = run_pipeline(q, c)
    assert out.status == "COMPLETE" and resets == [1.0]
    assert out.causal.configuration.watchdog.mode == "NONE"


def test_future_evidence_never_retimed():
    ev = EvidenceRecord(1.0, "camera_front", Modality.VISION, True)
    b = ConstructedBatch.build(
        "synthetic:future",
        (ConstructedInput("synthetic:first", 0, MultimodalFrame(0.0, (ev,))),),
        provenance="CONSTRUCTED_IN_MEMORY",
    )
    q = IntegrationRequest.prepare(
        b, MultimodalDecisionEngine(), mode="OFFLINE", code_identity="synthetic:code:21v1"
    )
    r = run_pipeline(q)
    assert r.status == "INCOMPLETE" and r.controller_calls == 0
