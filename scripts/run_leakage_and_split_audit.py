#!/usr/bin/env python
"""Generate non-destructive dataset leakage audits and clean grouped splits.

Never touches raw media under ``data/raw/``. Operates strictly on verified manifests
and split JSON/JSONL records.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from railway_detection.data.leakage_audit import (
    audit_audio_split,
    audit_vision_partition,
    build_session_grouped_vision_split,
    build_stem_grouped_audio_split,
)

ROOT = Path(__file__).resolve().parent.parent


def _load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(r, sort_keys=True) for r in rows) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--gap-s", type=float, default=600.0)
    args = ap.parse_args()
    root: Path = args.root

    vis_rows = _load_jsonl(root / "results/dataset_validation/dataset_manifest.jsonl")

    # 1. Audit historical 705d388743ea split
    s705d_map: dict[str, str] = {}
    for sp in ("train", "val", "test"):
        for r in _load_jsonl(root / f"data/splits/705d388743ea/{sp}.jsonl"):
            s705d_map[r["sample_id"]] = sp
    audit_705d = audit_vision_partition(vis_rows, s705d_map)

    # 2. Audit original Roboflow directory split
    rf_map: dict[str, str] = {}
    for r in vis_rows:
        sd = r.get("provenance", {}).get("split_dir", "train")
        rf_map[r["image_id"]] = "val" if sd == "valid" else sd
    audit_rf = audit_vision_partition(vis_rows, rf_map)

    # 3. Construct non-destructive session-grouped Vision V1 split
    vis_records, vis_clean_summary = build_session_grouped_vision_split(vis_rows, gap_s=args.gap_s)
    vis_out_dir = root / "data/splits/vision_v1_session_grouped"
    for sp in ("train", "val", "test"):
        _write_jsonl(vis_out_dir / f"{sp}.jsonl", vis_records[sp])
    _write_json(vis_out_dir / "split_summary.json", vis_clean_summary)

    # 4. Audit Audio V3 + construct non-destructive stem-grouped Audio V3 split
    v3_audio = json.loads((root / "data/splits/audio/v3/dataset_split.json").read_text(encoding="utf-8"))
    new_audio, audio_summary = build_stem_grouped_audio_split(v3_audio)
    audio_out_dir = root / "data/splits/audio_v3_stem_grouped"
    _write_json(audio_out_dir / "dataset_split.json", new_audio)
    _write_json(audio_out_dir / "split_summary.json", audio_summary)

    combined_report = {
        "schema_version": "dataset-leakage-audit/1.0",
        "raw_media_accessed": False,
        "vision_original_roboflow": audit_rf,
        "vision_705d388743ea": audit_705d,
        "vision_session_grouped_candidate": vis_clean_summary,
        "audio_v3_original": audit_audio_split(v3_audio),
        "audio_v3_stem_grouped_candidate": audio_summary["audit_stem_grouped"],
    }
    out_report = root / "results/dataset_audit/vision_audio_leakage_audit.json"
    _write_json(out_report, combined_report)
    print(json.dumps({
        "status": "OK",
        "vision_705d_crossing_600s": next(s for s in audit_705d["temporal_session_sweeps"] if s["gap_s"] == 600.0),
        "vision_clean_counts": vis_clean_summary["audit"]["split_image_counts"],
        "vision_clean_crossing_600s": next(s for s in vis_clean_summary["audit"]["temporal_session_sweeps"] if s["gap_s"] == 600.0),
        "audio_v3_leaked_stems": combined_report["audio_v3_original"]["cross_split_positive_stem_count"],
        "audio_clean_leaked_stems": combined_report["audio_v3_stem_grouped_candidate"]["cross_split_positive_stem_count"],
        "report": str(out_report),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
