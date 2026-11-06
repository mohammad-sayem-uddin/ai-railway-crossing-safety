# Mission 29 historical results audit

Status: permitted documentary/code audit only. No raw media, checkpoint, cache, protected review corpus, inference, training or real-data replay/evaluation was accessed or performed. Values below are reported historical facts, not independently reproduced results. Original documents remain unchanged. The exact register includes source paths, lines, metadata digests, model/config/split provenance, definitions, risks, permission state and preparation scope.

## H29-VISION — YOLOv8n still-image development diagnostics

Reported values: `{"mAP50": "0.9946", "mAP50_95": "0.855", "reported_objects": 487, "reported_cropped_images": 3165}`.

Reported bounding-box average precision at IoU .50 and over .50:.95; not event detection, crossing protection, direction or safety rates.

Provenance/model: `{"model_name": "YOLOv8n", "checkpoint_reference": "experiments/vision/39f402dfe460/checkpoints/weights/best.pt", "configuration_declared_sha256": "3f5bb5b23f82f5d963d23dc8f3f1896a83532424d8e4ef70a406b6abfba18ebd", "checkpoint_identity_reverified": false}`.

Split/source provenance: `{"partition": "705d388743ea", "split": "development_fallback", "reported_leakage_risk": true, "reported_allow_ungrouped_fallback": true, "current_config_require_grouping": true, "current_config_allow_ungrouped_fallback": false, "current_config_does_not_repair_historical_split": true}`.

Evidence: `README.md:102`; `README.md:106`; `configs/frozen_experiment_v1.yaml:15`.

Risks: Documented ungrouped fallback and frame/scene leakage; historical split artifact not reopened; README single-class language versus front/rear/side configuration mapping is not resolved without exact asset evidence.

Limits: No new inference, checkpoint/cache access or raw-data evaluation; Historical report is not an independently reproduced result; Exact source/member/model rights and current physical identities remain unverified; No event-independent or cross-site generalization; 487 objects and 3,165 images are reported development counts, not 27 independent train events.

Preparation use: **HISTORICAL_LIMITATION_NOTE_ONLY**. Exact-source rights remain unresolved; no external publication/reproduction permission is established here.

## H29-AUDIO-README — Audio V3 rounded summary

Reported values: `{"F1": "0.869", "ROC_AUC": "0.961", "operating_threshold": "0.3700"}`.

README labels these validation metrics; detailed report labels comparable numbers test-window outcomes.

Provenance/model: `{"model_name": "CompactTrainHornCNN V3", "checkpoint_reference": "experiments/audio/RUN_20261008_AUDIO_V3_ESC50/checkpoints/best.pt", "configuration_declared_sha256": "ea1bb81d74230af71ba22b6d534a2ac550bca05833d1532e223376926c512782", "checkpoint_identity_reverified": false}`.

Split/source provenance: `{"reported_split_role": "VALIDATION_IN_README", "split_role_conflicted_with_detailed_report": true}`.

Evidence: `README.md:117`; `configs/frozen_experiment_v1.yaml:25`.

Risks: Validation/test labeling conflict; Checkpoint hash is configuration-declared only; no independent member/provenance verification.

Limits: No new inference, checkpoint/cache access or raw-data evaluation; Historical report is not an independently reproduced result; Exact source/member/model rights and current physical identities remain unverified; Rounded AUC .961 versus detailed .9613 is reported precision, not an independent replication; No event-level or gate-level performance claim.

Preparation use: **HISTORICAL_LIMITATION_NOTE_ONLY**. Exact-source rights remain unresolved; no external publication/reproduction permission is established here.

## H29-AUDIO-REPORT — Audio V3 detailed historical report

Reported values: `{"F1": "0.8690", "ROC_AUC": "0.9613", "operating_threshold": "0.3700", "reported_validation_F1": "0.9942", "recording_F1": "0.8667", "recording_ROC_AUC": "0.9408"}`.

Window F1/AUC and separately pooled recording F1/AUC; neither is a train-event safety metric.

Provenance/model: `{"model_name": "CompactTrainHornCNN V3", "configuration_reference": "configs/frozen_experiment_v1.yaml", "checkpoint_identity_reverified": false}`.

Split/source provenance: `{"reported_split_role": "TEST_WINDOWS", "reported_test_recordings": 26, "reported_test_windows": 182, "reported_negative_folds": {"train": [1, 2, 3], "validation": [4], "test": [5]}, "grouping_claim_independently_reverified": false}`.

