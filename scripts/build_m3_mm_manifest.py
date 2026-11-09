#!/usr/bin/env python3
"""Mission 3: build the full-multimodal replay manifest + coverage report.

Anchors on the existing Mission 41/43-era evaluation manifest (located by
content, preferring the file whose SHA-256 starts with the known binding
prefix 61155c9b), keeps its front/audio cache entries untouched, and adds a
hash-bound ``back_vision_cache`` entry per event from the Mission 39 back
run caches. This is ungated data preparation: it reads cache files and
writes NEW artifacts only --

  data/manifests/m3_multimodal_replay_manifest.json
  results/m3_mm_assembly/coverage_report.csv
  results/m3_mm_assembly/assembly_summary.json

Nothing historical is modified. If the anchor manifest cannot be identified
unambiguously, the script lists candidates and stops without writing.
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

ANCHOR_PREFIX = "61155c9b"
ANCHOR_SEARCH_DIRS = [
    ROOT / "docs" / "generated" / "research_results",
    ROOT / "data" / "manifests",
    ROOT / "results",
]
BACK_SEARCH_DIRS = [
    ROOT / "data" / "cache" / "b0_back",
    ROOT / "results" / "experiments" / "cache",
    ROOT / "results",
]
OUT_MANIFEST = ROOT / "data" / "manifests" / "m3_multimodal_replay_manifest.json"
OUT_DIR = ROOT / "results" / "m3_mm_assembly"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def cache_info(rel_path: Path) -> dict:
    data = (ROOT / rel_path).read_bytes()
    lines = [ln for ln in data.decode("utf-8").splitlines() if ln.strip()]
    return {
        "path": rel_path.as_posix(),
        "sha256": sha256_bytes(data),
        "line_count": len(lines),
        "byte_size": len(data),
    }


def find_anchor() -> tuple[Path, dict, str]:
    candidates: list[tuple[Path, dict, str]] = []
    for base in ANCHOR_SEARCH_DIRS:
        if not base.exists():
            continue
        for path in base.rglob("*.json"):
            if path.stat().st_size > 8_000_000:
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if (
                isinstance(data, dict)
                and data.get("manifest_version") == "1.0.0"
                and isinstance(data.get("events"), dict)
                and data["events"]
                and all(
                    isinstance(e, dict) and "front_vision_cache" in e
                    for e in data["events"].values()
                )
            ):
                candidates.append((path, data, sha256_bytes(path.read_bytes())))
    if not candidates:
        raise SystemExit("NO anchor manifest candidates found; stopping.")
    for path, data, digest in candidates:
        if digest.startswith(ANCHOR_PREFIX):
            return path, data, digest
    if len(candidates) == 1:
        path, data, digest = candidates[0]
        print(f"WARNING: single candidate but hash {digest[:12]} lacks known prefix; using it.")
        return path, data, digest
    print("AMBIGUOUS anchor candidates:")
    for path, _data, digest in candidates:
        print(f"  {digest[:12]}  {path.relative_to(ROOT)}")
    raise SystemExit("Anchor ambiguous; stopping without writing.")


def find_back_cache(cohort: str, event_num: int) -> Path | None:
    name = f"{cohort}_event_{event_num:03d}_back.jsonl"
    for base in BACK_SEARCH_DIRS:
        if not base.exists():
            continue
        hits = sorted(base.rglob(name))
        if hits:
            return hits[0].relative_to(ROOT)
    return None


def count_detections(rel_path: Path) -> tuple[int, int]:
    records = 0
    detections = 0
    with open(ROOT / rel_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            records += 1
            try:
                row = json.loads(line)
            except Exception:
                continue
            dets = row.get("detections")
            if isinstance(dets, list):
                detections += len(dets)
    return records, detections


def main() -> int:
    anchor_path, anchor, anchor_sha = find_anchor()
    print(f"anchor: {anchor_path.relative_to(ROOT)} sha256={anchor_sha}")
    events = anchor["events"]
    new_events: dict[str, dict] = {}
    coverage_rows: list[dict] = []

    for event_key in sorted(events):
        entry = dict(events[event_key])
        event_id = entry.get("event_id", event_key)
        # cohort + number from the front cache filename, e.g. train_events_event_001
        front_name = Path(entry["front_vision_cache"]["path"]).name
        stem = front_name.replace("_front.jsonl", "")
        cohort, _, num = stem.rpartition("_event_")
        event_num = int(num)
        back_rel = find_back_cache(cohort, event_num)
        row = {"event_id": event_id, "cohort": cohort}
        for stream, key in (
            ("front_vision", "front_vision_cache"),
            ("front_audio", "front_audio_cache"),
        ):
            if key in entry:
                recs, dets = count_detections(Path(entry[key]["path"]))
                row[f"{stream}_present"] = True
                row[f"{stream}_records"] = recs
                row[f"{stream}_detections"] = dets
            else:
                row[f"{stream}_present"] = False
                row[f"{stream}_records"] = ""
                row[f"{stream}_detections"] = ""
        if back_rel is not None:
            entry["back_vision_cache"] = cache_info(back_rel)
            recs, dets = count_detections(back_rel)
            row["back_vision_present"] = True
            row["back_vision_records"] = recs
            row["back_vision_detections"] = dets
        else:
            row["back_vision_present"] = False
            row["back_vision_records"] = ""
            row["back_vision_detections"] = ""
        coverage_rows.append(row)
        new_events[event_key] = entry

    manifest = {
        "manifest_version": "1.0.0",
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "cohort": f"{anchor.get('cohort', 'phase12')}_m3_multimodal",
        "events": new_events,
    }
    OUT_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    OUT_MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    manifest_sha = sha256_bytes(OUT_MANIFEST.read_bytes())

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fields = [
        "event_id", "cohort",
        "front_vision_present", "front_vision_records", "front_vision_detections",
        "back_vision_present", "back_vision_records", "back_vision_detections",
        "front_audio_present", "front_audio_records", "front_audio_detections",
    ]
    with open(OUT_DIR / "coverage_report.csv", "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(coverage_rows)

    summary = {
        "anchor_manifest": str(anchor_path.relative_to(ROOT)),
        "anchor_manifest_sha256": anchor_sha,
        "new_manifest": str(OUT_MANIFEST.relative_to(ROOT)),
        "new_manifest_sha256": manifest_sha,
        "events_total": len(coverage_rows),
        "events_with_back": sum(1 for r in coverage_rows if r["back_vision_present"]),
        "events_with_audio": sum(1 for r in coverage_rows if r["front_audio_present"]),
    }
    (OUT_DIR / "assembly_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
