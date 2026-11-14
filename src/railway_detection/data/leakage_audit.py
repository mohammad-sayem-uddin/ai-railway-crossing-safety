"""Non-destructive leakage auditing and session/stem-grouped split builders.

Reads only plain-text manifests, metadata, and existing split JSON/JSONL files;
never opens, decodes, or hashes raw media files under ``data/raw/``.
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

VISION_TS_PATTERNS: tuple[tuple[str, re.Pattern[str], str], ...] = (
    ("Screenshot", re.compile(r"^Screenshot-(\d{4}-\d{2}-\d{2}-at-\d{2}-\d{2}-\d{2})"), "%Y-%m-%d-at-%H-%M-%S"),
    ("IMG", re.compile(r"^IMG_(\d{8}_\d{6})"), "%Y%m%d_%H%M%S"),
    ("image", re.compile(r"^image-(\d{4}-\d{2}-\d{2}T\d{6})"), "%Y-%m-%dT%H%M%S"),
)
_EPOCH_MS_RE = re.compile(r"^17\d{11}_jpg$")
_ESC50_NEG_RE = re.compile(r"^(?:esc50_|neg_)([1-5])-\d+-[A-Z]-\d+$")


def parse_vision_source_timestamp(split_group_id: str) -> tuple[float | None, str]:
    """Extract capture epoch timestamp (UTC) and filename pattern kind if encoded."""
    stem = split_group_id.removeprefix("source:")
    for kind, pattern, fmt in VISION_TS_PATTERNS:
        match = pattern.match(stem)
        if match:
            dt = datetime.strptime(match.group(1), fmt).replace(tzinfo=UTC)
            return dt.timestamp(), kind
    if _EPOCH_MS_RE.match(stem):
        epoch_ms = int(stem.split("_", 1)[0])
        return epoch_ms / 1000.0, "epoch_ms"
    return None, "unparsed"


def assign_vision_capture_sessions(
    manifest_rows: list[dict[str, Any]],
    *,
    gap_s: float = 600.0,
) -> dict[str, str]:
    """Cluster each unique ``split_group_id`` into atomic capture sessions.

    Timestamped sources separated by at most ``gap_s`` seconds share one session ID
    (``session_NNN``). Unparsed sources retain isolated per-source IDs
    (``unparsed::<split_group_id>``) so augmented copies stay atomic.
    """
    unique_gids = sorted({row["split_group_id"] for row in manifest_rows})
    timestamped: list[tuple[float, str]] = []
    mapping: dict[str, str] = {}
    for gid in unique_gids:
        ts, _ = parse_vision_source_timestamp(gid)
        if ts is None:
            mapping[gid] = f"unparsed::{gid}"
        else:
            timestamped.append((ts, gid))
    timestamped.sort(key=lambda item: (item[0], item[1]))
    if not timestamped:
        return mapping

    session_idx = 0
    prev_ts = timestamped[0][0]
    for ts, gid in timestamped:
        if ts - prev_ts > gap_s:
            session_idx += 1
        mapping[gid] = f"session_{session_idx:03d}"
        prev_ts = ts
    return mapping


def audit_vision_partition(
    manifest_rows: list[dict[str, Any]],
    split_by_image_id: dict[str, str],
    *,
    gap_sweeps_s: tuple[float, ...] = (120.0, 300.0, 600.0, 1800.0, 3600.0),
) -> dict[str, Any]:
    """Audit source-group, augmentation, and temporal session leakage for a vision split."""
    splits = ("train", "val", "test")
    img_counts = {sp: 0 for sp in splits}
    unique_groups: dict[str, set[str]] = {sp: set() for sp in splits}
    rf_origins: dict[str, Counter[str]] = {sp: Counter() for sp in splits}
    class_boxes: dict[str, Counter[str]] = {sp: Counter() for sp in splits}
    gid_splits: dict[str, set[str]] = defaultdict(set)

    for row in manifest_rows:
        img_id = row["image_id"]
        if img_id not in split_by_image_id:
            continue
        sp = split_by_image_id[img_id]
        gid = row["split_group_id"]
        img_counts[sp] += 1
        unique_groups[sp].add(gid)
        gid_splits[gid].add(sp)
        rf_origins[sp][row.get("provenance", {}).get("split_dir", "unknown")] += 1
        for ann in row.get("annotations", ()):
            class_boxes[sp][ann["label"]] += 1

    multi_split_groups = sorted(g for g, sps in gid_splits.items() if len(sps) > 1)
    session_sweeps: list[dict[str, Any]] = []
    for gap in gap_sweeps_s:
        sess_map = assign_vision_capture_sessions(manifest_rows, gap_s=gap)
        sess_splits: dict[str, set[str]] = defaultdict(set)
        train_sessions: set[str] = set()
        for row in manifest_rows:
            img_id = row["image_id"]
            if img_id not in split_by_image_id:
                continue
            sp = split_by_image_id[img_id]
            sess_id = sess_map[row["split_group_id"]]
            sess_splits[sess_id].add(sp)
            if sp == "train":
                train_sessions.add(sess_id)
        ts_sessions = {s for s in sess_splits if s.startswith("session_")}
        crossing_ts = sorted(s for s in ts_sessions if len(sess_splits[s]) > 1)
        test_ts_total = 0
        test_ts_leaked = 0
        val_ts_total = 0
        val_ts_leaked = 0
        for row in manifest_rows:
            img_id = row["image_id"]
            if img_id not in split_by_image_id:
                continue
            sp = split_by_image_id[img_id]
            sess_id = sess_map[row["split_group_id"]]
            if not sess_id.startswith("session_"):
                continue
            if sp == "test":
                test_ts_total += 1
                if sess_id in train_sessions:
                    test_ts_leaked += 1
            elif sp == "val":
                val_ts_total += 1
                if sess_id in train_sessions:
                    val_ts_leaked += 1
        session_sweeps.append(
            {
                "gap_s": gap,
                "timestamped_session_count": len(ts_sessions),
                "crossing_timestamped_sessions": len(crossing_ts),
                "test_timestamped_imgs_total": test_ts_total,
                "test_timestamped_imgs_sharing_session_with_train": test_ts_leaked,
                "val_timestamped_imgs_total": val_ts_total,
                "val_timestamped_imgs_sharing_session_with_train": val_ts_leaked,
            }
        )

    return {
        "split_image_counts": img_counts,
        "unique_source_counts": {sp: len(unique_groups[sp]) for sp in splits},
        "multi_split_source_group_count": len(multi_split_groups),
        "rf_origin_by_split": {sp: dict(sorted(rf_origins[sp].items())) for sp in splits},
        "class_boxes_by_split": {sp: dict(sorted(class_boxes[sp].items())) for sp in splits},
        "temporal_session_sweeps": session_sweeps,
    }


def _select_canonical_image_for_eval(group_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Select one unaugmented representative per ``split_group_id`` for val/test."""
    priority = {"test": 0, "valid": 1, "train": 2}
    return sorted(
        group_rows,
        key=lambda r: (
            priority.get(r.get("provenance", {}).get("split_dir", "train"), 9),
            r["image_id"],
        ),
    )[0]


