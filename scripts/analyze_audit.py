#!/usr/bin/env python3
"""
Deep analysis of TRAIN_VIDEO_AUDIO 2 audit data.
"""
import json
from collections import defaultdict
from pathlib import Path

AUDIT_FILE = Path("/Users/sayemuddin/Desktop/Train_automation/data/manifests/raw_audit_train_video_audio_2.json")

def main():
    with open(AUDIT_FILE) as f:
        data = json.load(f)

    print("=== SUMMARY OF FILE COUNTS ===")
    for folder, files in data.items():
        print(f"{folder:25}: {len(files)} files")

    print("\n=== CORRUPTED / ERROR FILES ===")
    has_errors = False
    for folder, files in data.items():
        for item in files:
            if item.get("error"):
                print(f"Error in {folder}/{item['filename']}: {item['error']}")
                has_errors = True
    if not has_errors:
        print("None! All media probed successfully by ffprobe.")

    print("\n=== DUPLICATE SHA-256 DETECTION ===")
    all_sha = defaultdict(list)
    for folder, files in data.items():
        for item in files:
            all_sha[item["sha256"]].append((folder, item["filename"]))

    dups = {k: v for k, v in all_sha.items() if len(v) > 1}
    if dups:
        print(f"Found {len(dups)} duplicate hash sets:")
        for sha, occurrences in dups.items():
            print(f"  SHA: {sha[:12]}... -> {occurrences}")
    else:
        print("No duplicate SHA-256 hashes found anywhere!")

    print("\n=== VIDEO ANALYSIS: TRAIN_FRONT vs TRAIN_BACKK ===")
    tf_files = {item["filename"]: item for item in data.get("Train_front", [])}
    tb_files = {item["filename"]: item for item in data.get("Train_backk", [])}
    print(f"Train_front file names: {sorted(list(tf_files.keys()))}")
    print(f"Train_backk file names: {sorted(list(tb_files.keys()))}")

    # Pairing analysis
    common_names = set(tf_files.keys()) & set(tb_files.keys())
    only_tf = set(tf_files.keys()) - set(tb_files.keys())
    only_tb = set(tb_files.keys()) - set(tf_files.keys())
    print(f"Exact matching filenames between front and back: {len(common_names)}")
    if only_tf:
        print(f"Only in Train_front: {only_tf}")
    if only_tb:
        print(f"Only in Train_backk: {only_tb}")

    print("\nPairing comparison (Front vs Back):")
    for name in sorted(list(common_names)):
        f = tf_files[name]
        b = tb_files[name]
        dur_f = f["duration_s"]
        dur_b = b["duration_s"]
        diff = abs(dur_f - dur_b) if (dur_f and dur_b) else None
        print(f"  {name:30} | Front: {dur_f:6.2f}s, {f['width']}x{f['height']}, {f['fps']}fps, audio={f['has_audio']} | Back: {dur_b:6.2f}s, {b['width']}x{b['height']}, {b['fps']}fps, audio={b['has_audio']} | DurDiff={diff:.2f}s")

    print("\n=== NO-TRAIN VIDEO ANALYSIS ===")
    nt_front = {item["filename"]: item for item in data.get("No_train_front", [])}
    nt_back = {item["filename"]: item for item in data.get("No_train_back", [])}
    print(f"No_train_front filenames: {sorted(list(nt_front.keys()))}")
    print(f"No_train_back filenames:  {sorted(list(nt_back.keys()))}")
    for name in sorted(set(nt_front.keys()) | set(nt_back.keys())):
        f = nt_front.get(name)
        b = nt_back.get(name)
        f_str = f"{f['duration_s']:6.2f}s, {f['width']}x{f['height']}, fps={f['fps']}, audio={f['has_audio']}" if f else "MISSING"
        b_str = f"{b['duration_s']:6.2f}s, {b['width']}x{b['height']}, fps={b['fps']}, audio={b['has_audio']}" if b else "MISSING"
        print(f"  {name:10} | Front: {f_str} | Back: {b_str}")

    print("\n=== ENGINE CAMERA ANALYSIS ===")
    ef_files = {item["filename"]: item for item in data.get("Engine_front_camera", [])}
    eb_files = {item["filename"]: item for item in data.get("Engine_back_camera", [])}
    print(f"Engine_front filenames: {sorted(list(ef_files.keys()))}")
    print(f"Engine_back filenames:  {sorted(list(eb_files.keys()))}")
    for name in sorted(set(ef_files.keys()) | set(eb_files.keys())):
        f = ef_files.get(name)
        b = eb_files.get(name)
        f_str = f"{f['duration_s']:6.2f}s, {f['width']}x{f['height']}, fps={f['fps']}, audio={f['has_audio']}" if f else "MISSING"
        b_str = f"{b['duration_s']:6.2f}s, {b['width']}x{b['height']}, fps={b['fps']}, audio={b['has_audio']}" if b else "MISSING"
        print(f"  {name:10} | Front: {f_str} | Back: {b_str}")

    print("\n=== AUDIO INVENTORY ANALYSIS ===")
    pos = data.get("Positive_Audio", [])
    neg = data.get("Negative_Audio", [])
    
    pos_durations = [x["duration_s"] for x in pos if x["duration_s"]]
    neg_durations = [x["duration_s"] for x in neg if x["duration_s"]]
    
    pos_sr = {x["sample_rate"] for x in pos}
    neg_sr = {x["sample_rate"] for x in neg}
    
    pos_ch = {x["channels"] for x in pos}
    neg_ch = {x["channels"] for x in neg}
    
    pos_codecs = {x["audio_codec"] for x in pos}
    neg_codecs = {x["audio_codec"] for x in neg}
    
    print(f"Positive Audio: {len(pos)} files")
    print(f"  Durations: min={min(pos_durations):.2f}s, max={max(pos_durations):.2f}s, avg={sum(pos_durations)/len(pos_durations):.2f}s, total={sum(pos_durations):.2f}s")
    print(f"  Sample rates: {pos_sr}")
    print(f"  Channels: {pos_ch}")
    print(f"  Codecs: {pos_codecs}")
    
    print(f"\nNegative Audio: {len(neg)} files")
    print(f"  Durations: min={min(neg_durations):.2f}s, max={max(neg_durations):.2f}s, avg={sum(neg_durations)/len(neg_durations):.2f}s, total={sum(neg_durations):.2f}s")
    print(f"  Sample rates: {neg_sr}")
    print(f"  Channels: {neg_ch}")
    print(f"  Codecs: {neg_codecs}")

if __name__ == "__main__":
    main()
