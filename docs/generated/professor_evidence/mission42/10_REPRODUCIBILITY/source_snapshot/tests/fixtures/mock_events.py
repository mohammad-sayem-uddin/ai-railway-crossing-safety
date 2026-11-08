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


def make_realistic_mock_event_cohort(root: Path, count: int = 5) -> list[Path]:
    """Generate a diverse cohort of mock Layer B event bundles for end-to-end integration testing."""
    event_paths: list[Path] = []
    root.mkdir(parents=True, exist_ok=True)

    for i in range(1, count + 1):
        event_id = f"real_mock_{i:03d}"
        event_dir = root / event_id
        event_dir.mkdir(parents=True, exist_ok=True)
        (event_dir / "labels").mkdir(parents=True, exist_ok=True)

        # Vary camera naming across events
        if i % 2 == 1:
            cam1_name, cam2_name = "camera_front.mp4", "camera_rear.mp4"
        else:
            cam1_name, cam2_name = "camera_1.mp4", "camera_2.mp4"

        (event_dir / cam1_name).write_bytes(b"mock-video-front-stream")
        (event_dir / cam2_name).write_bytes(b"mock-video-rear-stream")
        (event_dir / "audio.wav").write_bytes(b"mock-audio-wav-stream")

        # Entry at 8.0s, clearance at 16.0s
        (event_dir / "labels" / "event_labels.json").write_text(
            json.dumps(
                {
                    "labels": [
                        {
                            "name": "crossing_entry",
                            "timestamp_s": 8.0,
                            "label_status": "observed",
                            "uncertainty_s": 0.1,
                        },
                        {
                            "name": "tail_clearance",
                            "timestamp_s": 16.0,
                            "label_status": "observed",
                            "uncertainty_s": 0.1,
                        },
                    ],
                    "mock_data": True,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        (event_dir / "geometry.json").write_text(
            json.dumps({"geometry_version": "v1.0", "crossing_id": f"crossing_{i:02d}"}, indent=2),
            encoding="utf-8",
        )

        # For event 3, omit metadata.json to test non-strict ingestion
        if i != 3:
            (event_dir / "metadata.json").write_text(
                json.dumps(
                    {
                        "event_id": event_id,
                        "crossing_id": f"crossing_{i:02d}",
                        "weather": "clear" if i % 2 == 1 else "rain",
                        "lighting": "day" if i < 4 else "night",
                        "sync_method": "audiovisual_clap",
                        "sync_uncertainty_s": 0.05,
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )

        event_paths.append(event_dir)

    return event_paths

