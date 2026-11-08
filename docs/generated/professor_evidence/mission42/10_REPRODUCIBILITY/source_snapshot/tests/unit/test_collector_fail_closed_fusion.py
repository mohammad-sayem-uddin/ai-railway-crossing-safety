"""Regression test for the silent-zero-offset-fallback fix in
`MultimodalEvidenceCollector` (R04 Problem E.4).

Before this fix, a vision source not explicitly registered in an attached
`SyncAligner` was silently treated as if it were already on the master
clock (effective offset 0.0). This test pins the fix: an aligner that is
missing a registration for an actively fused vision source must raise,
never silently default to zero offset. Single-camera operation with NO
aligner at all remains unaffected (Problem E.10).
"""

from __future__ import annotations

import pytest

from railway_detection.data.sync import SyncAligner
from railway_detection.fusion.collector import MultimodalEvidenceCollector
from railway_detection.fusion.evidence import EvidenceRecord, Modality


def _vision_record(source_id: str, t: float) -> EvidenceRecord:
    return EvidenceRecord(
        timestamp_s=t,
        source_id=source_id,
        modality=Modality.VISION,
        available=True,
        detections=(),
    )


def _audio_record(source_id: str, t: float) -> EvidenceRecord:
    return EvidenceRecord(
        timestamp_s=t,
        source_id=source_id,
        modality=Modality.AUDIO,
        available=True,
        detections=(),
    )


def test_unregistered_vision_source_with_aligner_raises() -> None:
    aligner = SyncAligner()
    aligner.add_source("camera_1", offset_s=0.0, uncertainty_s=0.0)
    # camera_2 deliberately NOT registered.
    collector = MultimodalEvidenceCollector(sync_aligner=aligner)

    collector.add_evidence(_vision_record("camera_1", 1.0))  # registered: fine
    with pytest.raises(ValueError, match="fail-closed violation"):
        collector.add_evidence(_vision_record("camera_2", 1.0))  # unregistered: must raise


def test_fully_registered_aligner_applies_offset_correctly() -> None:
    aligner = SyncAligner()
    aligner.add_source("camera_1", offset_s=0.0, uncertainty_s=0.0)
    aligner.add_source("camera_2", offset_s=7.406, uncertainty_s=0.05)
    collector = MultimodalEvidenceCollector(sync_aligner=aligner)

    collector.add_evidence(_vision_record("camera_1", 10.0))
    collector.add_evidence(_vision_record("camera_2", 10.0))

    frame = collector.collect_frame(17.406, purge_older_than_s=100.0)
    # camera_2's local t=10.0 should appear at master time 17.406
    assert any(r.source_id == "camera_2" for r in frame.vision_records)


def test_single_camera_no_aligner_is_unaffected() -> None:
    """No aligner attached at all (single-camera, media-local-time mode)
    must continue to work exactly as before -- this is the explicitly
    required independent single-source operating mode."""
    collector = MultimodalEvidenceCollector(sync_aligner=None)
    collector.add_evidence(_vision_record("camera_1", 1.0))  # must not raise
    frame = collector.collect_frame(1.0, purge_older_than_s=100.0)
    assert any(r.source_id == "camera_1" for r in frame.vision_records)


def test_audio_source_exempt_from_registration_requirement() -> None:
    """Audio sources are not independently time-shifted by this aligner
    (they ride on whichever camera's clock they were extracted from); an
    unregistered audio source_id must not raise."""
    aligner = SyncAligner()
    aligner.add_source("camera_1", offset_s=0.0, uncertainty_s=0.0)
    aligner.add_source("camera_2", offset_s=7.406, uncertainty_s=0.05)
    collector = MultimodalEvidenceCollector(sync_aligner=aligner)

    collector.add_evidence(_audio_record("audio_1", 1.0))  # must not raise


# ---------------------------------------------------------------------------
# Collector-level duplicate / out-of-order rejection (Problem E/Task 2).
#
# Added during the Phase 7 independent audit after discovering that NONE of
# the tests above, nor the decision-engine-level duplicate/out-of-order
# tests in test_independent_safety_invariants.py (which exercise the engine
# directly, never routing through MultimodalEvidenceCollector.add_evidence
# at all), actually exercised this specific rejection path. Reverting the
# collector-level fix and re-running the full suite produced ZERO test
# failures -- a real gap in Phase 6's claimed test coverage. These four
# tests close it and were confirmed, by the same revert-and-rerun method,
# to fail when the fix is removed.
# ---------------------------------------------------------------------------


def test_duplicate_observation_rejected_not_buffered() -> None:
    collector = MultimodalEvidenceCollector()
    collector.add_evidence(_vision_record("camera_1", 5.0))
    collector.add_evidence(_vision_record("camera_1", 5.0))  # exact duplicate master_t

    frame = collector.collect_frame(5.0, purge_older_than_s=100.0)
    matching = [r for r in frame.vision_records if r.source_id == "camera_1"]
    assert len(matching) == 1, (
        f"duplicate observation must not be buffered a second time, found {len(matching)} copies"
    )
    assert len(collector.rejected_observations) == 1
    assert collector.rejected_observations[0]["reason"] == "duplicate_observation"
    assert collector.rejected_observations[0]["source_id"] == "camera_1"
    assert collector.rejected_observations[0]["local_timestamp_s"] == 5.0


def test_out_of_order_observation_rejected_not_buffered() -> None:
    collector = MultimodalEvidenceCollector()
    collector.add_evidence(_vision_record("camera_1", 5.0))
    collector.add_evidence(_vision_record("camera_1", 3.0))  # strictly earlier than last ingested

    frame_at_3 = collector.collect_frame(3.0, purge_older_than_s=100.0)
    assert not any(
        r.source_id == "camera_1" and r.timestamp_s == 3.0 for r in frame_at_3.vision_records
    ), "an out-of-order observation must not enter the buffer at all"
    assert len(collector.rejected_observations) == 1
    assert collector.rejected_observations[0]["reason"] == "out_of_order_observation"


def test_different_sources_do_not_falsely_trigger_rejection() -> None:
    """Duplicate/out-of-order rejection is keyed per source_id; interleaved
    ingestion across different sources (the normal production pattern) must
    never falsely reject a legitimate observation."""
    collector = MultimodalEvidenceCollector()
    collector.add_evidence(_vision_record("camera_1", 5.0))
    collector.add_evidence(_vision_record("camera_2", 1.0))  # different source, earlier t: fine
    collector.add_evidence(_audio_record("audio_1", 0.5))  # different source again: fine

    assert collector.rejected_observations == []
    frame = collector.collect_frame(5.0, purge_older_than_s=100.0)
    assert any(r.source_id == "camera_1" for r in frame.vision_records)


def test_in_order_distinct_observations_from_same_source_are_not_rejected() -> None:
    collector = MultimodalEvidenceCollector()
    for t in (0.0, 0.2, 0.4, 0.6, 0.8):
        collector.add_evidence(_vision_record("camera_1", t))
    assert collector.rejected_observations == []
    frame = collector.collect_frame(0.8, purge_older_than_s=100.0)
    assert any(r.source_id == "camera_1" and r.timestamp_s == 0.8 for r in frame.vision_records)
