"""Shared synthetic fixtures for the Mission 14 security regression tests.

Everything here builds a *fake repository* in a temporary directory and points
``media_guard.REAL_REPO_ROOT`` at it, so no test ever stats, opens or lists a path inside the real
checkout.  The file name does not start with ``test_`` on purpose: it is a helper, not a test.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import pytest

from railway_detection.safety import media_guard

EVENT = "train_events/event_001"


@dataclass
class FakeRepo:
    root: Path

    @property
    def raw_dir(self) -> Path:
        return self.root / "data/raw/layer_b/v2" / EVENT

    @property
    def video(self) -> Path:
        return self.raw_dir / "camera_front.mov"

    @property
    def other_raw(self) -> Path:
        return self.raw_dir / "camera_back.mov"

    def make(self) -> FakeRepo:
        for rel in (
            "data/raw/layer_b/v2/" + EVENT,
            "data/manifests",
            "data/governance",
            "data/ground_truth/reviews",
            "configs",
            "outputs/video_tests/run1",
            "experiments/vision/run1/evaluation",
            "experiments/vision/run1/checkpoints/weights",
            "results",
            "scratch",
        ):
            (self.root / rel).mkdir(parents=True, exist_ok=True)
        self.video.write_bytes(b"SYNTHETIC-FRONT-MEDIA")
        self.other_raw.write_bytes(b"SYNTHETIC-BACK-MEDIA")
        return self


def make_fake_repo(
    tmp_path_factory, monkeypatch: pytest.MonkeyPatch, name: str = "FakeRepo"
) -> FakeRepo:
    root = (tmp_path_factory.mktemp("fakerepo") / name).resolve()
    root.mkdir()
    repo = FakeRepo(root).make()
    monkeypatch.setattr(media_guard, "REAL_REPO_ROOT", root)
    return repo


def outside_dir(tmp_path_factory, name: str = "outside") -> Path:
    path = (tmp_path_factory.mktemp(name)).resolve()
    return path


def case_variant(path: Path) -> Path:
    """Same location spelled with different case in the last component of the repo root."""
    return path.parent / path.name.swapcase()


def filesystem_is_case_insensitive(path: Path) -> bool:
    alt = case_variant(path)
    return alt != path and alt.exists() and os.path.samefile(alt, path)


requires_case_insensitive = pytest.mark.skipif(
    False, reason="evaluated per test via filesystem_is_case_insensitive"
)
