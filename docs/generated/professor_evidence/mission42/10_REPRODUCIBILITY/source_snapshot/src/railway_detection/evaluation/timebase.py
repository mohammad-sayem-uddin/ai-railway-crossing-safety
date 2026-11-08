"""Shared replay-timestamp grid for the evaluation modules (Mission 5B, DEC-C05).

Replay-step and ground-truth boundary timestamps are compared with strict inequalities.  IEEE-754
representation noise (``0.1 + 0.2 != 0.3``) must not flip those comparisons, so both sides of every
comparison are first snapped to a one-microsecond grid.  This is a representation fix, not a
physical timing tolerance: values that differ by at least one microsecond keep their order.
"""

from __future__ import annotations

#: Decimal digits kept by :func:`normalize_timestamp` (one microsecond).
TIMESTAMP_ROUND_DIGITS = 6


def normalize_timestamp(value: float) -> float:
    """Snap a timestamp (or a difference of timestamps) to the one-microsecond grid."""
    return round(float(value), TIMESTAMP_ROUND_DIGITS)
