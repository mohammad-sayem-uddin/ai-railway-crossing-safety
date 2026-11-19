"""Exploratory spatial track-corridor and rail-vehicle geometry filters.

Designed strictly as opt-in, exploratory post-hoc mitigations grounded in camera
geometry observations from Mission 11/12 upright inference (never mutating the
frozen v1 baseline configuration or rules):

1. ``is_overhead_ceiling_detection``: rejects top-border overhead structures
   (such as highway/metro flyover decks in ``no_train_events/event_002``) that
   remain pinned to the top edge of the image with vertical center above the
   track corridor (``y_min_norm < top_edge_margin_norm`` and ``y_cen_norm < max_ycen_norm``).
2. ``is_back_rail_vehicle_detection``: retains standard ``side``/``rear`` classes
   and preserves large, high-confidence ``front``-class rail vehicles on the back
   camera (so solitary locomotives such as ``engine_events/event_001`` are treated
   as safety-relevant positives while tiny distant background glares remain filtered).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any


def _normalize_box(
    bbox_xyxy: Sequence[float],
    frame_width: int,
    frame_height: int,
) -> tuple[float, float, float, float, float]:
    """Return ``(ymin_norm, ycen_norm, ymax_norm, area_norm, height_norm)``."""
    w = max(float(frame_width), 1.0)
    h = max(float(frame_height), 1.0)
    x1, y1, x2, y2 = (float(bbox_xyxy[0]), float(bbox_xyxy[1]), float(bbox_xyxy[2]), float(bbox_xyxy[3]))
    ymin_norm = y1 / h
    ymax_norm = y2 / h
    ycen_norm = 0.5 * (y1 + y2) / h
    bw = max(0.0, x2 - x1)
    bh = max(0.0, y2 - y1)
    area_norm = (bw * bh) / (w * h)
    height_norm = bh / h
    return ymin_norm, ycen_norm, ymax_norm, area_norm, height_norm


def is_overhead_ceiling_detection(
    bbox_xyxy: Sequence[float],
    frame_width: int,
    frame_height: int,
    *,
    top_edge_margin_norm: float = 0.05,
    max_ycen_norm: float = 0.35,
) -> bool:
    """Return ``True`` when a box is pinned to the top ceiling above track level."""
    if len(bbox_xyxy) != 4:
        return False
    ymin_norm, ycen_norm, _, _, _ = _normalize_box(bbox_xyxy, frame_width, frame_height)
    return ymin_norm < top_edge_margin_norm and ycen_norm < max_ycen_norm


def filter_detections_track_corridor(
    detections: Iterable[Mapping[str, Any]],
    frame_width: int,
    frame_height: int,
    *,
    conf_threshold: float = 0.35,
    top_edge_margin_norm: float = 0.05,
    max_ycen_norm: float = 0.35,
) -> list[dict[str, Any]]:
    """Keep qualifying detections whose boxes do not represent top-ceiling structures."""
    kept: list[dict[str, Any]] = []
    for det in detections:
        conf = float(det.get("confidence", 0.0))
        if conf < conf_threshold:
            continue
        bbox = det.get("bbox_xyxy")
        if bbox is not None and is_overhead_ceiling_detection(
            bbox,
            frame_width,
            frame_height,
            top_edge_margin_norm=top_edge_margin_norm,
            max_ycen_norm=max_ycen_norm,
        ):
            continue
        kept.append(dict(det))
    return kept


def is_back_rail_vehicle_detection(
    label: str,
    confidence: float,
    bbox_xyxy: Sequence[float] | None,
    frame_width: int,
    frame_height: int,
    *,
    conf_threshold: float = 0.35,
    min_front_area_norm: float = 0.03,
    min_front_conf: float = 0.70,
) -> bool:
    """Accept ``side``/``rear`` classes plus large, high-confidence ``front`` rail vehicles."""
    norm_lbl = str(label).strip().lower()
    if confidence < conf_threshold:
        return False
    if norm_lbl in ("side", "rear"):
        return True
    if norm_lbl != "front" or bbox_xyxy is None or len(bbox_xyxy) != 4:
        return False
    if confidence < min_front_conf:
        return False
    _, _, _, area_norm, _ = _normalize_box(bbox_xyxy, frame_width, frame_height)
    return area_norm >= min_front_area_norm
