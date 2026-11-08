#!/usr/bin/env python3
"""Generates frozen parameters and experiment manifests for real-world evaluation."""

from __future__ import annotations

import datetime
import json
import platform
import subprocess
import sys
from pathlib import Path

from railway_detection.experiments.leakage_guard import (
    FROZEN_AUDIO_PATH,
    FROZEN_AUDIO_SHA256,
    FROZEN_PARAMETERS,
    FROZEN_YOLO_PATH,
    FROZEN_YOLO_SHA256,
    compute_sha256,
    verify_checkpoint_immutability,
    verify_no_layer_b_in_training,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_DIR = REPO_ROOT / "results" / "experiments" / "manifests"


def get_git_commit(repo_root: Path) -> str:
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except Exception:
        return "unknown_commit"


def get_installed_packages() -> list[str]:
    try:
        res = subprocess.run(
            [sys.executable, "-m", "pip", "freeze"],
            capture_output=True,
            text=True,
            check=True,
        )
        return [line.strip() for line in res.stdout.splitlines() if line.strip()]
    except Exception:
        return []


def generate_manifests() -> dict[str, Path]:
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now(datetime.UTC).isoformat()

    # 1. Verify integrity before writing manifests
    verify_checkpoint_immutability(REPO_ROOT)
    verify_no_layer_b_in_training(REPO_ROOT)

    # 2. Write frozen_parameters.json
    frozen_params_path = MANIFEST_DIR / "frozen_parameters.json"
    frozen_params_data = {
        "manifest_version": "1.0.0",
        "created_at_utc": timestamp,
        "yolo_checkpoint": {
            "path": FROZEN_YOLO_PATH,
            "sha256": FROZEN_YOLO_SHA256,
        },
        "audio_checkpoint": {
            "path": FROZEN_AUDIO_PATH,
            "sha256": FROZEN_AUDIO_SHA256,
        },
        "parameters": FROZEN_PARAMETERS,
    }
    with open(frozen_params_path, "w", encoding="utf-8") as f:
        json.dump(frozen_params_data, f, indent=2)

    # 3. Write layer_b_event_manifest.json with hashes
    layer_b_src_manifest = REPO_ROOT / "data" / "manifests" / "layer_b_video_manifest.json"
    layer_b_dst_manifest = MANIFEST_DIR / "layer_b_event_manifest.json"
    if layer_b_src_manifest.exists():
        with open(layer_b_src_manifest, "r", encoding="utf-8") as f:
            video_manifest_data = json.load(f)
    else:
        video_manifest_data = []

    with open(layer_b_dst_manifest, "w", encoding="utf-8") as f:
        json.dump(video_manifest_data, f, indent=2)

    # 4. Write experiment_manifest.json
    exp_manifest_path = MANIFEST_DIR / "experiment_manifest.json"
    exp_manifest_data = {
        "experiment_id": f"EXP_REAL_WORLD_{datetime.date.today().strftime('%Y%m%d')}_001",
        "timestamp_utc": timestamp,
        "git_commit": get_git_commit(REPO_ROOT),
        "python_version": sys.version,
        "platform": platform.platform(),
        "packages": get_installed_packages(),
        "frozen_parameters_sha256": compute_sha256(frozen_params_path),
        "layer_b_manifest_sha256": compute_sha256(layer_b_dst_manifest),
    }
    with open(exp_manifest_path, "w", encoding="utf-8") as f:
        json.dump(exp_manifest_data, f, indent=2)

    print(f"Manifests successfully created in {MANIFEST_DIR}:")
    print(f"  - {frozen_params_path.name}")
    print(f"  - {layer_b_dst_manifest.name}")
    print(f"  - {exp_manifest_path.name}")

    return {
        "frozen_parameters": frozen_params_path,
        "layer_b_manifest": layer_b_dst_manifest,
        "experiment_manifest": exp_manifest_path,
    }


if __name__ == "__main__":
    generate_manifests()
