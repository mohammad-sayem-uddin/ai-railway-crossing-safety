# ruff: noqa: E501
"""Mission 10 / WP10.7: differential validation of the M4 / M5 classification path.

``classify_m4`` is compared with an independent oracle over an exhaustive synthetic grid. The oracle
is written from the documented rules (strict open interval, no tolerance, zero-origin M5, no steps in
the interval is NOT_EVALUABLE) using integer microseconds, not the production grid helper, so a bug
that is shared by construction cannot hide. Everything is in-memory: no media, caches or real events.
"""

from __future__ import annotations

import itertools

import pytest

from railway_detection.evaluation.metrics import (
    M4_REASON_NO_INTERIOR_STEPS,
    M4_REASON_REPLAY_ENDED_BEFORE_T4,
    M4_REASON_REPLAY_STARTED_AT_OR_AFTER_T4,
    M4_REASON_REPLAY_STARTED_LATE,
    M4_STATUS_EVALUABLE,
    M4_STATUS_NEVER_PROTECTED,
    M4_STATUS_NOT_EVALUABLE,
    classify_m4,
)
from railway_detection.simulation.runner import SimulationRunResult, SimulationStep

TICK_US = 200_000  # the controller's 0.2 s tick, in integer microseconds


def _steps(first: int, last: int, block_from: int | None, glitch: int | None, glitch_gate: str):
    out = []
    for i in range(first, last + 1):
        blocked = block_from is not None and i >= block_from
        gate = "CLOSED" if blocked else "OPEN"
        if glitch is not None and i == glitch:
            blocked, gate = False, glitch_gate
        out.append(
            SimulationStep(
                i * TICK_US / 1e6, "TRAIN_PRESENT", gate, 0.0 if blocked else 90.0, blocked, None
            )  # type: ignore[arg-type]
        )
    return out


def _oracle(ticks: list[tuple[int, bool, str]], t4_us: int):
    """Documented rules, integer microseconds. Returns (status, premature, never, reason)."""
    if not ticks:
        return ("NOT_EVALUABLE", None, None, "replay_empty")
    first, last = ticks[0][0], ticks[-1][0]
    blocked_times = [t for t, blocked, _ in ticks if blocked]
    t_blocked = blocked_times[0] if blocked_times else None
    covered = last >= t4_us
    if t_blocked is not None and t_blocked < t4_us:
        interior = [(b, g) for t, b, g in ticks if t_blocked < t < t4_us]
        if any((not b) or g in ("OPENING", "OPEN") for b, g in interior):
            return ("EVALUABLE", True, False, None)
        if not covered:
            return ("NOT_EVALUABLE", None, None, "replay_ended_before_T4")
        if not interior:
            return ("NOT_EVALUABLE", None, None, "no_steps_in_protection_interval")
        return ("EVALUABLE", False, False, None)
    if not covered:
        return ("NOT_EVALUABLE", None, None, "replay_ended_before_T4")
    if first >= t4_us:
        return ("NOT_EVALUABLE", None, None, "replay_started_at_or_after_T4")
    if first > 0:
        return ("NOT_EVALUABLE", None, None, "replay_started_late")
    return ("NEVER_PROTECTED_M5", None, True, None)


def _grid():
    for t4_ticks in (5, 10):  # T4 = 1.0 s and 2.0 s
        for first, last, block_from, glitch_gate in itertools.product(
            (0, 1, 3, t4_ticks, t4_ticks + 2),
            (0, 2, t4_ticks - 1, t4_ticks, t4_ticks + 3),
            (None, 0, 1, 2, t4_ticks - 1, t4_ticks, t4_ticks + 1),
            ("OPEN", "OPENING", "CLOSED"),
        ):
            if last < first:
                continue
            for glitch in (None, first, first + 1, t4_ticks - 1, t4_ticks, t4_ticks + 1):
                yield t4_ticks, first, last, block_from, glitch, glitch_gate


CASES = list(_grid())


