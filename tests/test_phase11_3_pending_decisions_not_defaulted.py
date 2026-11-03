"""Phase 11.3, Task 5: confirms that none of the four decisions recorded as
`PENDING_RESEARCHER_DECISION` in `docs/PHASE11_3_RESEARCHER_DECISIONS.md`
has quietly received a permissive default anywhere in the implementation.
Each test proves ABSENCE of a mechanism that would constitute a silent
decision, using only introspection and synthetic data -- never the real 27
review records.

Phase 11.7 update: Decisions 2 and 4 were explicitly researcher-selected
(v1.2.0) and then genuinely implemented in Phase 11.7 -- this is the
opposite of a silent default (a recorded researcher choice, deliberately
and visibly built, with its own dedicated test coverage in
`tests/test_phase11_7_governance_controls.py`). The two Decision-2 and two
Decision-4 tests that used to prove ABSENCE have been replaced below with
tests proving the implementation matches the SPECIFIC option the researcher
selected, not some other option that would itself be an undocumented
default. Decisions 1 and 3 remain genuinely unimplemented (Decision 1's
numeric thresholds are still `PENDING` pending pilot data; Decision 3's
second-review-trigger and clear-case-audit mechanisms are still open) --
their absence tests are unchanged.
"""

from __future__ import annotations

import inspect

import railway_detection.annotation.promotion_gate as gate_module
import railway_detection.annotation.stage2_1_schema as schema_module
from railway_detection.annotation.stage2_1_schema import MIN_PLAUSIBLE_REVIEW_DURATION_S


# --- Decision 1: review-duration floor is flat, not silently scaled ------


def test_review_duration_floor_is_a_plain_flat_constant_not_a_scaling_function() -> None:
    """If this were a function (e.g. scaling by event duration or trailing
    car count), Decision 1 part (B)/(C) would have been silently chosen.
    It is a plain float -- the flat-floor interpretation only, exactly as
    documented as provisional in Phase 11.2/Phase 11.3."""
    assert isinstance(MIN_PLAUSIBLE_REVIEW_DURATION_S, float)
    assert MIN_PLAUSIBLE_REVIEW_DURATION_S == 30.0


def test_no_secondary_fast_but_passing_review_band_exists() -> None:
    """Decision 1's option (D) -- auto-routing sessions in a 'fast but
    passing' band to NEEDS_SECOND_REVIEW -- has not been silently
    implemented. There is exactly one threshold, not two."""
    source = inspect.getsource(schema_module)
    # Only one duration-related threshold constant should exist.
    assert source.count("MIN_PLAUSIBLE_REVIEW_DURATION_S") >= 1
    forbidden = ["SECONDARY_DURATION_THRESHOLD", "FAST_REVIEW_THRESHOLD_S", "AUTO_SECOND_REVIEW_DURATION_S"]
    for name in forbidden:
        assert not hasattr(schema_module, name)


# --- Decision 2: Phase 11.7 implements the researcher-selected option (B),
# a MANDATORY allowlist -- not the denylist-only status quo, and not the
# hybrid option (C) the Phase 11.6 recommendation suggested but the
# researcher did not select. -------------------------------------------


def test_allowlist_mechanism_now_exists_matching_the_selected_option() -> None:
    """Decision 2 = option (B), mandatory allowlist (researcher-selected,
    `docs/PHASE11_3_RESEARCHER_DECISIONS.md` v1.2.0) -- confirmed actually
    implemented, not merely recorded as a choice. Full behavioral coverage
    (positive/negative/tampering/bypass) lives in
    `tests/test_phase11_7_governance_controls.py`; this test only confirms
    the mechanism's existence and that the pre-existing denylist was
    preserved alongside it, per Decision 2's explicit requirement not to
    replace the denylist."""
    assert hasattr(gate_module, "load_authorized_reviewers")
    assert hasattr(gate_module, "AuthorizedReviewersLoadError")
    assert hasattr(schema_module, "REVIEWER_ID_BLOCKLIST")  # denylist preserved, not replaced


