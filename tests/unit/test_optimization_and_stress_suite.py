"""Synthetic unit tests for calibration/hysteresis, duty-cycle model, and stress suite."""

from __future__ import annotations

from railway_detection.experiments.optimization_and_stress import (
    apply_temperature_scaling,
    compute_binary_ece_and_brier,
    compute_event_triggered_duty_cycle,
    evaluate_acoustic_hysteresis_and_calibration,
    evaluate_weather_and_interlocking_stress,
)


def test_acoustic_hysteresis_and_calibration_on_synthetic_events():
    events = [
        {"event_id": "train_1", "cohort": "train_events", "binary_label": 1, "scores": [0.2, 0.88, 0.91, 0.90, 0.1]},
        {"event_id": "train_2", "cohort": "train_events", "binary_label": 0, "scores": [0.1, 0.55, 0.2, 0.42, 0.1]},
        {"event_id": "nt_1", "cohort": "no_train_events", "binary_label": None, "scores": [0.81, 0.80, 0.79, 0.1]},
        {"event_id": "eng_1", "cohort": "engine_events", "binary_label": None, "scores": [0.12, 0.14, 0.08]},
    ]
    res = evaluate_acoustic_hysteresis_and_calibration(
        events, thresholds=(0.37, 0.85), k_values=(1, 2), temperatures=(1.0, 2.0)
    )
    # At tau=0.37, k=1: isolated spike in train_2 triggers FP (spec=0.0)
    r_37_1 = next(x for x in res["hysteresis_grid"] if x["threshold"] == 0.37 and x["k_consecutive"] == 1)
    assert r_37_1["tp"] == 1 and r_37_1["fp"] == 1 and r_37_1["no_train_fp"] == 1
    # At tau=0.37, k=2: isolated spikes in train_2 suppressed (tn=1, spec=1.0), sustained nt_1 remains FP
    r_37_2 = next(x for x in res["hysteresis_grid"] if x["threshold"] == 0.37 and x["k_consecutive"] == 2)
    assert r_37_2["tn"] == 1 and r_37_2["specificity"] == 1.0 and r_37_2["no_train_fp"] == 1
    # At tau=0.85, k=2: train_1 still triggers while road-horn nt_1 is excluded
    r_85_2 = next(x for x in res["hysteresis_grid"] if x["threshold"] == 0.85 and x["k_consecutive"] == 2)
    assert r_85_2["tp"] == 1 and r_85_2["fp"] == 0 and r_85_2["no_train_fp"] == 0

    cal = compute_binary_ece_and_brier([0.9, 0.1], [1, 0], n_bins=5)
    assert cal["brier"] < 0.02 and abs(cal["ece"] - 0.1) < 1e-4
    scaled = apply_temperature_scaling([0.9, 0.1], 2.0)
    assert 0.5 < scaled[0] < 0.9 and 0.1 < scaled[1] < 0.5


def test_duty_cycle_analytical_scaling_invariants():
    dc = compute_event_triggered_duty_cycle(50.0, 1.0, trains_per_day_list=(10, 40))
    rows = dc["duty_cycle_scenarios"]
    assert rows[0]["vision_frame_reduction_pct"] > rows[1]["vision_frame_reduction_pct"] > 90.0
    assert rows[0]["total_compute_time_reduction_pct"] > 80.0
    assert (
        rows[0]["sbc_analytical_projections"]["rpi4b_4gb_cortex_a72"]["projection_type"]
        == "ANALYTICAL_PROJECTION_UNMEASURED_HARDWARE"
    )


def test_weather_and_interlocking_stress_zero_unsafe_openings():
    stress = evaluate_weather_and_interlocking_stress(
        alphas=(1.0, 0.6, 0.35), drop_probs=(0.0, 0.30), seeds=(11, 22)
    )
    assert stress["input_classification"] == "SYNTHETIC_ONLY"
    assert stress["total_grid_runs"] == 12
    assert stress["total_unsafe_openings"] == 0
    assert stress["total_illegal_transitions"] == 0
    assert stress["interlocking_scenarios"]["stalled_obstacle_during_departure"]["held_closed_past_20_8s"] is True
    assert stress["interlocking_scenarios"]["multi_train_reopen_interrupt"]["final_gate_state"] == "CLOSED"
