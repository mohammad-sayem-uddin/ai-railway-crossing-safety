#!/usr/bin/env python3
"""Generate publication-quality 300-DPI figures for Mission 13 Model Generalization Audit.

Strictly uses measured logs, JSON artifacts, and checkpoints under ``results/model_generalization_audit/``
and ``experiments/``. Uses BytesIO PNG writing cleanly without raw media access.
"""

from __future__ import annotations

import hashlib
import io
import json
import sys
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

AUDIT_DIR = REPO_ROOT / "results" / "model_generalization_audit"
FIG_DIR = REPO_ROOT / "docs" / "generated" / "model_generalization_audit" / "figures"

V1_HIST = REPO_ROOT / "experiments" / "audio" / "RUN_20260923_AUDIO_001" / "metrics" / "training_history.json"
V2_HIST = REPO_ROOT / "experiments" / "audio" / "RUN_20261008_AUDIO_V2" / "metrics" / "training_history.json"
V3_METRICS = REPO_ROOT / "experiments" / "audio" / "RUN_20261008_AUDIO_V3_ESC50" / "metrics" / "metrics.json"


def _setup_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 8.6,
            "axes.titlesize": 9.8,
            "axes.titleweight": "bold",
            "axes.labelsize": 8.6,
            "legend.fontsize": 7.6,
            "xtick.labelsize": 7.8,
            "ytick.labelsize": 7.8,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.dpi": 300,
        }
    )


def _save_png(fig: plt.Figure, out_path: Path) -> tuple[int, str]:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    data = buf.getvalue()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(data)
    return len(data), hashlib.sha256(data).hexdigest()


