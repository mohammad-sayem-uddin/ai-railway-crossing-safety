"""Build the FULL 27-event multimodal replay manifest (Mission 3, v2).

Anchors on the genuine Mission 43 assembly manifest
(docs/generated/professor_evidence/mission43/B2_EVALUATION_INPUT_MANIFEST.json,
sha256 2fb08c92e6d389e55e3963c0f47f0d7fa7959922f39b9b4b600f244a57a46b72),
whose events dict records front_vision_cache / front_audio_cache paths AND
their sha256 values. Every front/audio file is re-hashed and checked against
the recorded value; a mismatch aborts the build. Back-camera predictions are
resolved per event: Mission 43 predictions first, else the Mission 39
predictions (the 5 pilot events), giving complete 27/27 back coverage.

Output schema matches the Mission 39 replay manifests consumed by
CacheOnlyReplayEngine / CacheOnlyMultimodalReplayEngine.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import sys

ROOT = "/Users/sayemuddin/Desktop/Train_automation"
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, "src"))

ANCHOR = ("docs/generated/professor_evidence/mission43/"
          "B2_EVALUATION_INPUT_MANIFEST.json")
ANCHOR_SHA = "2fb08c92e6d389e55e3963c0f47f0d7fa7959922f39b9b4b600f244a57a46b72"
BACK_DIRS = [
    ("mission43", "docs/generated/professor_evidence/mission43/predictions"),
    ("mission39", "docs/generated/research_results/mission39/predictions"),
]
OUT_MANIFEST = "data/manifests/m3_multimodal_replay_manifest.json"
OUT_DIR = "results/m3_mm_assembly"


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    anchor_sha = sha256_of(ANCHOR)
    assert anchor_sha == ANCHOR_SHA, f"anchor hash drift: {anchor_sha}"
    anchor = json.load(open(ANCHOR))
    events = anchor["events"]
    assert isinstance(events, dict) and len(events) == 27, len(events)

    entries, coverage = [], []
    problems = []
    for event_id, ev in events.items():
        front = ev.get("front_vision_cache") or {}
        audio = ev.get("front_audio_cache") or {}
        f_path, a_path = front.get("path"), audio.get("path")
        key = os.path.basename(f_path).replace("_front.jsonl", "") if f_path \
            else event_id.replace("/", "_")
        for label, spec in (("front", front), ("audio", audio)):
            p, recorded = spec.get("path"), spec.get("sha256")
            if p is None:
                continue
            if not os.path.exists(p):
                problems.append(f"{key}: {label} missing {p}")
            elif recorded and sha256_of(p) != recorded:
                problems.append(f"{key}: {label} HASH MISMATCH {p}")
        back_path = back_src = None
        for label, d in BACK_DIRS:
            cand = os.path.join(d, key + "_back.jsonl")
            if os.path.exists(cand):
                back_path, back_src = cand, label
                break
        if back_path is None:
            problems.append(f"{key}: no back predictions found")
        entries.append({
            "event_key": key,
            "event_id": event_id,
            "front_cache_path": f_path,
            "front_cache_sha256": front.get("sha256"),
            "audio_cache_path": a_path,
            "audio_cache_sha256": audio.get("sha256"),
            "back_cache_path": back_path,
            "back_cache_sha256": sha256_of(back_path) if back_path else None,
            "back_source": back_src,
        })
        coverage.append({
            "event_key": key, "event_id": event_id,
            "front": bool(f_path), "audio": bool(a_path),
            "back": back_path is not None, "back_source": back_src or "",
        })

    manifest = {
        "manifest_version": "1.0.0",
        "mission": "mission3_master_research_completion",
        "anchor_manifest": ANCHOR,
        "anchor_manifest_sha256": anchor_sha,
        "events": entries,
    }
    os.makedirs(os.path.dirname(OUT_MANIFEST), exist_ok=True)
    with open(OUT_MANIFEST, "w") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "coverage_report.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(coverage[0].keys()))
        w.writeheader()
        w.writerows(coverage)
    summary = {
        "events": len(entries),
        "with_back": sum(c["back"] for c in coverage),
        "with_audio": sum(c["audio"] for c in coverage),
        "problems": problems,
        "manifest_sha256": sha256_of(OUT_MANIFEST),
    }
    with open(os.path.join(OUT_DIR, "assembly_summary.json"), "w") as fh:
        json.dump(summary, fh, indent=2, sort_keys=True)
    print(json.dumps(summary, indent=2))
    print("BUILDER_V2_DONE")


if __name__ == "__main__":
    main()