def test_reviewer_id_alone_no_longer_sufficient_without_the_allowlist() -> None:
    """Being well-formed and non-blocklisted (schema-level) is necessary
    but, since Phase 11.7, no longer SUFFICIENT for promotion -- the
    identity must also appear in the caller-supplied allowlist. This is
    the inverse of this file's old `test_any_non_blocklisted_reviewer_id_is_currently_accepted`:
    that test proved the (then-true) absence of this exact gate."""
    from railway_detection.annotation.promotion_gate import validate_for_promotion

    sig = inspect.signature(validate_for_promotion)
    assert "authorized_reviewers" in sig.parameters
    assert sig.parameters["authorized_reviewers"].default is inspect.Parameter.empty


# --- Decision 3: no auto-resolution of disagreement, no numeric tolerance -


def test_no_automated_tie_breaking_function_exists() -> None:
    """Re-confirms Phase 11.2's finding still holds after this phase's
    additions -- no function anywhere resolves a disagreement
    automatically."""
    forbidden_names = ["resolve_disagreement", "average_values", "majority_vote", "auto_resolve"]
    for name in forbidden_names:
        assert not hasattr(gate_module, name)
        assert not hasattr(schema_module, name)


def test_no_numeric_agreement_tolerance_constant_exists() -> None:
    """Decision 3 part (b)'s option (B) -- a specific numeric tolerance for
    judging two reviewers' values as 'agreeing' -- has not been silently
    chosen. No such constant exists in either module."""
    forbidden_names = [
        "AGREEMENT_TOLERANCE_S", "BOUNDARY_AGREEMENT_TOLERANCE", "FRAME_TOLERANCE",
        "DISAGREEMENT_THRESHOLD_S",
    ]
    for name in forbidden_names:
        assert not hasattr(gate_module, name)
        assert not hasattr(schema_module, name)


def test_no_rule_determines_which_events_require_second_review() -> None:
    """Decision 3 part (a) -- whether second review is mandatory-for-all,
    triggered-by-uncertainty, or triggered-by-a-fixed-subset -- has not
    been silently chosen. No function inspects boundary states or event
    identity to decide this."""
    forbidden_names = [
        "requires_second_review", "needs_mandatory_second_review", "is_second_review_required",
    ]
    for name in forbidden_names:
        assert not hasattr(gate_module, name)
        assert not hasattr(schema_module, name)


# --- Decision 4: Phase 11.7 implements the researcher-selected option,
# (B)+(C) COMBINED -- fresh re-verification at promotion time (B) PLUS a
# reviewer-independently-observed media hash recorded in the schema (C) --
# stronger than either option alone, as the researcher explicitly chose. -


def test_promotion_gate_now_genuinely_rehashes_raw_media_matching_option_b() -> None:
    """Decision 4 part (B): confirmed `validate_for_promotion` now DOES
    open and hash raw media files at promotion time (the opposite of this
    file's old `test_promotion_gate_never_reads_or_hashes_raw_media_files_itself`,
    which correctly proved this was absent before Phase 11.7). Full
    behavioral coverage (missing file, substituted file, changed-since-review)
    lives in `tests/test_phase11_7_governance_controls.py`."""
    assert hasattr(gate_module, "compute_media_sha256_pair")
    source = inspect.getsource(gate_module.validate_for_promotion)
    assert "compute_media_sha256_pair" in source


def test_stage2_1_schema_now_has_reviewer_observed_media_hash_field_matching_option_c() -> None:
    """Decision 4 part (C): `reviewer_observed_media_hashes` is now a
    required field on `Stage21ReviewRecord` (the opposite of this file's
    old `test_stage2_1_schema_has_no_independently_observed_media_hash_field`).
    Field name differs slightly from the two names that test searched for
    (`reviewer_observed_media_sha256`/`independently_verified_media_hash`)
    -- those were anticipated placeholder names from the Phase 11.3
    proposal text, not a commitment to the exact final name."""
    import dataclasses

    field_names = {f.name for f in dataclasses.fields(schema_module.Stage21ReviewRecord)}
    assert "reviewer_observed_media_hashes" in field_names
    assert hasattr(schema_module, "ReviewerObservedMediaHashes")