Evidence: `docs/AUDIO_MODEL_V3_ESC50_REPORT.md:178`; `docs/AUDIO_MODEL_V3_ESC50_REPORT.md:188`; `docs/AUDIO_MODEL_V3_ESC50_REPORT.md:80`.

Risks: The report asserts source/fold isolation; actual manifests, sources and weights were not accessed; Exact-member rights/attribution unresolved; source/channel confounding not ruled out.

Limits: No new inference, checkpoint/cache access or raw-data evaluation; Historical report is not an independently reproduced result; Exact source/member/model rights and current physical identities remain unverified; README 128-mel statement conflicts with frozen/report 64 bands; paper FFT/hop statements also conflict with frozen 512/256; Do not silently equate windows, recordings, events or validation/test partitions.

Preparation use: **HISTORICAL_LIMITATION_NOTE_ONLY**. Exact-source rights remain unresolved; no external publication/reproduction permission is established here.

## H29-AUDIO-V2 — Prohibited historical Audio V2

Reported values: `{"historical_perfect_scores": "NOT_ADMISSIBLE_AS_CURRENT_PERFORMANCE"}`.

Historical component scores do not override present prohibition.

Provenance/model: `{"checkpoint_reference": "models/audio/best_checkpoint.pt", "configuration_prohibited_sha256": "59b0785f73b201dfd2fb335b98f6ddb764c8544d1ca5fc9e8aa326d74ffcf7d5", "execution": "PROHIBITED"}`.

Split/source provenance: `{"status": "HISTORICAL_LEAKAGE_AND_PROVENANCE_LIMITATIONS"}`.

Evidence: `configs/frozen_experiment_v1.yaml:27`; `src/railway_detection/experiments/frozen_config.py:33`; `src/railway_detection/experiments/frozen_config.py:377`; `src/railway_detection/evaluation/replay_producer.py:207`.

Risks: Existing config-integrity, checkpoint prohibition and replay provenance path remain authoritative.

Limits: No new inference, checkpoint/cache access or raw-data evaluation; Historical report is not an independently reproduced result; Exact source/member/model rights and current physical identities remain unverified; No V2 loading, hashing, inference, replay or rehabilitation.

Preparation use: **PROHIBITION_NOTE_ONLY**. Exact-source rights remain unresolved; no external publication/reproduction permission is established here.

## H29-SYNC010 — Conflicting event_010 synchronization documents

Reported values: `{"reported_acoustic_offset_s": "+2.7158", "reported_metadata_offset_s": "-17.0", "reported_discrepancy_s": "19.72", "document_statuses": ["RESOLVED_VIA_AUDIO", "AMBIGUOUS", "CALIBRATION_SUPPORTED_WITH_CLAIMED_VISUAL_CORROBORATION"]}`.

Historical clock-offset assertions and conflicting classifications, not fresh source synchronization.

Provenance/model: `{"event": "train_events/event_010", "not_the_excluded_qualified_historical_duplicate": true}`.

Split/source provenance: `{"R04_exact_events": ["train_events/event_001", "train_events/event_002", "train_events/event_005", "train_events/event_006", "train_events/event_007", "train_events/event_009", "train_events/event_011", "train_events/event_012", "train_events/event_013", "train_events/event_014", "train_events/event_017"], "event_010_in_R04": false}`.

Evidence: `docs/PHASE5_OUTPUT_AUDIT_AND_R04_FEASIBILITY.md:147`; `docs/R04_CALIBRATION_VALIDATION_REPORT.md:130`; `docs/R04_ALL_EVENT_CALIBRATION_INVESTIGATION.md:273`.

Risks: No independently authenticated source identity or original corroboration inspected; Historical lens-plane correspondence cannot establish physical roadway entry.

Limits: No new inference, checkpoint/cache access or raw-data evaluation; Historical report is not an independently reproduced result; Exact source/member/model rights and current physical identities remain unverified; Do not select one contradictory offset/status by guessing; No new media inspection, T2 lens-plane substitution, acoustic GT shift or R04 expansion.

Preparation use: **HISTORICAL_LIMITATION_NOTE_ONLY**. Exact-source rights remain unresolved; no external publication/reproduction permission is established here.

## H29-T0 — T0 left-censoring documentary register and contradictions

Reported values: `{"reported_left_censored": ["20/23", "23/23"], "reported_observed_emergence_event_ids": ["event_009", "event_015", "event_016"]}`.

Recording-onset censoring claims, not newly observed train arrivals or human-verified counts.

Provenance/model: `{"boundary": "T0", "actual_human_observations_verified": 0}`.

Split/source provenance: `{"candidate_train_events": 23, "genuine_evaluable_denominator": null}`.

