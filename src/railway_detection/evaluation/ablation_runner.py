"""Phase 13 experiment planning and execution boundary.

The descriptive contract validator remains here. Reusable synthetic execution
is implemented by :mod:`experiment_engine`; official empirical execution is
still refused because the repository has no verifiable authorization artifact
or complete Phase 12 prerequisites.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from railway_detection.experiments.frozen_config import (
    compute_canonical_config_hash,
    load_frozen_config,
)
from railway_detection.research_contracts import (
    AblationConditionContract,
    ResearchContractError,
    missing_phase13_prerequisites,
    validate_ablation_condition_contracts,
)


class Phase13ExecutionBlocked(RuntimeError):
    """Raised for every attempt to execute a Phase 13 empirical condition."""


@dataclass(frozen=True)
class Phase13Prerequisites:
    """Self-reported readiness metadata; never treated as authorization proof."""

    phase12_baseline_complete: bool = False
    approved_ground_truth_available: bool = False
    frozen_config_hash_verified: bool = False
    researcher_scope_authorized: bool = False

    def blockers(self) -> tuple[str, ...]:
        return missing_phase13_prerequisites(
            phase12_baseline_complete=self.phase12_baseline_complete,
            approved_ground_truth_available=self.approved_ground_truth_available,
            frozen_config_hash_verified=self.frozen_config_hash_verified,
            researcher_scope_authorized=self.researcher_scope_authorized,
        )


@dataclass(frozen=True)
class Phase13Plan:
    """Validated descriptive plan; contains no results or replay outputs."""

    frozen_config_sha256: str
    conditions: tuple[AblationConditionContract, ...]
    execution_status: str = "BLOCKED_NOT_AUTHORIZED"
    baseline_condition_id: str = "baseline"
    repeat_seeds: tuple[int, ...] = (42,)

    def to_dict(self) -> dict[str, Any]:
        return {
            "phase": "13",
            "execution_status": self.execution_status,
            "frozen_config_sha256": self.frozen_config_sha256,
            "baseline_condition_id": self.baseline_condition_id,
            "repeat_seeds": list(self.repeat_seeds),
            "conditions": [
                {
                    "condition_id": item.condition_id,
                    "condition_type": item.condition_type,
                    "changed_factors": list(item.changed_factors),
                    "is_baseline": item.is_baseline,
                }
                for item in self.conditions
            ],
            "results": None,
            "disclaimer": (
                "Plan validation is not researcher authorization and produces "
                "no experimental findings."
            ),
        }


class Phase13AblationRunner:
    """Validates plans and refuses empirical execution until explicitly enabled."""

    def __init__(self, config_path: Path | str) -> None:
        self.config_path = Path(config_path)

    def prepare_plan(
        self,
        conditions: Sequence[AblationConditionContract],
        *,
        repeat_seeds: Sequence[int] = (42,),
    ) -> Phase13Plan:
        """Validate condition descriptions and current frozen-config identity."""
        config = load_frozen_config(self.config_path)
        recomputed_hash = compute_canonical_config_hash(config.raw_dict)
        if recomputed_hash != config.config_hash:
            raise ResearchContractError(
                "frozen config hash changed during plan validation"
            )
        if any(condition.uses_audio_v2 for condition in conditions):
            raise ResearchContractError("Audio V2 is prohibited in Phase 13 conditions")
        validate_ablation_condition_contracts(
            conditions, frozen_config_sha256=recomputed_hash
        )
        if not repeat_seeds or any(
            not isinstance(seed, int) or isinstance(seed, bool) for seed in repeat_seeds
        ):
            raise ResearchContractError("repeat_seeds must be nonempty integer seeds")
        if len(set(repeat_seeds)) != len(repeat_seeds):
            raise ResearchContractError("repeat_seeds must be unique")
        baseline = next(condition for condition in conditions if condition.is_baseline)
        return Phase13Plan(
            frozen_config_sha256=recomputed_hash,
            conditions=tuple(conditions),
            baseline_condition_id=baseline.condition_id,
            repeat_seeds=tuple(repeat_seeds),
        )

    def run(
        self,
        *,
        plan: Phase13Plan,
        prerequisites: Phase13Prerequisites,
    ) -> None:
        """Refuse this legacy empirical entry point regardless of boolean claims.

        Synthetic integrations must use ``Phase13ExperimentEngine`` directly.
        This method has no provider interface and cannot run empirical data.
        """
        del plan
        blockers = prerequisites.blockers()
        reason = ", ".join(blockers) if blockers else "verified researcher authorization is absent"
        raise Phase13ExecutionBlocked(
            "Phase 13 execution is disabled: "
            f"{reason}. Use the explicitly synthetic internal engine for tests; "
            "no empirical replay or official results were produced."
        )