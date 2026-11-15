"""Synthetic unit tests for Experiment R (LOEO CV & optical-degradation audio wakeup)."""

from __future__ import annotations

from railway_detection.experiments.optimization_and_stress import (
    evaluate_loeo_acoustic_crossval,
    evaluate_optical_degradation_wakeup_ablation,
)
from railway_detection.fusion.collector import MultimodalEvidenceCollector
from railway_detection.fusion.decision_engine_v3_four_layer import (
    MultimodalDecisionEngineV3FourLayer,
)
from railway_detection.fusion.evidence import (
    Detection,
    EvidenceRecord,
    Modality,
    OccupancyEvidence,
    OccupancyState,
)
from railway_detection.fusion.rules_v3_four_layer import RuleIdV3
from railway_detection.simulation.runner import EventSimulationRunner


def test_loeo_crossval_and_bootstrap_ci_structure():
    events = [
        {"event_id": f"pos_{i}", "cohort": "train_events", "binary_label": 1, "scores": [0.1, 0.91, 0.92, 0.90, 0.2]}
        for i in range(6)
    ] + [
        {"event_id": f"neg_{i}", "cohort": "train_events", "binary_label": 0, "scores": [0.1, 0.50, 0.12, 0.15, 0.08]}
        for i in range(4)
    ] + [
        {"event_id": "nt_1", "cohort": "no_train_events", "binary_label": None, "scores": [0.70, 0.72, 0.69]},
    ]
    res = evaluate_loeo_acoustic_crossval(events, n_bootstrap=200)
    assert res["n_labeled_train"] == 10
    assert len(res["folds"]) == 10
    assert res["loeo_oof_hysteresis_metrics"]["f1"] == 1.0
    assert res["bootstrap_95_ci"]["f1"]["ci95_low"] >= 0.8


def test_optical_degradation_wakeup_closes_fog_cliff_without_clear_false_alarms():
    ablation = evaluate_optical_degradation_wakeup_ablation(alphas=(1.0, 0.45, 0.35))
    row_35 = next(r for r in ablation["attenuation_sweep"] if r["alpha_conf"] == 0.35)
    assert row_35["baseline_v3_closed"] is False
    assert row_35["wakeup_v3_closed"] is True
    assert row_35["wakeup_v3_unsafe_open"] is False
    assert row_35["wakeup_v3_all_legal"] is True
    assert ablation["controls"]["clear_optics_sustained_ambient_horn_closed"] is False
    assert ablation["controls"]["degraded_optics_single_impulse_horn_closed"] is False


def test_default_v3_keeps_optical_degradation_wakeup_disabled():
    eng_default = MultimodalDecisionEngineV3FourLayer()
    assert eng_default.enable_optical_degradation_audio_wakeup is False
    eng_opt = MultimodalDecisionEngineV3FourLayer(enable_optical_degradation_audio_wakeup=True)
    col = MultimodalEvidenceCollector(window_tolerance_s=0.5, event_id="w", allow_stale_detection_backfill=False)
    for step in range(30):
        t = round(step * 0.2, 2)
        col.add_evidence(
            EvidenceRecord(
                timestamp_s=t,
                source_id="camera_1",
                modality=Modality.VISION,
                available=True,
                detections=[],
                metadata={"optical_visibility_score": 0.30, "optical_degraded": True},
            )
        )
        col.add_occupancy(OccupancyEvidence(t, "occ_1", OccupancyState.OCCUPIED, True, 0.9))
        col.add_evidence(EvidenceRecord(t, "audio_1", Modality.AUDIO, True, [Detection("train", 0.88)]))
    frames = col.generate_frames_from_history(0.0, 5.8, stride_s=0.2)
    res_def = EventSimulationRunner(decision_engine=eng_default).run_frames(frames, event_id="w")
    res_opt = EventSimulationRunner(decision_engine=eng_opt).run_frames(frames, event_id="w")
    assert all(s.gate_state == "OPEN" for s in res_def.steps)
    assert any(s.decision.rule_id == RuleIdV3.RULE_L3_OPTICAL_DEGRADED_AUDIO_WAKEUP.value for s in res_opt.steps)
    assert any(s.gate_state in ("CLOSING", "CLOSED") for s in res_opt.steps)
