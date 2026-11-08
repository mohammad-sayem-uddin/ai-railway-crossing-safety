"""Regression tests for the single predeclared R04 calibration acceptance rule.

`railway_detection.data.sync_calibration.classify_event` is the ONLY place
that decides CALIBRATION_SUPPORTED / PROVISIONAL / AMBIGUOUS / FAILED /
NOT_ASSESSABLE. These tests pin the rule's boundaries so it cannot drift
back toward "declare success to unblock the pipeline" without a test
failing first, and reproduce the exact finding that motivated this module:
several events in the prior hand-authored report were labeled
CALIBRATION_SUPPORTED while violating the report's own stated
window-consistency criterion.
"""

from __future__ import annotations

import math

from railway_detection.data.sync_calibration import (
    SUPPORTED_GEOMETRIC_JITTER_BOUND_S,
    CorroborationRecord,
    classify_event,
    diagnose_sidelobe_mode,
)


def _diag(lag_s=5.0, psr=2.5, snr=20.0, window_range_s=0.1):
    return {"lag_s": lag_s, "psr": psr, "snr": snr, "window_range_s": window_range_s}


def test_supported_requires_all_four_conditions_simultaneously():
    good = classify_event("e", _diag(), qt_delta_s=5.1)
    assert good.verdict == "CALIBRATION_SUPPORTED"
    assert good.uncertainty_s == SUPPORTED_GEOMETRIC_JITTER_BOUND_S

    # Each single condition failing alone must prevent SUPPORTED.
    low_psr = classify_event("e", _diag(psr=1.9), qt_delta_s=5.1)
    assert low_psr.verdict != "CALIBRATION_SUPPORTED"

    wide_window = classify_event("e", _diag(window_range_s=0.21), qt_delta_s=5.1)
    assert wide_window.verdict != "CALIBRATION_SUPPORTED"

    low_snr = classify_event("e", _diag(snr=14.9), qt_delta_s=5.1)
    assert low_snr.verdict != "CALIBRATION_SUPPORTED"

    bad_qt = classify_event("e", _diag(), qt_delta_s=20.0)
    assert bad_qt.verdict != "CALIBRATION_SUPPORTED"


def test_reproduces_the_original_finding_window_range_violation():
    """These five (event, psr, window_range) pairs are transcribed from the
    prior report's own table for events it labeled CALIBRATION_SUPPORTED
    despite each violating the report's own stated window-consistency
    criterion (< 0.30s). Under the single frozen rule here, none may be
    classified CALIBRATION_SUPPORTED."""
    violators = [
        ("event_001", 2.41, 1.52),
        ("event_005", 2.27, 0.58),
        ("event_007", 5.99, 1.48),
        ("event_009", 2.53, 2.11),
        ("event_015", 2.15, 3.57),
    ]
    for event_id, psr, window_range_s in violators:
        v = classify_event(
            event_id,
            _diag(psr=psr, snr=25.0, window_range_s=window_range_s),
            qt_delta_s=None,
        )
        assert v.verdict != "CALIBRATION_SUPPORTED", (
            f"{event_id}: window_range_s={window_range_s} must not qualify as "
            f"CALIBRATION_SUPPORTED under a rule that caps it at "
            f"{0.20}s, regardless of PSR"
        )


def test_missing_diagnostics_is_not_assessable():
    v = classify_event("e", None, qt_delta_s=None)
    assert v.verdict == "NOT_ASSESSABLE"
    assert v.lag_s is None


def test_estimator_error_is_failed():
    v = classify_event("e", {"error": "empty audio file"}, qt_delta_s=None)
    assert v.verdict == "FAILED"


def test_non_finite_lag_is_failed():
    v = classify_event("e", _diag(lag_s=math.nan), qt_delta_s=None)
    assert v.verdict == "FAILED"


def test_ambiguous_low_psr_no_common_transient():
    v = classify_event("e", _diag(psr=1.05, snr=9.0, window_range_s=3.0), qt_delta_s=None)
    assert v.verdict == "AMBIGUOUS"


def test_provisional_band_requires_moderate_quality():
    v = classify_event("e", _diag(psr=1.6, snr=16.0, window_range_s=0.6), qt_delta_s=4.9)
    assert v.verdict == "PROVISIONAL"


def test_large_metadata_disagreement_without_corroboration_is_ambiguous_even_with_good_acoustics():
    """A device clock drift of tens of seconds (observed for two real events
    in this dataset) must not be papered over by a good acoustic peak alone;
    classification must fail closed without independent corroboration."""
    v = classify_event("e", _diag(psr=3.0, snr=30.0, window_range_s=0.05), qt_delta_s=-33.0)
    assert v.verdict != "CALIBRATION_SUPPORTED"


def test_rule_is_deterministic_and_order_independent():
    """Calling classify_event twice on identical input must give identical
    output -- no hidden state, no per-call randomness."""
    a = classify_event("e", _diag(), qt_delta_s=5.1)
    b = classify_event("e", _diag(), qt_delta_s=5.1)
    assert a == b


