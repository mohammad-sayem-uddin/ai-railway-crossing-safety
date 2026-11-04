"""Exact commanded fixtures and independent invariants; no research data."""

from dataclasses import replace
from fractions import Fraction as Q

import pytest

from railway_detection.synthetic.convention_b import (
    CausalRunner,
    Command,
    SyntheticEvent,
    Watchdog,
    legacy_float_to_us,
    normalize_command,
    timestamp_us,
)


def grid(n, h=Q(1, 5)):
    return [k*h for k in range(n+1)]


def cumulative(deltas):
    result = [Q(0)]
    for delta in deltas:
        result.append(result[-1]+delta)
    return result


def events(times, commands):
    assert len(times) == len(commands)
    result = []
    for i, (time, command) in enumerate(zip(times, commands, strict=True)):
        value = Q(time)*1_000_000
        assert value.denominator == 1
        result.append(SyntheticEvent(f"synthetic:observation:{i}", int(value), command))
    return result


# Published C2 exact reference values, independently checked in C3. No runner
# implementation is used to derive expected numbers in this table.
VECTORS = [
    ("01", grid(1), "LL", {}, ("0", "0", "84")),
    ("02", grid(2), "HLL", {}, ("0", "0", "84")),
    ("03", grid(15), "L"*16, {}, ("8/5", "3/2", "0")),
    ("04", grid(30, Q(1, 10)), "L"*31, {}, ("8/5", "3/2", "0")),
    ("05", cumulative([Q(1, 10), Q(7, 20), Q(1, 20), Q(1, 2)]*5),
     "L"*21, {}, ("71/20", "7/2", "0")),
    ("06", grid(70), "H"+"L"*20+"H"*20+"R"*30, {}, ("8", "8", "90")),
    ("07", grid(30), "H"+"L"*30, {}, ("22/5", "43/10", "0")),
    ("08", grid(100), "H"+"L"*20+"R"*20+"H"*20+"L"*40, {}, ("52/5", "103/10", "0")),
    ("09", cumulative([Q(1, 5)]*10+[Q(1, 10)]), "H"+"L"*11, {}, ("1/2", "2/5", "33")),
    ("10-prefix", [Q(1), Q(6, 5), Q(7, 5)], "LLL", {}, ("0", "0", "78")),
    ("11-prefix", [Q(1), Q(7, 5), Q(8, 5)], "LLL", {}, ("0", "0", "72")),
    ("12-W1", [Q(1), Q(6, 5), Q(16, 5), Q(21, 5)], "HHLL", {}, ("0", "0", "60")),
    ("12-W2", [Q(1), Q(6, 5), Q(21, 5)], "HHL", {}, ("0", "0", "90")),
    ("13-above", grid(1), "HH", {"initial_angle": "45.0000001"},
     ("0", "0", "450000001/10000000")),
    ("13-equal", grid(1), "HH", {"initial_angle": 45}, ("1/5", "1/5", "45")),
    ("13-below", grid(1), "HH", {"initial_angle": "44.9999999"},
     ("1/5", "1/5", "449999999/10000000")),
    ("16", grid(10)+[Q(21, 10)], "L"*12, {}, ("7/10", "3/5", "27")),
    ("17", grid(40), "H"+"L"*20+"R"*20, {"opening_seconds": 6},
     ("28/5", "11/2", "57")),
    ("18", grid(30), "L"*31, {}, ("23/5", "9/2", "0")),
    ("20-CLOSED", [0, 1, 2], ("CLOSED",)*3, {"initial_angle": 60}, ("2", "3/2", "0")),
    ("20-OPEN", [0, 1, 2], ("OPEN",)*3, {"initial_angle": 30}, ("0", "1/2", "90")),
]


@pytest.mark.parametrize("case,times,commands,parameters,expected", VECTORS,
                         ids=[v[0] for v in VECTORS])