def build_session_grouped_vision_split(
    manifest_rows: list[dict[str, Any]],
    *,
    gap_s: float = 600.0,
    ratios: tuple[float, float, float] = (0.70, 0.15, 0.15),
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    """Build a leakage-free session-grouped Vision V1 split.

    Guarantees:
    - Every ``gap_s`` timestamp session (and every unparsed source group) is assigned
      atomically to exactly one partition among ``train``, ``val``, and ``test``.
    - ``val`` and ``test`` keep exactly 1 canonical image per ``split_group_id`` to
      eliminate Roboflow 3x offline-augmentation duplication during evaluation; ``train``
      retains all rows belonging to training sessions.
    - Partitioning uses deterministic stratified greedy bin-packing over session
      source counts and rare-class (``rear``, ``side``) counts.
    """
    sess_map = assign_vision_capture_sessions(manifest_rows, gap_s=gap_s)
    rows_by_gid: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in manifest_rows:
        rows_by_gid[row["split_group_id"]].append(row)

    sessions_gids: dict[str, list[str]] = defaultdict(list)
    for gid in sorted(rows_by_gid):
        sessions_gids[sess_map[gid]].append(gid)

    # Aggregate unique-source & box statistics per atomic session cluster.
    clusters: list[dict[str, Any]] = []
    tot_sources = len(rows_by_gid)
    tot_cls: Counter[str] = Counter()
    for sess_id, gids in sorted(sessions_gids.items()):
        cls_counts: Counter[str] = Counter()
        for gid in gids:
            canon = _select_canonical_image_for_eval(rows_by_gid[gid])
            for ann in canon.get("annotations", ()):
                cls_counts[ann["label"]] += 1
                tot_cls[ann["label"]] += 1
        clusters.append(
            {
                "session_id": sess_id,
                "gids": gids,
                "n_sources": len(gids),
                "n_rear": cls_counts.get("rear", 0),
                "n_side": cls_counts.get("side", 0),
                "n_front": cls_counts.get("front", 0),
            }
        )

    # Sort largest / rarest-class sessions first for balanced deterministic packing.
    clusters.sort(key=lambda c: (-c["n_sources"], -c["n_rear"], -c["n_side"], c["session_id"]))
    splits = ("train", "val", "test")
    target_sources = {sp: ratios[i] * tot_sources for i, sp in enumerate(splits)}
    target_rear = {sp: ratios[i] * tot_cls.get("rear", 0) for i, sp in enumerate(splits)}
    target_side = {sp: ratios[i] * tot_cls.get("side", 0) for i, sp in enumerate(splits)}

    cur_sources = {sp: 0.0 for sp in splits}
    cur_rear = {sp: 0.0 for sp in splits}
    cur_side = {sp: 0.0 for sp in splits}
    sess_assignment: dict[str, str] = {}

    for c in clusters:
        best_sp = "train"
        best_cost = float("inf")
        for sp in splits:
            src_err = ((cur_sources[sp] + c["n_sources"] - target_sources[sp]) / max(target_sources[sp], 1.0)) ** 2
            rear_err = ((cur_rear[sp] + c["n_rear"] - target_rear[sp]) / max(target_rear[sp], 1.0)) ** 2
            side_err = ((cur_side[sp] + c["n_side"] - target_side[sp]) / max(target_side[sp], 1.0)) ** 2
            other_err = 0.0
            for osp in splits:
                if osp != sp:
                    other_err += ((cur_sources[osp] - target_sources[osp]) / max(target_sources[osp], 1.0)) ** 2
            cost = 2.0 * src_err + 1.5 * rear_err + 1.0 * side_err + 0.5 * other_err
            if cost < best_cost:
                best_cost = cost
                best_sp = sp
        sess_assignment[c["session_id"]] = best_sp
        cur_sources[best_sp] += c["n_sources"]
        cur_rear[best_sp] += c["n_rear"]
        cur_side[best_sp] += c["n_side"]

    split_records: dict[str, list[dict[str, Any]]] = {sp: [] for sp in splits}
    split_by_img_id: dict[str, str] = {}
    excluded_eval_aug_duplicates = 0

    for sess_id, gids in sorted(sessions_gids.items()):
        sp = sess_assignment[sess_id]
        for gid in gids:
            g_rows = sorted(rows_by_gid[gid], key=lambda r: r["image_id"])
            if sp == "train":
                for r in g_rows:
                    split_records["train"].append({"sample_id": r["image_id"], "session_id": sess_id})
                    split_by_img_id[r["image_id"]] = "train"
            else:
                canon = _select_canonical_image_for_eval(g_rows)
                split_records[sp].append({"sample_id": canon["image_id"], "session_id": sess_id})
                split_by_img_id[canon["image_id"]] = sp
                excluded_eval_aug_duplicates += len(g_rows) - 1

    audit = audit_vision_partition(manifest_rows, split_by_img_id)
    summary = {
        "schema_version": "vision-session-grouped-split/1.0",
        "gap_s": gap_s,
        "target_ratios": {"train": ratios[0], "val": ratios[1], "test": ratios[2]},
        "total_manifest_images": len(manifest_rows),
        "total_unique_sources": tot_sources,
        "excluded_eval_augmentation_duplicates": excluded_eval_aug_duplicates,
        "eval_canonical_only": True,
        "audit": audit,
        "session_assignments": dict(sorted(sess_assignment.items())),
    }
    return split_records, summary


def extract_audio_positive_stem(recording_id: str) -> str:
    """Normalize a positive audio recording ID to its underlying source stem."""
    raw = recording_id.removeprefix("pos_").strip()
    # Strip multi-segment bitrate/chunk suffixes like " - 128", " - 128-3", or "-128-12"
    stem = re.sub(r"\s*-\s*128(?:[-_]\d+)?$", "", raw)
    # Also group duplicate copy suffixes like "19(1)" with "19"
    stem = re.sub(r"\(\d+\)$", "", stem)
    stem = re.sub(r"\s+", " ", stem).strip()
    return stem


def extract_audio_negative_fold(recording_id: str) -> str:
    """Extract the ESC-50 fold identifier (``1``..``5``) from a negative clip ID."""
    match = _ESC50_NEG_RE.match(recording_id)
    if match:
        return f"esc50_fold_{match.group(1)}"
    return f"other::{recording_id}"


def audit_audio_split(split_payload: dict[str, Any]) -> dict[str, Any]:
    """Audit positive YouTube stem leakage and ESC-50 fold isolation in an audio split."""
    partitions = split_payload["partitions"]
    pos_stems: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    neg_folds: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    counts: dict[str, dict[str, int]] = {}

    for sp in ("train", "val", "test"):
        recs = partitions[sp]["recordings"]
        pos_n = 0
        neg_n = 0
        for rec in recs:
            if rec.startswith("pos_"):
                pos_n += 1
                pos_stems[extract_audio_positive_stem(rec)][sp] += 1
            else:
                neg_n += 1
                neg_folds[extract_audio_negative_fold(rec)][sp] += 1
        counts[sp] = {"positive": pos_n, "negative": neg_n, "total": pos_n + neg_n}

    leaked_stems = {st: dict(c) for st, c in sorted(pos_stems.items()) if len(c) > 1}
    leaked_pos_recs = sum(sum(c.values()) for c in leaked_stems.values())
    total_pos = sum(counts[sp]["positive"] for sp in counts)
    leaked_neg_folds = {f: dict(c) for f, c in sorted(neg_folds.items()) if len(c) > 1}

    return {
        "counts_by_split": counts,
        "unique_positive_stems": len(pos_stems),
        "cross_split_positive_stem_count": len(leaked_stems),
        "positive_recordings_in_cross_split_stems": leaked_pos_recs,
        "positive_recording_stem_leakage_fraction": (
            round(leaked_pos_recs / total_pos, 4) if total_pos else 0.0
        ),
        "cross_split_positive_stems": leaked_stems,
        "unique_negative_folds": len(neg_folds),
        "cross_split_negative_fold_count": len(leaked_neg_folds),
        "cross_split_negative_folds": leaked_neg_folds,
    }


def build_stem_grouped_audio_split(
    v3_split_payload: dict[str, Any],
    *,
    ratios: tuple[float, float, float] = (0.70, 0.15, 0.15),
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Construct a zero-stem-leakage, zero-ESC50-fold-leakage Audio V3 candidate split."""
    all_pos: list[str] = []
    all_neg: list[str] = []
    for sp in ("train", "val", "test"):
        for rec in v3_split_payload["partitions"][sp]["recordings"]:
            if rec.startswith("pos_"):
                all_pos.append(rec)
            else:
                all_neg.append(rec)

    pos_groups: dict[str, list[str]] = defaultdict(list)
    for rec in sorted(all_pos):
        pos_groups[extract_audio_positive_stem(rec)].append(rec)

    # Preserve standard ESC-50 fold isolation: folds 1-3 -> train, fold 4 -> val, fold 5 -> test.
    fold_target = {
        "esc50_fold_1": "train",
        "esc50_fold_2": "train",
        "esc50_fold_3": "train",
        "esc50_fold_4": "val",
        "esc50_fold_5": "test",
    }
    neg_by_split: dict[str, list[str]] = {"train": [], "val": [], "test": []}
    for rec in sorted(all_neg):
        sp = fold_target.get(extract_audio_negative_fold(rec), "train")
        neg_by_split[sp].append(rec)

    # Balance positives strictly by atomic stem cluster toward target counts (~70/15/15).
    splits = ("train", "val", "test")
    total_pos = len(all_pos)
    target_pos = {"train": ratios[0] * total_pos, "val": len(neg_by_split["val"]), "test": len(neg_by_split["test"])}
    if target_pos["val"] == 0:
        target_pos["val"] = ratios[1] * total_pos
    if target_pos["test"] == 0:
        target_pos["test"] = ratios[2] * total_pos
    target_pos["train"] = float(total_pos) - target_pos["val"] - target_pos["test"]

    cur_pos = {sp: 0 for sp in splits}
    pos_by_split: dict[str, list[str]] = {sp: [] for sp in splits}

    # Place largest stems first; multi-segment stems naturally assign to train first while
    # single-clip stems fill val/test up to exact class balance with ESC-50 fold negatives.
    stem_items = sorted(pos_groups.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    for stem, recs in stem_items:
        best_sp = min(
            splits,
            key=lambda sp: (
                0 if cur_pos[sp] + len(recs) <= target_pos[sp] + 0.5 else 1,
                ((cur_pos[sp] + len(recs) - target_pos[sp]) / max(target_pos[sp], 1.0)) ** 2,
                abs(cur_pos[sp] + len(recs) - target_pos[sp]),
                sp,
            ),
        )
        pos_by_split[best_sp].extend(recs)
        cur_pos[best_sp] += len(recs)

    new_partitions: dict[str, Any] = {}
    for sp in splits:
        combined = sorted(pos_by_split[sp]) + sorted(neg_by_split[sp])
        new_partitions[sp] = {
            "positive_count": len(pos_by_split[sp]),
            "negative_count": len(neg_by_split[sp]),
            "total_count": len(combined),
            "recordings": combined,
        }

    new_payload = {
        "experiment": "audio_v3_stem_grouped_leakage_free",
        "seed": "deterministic_stem_grouped",
        "split_ratio": {"train": ratios[0], "val": ratios[1], "test": ratios[2]},
        "partitions": new_partitions,
    }
    summary = {
        "schema_version": "audio-stem-grouped-split/1.0",
        "audit_original_v3": audit_audio_split(v3_split_payload),
        "audit_stem_grouped": audit_audio_split(new_payload),
    }
    return new_payload, summary
