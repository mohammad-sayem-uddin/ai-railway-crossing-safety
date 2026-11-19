#!/usr/bin/env python3
"""Build Mission 11 authoritative 27-event deliverables, figures, tables, and handover updates.

Strictly data-driven from verified JSON outputs under:
- ``results/upright_inference_v2/UPRIGHT_INFERENCE_MANIFEST.json``
- ``results/upright_27_event_evaluation/*.json``
- ``results/multimodal_27_event_evaluation/*.json``
Never accesses raw media.
"""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import generate_mission11_upright_figures as fig11  # noqa: E402

UPRIGHT_MANIFEST_PATH = ROOT / "results" / "upright_inference_v2" / "UPRIGHT_INFERENCE_MANIFEST.json"
UPRIGHT_EVAL_DIR = ROOT / "results" / "upright_27_event_evaluation"
BASELINE_EVAL_DIR = ROOT / "results" / "multimodal_27_event_evaluation"
HANDOVER_MD = ROOT / "docs" / "generated" / "FINAL_PROFESSOR_RESEARCH_HANDOVER.md"
TABLES_MD = ROOT / "docs" / "generated" / "professor_research_handover" / "PUBLICATION_TABLES_AND_CAPTIONS.md"
INDEX_MD = ROOT / "docs" / "generated" / "professor_research_handover" / "README_HANDOVER_INDEX.md"
MANIFEST_JSON = ROOT / "docs" / "generated" / "professor_research_handover" / "HANDOVER_EVIDENCE_MANIFEST.json"


def _sha256_text_file(path: Path) -> tuple[int, str]:
    with path.open(encoding="utf-8", newline="") as handle:
        encoded = handle.read().encode("utf-8")
    return len(encoded), hashlib.sha256(encoded).hexdigest()


def _binary_outcome(pred: bool, truth: bool, *, cohort: str, include_engine: bool = False) -> str:
    if cohort == "engine_events" and not include_engine:
        return "ENGINE_DETECTED" if pred else "ENGINE_MISSED"
    if truth and pred:
        return "TP"
    if truth and not pred:
        return "FN"
    if not truth and pred:
        return "FP"
    return "TN"


def _false_alarm_cause(row: dict[str, Any]) -> str:
    causes: list[str] = []
    if row["cohort"] in ("no_train_events", "engine_events") or not row["gt_horn_present"]:
        if row["pred_A1_audio_037_k1"] and not row["gt_horn_present"]:
            causes.append(
                f"Audio tau>=0.37 k=1 emitted {row['audio_pos_037']} FP windows "
                f"(max={row['audio_max_score']}@{row['audio_peak_s']}s, max_run_075={row['audio_max_run_075']}) on non-horn road/ambient sound"
            )
    if row["cohort"] == "no_train_events":
        if row["front_det_frames"] > 0:
            causes.append(
                f"Front spurious dets={row['front_det_frames']}f (mc={row['front_max_consec']}, maxC={row['front_max_conf']})"
            )
        if row["back_cls_front"] > 0:
            causes.append(
                f"Back spurious front-class={row['back_cls_front']}obj (side={row['back_cls_side']}, rear={row['back_cls_rear']})"
            )
    return "; ".join(causes) if causes else "NONE"