def _roc_curve_pts(y: np.ndarray, p: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    order = np.argsort(-p, kind="mergesort")
    y_s = y[order]
    tp = np.cumsum(y_s == 1)
    fp = np.cumsum(y_s == 0)
    tpr = np.concatenate(([0.0], tp / max(int(np.sum(y == 1)), 1), [1.0]))
    fpr = np.concatenate(([0.0], fp / max(int(np.sum(y == 0)), 1), [1.0]))
    return fpr, tpr


def _pr_curve_pts(y: np.ndarray, p: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    order = np.argsort(-p, kind="mergesort")
    y_s = y[order]
    tp = np.cumsum(y_s == 1)
    fp = np.cumsum(y_s == 0)
    rec = np.concatenate(([0.0], tp / max(int(np.sum(y == 1)), 1)))
    prec = np.concatenate(([1.0], tp / np.maximum(tp + fp, 1e-12)))
    return rec, prec


def _eval_ckpt_raw(ckpt_path: Path, m3_rows: list[dict[str, Any]], sg_split: dict[str, Any]) -> dict[str, Any]:
    from run_mission13_audio_audit import eval_crossing_a, prepare_or_verify_crossing_audio_cache

    from railway_detection.audio.model import CompactTrainHornCNN

    ckpt = torch.load(ckpt_path, map_location="cpu", weights_only=False)
    model = CompactTrainHornCNN(in_channels=1, dropout=0.30)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()
    mu, sd = float(ckpt["norm_mean"]), float(ckpt["norm_std"])

    test_recs = set(sg_split["partitions"]["test"]["recordings"])
    te_rows = [r for r in m3_rows if r["sample_id"] in test_recs]
    X_te = np.stack([np.load(REPO_ROOT / r["feature_path"]) for r in te_rows], axis=0).astype(np.float32)
    y_te = np.array([int(r["class_id"]) for r in te_rows], dtype=np.int64)
    xn = (X_te - mu) / sd
    with torch.no_grad():
        probs_te = torch.sigmoid(model(torch.from_numpy(xn).float().unsqueeze(1))).numpy()

    cross = prepare_or_verify_crossing_audio_cache()
    cross_feats = (cross["feats"] - mu) / sd
    with torch.no_grad():
        cross_probs = torch.sigmoid(model(torch.from_numpy(cross_feats).float().unsqueeze(1))).numpy()
    by_eid = cross["by_event_idx"]
    ev_scores, ev_labels = [], []
    for row in cross["rows_27"]:
        if row["cohort"] == "engine_events":
            continue
        eid = row["event_id"]
        ev_scores.append(float(np.max(cross_probs[by_eid[eid]])))
        ev_labels.append(1 if (row["cohort"] == "train_events" and row["gt_horn_present"]) else 0)
    _ = eval_crossing_a
    return {
        "sg_test_y": y_te,
        "sg_test_p": probs_te,
        "cross_26_y": np.array(ev_labels, dtype=np.int64),
        "cross_26_p": np.array(ev_scores, dtype=np.float64),
        "thr": float(ckpt["operating_threshold"]),
    }


def generate_audio_figures() -> dict[str, tuple[int, str]]:
    """Generate the 3 multi-panel CompactTrainHornCNN generalization figures."""
    _setup_style()
    a_sum = json.loads((AUDIT_DIR / "audio_audit_summary.json").read_text(encoding="utf-8"))
    v3_m = json.loads(V3_METRICS.read_text(encoding="utf-8"))
    h3 = v3_m["training_history"]
    ep3 = np.arange(1, len(h3["train_loss"]) + 1)

    s_recipe = a_sum["stem_grouped_ablations"]["stem_grouped_v3_recipe"]["seed42_detail"]
    s_gn = a_sum["stem_grouped_ablations"]["stem_grouped_groupnorm_specaug"]["seed42_detail"]
    h_rec = s_recipe["history"]
    h_gn = s_gn["history"]

    saved: dict[str, tuple[int, str]] = {}

    # === Fig A1: Training/Validation Loss, LR Schedule, Clean Train-Val F1 & Historical Runs ===
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12.6, 8.8))

    ax1.plot(ep3, h3["train_loss"], label="Train Loss (V3 aug)", color="#0072B2", lw=2.0)
    ax1.plot(ep3, h3["val_loss"], label="Val Loss (59.3% leaked stems)", color="#D55E00", lw=1.8)
    ax1.axvline(v3_m["best_epoch"], color="#111827", ls="--", lw=1.1, label=f"Best Ep {v3_m['best_epoch']} (val_loss=0.0794)")
    ax1.annotate("Ep 13 Val Spike\n1.1642 (F1=0.297)", xy=(13, 1.1642), xytext=(15.0, 0.88),
                 arrowprops={"arrowstyle": "->", "color": "#B91C1C", "lw": 1.1}, fontsize=7.6, color="#991B1B", fontweight="bold")
    ax1.set_xlabel("Epoch")
    ax1.set_ylabel("BCE Loss")
    ax1.set_title("(a) Frozen Audio V3 (RUN_20261008_AUDIO_V3_ESC50): Loss Curves")
    ax1.legend(loc="upper right", frameon=True)
    ax1.grid(alpha=0.25, ls="--")

    ep_r = np.arange(1, len(h_rec["val_loss"]) + 1)
    ep_g = np.arange(1, len(h_gn["val_loss"]) + 1)
    ax2.plot(ep_r, h_rec["val_loss"], label="Stem-Grouped BatchNorm (spikes>0.20: 4.4+-2.3)", color="#C0392B", lw=1.6, alpha=0.88)
    ax2.plot(ep_g, h_gn["val_loss"], label="Stem-Grouped GroupNorm+SpecAug (spikes: 2.4)", color="#009E73", lw=1.9)
    ax2.set_ylim(0.25, 1.18)
    ax2_lr = ax2.twinx()
    ax2_lr.plot(ep_r, h_rec["lr"], label="Cosine LR", color="#64748B", ls=":", lw=1.3)
    ax2_lr.set_ylabel("Learning Rate", color="#64748B")
    ax2_lr.tick_params(axis="y", colors="#64748B")
    ax2_lr.spines["top"].set_visible(False)
    ax2.set_xlabel("Epoch")
    ax2.set_ylabel("Clean Validation Loss")
    ax2.set_title("(b) BatchNorm Validation Volatility vs GroupNorm & LR Schedule")
    ax2.legend(loc="upper right", frameon=True, fontsize=7.2)
    ax2.grid(alpha=0.25, ls="--")

    ax3.plot(ep_r, h_rec["train_f1_clean"], label="Un-aug Train F1 (Seed 42)", color="#0072B2", lw=2.0)
    ax3.plot(ep_r, h_rec["val_f1"], label="Clean Val F1 (Fold 4, 0% leak)", color="#E69F00", lw=1.9)
    ax3.axhline(s_recipe["test_cal"]["f1"], color="#009E73", ls="-.", lw=1.6, label=f"Seed 42 Locked Test F1 ({s_recipe['test_cal']['f1']:.4f})")
    ax3.axvline(s_recipe["best_epoch"], color="#111827", ls="--", lw=1.1, label=f"Best Ep {s_recipe['best_epoch']}")
    ax3.set_ylim(0.45, 1.03)
    ax3.set_xlabel("Epoch")
    ax3.set_ylabel("F1 Score (Clean Un-augmented)")
    ax3.set_title("(c) Leakage-Free Stem-Grouped Train vs Val vs Test Gap")
    ax3.legend(loc="lower right", frameon=True)
    ax3.grid(alpha=0.25, ls="--")

    # Panel (d): Evolution across V1, V2, V3 Leaked, Clean 5-Seed, External Crossing_A
    bars_lbl = ["V1 Baseline\n(old log)", "V2 Field Neg\n(domain leak)", "V3 Original\n(val/test split)", "Stem-Grouped\n5-Seed (clean)", "External\ncrossing_A (Rec26)"]
    val_scores = [0.8602, 0.9882, 0.9942, a_sum["stem_grouped_ablations"]["stem_grouped_v3_recipe"]["aggregate_5seeds"]["val_f1_cal"]["mean"], np.nan]
    test_scores = [0.6971, 1.0000, 0.8690, a_sum["stem_grouped_ablations"]["stem_grouped_v3_recipe"]["aggregate_5seeds"]["test_f1_cal"]["mean"], a_sum["frozen_v3_audit"]["crossing_a_external"]["recording_26_tau_metrics"]["f1"]]
    x = np.arange(len(bars_lbl))
    w = 0.34
    ax4.bar(x[:4] - w / 2, val_scores[:4], w, label="Validation F1 (Model Selection)", color="#94A3B8")
    ax4.bar(x + np.array([w / 2, w / 2, w / 2, w / 2, 0.0]), test_scores, w, label="Test / Field F1", color="#0072B2")
    for idx, v in enumerate(val_scores[:4]):
        ax4.text(x[idx] - w / 2, v + 0.015, f"{v:.3f}", ha="center", va="bottom", fontsize=7.0)
    for idx, v in enumerate(test_scores):
        xp = x[idx] + (w / 2 if idx < 4 else 0.0)
        ax4.text(xp, v + 0.015, f"{v:.3f}", ha="center", va="bottom", fontsize=7.0, fontweight="bold")
    ax4.set_xticks(x, bars_lbl, fontsize=7.5)
    ax4.set_ylim(0, 1.15)
    ax4.set_ylabel("F1 Score")
    ax4.set_title("(d) Val-to-Test Inflation Across V1 -> V2 -> V3 -> Clean -> Field")
    ax4.legend(loc="upper right", frameon=True)
    ax4.grid(axis="y", alpha=0.25, ls="--")

    fig.suptitle("CompactTrainHornCNN: Training History, Leakage Inflation & Volatility Diagnostics", fontsize=11.0, fontweight="bold")
    fig.tight_layout()
    p1 = FIG_DIR / "fig_m13_a1_training_and_instability.png"
    saved[str(p1.relative_to(REPO_ROOT))] = _save_png(fig, p1)

    # === Fig A2: ROC, PR Curves, Confusion Matrices, Calibration & Confidence Distribution ===
    m3_rows = json.loads((REPO_ROOT / "data/manifests/audio_training_dataset_v3.json").read_text(encoding="utf-8"))
    sg_split = json.loads((REPO_ROOT / "data/splits/audio_v3_stem_grouped/dataset_split.json").read_text(encoding="utf-8"))
    frozen_ckpt = REPO_ROOT / a_sum["frozen_v3_audit"]["checkpoint_path"]
    sg_ckpt = AUDIT_DIR / "audio_checkpoints" / "stem_grouped_v3_recipe_seed42.pt"

    f_raw_y = np.array(a_sum["frozen_v3_audit"]["raw_test_scores_sample"]["test_labels"], dtype=np.int64)
    f_raw_p = np.array(a_sum["frozen_v3_audit"]["raw_test_scores_sample"]["test_probs"], dtype=np.float64)
    sg_eval = _eval_ckpt_raw(sg_ckpt, m3_rows, sg_split)
    f_cross = _eval_ckpt_raw(frozen_ckpt, m3_rows, sg_split)

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12.6, 8.8))

    for lbl, y_a, p_a, col, ls in [
        (f"V3 Orig Test (n=182, AUC={a_sum['frozen_v3_audit']['test_037']['auc_roc']:.3f})", f_raw_y, f_raw_p, "#0072B2", "-"),
        (f"Stem-Grouped Seed42 Test (n=206, AUC={s_recipe['test_cal']['auc_roc']:.3f})", sg_eval["sg_test_y"], sg_eval["sg_test_p"], "#009E73", "--"),
        (f"External crossing_A Rec-26 (AUC={a_sum['frozen_v3_audit']['crossing_a_external']['recording_26_tau_metrics']['auc_roc']:.3f})", f_cross["cross_26_y"], f_cross["cross_26_p"], "#D55E00", "-."),
    ]:
        fpr, tpr = _roc_curve_pts(y_a, p_a)
        ax1.plot(fpr, tpr, label=lbl, color=col, ls=ls, lw=2.0)
    ax1.plot([0, 1], [0, 1], "k:", lw=1.0, alpha=0.5)
    ax1.set_xlabel("False Positive Rate")
    ax1.set_ylabel("True Positive Rate")
    ax1.set_title("(a) ROC Curves: In-Domain Test vs External crossing_A")
    ax1.legend(loc="lower right", frameon=True, fontsize=7.3)
    ax1.grid(alpha=0.25, ls="--")

    for lbl, y_a, p_a, col, ls in [
        (f"V3 Orig Test (PR-AUC={a_sum['frozen_v3_audit']['test_037']['pr_auc']:.3f})", f_raw_y, f_raw_p, "#0072B2", "-"),
        (f"Stem-Grouped Seed42 Test (PR-AUC={s_recipe['test_cal']['pr_auc']:.3f})", sg_eval["sg_test_y"], sg_eval["sg_test_p"], "#009E73", "--"),
        (f"External crossing_A Rec-26 (PR-AUC={a_sum['frozen_v3_audit']['crossing_a_external']['recording_26_tau_metrics']['pr_auc']:.3f})", f_cross["cross_26_y"], f_cross["cross_26_p"], "#D55E00", "-."),
    ]:
        rc, pr = _pr_curve_pts(y_a, p_a)
        ax2.plot(rc, pr, label=lbl, color=col, ls=ls, lw=2.0)
    ax2.set_xlabel("Recall")
    ax2.set_ylabel("Precision")
    ax2.set_title("(b) Precision-Recall Curves")
    ax2.legend(loc="lower left", frameon=True, fontsize=7.3)
    ax2.grid(alpha=0.25, ls="--")

    # Panel (c): Confusion Matrices summary grid + confidence distribution
    f_cm = a_sum["frozen_v3_audit"]["test_037"]
    fr_cm = a_sum["frozen_v3_audit"]["test_rec_037"]
    s_cm = s_recipe["test_cal"]
    xa_cm = a_sum["frozen_v3_audit"]["crossing_a_external"]
    cm_cats = ["V3 Test\nWin (n=182)", "V3 Test\nRec (n=26)", "Clean Seed42\nWin (n=206)", "crossing_A\nRec26 (T=0.37)"]
    tp_r = [f_cm["tp"] / f_cm["n_pos"], fr_cm["tp"] / fr_cm["n_pos"], s_cm["tp"] / s_cm["n_pos"], xa_cm["horn_present_13_tp_tau"] / 13.0]
    tn_r = [f_cm["tn"] / f_cm["n_neg"], fr_cm["tn"] / fr_cm["n_neg"], s_cm["tn"] / s_cm["n_neg"], (13 - xa_cm["horn_absent_10_fp_tau"] - xa_cm["no_train_3_fp_tau"]) / 13.0]
    xc = np.arange(len(cm_cats))
    ax3.bar(xc - 0.18, [100 * v for v in tp_r], 0.35, label="Sensitivity / Recall (%)", color="#009E73")
    ax3.bar(xc + 0.18, [100 * v for v in tn_r], 0.35, label="Specificity (%)", color="#0072B2")
    raw_lbls_tp = [f"{f_cm['tp']}/{f_cm['n_pos']}", f"{fr_cm['tp']}/{fr_cm['n_pos']}", f"{s_cm['tp']}/{s_cm['n_pos']}", f"{xa_cm['horn_present_13_tp_tau']}/13"]
    raw_lbls_tn = [f"{f_cm['tn']}/{f_cm['n_neg']}", f"{fr_cm['tn']}/{fr_cm['n_neg']}", f"{s_cm['tn']}/{s_cm['n_neg']}", f"{13 - xa_cm['horn_absent_10_fp_tau'] - xa_cm['no_train_3_fp_tau']}/13"]
    for i in range(len(cm_cats)):
        ax3.text(xc[i] - 0.18, 100 * tp_r[i] + 2, f"{100*tp_r[i]:.0f}%\n({raw_lbls_tp[i]})", ha="center", va="bottom", fontsize=7.0)
        ax3.text(xc[i] + 0.18, 100 * tn_r[i] + 2, f"{100*tn_r[i]:.0f}%\n({raw_lbls_tn[i]})", ha="center", va="bottom", fontsize=7.0)
    ax3.set_xticks(xc, cm_cats)
    ax3.set_ylim(0, 122)
    ax3.set_ylabel("Rate (%)")
    ax3.set_title("(c) Confusion Matrix Rates (Recall vs Specificity)")
    ax3.legend(loc="upper right", frameon=True)
    ax3.grid(axis="y", alpha=0.25, ls="--")

    # Panel (d): 10-bin Reliability + Confidence Histogram overlay
    b_v3 = [b for b in f_cm["reliability_bins"] if b["count"] > 0]
    b_sg = [b for b in s_cm["reliability_bins"] if b["count"] > 0]
    ax4.plot([0, 1], [0, 1], "k--", lw=1.0, label="Perfect Calibration")
    ax4.plot([b["mean_conf"] for b in b_v3], [b["emp_pos_rate"] for b in b_v3], "o-", color="#D55E00", lw=1.8, label=f"V3 Orig Test (ECE={f_cm['ece_10bin']:.4f})")
    ax4.plot([b["mean_conf"] for b in b_sg], [b["emp_pos_rate"] for b in b_sg], "s-", color="#009E73", lw=1.8, label=f"Clean Seed42 Test (ECE={s_cm['ece_10bin']:.4f})")
    ax4_h = ax4.twinx()
    ax4_h.hist(f_raw_p[f_raw_y == 1], bins=10, range=(0, 1), alpha=0.20, color="#10B981", label="V3 Pos Prob Hist")
    ax4_h.hist(f_raw_p[f_raw_y == 0], bins=10, range=(0, 1), alpha=0.20, color="#EF4444", label="V3 Neg Prob Hist")
    ax4_h.set_ylabel("Test Window Count", color="#64748B")
    ax4_h.spines["top"].set_visible(False)
    ax4.set_xlabel("Predicted Probability")
    ax4.set_ylabel("Empirical Positive Frequency")
    ax4.set_title("(d) Reliability Diagram & Test Score Distribution")
    ax4.legend(loc="upper left", frameon=True, fontsize=7.2)
    ax4.grid(alpha=0.25, ls="--")

    fig.suptitle("CompactTrainHornCNN: Discrimination, Confusion Trade-off & Probability Calibration", fontsize=11.0, fontweight="bold")
    fig.tight_layout()
    p2 = FIG_DIR / "fig_m13_a2_roc_pr_confusion_calibration.png"
    saved[str(p2.relative_to(REPO_ROOT))] = _save_png(fig, p2)

    # === Fig A3: ESC-50 Error Breakdown, Multi-Seed Ablation, 5-Fold CV & Learning Curve ===
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12.6, 8.8))

    cats = [(c, v) for c, v in a_sum["frozen_v3_audit"]["test_by_category"].items() if c != "train_horn"]
    cats.sort(key=lambda kv: (-(kv[1]["fp_037"] / max(kv[1]["n_wins"], 1)), kv[0]))
    c_lbls = [f"{c} (n={v['n_wins']})" for c, v in cats]
    c_fpr = [100.0 * v["fp_037"] / max(v["n_wins"], 1) for _, v in cats]
    cols = ["#DC2626" if r > 0 else "#64748B" for r in c_fpr]
    ax1.barh(range(len(cats)), c_fpr, color=cols)
    for idx_c, ((_, vv), fpr_v) in enumerate(zip(cats, c_fpr, strict=True)):
        if fpr_v > 0:
            ax1.text(fpr_v + 1.0, idx_c, f"{fpr_v:.1f}% (maxP={vv['max_p']:.3f})", va="center", fontsize=7.0, fontweight="bold", color="#991B1B")
    ax1.set_yticks(range(len(cats)), c_lbls, fontsize=7.3)
    ax1.invert_yaxis()
    ax1.set_xlim(0, 74)
    ax1.set_xlabel("Window False-Positive Rate @ T*=0.37 (%)")
    ax1.set_title("(a) ESC-50 Fold-5 Hard-Negative FP Rate @ T*=0.37")
    ax1.grid(axis="x", alpha=0.25, ls="--")

    abl = a_sum["stem_grouped_ablations"]
    abl_keys = [("stem_grouped_v3_recipe", "V3 Recipe\n(BatchNorm)"), ("stem_grouped_specaug_strongreg", "SpecAug+\nStrongReg"), ("stem_grouped_groupnorm_specaug", "GroupNorm+\nSpecAug")]
    xa = np.arange(len(abl_keys))
    wa = 0.24
    val_m = [abl[k]["aggregate_5seeds"]["val_f1_cal"]["mean"] for k, _ in abl_keys]
    te_m = [abl[k]["aggregate_5seeds"]["test_f1_cal"]["mean"] for k, _ in abl_keys]
    te_sd = [abl[k]["aggregate_5seeds"]["test_f1_cal"]["std"] for k, _ in abl_keys]
    xa_m = [abl[k]["aggregate_5seeds"]["crossing_a_rec_26_pr_auc"]["mean"] for k, _ in abl_keys]
    xa_sd = [abl[k]["aggregate_5seeds"]["crossing_a_rec_26_pr_auc"]["std"] for k, _ in abl_keys]
    ax2.bar(xa - wa, val_m, wa, label="Clean Val F1 (5-seed mean)", color="#94A3B8")
    ax2.bar(xa, te_m, wa, yerr=te_sd, capsize=3, label="Clean Test F1 (5-seed)", color="#0072B2")
    ax2.bar(xa + wa, xa_m, wa, yerr=xa_sd, capsize=3, label="External crossing_A PR-AUC", color="#D55E00")
    ax2.set_xticks(xa, [lbl for _, lbl in abl_keys])
    ax2.set_ylim(0, 1.08)
    ax2.set_ylabel("Score")
    ax2.set_title("(b) Controlled Stem-Grouped Regularization & Normalization Ablations")
    ax2.legend(loc="upper right", frameon=True, fontsize=7.2)
    ax2.grid(axis="y", alpha=0.25, ls="--")

    cv_v3 = a_sum["grouped_5fold_cv"]["stem_grouped_v3_recipe"]["folds"]
    cv_gn = a_sum["grouped_5fold_cv"]["stem_grouped_groupnorm_specaug"]["folds"]
    xf = np.arange(1, 6)
    ax3.plot(xf, [r["test_f1_cal"] for r in cv_v3], "o-", color="#0072B2", lw=2.0, label=f"V3 Recipe F1 (mean={a_sum['grouped_5fold_cv']['stem_grouped_v3_recipe']['mean_test_f1_cal']:.3f}+-{a_sum['grouped_5fold_cv']['stem_grouped_v3_recipe']['std_test_f1_cal']:.3f})")
    ax3.plot(xf, [r["test_f1_cal"] for r in cv_gn], "s--", color="#009E73", lw=1.8, label=f"GroupNorm+SpecAug F1 (mean={a_sum['grouped_5fold_cv']['stem_grouped_groupnorm_specaug']['mean_test_f1_cal']:.3f}+-{a_sum['grouped_5fold_cv']['stem_grouped_groupnorm_specaug']['std_test_f1_cal']:.3f})")
    ax3.plot(xf, [r["test_pr_auc"] for r in cv_v3], "^:", color="#E69F00", lw=1.6, label=f"V3 Recipe PR-AUC (mean={a_sum['grouped_5fold_cv']['stem_grouped_v3_recipe']['mean_test_pr_auc']:.3f})")
    ax3.set_xticks(xf, [f"Fold {i}" for i in xf])
    ax3.set_ylim(0.65, 1.03)
    ax3.set_ylabel("Held-Out Fold Score")
    ax3.set_title("(c) 5-Fold Strict Stem+Fold Grouped Cross-Validation")
    ax3.legend(loc="lower left", frameon=True, fontsize=7.1)
    ax3.grid(alpha=0.25, ls="--")

    lc = a_sum["learning_curve"]
    lcf = [int(round(100 * r["fraction"])) for r in lc]
    ax4.plot(lcf, [r["train_f1_mean"] for r in lc], "o-", color="#0072B2", lw=1.8, label="Train F1 (clean)")
    ax4.plot(lcf, [r["val_f1_mean"] for r in lc], "s--", color="#E69F00", lw=1.8, label="Clean Val F1")
    te_lc = np.array([r["test_f1_mean"] for r in lc])
    te_lcsd = np.array([r["test_f1_std"] for r in lc])
    ax4.errorbar(lcf, te_lc, yerr=te_lcsd, fmt="^-", color="#009E73", lw=2.0, capsize=3, label="Clean Test F1 (+-1 SD)")
    ax4.plot(lcf, [r["test_pr_auc_mean"] for r in lc], "d:", color="#C0392B", lw=1.7, label="Clean Test PR-AUC")
    ax4.set_xticks(lcf, [f"{p}%" for p in lcf])
    ax4.set_ylim(0.60, 1.03)
    ax4.set_xlabel("Clean Stem-Grouped Training Clusters Used")
    ax4.set_ylabel("Score")
    ax4.set_title("(d) Audio Learning Curve (Data-Scarcity Variance Diagnosis)")
    ax4.legend(loc="lower right", frameon=True, fontsize=7.2)
    ax4.grid(alpha=0.25, ls="--")

    fig.suptitle("CompactTrainHornCNN: Category Failures, Regularization Ablations, 5-Fold CV & Learning Curves", fontsize=11.0, fontweight="bold")
    fig.tight_layout()
    p3 = FIG_DIR / "fig_m13_a3_errors_cv_and_learning_curve.png"
    saved[str(p3.relative_to(REPO_ROOT))] = _save_png(fig, p3)
    return saved