def test_the_grid_is_large_and_covers_every_documented_outcome():
    seen = set()
    for t4_ticks, first, last, block_from, glitch, gate in CASES:
        steps = _steps(first, last, block_from, glitch, gate)
        seen.add(
            _oracle(
                [
                    (int(round(s.timestamp_s * 1e6)), s.is_passage_blocked, s.gate_state)
                    for s in steps
                ],
                t4_ticks * TICK_US,
            )[:1]
            + (
                _oracle(
                    [
                        (int(round(s.timestamp_s * 1e6)), s.is_passage_blocked, s.gate_state)
                        for s in steps
                    ],
                    t4_ticks * TICK_US,
                )[3],
            )
        )
    assert len(CASES) > 3000
    assert {
        ("EVALUABLE", None),
        ("NEVER_PROTECTED_M5", None),
        ("NOT_EVALUABLE", "replay_ended_before_T4"),
        ("NOT_EVALUABLE", "no_steps_in_protection_interval"),
        ("NOT_EVALUABLE", "replay_started_late"),
        ("NOT_EVALUABLE", "replay_started_at_or_after_T4"),
    } <= seen


@pytest.mark.parametrize("chunk", range(8))
def test_production_classifier_agrees_with_the_independent_oracle(chunk: int):
    mismatches = []
    for t4_ticks, first, last, block_from, glitch, gate in CASES[chunk::8]:
        steps = _steps(first, last, block_from, glitch, gate)
        run = SimulationRunResult(
            event_id="train_events/event_001",
            scenario_name="diff",
            steps=steps,
            total_duration_s=steps[-1].timestamp_s,
            closed_duration_s=0.0,
        )
        got = classify_m4(run, t4_ticks * TICK_US / 1e6)
        ticks = [(round(s.timestamp_s * 1e6), s.is_passage_blocked, s.gate_state) for s in steps]
        want = _oracle(ticks, t4_ticks * TICK_US)
        if (got.status, got.premature, got.never_protected, got.reason) != want:
            mismatches.append((t4_ticks, first, last, block_from, glitch, gate, got.status, want))
    assert not mismatches, mismatches[:5]


def test_m4_and_m5_are_mutually_exclusive_and_never_both_asserted():
    for t4_ticks, first, last, block_from, glitch, gate in CASES[::7]:
        steps = _steps(first, last, block_from, glitch, gate)
        run = SimulationRunResult(
            "train_events/event_001", "diff", steps, steps[-1].timestamp_s, 0.0
        )
        got = classify_m4(run, t4_ticks * TICK_US / 1e6)
        assert not (got.premature is not None and got.never_protected)
        if got.status == M4_STATUS_NOT_EVALUABLE:
            assert got.premature is None and got.never_protected is None and got.reason


def test_reason_constants_match_the_documented_strings():
    assert M4_REASON_REPLAY_ENDED_BEFORE_T4 == "replay_ended_before_T4"
    assert M4_REASON_NO_INTERIOR_STEPS == "no_steps_in_protection_interval"
    assert M4_REASON_REPLAY_STARTED_LATE == "replay_started_late"
    assert M4_REASON_REPLAY_STARTED_AT_OR_AFTER_T4 == "replay_started_at_or_after_T4"
    assert (M4_STATUS_EVALUABLE, M4_STATUS_NEVER_PROTECTED, M4_STATUS_NOT_EVALUABLE) == (
        "EVALUABLE",
        "NEVER_PROTECTED_M5",
        "NOT_EVALUABLE",
    )


def test_float_representation_noise_does_not_change_the_verdict():
    # 0.1 + 0.2 != 0.3 in IEEE-754, but both are the same microsecond: the step sits ON T4.
    steps = [
        SimulationStep(0.0, "TRAIN_PRESENT", "CLOSED", 0.0, True, None),  # type: ignore[arg-type]
        SimulationStep(0.1 + 0.2, "TRAIN_PRESENT", "OPEN", 90.0, False, None),  # type: ignore[arg-type]
    ]
    run = SimulationRunResult("train_events/event_001", "noise", steps, steps[-1].timestamp_s, 0.0)
    got = classify_m4(run, 0.3)
    assert got.status == M4_STATUS_NOT_EVALUABLE and got.reason == M4_REASON_NO_INTERIOR_STEPS


def test_a_genuine_one_microsecond_difference_is_preserved():
    steps = [
        SimulationStep(0.0, "TRAIN_PRESENT", "CLOSED", 0.0, True, None),  # type: ignore[arg-type]
        SimulationStep(0.299999, "TRAIN_PRESENT", "OPEN", 90.0, False, None),  # type: ignore[arg-type]
        SimulationStep(0.3, "TRAIN_PRESENT", "CLOSED", 0.0, True, None),  # type: ignore[arg-type]
    ]
    run = SimulationRunResult("train_events/event_001", "micro", steps, 0.3, 0.0)
    got = classify_m4(run, 0.3)
    assert got.status == M4_STATUS_EVALUABLE and got.premature is True
