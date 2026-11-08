"""Unit tests for video frame selection and timestamp math.

The cv2-dependent generator is not exercised here (no real video fixtures);
the pure functions that define its behavior are fully covered.
"""

from __future__ import annotations

import pytest

from railway_detection.vision.video import (
    select_frame_indices,
    timestamps_for_frames,
)


def test_timestamps_from_fps():
    assert timestamps_for_frames([0, 1, 2], 10.0) == [0.0, 0.1, 0.2]
    assert timestamps_for_frames([30], 30.0) == [1.0]


def test_timestamps_reject_nonpositive_fps():
    with pytest.raises(ValueError):
        timestamps_for_frames([0], 0.0)
    with pytest.raises(ValueError):
        timestamps_for_frames([0], -1.0)


def test_select_all_frames_when_no_sampling():
    assert select_frame_indices(5, native_fps=30.0) == [0, 1, 2, 3, 4]


def test_select_by_stride():
    assert select_frame_indices(10, native_fps=30.0, stride=3) == [0, 3, 6, 9]


def test_select_by_target_fps():
    # 30 native FPS sampled at 10 Hz -> every 3rd frame.
    assert select_frame_indices(10, native_fps=30.0, target_fps=10.0) == [0, 3, 6, 9]


def test_target_fps_and_stride_conflict():
    with pytest.raises(ValueError):
        select_frame_indices(10, native_fps=30.0, target_fps=10.0, stride=2)


def test_empty_and_invalid_inputs():
    assert select_frame_indices(0, native_fps=30.0) == []
    assert select_frame_indices(-1, native_fps=30.0) == []
    with pytest.raises(ValueError):
        select_frame_indices(10, native_fps=30.0, stride=0)
    with pytest.raises(ValueError):
        select_frame_indices(10, native_fps=0.0, target_fps=5.0)


def test_deterministic_selection():
    first = select_frame_indices(100, native_fps=25.0, target_fps=5.0)
    second = select_frame_indices(100, native_fps=25.0, target_fps=5.0)
    assert first == second
    assert len(first) == len(set(first))
