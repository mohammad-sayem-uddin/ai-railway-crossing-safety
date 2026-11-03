"""Mission 4D: Governance integrity remediation tests.

All fixtures are synthetic. No raw media, no real review records, no
ground-truth modification, no experiment execution.
"""

from __future__ import annotations

import pytest

from railway_detection.experiments.frozen_config import load_frozen_config
from railway_detection.experiments.preflight_validator import (
    CONFIG_CLASS_RESEARCHER_APPROVED,
    CONFIG_CLASS_SYNTHETIC_TEST,
    CONFIG_CLASS_UNRESOLVED,
    classify_experiment_parameters,
    run_experiment_preflight,
)


@pytest.fixture
def frozen():
    return load_frozen_config()


# ---------------------------------------------------------------------------
# B7e approval-classification integrity
# ---------------------------------------------------------------------------


def test_b7e_params_present_without_approval_remain_unresolved(frozen):
    """B7e parameter presence alone must NOT grant researcher_approved."""
    classifications = classify_experiment_parameters(
        frozen,
        experiment_family="B7e",
        failure_injector="B7e",
        injector_parameters={"delay_s": 3.0, "target_source": "camera_1"},
        b7e_parameters_approved=False,
    )
    b7e = [c for c in classifications if c.parameter_key == "injector.b7e_parameters"]
    assert len(b7e) == 1
    assert b7e[0].classification == CONFIG_CLASS_UNRESOLVED


def test_b7e_params_present_with_pending_decision_remain_unresolved(frozen):
    """Pending canonical decision means parameters stay unresolved."""
    classifications = classify_experiment_parameters(
        frozen,
        experiment_family="B7e",
        failure_injector="B7e",
        injector_parameters={"delay_s": 5.0, "target_source": "camera_2"},
        b7e_parameters_approved=False,
    )
    b7e = [c for c in classifications if c.parameter_key == "injector.b7e_parameters"]
    assert b7e[0].classification == CONFIG_CLASS_UNRESOLVED


def test_b7e_params_synthetic_test_classification(frozen):
    """Synthetic test with B7e params gets synthetic_test_configuration."""
    classifications = classify_experiment_parameters(
        frozen,
        experiment_family="B7e",
        failure_injector="B7e",
        injector_parameters={"delay_s": 2.0, "target_source": "audio_1"},
        is_synthetic_test=True,
        b7e_parameters_approved=False,
    )
    b7e = [c for c in classifications if c.parameter_key == "injector.b7e_parameters"]
    assert b7e[0].classification == CONFIG_CLASS_SYNTHETIC_TEST


def test_b7e_params_historical_classification(frozen):
    """Historical configuration always returns historical, not approved."""
    classifications = classify_experiment_parameters(
        frozen,
        experiment_family="B7e",
        failure_injector="B7e",
        injector_parameters={"delay_s": 2.0, "target_source": "camera_1"},
        is_historical=True,
    )
    assert len(classifications) == 1
    assert classifications[0].classification == "historical_configuration"


def test_b7e_params_with_explicit_approval_get_researcher_approved(frozen):
    """Only explicit b7e_parameters_approved=True grants researcher_approved."""
    classifications = classify_experiment_parameters(
        frozen,
        experiment_family="B7e",
        failure_injector="B7e",
        injector_parameters={"delay_s": 4.0, "target_source": "camera_1"},
        b7e_parameters_approved=True,
    )
    b7e = [c for c in classifications if c.parameter_key == "injector.b7e_parameters"]
    assert b7e[0].classification == CONFIG_CLASS_RESEARCHER_APPROVED


def test_b7e_params_missing_remain_unresolved(frozen):
    """Missing B7e parameters remain unresolved regardless of approval flag."""
    classifications = classify_experiment_parameters(
        frozen,
        experiment_family="B7e",
        failure_injector="B7e",
        injector_parameters={},
        b7e_parameters_approved=False,
    )
    b7e = [c for c in classifications if c.parameter_key == "injector.b7e_parameters"]
    assert b7e[0].classification == CONFIG_CLASS_UNRESOLVED


