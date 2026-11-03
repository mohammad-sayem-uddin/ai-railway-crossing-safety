#!/usr/bin/env python3
"""
Comprehensive Read-Only Audit of TRAIN_VIDEO_AUDIO 2 Dataset.
"""
import sys
import json
import hashlib
import subprocess
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from railway_detection.safety.media_guard import require_media_authorization  # noqa: E402

DATASET_ROOT = Path("/Users/sayemuddin/Desktop/Train_automation/TRAIN_VIDEO_AUDIO 2")

def get_sha256(filepath):
    h = hashlib.sha256()
    require_media_authorization(filepath, "HASH_RAW_MEDIA")
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def probe_file(filepath):
    require_media_authorization(filepath, "MEDIA_PROBE")
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration,size,bit_rate,format_name:stream=index,codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels",
        "-of", "json",
        str(filepath)
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(res.stdout)
    except Exception as e:
        return {"error": str(e)}

def audit_directory(folder_path):
    results = []
    for p in sorted(folder_path.iterdir()):
        if p.name.startswith("."):
            continue
        if p.is_dir():
            continue
        
        stat = p.stat()
        sha = get_sha256(p)
        probe = probe_file(p)
        
        # parse streams
        video_stream = None
        audio_stream = None
        format_info = probe.get("format", {})
        
        for s in probe.get("streams", []):
            if s.get("codec_type") == "video" and video_stream is None:
                video_stream = s
            elif s.get("codec_type") == "audio" and audio_stream is None:
                audio_stream = s
                
        duration = None
        if "duration" in format_info:
            try:
                duration = float(format_info["duration"])
            except (ValueError, TypeError):
                pass
                
        fps = None
        if video_stream and "r_frame_rate" in video_stream:
            rfr = video_stream["r_frame_rate"]
            try:
                if "/" in rfr:
                    num, den = rfr.split("/")
                    fps = round(float(num) / float(den), 2) if float(den) != 0 else None
                else:
                    fps = float(rfr)
            except Exception:
                pass
                
        info = {
            "filename": p.name,
            "path": str(p),
            "size_bytes": stat.st_size,
            "sha256": sha,
            "duration_s": duration,
            "container": format_info.get("format_name"),
            "has_video": video_stream is not None,
            "has_audio": audio_stream is not None,
            "video_codec": video_stream.get("codec_name") if video_stream else None,
            "width": video_stream.get("width") if video_stream else None,
            "height": video_stream.get("height") if video_stream else None,
            "fps": fps,
            "audio_codec": audio_stream.get("codec_name") if audio_stream else None,
            "sample_rate": int(audio_stream["sample_rate"]) if audio_stream and "sample_rate" in audio_stream else None,
            "channels": int(audio_stream["channels"]) if audio_stream and "channels" in audio_stream else None,
            "error": probe.get("error")
        }
        results.append(info)
    return results

def main():
    if not DATASET_ROOT.exists():
        print(f"Error: {DATASET_ROOT} does not exist.")
        sys.exit(1)
        
    audit_data = {}
    subfolders = [
        "Train_front",
        "Train_backk",
        "No_train_front",
        "No_train_back",
        "Engine_front_camera",
        "Engine_back_camera",
        "Positive_Audio",
        "Negative_Audio"
    ]
    
    for sub in subfolders:
        folder = DATASET_ROOT / sub
        if folder.exists():
            print(f"Auditing {sub}...")
            audit_data[sub] = audit_directory(folder)
            print(f"  Found {len(audit_data[sub])} files.")
        else:
            print(f"Warning: {sub} not found!")
            
    out_file = Path("/Users/sayemuddin/Desktop/Train_automation/data/manifests/raw_audit_train_video_audio_2.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w") as f:
        json.dump(audit_data, f, indent=2)
    print(f"Audit written to {out_file}")

if __name__ == "__main__":
    main()