def test_uncorroborated_clock_jump_fails_closed():
    """Event with clean acoustic metrics but a large QuickTime clock jump
    (e.g. event_010: lag 2.7158s, QT -17.0s, delta 19.72s) must fail closed
    as AMBIGUOUS when no independent corroboration is provided."""
    diag_010 = _diag(lag_s=2.7158, psr=2.14, snr=22.34, window_range_s=0.0001)
    v = classify_event("train_events/event_010", diag_010, qt_delta_s=-17.0, corroboration=None)
    assert v.verdict == "AMBIGUOUS"
    assert v.uncertainty_s == "unknown"


def test_unverified_corroboration_fails_closed():
    """A corroboration record with verified=False must NOT bypass the metadata
    sanity check and must fail closed as AMBIGUOUS."""
    diag_010 = _diag(lag_s=2.7158, psr=2.14, snr=22.34, window_range_s=0.0001)
    corrob = CorroborationRecord(
        source="visual_landmark",
        verified=False,
        candidate_offset_s=2.716,
        tolerance_s=0.05,
        reviewer=None,
        notes="pending human review",
    )
    v = classify_event("train_events/event_010", diag_010, qt_delta_s=-17.0, corroboration=corrob)
    assert v.verdict == "AMBIGUOUS"


def test_verified_corroboration_promotes_when_acoustics_satisfy_supported():
    """When independent corroboration is verified and candidate offset matches
    the acoustic lag within tolerance, an uncorrupted acoustic estimate
    (PSR >= 2.0, window_range <= 0.20, SNR >= 15) is legitimately promoted
    to CALIBRATION_SUPPORTED despite the QuickTime clock discrepancy."""
    diag_010 = _diag(lag_s=2.7158, psr=2.14, snr=22.34, window_range_s=0.0001)
    corrob = CorroborationRecord(
        source="visual_landmark",
        verified=True,
        candidate_offset_s=2.7158,
        tolerance_s=0.05,
        reviewer="human_reviewer_1",
        evidence_provenance="scratch/r04_visual_review/train_events/event_010/review_record.json",
        notes="locomotive pilot verified at landmark",
    )
    v = classify_event("train_events/event_010", diag_010, qt_delta_s=-17.0, corroboration=corrob)
    assert v.verdict == "CALIBRATION_SUPPORTED"
    assert v.uncertainty_s == SUPPORTED_GEOMETRIC_JITTER_BOUND_S
    assert any("verified by human_reviewer_1 via visual_landmark" in r for r in v.reasons)


def test_verified_corroboration_does_not_promote_if_acoustics_are_poor():
    """Independent corroboration must NEVER paper over unstable or low-quality
    acoustic evidence (e.g. PSR < 2.0 or window_range > 0.20s)."""
    poor_acoustics = _diag(lag_s=3.0, psr=1.2, snr=12.0, window_range_s=0.50)
    corrob = CorroborationRecord(
        source="visual_landmark",
        verified=True,
        candidate_offset_s=3.0,
        tolerance_s=0.05,
        reviewer="human_reviewer_1",
        evidence_provenance="scratch/r04_visual_review/train_events/event_004/review_record.json",
    )
    v = classify_event("e", poor_acoustics, qt_delta_s=10.0, corroboration=corrob)
    assert v.verdict != "CALIBRATION_SUPPORTED"


def test_mismatched_corroboration_fails_closed():
    """If candidate offset from corroboration disagrees with acoustic lag
    beyond tolerance, the event must fail closed as AMBIGUOUS."""
    diag_010 = _diag(lag_s=2.7158, psr=2.14, snr=22.34, window_range_s=0.0001)
    mismatched = CorroborationRecord(
        source="visual_landmark",
        verified=True,
        candidate_offset_s=5.0000,  # disagrees with acoustic 2.7158 by 2.28s
        tolerance_s=0.50,
        reviewer="human_reviewer_1",
        evidence_provenance="scratch/r04_visual_review/train_events/event_010/review_record.json",
    )
    v = classify_event("train_events/event_010", diag_010, qt_delta_s=-17.0, corroboration=mismatched)
    assert v.verdict == "AMBIGUOUS"


def test_corroboration_validation_rejects_missing_or_empty_reviewer():
    """CorroborationRecord must reject empty or missing reviewer."""
    rec = CorroborationRecord(
        source="visual_landmark",
        verified=True,
        candidate_offset_s=2.7158,
        reviewer="",
        evidence_provenance="scratch/path/review.json",
    )
    errors = rec.validate()
    assert any("reviewer identity is required" in e for e in errors)
    assert not rec.is_valid


def test_corroboration_validation_rejects_prohibited_automated_reviewer():
    """CorroborationRecord must reject self-asserted automated/AI agents."""
    for bad in ["agent", "ai", "assistant", "automated", "synthetic", "bot", "auto"]:
        rec = CorroborationRecord(
            source="visual_landmark",
            verified=True,
            candidate_offset_s=2.7158,
            reviewer=bad,
            evidence_provenance="scratch/path/review.json",
        )
        errors = rec.validate()
        assert any("prohibited automated/unspecified identity" in e for e in errors)
        assert not rec.is_valid


