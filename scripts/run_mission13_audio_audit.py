#!/usr/bin/env python3
"""Mission 13 Complete CompactTrainHornCNN Generalization, Leakage & Retraining Audit.

Audits the frozen Audio V1/V2/V3 checkpoints cleanly, quantifies positive-stem and
ESC-50 fold leakage, compares un-augmented Train vs Val vs Locked Test vs external
crossing_A (27-event field audio), runs leakage-free multi-seed retraining on
``data/splits/audio_v3_stem_grouped/``, 5-fold grouped CV, sample-size learning
curves, and controlled regularization / GroupNorm ablations.

Preserves all Mission 11 frozen checkpoints and artifacts untouched.
"""

from __future__ import annotations

import datetime as dt
import json
import math
import random
import sys
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from railway_detection.audio.features import compute_log_mel_spectrogram  # noqa: E402
from railway_detection.audio.model import CompactTrainHornCNN  # noqa: E402
from railway_detection.audio.preprocessor import (  # noqa: E402
    load_wav,
    sliding_windows,
    standardize_wav,
)
from railway_detection.data.audio_extractor import extract_audio_from_video  # noqa: E402
from railway_detection.data.leakage_audit import (  # noqa: E402
    extract_audio_negative_fold,
    extract_audio_positive_stem,
)
from railway_detection.experiments.frozen_config import compute_file_sha256  # noqa: E402
from railway_detection.safety.media_guard import require_media_authorization  # noqa: E402

V3_MANIFEST_PATH = REPO_ROOT / "data" / "manifests" / "audio_training_dataset_v3.json"
V3_STEM_SPLIT_PATH = REPO_ROOT / "data" / "splits" / "audio_v3_stem_grouped" / "dataset_split.json"
V3_FROZEN_CKPT = REPO_ROOT / "experiments" / "audio" / "RUN_20261008_AUDIO_V3_ESC50" / "checkpoints" / "best.pt"
V2_HIST_PATH = REPO_ROOT / "experiments" / "audio" / "RUN_20261008_AUDIO_V2" / "metrics" / "training_history.json"
V1_HIST_PATH = REPO_ROOT / "experiments" / "audio" / "RUN_20260923_AUDIO_001" / "metrics" / "training_history.json"
V3_METRICS_PATH = REPO_ROOT / "experiments" / "audio" / "RUN_20261008_AUDIO_V3_ESC50" / "metrics" / "metrics.json"
M11_UPRIGHT_TABLE_PATH = REPO_ROOT / "results" / "upright_27_event_evaluation" / "event_by_event_27_multimodal_evaluation.json"
M11_UPRIGHT_MANIFEST_PATH = REPO_ROOT / "results" / "upright_inference_v2" / "UPRIGHT_INFERENCE_MANIFEST.json"
CROSSING_AUDIO_CACHE_NPZ = Path("/tmp/m13_crossing_audio_feats.npz")

OUT_DIR = REPO_ROOT / "results" / "model_generalization_audit"
CKPT_OUT_DIR = OUT_DIR / "audio_checkpoints"