def generate_vision_baseline_figure() -> dict[str, tuple[int, str]]:
    """Generate Fig. V1: YOLOv8n 39f402dfe460 training curves, Ep91-97 overfitting & evaluator reconciliation."""
    _setup_style()
    v_sum = json.loads((AUDIT_DIR / "vision_baseline_39f402_audit.json").read_text(encoding="utf-8"))
    rows = v_sum["epochs"]
    ep = np.array([r["epoch"] for r in rows], dtype=float)
    tr_box = np.array([r["train/box_loss"] for r in rows])
    vl_box = np.array([r["val/box_loss"] for r in rows])
    tr_cls = np.array([r["train/cls_loss"] for r in rows])
    vl_cls = np.array([r["val/cls_loss"] for r in rows])
    tr_dfl = np.array([r["train/dfl_loss"] for r in rows])
    vl_dfl = np.array([r["val/dfl_loss"] for r in rows])
    p_b = np.array([r["metrics/precision(B)"] for r in rows])
    r_b = np.array([r["metrics/recall(B)"] for r in rows])
    m50 = np.array([r["metrics/mAP50(B)"] for r in rows])
    m5095 = np.array([r["metrics/mAP50-95(B)"] for r in rows])
    lr0 = np.array([r["lr/pg0"] for r in rows])

    fig, axes = plt.subplots(2, 2, figsize=(13.6, 9.0))
    ax1, ax2 = axes[0, 0], axes[0, 1]
    ax3, ax4 = axes[1, 0], axes[1, 1]

    # (a) Train vs Val losses
    ax1.plot(ep, tr_cls, color="#0072B2", lw=1.7, label="Train cls_loss")
    ax1.plot(ep, vl_cls, color="#0072B2", lw=1.9, ls="--", label="Val cls_loss (min Ep72: 0.411)")
    ax1.plot(ep, tr_box, color="#D55E00", lw=1.6, label="Train box_loss")
    ax1.plot(ep, vl_box, color="#D55E00", lw=1.8, ls="--", label="Val box_loss (min Ep78: 0.817)")
    ax1.plot(ep, tr_dfl, color="#009E73", lw=1.4, alpha=0.85, label="Train dfl_loss")
    ax1.plot(ep, vl_dfl, color="#009E73", lw=1.6, ls="--", alpha=0.9, label="Val dfl_loss (min Ep72: 1.111)")
    ax1.axvline(72, color="#64748B", ls=":", lw=1.1, label="Val cls min (Ep72)")
    ax1.axvline(91, color="#C0392B", ls="-.", lw=1.2, label="close_mosaic=10 (Ep91)")
    ax1.axvline(93, color="#16A34A", ls=":", lw=1.2, label="best.pt (Ep93) | end Ep97")
    ax1.set_xlabel("Epoch (Logged 1–97 of 100; 6.29 h on MPS)")
    ax1.set_ylabel("Loss")
    ax1.set_title("(a) YOLOv8n (39f402) Train vs. Leaked-Val Loss Trajectories")
    ax1.legend(loc="upper right", ncol=2, fontsize=6.7, frameon=True)
    ax1.grid(alpha=0.25, ls="--")

    # (b) Validation Precision / Recall / mAP50 / mAP50-95
    ax2.plot(ep, m50, color="#0072B2", lw=2.0, label="Val mAP@0.50 (peak Ep56: 0.9759)")
    ax2.plot(ep, m5095, color="#D55E00", lw=2.1, label="Val mAP@0.50:0.95 (best Ep93: 0.7684)")
    ax2.plot(ep, p_b, color="#009E73", lw=1.4, alpha=0.85, label="Val Precision")
    ax2.plot(ep, r_b, color="#8E44AD", lw=1.4, ls="--", alpha=0.85, label="Val Recall")
    tr_best = v_sum["evaluator_py_reconciliation"]["ultralytics_real_val"]["39f402_best_ep93"]["train"]
    ax2.axhline(tr_best["mAP50_95"], color="#D55E00", ls=":", lw=1.3, label=f"Train mAP@50-95={tr_best['mAP50_95']:.4f} (-13.7 pp gap)")
    ax2.axvline(91, color="#C0392B", ls="-.", lw=1.1)
    ax2.axvline(93, color="#16A34A", ls=":", lw=1.1)
    ax2.set_ylim(0.35, 1.03)
    ax2.set_xlabel("Epoch")
    ax2.set_ylabel("Metric Score")
    ax2.set_title("(b) Validation Metrics & -13.71 pp Train-Val mAP@0.50:0.95 Gap")
    ax2.legend(loc="lower right", fontsize=7.0, frameon=True)
    ax2.grid(alpha=0.25, ls="--")

    # (c) Zoom on Epochs 65-97: post-mosaic memorization & LR
    mask = ep >= 65
    ax3.plot(ep[mask], tr_cls[mask], "o-", ms=3, color="#0072B2", lw=1.7, label="Train cls_loss (Ep90 0.363 -> Ep97 0.228)")
    ax3.plot(ep[mask], vl_cls[mask], "s--", ms=3, color="#C0392B", lw=1.9, label="Val cls_loss (Ep72 0.411 -> Ep97 0.431)")
    ax3_r = ax3.twinx()
    ax3_r.spines["top"].set_visible(False)
    ax3_r.plot(ep[mask], m5095[mask], "^-", ms=3.5, color="#D55E00", lw=1.7, label="Val mAP@50-95 (Ep93 0.7684 -> Ep97 0.7575)")
    ax3_r.plot(ep[mask], lr0[mask] * 1000.0, ":", color="#64748B", lw=1.3, label="lr/pg0 x1e3")
    ax3.axvline(72, color="#64748B", ls=":", lw=1.1)
    ax3.axvline(91, color="#C0392B", ls="-.", lw=1.2)
    ax3.axvline(93, color="#16A34A", ls=":", lw=1.2)
    ax3.set_xlabel("Epoch (Late-Training Zoom 65–97)")
    ax3.set_ylabel("Classification Loss")
    ax3_r.set_ylabel("Val mAP@50-95 / LR (x1e-3)")
    ax3.set_title("(c) Late-Epoch Overfitting Zoom & Post-Mosaic Divergence (Ep65–97)")
    l1, lb1 = ax3.get_legend_handles_labels()
    l2, lb2 = ax3_r.get_legend_handles_labels()
    ax3.legend(l1 + l2, lb1 + lb2, loc="lower left", fontsize=6.7, frameon=True)
    ax3.grid(alpha=0.25, ls="--")

    # (d) Evaluator Reconciliation & Split Gap (705d388743ea)
    u = v_sum["evaluator_py_reconciliation"]["ultralytics_real_val"]["39f402_best_ep93"]
    ck = v_sum["evaluator_py_reconciliation"]["checked_in_eval_metrics_json"]
    cats = ["Precision", "Recall", "mAP@0.50", "mAP@0.50:0.95"]
    vals_tr = [u["train"]["mp"], u["train"]["mr"], u["train"]["mAP50"], u["train"]["mAP50_95"]]
    vals_vl = [u["val"]["mp"], u["val"]["mr"], u["val"]["mAP50"], u["val"]["mAP50_95"]]
    vals_te = [u["test"]["mp"], u["test"]["mr"], u["test"]["mAP50"], u["test"]["mAP50_95"]]
    vals_ev = [
        np.mean(list(ck["per_class_precision"].values())),
        np.mean(list(ck["per_class_recall"].values())),
        ck["map50"],
        ck["map50_95"],
    ]
    x = np.arange(len(cats))
    w = 0.20
    ax4.bar(x - 1.5 * w, vals_tr, w, label="Train (Ultralytics Ep93)", color="#0072B2")
    ax4.bar(x - 0.5 * w, vals_vl, w, label="Val (Ultralytics Ep93, leaked)", color="#E69F00")
    ax4.bar(x + 0.5 * w, vals_te, w, label="Test (Ultralytics Ep93, leaked)", color="#009E73")
    ax4.bar(x + 1.5 * w, vals_ev, w, label="Checked-in evaluator.py (Test)", color="#C0392B")
    for xi, vt, ve in zip(x, vals_te, vals_ev, strict=True):
        ax4.text(xi + 0.5 * w, vt + 0.012, f"{vt:.3f}", ha="center", va="bottom", fontsize=6.5, rotation=90)
        ax4.text(xi + 1.5 * w, ve + 0.012, f"{ve:.3f}", ha="center", va="bottom", fontsize=6.5, rotation=90)
    ax4.set_xticks(x, cats)
    ax4.set_ylim(0.55, 1.13)
    ax4.set_ylabel("Score")
    ax4.set_title("(d) 705d Split Gap & evaluator.py vs Ultralytics Reconciliation")
    ax4.legend(loc="lower left", fontsize=6.9, frameon=True)
    ax4.grid(axis="y", alpha=0.25, ls="--")

    fig.suptitle("Frozen YOLOv8n (39f402dfe460): Training History, Post-Mosaic Overfitting & Split Reconciliation", fontsize=11.0, fontweight="bold")
    fig.tight_layout()
    p = FIG_DIR / "fig_m13_v1_39f402_training_curves.png"
    return {str(p.relative_to(REPO_ROOT)): _save_png(fig, p)}


