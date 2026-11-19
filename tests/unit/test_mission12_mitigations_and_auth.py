"""Synthetic unit tests for Mission 12 exploratory spatial filters and ROI-filtered FSM replay."""

from __future__ import annotations

from railway_detection.fusion.collector import MultimodalFrame
from railway_detection.fusion.decision_engine_v3_four_layer import (
    MultimodalDecisionEngineV3FourLayer,
)
from railway_detection.fusion.evidence import Detection, EvidenceRecord, Modality
from railway_detection.fusion.spatial_filters import (
    filter_detections_track_corridor,
    is_back_rail_vehicle_detection,
    is_overhead_ceiling_detection,
)


def test_overhead_ceiling_detection_rejects_bridge_and_preserves_track_and_tall_trains() -> None:
    """Overhead flyover bridge decks at ceiling are rejected while track/tall trains stay."""
    # Observed overhead bridge deck geometry in 1080x1920 front camera (ycen_norm ~ 0.149)
    bridge_box = [0.0, 0.0, 1080.0, 570.0]
    assert is_overhead_ceiling_detection(bridge_box, 1080, 1920) is True

    # Real track-level train car (ymin_norm = 0.458, ycen_norm = 0.568)
    track_train_box = [80.0, 880.0, 1040.0, 1300.0]
    assert is_overhead_ceiling_detection(track_train_box, 1080, 1920) is False

    # Very tall near-camera train touching top edge but centered low (ycen_norm = 0.417 > 0.35)
    tall_close_train_box = [20.0, 0.0, 1020.0, 1600.0]
    assert is_overhead_ceiling_detection(tall_close_train_box, 1080, 1920) is False

    # Malformed box must fail safe (not reject)
    assert is_overhead_ceiling_detection([10.0, 20.0], 1080, 1920) is False


def test_filter_detections_track_corridor_applies_conf_and_roi() -> None:
    """Track-corridor filter removes overhead ceiling bridge FPs and low-conf noise."""
    detections = [
        {"class_name": "side", "confidence": 0.82, "bbox_xyxy": [0.0, 0.0, 1080.0, 570.0]},
        {"class_name": "side", "confidence": 0.65, "bbox_xyxy": [100.0, 920.0, 980.0, 1240.0]},
        {"class_name": "front", "confidence": 0.30, "bbox_xyxy": [100.0, 920.0, 500.0, 1200.0]},
    ]
    kept = filter_detections_track_corridor(detections, 1080, 1920, conf_threshold=0.35)
    assert len(kept) == 1
    assert kept[0]["confidence"] == 0.65
    assert kept[0]["bbox_xyxy"] == [100.0, 920.0, 980.0, 1240.0]


def test_back_rail_vehicle_detection_preserves_locomotives_and_filters_glare() -> None:
    """Back-camera filter keeps side/rear and large locomotives while dropping tiny front glares."""
    assert is_back_rail_vehicle_detection("side", 0.40, None, 3840, 2160) is True
    assert is_back_rail_vehicle_detection("rear", 0.38, None, 3840, 2160) is True
    assert is_back_rail_vehicle_detection("person", 0.95, [0, 0, 2000, 1500], 3840, 2160) is False

    # Solitary locomotive head-on in 3840x2160 (area ~ 0.12, conf ~ 0.88)
    loco_box = [1400.0, 400.0, 2240.0, 1580.0]
    assert is_back_rail_vehicle_detection("front", 0.88, loco_box, 3840, 2160) is True

    # Tiny distant front-class streetlamp/pillar glare (area ~ 0.005, conf ~ 0.675 or 0.85)
    glare_box = [1800.0, 900.0, 2000.0, 1100.0]
    assert is_back_rail_vehicle_detection("front", 0.675, glare_box, 3840, 2160) is False
    assert is_back_rail_vehicle_detection("front", 0.85, glare_box, 3840, 2160) is False


def test_roi_filtered_detections_prevent_fsm_false_closure_on_synthetic_bridge_stream() -> None:
    """End-to-end synthetic check: ceiling bridge stream triggers raw FSM, stays IDLE after ROI."""
    raw_stream = [
        {"class_name": "side", "confidence": 0.78, "bbox_xyxy": [0.0, 0.0, 1080.0, 560.0]},
    ]
    eng_raw = MultimodalDecisionEngineV3FourLayer(enable_audio_hysteresis_wakeup=True)
    eng_filtered = MultimodalDecisionEngineV3FourLayer(enable_audio_hysteresis_wakeup=True)
    for ts in (0.0, 0.2, 0.4, 0.6):
        raw_dets = tuple(Detection(label=d["class_name"], confidence=d["confidence"]) for d in raw_stream)
        raw_rec = EvidenceRecord(
            timestamp_s=ts,
            source_id="vision_front",
            modality=Modality.VISION,
            available=True,
            detections=raw_dets,
        )
        out_raw = eng_raw.evaluate_frame(MultimodalFrame(master_timestamp_s=ts, vision_records=(raw_rec,)))

        kept = filter_detections_track_corridor(raw_stream, 1080, 1920)
        filt_dets = tuple(Detection(label=d["class_name"], confidence=d["confidence"]) for d in kept)
        filt_rec = EvidenceRecord(
            timestamp_s=ts,
            source_id="vision_front",
            modality=Modality.VISION,
            available=True,
            detections=filt_dets,
        )
        out_filt = eng_filtered.evaluate_frame(MultimodalFrame(master_timestamp_s=ts, vision_records=(filt_rec,)))
        assert out_filt.resulting_state == "IDLE"
    assert out_raw.resulting_state != "IDLE"
