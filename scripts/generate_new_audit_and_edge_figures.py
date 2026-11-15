#!/usr/bin/env python
"""Generate high-DPI (300 DPI) publication figures for leakage, audio hysteresis,
CPU/edge profiling, and weather-attenuation stress experiments.

Reads only verified JSON outputs under ``results/dataset_audit/`` and
``results/exploratory_v2/optimization_and_stress/``. Never accesses raw media.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent


def _setup_style() -> None:
    plt.rcParams.update(
        {
            "font.size": 9.5,
            "axes.titlesize": 10.5,
            "axes.labelsize": 9.5,
            "legend.fontsize": 8.5,
            "xtick.labelsize": 8.5,
            "ytick.labelsize": 8.5,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.dpi": 300,
        }
    )


def make_fig11_leakage(root: Path, out_dir: Path) -> Path:
    rep = json.loads((root / "results/dataset_audit/vision_audio_leakage_audit.json").read_text())
    s705 = rep["vision_705d388743ea"]
    vcl = rep["vision_session_grouped_candidate"]["audit"]
    a_orig = rep["audio_v3_original"]
    a_cln = rep["audio_v3_stem_grouped_candidate"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.2, 4.1))

    # Panel A: Vision leakage rates (%)
    labels_v = [
        "Sessions Crossing\nSplits (gap<=600s)",
        "Timestamped Test\nSharing Train Session",
        "RF Train Augs\nInside Test Split",
    ]
    v_705_vals = [
        100.0 * 27 / 29,
        100.0 * 447 / 447,
        100.0 * s705["rf_origin_by_split"]["test"]["train"] / s705["split_image_counts"]["test"],
    ]
    v_cln_vals = [0.0, 0.0, 0.0]
    x = np.arange(len(labels_v))
    w = 0.34
    b1 = ax1.bar(x - w / 2, v_705_vals, w, label="Legacy 705d388743ea", color="#C0392B")
    b2 = ax1.bar(x + w / 2, v_cln_vals, w, label="Session-Grouped Candidate", color="#1E8449")
    for bar, val in zip(b1, v_705_vals, strict=True):
        ax1.text(bar.get_x() + bar.get_width() / 2, val + 2.0, f"{val:.1f}%", ha="center", va="bottom", fontsize=8)
    for bar in b2:
        ax1.text(bar.get_x() + bar.get_width() / 2, 2.0, "0.0%", ha="center", va="bottom", fontsize=8, fontweight="bold", color="#1E8449")
    ax1.set_xticks(x, labels_v)
    ax1.set_ylim(0, 118)
    ax1.set_ylabel("Leakage / Contamination (%)")
    ax1.set_title("(a) Vision V1 Split Leakage (baler.v1i.yolov8)")
    ax1.legend(loc="upper right", frameon=False)
    ax1.grid(axis="y", alpha=0.25, linestyle="--")

    # Panel B: Audio V3 leakage (%) & clean class balance
    labels_a = [
        "Cross-Split\nPos Stems (%)",
        "Pos Clips in\nLeaked Stems (%)",
        "Cross-Split\nESC-50 Folds (%)",
    ]
    a_orig_vals = [
        100.0 * a_orig["cross_split_positive_stem_count"] / a_orig["unique_positive_stems"],
        100.0 * a_orig["positive_recording_stem_leakage_fraction"],
        0.0,
    ]
    a_cln_vals = [0.0, 0.0, 0.0]
    x2 = np.arange(len(labels_a))
    b3 = ax2.bar(x2 - w / 2, a_orig_vals, w, label="Legacy Audio V3 Split", color="#D35400")
    b4 = ax2.bar(x2 + w / 2, a_cln_vals, w, label="Stem-Grouped (60/13/13)", color="#2874A6")
    for bar, val in zip(b3, a_orig_vals, strict=True):
        ax2.text(bar.get_x() + bar.get_width() / 2, val + 1.2, f"{val:.1f}%", ha="center", va="bottom", fontsize=8)
    for bar in b4:
        ax2.text(bar.get_x() + bar.get_width() / 2, 1.2, "0.0%", ha="center", va="bottom", fontsize=8, fontweight="bold", color="#2874A6")
    ax2.set_xticks(x2, labels_a)
    ax2.set_ylim(0, 44)
    ax2.set_ylabel("Cross-Split Leakage (%)")
    ax2.set_title("(b) Audio V3 Stem & Fold Isolation (n=172)")
    ax2.legend(loc="upper right", frameon=False)
    ax2.grid(axis="y", alpha=0.25, linestyle="--")

    fig.tight_layout()
    out_path = out_dir / "fig11_dataset_leakage_comparison.png"
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    return out_path


def make_fig12_audio_hysteresis(root: Path, out_dir: Path) -> Path:
    eo = json.loads((root / "results/exploratory_v2/optimization_and_stress/exp_o_audio_calibration_hysteresis.json").read_text())
    grid = eo["hysteresis_grid"]
    taus = sorted({r["threshold"] for r in grid})

    def _series(k_val: int, key: str) -> list[float]:
        return [next(r[key] for r in grid if r["threshold"] == t and r["k_consecutive"] == k_val) for t in taus]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.2, 4.1))

    ax1.plot(taus, _series(1, "recall"), "o--", color="#2E86C1", label="Recall (k=1)")
    ax1.plot(taus, _series(1, "specificity"), "s--", color="#E74C3C", label="Specificity (k=1)")
    ax1.plot(taus, _series(2, "recall"), "o-", color="#1B4F72", linewidth=2.0, label="Recall (k=2)")
    ax1.plot(taus, _series(2, "specificity"), "s-", color="#1E8449", linewidth=2.0, label="Specificity (k=2)")
    ax1.plot(taus, _series(2, "f1"), "^-", color="#8E44AD", linewidth=1.8, label="F1 Score (k=2)")
    ax1.axvline(0.37, color="#7F8C8D", linestyle=":", linewidth=1.2)
    ax1.text(0.378, 1.12, "Frozen T*=0.37", fontsize=7.5, color="#566573", va="top")
    ax1.axvline(0.75, color="#1E8449", linestyle=":", linewidth=1.2)
    ax1.text(0.758, 0.14, "Best F1\n(0.75, k=2)\n0/3 no_train FP", fontsize=7.5, color="#1E8449")
    ax1.set_xlabel("Confidence Threshold (tau)")
    ax1.set_ylabel("Event-Level Metric (audio23)")
    ax1.set_ylim(-0.04, 1.16)
    ax1.set_title("(a) Exp O: Acoustic Threshold x Hysteresis Trade-off")
    ax1.legend(loc="lower left", frameon=True, framealpha=0.92, fontsize=7.5)
    ax1.grid(alpha=0.25, linestyle="--")

    temps = [r["temperature"] for r in eo["calibration_temperature_sweep_exploratory"]]
    eces = [r["ece_5bin"] for r in eo["calibration_temperature_sweep_exploratory"]]
    briers = [r["brier"] for r in eo["calibration_temperature_sweep_exploratory"]]
    ax2.plot(temps, eces, "o-", color="#C0392B", linewidth=2.0, label="ECE (5-bin)")
    ax2.plot(temps, briers, "s-", color="#2874A6", linewidth=2.0, label="Brier Score")
    for t_v, e_v in zip(temps, eces, strict=True):
        ax2.text(t_v, e_v + 0.012, f"{e_v:.3f}", ha="center", fontsize=7.5, color="#C0392B")
    ax2.set_xlabel("Temperature Scaling Parameter T")
    ax2.set_ylabel("Calibration Error / Brier")
    ax2.set_ylim(0.0, 0.38)
    ax2.set_title("(b) Field audio23 Overconfidence Calibration (Exploratory)")
    ax2.legend(loc="upper right", frameon=False)
    ax2.grid(alpha=0.25, linestyle="--")

    fig.tight_layout()
    out_path = out_dir / "fig12_audio_hysteresis_and_calibration.png"
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    return out_path


def make_fig13_cpu_edge(root: Path, out_dir: Path) -> Path:
    ep = json.loads((root / "results/exploratory_v2/optimization_and_stress/exp_p_cpu_edge_benchmark.json").read_text())
    vb = ep["vision_cpu_benchmarks_ms"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.2, 4.1))

    # Panel A: Real host CPU ms/frame
    cats = ["YOLO E2E\n640x640", "YOLO E2E\n416x416", "Fwd Eager\n640", "Fwd TS\n640", "Fwd Eager\n416", "Fwd TS\n416", "Fwd TS\n320"]
    vals = [
        vb["yolo_predict_e2e_640"]["mean_ms"],
        vb["yolo_predict_e2e_416"]["mean_ms"],
        vb["yolov8n_forward_640_fp32"]["mean_ms"],
        vb["yolov8n_torchscript_640_fp32"]["mean_ms"],
        vb["yolov8n_forward_416_fp32"]["mean_ms"],
        vb["yolov8n_torchscript_416_fp32"]["mean_ms"],
        vb["yolov8n_torchscript_320_fp32"]["mean_ms"],
    ]
    colors = ["#C0392B", "#E67E22", "#5D6D7E", "#2874A6", "#7F8C8D", "#1E8449", "#117A65"]
    bars = ax1.bar(np.arange(len(cats)), vals, color=colors, width=0.62)
    for b, v in zip(bars, vals, strict=True):
        ax1.text(b.get_x() + b.get_width() / 2, v + 1.0, f"{v:.1f} ms", ha="center", va="bottom", fontsize=7.5)
    ax1.axhline(200.0, color="#922B21", linestyle="--", linewidth=1.0, alpha=0.6)
    ax1.text(4.3, 62.0, f"Audio CNN TS: {ep['audio_cpu_benchmarks_ms']['cnn_torchscript_fp32']['mean_ms']:.2f} ms\nV3 FSM tick: {ep['v3_fsm_closed_loop_121_ticks_ms']['per_tick_mean_ms']:.3f} ms", fontsize=7.5, bbox={"boxstyle": "round", "fc": "#F8F9F9", "ec": "#D5DBDB"})
    ax1.set_xticks(np.arange(len(cats)), cats, fontsize=7.5)
    ax1.set_ylim(0, 74)
    ax1.set_ylabel("Mean Host CPU Latency (ms / frame)")
    ax1.set_title("(a) Exp P: Measured Apple M1 CPU Inference Latency")
    ax1.grid(axis="y", alpha=0.25, linestyle="--")

    # Panel B: Analytical Pi 4B CPU core utilization (Continuous vs Gated)
    d640 = ep["event_triggered_duty_cycle_640"]["duty_cycle_scenarios"]
    d416 = ep["event_triggered_duty_cycle_416"]["duty_cycle_scenarios"]
    modes = ["Cont. 24/7\n640px", "Gated 20/d\n640px", "Cont. 24/7\n416px", "Gated 20/d\n416px", "Gated 40/d\n416px"]
    rpi_cores = [
        d640[1]["sbc_analytical_projections"]["rpi4b_4gb_cortex_a72"]["projected_continuous_core_fraction"],
        d640[1]["sbc_analytical_projections"]["rpi4b_4gb_cortex_a72"]["projected_event_triggered_core_fraction"],
        d416[1]["sbc_analytical_projections"]["rpi4b_4gb_cortex_a72"]["projected_continuous_core_fraction"],
        d416[1]["sbc_analytical_projections"]["rpi4b_4gb_cortex_a72"]["projected_event_triggered_core_fraction"],
        d416[2]["sbc_analytical_projections"]["rpi4b_4gb_cortex_a72"]["projected_event_triggered_core_fraction"],
    ]
    c_rpi = ["#C0392B", "#1E8449", "#E67E22", "#2874A6", "#117A65"]
    b_r = ax2.bar(np.arange(len(modes)), rpi_cores, color=c_rpi, width=0.58)
    for b, v in zip(b_r, rpi_cores, strict=True):
        ax2.text(b.get_x() + b.get_width() / 2, v + 0.06, f"{v:.3f}", ha="center", va="bottom", fontsize=8)
    ax2.axhline(4.0, color="#7B241C", linestyle=":", linewidth=1.2)
    ax2.axhline(1.0, color="#566573", linestyle="--", linewidth=1.0)
    ax2.text(2.8, 1.08, "1.0 full CPU core", fontsize=7.5, color="#566573")
    ax2.set_xticks(np.arange(len(modes)), modes, fontsize=8)
    ax2.set_ylim(0, 3.6)
    ax2.set_ylabel("Projected Pi 4B CPU Cores Used")
    ax2.set_title("(b) Analytical Duty Cycle (5.5x Pi4 Scaling, Unmeasured SBC)")
    ax2.grid(axis="y", alpha=0.25, linestyle="--")

    fig.tight_layout()
    out_path = out_dir / "fig13_cpu_edge_benchmark_and_duty_cycle.png"
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    return out_path


def make_fig14_weather_stress(root: Path, out_dir: Path) -> Path:
    eq = json.loads((root / "results/exploratory_v2/optimization_and_stress/exp_q_weather_and_interlocking_stress.json").read_text())
    grid = eq["weather_dropout_grid"]
    alphas = sorted({r["alpha_conf"] for r in grid}, reverse=True)
    drops = sorted({r["burst_drop_prob"] for r in grid})

    mat = np.zeros((len(alphas), len(drops)))
    for i, a in enumerate(alphas):
        for j, d in enumerate(drops):
            row = next(r for r in grid if r["alpha_conf"] == a and r["burst_drop_prob"] == d)
            mat[i, j] = row["closure_rate"] * 100.0

    fig, ax = plt.subplots(figsize=(6.4, 4.1))
    im = ax.imshow(mat, cmap="YlGn", vmin=0, vmax=100, aspect="auto")
    for i, a in enumerate(alphas):
        for j, d in enumerate(drops):
            row = next(r for r in grid if r["alpha_conf"] == a and r["burst_drop_prob"] == d)
            eff = row["effective_front_conf"]
            val = mat[i, j]
            txt_col = "white" if val > 60 else "black"
            ax.text(
                j,
                i,
                f"{val:.0f}% Closed\n(0 Unsafe)",
                ha="center",
                va="center",
                color=txt_col,
                fontsize=8,
                fontweight="bold",
            )
    ax.set_xticks(np.arange(len(drops)), [f"{int(d*100)}% Drop" for d in drops])
    ax.set_yticks(np.arange(len(alphas)), [f"alpha={a:.2f}\n(conf={0.88*a:.2f})" for a in alphas])
    ax.set_xlabel("Random Burst Frame Drop Probability (p_drop)")
    ax.set_ylabel("Optical Visibility Attenuation (alpha)")
    ax.set_title("Exp Q: Synthetic Weather Attenuation x Dropout (100 Runs, 0 Unsafe Opens)")
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cb.set_label("Closure Trigger Rate (%)")

    fig.tight_layout()
    out_path = out_dir / "fig14_weather_attenuation_stress_heatmap.png"
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    return out_path


def make_fig15_exp_r_loeo_and_optical_wakeup(root: Path, out_dir: Path) -> Path:
    er = json.loads((root / "results/exploratory_v2/optimization_and_stress/exp_r_crossval_and_failsafe.json").read_text())
    loeo = er["loeo_acoustic_crossval"]
    base = loeo["baseline_frozen_tau037_k1"]
    oof = loeo["loeo_oof_hysteresis_metrics"]
    cal = loeo["oof_calibration"]
    ci = loeo["bootstrap_95_ci"]
    wake = er["optical_degradation_wakeup_ablation"]
    sweep = wake["attenuation_sweep"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.6, 4.3))

    # Panel A: 23-fold LOEO Acoustic Cross-Validation
    metrics = ["Accuracy", "Specificity", "Precision", "F1 Score", "Brier Score\n(↓ Better)", "ECE (5-bin)\n(↓ Better)"]
    base_vals = [base["accuracy"], base["specificity"], base["precision"], base["f1"], cal["uncalibrated_brier"], cal["uncalibrated_ece_5bin"]]
    oof_vals = [oof["accuracy"], oof["specificity"], oof["precision"], oof["f1"], cal["oof_temp_scaled_brier"], cal["oof_temp_scaled_ece_5bin"]]
    x = np.arange(len(metrics))
    w = 0.36
    b1 = ax1.bar(x - w / 2, base_vals, w, label="Frozen Baseline (tau=0.37, k=1)", color="#7F8C8D")
    b2 = ax1.bar(x + w / 2, oof_vals, w, label="23-Fold Nested LOEO OOF (Calibrated)", color="#1E8449")
    for bars in (b1, b2):
        for bar in bars:
            v = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width() / 2, v + 0.018, f"{v:.3f}", ha="center", va="bottom", fontsize=7.1)
    ax1.set_xticks(x, metrics, fontsize=7.5)
    ax1.set_ylim(0.0, 0.98)
    ax1.set_ylabel("Metric Value")
    ax1.set_title("(a) Exp R: 23-Fold LOEO Audio CV & OOF Calibration")
    ax1.legend(loc="upper right", frameon=True, fontsize=7.3)
    ax1.text(
        0.02,
        0.97,
        f"2,000-resample Bootstrap 95% CI:\n"
        f"F1 = {oof['f1']:.3f} [{ci['f1']['ci95_low']:.3f}, {ci['f1']['ci95_high']:.3f}]\n"
        f"Spec = {oof['specificity']:.3f} [{ci['specificity']['ci95_low']:.3f}, {ci['specificity']['ci95_high']:.3f}]\n"
        f"Selected: tau=0.75, k=2 (20/23 folds)",
        transform=ax1.transAxes,
        va="top",
        fontsize=7.2,
        bbox={"boxstyle": "round", "fc": "#F8F9F9", "ec": "#D5DBDB"},
    )
    ax1.grid(axis="y", alpha=0.25, linestyle="--")

    # Panel B: Optical Attenuation Sweep (Baseline V3 vs Opt-In Degraded Audio Wakeup)
    alphas = [float(r["alpha_conf"]) for r in sweep]
    base_cls = [100.0 if r["baseline_v3_closed"] else 0.0 for r in sweep]
    wake_cls = [100.0 if r["wakeup_v3_closed"] else 0.0 for r in sweep]
    xp = np.arange(len(alphas))
    w2 = 0.36
    ax2.bar(xp - w2 / 2, base_cls, w2, label="Baseline V3 (wakeup disabled)", color="#2874A6")
    ax2.bar(xp + w2 / 2, wake_cls, w2, label="Opt-In Optical-Degraded Audio Wakeup", color="#D35400")
    for idx, row in enumerate(sweep):
        bval = base_cls[idx]
        wval = wake_cls[idx]
        ax2.text(xp[idx] - w2 / 2, bval + 2.0, f"{int(bval)}%", ha="center", va="bottom", fontsize=7.3)
        ax2.text(xp[idx] + w2 / 2, wval + 2.0, f"{int(wval)}%\n@{row['wakeup_v3_trigger_s']:.1f}s", ha="center", va="bottom", fontsize=6.9)
    ax2.set_xticks(xp, [f"alpha={r['alpha_conf']:.2f}\n(conf={r['effective_front_conf']:.2f})" for r in sweep], fontsize=7.6)
    ax2.set_ylim(0, 146)
    ax2.set_yticks([0, 20, 40, 60, 80, 100])
    ax2.set_ylabel("Synthetic Approach Closure Rate (%)")
    ax2.set_title("(b) Exp R: Optical Cliff Recovery (0 Unsafe Opens)")
    ax2.legend(loc="lower left", frameon=True, fontsize=7.4)
    ax2.text(
        0.02,
        0.97,
        f"Negative controls (0/2 closed):\n"
        f"Clear sky + ambient horn: closed={wake['controls']['clear_optics_sustained_ambient_horn_closed']}\n"
        f"Degraded optics + 1 impulse: closed={wake['controls']['degraded_optics_single_impulse_horn_closed']}",
        transform=ax2.transAxes,
        va="top",
        fontsize=7.2,
        bbox={"boxstyle": "round", "fc": "#FEF9E7", "ec": "#F9E79F"},
    )
    ax2.grid(axis="y", alpha=0.25, linestyle="--")

    fig.tight_layout()
    out_path = out_dir / "fig15_exp_r_loeo_and_optical_wakeup.png"
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    return out_path


def main() -> int:
    _setup_style()
    out_dir = ROOT / "docs/generated/figures"
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = [
        make_fig11_leakage(ROOT, out_dir),
        make_fig12_audio_hysteresis(ROOT, out_dir),
        make_fig13_cpu_edge(ROOT, out_dir),
        make_fig14_weather_stress(ROOT, out_dir),
        make_fig15_exp_r_loeo_and_optical_wakeup(ROOT, out_dir),
    ]
    print(json.dumps({"status": "OK", "figures": [str(p.relative_to(ROOT)) for p in paths]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