class GroupNormTrainHornCNN(nn.Module):
    """Regularized CompactTrainHornCNN variant replacing BatchNorm with GroupNorm/LayerNorm."""

    def __init__(self, in_channels: int = 1, dropout: float = 0.40) -> None:
        super().__init__()
        self.conv1 = nn.Conv2d(in_channels, 16, kernel_size=3, padding=1)
        self.gn1 = nn.GroupNorm(4, 16)
        self.pool1 = nn.MaxPool2d(kernel_size=2, stride=2)

        self.conv2 = nn.Conv2d(16, 32, kernel_size=3, padding=1)
        self.gn2 = nn.GroupNorm(4, 32)
        self.pool2 = nn.MaxPool2d(kernel_size=2, stride=2)

        self.conv3 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.gn3 = nn.GroupNorm(8, 64)
        self.pool3 = nn.AdaptiveAvgPool2d((1, 1))

        self.fc1 = nn.Linear(64, 32)
        self.ln_fc = nn.LayerNorm(32)
        self.dropout = nn.Dropout(dropout)
        self.fc2 = nn.Linear(32, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if x.dim() == 3:
            x = x.unsqueeze(1)
        x = self.pool1(F.relu(self.gn1(self.conv1(x))))
        x = self.pool2(F.relu(self.gn2(self.conv2(x))))
        x = self.pool3(F.relu(self.gn3(self.conv3(x))))
        x = x.flatten(start_dim=1)
        x = self.dropout(F.relu(self.ln_fc(self.fc1(x))))
        return self.fc2(x).squeeze(-1)


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def wilson_ci_95(k: int, n: int) -> tuple[float, float]:
    if n <= 0:
        return (0.0, 0.0)
    z = 1.959963984540054
    p = k / n
    denom = 1.0 + (z * z) / n
    center = (p + (z * z) / (2.0 * n)) / denom
    half = (z * math.sqrt((p * (1.0 - p) + (z * z) / (4.0 * n)) / n)) / denom
    return (round(max(0.0, center - half), 4), round(min(1.0, center + half), 4))


def compute_binary_metrics(labels: np.ndarray, scores: np.ndarray, threshold: float) -> dict[str, Any]:
    y = np.asarray(labels, dtype=np.int64)
    p = np.asarray(scores, dtype=np.float64)
    preds = (p >= threshold).astype(np.int64)
    tp = int(np.sum((preds == 1) & (y == 1)))
    fp = int(np.sum((preds == 1) & (y == 0)))
    fn = int(np.sum((preds == 0) & (y == 1)))
    tn = int(np.sum((preds == 0) & (y == 0)))
    n = len(y)
    acc = (tp + tn) / max(n, 1)
    prec = tp / max(tp + fp, 1) if (tp + fp) > 0 else 0.0
    rec = tp / max(tp + fn, 1) if (tp + fn) > 0 else 0.0
    spec = tn / max(tn + fp, 1) if (tn + fp) > 0 else 0.0
    f1 = 2.0 * prec * rec / max(prec + rec, 1e-12) if (prec + rec) > 0 else 0.0
    bal_acc = 0.5 * (rec + spec)

    pos_mask = y == 1
    n_pos = int(np.sum(pos_mask))
    n_neg = n - n_pos
    if n_pos == 0 or n_neg == 0:
        auc_roc = float("nan")
        pr_auc = float("nan")
    else:
        # Exact average-rank Mann-Whitney U handles ties properly
        order = np.argsort(p, kind="mergesort")
        ranks = np.empty(n, dtype=np.float64)
        sorted_p = p[order]
        i = 0
        while i < n:
            j = i + 1
            while j < n and sorted_p[j] == sorted_p[i]:
                j += 1
            avg_rank = 0.5 * (i + 1 + j)
            ranks[order[i:j]] = avg_rank
            i = j
        auc_roc = float((np.sum(ranks[pos_mask]) - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg))

        desc = np.argsort(-p, kind="mergesort")
        tp_c = np.cumsum(y[desc] == 1)
        fp_c = np.cumsum(y[desc] == 0)
        recs = np.concatenate(([0.0], tp_c / n_pos, [1.0]))
        precs = np.concatenate(([1.0], tp_c / np.maximum(tp_c + fp_c, 1e-12), [0.0]))
        pr_auc = float(np.trapezoid(precs[:-1], recs[:-1])) if hasattr(np, "trapezoid") else float(np.trapz(precs[:-1], recs[:-1]))

    brier = float(np.mean((p - y) ** 2.0))
    eps = 1e-7
    p_clip = np.clip(p, eps, 1.0 - eps)
    bce_unweighted = float(-np.mean(y * np.log(p_clip) + (1 - y) * np.log(1.0 - p_clip)))

    bins = np.linspace(0.0, 1.0, 11)
    ece = 0.0
    reliability_bins = []
    for b in range(10):
        lo, hi = bins[b], bins[b + 1]
        mask = (p >= lo) & (p <= hi if b == 9 else p < hi)
        cnt = int(np.sum(mask))
        if cnt > 0:
            mean_c = float(np.mean(p[mask]))
            emp_a = float(np.mean(y[mask]))
            ece += (cnt / max(n, 1)) * abs(emp_a - mean_c)
            reliability_bins.append({"bin": [round(lo, 1), round(hi, 1)], "count": cnt, "mean_conf": round(mean_c, 4), "emp_pos_rate": round(emp_a, 4)})
        else:
            reliability_bins.append({"bin": [round(lo, 1), round(hi, 1)], "count": 0, "mean_conf": None, "emp_pos_rate": None})

    return {
        "n": n,
        "n_pos": n_pos,
        "n_neg": n_neg,
        "threshold": round(float(threshold), 4),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "recall_ci95": list(wilson_ci_95(tp, tp + fn)),
        "specificity": round(spec, 4),
        "specificity_ci95": list(wilson_ci_95(tn, tn + fp)),
        "f1": round(f1, 4),
        "balanced_accuracy": round(bal_acc, 4),
        "auc_roc": round(auc_roc, 4) if not math.isnan(auc_roc) else None,
        "pr_auc": round(pr_auc, 4) if not math.isnan(pr_auc) else None,
        "brier": round(brier, 4),
        "bce": round(bce_unweighted, 4),
        "ece_10bin": round(float(ece), 4),
        "reliability_bins": reliability_bins,
    }


def apply_v3_aug(feat: np.ndarray, rng: np.random.Generator, *, specaugment: bool = False) -> np.ndarray:
    aug = feat.copy()
    aug = aug + rng.uniform(-2.5, 2.5)
    shift = int(rng.integers(-3, 4))
    if shift != 0:
        aug = np.roll(aug, shift, axis=1)
    aug = aug + rng.normal(0.0, float(rng.uniform(0.01, 0.05)), size=aug.shape)
    if specaugment:
        # 1 frequency mask (up to 8 mel bins) + 1 time mask (up to 10 frames)
        f_w = int(rng.integers(1, 9))
        f0 = int(rng.integers(0, max(1, aug.shape[0] - f_w)))
        aug[f0 : f0 + f_w, :] = 0.0
        t_w = int(rng.integers(1, 11))
        t0 = int(rng.integers(0, max(1, aug.shape[1] - t_w)))
        aug[:, t0 : t0 + t_w] = 0.0
    return aug


def prepare_or_verify_crossing_audio_cache() -> dict[str, Any]:
    """Extract and cache the 27 crossing_A event natural log-Mel arrays under owner auth."""
    m11_table = json.loads(M11_UPRIGHT_TABLE_PATH.read_text(encoding="utf-8"))
    rows_27 = m11_table["events"] if isinstance(m11_table, dict) else m11_table
    inventory = json.loads((REPO_ROOT / "docs" / "PHASE11_3_REVIEW_INVENTORY.json").read_text(encoding="utf-8"))
    manifest = json.loads(M11_UPRIGHT_MANIFEST_PATH.read_text(encoding="utf-8"))
    by_eid = {e["event_id"]: e for e in manifest["events"]}

    if not CROSSING_AUDIO_CACHE_NPZ.exists():
        all_feats = []
        all_eids = []
        all_widx = []
        for row in rows_27:
            eid = row["event_id"]
            front_mov = REPO_ROOT / inventory["events"][eid]["raw_media"]["front"]["path"]
            require_media_authorization(front_mov, "AUDIO_EXTRACTION")
            with tempfile.TemporaryDirectory(prefix="m13_x_aud_") as tmp_dir:
                wav = Path(tmp_dir) / f"{eid.replace('/', '_')}.wav"
                extract_audio_from_video(front_mov, wav, sample_rate=16000, channels=1)
                samples, sr = load_wav(wav)
                std_wav = standardize_wav(samples, sr, target_rate=16000)
                windows = sliding_windows(std_wav, 16000, window_s=1.0, hop_s=0.5)
                for wi, w in enumerate(windows):
                    w_sig = w.samples
                    target_len = 16000
                    if len(w_sig) < target_len:
                        w_sig = np.pad(w_sig, (0, target_len - len(w_sig)), mode="reflect")
                    elif len(w_sig) > target_len:
                        w_sig = w_sig[:target_len]
                    mel = compute_log_mel_spectrogram(
                        w_sig,
                        sample_rate=16000,
                        n_fft=512,
                        hop_length=256,
                        n_mels=64,
                        f_min=80.0,
                        f_max=8000.0,
                        log_scale="natural",
                    ).astype(np.float32)
                    all_feats.append(mel)
                    all_eids.append(eid)
                    all_widx.append(wi)
        np.savez_compressed(
            CROSSING_AUDIO_CACHE_NPZ,
            feats=np.stack(all_feats, axis=0),
            eids=np.array(all_eids),
            widx=np.array(all_widx, dtype=np.int32),
        )

    npz = np.load(CROSSING_AUDIO_CACHE_NPZ)
    feats = npz["feats"]
    eids = [str(x) for x in npz["eids"]]

    # Verify parity against Mission 11 saved raw scores!
    ckpt = torch.load(V3_FROZEN_CKPT, map_location="cpu", weights_only=False)
    model = CompactTrainHornCNN(in_channels=1, dropout=0.30)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()
    norm_x = (feats - float(ckpt["norm_mean"])) / float(ckpt["norm_std"])
    with torch.no_grad():
        probs = torch.sigmoid(model(torch.from_numpy(norm_x).float().unsqueeze(1))).numpy()

    by_event_idx: dict[str, list[int]] = defaultdict(list)
    for idx, eid in enumerate(eids):
        by_event_idx[eid].append(idx)

    max_diff = 0.0
    for row in rows_27:
        eid = row["event_id"]
        rec_p = REPO_ROOT / by_eid[eid]["audio_raw_path"]
        ref = [float(json.loads(ln)["metadata"]["probability"]) for ln in rec_p.read_text(encoding="utf-8").splitlines() if ln.strip()]
        got = probs[by_event_idx[eid]]
        assert len(ref) == len(got), f"Window count mismatch for {eid}: {len(ref)} vs {len(got)}"
        max_diff = max(max_diff, float(np.max(np.abs(np.array(ref) - got))))

    return {
        "feats": feats,
        "eids": eids,
        "by_event_idx": dict(by_event_idx),
        "rows_27": rows_27,
        "parity_max_abs_diff_vs_mission11": round(max_diff, 8),
    }


def longest_run(scores: np.ndarray, tau: float) -> int:
    best = cur = 0
    for s in scores:
        if s >= tau:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


def eval_crossing_a(model: nn.Module, norm_mean: float, norm_std: float, tau: float, cross: dict[str, Any]) -> dict[str, Any]:
    feats = cross["feats"]
    x = (feats - norm_mean) / norm_std
    model.eval()
    with torch.no_grad():
        probs = torch.sigmoid(model(torch.from_numpy(x).float().unsqueeze(1))).numpy()

    by_event_idx = cross["by_event_idx"]
    ev_max_scores, ev_bin_labels = [], []
    cohort_res = {"train_horn_present_13": [], "train_horn_absent_10": [], "no_train_3": [], "engine_1": []}
    all_tr_probs, all_tr_labels = [], []

    for row in cross["rows_27"]:
        eid = row["event_id"]
        sc = probs[by_event_idx[eid]]
        mp = float(np.max(sc))
        pos_at_tau = bool(mp >= tau)
        pos_050 = bool(mp >= 0.50)
        pos_hyst = bool(longest_run(sc, 0.75) >= 2)
        item = {"eid": eid, "max_p": round(mp, 4), "pos_tau": pos_at_tau, "pos_050": pos_050, "pos_075k2": pos_hyst}
        if row["cohort"] == "train_events":
            if row["gt_horn_present"]:
                cohort_res["train_horn_present_13"].append(item)
                ev_max_scores.append(mp)
                ev_bin_labels.append(1)
                all_tr_probs.extend(sc.tolist())
                all_tr_labels.extend([1] * len(sc))
            else:
                cohort_res["train_horn_absent_10"].append(item)
                ev_max_scores.append(mp)
                ev_bin_labels.append(0)
        elif row["cohort"] == "no_train_events":
            cohort_res["no_train_3"].append(item)
            all_tr_probs.extend(sc.tolist())
            all_tr_labels.extend([0] * len(sc))
        else:
            cohort_res["engine_1"].append(item)

    # Recording-level Horn-Present (13) vs Horn-Absent+No-Train (13) ROC-AUC & PR-AUC
    scores_26 = [x["max_p"] for x in cohort_res["train_horn_present_13"]] + [x["max_p"] for x in cohort_res["train_horn_absent_10"]] + [x["max_p"] for x in cohort_res["no_train_3"]]
    labels_26 = [1] * 13 + [0] * 13
    rec_m_tau = compute_binary_metrics(np.array(labels_26), np.array(scores_26), threshold=tau)
    rec_m_hyst = compute_binary_metrics(
        np.array(labels_26),
        np.array([1.0 if x["pos_075k2"] else 0.0 for x in (cohort_res["train_horn_present_13"] + cohort_res["train_horn_absent_10"] + cohort_res["no_train_3"])]),
        threshold=0.5,
    )
    return {
        "horn_present_13_tp_tau": sum(1 for x in cohort_res["train_horn_present_13"] if x["pos_tau"]),
        "horn_present_13_tp_075k2": sum(1 for x in cohort_res["train_horn_present_13"] if x["pos_075k2"]),
        "horn_absent_10_fp_tau": sum(1 for x in cohort_res["train_horn_absent_10"] if x["pos_tau"]),
        "horn_absent_10_fp_075k2": sum(1 for x in cohort_res["train_horn_absent_10"] if x["pos_075k2"]),
        "no_train_3_fp_tau": sum(1 for x in cohort_res["no_train_3"] if x["pos_tau"]),
        "no_train_3_fp_075k2": sum(1 for x in cohort_res["no_train_3"] if x["pos_075k2"]),
        "engine_1_pos_tau": sum(1 for x in cohort_res["engine_1"] if x["pos_tau"]),
        "recording_26_tau_metrics": {
            "f1": rec_m_tau["f1"],
            "precision": rec_m_tau["precision"],
            "recall": rec_m_tau["recall"],
            "specificity": rec_m_tau["specificity"],
            "auc_roc": rec_m_tau["auc_roc"],
            "pr_auc": rec_m_tau["pr_auc"],
        },
        "recording_26_hyst_075k2_metrics": {
            "f1": rec_m_hyst["f1"],
            "precision": rec_m_hyst["precision"],
            "recall": rec_m_hyst["recall"],
            "specificity": rec_m_hyst["specificity"],
        },
    }


def rec_level_metrics(meta_list: list[dict[str, Any]], scores: np.ndarray, threshold: float) -> dict[str, Any]:
    by_rec_s: dict[str, list[float]] = defaultdict(list)
    by_rec_y: dict[str, int] = {}
    for m, s in zip(meta_list, scores, strict=True):
        rid = f"{m['class_id']}/{m['source_file']}"
        by_rec_s[rid].append(float(s))
        by_rec_y[rid] = int(m["class_id"])
    rids = sorted(by_rec_s)
    ry = np.array([by_rec_y[r] for r in rids], dtype=np.int64)
    rs = np.array([max(by_rec_s[r]) for r in rids], dtype=np.float64)
    return compute_binary_metrics(ry, rs, threshold)


def run_one_audio_training(
    X_tr_raw: np.ndarray,
    y_tr: np.ndarray,
    meta_tr: list[dict[str, Any]],
    X_va_raw: np.ndarray,
    y_va: np.ndarray,
    meta_va: list[dict[str, Any]],
    X_te_raw: np.ndarray,
    y_te: np.ndarray,
    meta_te: list[dict[str, Any]],
    *,
    seed: int,
    arch: str = "CompactTrainHornCNN",
    dropout: float = 0.30,
    weight_decay: float = 1e-4,
    specaugment: bool = False,
    grad_clip: float | None = None,
    epochs: int = 40,
    patience: int = 10,
    cross_cache: dict[str, Any] | None = None,
    save_ckpt_path: Path | None = None,
) -> dict[str, Any]:
    set_seed(seed)
    device = torch.device("cpu")
    norm_mean = float(np.mean(X_tr_raw))
    norm_std = float(np.std(X_tr_raw))
    if norm_std < 1e-6:
        norm_std = 1.0

    X_tr = (X_tr_raw - norm_mean) / norm_std
    X_va = (X_va_raw - norm_mean) / norm_std
    X_te = (X_te_raw - norm_mean) / norm_std

    if arch == "GroupNormTrainHornCNN":
        model: nn.Module = GroupNormTrainHornCNN(in_channels=1, dropout=dropout).to(device)
    else:
        model = CompactTrainHornCNN(in_channels=1, dropout=dropout).to(device)

    n_pos = max(int(np.sum(y_tr == 1)), 1)
    n_neg = max(int(np.sum(y_tr == 0)), 1)
    pos_weight = torch.tensor([n_neg / n_pos], dtype=torch.float32, device=device)
    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    optimizer = AdamW(model.parameters(), lr=1e-3, weight_decay=weight_decay)
    scheduler = CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-5)

    aug_rng = np.random.default_rng(seed)
    best_val_loss = float("inf")
    best_val_f1 = -1.0
    best_epoch = 1
    best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
    no_imp = 0

    history: dict[str, list[float]] = {
        "train_loss_aug": [],
        "train_acc_clean": [],
        "train_f1_clean": [],
        "val_loss": [],
        "val_acc": [],
        "val_f1": [],
        "val_auc": [],
        "lr": [],
    }

    for ep in range(1, epochs + 1):
        model.train()
        idx = np.arange(len(X_tr))
        np.random.shuffle(idx)
        run_loss = 0.0
        for st in range(0, len(X_tr), 32):
            b_idx = idx[st : st + 32]
            bx = np.stack([apply_v3_aug(X_tr[k], aug_rng, specaugment=specaugment) for k in b_idx], axis=0)
            by = y_tr[b_idx]
            tx = torch.from_numpy(bx).float().unsqueeze(1)
            ty = torch.from_numpy(by).float()
            optimizer.zero_grad()
            logits = model(tx)
            loss = criterion(logits, ty)
            loss.backward()
            if grad_clip is not None:
                nn.utils.clip_grad_norm_(model.parameters(), grad_clip)
            optimizer.step()
            run_loss += float(loss.item()) * len(b_idx)
        scheduler.step()
        lr_now = float(scheduler.get_last_lr()[0])

        model.eval()
        with torch.no_grad():
            tr_probs = torch.sigmoid(model(torch.from_numpy(X_tr).float().unsqueeze(1))).numpy()
            va_logits = model(torch.from_numpy(X_va).float().unsqueeze(1))
            va_loss = float(criterion(va_logits, torch.from_numpy(y_va).float()).item())
            va_probs = torch.sigmoid(va_logits).numpy()

        tr_m = compute_binary_metrics(y_tr, tr_probs, threshold=0.5)
        va_m = compute_binary_metrics(y_va, va_probs, threshold=0.5)

        history["train_loss_aug"].append(round(run_loss / max(len(X_tr), 1), 4))
        history["train_acc_clean"].append(tr_m["accuracy"])
        history["train_f1_clean"].append(tr_m["f1"])
        history["val_loss"].append(round(va_loss, 4))
        history["val_acc"].append(va_m["accuracy"])
        history["val_f1"].append(va_m["f1"])
        history["val_auc"].append(va_m["auc_roc"] if va_m["auc_roc"] is not None else 0.5)
        history["lr"].append(lr_now)

        if va_loss < best_val_loss - 1e-4 or (va_m["f1"] > best_val_f1 and va_loss <= best_val_loss + 0.05):
            best_val_loss = va_loss
            best_val_f1 = va_m["f1"]
            best_epoch = ep
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            no_imp = 0
        else:
            no_imp += 1
            if no_imp >= patience:
                break

    # Final epoch metrics before loading best weights
    model.eval()
    with torch.no_grad():
        final_va_probs = torch.sigmoid(model(torch.from_numpy(X_va).float().unsqueeze(1))).numpy()
        final_te_probs = torch.sigmoid(model(torch.from_numpy(X_te).float().unsqueeze(1))).numpy()
    final_va_m_05 = compute_binary_metrics(y_va, final_va_probs, 0.50)

    # Restore best epoch weights strictly from Val
    model.load_state_dict(best_state)
    model.eval()
    with torch.no_grad():
        tr_probs_best = torch.sigmoid(model(torch.from_numpy(X_tr).float().unsqueeze(1))).numpy()
        va_probs_best = torch.sigmoid(model(torch.from_numpy(X_va).float().unsqueeze(1))).numpy()
        te_probs_best = torch.sigmoid(model(torch.from_numpy(X_te).float().unsqueeze(1))).numpy()

    # Calibrate threshold strictly on validation split
    best_t = 0.50
    best_t_f1 = -1.0
    for t in np.linspace(0.10, 0.90, 81):
        m = compute_binary_metrics(y_va, va_probs_best, float(t))
        if m["f1"] > best_t_f1:
            best_t_f1 = m["f1"]
            best_t = float(round(float(t), 4))

    if save_ckpt_path is not None:
        save_ckpt_path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(
            {
                "epoch": best_epoch,
                "arch": arch,
                "model_state_dict": best_state,
                "norm_mean": norm_mean,
                "norm_std": norm_std,
                "val_loss": best_val_loss,
                "val_f1": best_val_f1,
                "operating_threshold": best_t,
            },
            save_ckpt_path,
        )

    val_spikes = sum(1 for i in range(1, len(history["val_loss"])) if history["val_loss"][i] - history["val_loss"][i - 1] > 0.20)
    res: dict[str, Any] = {
        "seed": seed,
        "arch": arch,
        "params": int(sum(p.numel() for p in model.parameters())),
        "epochs_ran": len(history["val_loss"]),
        "best_epoch": best_epoch,
        "best_val_loss": round(best_val_loss, 4),
        "val_loss_max": max(history["val_loss"]),
        "val_spikes_gt_0p20": int(val_spikes),
        "calibrated_threshold": best_t,
        "norm_mean": round(norm_mean, 4),
        "norm_std": round(norm_std, 4),
        "train_clean_050": compute_binary_metrics(y_tr, tr_probs_best, 0.50),
        "train_clean_cal": compute_binary_metrics(y_tr, tr_probs_best, best_t),
        "val_050": compute_binary_metrics(y_va, va_probs_best, 0.50),
        "val_cal": compute_binary_metrics(y_va, va_probs_best, best_t),
        "test_050": compute_binary_metrics(y_te, te_probs_best, 0.50),
        "test_cal": compute_binary_metrics(y_te, te_probs_best, best_t),
        "test_rec_cal": rec_level_metrics(meta_te, te_probs_best, best_t),
        "final_ep_val_f1_050": final_va_m_05["f1"],
        "final_ep_test_f1_050": compute_binary_metrics(y_te, final_te_probs, 0.50)["f1"],
        "history": history,
    }
    if cross_cache is not None:
        res["crossing_a_eval"] = eval_crossing_a(model, norm_mean, norm_std, best_t, cross_cache)
    return res