Evidence: `docs/DATASET_ANNOTATION_QUALITY_AUDIT.md:59`; `README.md:162`; `docs/PAPER_DRAFT_DESCRIPTIVE_BENCHMARK.md:163`; `docs/generated/SAME_CAMERA_FEASIBILITY_CENSORING_AND_ENGINE_EXCLUSION_20261101_M4E3.md:54`.

Risks: Legacy candidate annotations and report contradictions; source and human evidence not authenticated.

Limits: No new inference, checkpoint/cache access or raw-data evaluation; Historical report is not an independently reproduced result; Exact source/member/model rights and current physical identities remain unverified; Do not infer onset from recording zero or fill missing time; Retain originals/disagreements and per-metric eligibility; no current 20/23 or 23/23 empirical claim.

Preparation use: **HISTORICAL_LIMITATION_NOTE_ONLY**. Exact-source rights remain unresolved; no external publication/reproduction permission is established here.

## H29-M4M5 — Historical M4/M5 non-evaluability

Reported values: `{"reported_evaluable_count": 0, "observed_real_M4_rate": null, "observed_real_M5_count": null}`.

M4 premature opening is primary; M5 integer failure companion. Historical report says unavailable T4 made real outcomes non-evaluable.

Provenance/model: `{"metrics": ["M4", "NEVER_PROTECTED_M5"], "current_approved_GT": null}`.

Split/source provenance: `{"historically_reported_evaluable_count": 0, "current_empirical_denominator": null}`.

Evidence: `docs/generated/master_reaudit/HISTORICAL_BENCHMARK_CAUSALITY_IMPACT_AUDIT.md:22`; `docs/generated/phase2/EXPERIMENT_DESIGN_CONSOLIDATED.md:73`.

Risks: Historical result packages and protected proposals were not reopened; Retroactive timing, missing GT, sparse-sampling and source-clock limits remain relevant.

Limits: No new inference, checkpoint/cache access or raw-data evaluation; Historical report is not an independently reproduced result; Exact source/member/model rights and current physical identities remain unverified; Non-computable is not a measured zero percent or zero failures; Do not drop independent back-camera primary analysis in favor of the old front-only draft.

Preparation use: **HISTORICAL_LIMITATION_NOTE_ONLY**. Exact-source rights remain unresolved; no external publication/reproduction permission is established here.

## H29-MTR — Historical lead-in/timing diagnostics

Reported values: `{"historical_3_6s": "ENGINEERING_DIAGNOSTIC_NOT_REGULATORY_STANDARD", "fresh_physical_MTR": null}`.

MTR remains a feasibility screen, with censoring/eligibility and actuator convention explicit.

Provenance/model: `{"scope": "Historical controller and censoring diagnostics, not hardware timing"}`.

Split/source provenance: `{"human_verified_physical_lead_in": null}`.

Evidence: `docs/generated/master_reaudit/MTR_ARITHMETIC_CENSORING_RECHALLENGE.md:26`; `docs/generated/master_reaudit/HISTORICAL_BENCHMARK_CAUSALITY_IMPACT_AUDIT.md:243`.

Risks: Recording pre-roll is not necessarily physical approach lead-in; Old retroactive simulation and floating-point effects cannot be cited as current real latency.

Limits: No new inference, checkpoint/cache access or raw-data evaluation; Historical report is not an independently reproduced result; Exact source/member/model rights and current physical identities remain unverified; No new scientific threshold or inferential test; A fixed-command mathematical correction is not a rerun of a real-data experiment.

Preparation use: **HISTORICAL_LIMITATION_NOTE_ONLY**. Exact-source rights remain unresolved; no external publication/reproduction permission is established here.

## Manuscript contradictions to exclude from the new draft

The old descriptive manuscript is historical evidence, not an operative authority. It uses 23/23 left-censoring rather than the 20/23 register; front-only primary framing instead of retained independent cameras; superseded T1/T2/T3/T4 meanings; a 12-event synchronization narrative instead of exact eleven-event R04; and an AI-agent contribution label alongside unsupported human-approval/reproducibility statements. README and frozen configuration also disagree on audio feature parameters, and README single-class vision text is not reconciled with the configuration’s front/rear/side mapping. These are recorded contradictions. No original source or checkpoint is inspected to guess a resolution.

The new draft preserves adopted boundary/metric/camera decisions and reports the historic numbers only as limitations/provenance context. Do not average conflicting values, silently choose a split label, backfill timestamps, convert null M4/M5 into zero, or state current zero leakage because the present config disables ungrouped fallback.