def test_corroboration_validation_rejects_missing_evidence_provenance():
    """CorroborationRecord must reject missing evidence_provenance."""
    rec = CorroborationRecord(
        source="visual_landmark",
        verified=True,
        candidate_offset_s=2.7158,
        reviewer="human_reviewer_1",
        evidence_provenance=None,
    )
    errors = rec.validate()
    assert any("evidence_provenance is required" in e for e in errors)
    assert not rec.is_valid


def test_corroboration_validation_rejects_invalid_source_and_tolerance():
    """CorroborationRecord must reject invalid sources or unreasonable tolerance."""
    rec_bad_src = CorroborationRecord(
        source="container_metadata",
        verified=True,
        candidate_offset_s=2.7158,
        tolerance_s=0.05,
        reviewer="human_reviewer_1",
        evidence_provenance="scratch/path/review.json",
    )
    assert any("source 'container_metadata' is invalid" in e for e in rec_bad_src.validate())

    rec_bad_tol = CorroborationRecord(
        source="visual_landmark",
        verified=True,
        candidate_offset_s=2.7158,
        tolerance_s=-0.1,
        reviewer="human_reviewer_1",
        evidence_provenance="scratch/path/review.json",
    )
    assert any("tolerance_s must be a positive finite float <= 1.00s" in e for e in rec_bad_tol.validate())

    rec_excessive_tol = CorroborationRecord(
        source="visual_landmark",
        verified=True,
        candidate_offset_s=2.7158,
        tolerance_s=5.0,  # > 1.00s
        reviewer="human_reviewer_1",
        evidence_provenance="scratch/path/review.json",
    )
    assert any("tolerance_s must be a positive finite float <= 1.00s" in e for e in rec_excessive_tol.validate())


def test_corroboration_dict_parsing_and_contract_enforcement():
    """Dictionaries passed to classify_event must undergo identical contract validation."""
    diag_010 = _diag(lag_s=2.7158, psr=2.14, snr=22.34, window_range_s=0.0001)

    # Valid dict promotes
    valid_dict = {
        "source": "visual_landmark",
        "verified": True,
        "candidate_offset_s": 2.7158,
        "tolerance_s": 0.05,
        "reviewer": "human_reviewer_1",
        "evidence_provenance": "scratch/r04_visual_review/train_events/event_010/review_record.json",
    }
    v = classify_event("train_events/event_010", diag_010, qt_delta_s=-17.0, corroboration=valid_dict)
    assert v.verdict == "CALIBRATION_SUPPORTED"

    # Self-asserted agent dict fails closed
    fake_dict = {
        "source": "visual_landmark",
        "verified": True,
        "candidate_offset_s": 2.7158,
        "tolerance_s": 0.05,
        "reviewer": "agent",
        "evidence_provenance": "scratch/r04_visual_review/train_events/event_010/review_record.json",
    }
    v_fake = classify_event("train_events/event_010", diag_010, qt_delta_s=-17.0, corroboration=fake_dict)
    assert v_fake.verdict == "AMBIGUOUS"


def test_diagnose_sidelobe_mode_taxonomy():
    """Verify that diagnose_sidelobe_mode faithfully classifies failure modes."""
    # Fully supported
    assert diagnose_sidelobe_mode(7.406, 7.1495, 2.24, 24.27, 0.0001, 0.59) == "SUPPORTED"
    # Metadata clock jump (event_010)
    assert diagnose_sidelobe_mode(2.7158, 1.8612, 2.14, 22.34, 0.0001, 19.72) == "METADATA_CLOCK_DISCREPANCY"
    # Adjacent shoulder (no_train_003: delta = 51.3 ms)
    assert diagnose_sidelobe_mode(-0.4022, -0.3509, 1.96, 21.18, 0.0003, 0.40) == "ADJACENT_SHOULDER"
    # Harmonic periodicity (event_023: delta = 257.9 ms)
    assert diagnose_sidelobe_mode(1.2277, 0.9698, 1.29, 14.40, 0.0048, 0.23) == "HARMONIC_PERIODICITY"
    # Competing multipath (event_004: window_range = 0.2394s, psr = 1.15)
    assert diagnose_sidelobe_mode(4.9001, 5.1398, 1.15, 24.96, 0.2394, 0.10) == "COMPETING_MULTIPATH"
    # Temporal drift (event_015: window_range = 11.32s)
    assert diagnose_sidelobe_mode(11.4404, 11.6479, 1.90, 21.18, 11.3229, 0.56) == "TEMPORAL_WINDOW_DRIFT"
    # Complete decorrelation (event_020: psr = 1.01, snr = 9.11)
    assert diagnose_sidelobe_mode(-0.0284, 0.4341, 1.01, 9.11, 6.5232, 4.03) == "CORRELATION_DECORRELATION"

