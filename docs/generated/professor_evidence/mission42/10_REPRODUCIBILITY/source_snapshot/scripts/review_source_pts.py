"""Neutral visual frame browser; no annotations, model output or evidence acceptance.

Run only with an actual source-presentation/read permission. Operator arguments
and terminal remain private; the reviewer sees the neutral window only.
"""

from __future__ import annotations

import argparse
import re
from fractions import Fraction
from pathlib import Path

from railway_detection.config.exceptions import ConfigError
from railway_detection.vision.video import VideoFrame, frame_generator


def stamp(frame: VideoFrame) -> Fraction:
    if frame.pts_ticks is None or frame.timebase is None:
        raise ConfigError("source PTS required")
    return frame.pts_ticks * Fraction(*frame.timebase)


def browse(path: Path, stream_index: int, token: str) -> None:
    """Display raw visual frames with explicit original PTS, never source paths.

    Backward navigation re-decodes read-only from the start, retaining no image
    corpus. The existing frame-generator authorization runs on each new pass.
    """
    if re.fullmatch(r"[A-Z][0-9]{3}", token) is None:
        raise ValueError("neutral token must be one letter followed by three digits")
    import cv2

    def reopen():
        return frame_generator(path, source_pts=True, video_stream_index=stream_index)

    frames = reopen()
    current = next(frames)
    title = f"Source review {token}"
    try:
        cv2.namedWindow(title, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(title, 1280, 800)
        while True:
            # Keep the readout outside the source pixels so it hides no landmark.
            image = cv2.copyMakeBorder(current.image, 48, 0, 0, 0, cv2.BORDER_CONSTANT)
            tb = current.timebase
            assert tb is not None
            label = (
                f"{token} frame={current.frame_index} PTS={current.pts_ticks} "
                f"tb={tb[0]}/{tb[1]} stream={current.stream_index}"
            )
            cv2.putText(image, label, (16, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
            cv2.imshow(title, image)
            key = cv2.waitKey(0) & 0xFF
            if key in (ord("q"), 27):
                break
            if key not in (ord("n"), ord("b"), ord("f"), ord("r")):
                continue
            if key in (ord("b"), ord("r")):
                old_index = current.frame_index
                target = stamp(current) - 1
                frames.close()
                frames = reopen()
                for candidate in frames:
                    current = candidate
                    if (key == ord("b") and current.frame_index >= max(0, old_index - 1)) or (
                        key == ord("r") and stamp(current) >= target
                    ):
                        break
            else:
                target = stamp(current) + 1
                for candidate in frames:
                    current = candidate
                    if key == ord("n") or stamp(current) >= target:
                        break
            # At EOF keep the last actual frame; never invent a boundary/exit.
    finally:
        frames.close()
        cv2.destroyWindow(title)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", required=True, type=Path)
    parser.add_argument("--stream-index", required=True, type=int)
    parser.add_argument("--token", required=True, help="neutral operator-assigned token, e.g. Q001")
    args = parser.parse_args()
    browse(args.video, args.stream_index, args.token)


if __name__ == "__main__":
    main()