def load_partition_arrays(rows: list[dict[str, Any]]) -> tuple[np.ndarray, np.ndarray, list[dict[str, Any]]]:
    feats = [np.load(REPO_ROOT / r["feature_path"]) for r in rows]
    labels = [int(r["class_id"]) for r in rows]
    return np.stack(feats, axis=0).astype(np.float32), np.array(labels, dtype=np.int64), rows


def build_5fold_stem_and_fold_groups(m3: list[dict[str, Any]]) -> list[list[str]]:
    """Return 5 disjoint recording lists grouped strictly by (pos_stem) and (esc50_fold)."""
    by_sid: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in m3:
        by_sid[r["sample_id"]].append(r)

    pos_groups: dict[str, list[str]] = defaultdict(list)
    neg_by_fold: dict[int, list[str]] = defaultdict(list)
    for sid, rlist in sorted(by_sid.items()):
        r0 = rlist[0]
        if r0["class_id"] == 1:
            stem = extract_audio_positive_stem(Path(r0["source_file"]).stem)
            pos_groups[stem].append(sid)
        else:
            fold_str = extract_audio_negative_fold(sid)
            fold_num = int(fold_str.rsplit("_", 1)[-1]) if fold_str.startswith("esc50_fold_") else 1
            neg_by_fold[fold_num].append(sid)

    fold_pos: list[list[str]] = [[] for _ in range(5)]
    counts = [0] * 5
    for _stem, sids in sorted(pos_groups.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        f_idx = min(range(5), key=lambda k: (counts[k], k))
        fold_pos[f_idx].extend(sids)
        counts[f_idx] += len(sids)

    folds: list[list[str]] = []
    for k in range(5):
        folds.append(sorted(fold_pos[k]) + sorted(neg_by_fold[k + 1]))
    return folds


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CKPT_OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("[1/5] Caching and verifying 27 crossing_A field audio spectrograms...", flush=True)
    cross_cache = prepare_or_verify_crossing_audio_cache()
    print(f"   Parity max abs diff vs Mission 11 saved JSONL: {cross_cache['parity_max_abs_diff_vs_mission11']}")

    print("[2/5] Auditing frozen V3 Audio checkpoint (original leaked split + crossing_A)...", flush=True)
    m3 = json.loads(V3_MANIFEST_PATH.read_text(encoding="utf-8"))
    sg = json.loads(V3_STEM_SPLIT_PATH.read_text(encoding="utf-8"))

    orig_parts = {p: [r for r in m3 if r["partition"] == p] for p in ("train", "val", "test")}
    X_o_tr, y_o_tr, m_o_tr = load_partition_arrays(orig_parts["train"])
    X_o_va, y_o_va, m_o_va = load_partition_arrays(orig_parts["val"])
    X_o_te, y_o_te, m_o_te = load_partition_arrays(orig_parts["test"])

    ckpt_v3 = torch.load(V3_FROZEN_CKPT, map_location="cpu", weights_only=False)
    v3_model = CompactTrainHornCNN(in_channels=1, dropout=0.30)
    v3_model.load_state_dict(ckpt_v3["model_state_dict"])
    v3_model.eval()
    v3_mean = float(ckpt_v3["norm_mean"])
    v3_std = float(ckpt_v3["norm_std"])
    v3_thr = float(ckpt_v3["operating_threshold"])

    def _infer(m: nn.Module, X_raw: np.ndarray, mu: float, sd: float) -> np.ndarray:
        xn = (X_raw - mu) / sd
        with torch.no_grad():
            return torch.sigmoid(m(torch.from_numpy(xn).float().unsqueeze(1))).numpy()

    p_o_tr = _infer(v3_model, X_o_tr, v3_mean, v3_std)
    p_o_va = _infer(v3_model, X_o_va, v3_mean, v3_std)
    p_o_te = _infer(v3_model, X_o_te, v3_mean, v3_std)

    # Check consecutive window autocorrelation/cosine similarity (50% overlap leakage structure)
    by_rec_wins: dict[str, list[tuple[int, np.ndarray]]] = defaultdict(list)
    for r in m3:
        by_rec_wins[r["sample_id"]].append((int(r["window_index"]), np.load(REPO_ROOT / r["feature_path"]).flatten()))
    lag1_cos, lag2_cos = [], []
    for wlist in by_rec_wins.values():
        wlist.sort(key=lambda t: t[0])
        vecs = [v for _, v in wlist]
        for i in range(len(vecs) - 1):
            lag1_cos.append(float(np.dot(vecs[i], vecs[i + 1]) / (np.linalg.norm(vecs[i]) * np.linalg.norm(vecs[i + 1]) + 1e-12)))
        for i in range(len(vecs) - 2):
            lag2_cos.append(float(np.dot(vecs[i], vecs[i + 2]) / (np.linalg.norm(vecs[i]) * np.linalg.norm(vecs[i + 2]) + 1e-12)))

    # Leaked vs unseen positive windows in original Val & Test
    tr_stems = {extract_audio_positive_stem(Path(r["source_file"]).stem) for r in m_o_tr if r["class_id"] == 1}
    leak_breakdown = {}
    for s_lbl, meta_sp, p_sp in (("val", m_o_va, p_o_va), ("test", m_o_te, p_o_te)):
        lk_p = [float(p_sp[i]) for i, m in enumerate(meta_sp) if m["class_id"] == 1 and extract_audio_positive_stem(Path(m["source_file"]).stem) in tr_stems]
        un_p = [float(p_sp[i]) for i, m in enumerate(meta_sp) if m["class_id"] == 1 and extract_audio_positive_stem(Path(m["source_file"]).stem) not in tr_stems]
        leak_breakdown[s_lbl] = {
            "leaked_pos_wins_n": len(lk_p),
            "leaked_pos_recall_037": round(sum(1 for x in lk_p if x >= v3_thr) / max(len(lk_p), 1), 4),
            "leaked_pos_mean_prob": round(float(np.mean(lk_p)), 4) if lk_p else None,
            "unseen_pos_wins_n": len(un_p),
            "unseen_pos_recall_037": round(sum(1 for x in un_p if x >= v3_thr) / max(len(un_p), 1), 4),
            "unseen_pos_mean_prob": round(float(np.mean(un_p)), 4) if un_p else None,
        }

    # Test category breakdown & false negatives/positives
    cat_te = defaultdict(lambda: {"n": 0, "fp_037": 0, "fp_050": 0, "probs": []})
    for i, m in enumerate(m_o_te):
        cat = m.get("category", "train_horn")
        pr = float(p_o_te[i])
        cat_te[cat]["n"] += 1
        cat_te[cat]["probs"].append(pr)
        if m["class_id"] == 0 and pr >= v3_thr:
            cat_te[cat]["fp_037"] += 1
        if m["class_id"] == 0 and pr >= 0.50:
            cat_te[cat]["fp_050"] += 1

    frozen_v3_audit = {
        "checkpoint_path": str(V3_FROZEN_CKPT.relative_to(REPO_ROOT)),
        "checkpoint_sha256": compute_file_sha256(V3_FROZEN_CKPT),
        "best_epoch": int(ckpt_v3["epoch"]),
        "threshold": v3_thr,
        "window_overlap_cosine_similarity": {
            "lag1_0p5s_mean": round(float(np.mean(lag1_cos)), 4),
            "lag2_1p0s_mean": round(float(np.mean(lag2_cos)), 4),
        },
        "train_unaug_037": compute_binary_metrics(y_o_tr, p_o_tr, v3_thr),
        "val_037": compute_binary_metrics(y_o_va, p_o_va, v3_thr),
        "test_037": compute_binary_metrics(y_o_te, p_o_te, v3_thr),
        "test_050": compute_binary_metrics(y_o_te, p_o_te, 0.50),
        "test_rec_037": rec_level_metrics(m_o_te, p_o_te, v3_thr),
        "leaked_vs_unseen_stem_positives": leak_breakdown,
        "test_by_category": {
            c: {
                "n_wins": v["n"],
                "fp_037": v["fp_037"],
                "fp_050": v["fp_050"],
                "mean_p": round(float(np.mean(v["probs"])), 4),
                "max_p": round(float(np.max(v["probs"])), 4),
            }
            for c, v in sorted(cat_te.items())
        },
        "crossing_a_external": eval_crossing_a(v3_model, v3_mean, v3_std, v3_thr, cross_cache),
        "raw_test_scores_sample": {
            "test_labels": y_o_te.tolist(),
            "test_probs": [round(float(x), 5) for x in p_o_te],
        },
    }

    print("[3/5] Running leakage-free multi-seed stem-grouped retrains & ablations...", flush=True)
    sg_sets = {p: set(sg["partitions"][p]["recordings"]) for p in ("train", "val", "test")}
    sg_parts = {p: [r for r in m3 if r["sample_id"] in sg_sets[p]] for p in ("train", "val", "test")}
    X_s_tr, y_s_tr, m_s_tr = load_partition_arrays(sg_parts["train"])
    X_s_va, y_s_va, m_s_va = load_partition_arrays(sg_parts["val"])
    X_s_te, y_s_te, m_s_te = load_partition_arrays(sg_parts["test"])

    seeds = [42, 101, 202, 303, 404]
    configs = {
        "stem_grouped_v3_recipe": {"arch": "CompactTrainHornCNN", "dropout": 0.30, "weight_decay": 1e-4, "specaugment": False, "grad_clip": None, "patience": 10},
        "stem_grouped_specaug_strongreg": {"arch": "CompactTrainHornCNN", "dropout": 0.45, "weight_decay": 1e-3, "specaugment": True, "grad_clip": 1.0, "patience": 15},
        "stem_grouped_groupnorm_specaug": {"arch": "GroupNormTrainHornCNN", "dropout": 0.40, "weight_decay": 1e-3, "specaugment": True, "grad_clip": 1.0, "patience": 15},
    }
    ablation_results: dict[str, Any] = {}
    for cfg_name, cfg in configs.items():
        runs = []
        for s in seeds:
            ckpt_p = CKPT_OUT_DIR / f"{cfg_name}_seed{s}.pt" if s == 42 else None
            r = run_one_audio_training(
                X_s_tr, y_s_tr, m_s_tr,
                X_s_va, y_s_va, m_s_va,
                X_s_te, y_s_te, m_s_te,
                seed=s,
                arch=cfg["arch"],
                dropout=cfg["dropout"],
                weight_decay=cfg["weight_decay"],
                specaugment=cfg["specaugment"],
                grad_clip=cfg["grad_clip"],
                patience=cfg["patience"],
                cross_cache=cross_cache,
                save_ckpt_path=ckpt_p,
            )
            runs.append(r)

        def _agg(vals: list[float]) -> dict[str, float]:
            arr = np.array(vals, dtype=np.float64)
            return {"mean": round(float(arr.mean()), 4), "std": round(float(arr.std(ddof=1)), 4) if len(arr) > 1 else 0.0, "min": round(float(arr.min()), 4), "max": round(float(arr.max()), 4)}

        ablation_results[cfg_name] = {
            "config": cfg,
            "aggregate_5seeds": {
                "train_clean_f1_050": _agg([x["train_clean_050"]["f1"] for x in runs]),
                "val_f1_cal": _agg([x["val_cal"]["f1"] for x in runs]),
                "test_f1_cal": _agg([x["test_cal"]["f1"] for x in runs]),
                "test_f1_050": _agg([x["test_050"]["f1"] for x in runs]),
                "test_roc_auc": _agg([x["test_cal"]["auc_roc"] for x in runs]),
                "test_pr_auc": _agg([x["test_cal"]["pr_auc"] for x in runs]),
                "test_specificity_cal": _agg([x["test_cal"]["specificity"] for x in runs]),
                "test_rec_f1_cal": _agg([x["test_rec_cal"]["f1"] for x in runs]),
                "val_spikes_gt_0p20": _agg([float(x["val_spikes_gt_0p20"]) for x in runs]),
                "crossing_a_rec_26_pr_auc": _agg([x["crossing_a_eval"]["recording_26_tau_metrics"]["pr_auc"] for x in runs]),
                "crossing_a_no_train_fp_tau": _agg([float(x["crossing_a_eval"]["no_train_3_fp_tau"]) for x in runs]),
                "crossing_a_horn_present_tp_075k2": _agg([float(x["crossing_a_eval"]["horn_present_13_tp_075k2"]) for x in runs]),
            },
            "seed42_detail": runs[0],
            "all_seed_summaries": [
                {k: v for k, v in r.items() if k != "history"}
                for r in runs
            ],
        }
        print(
            f"   {cfg_name}: Test F1(cal)={ablation_results[cfg_name]['aggregate_5seeds']['test_f1_cal']['mean']:.4f}"
            f"+-{ablation_results[cfg_name]['aggregate_5seeds']['test_f1_cal']['std']:.4f}, "
            f"PR-AUC={ablation_results[cfg_name]['aggregate_5seeds']['test_pr_auc']['mean']:.4f}, "
            f"Spikes={ablation_results[cfg_name]['aggregate_5seeds']['val_spikes_gt_0p20']['mean']:.1f}, "
            f"X_A PR-AUC={ablation_results[cfg_name]['aggregate_5seeds']['crossing_a_rec_26_pr_auc']['mean']:.4f}",
            flush=True,
        )

    print("[4/5] Running 5-fold strict stem+fold grouped CV...", flush=True)
    folds = build_5fold_stem_and_fold_groups(m3)
    by_sid = defaultdict(list)
    for r in m3:
        by_sid[r["sample_id"]].append(r)

    cv_results: dict[str, Any] = {}
    for cfg_name in ("stem_grouped_v3_recipe", "stem_grouped_groupnorm_specaug"):
        cfg = configs[cfg_name]
        fold_metrics = []
        for f_test_idx in range(5):
            f_val_idx = (f_test_idx + 4) % 5
            te_sids = set(folds[f_test_idx])
            va_sids = set(folds[f_val_idx])
            tr_rows, va_rows, te_rows = [], [], []
            for sid, rows in sorted(by_sid.items()):
                if sid in te_sids:
                    te_rows.extend(rows)
                elif sid in va_sids:
                    va_rows.extend(rows)
                else:
                    tr_rows.extend(rows)
            Xt, yt, mt = load_partition_arrays(tr_rows)
            Xv, yv, mv = load_partition_arrays(va_rows)
            Xe, ye, me = load_partition_arrays(te_rows)
            rr = run_one_audio_training(
                Xt, yt, mt, Xv, yv, mv, Xe, ye, me,
                seed=42 + f_test_idx,
                arch=cfg["arch"],
                dropout=cfg["dropout"],
                weight_decay=cfg["weight_decay"],
                specaugment=cfg["specaugment"],
                grad_clip=cfg["grad_clip"],
                patience=cfg["patience"],
            )
            fold_metrics.append({
                "fold": f_test_idx + 1,
                "n_test_recs": len(te_sids),
                "n_test_wins": len(te_rows),
                "test_f1_cal": rr["test_cal"]["f1"],
                "test_roc_auc": rr["test_cal"]["auc_roc"],
                "test_pr_auc": rr["test_cal"]["pr_auc"],
                "test_specificity_cal": rr["test_cal"]["specificity"],
                "test_rec_f1_cal": rr["test_rec_cal"]["f1"],
            })
        cv_results[cfg_name] = {
            "folds": fold_metrics,
            "mean_test_f1_cal": round(float(np.mean([f["test_f1_cal"] for f in fold_metrics])), 4),
            "std_test_f1_cal": round(float(np.std([f["test_f1_cal"] for f in fold_metrics], ddof=1)), 4),
            "mean_test_pr_auc": round(float(np.mean([f["test_pr_auc"] for f in fold_metrics])), 4),
            "mean_test_roc_auc": round(float(np.mean([f["test_roc_auc"] for f in fold_metrics])), 4),
            "mean_test_rec_f1_cal": round(float(np.mean([f["test_rec_f1_cal"] for f in fold_metrics])), 4),
        }
        print(f"   5-fold CV {cfg_name}: Test F1={cv_results[cfg_name]['mean_test_f1_cal']:.4f}+-{cv_results[cfg_name]['std_test_f1_cal']:.4f}, PR-AUC={cv_results[cfg_name]['mean_test_pr_auc']:.4f}", flush=True)

    print("[5/5] Running sample-size learning curve (20%, 40%, 60%, 80%, 100% of clean train clusters)...", flush=True)
    # Cluster training groups strictly by (positive_stem or recording_id)
    tr_clusters: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in sg_parts["train"]:
        key = f"pos::{extract_audio_positive_stem(Path(r['source_file']).stem)}" if r["class_id"] == 1 else f"neg::{r['sample_id']}"
        tr_clusters[key].append(r)
    pos_keys = sorted(k for k in tr_clusters if k.startswith("pos::"))
    neg_keys = sorted(k for k in tr_clusters if k.startswith("neg::"))

    learning_curve = []
    for frac in (0.20, 0.40, 0.60, 0.80, 1.00):
        sub_runs = []
        for s_off in (0, 1, 2):
            rng_lc = random.Random(1000 + int(frac * 100) + s_off)
            pk = list(pos_keys)
            nk = list(neg_keys)
            rng_lc.shuffle(pk)
            rng_lc.shuffle(nk)
            sel_pk = pk[: max(2, int(round(frac * len(pk))))]
            sel_nk = nk[: max(2, int(round(frac * len(nk))))]
            sub_rows = [r for k in (sel_pk + sel_nk) for r in tr_clusters[k]]
            Xsub, ysub, msub = load_partition_arrays(sub_rows)
            rr = run_one_audio_training(
                Xsub, ysub, msub,
                X_s_va, y_s_va, m_s_va,
                X_s_te, y_s_te, m_s_te,
                seed=42 + s_off,
                arch="CompactTrainHornCNN",
                dropout=0.30,
                weight_decay=1e-4,
                specaugment=False,
            )
            sub_runs.append(rr)
        learning_curve.append({
            "fraction": frac,
            "mean_train_windows": round(float(np.mean([r["train_clean_050"]["n"] for r in sub_runs])), 1),
            "train_f1_mean": round(float(np.mean([r["train_clean_050"]["f1"] for r in sub_runs])), 4),
            "val_f1_mean": round(float(np.mean([r["val_cal"]["f1"] for r in sub_runs])), 4),
            "test_f1_mean": round(float(np.mean([r["test_cal"]["f1"] for r in sub_runs])), 4),
            "test_f1_std": round(float(np.std([r["test_cal"]["f1"] for r in sub_runs], ddof=1)), 4),
            "test_pr_auc_mean": round(float(np.mean([r["test_cal"]["pr_auc"] for r in sub_runs])), 4),
        })
        print(f"   LC frac={frac:.0%}: Tr F1={learning_curve[-1]['train_f1_mean']:.4f}, Val F1={learning_curve[-1]['val_f1_mean']:.4f}, Test F1={learning_curve[-1]['test_f1_mean']:.4f}+-{learning_curve[-1]['test_f1_std']:.4f}", flush=True)

    summary = {
        "schema_version": "mission13-audio-audit/1.0",
        "generated_at_utc": dt.datetime.now(dt.UTC).isoformat(),
        "v1_v2_v3_historical_histories": {
            "v1_metrics_path": str(V1_HIST_PATH.relative_to(REPO_ROOT)),
            "v2_metrics_path": str(V2_HIST_PATH.relative_to(REPO_ROOT)),
            "v3_metrics_path": str(V3_METRICS_PATH.relative_to(REPO_ROOT)),
        },
        "frozen_v3_audit": frozen_v3_audit,
        "stem_grouped_split_counts": {
            sp: {"n_recs": len(sg_sets[sp]), "n_wins": len(sg_parts[sp]), "n_pos_wins": sum(1 for r in sg_parts[sp] if r["class_id"] == 1), "n_neg_wins": sum(1 for r in sg_parts[sp] if r["class_id"] == 0)}
            for sp in ("train", "val", "test")
        },
        "stem_grouped_ablations": ablation_results,
        "grouped_5fold_cv": cv_results,
        "learning_curve": learning_curve,
    }
    out_path = OUT_DIR / "audio_audit_summary.json"
    out_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print("WROTE:", out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
