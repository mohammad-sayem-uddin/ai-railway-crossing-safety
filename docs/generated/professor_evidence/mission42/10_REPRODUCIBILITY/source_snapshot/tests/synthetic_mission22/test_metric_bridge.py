from dataclasses import replace

import pytest

from railway_detection.fusion.collector import MultimodalFrame
from railway_detection.synthetic.convention_b_pipeline import (
    ConstructedBatch,
    ConstructedInput,
    IntegrationRequest,
    ScriptedDecisions,
    run_pipeline,
)
from railway_detection.synthetic.integration_contracts import project_b_metrics


def run(times, commands, **kwargs):
    batch = ConstructedBatch.build(
        "synthetic:fixture",
        tuple(
            ConstructedInput("synthetic:f" + str(i), t, MultimodalFrame(t / 1_000_000))
            for i, t in enumerate(times)
        ),
        provenance="CONSTRUCTED_IN_MEMORY",
    )
    request = IntegrationRequest.prepare(
        batch,
        ScriptedDecisions(tuple(commands)),
        mode="ARRIVAL",
        code_identity="synthetic:code",
        **kwargs,
    )
    return request, run_pipeline(request)


@pytest.mark.parametrize("state", ["CENSORED", "UNCERTAIN", "NOT_OBSERVABLE"])
def test_missing_censored_never_zero(state):
    request, result = run([0, 2_000_000], ["LOWER", "LOWER"])
    m = project_b_metrics(result, expected_request=request, t4_us=None, boundary_state=state)
    assert m["M4"] is None and m["M5"] is None and m["reason"] == "t4_" + state.lower()


def test_opening_is_motion_not_new_intent_and_m5_integer():
    request, result = run(
        [0, 2_000_000, 3_000_000, 4_000_000, 5_000_000], ["LOWER", "RAISE", "HOLD", "HOLD", "HOLD"]
    )
    m = project_b_metrics(result, expected_request=request, t4_us=5_000_000)
    assert m["M4"] is True and m["M5"] == 0
    assert m["points"][1]["geometry_state"] == "CLOSING"  # RAISE only acts in the next interval
    assert m["points"][2]["geometry_state"] == "OPENING"
    request, result = run([0, 1_000_000, 2_000_000], ["HOLD"] * 3)
    m = project_b_metrics(result, expected_request=request, t4_us=2_000_000)
    assert m["M4"] is None and type(m["M5"]) is int and m["M5"] == 1


def test_incomplete_and_tampered_outputs_not_safe():
    request, result = run([0, 1_000_000], ["LOWER", "BAD"])
    assert project_b_metrics(result, expected_request=request, t4_us=3_000_000)["M5"] is None
    with pytest.raises(ValueError, match="retained replay"):
        project_b_metrics(
            replace(result, controller_calls=99), expected_request=request, t4_us=3_000_000
        )


@pytest.mark.parametrize("t", [True, -1, 0.2, 3_600_000_001])
def test_invalid_t4_rejected(t):
    request, result = run([0, 1_000_000], ["HOLD"] * 2)
    with pytest.raises(ValueError):
        project_b_metrics(result, expected_request=request, t4_us=t)
