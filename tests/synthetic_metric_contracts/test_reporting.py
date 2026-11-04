from types import SimpleNamespace

import pytest

from railway_detection.evaluation.lead_in_screen import screen_missed_train_lead_in
from railway_detection.evaluation.metrics import (
    DescriptiveMetricRow,
    classify_m4,
    summarize_descriptive_rows,
)
from railway_detection.simulation.runner import SimulationRunResult


@pytest.mark.parametrize(
    "steps,t4,status,premature,never",
    [
        ([], 4, "NOT_EVALUABLE", None, None),
        ([(0, False, "OPEN"), (4, False, "OPEN")], 4, "NEVER_PROTECTED_M5", None, True),
        ([(0, True, "CLOSED"), (2, False, "OPEN")], 4, "EVALUABLE", True, False),
        ([(0, True, "CLOSED"), (2, True, "CLOSED")], 4, "NOT_EVALUABLE", None, None),
        ([(0, True, "CLOSED"), (4, True, "CLOSED")], 4, "NOT_EVALUABLE", None, None),
        (
            [(0, True, "CLOSED"), (2, True, "CLOSED"), (4, True, "CLOSED")],
            4,
            "EVALUABLE",
            False,
            False,
        ),
        ([(1, False, "OPEN"), (4, False, "OPEN")], 4, "NOT_EVALUABLE", None, None),
        ([(0, True, "CLOSED")], None, "NOT_EVALUABLE", None, None),
    ],
)
def test_six_case_and_edge_oracles(steps, t4, status, premature, never):
    r = SimulationRunResult(
        "synthetic:metric",
        "constructed",
        steps=[
            SimpleNamespace(timestamp_s=float(t), is_passage_blocked=b, gate_state=g)
            for t, b, g in steps
        ],
    )
    out = classify_m4(r, t4)
    assert (out.status, out.premature, out.never_protected) == (status, premature, never)


def row(event, camera, metric, value, reason=None):
    return DescriptiveMetricRow(
        event, camera, "constructed", metric, value, reason, "synthetic:receipt"
    )


def test_per_metric_denominators_camera_cohort_and_nulls():
    rows = (
        row("train_events/event_001", "back", "M4", True),
        row("train_events/event_002", "back", "M4", None, "censored"),
        row("train_events/event_001", "front", "M4", False),
        row("engine_events/event_001", "back", "M4", True),
        row("train_events/event_001", "back", "M5", 1),
        row("train_events/event_001", "back", "WLT", 2.0),
        row("train_events/event_002", "back", "WLT", 4.0),
    )
    out = summarize_descriptive_rows(rows)
    back = next(
        x
        for x in out
        if x["cohort"] == "train_events" and x["camera"] == "back" and x["metric"] == "M4"
    )
    assert (
        back["denominator"] == 1
        and back["numerator"] == 1
        and back["excluded_by_reason"] == {"censored": 1}
    )
    engine = next(x for x in out if x["cohort"] == "engine_events")
    assert engine["denominator"] == 0 and engine["proportion"] is None
    assert next(x for x in out if x["metric"] == "WLT")["median"] == 3.0
    assert type(next(x for x in out if x["metric"] == "M5")["numerator"]) is int


@pytest.mark.parametrize(
    "bad",
    [
        row("event_001", "back", "M5", 1),
        row("train_events/event_001", "back", "M5", True),
        row("train_events/event_001", "back", "M4", 1),
        row("train_events/event_001", "back", "WLT", float("nan")),
        row("train_events/event_001", "back", "M4", None),
    ],
)
def test_reporting_rejects_ambiguous_or_false_denominators(bad):
    with pytest.raises(ValueError):
        summarize_descriptive_rows((bad,))


def test_duplicate_and_lead_in_provenance():
    r = row("train_events/event_001", "back", "M5", 1)
    with pytest.raises(ValueError):
        summarize_descriptive_rows((r, r))
    screen = screen_missed_train_lead_in(
        2.0,
        first_visible_time_s=1.0,
        first_visible_left_censored=False,
        min_block_latency_s=3.6,
        min_block_latency_source="synthetic:config:tick200ms",
    )
    assert not screen.evaluable and screen.min_block_latency_source == "synthetic:config:tick200ms"