def test_all_21_exact_reference_vectors(case, times, commands, parameters, expected):
    result = CausalRunner(**parameters).run(events(times, commands), fixture_id="synthetic:oracle")
    assert result.status == "COMPLETE"
    assert (result.endpoint_seconds, result.continuous_seconds, result.final_angle) == tuple(
        Q(v) for v in expected)
    assert sum((Q(i.end_us-i.start_us, 1_000_000) for i in result.intervals), Q(0)) == (
        times[-1]-times[0])
    assert all(i.effective_us <= i.start_us for i in result.intervals)


def test_delayed_issue_has_distinct_interval_provenance():
    r = CausalRunner().run(events(grid(2), "HLL"), fixture_id="synthetic:delayed")
    assert [i.post_angle for i in r.intervals] == [90, 84]
    assert [i.applied_command for i in r.intervals] == [Command.HOLD, Command.LOWER]
    assert r.intervals[1].origin_event_id == r.issues[1].event_id
    assert r.intervals[1].effective_us == 200000


@pytest.mark.parametrize("raw", [None, True, False, -1, float('nan'), float('inf'),
                                  0.2, "-0", "NaN", "1e-6", "0.0000001", [], ""])
def test_bad_timestamp_aborts_before_propagation_and_preserves_prefix(raw):
    source = [SyntheticEvent("synthetic:ok", 0, "L"), SyntheticEvent("synthetic:bad", raw, "R")]
    r = CausalRunner().run(source, fixture_id="synthetic:bad-time", report_times=(0, "1"))
    assert r.status == "INCOMPLETE" and r.horizon_us == 0 and r.final_angle == 90
    assert r.endpoint_seconds == r.continuous_seconds == 0
    assert r.report_endpoint_seconds is None and len(r.issues) == 1


def test_timestamp_units_and_explicit_legacy_adapter():
    assert timestamp_us(1) == 1 and timestamp_us("1") == 1000000
    assert timestamp_us("1.000001") == 1000001
    assert legacy_float_to_us(.2) == 200000
    assert legacy_float_to_us(1e-6) == 1
    with pytest.raises(ValueError):
        legacy_float_to_us(.1+.2)
    for value in (True, -1., float('nan'), float('inf')):
        with pytest.raises(ValueError):
            legacy_float_to_us(value)


@pytest.mark.parametrize("angle", [45.0, True, "NaN", -1, 91])
def test_invalid_or_binary_float_initial_angle_rejected(angle):
    with pytest.raises(ValueError):
        CausalRunner(initial_angle=angle)


def test_rejected_arrivals_cannot_replace_command_or_advance_accepted_clock():
    source = events([1, Q(6, 5), Q(6, 5), Q(11, 10), Q(7, 5)], "LLRRL")
    r = CausalRunner().run(source, fixture_id="synthetic:rejections")
    assert r.status == "COMPLETE" and r.final_angle == 78
    assert [x.reason for x in r.rejections] == ["DUPLICATE", "OUT_OF_ORDER"]
    assert len(r.accepted_event_ids) == len(r.issues) == 3
    assert all(i.applied_command == Command.LOWER for i in r.intervals)
    assert r.horizon_us == 1400000


def test_offline_sort_is_explicit_and_prevalidates_before_actuation():
    source = events([0, Q(2, 5), Q(1, 5), Q(2, 5)], "LLLR")
    r = CausalRunner().run(source, fixture_id="synthetic:offline", mode="OFFLINE")
    assert r.reordered and r.final_angle == 78 and len(r.rejections) == 1
    bad = source+[SyntheticEvent("synthetic:invalid", None, "L")]
    r = CausalRunner().run(bad, fixture_id="synthetic:offline", mode="OFFLINE")
    assert r.status == "INCOMPLETE" and not r.intervals and r.origin_us is None


