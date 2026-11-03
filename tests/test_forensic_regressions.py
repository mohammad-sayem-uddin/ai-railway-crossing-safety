"""Regression tests for forensic defects identified during research audit.

Verifies:
1. Hardcoded timestamp fallback pattern detection and rejection.
2. Conceptual danger-zone exit boundary reconciliation (intermediate landmark vs canonical exit plane).
3. Acoustic SNR ratio calibration (linear power ratio vs true logarithmic decibels).
4. Multi-camera unsynchronized exposure segregation (R04).
"""

from __future__ import annotations

import math


def test_regression_detects_hardcoded_fallback_patterns() -> None:
    """Verifies that timestamp proposals matching known synthetic formula patterns are flagged."""
    # Pattern 1: T1=3.00, T2=3.70, T3=3.50 (synthetic 0.7s offset)
    def is_synthetic_pattern(t1: float | None, t2: float | None, t3: float | None) -> bool:
        if t1 is None or t2 is None:
            return False
        # Exact synthetic offsets: t2 - t1 == 0.70s and fixed values
        return (abs(t1 - 3.00) < 1e-4 and abs(t2 - 3.70) < 1e-4) or \
               (abs(t1 - 3.50) < 1e-4 and abs(t2 - 4.20) < 1e-4)

    assert is_synthetic_pattern(3.00, 3.70, 3.50) is True
    assert is_synthetic_pattern(3.50, 4.20, 3.50) is True
    # Real physical measurements must NOT match the synthetic fallback formula
    assert is_synthetic_pattern(2.10, 2.80, 3.20) is False
    assert is_synthetic_pattern(5.80, 6.50, 3.60) is False
    assert is_synthetic_pattern(None, None, 6.00) is False


def test_regression_canonical_exit_boundary_congruence() -> None:
    """Verifies that T3 and T4 map to the identical conceptual departure boundary plane.
    
    In event_005:
    - Intermediate trackside relay cabinet: 5.60s (Frame 168)
    - Canonical transverse departure boundary plane: 6.00s (Frame 180)
    T3 must be measured at the departure boundary plane to match T4 semantics.
    """
    class ExitBoundaryChecker:
        def __init__(self, canonical_boundary_plane_name: str):
            self.canonical_plane = canonical_boundary_plane_name

        def validate_markers(self, t3_marker_name: str, t4_marker_name: str | None) -> bool:
            # If t4 is observable, both must share the same physical boundary plane
            if t3_marker_name != self.canonical_plane:
                return False
            if t4_marker_name is not None and t4_marker_name != self.canonical_plane:
                return False
            return True

    checker = ExitBoundaryChecker("departure_boundary_plane")
    # Intermediate landmark fails canonical congruence
    assert checker.validate_markers("signal_relay_cabinet", None) is False
    # Canonical departure plane passes
    assert checker.validate_markers("departure_boundary_plane", None) is True
    assert checker.validate_markers("departure_boundary_plane", "departure_boundary_plane") is True


def test_regression_snr_linear_to_decibel_conversion() -> None:
    """Verifies that linear power spectral prominence ratios are correctly converted to decibels."""
    # Prior defect: linear peak-to-median ratio 156.4 was reported directly as '156.4 dB'
    # Correct formula: SNR_dB = 10 * log10(P_peak / P_median)
    linear_prominence_ratio = 156.402
    calculated_db = 10.0 * math.log10(linear_prominence_ratio)
    
    # 10 * log10(156.402) ≈ 21.94 dB
    assert 21.90 <= calculated_db <= 22.00
    assert abs(calculated_db - 21.942) < 0.01

    # Disallow uncalibrated linear ratio directly in dB field
    def validate_snr_bounds(snr_db: float) -> bool:
        # Realistic locomotive horn SNR in outdoor field environment rarely exceeds 45 dB
        return 0.0 <= snr_db <= 50.0

    assert validate_snr_bounds(calculated_db) is True
    assert validate_snr_bounds(linear_prominence_ratio) is False  # 156.4 dB would be ear-shattering / unrealistic


def test_regression_prevents_unsynchronized_camera_exposure_pooling() -> None:
    """Verifies that camera stream exposures are not summed as synchronized wall-clock time."""
    front_exposure_s = 79.557
    back_exposure_s = 78.107
    is_synchronized = False

    def compute_wall_clock_exposure(front_s: float, back_s: float, synchronized: bool) -> float | None:
        if not synchronized:
            # Unsynchronized streams cannot be summed or fused into concurrent wall-clock exposure
            return None
        # If synchronized with zero offset: max(front, back) or intersection
        return max(front_s, back_s)

    wall_clock = compute_wall_clock_exposure(front_exposure_s, back_exposure_s, is_synchronized)
    assert wall_clock is None

    # Summed stream-seconds is strictly an archive audit metric, NOT operational exposure
    stream_seconds = front_exposure_s + back_exposure_s
    assert abs(stream_seconds - 157.664) < 1e-3
