"""Generate synthetic Layer B event bundles for software interface tests.

Mock data is explicitly labeled and must never enter research result tables.
Media files are tiny placeholder binaries, not decodable recordings.
"""

from __future__ import annotations

import json
from pathlib import Path


def make_mock_event_bundle(root: Path, event_id: str = "event_001") -> Path:
    """Create a valid mock Layer B event bundle directory."""
    event_dir = root / event_id
    (event_dir / "labels").mkdir(parents=True, exist_ok=True)

    for name in ("camera_1.mp4", "camera_2.mp4", "audio.wav"):
        (event_dir / name).write_bytes(b"mock-media-placeholder")

    (event_dir / "metadata.json").write_text(
        json.dumps(
            {
                "event_id": event_id,
                "crossing_id": "mock_crossing",
                "session_id": "mock_session",
                "train_direction": "approach_to_departure",
                "weather": "clear",
                "lighting": "day",
                "train_type": "unknown",
                "synchronization_method": "audiovisual_clap",
                "sync_uncertainty_s": 0.1,
                "mock_data": True,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    (event_dir / "geometry.json").write_text(
        json.dumps(
            {
                "geometry_version": "mock-1",
                "crossing_reference_zone": "landmark_annotated",
                "tail_clearance_observable": True,
                "mock_data": True,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    (event_dir / "labels" / "event_labels.json").write_text(
        json.dumps(
            {
                "labels": [
                    {
                        "name": "crossing_entry",
                        "timestamp_s": 10.0,
                        "label_status": "observed",
                        "uncertainty_s": 0.05,
                        "annotator": "mock",
                    },
                    {
                        "name": "tail_clearance",
                        "timestamp_s": 45.0,
                        "label_status": "observed",
                        "uncertainty_s": 0.1,
                        "annotator": "mock",
                    },
                ],
                "mock_data": True,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return event_dir


def make_mock_event_bundle_incomplete(root: Path, event_id: str = "event_bad") -> Path:
    """Create an incomplete mock bundle (missing metadata, empty camera)."""
    event_dir = root / event_id
    event_dir.mkdir(parents=True, exist_ok=True)
    (event_dir / "camera_1.mp4").write_bytes(b"")
    (event_dir / "camera_2.mp4").write_bytes(b"mock")
    return event_dir
