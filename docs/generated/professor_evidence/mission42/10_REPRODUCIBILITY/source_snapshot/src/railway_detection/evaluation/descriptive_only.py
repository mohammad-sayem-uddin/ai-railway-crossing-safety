"""Isolated synthetic-only descriptive aggregation.

This module is intentionally separate from the official Phase 12 input manifest,
split validator, manifest builder, execution gate, and evaluation runner.  It
implements only the unambiguous software portion of the proposed
``full_cohort_descriptive`` concept: aggregate already-computed typed event
evaluations and retain explicit population/limitation metadata.

It cannot consume raw media, create official evidence, or turn synthetic output
into an official result.  A future researcher-approved descriptive contract may
reuse the shape, but this proposed schema is not an authoritative input format.
"""

from __future__ import annotations

import copy
import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from railway_detection.evaluation.input_contracts import EvidenceClassification
from railway_detection.evaluation.metrics import (
    CohortEvaluationSummary,
    EventMetricsCalculator,
    SingleEventEvaluation,
)
from railway_detection.experiments.cache_provenance import (
    CACHE_REUSE_ISOLATED_RUN,
    CacheProvenanceError,
    ControlledCacheProvenance,
    validate_controlled_cache_provenance,
)

DESCRIPTIVE_ONLY_SCHEMA = "PROPOSED-descriptive-only-synthetic/1"
DESCRIPTIVE_ONLY_MODE = "full_cohort_descriptive"


class DescriptiveOnlyRefusal(ValueError):
    """A proposed descriptive-only input cannot be safely aggregated."""

    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


@dataclass(frozen=True)
class DescriptiveOnlyInput:
    """Proposed synthetic input wrapper; not an official Phase 12 manifest."""

    event_evaluations: tuple[SingleEventEvaluation, ...]
    population_label: str
    provenance: Mapping[str, Any]
    limitations: tuple[str, ...]
    permitted_claims: tuple[str, ...]
    evidence_classification: EvidenceClassification = EvidenceClassification.SYNTHETIC
    mode_id: str = DESCRIPTIVE_ONLY_MODE
    schema_version: str = DESCRIPTIVE_ONLY_SCHEMA


