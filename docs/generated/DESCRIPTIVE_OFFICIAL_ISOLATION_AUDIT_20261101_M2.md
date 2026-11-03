# DESCRIPTIVE vs. OFFICIAL EVALUATION ISOLATION AUDIT — MISSION 2 (2026-11-01)

- **Document ID**: `DESCRIPTIVE_OFFICIAL_ISOLATION_AUDIT_20261101_M2`
- **Mission**: `MISSION 2 — PIPELINE INTEGRITY VERIFICATION, SAFE REMEDIATION & STAGE-2.1 READINESS`

---

## 1. Approved Researcher Contract (D3, 2026-10-30)

- **D3 = descriptive-only evaluation**:
  - A separate descriptive-only evaluation mode is approved.
  - It must remain isolated from the official evaluation workflow.
  - It must not create an artificial train/validation/test split or be described as official test-set performance.
  - Claims must remain fixed-site descriptive claims. No cross-site generalization claims.

---

## 2. Structural and Runtime Isolation Verification

| Isolation Boundary | Descriptive-Only Pathway (`src/railway_detection/evaluation/descriptive_only.py`) | Official Phase 12 Pathway (`evaluation_runner.py`, `execution_gate.py`, `input_contracts.py`, `replay_producer.py`) | Verification Result |
| :--- | :--- | :--- | :--- |
| **Schema Version** | `"PROPOSED-descriptive-only-synthetic/1"` (`DESCRIPTIVE_ONLY_SCHEMA`) | `"phase12-evaluation-inputs/1"` (`INPUT_MANIFEST_SCHEMA`) and `"phase12-run-manifest/1"` | **Mutually Rejected**: `load_evaluation_input_manifest` raises `EvaluationInputError("MANIFEST_SCHEMA_UNSUPPORTED")` on descriptive-only JSON; `aggregate_descriptive_only` raises `DescriptiveOnlyRefusal("SCHEMA_UNSUPPORTED")` on official schemas. |
| **Mode Identifier** | `"full_cohort_descriptive"` (`DESCRIPTIVE_ONLY_MODE`) | Official held-out test split execution (`AUTHORIZED_OPERATION = "phase12_official_evaluation"`) | **Mutually Rejected**: `aggregate_descriptive_only` raises `MODE_UNSUPPORTED` on any mode other than `full_cohort_descriptive`. |
| **Evidence Classification** | Accepts `EvidenceClassification.SYNTHETIC` only; refuses `EvidenceClassification.REAL` with `OFFICIAL_CONVERSION_REFUSED`. | `Phase12EvaluationRunner.run_official` requires `EvidenceClassification.REAL` bound to a live `_OfficialPermit` and `EVAL-AUTH`. | **Mutually Rejected**: Descriptive-only cannot accept `REAL` evidence or produce a permit; official runner refuses unpermitted execution. |
| **Official Eligibility Flag** | `DescriptiveOnlyReport.official_evaluation_eligible` is hardcoded to `False`. | Requires `ready=True` from `assess_official_phase12_readiness` (Stage-2.1 receipt + split + R04 + protocol + manifest + `EVAL-AUTH`). | **Isolated**: No code path converts a `DescriptiveOnlyReport` into an official Phase 12 input or result. |
| **Train / Val / Test Split** | Does **not** import or call `validate_event_level_split`; operates over the caller-supplied fixed-site cohort without fabricating a split. | Requires `data/splits/phase12_event_split_decision.json` and replays **only** `partitions["test"]`. | **Isolated**: Descriptive-only never creates an artificial split. |
| **Claim Scope Enforcement** | `_validate_input` inspects `permitted_claims` and raises `DescriptiveOnlyRefusal("FORBIDDEN_CLAIM_SCOPE")` if any entry claims cross-site generalization, official test-set performance, or held-out test validation. | Bound to recorded governance decisions and protocol profile. | **Enforced**: Fixed-site descriptive limitation is structurally checked. |
| **Engine Event (`engine_events/event_001`)** | Rejects pooling of `engine_events/...` (`ENGINE_EVENT_POOLING_REFUSED`); records `engine_case_study_ids` separately while keeping `summary.eligible_events` and `summary.no_train_events` unpolluted. | Marks `engine_events` with `evaluable=False, notes="engine_event_excluded"` and counts in `cohort_summary.engine_events`. | **Consistent & Isolated**: `engine_events/event_001` is never pooled into train or negative-control denominators in either mode. |
| **Historical Diagnostic vs. Controlled Separation** | Refuses inputs where `source_category == "historical_diagnostic"` (or `cache_classification == "historical_diagnostic"`) is claimed as `"controlled_experimental"` or `"official_evaluation"` (`HISTORICAL_AS_CONTROLLED_REFUSED`). | Requires `phase12-replay-evidence/1` with verified `frozen_config_canonical_sha256`, `checkpoint_sha256`, and `media_sha256` matching Stage-2.1 review records. | **Enforced**: Historical diagnostic outputs cannot masquerade as controlled experimental or official evaluation outputs. |
| **Raw Media Access** | Zero imports or calls to `cv2`, `subprocess`, `frame_generator`, or `extract_audio_from_video`. | Zero raw media decoding in `Phase12EvaluationRunner` or `execution_gate.py`. | **Verified**: Synthetic-safe and media-isolated. |