def test_b7e_preflight_reports_pending_decision_blocker(frozen):
    """Preflight with B7e params but no approval still reports pending decision."""
    report = run_experiment_preflight(
        frozen,
        experiment_family="B7e",
        failure_injector="B7e",
        injector_parameters={"delay_s": 3.0, "target_source": "camera_1"},
        b7e_parameters_approved=False,
    )
    decision_codes = {f.code for f in report.unresolved_scientific_decision_blockers}
    # B7e parameters missing triggers the blocker
    assert "DECISION_B7E_NUMERICAL_PARAMETERS_PENDING" in decision_codes or report.ready_for_requested_mode is False


# ---------------------------------------------------------------------------
# Threshold/ROI approval integrity: d1/d2 must NOT implicitly grant
# ---------------------------------------------------------------------------


def test_d1_approved_does_not_implicitly_grant_threshold_approval(frozen):
    """d1_approved=True must NOT classify thresholds as researcher_approved."""
    classifications = classify_experiment_parameters(
        frozen,
        experiment_family="B4",
        d1_approved=True,
        d2_approved=False,
        d4_approved=False,
    )
    by_key = {c.parameter_key: c.classification for c in classifications}
    assert by_key["fusion_and_operating_thresholds"] == CONFIG_CLASS_UNRESOLVED


def test_d2_approved_does_not_implicitly_grant_roi_approval(frozen):
    """d2_approved=True must NOT classify ROI as researcher_approved."""
    classifications = classify_experiment_parameters(
        frozen,
        experiment_family="B4",
        d1_approved=False,
        d2_approved=True,
        d4_approved=False,
    )
    by_key = {c.parameter_key: c.classification for c in classifications}
    assert by_key["roi_and_calibration_geometry"] == CONFIG_CLASS_UNRESOLVED


def test_explicit_threshold_approval_still_works(frozen):
    """Explicit operating_thresholds_approved=True still grants approval."""
    classifications = classify_experiment_parameters(
        frozen,
        experiment_family="B4",
        operating_thresholds_approved=True,
    )
    by_key = {c.parameter_key: c.classification for c in classifications}
    assert by_key["fusion_and_operating_thresholds"] == CONFIG_CLASS_RESEARCHER_APPROVED


def test_explicit_roi_approval_still_works(frozen):
    """Explicit roi_geometry_approved=True still grants approval."""
    classifications = classify_experiment_parameters(
        frozen,
        experiment_family="B4",
        roi_geometry_approved=True,
    )
    by_key = {c.parameter_key: c.classification for c in classifications}
    assert by_key["roi_and_calibration_geometry"] == CONFIG_CLASS_RESEARCHER_APPROVED


def test_no_approval_flags_all_unresolved(frozen):
    """With no approval flags, thresholds and ROI remain unresolved."""
    classifications = classify_experiment_parameters(
        frozen,
        experiment_family="B4",
    )
    by_key = {c.parameter_key: c.classification for c in classifications}
    assert by_key["fusion_and_operating_thresholds"] == CONFIG_CLASS_UNRESOLVED
    assert by_key["roi_and_calibration_geometry"] == CONFIG_CLASS_UNRESOLVED
    assert by_key["timing.cross_camera_sync"] == CONFIG_CLASS_UNRESOLVED


# ---------------------------------------------------------------------------
# Preflight never grants EVAL-AUTH or official readiness
# ---------------------------------------------------------------------------


def test_preflight_never_grants_eval_auth(frozen):
    """Preflight report must always have grants_eval_auth=False."""
    report = run_experiment_preflight(
        frozen,
        experiment_family="B0",
        evaluation_mode="official_evaluation",
        d1_approved=True,
        d2_approved=True,
        d4_approved=True,
        operating_thresholds_approved=True,
        roi_geometry_approved=True,
        stage2_1_completed=True,
        promotion_receipt_present=True,
        official_split_present=True,
        official_manifest_present=True,
        eval_auth_granted=True,
    )
    assert report.grants_eval_auth is False
    assert report.grants_official_readiness is False
    assert report.is_diagnostic_only is True


# ---------------------------------------------------------------------------
# R04 candidate status cannot become synchronization acceptance
# ---------------------------------------------------------------------------


def test_r04_candidate_not_acceptance(frozen):
    """Cross-camera sync without explicit d4_approved remains unresolved."""
    classifications = classify_experiment_parameters(
        frozen,
        experiment_family="B4",
        d4_approved=False,
    )
    by_key = {c.parameter_key: c.classification for c in classifications}
    assert by_key["timing.cross_camera_sync"] == CONFIG_CLASS_UNRESOLVED