def generate_vision_kaggle_figures() -> dict[str, tuple[int, str]]:
    """Generate Fig. V2 & V3: split leakage, clean Kaggle retrain learning curves, confusion, & field FPs."""
    _setup_style()
    saved: dict[str, tuple[int, str]] = {}

    sp_cmp = json.loads((AUDIT_DIR / "vision_split_leakage_comparison.json").read_text(encoding="utf-8"))
    v39 = json.loads((AUDIT_DIR / "vision_baseline_39f402_audit.json").read_text(encoding="utf-8"))
    v39_clean = json.loads((AUDIT_DIR / "vision_39f402_on_clean_splits.json").read_text(encoding="utf-8"))
    kag = json.loads((AUDIT_DIR / "vision_kaggle_clean_retrain_audit.json").read_text(encoding="utf-8"))
    fld = json.loads((AUDIT_DIR / "vision_clean_vs_frozen_field_diagnostics.json").read_text(encoding="utf-8"))

    # ---------- FIG V2: Leakage, Clean Learning Trajectories, Train-Val-Test Gap, BBox Scale Recall ----------
    fig, axes = plt.subplots(2, 2, figsize=(14.0, 9.2))
    ax1, ax2 = axes[0, 0], axes[0, 1]
    ax3, ax4 = axes[1, 0], axes[1, 1]

    # (a) Split contamination comparison
    split_keys = ["leaked_705d388743ea", "session_grouped", "day_grouped"]
    split_lbls = [
        f"Leaked 705d388743ea\n(Frozen 39f402 | {sp_cmp['leaked_705d388743ea']['test']['aug_multiplier']:.2f}x)",
        f"Session-Grouped\n(Clean | {sp_cmp['session_grouped']['test']['aug_multiplier']:.2f}x)",
        f"Day-Grouped\n(Day-Disjoint | {sp_cmp['day_grouped']['test']['aug_multiplier']:.2f}x)",
    ]
    pct_600s_te = [100.0 * sp_cmp[k]["test"]["within_600s_of_train"] / sp_cmp[k]["test"]["n_timestamped"] for k in split_keys]
    pct_same_day_te = [100.0 * sp_cmp[k]["test"]["same_calendar_day_as_train"] / sp_cmp[k]["test"]["n_timestamped"] for k in split_keys]
    seen_39f_te = [100.0 * sp_cmp[k]["test"]["seen_exact_in_39f_train"] / sp_cmp[k]["test"]["n_images"] for k in split_keys]

    x = np.arange(len(split_keys))
    w = 0.24
    ax1.bar(x - w, pct_600s_te, w, label="Test <=600s of Train (%)", color="#C0392B")
    ax1.bar(x, pct_same_day_te, w, label="Test Same Calendar Day (%)", color="#E69F00")
    ax1.bar(x + w, seen_39f_te, w, label="In Frozen 39f402 Train (%)", color="#0072B2")
    for xi, a, b, c in zip(x, pct_600s_te, pct_same_day_te, seen_39f_te, strict=True):
        ax1.text(xi - w, a + 1.5, f"{a:.1f}%", ha="center", va="bottom", fontsize=7.2)
        ax1.text(xi, b + 1.5, f"{b:.1f}%", ha="center", va="bottom", fontsize=7.2)
        ax1.text(xi + w, c + 1.5, f"{c:.1f}%", ha="center", va="bottom", fontsize=7.2)
    ax1.set_xticks(x, split_lbls)
    ax1.set_ylim(0, 120)
    ax1.set_ylabel("Contamination / Overlap (%)")
    ax1.set_title("(a) Test-Split Temporal, Day & Augmentation Contamination")
    ax1.legend(loc="upper right", fontsize=7.2, frameon=True)
    ax1.grid(axis="y", alpha=0.25, ls="--")

    # (b) Clean YOLO Learning Curves (Val mAP50-95 & Val cls_loss)
    k_runs = kag["runs"]
    colors = {"session_grouped_base": "#E69F00", "day_grouped_base": "#0072B2", "day_grouped_reg": "#009E73"}
    lbls = {"session_grouped_base": "Session-Grouped Base", "day_grouped_base": "Day-Grouped Base", "day_grouped_reg": "Day-Grouped Reg"}
    ax2_r = ax2.twinx()
    ax2_r.spines["top"].set_visible(False)
    for rn in ("session_grouped_base", "day_grouped_base", "day_grouped_reg"):
        eps = np.array([r["epoch"] for r in k_runs[rn]["epochs"]], dtype=float)
        m5095 = np.array([r["metrics/mAP50-95(B)"] for r in k_runs[rn]["epochs"]])
        vcls = np.array([r["val/cls_loss"] for r in k_runs[rn]["epochs"]])
        ax2.plot(eps, m5095, color=colors[rn], lw=1.9, label=f"{lbls[rn]} mAP50-95 (best Ep{k_runs[rn]['best_epoch_fitness']})")
        ax2_r.plot(eps, vcls, color=colors[rn], lw=1.2, ls="--", alpha=0.75, label=f"{lbls[rn]} val/cls_loss")
    ax2.set_ylim(0.32, 0.85)
    ax2_r.set_ylim(0.35, 2.2)
    ax2.set_xlabel("Epoch (Kaggle T4 Clean 100-Epoch Retrains)")
    ax2.set_ylabel("Clean Val mAP@0.50:0.95")
    ax2_r.set_ylabel("Clean Val cls_loss (dashed)")
    ax2.set_title("(b) Clean Retrain Learning Curves (Val mAP@50-95 vs Val cls_loss)")
    l1, lb1 = ax2.get_legend_handles_labels()
    l2, lb2 = ax2_r.get_legend_handles_labels()
    ax2.legend(l1 + l2, lb1 + lb2, loc="center right", fontsize=6.6, frameon=True)
    ax2.grid(alpha=0.25, ls="--")

    # (c) Train vs Val vs Test mAP50-95 Generalization Gap
    u39 = v39["evaluator_py_reconciliation"]["ultralytics_real_val"]["39f402_best_ep93"]
    models_gap = [
        ("Frozen 39f402\n(705d Leaked)", u39["train"]["mAP50_95"], u39["val"]["mAP50_95"], u39["test"]["mAP50_95"]),
        ("Frozen 39f402\n(DayTest Unseen84)", u39["train"]["mAP50_95"], v39_clean["splits"]["best_ep93"]["day_grouped_val"]["mAP50_95"], v39_clean["splits"]["best_ep93"]["day_grouped_test_unseen_to_39f402"]["mAP50_95"]),
        ("Session-Grouped\nBase (Clean)", k_runs["session_grouped_base"]["eval"]["best"]["train"]["mAP50_95"], k_runs["session_grouped_base"]["eval"]["best"]["val"]["mAP50_95"], k_runs["session_grouped_base"]["eval"]["best"]["test"]["mAP50_95"]),
        ("Day-Grouped\nBase (Clean)", k_runs["day_grouped_base"]["eval"]["best"]["train"]["mAP50_95"], k_runs["day_grouped_base"]["eval"]["best"]["val"]["mAP50_95"], k_runs["day_grouped_base"]["eval"]["best"]["test"]["mAP50_95"]),
        ("Day-Grouped\nReg (Clean)", k_runs["day_grouped_reg"]["eval"]["best"]["train"]["mAP50_95"], k_runs["day_grouped_reg"]["eval"]["best"]["val"]["mAP50_95"], k_runs["day_grouped_reg"]["eval"]["best"]["test"]["mAP50_95"]),
    ]
    xg = np.arange(len(models_gap))
    wg = 0.25
    tr_v = [m[1] for m in models_gap]
    vl_v = [m[2] for m in models_gap]
    te_v = [m[3] for m in models_gap]
    ax3.bar(xg - wg, tr_v, wg, label="Train mAP@50-95", color="#0072B2")
    ax3.bar(xg, vl_v, wg, label="Val mAP@50-95", color="#E69F00")
    ax3.bar(xg + wg, te_v, wg, label="Test mAP@50-95", color="#009E73")
    for xi, tv, tev in zip(xg, tr_v, te_v, strict=True):
        ax3.text(xi + wg, tev + 0.012, f"{tev:.3f}\n({100*(tev-tv):+.1f}pp)", ha="center", va="bottom", fontsize=6.6)
    ax3.set_xticks(xg, [m[0] for m in models_gap], fontsize=7.6)
    ax3.set_ylim(0.50, 1.05)
    ax3.set_ylabel("Ultralytics COCO mAP@0.50:0.95")
    ax3.set_title("(c) Train -> Val -> Held-Out Test Generalization Gap")
    ax3.legend(loc="lower left", fontsize=7.3, frameon=True)
    ax3.grid(axis="y", alpha=0.25, ls="--")

    # (d) BBox-Size Recall@0.35 on Held-Out Day Test (n=264, 274 boxes)
    scales = [("large_ge16pct", "Large (>=16% area)\nn=95"), ("medium_4_16pct", "Medium (4-16%)\nn=108"), ("small_lt4pct", "Small (<4% area)\nn=71")]
    m_order = [("frozen_39f402", "Frozen 39f402 (68% seen; 7 FP)", "#94A3B8"), ("session_grouped_base", "Session-Grouped Base (4 FP)", "#E69F00"), ("day_grouped_base", "Day-Grouped Base (15 FP)", "#0072B2"), ("day_grouped_reg", "Day-Grouped Reg (4 FP)", "#009E73")]
    xs = np.arange(len(scales))
    ws = 0.20
    dt_sum = fld["day_grouped_test_264_conf035"]
    for idx_m, (mk, mlbl, mcol) in enumerate(m_order):
        vals = [dt_sum[mk]["by_bbox_area"][sk]["recall_035"] for sk, _ in scales]
        offs = (idx_m - 1.5) * ws
        ax4.bar(xs + offs, vals, ws, label=mlbl, color=mcol)
        for xi, v in zip(xs, vals, strict=True):
            ax4.text(xi + offs, v + 0.008, f"{v:.3f}", ha="center", va="bottom", fontsize=6.4, rotation=90)
    ax4.set_xticks(xs, [sl for _, sl in scales])
    ax4.set_ylim(0.75, 1.09)
    ax4.set_ylabel("Box Recall @ conf=0.35, IoU=0.50")
    ax4.set_title("(d) Held-Out Day Test (2026-05-23) Recall by Object Scale")
    ax4.legend(loc="lower left", fontsize=7.0, frameon=True)
    ax4.grid(axis="y", alpha=0.25, ls="--")

    fig.suptitle("YOLOv8n Leakage Audit vs. Clean Session- & Calendar-Day-Grouped Retraining on Kaggle T4", fontsize=11.0, fontweight="bold")
    fig.tight_layout()
    p_v2 = FIG_DIR / "fig_m13_v2_leakage_and_clean_retrain.png"
    saved[str(p_v2.relative_to(REPO_ROOT))] = _save_png(fig, p_v2)

    # ---------- FIG V3: Confusion Matrices, Per-Class AP50-95, & Field FP Persistence ----------
    fig2, axes2 = plt.subplots(2, 2, figsize=(14.0, 9.2))
    bx1, bx2 = axes2[0, 0], axes2[0, 1]
    bx3, bx4 = axes2[1, 0], axes2[1, 1]

    cm_lbls = ["front", "rear", "side", "bg"]
    for ax_cm, rn, ttl in (
        (bx1, "session_grouped_base", "(a) Test CM: Clean Session-Grouped Base (n=241)"),
        (bx2, "day_grouped_reg", "(b) Test CM: Clean Day-Grouped Regularized (n=264)"),
    ):
        mat = np.array(k_runs[rn]["eval"]["best"]["test"]["confusion_matrix"], dtype=int)
        ax_cm.imshow(mat, cmap="Blues")
        ax_cm.set_xticks(range(4), cm_lbls)
        ax_cm.set_yticks(range(4), cm_lbls)
        ax_cm.set_xlabel("True Class")
        ax_cm.set_ylabel("Predicted Class")
        ax_cm.set_title(ttl)
        for r in range(4):
            for c in range(4):
                ax_cm.text(
                    c,
                    r,
                    f"{mat[r, c]}",
                    ha="center",
                    va="center",
                    color="white" if mat[r, c] > mat.max() * 0.55 else "black",
                    fontsize=9.2,
                    fontweight="bold" if r == c else "normal",
                )

    # (c) Per-class mAP@50-95 across models on held-out Test splits
    cls_list = ["front", "rear", "side"]
    xc = np.arange(len(cls_list))
    wc = 0.16
    per_cls_models = [
        ("39f402 (705d Leaked)", u39["test"]["per_class_ap50_95"], "#94A3B8"),
        ("39f402 (Day Unseen84)", v39_clean["splits"]["best_ep93"]["day_grouped_test_unseen_to_39f402"]["per_class_ap50_95"], "#64748B"),
        ("Session-Grouped Base", k_runs["session_grouped_base"]["eval"]["best"]["test"]["per_class_ap50_95"], "#E69F00"),
        ("Day-Grouped Base", k_runs["day_grouped_base"]["eval"]["best"]["test"]["per_class_ap50_95"], "#0072B2"),
        ("Day-Grouped Reg", k_runs["day_grouped_reg"]["eval"]["best"]["test"]["per_class_ap50_95"], "#009E73"),
    ]
    for idx_c, (mlbl, dmap, col) in enumerate(per_cls_models):
        vals = [dmap[cl] for cl in cls_list]
        offs = (idx_c - 2.0) * wc
        bx3.bar(xc + offs, vals, wc, label=mlbl, color=col)
        for xi, v in zip(xc, vals, strict=True):
            bx3.text(xi + offs, v + 0.01, f"{v:.3f}", ha="center", va="bottom", fontsize=6.3, rotation=90)
    bx3.set_xticks(xc, ["front", "rear", "side"])
    bx3.set_ylim(0.55, 1.00)
    bx3.set_ylabel("Per-Class Test mAP@0.50:0.95")
    bx3.set_title("(c) Per-Class COCO AP@0.50:0.95 Across Leaked & Clean Test Splits")
    bx3.legend(loc="lower right", fontsize=6.9, frameon=True)
    bx3.grid(axis="y", alpha=0.25, ls="--")

    # (d) Field control / overhead bridge FP & locomotive persistence on upright crossing_A
    ca = fld["crossing_a_upright_controls_and_engine_conf035"]
    clips = [
        ("no_train_events/event_001_front", "NT01\nFront"),
        ("no_train_events/event_001_back", "NT01\nBack"),
        ("no_train_events/event_002_front", "NT02\nFront (Bridge)"),
        ("no_train_events/event_003_back", "NT03\nBack"),
        ("engine_events/event_001_front", "Eng01\nFront"),
        ("engine_events/event_001_back", "Eng01\nBack"),
    ]
    xfl = np.arange(len(clips))
    wfl = 0.20
    for idx_m, (mk, mlbl, mcol) in enumerate(m_order):
        vals = [100.0 * ca[mk][ck]["det_frames_conf035"] / max(ca[mk][ck]["sampled_frames"], 1) for ck, _ in clips]
        offs = (idx_m - 1.5) * wfl
        bx4.bar(xfl + offs, vals, wfl, label=mlbl.split(" (")[0], color=mcol)
    bx4.axvline(3.5, color="#334155", ls=":", lw=1.2)
    bx4.text(1.5, 104.0, "<- Non-Train Controls (FP Rate %) |", ha="center", fontsize=7.4, color="#C0392B", fontweight="bold")
    bx4.text(4.5, 104.0, "Solitary Locomotive ->", ha="center", fontsize=7.4, color="#009E73", fontweight="bold")
    bx4.set_xticks(xfl, [cl for _, cl in clips], fontsize=7.7)
    bx4.set_ylim(0, 115)
    bx4.set_ylabel("Frames Detected @ conf=0.35 (%)")
    bx4.set_title("(d) Field crossing_A Bridge-FP Persistence & Locomotive Recall")
    bx4.legend(loc="upper right", bbox_to_anchor=(0.99, 0.90), fontsize=7.0, frameon=True)
    bx4.grid(axis="y", alpha=0.25, ls="--")

    fig2.suptitle("YOLOv8n Error Diagnosis: Clean Test Confusion, Class Sensitivity & Field Domain Failure", fontsize=11.0, fontweight="bold")
    fig2.tight_layout()
    p_v3 = FIG_DIR / "fig_m13_v3_confusion_and_pr_comparison.png"
    saved[str(p_v3.relative_to(REPO_ROOT))] = _save_png(fig2, p_v3)
    return saved


def main() -> int:
    saved = generate_audio_figures()
    saved.update(generate_vision_baseline_figure())
    saved.update(generate_vision_kaggle_figures())
    print(json.dumps({"figures": saved}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