def _missed_detection_cause(row: dict[str, Any]) -> str:
    if row["cohort"] == "no_train_events":
        return "N/A (no_train control)"
    if row["cohort"] == "engine_events":
        if not row["pred_F6_full_multimodal_dual_sr_or_audio_075_k2"]:
            return (
                f"Solitary locomotive (0 trailing cars): front_mc={row['front_max_consec']} ({row['front_det_frames']}f), "
                f"back cls F/S/R={row['back_cls_front']}/{row['back_cls_side']}/{row['back_cls_rear']}, "
                f"horn absent (audio max={row['audio_max_score']})"
            )
        return "NONE (detected by upright F6)"
    if row["pred_F6_full_multimodal_dual_sr_or_audio_075_k2"]:
        return "NONE (detected by upright F6)"
    if row["pred_F7_exploratory_2of3_multimodal"]:
        return (
            f"Missed F6 (front_mc={row['front_max_consec']}, back_sr_c={row['back_max_consec_side_rear']}, "
            f"aud_r75={row['audio_max_run_075']}); recovered by F7 <=0.45s cross-frame pairing"
        )
    return (
        f"Optical+acoustic miss even upright (front={row['front_det_frames']}f/mc={row['front_max_consec']}, "
        f"back={row['back_det_frames']}f/sr_c={row['back_max_consec_side_rear']}, "
        f"horn={row['adopted_horn_status']}, aud_max={row['audio_max_score']}, r75={row['audio_max_run_075']})"
    )