def test_empty_single_and_cutoff_boundaries():
    runner = CausalRunner()
    r = runner.run([], fixture_id="synthetic:empty")
    assert r.status == "EMPTY" and r.final_angle is None and r.horizon_us is None
    r = runner.run(events([1], "L"), fixture_id="synthetic:single")
    assert r.status == "COMPLETE" and r.final_angle == 90 and not r.intervals
    with pytest.raises(ValueError):
        runner.run(events([1], "L"), fixture_id="synthetic:early", cutoff="0.9")
    r = runner.run(events([1], "L"), fixture_id="synthetic:equal", cutoff="1")
    assert not r.intervals and r.final_angle == 90
    r = runner.run(events([0, 3], "LR"), fixture_id="synthetic:inside", cutoff="0.2")
    assert r.final_angle == 84 and len(r.issues) == 1
    assert r.intervals[-1].end_kind == "CUTOFF"
    r = runner.run(events(grid(10), "L"*11), fixture_id="synthetic:extend", cutoff="2.1")
    assert (r.final_angle, r.endpoint_seconds, r.continuous_seconds) == (27, Q(7, 10), Q(3, 5))


def test_report_grid_and_event_grid_have_different_semantics():
    runner = CausalRunner()
    a = runner.run(events([0, 2], "LL"), fixture_id="synthetic:grid", report_times=(0, "2"))
    b = runner.run(events([0, 1, 2], "LLL"), fixture_id="synthetic:grid", report_times=(0, "2"))
    assert (a.endpoint_seconds, b.endpoint_seconds) == (2, 1)
    assert a.report_endpoint_seconds == b.report_endpoint_seconds == 2
    assert a.continuous_seconds == b.continuous_seconds == Q(1, 2)
    assert a.final_angle == b.final_angle == 30
    for grid_times in [(), (0, 0), ("1", "2"), (0, "3")]:
        with pytest.raises(ValueError):
            runner.run(events([0, 2], "LL"), fixture_id="synthetic:grid", report_times=grid_times)


@pytest.mark.parametrize("initial", [0, 30, 45, 90])
@pytest.mark.parametrize("command", ["H", "L", "R"])
def test_continuous_integral_and_fixed_reporting_invariant_to_noop_subdivision(initial, command):
    runner = CausalRunner(initial_angle=initial)
    a = runner.run(events([0, 2], command*2), fixture_id="synthetic:segment", report_times=(0, "2"))
    b = runner.run(events([0, Q(1, 10), Q(7, 10), 2], command*4),
                   fixture_id="synthetic:segment", report_times=(0, "2"))
    assert (a.final_angle, a.continuous_seconds, a.report_endpoint_seconds) == (
        b.final_angle, b.continuous_seconds, b.report_endpoint_seconds)


def test_command_conflict_and_identity_errors_are_incomplete_not_completed_runs():
    r = CausalRunner().run([SyntheticEvent("synthetic:conflict", 0, "CLOSING", "OPEN")],
                           fixture_id="synthetic:conflict")
    assert r.status == "INCOMPLETE" and not r.issues
    source = events([0, 1], "LL")
    r = CausalRunner().run([source[0], replace(source[1], event_id=source[0].event_id)],
                           fixture_id="synthetic:reuse")
    assert r.status == "INCOMPLETE" and r.horizon_us == 0
    with pytest.raises(ValueError):
        CausalRunner().run(source, fixture_id="real:event")
    assert normalize_command("CLOSED") == normalize_command("CLOSING") == Command.LOWER
    assert normalize_command("OPEN") == normalize_command("OPENING") == Command.RAISE


def test_executed_watchdog_profiles_match_conditional_oracles():
    source = events([1, Q(6, 5), Q(21, 5)], "HHL")
    scheduled = CausalRunner(watchdog=Watchdog("SCHEDULED", 2000000, "L"))
    detect = CausalRunner(watchdog=Watchdog("DETECT_ON_ARRIVAL", 2000000, "L"))
    a = scheduled.run(source, fixture_id="synthetic:watchdog")
    b = detect.run(source, fixture_id="synthetic:watchdog")
    assert (a.final_angle, b.final_angle) == (60, 90)
    assert (
        a.endpoint_seconds
        == b.endpoint_seconds
        == a.continuous_seconds
        == b.continuous_seconds
        == 0
    )
    assert any(issue.kind == "TIMER" and issue.timestamp_us == 3200000 for issue in a.issues)
    assert b.issues[-1].kind == "GAP_DETECTED"


