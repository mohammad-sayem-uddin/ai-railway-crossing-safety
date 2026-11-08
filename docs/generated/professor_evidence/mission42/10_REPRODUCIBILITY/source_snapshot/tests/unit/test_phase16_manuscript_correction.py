"""Phase 16 correction is additive and remains within the evidence boundary."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORRECTION = ROOT / "docs/PHASE16_MANUSCRIPT_CORRECTION_v1.md"


def test_versioned_correction_is_evidence_limited_and_preserves_historical_source():
    text = CORRECTION.read_text(encoding="utf-8")
    assert (ROOT / "Railway_Crossing_Automation_Research_Report.docx").is_file()
    assert "Original preserved" in text
    assert "No official Layer B result" in text
    assert "[evidence: experiments/vision/39f402dfe460/evaluation/metrics.json]" in text
    # The correction must not reintroduce the historical safety overclaims.
    assert "guarantees train clearance" not in text.lower()
    assert "eliminating catastrophic premature-opening risk" not in text.lower()


def test_correction_does_not_reference_prohibited_checkpoint_path():
    text = CORRECTION.read_text(encoding="utf-8")
    assert "models/audio/best_checkpoint.pt" not in text