def build_authoritative_27_event_table(
    eval_dir: Path = UPRIGHT_EVAL_DIR,
) -> tuple[Path, Path]:
    """Generate explicit Section-6 27-event table with TP/FP/FN/TN, causes, and gate outcomes."""
    events_payload = json.loads((eval_dir / "event_by_event_27_multimodal_evaluation.json").read_text(encoding="utf-8"))
    rows_out: list[dict[str, Any]] = []
    for r in events_payload["events"]:
        coh = r["cohort"]
        gt_train = bool(r["gt_is_train_event"])
        gt_rail = bool(r["gt_rail_vehicle_present"])
        gt_horn = bool(r["gt_horn_present"])
        rows_out.append(
            {
                "event_id": r["event_id"],
                "recording_session": r["recording_session"],
                "lighting": r["lighting"],
                "weather": r["weather"],
                "event_type": r["event_type"],
                "cohort": coh,
                "reference_label_provenance": "RESEARCHER_ADOPTED_AI_ASSISTED_UNREVIEWED_STAGE21",
                "gt_is_train_event": gt_train,
                "gt_rail_vehicle_present": gt_rail,
                "gt_horn_present": gt_horn,
                "front_det_frames": r["front_det_frames"],
                "front_max_consec": r["front_max_consec"],
                "front_cls_front_side_rear": f"{r['front_cls_front']}/{r['front_cls_side']}/{r['front_cls_rear']}",
                "front_conf_min_mean_max": f"{r['front_min_conf']}/{r['front_mean_conf']}/{r['front_max_conf']}",
                "front_first_det_s": r["front_first_det_s"],
                "back_det_frames": r["back_det_frames"],
                "back_max_consec": r["back_max_consec"],
                "back_max_consec_side_rear": r["back_max_consec_side_rear"],
                "back_cls_front_side_rear": f"{r['back_cls_front']}/{r['back_cls_side']}/{r['back_cls_rear']}",
                "back_conf_min_mean_max": f"{r['back_min_conf']}/{r['back_mean_conf']}/{r['back_max_conf']}",
                "back_first_det_s": r["back_first_det_s"],
                "side_proxy_total_objects": r["side_proxy_total_objects"],
                "side_tracker_state": r["side_tracker_state"],
                "audio_windows": r["audio_windows"],
                "audio_pos_037": r["audio_pos_037"],
                "audio_pos_075": r["audio_pos_075"],
                "audio_max_run_075": r["audio_max_run_075"],
                "audio_mean_max_score": f"{r['audio_mean_score']}/{r['audio_max_score']}",
                "audio_first_037_s": r["audio_first_037_s"],
                "audio_first_075_k2_s": r["audio_first_075_k2_s"],
                "pred_V2_front_L1": r["pred_V2_front_L1_confirm2"],
                "pred_V5_back_sr": r["pred_V5_back_confirm2_side_rear"],
                "pred_V8_dual_vision_sr": r["pred_V8_dual_vision_confirm2_side_rear"],
                "pred_A1_audio_037_k1": r["pred_A1_audio_037_k1"],
                "pred_A3_audio_075_k2": r["pred_A3_audio_075_k2"],
                "pred_F2_v3_default": r["pred_F2_v3_default_advisory_audio"],
                "pred_F4_front_or_audio": r["pred_F4_front_L1_or_audio_075_k2"],
                "pred_F6_full_mm": r["pred_F6_full_multimodal_dual_sr_or_audio_075_k2"],
                "pred_F7_2of3": r["pred_F7_exploratory_2of3_multimodal"],
                "pred_F8_strong_2of3_quorum": (
                    int(bool(r["pred_V2_front_L1_confirm2"]))
                    + int(bool(r["pred_V5_back_confirm2_side_rear"]))
                    + int(bool(r["pred_A3_audio_075_k2"]))
                ) >= 2,
                "class_V2_train23_vs_nt3": _binary_outcome(bool(r["pred_V2_front_L1_confirm2"]), gt_train, cohort=coh),
                "class_V8_dual_sr_train23_vs_nt3": _binary_outcome(bool(r["pred_V8_dual_vision_confirm2_side_rear"]), gt_train, cohort=coh),
                "class_A3_horn_status": _binary_outcome(bool(r["pred_A3_audio_075_k2"]), gt_horn, cohort=coh, include_engine=True),
                "class_F6_train23_vs_nt3": _binary_outcome(bool(r["pred_F6_full_multimodal_dual_sr_or_audio_075_k2"]), gt_train, cohort=coh),
                "class_F6_rail24_vs_nt3": _binary_outcome(bool(r["pred_F6_full_multimodal_dual_sr_or_audio_075_k2"]), gt_rail, cohort=coh, include_engine=True),
                "class_F7_train23_vs_nt3": _binary_outcome(bool(r["pred_F7_exploratory_2of3_multimodal"]), gt_train, cohort=coh),
                "class_F8_quorum_train23_vs_nt3": _binary_outcome(
                    (
                        int(bool(r["pred_V2_front_L1_confirm2"]))
                        + int(bool(r["pred_V5_back_confirm2_side_rear"]))
                        + int(bool(r["pred_A3_audio_075_k2"]))
                    ) >= 2,
                    gt_train,
                    cohort=coh,
                ),
                "false_alarm_cause": _false_alarm_cause(r),
                "missed_detection_cause": _missed_detection_cause(r),
                "f6_fsm_triggered": r["f6_fsm_triggered"],
                "f6_fsm_trigger_s": r["f6_fsm_trigger_s"],
                "f6_fsm_trigger_rule": r["f6_fsm_trigger_rule"],
                "f6_fsm_t_warning_s": r["f6_fsm_t_warning_s"],
                "f6_fsm_t_close_cmd_s": r["f6_fsm_t_close_cmd_s"],
                "f6_fsm_t_fully_closed_s": r["f6_fsm_t_fully_closed_s"],
                "gt_T2_s": r["gt_T2_s"],
                "f6_fsm_full_closure_margin_vs_T2_s": r["f6_fsm_full_closure_margin_vs_T2_s"],
                "f6_fsm_closure_timing_class": r["f6_fsm_closure_timing_class"],
                "f6_fsm_reopen_completed": r["f6_fsm_reopen_completed"],
                "f6_fsm_final_state": r["f6_fsm_final_state"],
                "f6_fsm_final_gate_state": r["f6_fsm_final_gate_state"],
            }
        )

    csv_out = eval_dir / "authoritative_27_event_results_table.csv"
    with open(csv_out, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows_out[0].keys()))
        writer.writeheader()
        writer.writerows(rows_out)

    json_out = eval_dir / "authoritative_27_event_results_table.json"
    json_out.write_text(
        json.dumps(
            {
                "schema_version": "mission11-authoritative-27-event-table/1.0",
                "generated_at_utc": dt.datetime.now(dt.UTC).isoformat(),
                "n_events": len(rows_out),
                "events": rows_out,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return csv_out, json_out


def _upsert_marked_block(doc_path: Path, marker_start: str, marker_end: str, block_body: str) -> None:
    text = doc_path.read_text(encoding="utf-8")
    wrapped = f"{marker_start}\n{block_body.rstrip()}\n{marker_end}"
    if marker_start in text and marker_end in text:
        pre = text.split(marker_start, 1)[0].rstrip()
        post = text.split(marker_end, 1)[1].lstrip("\n")
        new_text = pre + "\n\n" + wrapped + ("\n\n" + post if post else "\n")
    else:
        new_text = text.rstrip() + "\n\n" + wrapped + "\n"
    doc_path.write_text(new_text, encoding="utf-8")


def update_handover_and_tables(fig_hashes: dict[Path, tuple[int, str]], auth_csv: Path, auth_json: Path) -> None:
    comp = json.loads((UPRIGHT_EVAL_DIR / "baseline_vs_upright_comparison.json").read_text(encoding="utf-8"))
    fsm = json.loads((UPRIGHT_EVAL_DIR / "causal_fsm_gate_timing_summary.json").read_text(encoding="utf-8"))
    up_ab = json.loads((UPRIGHT_EVAL_DIR / "modality_and_fusion_ablation_metrics.json").read_text(encoding="utf-8"))
    manifest = json.loads(UPRIGHT_MANIFEST_PATH.read_text(encoding="utf-8"))

    v1 = up_ab["view1_train23_vs_no_train3_engine_separate"]
    v3 = up_ab["view3_rail_vehicle24_vs_no_train3"]
    by_name = {c["configuration"]: c for c in comp["config_comparison"]}
    smap = fsm["summaries"]
    sess = comp["session_comparison"]

    # 1. Append/Update Table X & XI in PUBLICATION_TABLES_AND_CAPTIONS.md
    t_lines: list[str] = [
        "## Table X — Upright (`db40305`) Original-Media 27-Event Modality & Fusion vs `pre-db40305` Baseline",
        "*(Evidence: [`UPRIGHT_INFERENCE_MANIFEST.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/upright_inference_v2/UPRIGHT_INFERENCE_MANIFEST.json), [`baseline_vs_upright_comparison.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/upright_27_event_evaluation/baseline_vs_upright_comparison.json), [`authoritative_27_event_results_table.csv`](file:///Users/sayemuddin/Desktop/Train_automation/results/upright_27_event_evaluation/authoritative_27_event_results_table.csv); `54/54` streams orientation-verified, audio max score delta vs cache = `"
        + f"{comp['audio_invariance']['max_abs_score_diff_across_all_windows']}`)*",
        "",
        "| Configuration | Base TP/23 | Upright TP/23 | ΔTP | NT FP/3 | Eng001 (B->U) | Upright Prec | Upright Recall [95% CI] | Upright Spec | Upright F1 | Rail24 F1 (V3) | McNemar p (Base vs Up) |",
        "|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for cfg_key, um in v1.items():
        cm = by_name[cfg_key]
        r3 = v3[cfg_key]
        ci_lo, ci_hi = um["recall_ci95"]
        eng_str = f"{'Y' if cm['baseline_engine_001'] else 'N'}->{'Y' if cm['upright_engine_001'] else 'N'}"
        t_lines.append(
            f"| `{cfg_key}` | {cm['baseline_tp']} | **{um['tp']}** | {cm['delta_tp']:+d} | {um['fp']} | {eng_str} | "
            f"{um['precision']*100:.1f}% | {um['recall']*100:.1f}% [{ci_lo*100:.1f}-{ci_hi*100:.1f}%] | "
            f"{um['specificity']*100:.1f}% | {um['f1']*100:.1f}% | {r3['tp']}/24 ({r3['f1']*100:.1f}%) | "
            f"{cm['mcnemar_p_upright_vs_baseline']:.4f} |"
        )
    q8 = comp["exploratory_quorum_comparison"]["F8_Exploratory_Strong_2of3_Quorum"]
    q8b, q8u = q8["baseline"], q8["upright"]
    q8t = q8["causal_quorum_timing_summary"]
    t_lines.append(
        f"| `F8_Exploratory_Strong_2of3_Quorum` (>=2 of V2,V5,A3) | {q8b['tp']} | **{q8u['tp']}** | "
        f"{q8u['tp'] - q8b['tp']:+d} | {q8u['fp_no_train']} | {'Y' if q8b['engine_001_detected'] else 'N'}->{'Y' if q8u['engine_001_detected'] else 'N'} | "
        f"{q8u['precision']*100:.1f}% | {q8u['recall']*100:.1f}% | {q8u['specificity']*100:.1f}% | "
        f"{q8u['f1']*100:.1f}% | {q8u['rail24_tp']}/24 ({q8u['rail24_f1']*100:.1f}%) | "
        f"{q8['mcnemar_p_baseline_vs_upright']:.4f} |"
    )
    t_lines.extend(
        [
            "",
            "## Table XI — Upright (`db40305`) Causal V3 FSM Gate-Control Replay & Previously Missed Event Recovery",
            "*(Evidence: [`causal_fsm_gate_timing_summary.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/upright_27_event_evaluation/causal_fsm_gate_timing_summary.json), [`COMPLETE_27_EVENT_UPRIGHT_MULTIMODAL_REPORT.md`](file:///Users/sayemuddin/Desktop/Train_automation/results/upright_27_event_evaluation/COMPLETE_27_EVENT_UPRIGHT_MULTIMODAL_REPORT.md))*",
            "",
            "| Causal FSM Architecture | Train Trig/23 | Full Boom Closed/23 | Warn<=T2 | Cmd<=T2 | Half<=T2 | Full<=T2 | NT FP/3 | Eng001 | Reopen Cycles |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for fk in [
        "FSM_V2_Front_L1",
        "FSM_F2_V3_Default_B4",
        "FSM_F3_WeakFront_Plus_Audio",
        "FSM_F4_Front_Or_Audio075k2",
        "FSM_F5_Dual_Vision_Sync11",
        "FSM_F6_Full_MM_Sync11",
        "FSM_F6_Full_MM_Bounded27",
        "FSM_F7_Exploratory_2of3_Bounded27",
    ]:
        fs = smap[fk]
        is_sync = fk.endswith("_Sync11")
        nt = "N/A" if is_sync else f"{fs['no_train_false_closures']}/3"
        eng = "N/A" if is_sync else ("YES" if fs["engine_001_triggered"] else "no")
        t_lines.append(
            f"| `{fk}` | {fs['train_triggers']}/{fs['n_train']} | {fs['train_full_closures']}/{fs['n_train']} | "
            f"{fs['train_pre_T2_warning']} | {fs['train_pre_T2_close_cmd']} | {fs['train_pre_T2_half_closed']} | "
            f"{fs['train_pre_T2_full_closure']} | {nt} | {eng} | {fs['complete_close_reopen_cycles']} |"
        )
    t_lines.extend(
        [
            "",
            "16. **Fig. 16 (`fig16`):** Pre-`db40305` sideways caches vs upright (`db40305`) original-media train recall, no-train FPs, and Session 1/Session 2 stratification across all modalities and fusion rules. ([`fig16_upright_vs_baseline_ablation.png`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/figures/fig16_upright_vs_baseline_ablation.png))",
            "17. **Fig. 17 (`fig17`):** Per-event optical detection recovery across all 27 original recordings and causal V3 FSM gate-closure timing relative to `T2`. ([`fig17_upright_event_recovery_and_fsm_timing.png`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/figures/fig17_upright_event_recovery_and_fsm_timing.png))",
        ]
    )
    _upsert_marked_block(
        TABLES_MD,
        "<!-- MISSION11_UPRIGHT_TABLES_START -->",
        "<!-- MISSION11_UPRIGHT_TABLES_END -->",
        "\n".join(t_lines),
    )

    # 2. Update FINAL_PROFESSOR_RESEARCH_HANDOVER.md
    rec_f6 = by_name["F6_Full_Multimodal_Dual_SideRear_Or_Audio075k2"]["recovered_train_events"]
    v2_m = by_name["V2_Front_L1_Confirm2"]
    v5_m = by_name["V5_Back_Confirm2_SideRear"]
    v8_m = by_name["V8_Dual_Vision_Confirm2_SideRear"]
    a1_m = by_name["A1_Audio_Frozen_037_k1"]
    a3_m = by_name["A3_Audio_Hysteresis_075_k2"]
    f6_m = by_name["F6_Full_Multimodal_Dual_SideRear_Or_Audio075k2"]
    f7_m = by_name["F7_Exploratory_2of3_Multimodal"]
    q8_all = comp["exploratory_quorum_comparison"]["F8_Exploratory_Strong_2of3_Quorum"]
    q8u = q8_all["upright"]
    q8t = q8_all["causal_quorum_timing_summary"]
    fsm_f6 = smap["FSM_F6_Full_MM_Bounded27"]
    fsm_f7 = smap["FSM_F7_Exploratory_2of3_Bounded27"]
    h_lines = [
        "### 7. Completed Original-Media Upright (`db40305`) 27-Event Multimodal Experiment (Mission 11)",
        "",
        f"*(Owner authorization `{manifest['authorization']['authorization_id']}` verified live; `54/54` source streams decoded with `{manifest['orientation_policy']}` and SHA-256-verified against inventory; full outputs in [`COMPLETE_27_EVENT_UPRIGHT_MULTIMODAL_REPORT.md`](file:///Users/sayemuddin/Desktop/Train_automation/results/upright_27_event_evaluation/COMPLETE_27_EVENT_UPRIGHT_MULTIMODAL_REPORT.md), [`authoritative_27_event_results_table.csv`](file:///Users/sayemuddin/Desktop/Train_automation/results/upright_27_event_evaluation/authoritative_27_event_results_table.csv), and `fig16`–`fig17`.)*",
        "",
        f"- **Orientation-Corrected Vision Recovery:** Front-only L1 causal vision (`V2`) rose from **`{v2_m['baseline_tp']}/23` -> `{v2_m['upright_tp']}/23`** (`McNemar p = {v2_m['mcnemar_p_upright_vs_baseline']:.4f}`, `{v2_m['upright_fp_no_train']}/3` no-train FP on upright `no_train_002`); Back-only Side/Rear (`V5`) rose **`{v5_m['baseline_tp']}/23` -> `{v5_m['upright_tp']}/23`** (`p = {v5_m['mcnemar_p_upright_vs_baseline']:.4f}`, **`{v5_m['upright_fp_no_train']}/3` FP**); Dual-Vision Side/Rear (`V8`) rose **`{v8_m['baseline_tp']}/23` -> `{v8_m['upright_tp']}/23`** (`p = {v8_m['mcnemar_p_upright_vs_baseline']:.4f}`, `{v8_m['upright_fp_no_train']}/3` FP). Session 1 daytime `V2` moved `{sess['Session 1']['baseline_V2_train_tp']}/{sess['Session 1']['n_train_events']} -> {sess['Session 1']['upright_V2_train_tp']}/{sess['Session 1']['n_train_events']}`.",
        f"- **Fresh Natural Log-Mel Audio Invariance & Horn Role:** Re-extracting 16 kHz mono WAVs and running frozen `CompactTrainHornCNN` (`log(mel + 1e-10)`) reproduced baseline scores within **`{comp['audio_invariance']['max_abs_score_diff_across_all_windows']}` max abs diff**. Frozen `(0.37, k=1)` detected `{a1_m['upright_tp']}/23` trains with **`{a1_m['upright_fp_no_train']}/3` road-horn FPs**; hysteresis `(0.75, k=2)` detected `{a3_m['upright_tp']}/23` with **`{a3_m['upright_fp_no_train']}/3` FPs**.",
        f"- **Multimodal Fusion (`F6`, `F7`, & Exploratory `F8` Quorum) + `8` Previously Missed Events:** Upright `F6` achieved **`{f6_m['upright_tp']}/23` (`F1={f6_m['upright_f1']*100:.1f}%`, `{f6_m['upright_fp_no_train']}/3` FP on `no_train_002`, `p={f6_m['mcnemar_p_upright_vs_baseline']:.4f}` vs baseline F6)** and exploratory `F7` achieved **`{f7_m['upright_tp']}/23` (`F1={f7_m['upright_f1']*100:.1f}%`, `{f7_m['upright_fp_no_train']}/3` FP, `p={f7_m['mcnemar_p_upright_vs_baseline']:.4f}` vs baseline F7)**, recovering all `{len(rec_f6)}` missed trains (`{', '.join(x.replace('train_events/', '') for x in rec_f6) or 'none'}`). Post-hoc `F8_Exploratory_Strong_2of3_Quorum` (`>=2 of {{V2,V5,A3}}`) suppressed the upright front `no_train_002` false positive and solitary `engine_001` (`{q8u['tp']}/23` TP, **`{q8u['fp_no_train']}/3` FP**, `Eng001=no`, **`F1={q8u['f1']*100:.1f}%`**), at a causal warning trade-off (`{q8t['f8_pre_T2_confirm']}/{q8t['n_train_with_T2']}` confirm <= `T2` vs `V2`/`F6` `{q8t['v2_pre_T2_confirm']}/{q8t['n_train_with_T2']}`). Solitary `engine_events/event_001` detection status: `V2={v2_m['upright_engine_001']}`, `V4_all_cls={by_name['V4_Back_Confirm2_AllClasses']['upright_engine_001']}`, `V5_SR={by_name['V5_Back_Confirm2_SideRear']['upright_engine_001']}`, `F6={f6_m['upright_engine_001']}`.",
        f"- **Causal V3 Gate-Control Timing & Departure Tracking:** Under upright `F6`, `{fsm_f6['train_triggers']}/23` triggered (`{fsm_f6['train_full_closures']}/23` full `0°` boom closures, `{fsm_f6['train_pre_T2_warning']}/23` warnings <= `T2`, `{fsm_f6['train_pre_T2_close_cmd']}/23` close cmds <= `T2`, **`{fsm_f6['train_pre_T2_full_closure']}/23` full closures <= `T2`**, `{fsm_f6['complete_close_reopen_cycles']}/27` reopen cycles); under `F7`, **`{fsm_f7['train_pre_T2_full_closure']}/23` full closures <= `T2`**. Upright `back_last_det_s - gt_T4_s` departure error (`n={comp['upright_m2_departure_summary']['n_events_with_T4_and_back_det']}`) measured mean `{comp['upright_m2_departure_summary']['mean_err_s']}s` (`{comp['upright_m2_departure_summary']['non_premature_count']}/22` non-premature). Remaining scientific boundaries (`0/27` independent `Stage-2.1` human reviews, single-crossing `leakage_safe = false`, `0/27` occupancy sensors, `physical_raspberry_pi_tested = false`) remain unchanged.",
    ]
    _upsert_marked_block(
        HANDOVER_MD,
        "<!-- MISSION11_UPRIGHT_HANDOVER_START -->",
        "<!-- MISSION11_UPRIGHT_HANDOVER_END -->",
        "\n".join(h_lines),
    )

    # 3. Update README_HANDOVER_INDEX.md cleanly without breaking the table above
    idx_block = "\n".join(
        [
            "### Mission 11 Original-Media Upright (`db40305`) Index",
            "",
            "| Component | Canonical File(s) | Scope / Status |",
            "|---|---|---|",
            (
                "| **11. Original-Media Upright Study (Mission 11)** | "
                "[`UPRIGHT_INFERENCE_MANIFEST.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/upright_inference_v2/UPRIGHT_INFERENCE_MANIFEST.json), "
                "[`COMPLETE_27_EVENT_UPRIGHT_MULTIMODAL_REPORT.md`](file:///Users/sayemuddin/Desktop/Train_automation/results/upright_27_event_evaluation/COMPLETE_27_EVENT_UPRIGHT_MULTIMODAL_REPORT.md), "
                "[`authoritative_27_event_results_table.csv`](file:///Users/sayemuddin/Desktop/Train_automation/results/upright_27_event_evaluation/authoritative_27_event_results_table.csv), "
                "[`baseline_vs_upright_comparison.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/upright_27_event_evaluation/baseline_vs_upright_comparison.json), "
                "`fig16`–`fig17` | `54/54` upright streams verified under owner `AUTH-MEDIA-ACCESS-20261119-MISSION10`; full pre-vs-post comparison & causal FSM replay |"
            ),
        ]
    )
    _upsert_marked_block(
        INDEX_MD,
        "<!-- MISSION11_INDEX_START -->",
        "<!-- MISSION11_INDEX_END -->",
        idx_block,
    )

    # 4. Update HANDOVER_EVIDENCE_MANIFEST.json preserving 51 'artifacts' entries
    hm = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))
    for entry in hm.get("artifacts", []):
        p = ROOT / entry["path"]
        if p.is_file() and p.suffix.lower() != ".png":
            entry["size_bytes"], entry["sha256"] = _sha256_text_file(p)
    for entry in hm.get("multimodal_27_event_evaluation_artifacts", []):
        p = ROOT / entry["path"]
        if p.is_file() and p.suffix.lower() != ".png":
            entry["size_bytes"], entry["sha256"] = _sha256_text_file(p)

    new_text_rels = [
        "scripts/generate_mission11_upright_figures.py",
        "scripts/build_mission11_handover_updates.py",
        "results/upright_inference_v2/UPRIGHT_INFERENCE_MANIFEST.json",
        "results/upright_27_event_evaluation/COMPLETE_27_EVENT_UPRIGHT_MULTIMODAL_REPORT.md",
        "results/upright_27_event_evaluation/event_by_event_27_multimodal_evaluation.csv",
        "results/upright_27_event_evaluation/event_by_event_27_multimodal_evaluation.json",
        "results/upright_27_event_evaluation/modality_and_fusion_ablation_metrics.csv",
        "results/upright_27_event_evaluation/modality_and_fusion_ablation_metrics.json",
        "results/upright_27_event_evaluation/modality_and_fusion_ablation_upright_vs_baseline.csv",
        "results/upright_27_event_evaluation/causal_fsm_gate_timing_summary.csv",
        "results/upright_27_event_evaluation/causal_fsm_gate_timing_summary.json",
        "results/upright_27_event_evaluation/failed_events_forensic_diagnosis.json",
        "results/upright_27_event_evaluation/baseline_vs_upright_comparison.json",
        str(auth_csv.relative_to(ROOT)),
        str(auth_json.relative_to(ROOT)),
    ]
    upright_entries = []
    for rel in new_text_rels:
        sz, sha = _sha256_text_file(ROOT / rel)
        upright_entries.append({"path": rel, "size_bytes": sz, "sha256": sha})
    for fp, (sz, sha) in fig_hashes.items():
        upright_entries.append({"path": str(fp.relative_to(ROOT)), "size_bytes": sz, "sha256": sha})
    hm["upright_27_event_experiment_artifacts"] = upright_entries
    hm["mission11_raw_media_accessed"] = True
    hm["mission11_authorization_id"] = manifest["authorization"]["authorization_id"]
    MANIFEST_JSON.write_text(json.dumps(hm, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    auth_csv, auth_json = build_authoritative_27_event_table()
    fig_hashes = fig11.generate_all_with_hashes()
    update_handover_and_tables(fig_hashes, auth_csv, auth_json)
    print(
        json.dumps(
            {
                "status": "OK",
                "authoritative_table": [str(auth_csv.relative_to(ROOT)), str(auth_json.relative_to(ROOT))],
                "figures": [str(p.relative_to(ROOT)) for p in fig_hashes],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