def test_watchdog_equal_time_sensor_priority_cancellation_and_one_shot():
    scheduled = CausalRunner(watchdog=Watchdog("SCHEDULED", 2000000, "L"))
    a = scheduled.run(events([0, 2], "HH"), fixture_id="synthetic:equal", cutoff="3")
    assert a.final_angle == 90 and not any(i.kind == "TIMER" for i in a.issues)
    source = events([0, 1, 1], "HHR")
    a = scheduled.run(source, fixture_id="synthetic:cancel", cutoff="6")
    timer_issues = [i for i in a.issues if i.kind == "TIMER"]
    assert len(timer_issues) == 1 and timer_issues[0].timestamp_us == 3000000
    assert len(a.accepted_event_ids) == 2
    b = scheduled.run(events([0], "H"), fixture_id="synthetic:at-due", cutoff="2")
    assert b.final_angle == 90 and b.issues[-1].timestamp_us == 2000000
    detect = CausalRunner(watchdog=Watchdog("DETECT_ON_ARRIVAL", 2000000, "L"))
    b = detect.run(events([0], "H"), fixture_id="synthetic:no-next", cutoff="6")
    assert b.final_angle == 90 and len(b.issues) == 1


def test_watchdog_detect_response_overrides_only_future_command():
    runner = CausalRunner(watchdog=Watchdog("DETECT_ON_ARRIVAL", 1000000, "L"))
    r = runner.run(events([0, 2], "HH"), fixture_id="synthetic:gap", cutoff="2.2")
    assert r.final_angle == 84 and r.intervals[0].applied_command == Command.HOLD
    assert r.issues[-1].requested_command == Command.HOLD
    assert r.issues[-1].command == Command.LOWER


def test_100_fresh_runs_are_byte_deterministic():
    source = events(VECTORS[4][1], VECTORS[4][2])
    expected = CausalRunner().run(source, fixture_id="synthetic:repeat").canonical_json()
    for _ in range(100):
        assert (
            CausalRunner().run(source, fixture_id="synthetic:repeat").canonical_json() == expected
        )


@pytest.mark.parametrize("times,commands,initial,opening,delta", [
    (grid(70), "H"+"L"*20+"H"*20+"R"*30, 90, 3, Q(0)),
    (grid(30), "H"+"L"*30, 90, 3, Q(-1, 5)),
    (grid(100), "H"+"L"*20+"R"*20+"H"*20+"L"*40, 90, 3, Q(-1, 5)),
    (grid(40), "H"+"L"*20+"R"*20, 90, 6, Q(0)),
    (grid(30), "H"+"R"*30, 0, 3, Q(1, 5)),
    (grid(30), "L"*31, 90, 3, Q(0)),
    ([Q(0), Q(1), Q(3)], "HLR", 90, 3, Q(2)),
    (cumulative([Q(1, 5)]*10+[Q(1, 10)]), "H"+"L"*11, 90, 3, Q(-1, 5)),
])
def test_fixed_command_boundary_identity_and_limits(times, commands, initial, opening, delta):
    # Independent mathematical Convention A oracle on constructed commands only.
    angle, endpoint_a = Q(initial), Q(0)
    for i in range(1, len(times)):
        dt = times[i]-times[i-1]
        if commands[i] == "L":
            angle = max(Q(0), angle-30*dt)
        elif commands[i] == "R":
            angle = min(Q(90), angle+Q(90, opening)*dt)
        endpoint_a += dt*int(angle <= 45)
    b = CausalRunner(initial_angle=initial, opening_seconds=opening).run(
        events(times, commands), fixture_id="synthetic:boundary-identity")
    assert b.endpoint_seconds-endpoint_a == delta
