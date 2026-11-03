#!/usr/bin/env python3
"""
Phase 1: Organize and Manifest V2 Dataset (Layer B Real-World Videos and Standalone Audio).
Strict adherence to zero-copy atomic moves and research isolation.
"""
import sys
import json
import shutil
import hashlib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from railway_detection.safety.media_guard import require_media_authorization  # noqa: E402

WORKSPACE = Path("/Users/sayemuddin/Desktop/Train_automation")
SRC_ROOT = WORKSPACE / "TRAIN_VIDEO_AUDIO 2"
AUDIT_FILE = WORKSPACE / "data/manifests/raw_audit_train_video_audio_2.json"

LAYER_B_V2 = WORKSPACE / "data/raw/layer_b/v2"
TRAIN_EVENTS_DIR = LAYER_B_V2 / "train_events"
NO_TRAIN_EVENTS_DIR = LAYER_B_V2 / "no_train_events"
ENGINE_EVENTS_DIR = LAYER_B_V2 / "engine_events"

AUDIO_POS_DIR = WORKSPACE / "data/raw/audio/train_horn/positive"
AUDIO_NEG_DIR = WORKSPACE / "data/raw/audio/train_horn/negative"

def get_sha256(filepath):
    h = hashlib.sha256()
    require_media_authorization(filepath, "HASH_RAW_MEDIA")
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def atomic_move_or_verify(src: Path, dst: Path, expected_sha: str):
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        existing_sha = get_sha256(dst)
        if existing_sha == expected_sha:
            print(f"Destination already exists with identical hash: {dst}")
            if src.exists():
                src.unlink()
            return True
        else:
            raise RuntimeError(f"Hash mismatch at destination {dst}: {existing_sha} != {expected_sha}")
    if not src.exists():
        raise FileNotFoundError(f"Source file not found: {src}")
    
    # Atomic rename on same filesystem
    shutil.move(str(src), str(dst))
    actual_sha = get_sha256(dst)
    if actual_sha != expected_sha:
        raise RuntimeError(f"Hash corrupted after move for {dst}!")
    return True

