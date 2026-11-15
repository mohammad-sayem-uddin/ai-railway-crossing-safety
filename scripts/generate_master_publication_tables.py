#!/usr/bin/env python3
"""Generate unified CSV and Markdown publication tables from verified JSON artifacts."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "results" / "publication_tables"


def _load_json(rel_path: str) -> dict[str, Any]:
    with (ROOT / rel_path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _md_table(headers: list[str], rows: list[list[Any]]) -> str:
    sep = ["---"] * len(headers)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(sep) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return "\n".join(lines)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    leak = _load_json("results/dataset_audit/vision_audio_leakage_audit.json")
    master_v2 = _load_json("results/exploratory_v2/MASTER_V2_SUMMARY.json")
    exp_d = _load_json("results/exploratory_v2/experiments/exp_d_back_departure.json")
    exp_j = _load_json("results/exploratory_v2/experiments/exp_j_temporal_vs_stateless.json")
    exp_k = _load_json("results/exploratory_v2/experiments/exp_k_ablation.json")
    exp_o = _load_json(
        "results/exploratory_v2/optimization_and_stress/exp_o_audio_calibration_hysteresis.json"
    )
    exp_p = _load_json(
        "results/exploratory_v2/optimization_and_stress/exp_p_cpu_edge_benchmark.json"
    )
    exp_q = _load_json(
        "results/exploratory_v2/optimization_and_stress/exp_q_weather_and_interlocking_stress.json"
    )
    exp_r = _load_json(
        "results/exploratory_v2/optimization_and_stress/exp_r_crossval_and_failsafe.json"
    )
    edge_scale = _load_json(
        "results/exploratory_v2/optimization_and_stress/host_edge_scaling_benchmark.json"
    )

    # ------------------------------------------------------------------
    # Table 1: Dataset & Leakage Remediation Summary
    # ------------------------------------------------------------------
    v_705d = leak["vision_705d388743ea"]
    v_rf = leak["vision_original_roboflow"]
    v_clean = leak["vision_session_grouped_candidate"]["audit"]
    a_orig = leak["audio_v3_original"]
    a_clean = leak["audio_v3_stem_grouped_candidate"]

    def _sweep_600(audit: dict[str, Any]) -> dict[str, Any]:
        for item in audit["temporal_session_sweeps"]:
            if abs(float(item["gap_s"]) - 600.0) < 1e-6:
                return item
        raise KeyError("gap_s=600.0 missing")

    v_rf_600 = _sweep_600(v_rf)
    v_705d_600 = _sweep_600(v_705d)
    v_clean_600 = _sweep_600(v_clean)

    t1_fields = [
        "dataset",
        "split_variant",
        "train_n",
        "val_n",
        "test_n",
        "cross_session_or_stem_leak",
        "test_overlap_with_train",
        "aug_or_fold_artifact",
    ]
    t1_rows = [
        {
            "dataset": "Vision V1 (baler.v1i)",
            "split_variant": "Original Roboflow folders",
            "train_n": v_rf["split_image_counts"]["train"],
            "val_n": v_rf["split_image_counts"]["val"],
            "test_n": v_rf["split_image_counts"]["test"],
            "cross_session_or_stem_leak": f"{v_rf_600['crossing_timestamped_sessions']}/{v_rf_600['timestamped_session_count']} sessions (gap<=600s)",
            "test_overlap_with_train": f"{v_rf_600['test_timestamped_imgs_sharing_session_with_train']}/{v_rf_600['test_timestamped_imgs_total']} timestamped test imgs",
            "aug_or_fold_artifact": "0 rf_train in test; ungrouped bursts",
        },
        {
            "dataset": "Vision V1 (baler.v1i)",
            "split_variant": "Active split 705d388743ea (leaked)",
            "train_n": v_705d["split_image_counts"]["train"],
            "val_n": v_705d["split_image_counts"]["val"],
            "test_n": v_705d["split_image_counts"]["test"],
            "cross_session_or_stem_leak": f"{v_705d_600['crossing_timestamped_sessions']}/{v_705d_600['timestamped_session_count']} sessions (gap<=600s)",
            "test_overlap_with_train": f"{v_705d_600['test_timestamped_imgs_sharing_session_with_train']}/{v_705d_600['test_timestamped_imgs_total']} timestamped test imgs",
            "aug_or_fold_artifact": f"{v_705d['rf_origin_by_split']['test']['train']}/{v_705d['split_image_counts']['test']} test from rf_train (87.1%)",
        },
        {
            "dataset": "Vision V1 (baler.v1i)",
            "split_variant": "Candidate vision_v1_session_grouped",
            "train_n": v_clean["split_image_counts"]["train"],
            "val_n": v_clean["split_image_counts"]["val"],
            "test_n": v_clean["split_image_counts"]["test"],
            "cross_session_or_stem_leak": f"{v_clean_600['crossing_timestamped_sessions']}/{v_clean_600['timestamped_session_count']} sessions (gap<=600s)",
            "test_overlap_with_train": f"{v_clean_600['test_timestamped_imgs_sharing_session_with_train']}/{v_clean_600['test_timestamped_imgs_total']} timestamped test imgs",
            "aug_or_fold_artifact": f"{leak['vision_session_grouped_candidate']['excluded_eval_augmentation_duplicates']} eval aug duplicates excluded",
        },
        {
            "dataset": "Audio V3 (TrainHorn + ESC-50)",
            "split_variant": "Original audio/v3/dataset_split.json",
            "train_n": a_orig["counts_by_split"]["train"]["total"],
            "val_n": a_orig["counts_by_split"]["val"]["total"],
            "test_n": a_orig["counts_by_split"]["test"]["total"],
            "cross_session_or_stem_leak": f"{a_orig['cross_split_positive_stem_count']}/{a_orig['unique_positive_stems']} pos stems cross splits",
            "test_overlap_with_train": f"{a_orig['positive_recordings_in_cross_split_stems']}/86 pos clips ({a_orig['positive_recording_stem_leakage_fraction']*100:.2f}%)",
            "aug_or_fold_artifact": f"{a_orig['cross_split_negative_fold_count']} cross-split ESC-50 folds",
        },
        {
            "dataset": "Audio V3 (TrainHorn + ESC-50)",
            "split_variant": "Candidate audio_v3_stem_grouped",
            "train_n": a_clean["counts_by_split"]["train"]["total"],
            "val_n": a_clean["counts_by_split"]["val"]["total"],
            "test_n": a_clean["counts_by_split"]["test"]["total"],
            "cross_session_or_stem_leak": f"{a_clean['cross_split_positive_stem_count']}/{a_clean['unique_positive_stems']} pos stems cross splits",
            "test_overlap_with_train": f"{a_clean['positive_recordings_in_cross_split_stems']}/86 pos clips (0.00%)",
            "aug_or_fold_artifact": f"{a_clean['cross_split_negative_fold_count']} cross-split ESC-50 folds; 60/13/13 balanced",
        },
    ]
    _write_csv(OUT_DIR / "table1_dataset_and_leakage_audit.csv", t1_fields, t1_rows)

    # ------------------------------------------------------------------
    # Table 2: Exp D / J / K Policy & Modality Ablation Summary
    # ------------------------------------------------------------------
    t2_fields = [
        "experiment",
        "policy_or_ablation",
        "b4_train23_triggers",
        "no_train3_fp",
        "sync11_closures",
        "sync11_premature_openings",
        "all_transitions_legal",
        "synthetic_4layer_outcome",
    ]
    policies = exp_j["policies"]
    syn_k = exp_k["synthetic_4layer_ablation"]
    real_k = exp_k["real_sync11_ablation"]
    t2_rows = [
        {
            "experiment": "Exp J",
            "policy_or_ablation": "stateless_union",
            "b4_train23_triggers": f"{policies['stateless_union']['b4_train23_closures']}/23",
            "no_train3_fp": f"{policies['stateless_union']['b4_no_train3_false_closures']}/3",
            "sync11_closures": f"{policies['stateless_union']['sync11_closures']}/11",
            "sync11_premature_openings": f"{policies['stateless_union']['sync11_premature_openings_vs_T4']}/11",
            "all_transitions_legal": "False",
            "synthetic_4layer_outcome": "N/A (no FSM statefulness)",
        },
        {
            "experiment": "Exp J",
            "policy_or_ablation": "stateless_vision_rule2",
            "b4_train23_triggers": f"{policies['stateless_vision_rule2']['b4_train23_closures']}/23",
            "no_train3_fp": f"{policies['stateless_vision_rule2']['b4_no_train3_false_closures']}/3",
            "sync11_closures": f"{policies['stateless_vision_rule2']['sync11_closures']}/11",
            "sync11_premature_openings": f"{policies['stateless_vision_rule2']['sync11_premature_openings_vs_T4']}/11",
            "all_transitions_legal": "False",
            "synthetic_4layer_outcome": "N/A (no FSM statefulness)",
        },
        {
            "experiment": "Exp D / J",
            "policy_or_ablation": "V1 (RULE_3)",
            "b4_train23_triggers": f"{policies['v1']['b4_train23_closures']}/23 (8 phys)",
            "no_train3_fp": f"{policies['v1']['b4_no_train3_false_closures']}/3",
            "sync11_closures": f"{policies['v1']['sync11_closures']}/11",
            "sync11_premature_openings": f"{master_v2['exp_d_premature_counts']['V1_RULE_3']}/11",
            "all_transitions_legal": "True",
            "synthetic_4layer_outcome": "Legacy baseline",
        },
        {
            "experiment": "Exp D / J",
            "policy_or_ablation": "V2 (RULE_3B_3C)",
            "b4_train23_triggers": f"{policies['v2']['b4_train23_closures']}/23 (9 phys)",
            "no_train3_fp": f"{policies['v2']['b4_no_train3_false_closures']}/3",
            "sync11_closures": f"{policies['v2']['sync11_closures']}/11",
            "sync11_premature_openings": f"{master_v2['exp_d_premature_counts']['V2_RULE_3B_3C']}/11",
            "all_transitions_legal": "True",
            "synthetic_4layer_outcome": "Reopens prematurely under sparse dropout (12.4s)",
        },
        {
            "experiment": "Exp D",
            "policy_or_ablation": "V3_GUARDED_DISAPPEARANCE",
            "b4_train23_triggers": "10/23 (9 phys)",
            "no_train3_fp": "0/3",
            "sync11_closures": "9/11",
            "sync11_premature_openings": f"{master_v2['exp_d_premature_counts']['V3_GUARDED_DISAPPEARANCE']}/11",
            "all_transitions_legal": "True",
            "synthetic_4layer_outcome": "Aborts under sparse dropout",
        },
        {
            "experiment": "Exp D / J / K",
            "policy_or_ablation": "V3_CONSERVATIVE_POSITIVE (Full 4-Layer)",
            "b4_train23_triggers": f"{policies['v3_conservative']['b4_train23_closures']}/23 (9 phys)",
            "no_train3_fp": f"{policies['v3_conservative']['b4_no_train3_false_closures']}/3",
            "sync11_closures": f"{real_k['full_sync11_front_audio_back']['closures']}/11",
            "sync11_premature_openings": f"{real_k['full_sync11_front_audio_back']['premature_openings']}/11",
            "all_transitions_legal": "True",
            "synthetic_4layer_outcome": f"{syn_k['full_4layer_nominal']['final_crossing_state']}/{syn_k['full_4layer_nominal']['final_gate_state']} (open@{syn_k['full_4layer_nominal']['first_opening_s']}s)",
        },
        {
            "experiment": "Exp K",
            "policy_or_ablation": "Ablation: No Audio",
            "b4_train23_triggers": "10/23",
            "no_train3_fp": "0/3",
            "sync11_closures": f"{real_k['no_audio_front_back_sync11']['closures']}/11",
            "sync11_premature_openings": f"{real_k['no_audio_front_back_sync11']['premature_openings']}/11",
            "all_transitions_legal": str(syn_k["no_audio"]["transition_legal"]),
            "synthetic_4layer_outcome": f"{syn_k['no_audio']['final_crossing_state']}/{syn_k['no_audio']['final_gate_state']} (open@{syn_k['no_audio']['first_opening_s']}s)",
        },
        {
            "experiment": "Exp K",
            "policy_or_ablation": "Ablation: No Back Camera",
            "b4_train23_triggers": "N/A",
            "no_train3_fp": "0/3",
            "sync11_closures": f"{real_k['no_back_front_audio_sync11']['closures']}/11",
            "sync11_premature_openings": f"{real_k['no_back_front_audio_sync11']['premature_openings']}/11",
            "all_transitions_legal": str(syn_k["no_back_camera"]["transition_legal"]),
            "synthetic_4layer_outcome": f"{syn_k['no_back_camera']['final_crossing_state']}/{syn_k['no_back_camera']['final_gate_state']} (fails closed)",
        },
        {
            "experiment": "Exp K",
            "policy_or_ablation": "Ablation: No Side Camera",
            "b4_train23_triggers": "10/23",
            "no_train3_fp": "0/3",
            "sync11_closures": "N/A (no side cam)",
            "sync11_premature_openings": "0/11",
            "all_transitions_legal": str(syn_k["no_side_camera"]["transition_legal"]),
            "synthetic_4layer_outcome": f"{syn_k['no_side_camera']['final_crossing_state']}/{syn_k['no_side_camera']['final_gate_state']} (open@{syn_k['no_side_camera']['first_opening_s']}s)",
        },
        {
            "experiment": "Exp K",
            "policy_or_ablation": "Ablation: No Occupancy Sensor",
            "b4_train23_triggers": "N/A",
            "no_train3_fp": "N/A",
            "sync11_closures": "N/A",
            "sync11_premature_openings": "0/11",
            "all_transitions_legal": str(syn_k["no_occupancy_sensor"]["transition_legal"]),
            "synthetic_4layer_outcome": f"{syn_k['no_occupancy_sensor']['final_crossing_state']}/{syn_k['no_occupancy_sensor']['final_gate_state']} (blocks reopen)",
        },
        {
            "experiment": "Exp K",
            "policy_or_ablation": "Ablation: No Front / Audio Only",
            "b4_train23_triggers": "0/23",
            "no_train3_fp": "0/3",
            "sync11_closures": f"{real_k['audio_only_no_vision_sync11']['closures']}/11",
            "sync11_premature_openings": "0/11",
            "all_transitions_legal": str(syn_k["no_front_camera"]["transition_legal"]),
            "synthetic_4layer_outcome": f"{syn_k['no_front_camera']['final_crossing_state']}/{syn_k['no_front_camera']['final_gate_state']} (0 triggers)",
        },
    ]
    _write_csv(OUT_DIR / "table2_policy_and_ablation_comparison.csv", t2_fields, t2_rows)

    # ------------------------------------------------------------------
    # Table 3: Exp O Selected Operating Points & Calibration
    # ------------------------------------------------------------------
    selected_points = [(0.37, 1), (0.37, 2), (0.50, 2), (0.65, 2), (0.75, 1), (0.75, 2), (0.85, 2)]
    t3_fields = [
        "threshold",
        "k_consecutive",
        "tp",
        "fp",
        "tn",
        "fn",
        "recall",
        "specificity",
        "precision",
        "f1",
        "accuracy",
        "no_train_fp",
        "engine_fp",
    ]
    t3_rows = []
    for tau, k in selected_points:
        match = next(
            r
            for r in exp_o["hysteresis_grid"]
            if abs(float(r["threshold"]) - tau) < 1e-6 and int(r["k_consecutive"]) == k
        )
        t3_rows.append(
            {
                "threshold": match["threshold"],
                "k_consecutive": match["k_consecutive"],
                "tp": match["tp"],
                "fp": match["fp"],
                "tn": match["tn"],
                "fn": match["fn"],
                "recall": match["recall"],
                "specificity": match["specificity"],
                "precision": match["precision"],
                "f1": match["f1"],
                "accuracy": match["accuracy"],
                "no_train_fp": f"{match['no_train_fp']}/{match['no_train_total']}",
                "engine_fp": f"{match['engine_fp']}/{match['engine_total']}",
            }
        )
    _write_csv(OUT_DIR / "table3_exp_o_audio_hysteresis_pareto.csv", t3_fields, t3_rows)

    # ------------------------------------------------------------------
    # Table 4: Exp P CPU Edge Benchmarks & Duty-Cycle Projections
    # ------------------------------------------------------------------
    v_bench = exp_p["vision_cpu_benchmarks_ms"]
    a_bench = exp_p["audio_cpu_benchmarks_ms"]
    fsm_bench = exp_p["v3_fsm_closed_loop_121_ticks_ms"]
    ckpt_audit = exp_p["checkpoint_size_audit"]

    t4_fields = [
        "stage_or_artifact",
        "input_or_mode",
        "measured_mean_ms_or_size",
        "p95_ms_or_diff",
        "fps_or_reduction",
        "evidence_status",
    ]
    d416 = exp_p["event_triggered_duty_cycle_416"]["duty_cycle_scenarios"]
    d640 = exp_p["event_triggered_duty_cycle_640"]["duty_cycle_scenarios"]
    e2e_speedup = round(v_bench["yolo_predict_e2e_640"]["mean_ms"] / v_bench["yolo_predict_e2e_416"]["mean_ms"], 2)
    aud_total_ms = round(a_bench["log_mel_1s_numpy"]["mean_ms"] + a_bench["cnn_torchscript_fp32"]["mean_ms"], 3)
    fsm_hz = round(1000.0 / fsm_bench["per_tick_mean_ms"])
    t4_rows = [
        {
            "stage_or_artifact": "YOLOv8n checkpoint file",
            "input_or_mode": "Raw unstripped vs stripped FP16",
            "measured_mean_ms_or_size": f"{ckpt_audit['vision_raw_unstripped_bytes']:,} B -> {ckpt_audit['vision_stripped_fp16_bytes']:,} B",
            "p95_ms_or_diff": f"FP32: {ckpt_audit['vision_stripped_fp32_bytes']:,} B",
            "fps_or_reduction": f"-{ckpt_audit['vision_strip_reduction_pct']}% disk",
            "evidence_status": "Measured on repo artifact",
        },
        {
            "stage_or_artifact": "YOLOv8n PyTorch eager",
            "input_or_mode": "1x3x640x640 / 416x416 / 320x320",
            "measured_mean_ms_or_size": f"{v_bench['yolov8n_forward_640_fp32']['mean_ms']} / {v_bench['yolov8n_forward_416_fp32']['mean_ms']} / {v_bench['yolov8n_forward_320_fp32']['mean_ms']} ms",
            "p95_ms_or_diff": f"p95: {v_bench['yolov8n_forward_640_fp32']['p95_ms']} / {v_bench['yolov8n_forward_416_fp32']['p95_ms']} / {v_bench['yolov8n_forward_320_fp32']['p95_ms']} ms",
            "fps_or_reduction": f"{v_bench['yolov8n_forward_640_fp32']['fps_equivalent']} / {v_bench['yolov8n_forward_416_fp32']['fps_equivalent']} / {v_bench['yolov8n_forward_320_fp32']['fps_equivalent']} FPS",
            "evidence_status": "Measured Apple M1 CPU (SYNTHETIC_ONLY)",
        },
        {
            "stage_or_artifact": "YOLOv8n TorchScript",
            "input_or_mode": "640x640 / 416x416 / 320x320",
            "measured_mean_ms_or_size": f"{v_bench['yolov8n_torchscript_640_fp32']['mean_ms']} / {v_bench['yolov8n_torchscript_416_fp32']['mean_ms']} / {v_bench['yolov8n_torchscript_320_fp32']['mean_ms']} ms",
            "p95_ms_or_diff": "max_abs_diff=0.0",
            "fps_or_reduction": f"{v_bench['yolov8n_torchscript_640_fp32']['fps_equivalent']} / {v_bench['yolov8n_torchscript_416_fp32']['fps_equivalent']} / {v_bench['yolov8n_torchscript_320_fp32']['fps_equivalent']} FPS",
            "evidence_status": "Measured Apple M1 CPU (SYNTHETIC_ONLY)",
        },
        {
            "stage_or_artifact": "Ultralytics YOLO.predict E2E",
            "input_or_mode": "640px vs 416px numpy RGB",
            "measured_mean_ms_or_size": f"{v_bench['yolo_predict_e2e_640']['mean_ms']} vs {v_bench['yolo_predict_e2e_416']['mean_ms']} ms",
            "p95_ms_or_diff": f"p95: {v_bench['yolo_predict_e2e_640']['p95_ms']} vs {v_bench['yolo_predict_e2e_416']['p95_ms']} ms",
            "fps_or_reduction": f"{v_bench['yolo_predict_e2e_640']['fps_equivalent']} vs {v_bench['yolo_predict_e2e_416']['fps_equivalent']} FPS ({e2e_speedup}x speedup)",
            "evidence_status": "Measured Apple M1 CPU (SYNTHETIC_ONLY)",
        },
        {
            "stage_or_artifact": "Audio log-Mel + CNN (TorchScript)",
            "input_or_mode": "1s 16kHz window [64x61]",
            "measured_mean_ms_or_size": f"{a_bench['log_mel_1s_numpy']['mean_ms']} + {a_bench['cnn_torchscript_fp32']['mean_ms']} ms ({aud_total_ms} ms total)",
            "p95_ms_or_diff": f"diff=0.0; INT8 Linear={a_bench['cnn_dynamic_int8_linear']['mean_ms']} ms (diff={a_bench['cnn_dynamic_int8_linear']['max_abs_diff_vs_eager']:.4f})",
            "fps_or_reduction": f"CNN TS={a_bench['cnn_torchscript_fp32']['fps_equivalent']} win/s",
            "evidence_status": "Measured Apple M1 CPU (SYNTHETIC_ONLY)",
        },
        {
            "stage_or_artifact": "V3 FSM + Collector + Gate",
            "input_or_mode": "121-tick full cycle",
            "measured_mean_ms_or_size": f"{fsm_bench['mean_ms']} ms total ({fsm_bench['per_tick_mean_ms']} ms/tick)",
            "p95_ms_or_diff": f"p95={fsm_bench['p95_ms']} ms",
            "fps_or_reduction": f"{fsm_hz:,} Hz tick rate",
            "evidence_status": "Measured Apple M1 CPU (SYNTHETIC_ONLY)",
        },
        {
            "stage_or_artifact": "Raspberry Pi 4B Duty Cycle (416px)",
            "input_or_mode": "24/7 5-FPS vs Event-Triggered (10/20/40 trains/d)",
            "measured_mean_ms_or_size": f"864,000 vs {d416[0]['total_gated_vision_frames_day']:,} / {d416[1]['total_gated_vision_frames_day']:,} / {d416[2]['total_gated_vision_frames_day']:,} frames/d",
            "p95_ms_or_diff": f"Continuous: {d416[0]['sbc_analytical_projections']['rpi4b_4gb_cortex_a72']['projected_continuous_core_fraction']} cores -> Gated: {d416[0]['sbc_analytical_projections']['rpi4b_4gb_cortex_a72']['projected_event_triggered_core_fraction']} / {d416[1]['sbc_analytical_projections']['rpi4b_4gb_cortex_a72']['projected_event_triggered_core_fraction']} / {d416[2]['sbc_analytical_projections']['rpi4b_4gb_cortex_a72']['projected_event_triggered_core_fraction']} cores",
            "fps_or_reduction": f"-{d416[2]['vision_frame_reduction_pct']}% to -{d416[0]['vision_frame_reduction_pct']}% frames (-{d416[2]['total_compute_time_reduction_pct']}% to -{d416[0]['total_compute_time_reduction_pct']}% compute)",
            "evidence_status": "ANALYTICAL_PROJECTION_UNMEASURED_HARDWARE (5.5x M1)",
        },
        {
            "stage_or_artifact": "Raspberry Pi 4B Duty Cycle (640px)",
            "input_or_mode": "24/7 5-FPS vs Event-Triggered (10/20/40 trains/d)",
            "measured_mean_ms_or_size": f"864,000 vs {d640[0]['total_gated_vision_frames_day']:,} / {d640[1]['total_gated_vision_frames_day']:,} / {d640[2]['total_gated_vision_frames_day']:,} frames/d",
            "p95_ms_or_diff": f"Continuous: {d640[0]['sbc_analytical_projections']['rpi4b_4gb_cortex_a72']['projected_continuous_core_fraction']} cores -> Gated: {d640[0]['sbc_analytical_projections']['rpi4b_4gb_cortex_a72']['projected_event_triggered_core_fraction']} / {d640[1]['sbc_analytical_projections']['rpi4b_4gb_cortex_a72']['projected_event_triggered_core_fraction']} / {d640[2]['sbc_analytical_projections']['rpi4b_4gb_cortex_a72']['projected_event_triggered_core_fraction']} cores",
            "fps_or_reduction": f"-{d640[2]['total_compute_time_reduction_pct']}% to -{d640[0]['total_compute_time_reduction_pct']}% compute",
            "evidence_status": "ANALYTICAL_PROJECTION_UNMEASURED_HARDWARE (5.5x M1)",
        },
    ]
    _write_csv(OUT_DIR / "table4_exp_p_cpu_edge_and_duty_cycle.csv", t4_fields, t4_rows)

    # ------------------------------------------------------------------
    # Table 5: Exp Q Weather Attenuation & Interlocking Stress
    # ------------------------------------------------------------------
    t5_fields = [
        "alpha_conf",
        "effective_front_conf",
        "burst_drop_prob_range",
        "runs_count",
        "closure_rate",
        "reopen_rate",
        "failsafe_rate",
        "miss_open_rate",
        "unsafe_opening_count",
        "all_transitions_legal",
    ]
    t5_rows = []
    alphas = sorted({float(r["alpha_conf"]) for r in exp_q["weather_dropout_grid"]}, reverse=True)
    for alpha in alphas:
        sub = [r for r in exp_q["weather_dropout_grid"] if abs(float(r["alpha_conf"]) - alpha) < 1e-6]
        t5_rows.append(
            {
                "alpha_conf": alpha,
                "effective_front_conf": sub[0]["effective_front_conf"],
                "burst_drop_prob_range": "0.00 to 0.50 (4 levels x 5 seeds)",
                "runs_count": sum(int(r["n_seeds"]) for r in sub),
                "closure_rate": round(sum(float(r["closure_rate"]) for r in sub) / len(sub), 3),
                "reopen_rate": round(sum(float(r["reopen_rate"]) for r in sub) / len(sub), 3),
                "failsafe_rate": round(sum(float(r["failsafe_rate"]) for r in sub) / len(sub), 3),
                "miss_open_rate": round(sum(float(r["miss_open_rate"]) for r in sub) / len(sub), 3),
                "unsafe_opening_count": sum(int(r["unsafe_opening_count"]) for r in sub),
                "all_transitions_legal": all(bool(r["all_transitions_legal"]) for r in sub),
            }
        )
    _write_csv(OUT_DIR / "table5_exp_q_weather_and_interlocking_stress.csv", t5_fields, t5_rows)

    # ------------------------------------------------------------------
    # Table 6: Exp R LOEO Cross-Validation, Optical-Degradation Wakeup & Host Edge Scaling
    # ------------------------------------------------------------------
    loeo = exp_r["loeo_acoustic_crossval"]
    loeo_base = loeo["baseline_frozen_tau037_k1"]
    loeo_oof = loeo["loeo_oof_hysteresis_metrics"]
    loeo_cal = loeo["oof_calibration"]
    loeo_ci = loeo["bootstrap_95_ci"]
    wake = exp_r["optical_degradation_wakeup_ablation"]
    w35 = next(r for r in wake["attenuation_sweep"] if abs(float(r["alpha_conf"]) - 0.35) < 1e-6)
    ts = edge_scale["thread_scaling_ms"]

    t6_fields = [
        "component",
        "configuration",
        "primary_metric",
        "secondary_metric",
        "evidence_status",
    ]
    t6_rows = [
        {
            "component": "Exp R: Audio LOEO Baseline",
            "configuration": "Frozen tau=0.37, k=1 (n=23 labeled train)",
            "primary_metric": f"F1={loeo_base['f1']} Acc={loeo_base['accuracy']} Spec={loeo_base['specificity']}",
            "secondary_metric": f"Uncal Brier={loeo_cal['uncalibrated_brier']} ECE={loeo_cal['uncalibrated_ece_5bin']}",
            "evidence_status": "REAL_LOCAL_BATCH4_AUDIO (unbiased baseline)",
        },
        {
            "component": "Exp R: Nested LOEO OOF",
            "configuration": "23-fold OOF T-scale + hysteresis (tau=0.75,k=2 in 20/23)",
            "primary_metric": f"F1={loeo_oof['f1']} [CI95 {loeo_ci['f1']['ci95_low']}..{loeo_ci['f1']['ci95_high']}], Acc={loeo_oof['accuracy']}, Spec={loeo_oof['specificity']}",
            "secondary_metric": f"OOF Brier={loeo_cal['oof_temp_scaled_brier']} ECE={loeo_cal['oof_temp_scaled_ece_5bin']} (dBrier CI [{loeo_ci['cal_minus_raw_brier']['ci95_low']}..{loeo_ci['cal_minus_raw_brier']['ci95_high']}])",
            "evidence_status": "REAL_LOCAL_BATCH4_AUDIO (out-of-fold + 2000x bootstrap)",
        },
        {
            "component": "Exp R: Optical-Degraded Wakeup",
            "configuration": "Opt-in L3 failsafe at alpha=0.35 (conf=0.308) + sustained horn",
            "primary_metric": f"Baseline closed={w35['baseline_v3_closed']} -> Wakeup closed={w35['wakeup_v3_closed']} (@{w35['wakeup_v3_trigger_s']:.1f}s)",
            "secondary_metric": f"0 unsafe opens; clear_ambient={wake['controls']['clear_optics_sustained_ambient_horn_closed']}, impulse={wake['controls']['degraded_optics_single_impulse_horn_closed']}",
            "evidence_status": "SYNTHETIC_ONLY (default V3 flag=False)",
        },
        {
            "component": "Host Edge Thread Scaling",
            "configuration": f"TorchScript 416px & 320px + Audio TS ({edge_scale['hardware']['machine']}, Pi_tested={edge_scale['physical_raspberry_pi_tested']})",
            "primary_metric": f"1/2/4T 416px={ts['threads_1']['vision_416_ts_ms']['mean_ms']}/{ts['threads_2']['vision_416_ts_ms']['mean_ms']}/{ts['threads_4']['vision_416_ts_ms']['mean_ms']} ms; 320px={ts['threads_1']['vision_320_ts_ms']['mean_ms']}/{ts['threads_2']['vision_320_ts_ms']['mean_ms']}/{ts['threads_4']['vision_320_ts_ms']['mean_ms']} ms",
            "secondary_metric": f"4T Audio TS={ts['threads_4']['audio_ts_ms']['mean_ms']} ms, logMel={ts['threads_4']['log_mel_ms']['mean_ms']} ms, RSS={edge_scale['peak_process_rss_mb']} MB",
            "evidence_status": "Measured Apple M1 CPU (physical Pi unmeasured)",
        },
    ]
    _write_csv(OUT_DIR / "table6_exp_r_loeo_wakeup_and_edge_scaling.csv", t6_fields, t6_rows)

    # ------------------------------------------------------------------
    # Unified Markdown Summary
    # ------------------------------------------------------------------
    md_sections = [
        "# Publication-Ready Summary Tables (`Exp A` – `Exp R` & Dataset Leakage Audit)\n",
        "Generated deterministically by `scripts/generate_master_publication_tables.py` from verified repository artifacts.\n",
        "## Table 1 — Vision V1 & Audio V3 Dataset Split Leakage Audit vs Clean Candidates\n",
        _md_table(t1_fields, [[r[k] for k in t1_fields] for r in t1_rows]),
        "\n\n## Table 2 — Decision Policy & Modality Ablation Summary (`Exp D`, `Exp J`, `Exp K`)\n",
        _md_table(t2_fields, [[r[k] for k in t2_fields] for r in t2_rows]),
        "\n\n## Table 3 — `Exp O`: Field Audio Threshold & Consecutive-Window Hysteresis Pareto Frontier\n",
        _md_table(t3_fields, [[r[k] for k in t3_fields] for r in t3_rows]),
        "\n\n## Table 4 — `Exp P`: Measured CPU Stage Profiling (Apple M1) & Analytical SBC Duty-Cycle Projections\n",
        _md_table(t4_fields, [[r[k] for k in t4_fields] for r in t4_rows]),
        "\n\n## Table 5 — `Exp Q`: Synthetic Optical Attenuation x Burst-Dropout Stress Grid (`100` runs)\n",
        _md_table(t5_fields, [[r[k] for k in t5_fields] for r in t5_rows]),
        "\n\n## Table 6 — `Exp R` & Host Edge Scaling (`LOEO CV`, `Optical-Degraded Wakeup`, `TorchScript Thread Scaling`)\n",
        _md_table(t6_fields, [[r[k] for k in t6_fields] for r in t6_rows]),
        "\n",
    ]
    (OUT_DIR / "PUBLICATION_TABLES.md").write_text("\n".join(md_sections), encoding="utf-8")
    print(json.dumps({"status": "OK", "tables_dir": str(OUT_DIR.relative_to(ROOT)), "files": sorted(p.name for p in OUT_DIR.iterdir())}, indent=2))


if __name__ == "__main__":
    main()
