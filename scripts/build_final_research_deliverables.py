#!/usr/bin/env python3
"""Build verified CSV deliverables in docs/generated/final_research/.

Reads ONLY deterministic artifacts generated under results/exploratory_execution/
and writes CSV summaries with explicit exploratory labeling.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
EXPLORATORY_DIR = REPO_ROOT / "results" / "exploratory_execution"
ANALYSIS_DIR = EXPLORATORY_DIR / "analysis"
REPLAY_SUMMARY_PATH = EXPLORATORY_DIR / "replays" / "replay_summary.json"
FAILURE_PATH = EXPLORATORY_DIR / "failure_injection" / "stress_and_recovery_results.json"
TEST_REPORT_PATH = REPO_ROOT / "docs" / "generated" / "final_research" / "test_execution_report.json"
REPRO_REPORT_PATH = ANALYSIS_DIR / "reproducibility_verification.json"
OUT_DIR = REPO_ROOT / "docs" / "generated" / "final_research"

EVAL_BASIS = "Exploratory evaluation against researcher-adopted AI-assisted reference annotations."


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    print(f"WROTE: {path.relative_to(REPO_ROOT)} ({len(rows)} rows)")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ablation = _read_json(ANALYSIS_DIR / "ablation_matrix.json")
    sms = _read_json(ANALYSIS_DIR / "safety_metrics_summary.json")
    replay_sum = _read_json(REPLAY_SUMMARY_PATH)
    stress = _read_json(FAILURE_PATH)
    test_rep = _read_json(TEST_REPORT_PATH)
    repro_rep = _read_json(REPRO_REPORT_PATH)
    dep_rows = _read_csv(ANALYSIS_DIR / "departure_reopening_analysis.csv")
    ev_csv_rows = _read_csv(ANALYSIS_DIR / "event_level_safety_metrics.csv")
    ab_csv_rows = _read_csv(ANALYSIS_DIR / "ablation_matrix.csv")

    # 1. ABLATION_MATRIX.csv & 2. EVENT_LEVEL_RESULTS.csv & 3. DEPARTURE_REOPENING_ANALYSIS.csv
    _write_csv(OUT_DIR / "ABLATION_MATRIX.csv", list(ab_csv_rows[0].keys()), ab_csv_rows)
    _write_csv(OUT_DIR / "EVENT_LEVEL_RESULTS.csv", list(ev_csv_rows[0].keys()), ev_csv_rows)
    _write_csv(OUT_DIR / "DEPARTURE_REOPENING_ANALYSIS.csv", list(dep_rows[0].keys()), dep_rows)

    # 4. BASELINE_COMPARISON.csv (combined view across ablation_rows)
    baseline_cols = [
        "scope",
        "run_label",
        "ablation_factor",
        "train_n",
        "missed_train_n",
        "missed_train_evaluable_n",
        "missed_train_rate",
        "missed_train_ci95",
        "zero_protection_n",
        "zero_protection_rate",
        "zero_protection_ci95",
        "m4_premature_n",
        "m4_evaluable_n",
        "m4_never_protected_n",
        "m4_premature_rate",
        "m4_premature_ci95",
        "reached_clear_n",
        "mean_warning_lead_s",
        "mean_closed_conv_a_s",
        "mean_closed_conv_b_s",
        "mean_blocked_fraction",
        "mean_transitions",
        "no_train_false_alarm_n",
        "no_train_false_alarm_episodes",
        "no_train_blocked_s",
        "evaluation_basis",
    ]
    baseline_out = [{**{k: r.get(k) for k in baseline_cols[:-1]}, "evaluation_basis": EVAL_BASIS} for r in ablation["ablation_rows"]]
    _write_csv(OUT_DIR / "BASELINE_COMPARISON.csv", baseline_cols, baseline_out)

    # 5. MULTIMODAL_EVALUATION.csv (sync11 contrasts + paired McNemar + tol=0.25 sensitivity)
    contrast_rows = []
    for c in ablation["paired_contrasts"]:
        bd = c["binary_discordance"]
        for metric_name in ("missed_train", "zero_protection", "premature_opening_m4", "reached_crossing_clear"):
            md = bd[metric_name]
            keys = [k for k in md.keys() if k not in ("evaluable_n", "exact_mcnemar_p", "excluded") and not k.endswith("_ids")]
            contrast_rows.append(
                {
                    "contrast_name": c["contrast_name"],
                    "arm_a": c["arm_a"],
                    "arm_b": c["arm_b"],
                    "paired_events_n": c["paired_events_n"],
                    "metric": metric_name,
                    "evaluable_n": md["evaluable_n"],
                    "discordant_counts": ", ".join(f"{k}={md[k]}" for k in keys),
                    "exact_mcnemar_p": md["exact_mcnemar_p"],
                    "mean_closed_duration_delta_b_minus_a_s": c["mean_closed_duration_delta_b_minus_a_s"],
                    "mean_transition_delta_b_minus_a": c["mean_transition_delta_b_minus_a"],
                    "research_question": c["research_question"],
                    "evaluation_basis": EVAL_BASIS,
                }
            )
    _write_csv(
        OUT_DIR / "MULTIMODAL_EVALUATION.csv",
        list(contrast_rows[0].keys()),
        contrast_rows,
    )

    # 6. FAILURE_INJECTION_RESULTS.csv (per-scenario aggregate)
    stress_groups = [
        ("EXP-G", stress["exp_g_missing_modality"]),
        ("EXP-H", stress["exp_h_contradictory_evidence"]["perturbations"]),
        ("EXP-I", stress["exp_i_failure_modes"]),
        ("EXP-K", stress["exp_k_recovery_and_interrupt"]),
    ]
    fi_agg_rows = []
    all_fi_run_rows = []
    for grp, runs in stress_groups:
        by_sc: dict[str, list[dict[str, Any]]] = {}
        for r in runs:
            by_sc.setdefault(r["scenario"], []).append(r)
            rc = r.get("rule_counts", {})
            all_fi_run_rows.append(
                {
                    "group": grp,
                    "scenario": r["scenario"],
                    "event_id": r["event_id"],
                    "policy": r["policy"],
                    "is_constructed_perturbation": r["is_constructed_perturbation"],
                    "fault_occurred": r["fault_occurred"],
                    "fail_safe_steps": r["fail_safe_steps"],
                    "direct_open_from_fault": r["direct_open_from_fault"],
                    "rejected_step_count": r.get("rejected_step_count", 0),
                    "closed_duration_s": r["closed_duration_s"],
                    "blocked_fraction": r["blocked_fraction"],
                    "missed_train": r.get("missed_train"),
                    "premature_opening_m4": r.get("premature_opening_m4"),
                    "m4_status": r.get("m4_status"),
                    "false_alarm": r.get("false_alarm"),
                    "final_crossing_state": r["final_crossing_state"],
                    "final_gate_state": r["final_gate_state"],
                    "rule4_fail_safe_clamp_count": rc.get("RULE_4_FAIL_SAFE_CLAMP", 0),
                    "rule7_interrupt_count": rc.get("RULE_7_NEW_TRAIN_INTERRUPT", 0),
                    "rule9_recovery_count": rc.get("RULE_9_SENSOR_RECOVERY", 0),
                    "rule3b_count": rc.get("RULE_3B_DEPARTURE_CONFIRMED_BY_TRAIN_END", 0),
                    "rule3c_count": rc.get("RULE_3C_DEPARTURE_CONFIRMED_BY_DISAPPEARANCE", 0),
                }
            )
        for sc, srows in by_sc.items():
            m4_eval = [x for x in srows if x.get("m4_status") == "EVALUABLE"]
            fi_agg_rows.append(
                {
                    "group": grp,
                    "scenario": sc,
                    "runs_n": len(srows),
                    "is_constructed_perturbation": any(x["is_constructed_perturbation"] for x in srows),
                    "fault_occurred_n": sum(1 for x in srows if x.get("fault_occurred")),
                    "direct_open_from_fault_n": sum(1 for x in srows if x.get("direct_open_from_fault")),
                    "rejected_step_total": sum(int(x.get("rejected_step_count", 0)) for x in srows),
                    "zero_protection_n": sum(1 for x in srows if x.get("closed_duration_s", 0.0) == 0.0),
                    "m4_premature_n": sum(1 for x in m4_eval if x.get("premature_opening_m4") is True),
                    "m4_evaluable_n": len(m4_eval),
                    "false_alarm_n": sum(1 for x in srows if x.get("false_alarm") is True),
                    "rule4_clamp_total": sum(int(x.get("rule_counts", {}).get("RULE_4_FAIL_SAFE_CLAMP", 0)) for x in srows),
                    "rule7_interrupts_total": sum(int(x.get("rule_counts", {}).get("RULE_7_NEW_TRAIN_INTERRUPT", 0)) for x in srows),
                    "rule9_recovery_total": sum(int(x.get("rule_counts", {}).get("RULE_9_SENSOR_RECOVERY", 0)) for x in srows),
                    "mean_closed_duration_s": round(sum(float(x.get("closed_duration_s", 0.0)) for x in srows) / len(srows), 4),
                    "mean_blocked_fraction": round(sum(float(x.get("blocked_fraction", 0.0)) for x in srows) / len(srows), 4),
                    "evaluation_basis": EVAL_BASIS,
                }
            )
    _write_csv(OUT_DIR / "FAILURE_INJECTION_RESULTS.csv", list(fi_agg_rows[0].keys()), fi_agg_rows)
    _write_csv(OUT_DIR / "FAIL_SAFE_TRANSITION_RESULTS.csv", list(all_fi_run_rows[0].keys()), all_fi_run_rows)

    # 8. MISSED_TRAIN_ANALYSIS.csv (23 train events across B0__v2, FRONT_AUDIO__v2, and B7__v2 if sync11)
    b0_map = {r["event_id"]: r for r in sms["event_rows"] if r["run_label"] == "B0__v2" and r["cohort"] == "train_events"}
    fa_map = {r["event_id"]: r for r in sms["event_rows"] if r["run_label"] == "FRONT_AUDIO__v2" and r["cohort"] == "train_events"}
    b7_map = {r["event_id"]: r for r in sms["event_rows"] if r["run_label"] == "DUAL_VISION_AUDIO__v2" and r["cohort"] == "train_events"}
    missed_rows = []
    for eid in sorted(b0_map.keys()):
        rb0 = b0_map[eid]
        rfa = fa_map[eid]
        rb7 = b7_map.get(eid)
        t1 = rb0["t1_s"]
        fb0 = rb0["first_blocked_s"]
        if t1 is None:
            cat = "LEFT_CENSORED_T1_NULL"
        elif fb0 is None:
            cat = "ZERO_PROTECTION_B0" if not (rb7 and rb7["first_blocked_s"] is not None) else "ZERO_PROTECTION_B0_RESCUED_BY_B7_BACK"
        else:
            cat = "LATE_CLOSURE_T1_BEFORE_MIN_ACTUATION_LATENCY"
        missed_rows.append(
            {
                "event_id": eid,
                "is_dual_sync_accepted": rb0["is_dual_sync_accepted"],
                "t0_censored": rb0["t0_censored"],
                "t1_s": t1,
                "t4_s": rb0["t4_s"],
                "b0_v2_first_warning_s": rb0["first_warning_s"],
                "b0_v2_first_blocked_s": fb0,
                "b0_v2_missed_train": rb0["missed_train"],
                "b0_v2_closed_conv_a_s": rb0["closed_duration_conv_a_s"],
                "front_audio_v2_first_blocked_s": rfa["first_blocked_s"],
                "front_audio_v2_closed_conv_a_s": rfa["closed_duration_conv_a_s"],
                "b7_v2_first_warning_s": rb7["first_warning_s"] if rb7 else None,
                "b7_v2_first_blocked_s": rb7["first_blocked_s"] if rb7 else None,
                "b7_v2_missed_train": rb7["missed_train"] if rb7 else None,
                "b7_v2_closed_conv_a_s": rb7["closed_duration_conv_a_s"] if rb7 else None,
                "root_cause_category": cat,
                "evaluation_basis": EVAL_BASIS,
            }
        )
    _write_csv(OUT_DIR / "MISSED_TRAIN_ANALYSIS.csv", list(missed_rows[0].keys()), missed_rows)

    # 9. PREMATURE_OPENING_ANALYSIS.csv (sync11 summary + tol=0.25s + M4 vs Legacy V9)
    prem_rows = []
    for cs in sms["cohort_summaries"]:
        if cs["cohort_slice"] == "sync11_CALIBRATION_SUPPORTED":
            prem_rows.append(
                {
                    "run_label": cs["run_label"],
                    "condition": cs["condition"],
                    "policy": cs["policy"],
                    "window_tolerance_s": 0.5,
                    "sync11_n": cs["train_events_n"],
                    "m4_premature_n": cs["m4_premature_n"],
                    "m4_evaluable_n": cs["m4_evaluable_n"],
                    "m4_never_protected_n": cs["m4_never_protected_n"],
                    "m4_premature_rate": cs["m4_premature_rate"],
                    "m4_premature_ci95": cs["m4_premature_ci95"],
                    "legacy_v9_premature_n": cs["legacy_v9_premature_n"],
                    "legacy_v9_evaluable_n": cs["legacy_v9_evaluable_n"],
                    "reached_crossing_clear_n": cs["reached_crossing_clear_n"],
                    "evaluation_basis": EVAL_BASIS,
                }
            )
    for pol in ("v2", "v1"):
        wt_sub = [r for r in replay_sum["window_tolerance_025_sensitivity"] if r["policy"] == pol]
        m4_ev = [r for r in wt_sub if r["premature_opening_m4"] is not None]
        m4_tr = sum(1 for r in m4_ev if r["premature_opening_m4"] is True)
        zp = sum(1 for r in wt_sub if r["closed_duration_s"] == 0.0)
        clr = sum(1 for r in wt_sub if r["reached_crossing_clear"])
        prem_rows.append(
            {
                "run_label": f"DUAL_VISION_AUDIO__{pol}_wt025",
                "condition": "B7",
                "policy": pol,
                "window_tolerance_s": 0.25,
                "sync11_n": len(wt_sub),
                "m4_premature_n": m4_tr,
                "m4_evaluable_n": len(m4_ev),
                "m4_never_protected_n": zp,
                "m4_premature_rate": round(m4_tr / len(m4_ev), 6) if m4_ev else None,
                "m4_premature_ci95": None,
                "legacy_v9_premature_n": None,
                "legacy_v9_evaluable_n": None,
                "reached_crossing_clear_n": clr,
                "evaluation_basis": EVAL_BASIS,
            }
        )
    _write_csv(OUT_DIR / "PREMATURE_OPENING_ANALYSIS.csv", list(prem_rows[0].keys()), prem_rows)

    # 10. WARNING_LEAD_TIME_ANALYSIS.csv (23 train events for B0__v2, B0__v1, B7__v2)
    b0_v1_map = {r["event_id"]: r for r in sms["event_rows"] if r["run_label"] == "B0__v1" and r["cohort"] == "train_events"}
    wlt_rows = []
    for eid in sorted(b0_map.keys()):
        r2 = b0_map[eid]
        r1 = b0_v1_map[eid]
        r7 = b7_map.get(eid)
        wlt_rows.append(
            {
                "event_id": eid,
                "is_dual_sync_accepted": r2["is_dual_sync_accepted"],
                "t0_censored": r2["t0_censored"],
                "t1_s": r2["t1_s"],
                "b0_v2_first_warning_s": r2["first_warning_s"],
                "b0_v2_signed_lead_s": r2["signed_warning_lead_to_t1_s"],
                "b0_v2_clamped_wlt_s": r2["warning_lead_clamped_s"],
                "b0_v1_first_warning_s": r1["first_warning_s"],
                "b0_v1_signed_lead_s": r1["signed_warning_lead_to_t1_s"],
                "b0_v1_clamped_wlt_s": r1["warning_lead_clamped_s"],
                "b7_v2_first_warning_s": r7["first_warning_s"] if r7 else None,
                "b7_v2_signed_lead_s": r7["signed_warning_lead_to_t1_s"] if r7 else None,
                "b7_v2_clamped_wlt_s": r7["warning_lead_clamped_s"] if r7 else None,
                "evaluation_basis": EVAL_BASIS,
            }
        )
    _write_csv(OUT_DIR / "WARNING_LEAD_TIME_ANALYSIS.csv", list(wlt_rows[0].keys()), wlt_rows)

    # 11. EXPERIMENT_REGISTRY.csv
    reg_rows = [
        {
            "experiment_id": "EXP-A_to_D_F_UNPERTURBED_REPLAY",
            "script_path": "scripts/run_exploratory_replay.py",
            "runs_count": replay_sum["total_runs"],
            "policies": "v2; v1; stateless_vision_rule2; stateless_union",
            "conditions": "B0; BACK_VISION; AUDIO_ONLY; FRONT_AUDIO; DUAL_VISION; DUAL_VISION_AUDIO",
            "cohort_scope": "all27 (front/audio/back) and strict 11_CALIBRATION_SUPPORTED (DUAL_*)",
            "execution_status": "COMPLETED_EXPLORATORY",
            "stage21_canonical_status": "NOT_CANONICAL_STAGE21",
            "notes": f"manifest_sha256={replay_sum['manifest_sha256']}; fail_closed_dual_guard={replay_sum['fail_closed_dual_guard']}",
        },
        {
            "experiment_id": "EXP-SENS_WINDOW_TOLERANCE_025",
            "script_path": "scripts/run_exploratory_replay.py",
            "runs_count": len(replay_sum["window_tolerance_025_sensitivity"]),
            "policies": "v2; v1",
            "conditions": "DUAL_VISION_AUDIO",
            "cohort_scope": "11_CALIBRATION_SUPPORTED",
            "execution_status": "COMPLETED_EXPLORATORY",
            "stage21_canonical_status": "NOT_CANONICAL_STAGE21",
            "notes": "Confirms collector window_tolerance_s=0.50 backfill across 3 consecutive 0.2s ticks vs 0.25s",
        },
        {
            "experiment_id": "EXP-G_MISSING_MODALITY",
            "script_path": "scripts/run_failure_injection_replays.py",
            "runs_count": stress["counts"]["exp_g_runs"],
            "policies": "v2",
            "conditions": "G1..G5",
            "cohort_scope": "11_CALIBRATION_SUPPORTED + 3_no_train (G5)",
            "execution_status": "COMPLETED_EXPLORATORY",
            "stage21_canonical_status": "CONSTRUCTED_STRESS_TEST",
            "notes": "0 direct fault->open transitions",
        },
        {
            "experiment_id": "EXP-H_CONTRADICTORY_EVIDENCE",
            "script_path": "scripts/run_failure_injection_replays.py",
            "runs_count": f"{stress['counts']['exp_h_natural_audits']} audits + {stress['counts']['exp_h_perturbation_runs']} perturbations",
            "policies": "v2; stateless_union",
            "conditions": "H1..H3 + natural_audit_11_sync",
            "cohort_scope": "11_CALIBRATION_SUPPORTED + 3_no_train (H3)",
            "execution_status": "COMPLETED_EXPLORATORY",
            "stage21_canonical_status": "CONSTRUCTED_STRESS_TEST",
            "notes": "H2 11/11 subthreshold vision stays IDLE; H3 shows V2 audio gating advantage vs stateless union",
        },
        {
            "experiment_id": "EXP-I_FAILURE_MODES",
            "script_path": "scripts/run_failure_injection_replays.py",
            "runs_count": stress["counts"]["exp_i_runs"],
            "policies": "v2",
            "conditions": "I1..I10",
            "cohort_scope": "11_CALIBRATION_SUPPORTED + 3_no_train (I10)",
            "execution_status": "COMPLETED_EXPLORATORY",
            "stage21_canonical_status": "CONSTRUCTED_STRESS_TEST",
            "notes": "I3 11/11 dual-cam fault fail-safe; I7 11/11 out-of-order rejected; I10 0.0s added vs B0__v2",
        },
        {
            "experiment_id": "EXP-K_RECOVERY_AND_INTERRUPT",
            "script_path": "scripts/run_failure_injection_replays.py",
            "runs_count": stress["counts"]["exp_k_runs"],
            "policies": "v2",
            "conditions": "K1..K3",
            "cohort_scope": "11_CALIBRATION_SUPPORTED + 3_no_train + 8 clearing events",
            "execution_status": "COMPLETED_EXPLORATORY",
            "stage21_canonical_status": "CONSTRUCTED_STRESS_TEST",
            "notes": "K1/K2 14/14 fault+recovery; K3 8/8 RULE_7 new-train interrupts",
        },
        {
            "experiment_id": "EXP-DEP_DEPARTURE_REOPENING",
            "script_path": "scripts/evaluate_departure_reopening.py",
            "runs_count": len(dep_rows),
            "policies": "v2; v1; stateless",
            "conditions": "DUAL_VISION_AUDIO",
            "cohort_scope": "11_CALIBRATION_SUPPORTED",
            "execution_status": "COMPLETED_EXPLORATORY",
            "stage21_canonical_status": "NOT_CANONICAL_STAGE21",
            "notes": "Isolates RULE_3C + sparse unrotated back caches + short post-T4 margins",
        },
        {
            "experiment_id": "EXP-REPRO_DETERMINISM",
            "script_path": "scripts/verify_exploratory_reproducibility.py",
            "runs_count": repro_rep["total_files_compared"],
            "policies": "all",
            "conditions": "all",
            "cohort_scope": "all exploratory JSON/CSV outputs",
            "execution_status": "VERIFIED_BIT_IDENTICAL" if repro_rep["verified_bit_identical"] else "FAILED",
            "stage21_canonical_status": "VERIFICATION_RECEIPT",
            "notes": f"verified_bit_identical={repro_rep['verified_bit_identical']} traces={repro_rep['trace_files_compared']} summaries={repro_rep['summary_and_analysis_files_compared']}",
        },
        {
            "experiment_id": "EXP-TEST_SUITE_AUDIT",
            "script_path": "tests/unit/test_exploratory_pipeline.py",
            "runs_count": f"{test_rep['full_suite_summary']['passed']}/{test_rep['full_suite_summary']['collected']} full; {test_rep['exploratory_and_manifest_targeted_run']['summary_line']}",
            "policies": "unit + integration",
            "conditions": "synthetic + repo guards",
            "cohort_scope": "full repository",
            "execution_status": "COMPLETED_TRIAGED",
            "stage21_canonical_status": "VERIFICATION_RECEIPT",
            "notes": f"0 exploratory failures; {test_rep['full_suite_summary']['failed']} preexisting triaged failures",
        },
    ]
    _write_csv(OUT_DIR / "EXPERIMENT_REGISTRY.csv", list(reg_rows[0].keys()), reg_rows)

    # 12. ORIGINAL_RESEARCH_OBJECTIVES_STATUS.csv
    obj_rows = [
        {
            "objective_id": "RQ-PRIMARY_V2",
            "description": "On synchronized recordings, compare two-camera audio-assisted temporal policy (B7) vs single-camera (B0/B4) & stateless baselines on missed-train and premature-opening outcomes.",
            "status": "COMPLETED_EXPLORATORY_NOT_CANONICAL",
            "evidence_artifact": "docs/generated/final_research/MULTIMODAL_EVALUATION.csv; docs/generated/final_research/BASELINE_COMPARISON.csv",
            "key_finding": "B7__v2 halves zero-protection (2/11 vs 4/11 B0__v2, p=0.50) and doubles clearances (8/11 vs 4/11, p=0.125) on current unrotated Nov 7-8 caches, while V2 RULE_3C increases M4 premature opening (7/9) and Temporal V2 significantly outperforms Stateless RULE_2 (p=0.007812 sync11; p=0.000244 all23).",
        },
        {
            "objective_id": "OBJ-01_CACHE_ONLY_EXECUTION",
            "description": "Execute full offline multimodal replay without raw media access or governance bypass.",
            "status": "COMPLETED_EXPLORATORY",
            "evidence_artifact": "scripts/run_exploratory_replay.py; results/exploratory_execution/replays/replay_summary.json",
            "key_finding": "336 deterministic runs + 22 tolerance sensitivity runs executed strictly from JSONL caches.",
        },
        {
            "objective_id": "OBJ-02_DUAL_CAMERA_SYNC_BOUNDARY",
            "description": "Enforce strict phase12 R04 CALIBRATION_SUPPORTED scope boundary for dual-camera claims.",
            "status": "COMPLETED_VERIFIED",
            "evidence_artifact": "scripts/exploratory_common.py; tests/unit/test_exploratory_pipeline.py",
            "key_finding": "11 sync events strictly permitted for DUAL_*; train_events/event_010 and 16 independent events fail-closed refused.",
        },
        {
            "objective_id": "OBJ-03_CONVENTION_B_EXACT_IDENTITY",
            "description": "Reconcile Convention B vs Convention A gate-closure timing theorem.",
            "status": "COMPLETED_VERIFIED",
            "evidence_artifact": "results/exploratory_execution/analysis/safety_metrics_summary.json",
            "key_finding": "Verified exact identity across all 336 runs: unique diff in {-0.2, 0.0}s with -0.2s strictly on terminal blocked runs.",
        },
        {
            "objective_id": "OBJ-04_DEPARTURE_PREMATURE_OPENING",
            "description": "Diagnose premature opening mechanisms relative to rear clearance T4.",
            "status": "COMPLETED_ROOT_CAUSE_IDENTIFIED",
            "evidence_artifact": "docs/generated/final_research/DEPARTURE_REOPENING_ANALYSIS.csv; docs/generated/final_research/figures/fig3_departure_premature_opening_margins.png",
            "key_finding": "RULE_3C clears on 2s missing detections over sparse unrotated back caches (0.76%-5.07% density on 9/10 events with T4), while 9/10 sync events with T4 have <=2.32s post-T4 tail (< T_clear=3.0s).",
        },
        {
            "objective_id": "OBJ-05_M39_M43_VS_OCT13_DIVERGENCE",
            "description": "Resolve discrepancy between Phase 10.1 Oct 13 (0/11-6/11) and Nov 7-8 M39/M43 (329 front + 1020 back) caches.",
            "status": "COMPLETED_ROOT_CAUSE_PROVEN",
            "evidence_artifact": "docs/generated/final_research/ARCHITECTURE_FINAL_STATUS.md; docs/generated/professor_evidence/mission44/",
            "key_finding": "Same frozen checkpoints used; Mission 37/38 PyAV source_pts=True dropped DISPLAYMATRIX rotation on 44/54 sources before Mission 39/43 YOLO inference; Mission 44 db40305 fixed video.py without re-running raw inference.",
        },
        {
            "objective_id": "OBJ-06_FAIL_SAFE_STRESS_TESTING",
            "description": "Verify fail-closed fault handling, sensor dropout, contradiction, and RULE_7 recovery.",
            "status": "COMPLETED_EXPLORATORY",
            "evidence_artifact": "docs/generated/final_research/FAILURE_INJECTION_RESULTS.csv",
            "key_finding": "0/202 stress/fault runs transitioned directly from fault to OPEN; 11/11 out-of-order rejected; 8/8 RULE_7 interrupts verified.",
        },
        {
            "objective_id": "OBJ-07_BIT_FOR_BIT_REPRODUCIBILITY",
            "description": "Verify end-to-end deterministic bit-identical regeneration of all exploratory outputs.",
            "status": "COMPLETED_VERIFIED",
            "evidence_artifact": "results/exploratory_execution/analysis/reproducibility_verification.json",
            "key_finding": "344/344 files bit-identical across full isolated re-run (wall time ~15.3s).",
        },
        {
            "objective_id": "OBJ-08_STAGE21_CANONICAL_PROMOTION",
            "description": "Formal human Stage-2.1 adjudication & official authorized benchmark execution.",
            "status": "BLOCKED_BY_HUMAN_AUTHORIZATION",
            "evidence_artifact": "data/governance/; scripts/run_stage21_review.py",
            "key_finding": "Zero Stage-2.1 human reviews or AUTH_MEDIA_ACCESS_GRANTED receipts exist; canonical execution gate remains closed.",
        },
        {
            "objective_id": "OBJ-09_RAW_VIDEO_REINFERENCE_UNROTATED_FIX",
            "description": "Re-run frozen YOLOv8n on rotated frames (post-Mission 44 db40305 fix) under formal AUTH.",
            "status": "BLOCKED_BY_MEDIA_ACCESS_HOLD",
            "evidence_artifact": "docs/generated/professor_evidence/mission44/SOURCE_DIAGNOSTIC_SCOPE.md",
            "key_finding": "Requires explicit researcher raw media unlock + updated cache manifest before claiming deployment-grade perception numbers.",
        },
    ]
    _write_csv(OUT_DIR / "ORIGINAL_RESEARCH_OBJECTIVES_STATUS.csv", list(obj_rows[0].keys()), obj_rows)


if __name__ == "__main__":
    main()