@dataclass(frozen=True)
class DescriptiveOnlyReport:
    """Deterministic, explicitly non-official descriptive summary."""

    schema_version: str
    mode_id: str
    evidence_classification: EvidenceClassification
    official_evaluation_eligible: bool
    population_label: str
    event_ids: tuple[str, ...]
    summary: CohortEvaluationSummary
    excluded_event_count: int
    excluded_event_ids: tuple[str, ...]
    limitations: tuple[str, ...]
    permitted_claims: tuple[str, ...]
    provenance: dict[str, Any]
    engine_case_study_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize without mutating source objects or implying official status."""
        return {
            "schema_version": self.schema_version,
            "mode_id": self.mode_id,
            "evidence_classification": self.evidence_classification.value,
            "official_evaluation_eligible": self.official_evaluation_eligible,
            "population_label": self.population_label,
            "event_ids": list(self.event_ids),
            "summary": self.summary.to_dict(),
            "excluded_event_count": self.excluded_event_count,
            "excluded_event_ids": list(self.excluded_event_ids),
            "engine_case_study_ids": list(self.engine_case_study_ids),
            "limitations": list(self.limitations),
            "permitted_claims": list(self.permitted_claims),
            "provenance": copy.deepcopy(self.provenance),
        }


_FORBIDDEN_CLAIM_PATTERNS = (
    "cross-site",
    "cross_site",
    "generalization",
    "official test",
    "official evaluation",
    "held-out test",
    "held_out_test",
)


def _is_forbidden_claim(claim: str) -> bool:
    lower = claim.strip().lower()
    if any(neg in lower for neg in ("no ", "not ", "non-", "never ", "without ")):
        return False
    return any(pat in lower for pat in _FORBIDDEN_CLAIM_PATTERNS)


def _validate_input(value: DescriptiveOnlyInput) -> None:
    if not isinstance(value, DescriptiveOnlyInput):
        raise DescriptiveOnlyRefusal(
            "SOURCE_TYPE_INVALID",
            f"expected DescriptiveOnlyInput, got {type(value).__name__}",
        )
    if value.schema_version != DESCRIPTIVE_ONLY_SCHEMA:
        raise DescriptiveOnlyRefusal(
            "SCHEMA_UNSUPPORTED", f"unsupported proposed schema {value.schema_version!r}"
        )
    if value.mode_id != DESCRIPTIVE_ONLY_MODE:
        raise DescriptiveOnlyRefusal(
            "MODE_UNSUPPORTED", f"unsupported descriptive mode {value.mode_id!r}"
        )
    if value.evidence_classification is not EvidenceClassification.SYNTHETIC:
        raise DescriptiveOnlyRefusal(
            "OFFICIAL_CONVERSION_REFUSED",
            "this isolated component accepts synthetic inputs only; it cannot create "
            "official results",
        )
    if not isinstance(value.population_label, str) or not value.population_label.strip():
        raise DescriptiveOnlyRefusal(
            "POPULATION_INVALID", "population_label must be non-empty"
        )
    if not isinstance(value.provenance, Mapping) or not value.provenance:
        raise DescriptiveOnlyRefusal(
            "PROVENANCE_MISSING", "descriptive provenance must be a non-empty mapping"
        )
    if not isinstance(value.limitations, tuple) or not value.limitations:
        raise DescriptiveOnlyRefusal(
            "LIMITATIONS_MISSING", "descriptive output must state at least one limitation"
        )
    if not isinstance(value.permitted_claims, tuple) or not value.permitted_claims:
        raise DescriptiveOnlyRefusal(
            "CLAIMS_MISSING", "descriptive output must state permitted claims"
        )
    for claim in value.permitted_claims:
        if not isinstance(claim, str) or not claim.strip():
            raise DescriptiveOnlyRefusal(
                "CLAIMS_MISSING", "permitted_claims entries must be non-empty strings"
            )
        if _is_forbidden_claim(claim):
            raise DescriptiveOnlyRefusal(
                "FORBIDDEN_CLAIM_SCOPE",
                f"Descriptive-only mode permits fixed-site descriptive claims only; "
                f"forbidden generalization/official claim: {claim!r}",
            )
    if value.provenance.get("source_category") == "historical_diagnostic" or (
        value.provenance.get("cache_classification") == "historical_diagnostic"
    ):
        if (
            value.provenance.get("claimed_category")
            in ("controlled_experimental", "official_evaluation")
            or value.provenance.get("controlled_run_verified") is True
        ):
            raise DescriptiveOnlyRefusal(
                "HISTORICAL_AS_CONTROLLED_REFUSED",
                "Historical diagnostic outputs cannot be presented as provenance-verified "
                "controlled experimental or official outputs.",
            )
    raw_cache_prov = value.provenance.get(
        "cache_provenance", value.provenance.get("controlled_cache_provenance")
    )
    claims_controlled = (
        value.provenance.get("cache_classification") == "controlled_experimental"
        or value.provenance.get("claimed_category") == "controlled_experimental"
        or value.provenance.get("controlled_run_verified") is True
    )
    if claims_controlled and raw_cache_prov is None:
        raise DescriptiveOnlyRefusal(
            "CONTROLLED_PROVENANCE_REQUIRED",
            "Provenance claiming controlled_experimental or controlled_run_verified=True "
            "must include a valid cache_provenance / controlled_cache_provenance record.",
        )
    if raw_cache_prov is not None:
        try:
            if isinstance(raw_cache_prov, ControlledCacheProvenance):
                raw_cache_prov.validate()
                parsed_prov = raw_cache_prov
            elif isinstance(raw_cache_prov, Mapping):
                parsed_prov = ControlledCacheProvenance.from_dict(raw_cache_prov)
            else:
                raise CacheProvenanceError(
                    "PROVENANCE_INVALID_TYPE",
                    f"cache_provenance must be Mapping or ControlledCacheProvenance, got {type(raw_cache_prov).__name__}",
                )
            expected_prov = value.provenance.get("expected_cache_provenance")
            if expected_prov is not None:
                expected_obj = (
                    expected_prov
                    if isinstance(expected_prov, ControlledCacheProvenance)
                    else ControlledCacheProvenance.from_dict(expected_prov)
                )
                reuse_policy = str(
                    value.provenance.get("cache_reuse_policy", CACHE_REUSE_ISOLATED_RUN)
                )
                validate_controlled_cache_provenance(
                    parsed_prov.to_dict(),
                    expected_obj,
                    reuse_policy=reuse_policy,
                )
        except CacheProvenanceError as exc:
            raise DescriptiveOnlyRefusal("CACHE_PROVENANCE_INVALID", str(exc)) from exc
    if not isinstance(value.event_evaluations, tuple) or not value.event_evaluations:
        raise DescriptiveOnlyRefusal(
            "EVENTS_MISSING", "at least one typed event evaluation is required"
        )

    event_ids: list[str] = []
    for evaluation in value.event_evaluations:
        if not isinstance(evaluation, SingleEventEvaluation):
            raise DescriptiveOnlyRefusal(
                "EVENT_TYPE_INVALID",
                f"expected SingleEventEvaluation, got {type(evaluation).__name__}",
            )
        if not isinstance(evaluation.event_id, str) or not evaluation.event_id.strip():
            raise DescriptiveOnlyRefusal("EVENT_ID_INVALID", "event_id must be non-empty")
        if str(evaluation.event_id).startswith("engine_events/") and (
            evaluation.has_train_ground_truth
            or (evaluation.evaluable and evaluation.notes != "engine_event_excluded")
        ):
            raise DescriptiveOnlyRefusal(
                "ENGINE_EVENT_POOLING_REFUSED",
                f"{evaluation.event_id}: engine_events must remain isolated from train-event "
                "and negative-control denominators (has_train_ground_truth=False, "
                "evaluable=False, notes='engine_event_excluded')",
            )
        event_ids.append(evaluation.event_id)
        for name in ("total_closed_s", "blocked_seconds", "exposure_s"):
            number = getattr(evaluation, name)
            if number is not None and (
                isinstance(number, bool)
                or not isinstance(number, (int, float))
                or not math.isfinite(number)
                or number < 0
            ):
                raise DescriptiveOnlyRefusal(
                    "NUMERIC_FIELD_INVALID", f"{evaluation.event_id}: {name} is invalid"
                )
    if len(event_ids) != len(set(event_ids)):
        raise DescriptiveOnlyRefusal("DUPLICATE_EVENT_ID", "event IDs must be unique")


def aggregate_descriptive_only(value: DescriptiveOnlyInput) -> DescriptiveOnlyReport:
    """Aggregate synthetic typed event evaluations without official-path access."""
    _validate_input(value)
    evaluations = tuple(value.event_evaluations)
    summary = EventMetricsCalculator.aggregate_cohort(list(evaluations))
    engine_ids = tuple(
        evaluation.event_id
        for evaluation in evaluations
        if evaluation.notes == "engine_event_excluded"
        or str(evaluation.event_id).startswith("engine_events/")
    )
    excluded = tuple(
        evaluation.event_id
        for evaluation in evaluations
        if not evaluation.evaluable and evaluation.event_id not in engine_ids
    )
    return DescriptiveOnlyReport(
        schema_version=value.schema_version,
        mode_id=value.mode_id,
        evidence_classification=value.evidence_classification,
        official_evaluation_eligible=False,
        population_label=value.population_label,
        event_ids=tuple(evaluation.event_id for evaluation in evaluations),
        summary=summary,
        excluded_event_count=len(excluded),
        excluded_event_ids=excluded,
        limitations=tuple(value.limitations),
        permitted_claims=tuple(value.permitted_claims),
        provenance=copy.deepcopy(dict(value.provenance)),
        engine_case_study_ids=engine_ids,
    )


__all__ = [
    "DESCRIPTIVE_ONLY_MODE",
    "DESCRIPTIVE_ONLY_SCHEMA",
    "DescriptiveOnlyInput",
    "DescriptiveOnlyRefusal",
    "DescriptiveOnlyReport",
    "aggregate_descriptive_only",
]