"""Evaluation and reporting for the railway detection research program.

Phase 12 modules:

- ``ground_truth_loader``: fail-closed loader for approved Stage-2.1 records.
- ``metrics``: event-level and cohort safety metrics with Wilson CIs.
- ``evaluation_runner``: synthetic-capable Phase 12 computation engine.
- ``execution_gate``: evidence-derived official execution blockers.
- ``experiment_engine``: synthetic-only Phase 13 condition runner.
- ``ablation_runner``: Phase 13 plan validator and empirical execution refusal.
- ``perturbation``: replay-input transforms; no ground-truth mutation.
- ``cache_only_engine``: fail-closed cache-only replay engine consuming
  hash-bound JSONL detection caches; zero raw-media access.
"""

from railway_detection.evaluation.ablation_runner import (
    Phase13AblationRunner,
    Phase13ExecutionBlocked,
    Phase13Plan,
    Phase13Prerequisites,
)
from railway_detection.evaluation.cache_only_engine import (
    CacheIntegrityError,
    CacheOnlyReplayEngine,
    CacheReplayRefusal,
    MediaAccessViolationError,
    ReplayOutput,
    ReplayRefusalRecord,
)
from railway_detection.evaluation.cache_phase12_adapter import (
    CachePhase12Adaptation,
    CachePhase12AdapterError,
    adapt_batch,
    to_event_replay,
    to_official_evidence_payload,
)
from railway_detection.evaluation.descriptive_only import (
    DESCRIPTIVE_ONLY_MODE,
    DESCRIPTIVE_ONLY_SCHEMA,
    DescriptiveOnlyInput,
    DescriptiveOnlyRefusal,
    DescriptiveOnlyReport,
    aggregate_descriptive_only,
)
from railway_detection.evaluation.evaluation_runner import (
    EvaluationRefused,
    Phase12EvaluationResult,
    Phase12EvaluationRunner,
    serialize_tick_log,
)
from railway_detection.evaluation.execution_gate import (
    ExecutionBlocker,
    OfficialExecutionReadiness,
    assess_official_phase12_readiness,
)
from railway_detection.evaluation.experiment_engine import (
    ExperimentCondition,
    ExperimentDataProvider,
    ExperimentInferenceProvider,
    ExperimentPlan,
    ExperimentPlanError,
    ExperimentRunResult,
    Phase13ExperimentEngine,
)
from railway_detection.evaluation.ground_truth_loader import (
    ApprovedEventGroundTruth,
    BoundaryNotComputable,
    CandidateProposalRefused,
    GroundTruthLoadError,
    LegacyRecordRefused,
    NotApprovedRefused,
    load_approved_ground_truth,
    load_approved_ground_truth_from_dir,
)
from railway_detection.evaluation.input_contracts import (
    EvaluationEventInput,
    EvaluationInputError,
    EvaluationInputSet,
    EvidenceClassification,
    load_evaluation_input_manifest,
    sha256_file,
)
from railway_detection.evaluation.metrics import (
    CohortEvaluationSummary,
    EventMetricsCalculator,
    SingleEventEvaluation,
    wilson_score_interval,
)
from railway_detection.evaluation.output_contracts import (
    EvaluationFailureReport,
    EvaluationProvenance,
    EvaluationRunOutput,
    canonical_json_bytes,
)
from railway_detection.evaluation.perturbation import (
    PerturbationRefused,
    PerturbationSpec,
    apply_confidence_noise,
    apply_sensor_dropout,
    apply_timing_jitter,
    refuse_ground_truth_perturbation,
)

__all__ = [
    "ApprovedEventGroundTruth",
    "BoundaryNotComputable",
    "CacheIntegrityError",
    "CacheOnlyReplayEngine",
    "CacheReplayRefusal",
    "CachePhase12Adaptation",
    "CachePhase12AdapterError",
    "DESCRIPTIVE_ONLY_MODE",
    "DESCRIPTIVE_ONLY_SCHEMA",
    "DescriptiveOnlyInput",
    "DescriptiveOnlyRefusal",
    "DescriptiveOnlyReport",
    "CandidateProposalRefused",
    "CohortEvaluationSummary",
    "EvaluationRefused",
    "EvaluationEventInput",
    "EvaluationFailureReport",
    "EvaluationInputError",
    "EvaluationInputSet",
    "EvaluationProvenance",
    "EvaluationRunOutput",
    "EvidenceClassification",
    "ExecutionBlocker",
    "ExperimentCondition",
    "ExperimentDataProvider",
    "ExperimentInferenceProvider",
    "ExperimentPlan",
    "ExperimentPlanError",
    "ExperimentRunResult",
    "EventMetricsCalculator",
    "GroundTruthLoadError",
    "LegacyRecordRefused",
    "MediaAccessViolationError",
    "NotApprovedRefused",
    "PerturbationRefused",
    "PerturbationSpec",
    "Phase13AblationRunner",
    "Phase13ExecutionBlocked",
    "Phase13Plan",
    "Phase13Prerequisites",
    "Phase12EvaluationResult",
    "Phase12EvaluationRunner",
    "Phase13ExperimentEngine",
    "OfficialExecutionReadiness",
    "ReplayOutput",
    "ReplayRefusalRecord",
    "SingleEventEvaluation",
    "load_approved_ground_truth",
    "load_approved_ground_truth_from_dir",
    "load_evaluation_input_manifest",
    "sha256_file",
    "assess_official_phase12_readiness",
    "adapt_batch",
    "aggregate_descriptive_only",
    "canonical_json_bytes",
    "apply_confidence_noise",
    "apply_sensor_dropout",
    "apply_timing_jitter",
    "refuse_ground_truth_perturbation",
    "to_event_replay",
    "to_official_evidence_payload",
    "serialize_tick_log",
    "wilson_score_interval",
]
