#!/usr/bin/env python3
"""
Audio Model V3: Positive and ESC-50 Negative Dataset Selection and Manifest Generation.

Enforces:
1. All 86 verified unique positive recordings from own train-horn pool.
2. Bitwise duplicate identification (41.mp3 == 42.mp3, keeping 41.mp3, rejecting 42.mp3).
3. Selection of exactly 86 unique ESC-50 negative recordings across 11 acoustic confusers.
4. Absolute exclusion of ESC-50 'train' category.
5. Strict fold-based partitioning (Folds 1-3 -> Train, Fold 4 -> Val, Fold 5 -> Test)
   guaranteeing ZERO source-file leakage across partitions.
6. Hard firewalls asserting ZERO files from custom negative pool or Layer B videos.
"""
from __future__ import annotations

import csv
import hashlib
import json
import random
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from railway_detection.safety.media_guard import require_media_authorization  # noqa: E402

WORKSPACE = Path("/Users/sayemuddin/Desktop/Train_automation")
POSITIVE_DIR = WORKSPACE / "data/raw/audio/train_horn/positive"
OLD_NEGATIVE_DIR = WORKSPACE / "data/raw/audio/train_horn/negative"
LAYER_B_DIR = WORKSPACE / "data/raw/layer_b"
ESC50_DIR = WORKSPACE / "ESC-50-master"
ESC50_CSV = ESC50_DIR / "meta/esc50.csv"
ESC50_AUDIO = ESC50_DIR / "audio"

MANIFESTS_DIR = WORKSPACE / "data/manifests"
SPLITS_DIR = WORKSPACE / "data/splits/audio/v3"

MANIFESTS_DIR.mkdir(parents=True, exist_ok=True)
SPLITS_DIR.mkdir(parents=True, exist_ok=True)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    require_media_authorization(path, "HASH_RAW_MEDIA")
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def probe_audio(path: Path) -> dict[str, Any]:
    require_media_authorization(path, "MEDIA_PROBE")
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration,size,bit_rate,format_name:stream=codec_name,sample_rate,channels",
        "-of", "json",
        str(path)
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)
        fmt = data.get("format", {})
        streams = data.get("streams", [{}])
        astream = streams[0] if streams else {}
        return {
            "duration": float(fmt.get("duration", 0.0)),
            "size_bytes": int(fmt.get("size", 0)),
            "codec": astream.get("codec_name", "unknown"),
            "sample_rate": int(astream.get("sample_rate", 0)),
            "channels": int(astream.get("channels", 0)),
        }
    except Exception as e:
        return {
            "duration": 0.0,
            "size_bytes": path.stat().st_size if path.exists() else 0,
            "codec": "error",
            "sample_rate": 0,
            "channels": 0,
            "error": str(e)
        }


