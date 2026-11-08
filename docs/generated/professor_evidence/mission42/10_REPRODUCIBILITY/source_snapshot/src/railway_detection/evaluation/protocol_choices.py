"""The scientific definitions the Phase 12 evaluator applies, with provenance.

Four definitions were listed as open by the Phase 12/13 audit. Searching the
repository's authoritative protocols shows that most already have a documented
answer, which this module records (with the source) instead of re-asking the
researcher:

====================================  ============================================
premature-opening window              **UNRESOLVED -- no default.** Protocol v9 /
                                      ground-truth protocol define an opening
                                      commanded while T1 <= t < T4 (what the code
                                      computes). The later design document (M4)
                                      proposes "first blocked tick < t < T4" and is
                                      explicitly pending ``[D-10]``. No
                                      researcher-attributed record accepts either;
                                      the "v9 is superseded" statement is an agent
                                      audit note. See
                                      docs/PREMATURE_OPENING_DECISION_EVIDENCE.md.
continuous-metric weighting           Event-weighted: the event is the unit of
                                      analysis (design section 9; protocol v9
                                      event-level denominators). Stream seconds
                                      appear only as nuisance exposure denominators.
censoring treatment                   Protocol v9 s5.3 / GT protocol s2.3, s4:
                                      censored or unobservable boundaries make the
                                      dependent metric ``not_evaluable`` and the
                                      event is excluded from that denominator,
                                      listed with its reason; never 0.0 or NaN.
false-alarm measure                   Protocol v9 s11.2: raw event counts, plus
                                      blocked seconds, closure episodes and
                                      per-stream exposure seconds. No hourly rate.
====================================  ============================================

The module therefore exposes the *documented profile*, hashes it so an EVAL-AUTH
record can bind to exactly what will be computed, and lets the researcher record
an explicit override (``phase12-protocol-decision/1``) **only** for a definition
the evaluator actually implements. An override naming an unimplemented
definition is refused rather than silently computed some other way.

What remains for the researcher is the premature-opening window: the profile has
no default for it, so an official run is refused until the researcher records one
(``choices.premature_opening_window``). Both ``t1_entry_to_t4_clearance`` (v9) and
``first_blocked_to_t4_clearance`` (M4) are implemented and selectable; neither is a default.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from typing import Any

PROTOCOL_CHOICE_OPTIONS: dict[str, dict[str, str]] = {
    "premature_opening_window": {
        "t1_entry_to_t4_clearance": "Opening commanded while T1 <= t < T4 (protocol v9).",
        "first_blocked_to_t4_clearance": (
            "Reopening after the barrier first blocked and before T4 "
            "(EXPERIMENT_DESIGN_FINAL.md M4, pending [D-10])."
        ),
        "t0_first_visible_to_t4_clearance": (
            "Reopening in [T0, T4). Documented nowhere; all 23 train events are "
            "left-censored at T0."
        ),
    },
    "continuous_metric_weighting": {
        "event_weighted": "Each evaluable event contributes equally.",
        "exposure_time_weighted": "Weight by recorded stream seconds. Documented nowhere.",
    },
    "censoring_treatment": {
        "exclude_censored_from_point_estimates": (
            "Censored/unobservable boundary => metric not evaluable; event excluded with reason."
        ),
        "report_censored_as_bounds": (
            "One-sided bounds with explicit counts (design sections 8.1/9)."
        ),
    },
    "false_alarm_measure": {
        "event_level_any_closure": "A no-train clip is a false alarm if it ever blocked.",
        "event_level_plus_stream_time_and_episodes": (
            "Event counts plus blocked seconds, closure episodes and exposure seconds; "
            "no hourly rate (protocol v9 s11.2, design N1)."
        ),
    },
}

# Options the evaluator computes today (metrics.py, simulation/runner.py).
IMPLEMENTED_OPTIONS: dict[str, frozenset[str]] = {
    "premature_opening_window": frozenset(
        {"t1_entry_to_t4_clearance", "first_blocked_to_t4_clearance"}
    ),
    "continuous_metric_weighting": frozenset({"event_weighted"}),
    "censoring_treatment": frozenset({"exclude_censored_from_point_estimates"}),
    # The event-level count is a subset of the extended report, so both are met.
    "false_alarm_measure": frozenset(
        {"event_level_any_closure", "event_level_plus_stream_time_and_episodes"}
    ),
}

# decision -> (documented value or None when unresolved, source, standing)
DOCUMENTED_PROFILE: dict[str, tuple[str | None, str, str]] = {
    "premature_opening_window": (
        None,
        "candidates: docs/FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md section 5.2 (T1<=t<T4) vs "
        "docs/EXPERIMENT_DESIGN_FINAL.md M4 (first blocked tick < t < T4)",
        "UNRESOLVED [D-10]: neither definition has a researcher-attributed acceptance",
    ),
    "continuous_metric_weighting": (
        "event_weighted",
        "docs/EXPERIMENT_DESIGN_FINAL.md section 9 (unit of analysis = event)",
        "documented",
    ),
    "censoring_treatment": (
        "exclude_censored_from_point_estimates",
        "docs/FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md section 5.3; "
        "docs/FINAL_GROUND_TRUTH_PROTOCOL.md sections 2.3 and 4",
        "documented",
    ),
    "false_alarm_measure": (
        "event_level_plus_stream_time_and_episodes",
        "docs/FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md section 11.2",
        "documented",
    ),
}

PROTOCOL_CHOICE_KEYS = tuple(sorted(PROTOCOL_CHOICE_OPTIONS))


class ProtocolChoiceError(ValueError):
    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


def validate_protocol_choices(choices: Mapping[str, Any]) -> None:
    """Validate an explicit researcher override (may be partial).

    Every named value must be a known option *and* implemented. Decisions the
    override omits keep their documented value.
    """
    extra = sorted(set(choices) - set(PROTOCOL_CHOICE_KEYS))
    if extra:
        raise ProtocolChoiceError("PROTOCOL_DECISION_INVALID", f"unknown decisions {extra}")
    if not choices:
        raise ProtocolChoiceError("PROTOCOL_DECISION_INVALID", "choices must not be empty")
    unsupported: dict[str, str] = {}
    for key, value in choices.items():
        if not isinstance(value, str) or value not in PROTOCOL_CHOICE_OPTIONS[key]:
            raise ProtocolChoiceError(
                "PROTOCOL_DECISION_INVALID",
                f"{key}={value!r} is not a known option {sorted(PROTOCOL_CHOICE_OPTIONS[key])}",
            )
        if value not in IMPLEMENTED_OPTIONS[key]:
            unsupported[key] = value
    if unsupported:
        raise ProtocolChoiceError(
            "PROTOCOL_CHOICE_NOT_IMPLEMENTED",
            f"the evaluator does not implement {unsupported}; implemented: "
            f"{ {k: sorted(v) for k, v in IMPLEMENTED_OPTIONS.items()} }",
        )


def unresolved_decisions(overrides: Mapping[str, Any] | None = None) -> list[str]:
    """Decisions with neither a documented value nor an explicit researcher choice."""
    given = overrides or {}
    return [
        key
        for key in PROTOCOL_CHOICE_KEYS
        if DOCUMENTED_PROFILE[key][0] is None and not isinstance(given.get(key), str)
    ]


def effective_profile(overrides: Mapping[str, Any] | None = None) -> dict[str, str]:
    """Documented values, replaced only by validated explicit researcher overrides.

    Raises ``ProtocolChoiceError`` if any decision is still unresolved: no value
    is ever invented to fill a gap.
    """
    if overrides:
        validate_protocol_choices(overrides)
    missing = unresolved_decisions(overrides)
    if missing:
        raise ProtocolChoiceError(
            "PREMATURE_OPENING_DEFINITION_UNDECIDED",
            f"no documented value or researcher choice for {missing}; see "
            "docs/PREMATURE_OPENING_DECISION_EVIDENCE.md",
        )
    profile = {
        key: str(DOCUMENTED_PROFILE[key][0]) for key in PROTOCOL_CHOICE_KEYS
        if DOCUMENTED_PROFILE[key][0] is not None
    }
    profile.update({key: str(value) for key, value in (overrides or {}).items()})
    return profile


def profile_sha256(profile: Mapping[str, str]) -> str:
    """Stable digest of the definitions an official run will apply."""
    body = ";".join(f"{key}={profile[key]}" for key in sorted(profile)).encode()
    return hashlib.sha256(b"phase12-protocol-profile/1;" + body).hexdigest()