def main():
    if not AUDIT_FILE.exists():
        print(f"Error: Audit file {AUDIT_FILE} not found. Run audit first.")
        sys.exit(1)
        
    with open(AUDIT_FILE) as f:
        audit = json.load(f)

    print("Step 1: Setting up target directories...")
    for d in [TRAIN_EVENTS_DIR, NO_TRAIN_EVENTS_DIR, ENGINE_EVENTS_DIR, AUDIO_POS_DIR, AUDIO_NEG_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    video_manifest_records = []
    
    # -------------------------------------------------------------
    # 1. TRAIN FULL EVENTS (23 events)
    # -------------------------------------------------------------
    print("\nStep 2: Organizing 23 full-train events...")
    # Map index to event_id
    # Ordering: 1..9, 11..21, 22, 23, 24
    train_event_order = [
        "1.mov", "2.mov", "3.mov", "4.mov", "5.mov", "6.mov", "7.mov", "8.mov", "9.mov",
        "11.mov", "12.mov", "13.mov", "14.mov", "15.mov", "16.mov", "17.mov", "18.mov",
        "19.mov", "20.mov", "21.mov",
        "22(night_video_lowlight)", "23(night_video_lowlight)", "24(night_video_lowlight)"
    ]
    
    tf_audit = {x["filename"]: x for x in audit["Train_front"]}
    tb_audit = {x["filename"]: x for x in audit["Train_backk"]}

    for idx, key in enumerate(train_event_order, start=1):
        event_id = f"event_{idx:03d}"
        event_dir = TRAIN_EVENTS_DIR / event_id
        event_dir.mkdir(parents=True, exist_ok=True)
        
        # Match front and back
        if "night" in key:
            front_fn = f"{key}.MOV"
            back_fn = f"{key}.mov"
        else:
            front_fn = key
            back_fn = key
            
        f_info = tf_audit[front_fn]
        b_info = tb_audit[back_fn]
        
        src_front = Path(f_info["path"])
        src_back = Path(b_info["path"])
        
        dst_front = event_dir / "camera_front.mov"
        dst_back = event_dir / "camera_back.mov"
        
        atomic_move_or_verify(src_front, dst_front, f_info["sha256"])
        atomic_move_or_verify(src_back, dst_back, b_info["sha256"])
        
        # Create backward-compatible symlink camera_rear.mov -> camera_back.mov
        rear_link = event_dir / "camera_rear.mov"
        if rear_link.exists() or rear_link.is_symlink():
            rear_link.unlink()
        rear_link.symlink_to("camera_back.mov")
        
        # Manifest records
        is_night = "night" in key
        video_manifest_records.append({
            "event_id": event_id,
            "event_type": "full_train_night" if is_night else "full_train",
            "camera_id": "front",
            "source_path": str(src_front),
            "destination_path": str(dst_front.relative_to(WORKSPACE)),
            "filename": "camera_front.mov",
            "original_filename": front_fn,
            "duration_s": f_info["duration_s"],
            "width": f_info["width"],
            "height": f_info["height"],
            "fps": f_info["fps"],
            "codec": f_info["video_codec"],
            "container": f_info["container"],
            "has_audio": f_info["has_audio"],
            "audio_codec": f_info["audio_codec"],
            "audio_sample_rate": f_info["sample_rate"],
            "audio_channels": f_info["channels"],
            "sha256": f_info["sha256"],
            "dataset_role": "REAL_WORLD_TRAIN_EVENT",
            "evaluation_eligible": True,
            "pairing_confidence": "confirmed_100%",
            "metadata_status": "verified"
        })
        video_manifest_records.append({
            "event_id": event_id,
            "event_type": "full_train_night" if is_night else "full_train",
            "camera_id": "back",
            "source_path": str(src_back),
            "destination_path": str(dst_back.relative_to(WORKSPACE)),
            "filename": "camera_back.mov",
            "original_filename": back_fn,
            "duration_s": b_info["duration_s"],
            "width": b_info["width"],
            "height": b_info["height"],
            "fps": b_info["fps"],
            "codec": b_info["video_codec"],
            "container": b_info["container"],
            "has_audio": b_info["has_audio"],
            "audio_codec": b_info["audio_codec"],
            "audio_sample_rate": b_info["sample_rate"],
            "audio_channels": b_info["channels"],
            "sha256": b_info["sha256"],
            "dataset_role": "REAL_WORLD_TRAIN_EVENT",
            "evaluation_eligible": True,
            "pairing_confidence": "confirmed_100%",
            "metadata_status": "verified"
        })

    # -------------------------------------------------------------
    # 2. NO-TRAIN EVENTS (3 events)
    # -------------------------------------------------------------
    print("\nStep 3: Organizing 3 no-train events...")
    nt_f_audit = {x["filename"]: x for x in audit["No_train_front"]}
    nt_b_audit = {x["filename"]: x for x in audit["No_train_back"]}
    
    no_train_pairs = [
        ("1.mov", "1.MOV"),
        ("2.MOV", "2.mov"),
        ("3.MOV", "3.mov")
    ]
    
    for idx, (f_fn, b_fn) in enumerate(no_train_pairs, start=1):
        event_id = f"event_{idx:03d}"
        event_dir = NO_TRAIN_EVENTS_DIR / event_id
        event_dir.mkdir(parents=True, exist_ok=True)
        
        f_info = nt_f_audit[f_fn]
        b_info = nt_b_audit[b_fn]
        
        src_front = Path(f_info["path"])
        src_back = Path(b_info["path"])
        
        dst_front = event_dir / "camera_front.mov"
        dst_back = event_dir / "camera_back.mov"
        
        atomic_move_or_verify(src_front, dst_front, f_info["sha256"])
        atomic_move_or_verify(src_back, dst_back, b_info["sha256"])
        
        rear_link = event_dir / "camera_rear.mov"
        if rear_link.exists() or rear_link.is_symlink():
            rear_link.unlink()
        rear_link.symlink_to("camera_back.mov")
        
        video_manifest_records.append({
            "event_id": event_id,
            "event_type": "no_train",
            "camera_id": "front",
            "source_path": str(src_front),
            "destination_path": str(dst_front.relative_to(WORKSPACE)),
            "filename": "camera_front.mov",
            "original_filename": f_fn,
            "duration_s": f_info["duration_s"],
            "width": f_info["width"],
            "height": f_info["height"],
            "fps": f_info["fps"],
            "codec": f_info["video_codec"],
            "container": f_info["container"],
            "has_audio": f_info["has_audio"],
            "audio_codec": f_info["audio_codec"],
            "audio_sample_rate": f_info["sample_rate"],
            "audio_channels": f_info["channels"],
            "sha256": f_info["sha256"],
            "dataset_role": "REAL_WORLD_NO_TRAIN",
            "evaluation_eligible": True,
            "pairing_confidence": "confirmed_100%",
            "metadata_status": "verified"
        })
        video_manifest_records.append({
            "event_id": event_id,
            "event_type": "no_train",
            "camera_id": "back",
            "source_path": str(src_back),
            "destination_path": str(dst_back.relative_to(WORKSPACE)),
            "filename": "camera_back.mov",
            "original_filename": b_fn,
            "duration_s": b_info["duration_s"],
            "width": b_info["width"],
            "height": b_info["height"],
            "fps": b_info["fps"],
            "codec": b_info["video_codec"],
            "container": b_info["container"],
            "has_audio": b_info["has_audio"],
            "audio_codec": b_info["audio_codec"],
            "audio_sample_rate": b_info["sample_rate"],
            "audio_channels": b_info["channels"],
            "sha256": b_info["sha256"],
            "dataset_role": "REAL_WORLD_NO_TRAIN",
            "evaluation_eligible": True,
            "pairing_confidence": "confirmed_100%",
            "metadata_status": "verified"
        })

    # -------------------------------------------------------------
    # 3. ENGINE EVENTS (1 new eligible, 1 historical duplicate excluded)
    # -------------------------------------------------------------
    print("\nStep 4: Organizing Engine events...")
    ef_audit = {x["filename"]: x for x in audit["Engine_front_camera"]}
    eb_audit = {x["filename"]: x for x in audit["Engine_back_camera"]}

    # Event 1: New Engine-Only (Eligible)
    e1_dir = ENGINE_EVENTS_DIR / "event_001"
    e1_dir.mkdir(parents=True, exist_ok=True)
    f_info = ef_audit["1.MOV"]
    b_info = eb_audit["1.mov"]
    src_front = Path(f_info["path"])
    src_back = Path(b_info["path"])
    dst_front = e1_dir / "camera_front.mov"
    dst_back = e1_dir / "camera_back.mov"
    atomic_move_or_verify(src_front, dst_front, f_info["sha256"])
    atomic_move_or_verify(src_back, dst_back, b_info["sha256"])
    rear_link = e1_dir / "camera_rear.mov"
    if rear_link.exists() or rear_link.is_symlink():
        rear_link.unlink()
    rear_link.symlink_to("camera_back.mov")
    
    video_manifest_records.append({
        "event_id": "event_001",
        "event_type": "engine_only",
        "camera_id": "front",
        "source_path": str(src_front),
        "destination_path": str(dst_front.relative_to(WORKSPACE)),
        "filename": "camera_front.mov",
        "original_filename": "1.MOV",
        "duration_s": f_info["duration_s"],
        "width": f_info["width"],
        "height": f_info["height"],
        "fps": f_info["fps"],
        "codec": f_info["video_codec"],
        "container": f_info["container"],
        "has_audio": f_info["has_audio"],
        "audio_codec": f_info["audio_codec"],
        "audio_sample_rate": f_info["sample_rate"],
        "audio_channels": f_info["channels"],
        "sha256": f_info["sha256"],
        "dataset_role": "REAL_WORLD_ENGINE_ONLY",
        "evaluation_eligible": True,
        "pairing_confidence": "confirmed_100%",
        "metadata_status": "verified"
    })
    video_manifest_records.append({
        "event_id": "event_001",
        "event_type": "engine_only",
        "camera_id": "back",
        "source_path": str(src_back),
        "destination_path": str(dst_back.relative_to(WORKSPACE)),
        "filename": "camera_back.mov",
        "original_filename": "1.mov",
        "duration_s": b_info["duration_s"],
        "width": b_info["width"],
        "height": b_info["height"],
        "fps": b_info["fps"],
        "codec": b_info["video_codec"],
        "container": b_info["container"],
        "has_audio": b_info["has_audio"],
        "audio_codec": b_info["audio_codec"],
        "audio_sample_rate": b_info["sample_rate"],
        "audio_channels": b_info["channels"],
        "sha256": b_info["sha256"],
        "dataset_role": "REAL_WORLD_ENGINE_ONLY",
        "evaluation_eligible": True,
        "pairing_confidence": "confirmed_100%",
        "metadata_status": "verified"
    })

    # Event 2: Historical Event 010 Duplicate (Excluded)
    e2_dir = ENGINE_EVENTS_DIR / "event_historical_duplicate_010"
    e2_dir.mkdir(parents=True, exist_ok=True)
    f_info = ef_audit["2.MOV"]
    b_info = eb_audit["2.MOV"]
    src_front = Path(f_info["path"])
    src_back = Path(b_info["path"])
    dst_front = e2_dir / "camera_front.mov"
    dst_back = e2_dir / "camera_back.mov"
    atomic_move_or_verify(src_front, dst_front, f_info["sha256"])
    atomic_move_or_verify(src_back, dst_back, b_info["sha256"])
    rear_link = e2_dir / "camera_rear.mov"
    if rear_link.exists() or rear_link.is_symlink():
        rear_link.unlink()
    rear_link.symlink_to("camera_back.mov")
    
    video_manifest_records.append({
        "event_id": "event_historical_duplicate_010",
        "event_type": "historical_engine_duplicate",
        "camera_id": "front",
        "source_path": str(src_front),
        "destination_path": str(dst_front.relative_to(WORKSPACE)),
        "filename": "camera_front.mov",
        "original_filename": "2.MOV",
        "duration_s": f_info["duration_s"],
        "width": f_info["width"],
        "height": f_info["height"],
        "fps": f_info["fps"],
        "codec": f_info["video_codec"],
        "container": f_info["container"],
        "has_audio": f_info["has_audio"],
        "audio_codec": f_info["audio_codec"],
        "audio_sample_rate": f_info["sample_rate"],
        "audio_channels": f_info["channels"],
        "sha256": f_info["sha256"],
        "dataset_role": "HISTORICAL_DUPLICATE_EXCLUDED",
        "evaluation_eligible": False,
        "pairing_confidence": "confirmed_100%",
        "metadata_status": "verified_historical_match_old_event_010"
    })
    video_manifest_records.append({
        "event_id": "event_historical_duplicate_010",
        "event_type": "historical_engine_duplicate",
        "camera_id": "back",
        "source_path": str(src_back),
        "destination_path": str(dst_back.relative_to(WORKSPACE)),
        "filename": "camera_back.mov",
        "original_filename": "2.MOV",
        "duration_s": b_info["duration_s"],
        "width": b_info["width"],
        "height": b_info["height"],
        "fps": b_info["fps"],
        "codec": b_info["video_codec"],
        "container": b_info["container"],
        "has_audio": b_info["has_audio"],
        "audio_codec": b_info["audio_codec"],
        "audio_sample_rate": b_info["sample_rate"],
        "audio_channels": b_info["channels"],
        "sha256": b_info["sha256"],
        "dataset_role": "HISTORICAL_DUPLICATE_EXCLUDED",
        "evaluation_eligible": False,
        "pairing_confidence": "confirmed_100%",
        "metadata_status": "verified_historical_match_old_event_010"
    })

    # Save video manifests
    v_manifest_json = WORKSPACE / "data/manifests/real_world_v2_video_manifest.json"
    v_manifest_jsonl = WORKSPACE / "data/manifests/real_world_v2_video_manifest.jsonl"
    
    with open(v_manifest_json, "w") as f:
        json.dump({
            "version": "2.0.0",
            "total_records": len(video_manifest_records),
            "summary": {
                "train_events": 23,
                "engine_events_eligible": 1,
                "engine_events_historical_duplicate": 1,
                "no_train_events": 3,
                "total_video_files": len(video_manifest_records)
            },
            "records": video_manifest_records
        }, f, indent=2)
        
    with open(v_manifest_jsonl, "w") as f:
        for r in video_manifest_records:
            f.write(json.dumps(r) + "\n")
    print(f"Video manifests written: {len(video_manifest_records)} records.")

    # -------------------------------------------------------------
    # 4. AUDIO ORGANIZATION & MANIFESTS
    # -------------------------------------------------------------
    print("\nStep 5: Organizing Audio dataset (Positive & Negative)...")
    audio_manifest_records = []
    
    # Positive Audio: 87 files
    pos_items = audit["Positive_Audio"]
    # Check 41 and 42 duplicate
    pos_hashes = {}
    for idx, item in enumerate(sorted(pos_items, key=lambda x: x["filename"]), start=1):
        sample_id = f"pos_{idx:03d}"
        src = Path(item["path"])
        dst = AUDIO_POS_DIR / item["filename"]
        atomic_move_or_verify(src, dst, item["sha256"])
        
        dup_status = "unique"
        sha = item["sha256"]
        if sha in pos_hashes:
            dup_status = f"exact_duplicate_of_{pos_hashes[sha]}"
        else:
            pos_hashes[sha] = item["filename"]
            
        audio_manifest_records.append({
            "sample_id": sample_id,
            "filename": item["filename"],
            "class": "positive",
            "source_path": str(src),
            "destination_path": str(dst.relative_to(WORKSPACE)),
            "duration_s": item["duration_s"],
            "sample_rate": item["sample_rate"],
            "channels": item["channels"],
            "codec": item["audio_codec"],
            "sha256": item["sha256"],
            "dataset_role": "audio_model_development",
            "duplicate_status": dup_status,
            "is_duplicate": dup_status != "unique"
        })

    # Negative Audio: 97 files
    neg_items = audit["Negative_Audio"]
    neg_hashes = {}
    for idx, item in enumerate(sorted(neg_items, key=lambda x: int(x["filename"].split(".")[0]) if x["filename"].split(".")[0].isdigit() else 999), start=1):
        sample_id = f"neg_{idx:03d}"
        src = Path(item["path"])
        dst = AUDIO_NEG_DIR / item["filename"]
        atomic_move_or_verify(src, dst, item["sha256"])
        
        dup_status = "unique"
        sha = item["sha256"]
        if sha in neg_hashes:
            dup_status = f"exact_duplicate_of_{neg_hashes[sha]}"
        else:
            neg_hashes[sha] = item["filename"]
            
        audio_manifest_records.append({
            "sample_id": sample_id,
            "filename": item["filename"],
            "class": "negative",
            "source_path": str(src),
            "destination_path": str(dst.relative_to(WORKSPACE)),
            "duration_s": item["duration_s"],
            "sample_rate": item["sample_rate"],
            "channels": item["channels"],
            "codec": item["audio_codec"],
            "sha256": item["sha256"],
            "dataset_role": "audio_model_development",
            "duplicate_status": dup_status,
            "is_duplicate": dup_status != "unique"
        })

    # Save audio manifests
    a_manifest_json = WORKSPACE / "data/manifests/audio_training_v2_manifest.json"
    a_manifest_jsonl = WORKSPACE / "data/manifests/audio_training_v2_manifest.jsonl"
    
    with open(a_manifest_json, "w") as f:
        json.dump({
            "version": "2.0.0",
            "total_records": len(audio_manifest_records),
            "summary": {
                "positive_total": len(pos_items),
                "positive_unique": len(pos_hashes),
                "negative_total": len(neg_items),
                "negative_unique": len(neg_hashes)
            },
            "records": audio_manifest_records
        }, f, indent=2)
        
    with open(a_manifest_jsonl, "w") as f:
        for r in audio_manifest_records:
            f.write(json.dumps(r) + "\n")
    print(f"Audio manifests written: {len(audio_manifest_records)} records.")

    # -------------------------------------------------------------
    # 5. BALANCED AUDIO SELECTION MANIFEST
    # -------------------------------------------------------------
    print("\nStep 6: Creating balanced audio training selection manifest...")
    # Unique positives = 86
    # Primary balanced experiment needs exactly 86 unique negatives
    # 95 unique negatives available -> Select 86, hold out 9 for hard-negative analysis
    # Outlier 14.mp3 (572.3s) is held out as extended ambient baseline
    # 8 other held-out files selected deterministically
    
    unique_positives = [r for r in audio_manifest_records if r["class"] == "positive" and not r["is_duplicate"]]
    assert len(unique_positives) == 86, f"Expected 86 unique positives, got {len(unique_positives)}"
    
    unique_negatives = [r for r in audio_manifest_records if r["class"] == "negative" and not r["is_duplicate"]]
    assert len(unique_negatives) == 95, f"Expected 95 unique negatives, got {len(unique_negatives)}"
    
    # 14.mp3 is rejected from primary balanced set due to extreme duration outlier (572.34s)
    outlier_neg = next(r for r in unique_negatives if r["filename"] == "14.mp3")
    remaining_neg = [r for r in unique_negatives if r["filename"] != "14.mp3"] # 94 clips
    
    # Need to select 86 from 94 (reject 8 more)
    # Let's reject 8 files evenly spaced by index to ensure uniform coverage across the dataset
    # 94 / 8 ≈ every 11th clip: indices [5, 17, 29, 41, 53, 65, 77, 89]
    reject_indices = {5, 17, 29, 41, 53, 65, 77, 89}
    
    selected_negatives = []
    rejected_negatives = [
        {
            "sample_id": outlier_neg["sample_id"],
            "filename": outlier_neg["filename"],
            "category": "extended_ambient_baseline",
            "sha256": outlier_neg["sha256"],
            "duration_s": outlier_neg["duration_s"],
            "reason_for_rejection": "Extreme duration outlier (572.34s continuous ambient baseline); preserved for continuous streaming evaluation"
        }
    ]
    
    for idx, r in enumerate(remaining_neg):
        if idx in reject_indices:
            rejected_negatives.append({
                "sample_id": r["sample_id"],
                "filename": r["filename"],
                "category": "field_acoustic_negative",
                "sha256": r["sha256"],
                "duration_s": r["duration_s"],
                "reason_for_rejection": "Held-out negative for hard-negative robustness evaluation pool (primary experiment balanced at 86)"
            })
        else:
            selected_negatives.append(r)
            
    assert len(selected_negatives) == 86, f"Expected 86 selected negatives, got {len(selected_negatives)}"
    assert len(rejected_negatives) == 9, f"Expected 9 rejected unique negatives, got {len(rejected_negatives)}"
    
    # Also record duplicate rejections
    for r in audio_manifest_records:
        if r["is_duplicate"]:
            rejected_negatives.append({
                "sample_id": r["sample_id"],
                "filename": r["filename"],
                "category": f"exact_duplicate_{r['class']}",
                "sha256": r["sha256"],
                "duration_s": r["duration_s"],
                "reason_for_rejection": f"Exact bitwise duplicate of {r['duplicate_status']}"
            })

    selected_records = []
    for p in unique_positives:
        selected_records.append({
            "sample_id": p["sample_id"],
            "filename": p["filename"],
            "class": "train_horn",
            "category": "locomotive_horn_sequence",
            "sha256": p["sha256"],
            "duration_s": p["duration_s"],
            "reason_for_selection": "Primary balanced positive class (unique locomotive horn)"
        })
    for n in selected_negatives:
        selected_records.append({
            "sample_id": n["sample_id"],
            "filename": n["filename"],
            "class": "non_train_sound",
            "category": "field_acoustic_negative",
            "sha256": n["sha256"],
            "duration_s": n["duration_s"],
            "reason_for_selection": "Primary balanced negative class (stratified field acoustic recording)"
        })

    selection_json = WORKSPACE / "data/manifests/audio_training_v2_selection.json"
    with open(selection_json, "w") as f:
        json.dump({
            "version": "2.0.0",
            "balanced_experiment_size": 172,
            "selected_positive_count": 86,
            "selected_negative_count": 86,
            "held_out_negative_count": 9,
            "duplicate_count": 3,
            "selected_records": selected_records,
            "rejected_records": rejected_negatives
        }, f, indent=2)
    print(f"Selection manifest written: 86 positive + 86 negative (total {len(selected_records)}).")

    print("\nPhase 1 organization complete!")

if __name__ == "__main__":
    main()