def main() -> None:
    print("=" * 60)
    print("AUDIO V3: POSITIVE & ESC-50 NEGATIVE SELECTION & MANIFESTS")
    print("=" * 60)

    # 1. Collect all custom negative MP3 hashes for FIREWALL verification
    custom_neg_hashes = set()
    custom_neg_files = set()
    if OLD_NEGATIVE_DIR.exists():
        for f in OLD_NEGATIVE_DIR.iterdir():
            if f.is_file() and f.suffix.lower() == ".mp3" and not f.name.startswith("."):
                custom_neg_files.add(f.name)
                custom_neg_hashes.add(sha256_file(f))
    print(f"Firewall: Found {len(custom_neg_hashes)} unique SHA-256 hashes in custom negative MP3 pool to block.")

    # 2. Collect Layer B video hashes for FIREWALL verification
    layer_b_hashes = set()
    if LAYER_B_DIR.exists():
        for f in LAYER_B_DIR.rglob("*"):
            if f.is_file() and not f.name.startswith("."):
                layer_b_hashes.add(sha256_file(f))
    print(f"Firewall: Found {len(layer_b_hashes)} Layer B file hashes to block.")

    # 3. Audit Positive Audio
    pos_files = sorted([f for f in POSITIVE_DIR.iterdir() if f.is_file() and not f.name.startswith(".")])
    print(f"Total positive physical files in {POSITIVE_DIR.name}: {len(pos_files)}")

    pos_by_hash = defaultdict(list)
    for p in pos_files:
        # Ignore symlinks or pdf artifacts
        if p.is_symlink() or p.suffix.lower() == ".pdf":
            continue
        h = sha256_file(p)
        pos_by_hash[h].append(p)

    print(f"Total unique positive audio recordings: {len(pos_by_hash)}")

    selected_positives = []
    rejected_positives = []

    for h, files in pos_by_hash.items():
        # Assert firewall
        assert h not in custom_neg_hashes, f"FIREWALL VIOLATION: positive {files[0]} found in custom negative pool!"
        assert h not in layer_b_hashes, f"FIREWALL VIOLATION: positive {files[0]} found in Layer B pool!"
        assert not str(files[0]).startswith(str(OLD_NEGATIVE_DIR)), "FIREWALL VIOLATION: Positive source in old negative dir!"

        # Pick primary file (lowest filename alphabetically e.g. 41.mp3 over 42.mp3)
        files_sorted = sorted(files, key=lambda x: x.name)
        primary = files_sorted[0]
        meta = probe_audio(primary)

        rec = {
            "sample_id": f"pos_{primary.stem}",
            "filename": primary.name,
            "source_path": str(primary.relative_to(WORKSPACE)),
            "source_dataset": "own_train_horn",
            "class": "train_horn",
            "label": 1,
            "sha256": h,
            "duration": meta["duration"],
            "sample_rate": meta["sample_rate"],
            "channels": meta["channels"],
            "codec": meta["codec"],
            "esc50_fold": None,
            "source_group": primary.stem,
            "selection_status": "selected",
        }
        selected_positives.append(rec)

        for dupe in files_sorted[1:]:
            dupe_meta = probe_audio(dupe)
            rejected_positives.append({
                "sample_id": f"pos_{dupe.stem}_rejected",
                "filename": dupe.name,
                "source_path": str(dupe.relative_to(WORKSPACE)),
                "source_dataset": "own_train_horn",
                "class": "train_horn",
                "label": 1,
                "sha256": h,
                "duration": dupe_meta["duration"],
                "sample_rate": dupe_meta["sample_rate"],
                "channels": dupe_meta["channels"],
                "codec": dupe_meta["codec"],
                "rejection_reason": f"Exact bitwise duplicate of {primary.name}",
            })

    # Sort positives deterministically
    selected_positives.sort(key=lambda x: x["filename"])
    assert len(selected_positives) == 86, f"Expected 86 unique positives, found {len(selected_positives)}"
    print(f"Successfully selected {len(selected_positives)} unique positive recordings.")
    print(f"Rejected {len(rejected_positives)} positive duplicates: {[r['filename'] for r in rejected_positives]}")

    # 4. Audit & Select ESC-50 Negatives
    with open(ESC50_CSV) as f:
        esc_rows = list(csv.DictReader(f))

    print(f"Total rows in ESC-50 CSV: {len(esc_rows)}")

    # Create full ESC-50 manifest
    esc50_full_manifest = []
    for r in esc_rows:
        af = ESC50_AUDIO / r["filename"]
        assert af.exists(), f"Missing audio file: {af}"
        esc50_full_manifest.append({
            "filename": r["filename"],
            "source_path": str(af.relative_to(WORKSPACE)),
            "source_dataset": "ESC50",
            "category": r["category"],
            "target": int(r["target"]),
            "fold": int(r["fold"]),
            "esc10": r["esc10"] == "True",
            "src_file": r["src_file"],
            "take": r["take"],
        })

    with open(MANIFESTS_DIR / "audio_v3_esc50_manifest.json", "w") as f:
        json.dump({"total_records": len(esc50_full_manifest), "records": esc50_full_manifest}, f, indent=2)

    with open(MANIFESTS_DIR / "audio_v3_esc50_manifest.jsonl", "w") as f:
        for r in esc50_full_manifest:
            f.write(json.dumps(r) + "\n")
    print(f"Saved full ESC-50 manifest ({len(esc50_full_manifest)} records).")

    # 5. Define negative allocation across the 11 target categories
    # 9 categories get 8 clips, 2 categories get 7 clips -> total = 86
    target_counts = {
        "car_horn": 8,
        "engine": 8,
        "siren": 8,
        "church_bells": 8,
        "clock_alarm": 8,
        "rain": 8,
        "thunderstorm": 8,
        "airplane": 8,
        "helicopter": 8,
        "wind": 7,
        "footsteps": 7,
    }
    assert sum(target_counts.values()) == 86

    # Stratified fold counts:
    # Train: 60 clips from Folds 1, 2, 3
    # Val: 13 clips from Fold 4
    # Test: 13 clips from Fold 5
    val_counts = {
        "car_horn": 2, "siren": 2, "engine": 1, "church_bells": 1, "clock_alarm": 1,
        "rain": 1, "wind": 1, "thunderstorm": 1, "footsteps": 1, "airplane": 1, "helicopter": 1
    }
    test_counts = {
        "engine": 2, "church_bells": 2, "car_horn": 1, "siren": 1, "clock_alarm": 1,
        "rain": 1, "wind": 1, "thunderstorm": 1, "footsteps": 1, "airplane": 1, "helicopter": 1
    }
    train_counts = {c: target_counts[c] - val_counts[c] - test_counts[c] for c in target_counts}

    assert sum(train_counts.values()) == 60
    assert sum(val_counts.values()) == 13
    assert sum(test_counts.values()) == 13

    # Group by fold and category
    by_fold_cat = defaultdict(lambda: defaultdict(list))
    for r in esc_rows:
        if r["category"] in target_counts:
            by_fold_cat[int(r["fold"])][r["category"]].append(r)

    rng = random.Random(42)

    selected_train_neg = []
    selected_val_neg = []
    selected_test_neg = []

    # Select Validation from Fold 4
    for cat, needed in sorted(val_counts.items()):
        avail = sorted(by_fold_cat[4][cat], key=lambda x: x["filename"])
        rng.shuffle(avail)
        selected_val_neg.extend(avail[:needed])

    # Select Test from Fold 5
    for cat, needed in sorted(test_counts.items()):
        avail = sorted(by_fold_cat[5][cat], key=lambda x: x["filename"])
        rng.shuffle(avail)
        selected_test_neg.extend(avail[:needed])

    # Select Train from Folds 1, 2, 3
    for cat, needed in sorted(train_counts.items()):
        avail = []
        for f in [1, 2, 3]:
            avail.extend(by_fold_cat[f][cat])
        avail = sorted(avail, key=lambda x: x["filename"])
        rng.shuffle(avail)
        selected_train_neg.extend(avail[:needed])

    assert len(selected_train_neg) == 60
    assert len(selected_val_neg) == 13
    assert len(selected_test_neg) == 13

    # Format selected negatives
    def format_neg_records(raw_list: list[dict], partition_name: str) -> list[dict]:
        formatted = []
        for r in raw_list:
            af = ESC50_AUDIO / r["filename"]
            h = sha256_file(af)
            # FIREWALL CHECKS
            assert h not in custom_neg_hashes, f"FIREWALL VIOLATION: ESC-50 {af.name} matches custom negative hash!"
            assert h not in layer_b_hashes, f"FIREWALL VIOLATION: ESC-50 {af.name} matches Layer B hash!"
            assert not str(af).startswith(str(OLD_NEGATIVE_DIR)), f"FIREWALL VIOLATION: Negative source path is in old negative dir!"
            assert r["category"] != "train", "FIREWALL VIOLATION: ESC-50 'train' category selected as negative!"

            meta = probe_audio(af)
            formatted.append({
                "sample_id": f"esc50_{Path(r['filename']).stem}",
                "filename": r["filename"],
                "source_path": str(af.relative_to(WORKSPACE)),
                "source_dataset": "ESC50",
                "class": "non_train_sound",
                "category": r["category"],
                "label": 0,
                "sha256": h,
                "duration": meta["duration"],
                "sample_rate": meta["sample_rate"],
                "channels": meta["channels"],
                "codec": meta["codec"],
                "esc50_fold": int(r["fold"]),
                "source_group": f"esc50_src_{r['src_file']}",
                "selection_status": "selected",
                "partition": partition_name,
            })
        return formatted

    train_neg_records = format_neg_records(selected_train_neg, "train")
    val_neg_records = format_neg_records(selected_val_neg, "val")
    test_neg_records = format_neg_records(selected_test_neg, "test")
    all_neg_records = train_neg_records + val_neg_records + test_neg_records
    assert len(all_neg_records) == 86

    # 6. Split Positives (70% Train = 60, 15% Val = 13, 15% Test = 13)
    pos_rng = random.Random(42)
    pos_shuffled = list(selected_positives)
    pos_rng.shuffle(pos_shuffled)

    train_pos = pos_shuffled[:60]
    val_pos = pos_shuffled[60:73]
    test_pos = pos_shuffled[73:86]

    for r in train_pos:
        r["partition"] = "train"
    for r in val_pos:
        r["partition"] = "val"
    for r in test_pos:
        r["partition"] = "test"

    assert len(train_pos) == 60
    assert len(val_pos) == 13
    assert len(test_pos) == 13

    # 7. Check for ZERO Source / File Leakage Across Partitions
    all_selected = train_pos + val_pos + test_pos + train_neg_records + val_neg_records + test_neg_records
    assert len(all_selected) == 172

    train_sources = set(r["source_group"] for r in (train_pos + train_neg_records))
    val_sources = set(r["source_group"] for r in (val_pos + val_neg_records))
    test_sources = set(r["source_group"] for r in (test_pos + test_neg_records))

    assert len(train_sources & val_sources) == 0, f"Source leakage Train & Val: {train_sources & val_sources}"
    assert len(train_sources & test_sources) == 0, f"Source leakage Train & Test: {train_sources & test_sources}"
    assert len(val_sources & test_sources) == 0, f"Source leakage Val & Test: {val_sources & test_sources}"

    print("Confirmed ZERO source group leakage across Train, Val, and Test!")

    # 8. Save Selection Manifest
    selection_manifest = {
        "experiment": "AUDIO_MODEL_V3_ESC50",
        "description": "Balanced Audio V3 experiment with 86 own train horn recordings and 86 ESC-50 environmental negatives",
        "firewall_verified": {
            "custom_negative_pool_excluded": True,
            "layer_b_video_audio_excluded": True,
            "esc50_train_category_excluded": True,
            "total_blocked_custom_neg_hashes": len(custom_neg_hashes),
            "total_blocked_layer_b_hashes": len(layer_b_hashes),
        },
        "selected_positive_count": len(selected_positives),
        "selected_negative_count": len(all_neg_records),
        "total_selected_recordings": len(all_selected),
        "negative_category_allocation": target_counts,
        "fold_allocation": {
            "train_folds": [1, 2, 3],
            "val_folds": [4],
            "test_folds": [5],
        },
        "partition_counts": {
            "train": {"positive": len(train_pos), "negative": len(train_neg_records), "total": 120},
            "val": {"positive": len(val_pos), "negative": len(val_neg_records), "total": 26},
            "test": {"positive": len(test_pos), "negative": len(test_neg_records), "total": 26},
        },
        "rejected_positive_duplicates": rejected_positives,
        "selected_records": all_selected,
    }

    with open(MANIFESTS_DIR / "audio_v3_selection.json", "w") as f:
        json.dump(selection_manifest, f, indent=2)
    print(f"Saved {MANIFESTS_DIR / 'audio_v3_selection.json'}")

    # 9. Save Dataset Split
    split_manifest = {
        "experiment": "AUDIO_MODEL_V3_ESC50",
        "seed": 42,
        "split_ratio": {"train": 0.6977, "val": 0.1512, "test": 0.1512},
        "partitions": {
            "train": {
                "positive_count": 60,
                "negative_count": 60,
                "total_count": 120,
                "recordings": [r["sample_id"] for r in (train_pos + train_neg_records)],
            },
            "val": {
                "positive_count": 13,
                "negative_count": 13,
                "total_count": 26,
                "recordings": [r["sample_id"] for r in (val_pos + val_neg_records)],
            },
            "test": {
                "positive_count": 13,
                "negative_count": 13,
                "total_count": 26,
                "recordings": [r["sample_id"] for r in (test_pos + test_neg_records)],
            },
        },
    }

    with open(SPLITS_DIR / "dataset_split.json", "w") as f:
        json.dump(split_manifest, f, indent=2)
    print(f"Saved {SPLITS_DIR / 'dataset_split.json'}")

    print("\nPhase 1 Selection & Manifest generation completed successfully!")


if __name__ == "__main__":
    main()
