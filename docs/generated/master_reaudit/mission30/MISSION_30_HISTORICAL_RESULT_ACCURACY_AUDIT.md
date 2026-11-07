# Mission 30 historical-result accuracy audit

Status: HUMAN_REVIEW_REQUIRED_NOT_SUBMISSION_AUTHORIZED

All eight canonical categories are retained as historical limitation notes. This verifies documentary transcription and current source bindings, not underlying recordings, model identity, correctness of original experiments or permission. No raw source path or checkpoint hash is reproduced. Audio values remain separated by report, split role and aggregation unit.

## H29-VISION

Reported metadata: `{"mAP50": "0.9946", "mAP50_95": "0.855", "reported_objects": 487, "reported_cropped_images": 3165}`.

Metric role: Reported bounding-box average precision at IoU .50 and over .50:.95; not event detection, crossing protection, direction or safety rates.

Exact documentary sources: `README.md`, line 102 (SHA-256 `d40b6918989c53bea5ed75fefc575b6e92dd884436cd1994def1ec27ad045854`); `README.md`, line 106 (SHA-256 `d40b6918989c53bea5ed75fefc575b6e92dd884436cd1994def1ec27ad045854`); `configs/frozen_experiment_v1.yaml`, line 15 (SHA-256 `b8ef5da052f002e75a2da0985add02a72d0d5684936263c14257aa12b0c9ac9a`).

Required qualifications: No new inference, checkpoint/cache access or raw-data evaluation; Historical report is not an independently reproduced result; Exact source/member/model rights and current physical identities remain unverified; No event-independent or cross-site generalization; 487 objects and 3,165 images are reported development counts, not 27 independent train events.

Manuscript location: Section 7, Table 5 and accompanying text. Positive empirical reuse: excluded. Independent reproduction: not performed. Rights: unresolved exact-member/model scope; external publication remains separately gated.

## H29-AUDIO-README

Reported metadata: `{"F1": "0.869", "ROC_AUC": "0.961", "operating_threshold": "0.3700"}`.

Metric role: README labels these validation metrics; detailed report labels comparable numbers test-window outcomes.

Exact documentary sources: `README.md`, line 117 (SHA-256 `d40b6918989c53bea5ed75fefc575b6e92dd884436cd1994def1ec27ad045854`); `configs/frozen_experiment_v1.yaml`, line 25 (SHA-256 `b8ef5da052f002e75a2da0985add02a72d0d5684936263c14257aa12b0c9ac9a`).

Required qualifications: No new inference, checkpoint/cache access or raw-data evaluation; Historical report is not an independently reproduced result; Exact source/member/model rights and current physical identities remain unverified; Rounded AUC .961 versus detailed .9613 is reported precision, not an independent replication; No event-level or gate-level performance claim.

Manuscript location: Section 7, Table 5 and accompanying text. Positive empirical reuse: excluded. Independent reproduction: not performed. Rights: unresolved exact-member/model scope; external publication remains separately gated.

## H29-AUDIO-REPORT

Reported metadata: `{"F1": "0.8690", "ROC_AUC": "0.9613", "operating_threshold": "0.3700", "reported_validation_F1": "0.9942", "recording_F1": "0.8667", "recording_ROC_AUC": "0.9408"}`.

Metric role: Window F1/AUC and separately pooled recording F1/AUC; neither is a train-event safety metric.

Exact documentary sources: `docs/AUDIO_MODEL_V3_ESC50_REPORT.md`, line 178 (SHA-256 `d8656f2a6a8325a5420d471b71748d4ade5e0b8b1fa8a4f03af6e1feccd207b0`); `docs/AUDIO_MODEL_V3_ESC50_REPORT.md`, line 188 (SHA-256 `d8656f2a6a8325a5420d471b71748d4ade5e0b8b1fa8a4f03af6e1feccd207b0`); `docs/AUDIO_MODEL_V3_ESC50_REPORT.md`, line 80 (SHA-256 `d8656f2a6a8325a5420d471b71748d4ade5e0b8b1fa8a4f03af6e1feccd207b0`).

Required qualifications: No new inference, checkpoint/cache access or raw-data evaluation; Historical report is not an independently reproduced result; Exact source/member/model rights and current physical identities remain unverified; README 128-mel statement conflicts with frozen/report 64 bands; paper FFT/hop statements also conflict with frozen 512/256; Do not silently equate windows, recordings, events or validation/test partitions.

Manuscript location: Section 7, Table 5 and accompanying text. Positive empirical reuse: excluded. Independent reproduction: not performed. Rights: unresolved exact-member/model scope; external publication remains separately gated.

## H29-AUDIO-V2

Reported metadata: `{"historical_perfect_scores": "NOT_ADMISSIBLE_AS_CURRENT_PERFORMANCE"}`.

Metric role: Historical component scores do not override present prohibition.

Exact documentary sources: `configs/frozen_experiment_v1.yaml`, line 27 (SHA-256 `b8ef5da052f002e75a2da0985add02a72d0d5684936263c14257aa12b0c9ac9a`); `src/railway_detection/experiments/frozen_config.py`, line 33 (SHA-256 `bcbe3684192664e4cb8b8d4221389cf4d13ee2a7f1c72cdc815f0a671f23e3bd`); `src/railway_detection/experiments/frozen_config.py`, line 377 (SHA-256 `bcbe3684192664e4cb8b8d4221389cf4d13ee2a7f1c72cdc815f0a671f23e3bd`); `src/railway_detection/evaluation/replay_producer.py`, line 207 (SHA-256 `855818b3dcc73ddab9b2669736e2dbfb5df861e986d0e6acc7697129bc3bed43`).

Required qualifications: No new inference, checkpoint/cache access or raw-data evaluation; Historical report is not an independently reproduced result; Exact source/member/model rights and current physical identities remain unverified; No V2 loading, hashing, inference, replay or rehabilitation.

Manuscript location: Section 7, Table 5 and accompanying text. Positive empirical reuse: excluded. Independent reproduction: not performed. Rights: unresolved exact-member/model scope; external publication remains separately gated.

## H29-SYNC010

Reported metadata: `{"reported_acoustic_offset_s": "+2.7158", "reported_metadata_offset_s": "-17.0", "reported_discrepancy_s": "19.72", "document_statuses": ["RESOLVED_VIA_AUDIO", "AMBIGUOUS", "CALIBRATION_SUPPORTED_WITH_CLAIMED_VISUAL_CORROBORATION"]}`.

Metric role: Historical clock-offset assertions and conflicting classifications, not fresh source synchronization.

Exact documentary sources: `docs/PHASE5_OUTPUT_AUDIT_AND_R04_FEASIBILITY.md`, line 147 (SHA-256 `8472df7943cc61d3125f3d3544b5b21470dcf304cde5d07db2ca54e55e4c6997`); `docs/R04_CALIBRATION_VALIDATION_REPORT.md`, line 130 (SHA-256 `9e4e80d599b85933b582ee733fc32f2849d452bd666caa39bcc3625b96521ae3`); `docs/R04_ALL_EVENT_CALIBRATION_INVESTIGATION.md`, line 273 (SHA-256 `3869fabf410de0b373de227a57b28d9738a0eecd2b134926f56ae67fa68134ff`).

Required qualifications: No new inference, checkpoint/cache access or raw-data evaluation; Historical report is not an independently reproduced result; Exact source/member/model rights and current physical identities remain unverified; Do not select one contradictory offset/status by guessing; No new media inspection, T2 lens-plane substitution, acoustic GT shift or R04 expansion.

Manuscript location: Section 7, Table 5 and accompanying text. Positive empirical reuse: excluded. Independent reproduction: not performed. Rights: unresolved exact-member/model scope; external publication remains separately gated.

## H29-T0

Reported metadata: `{"reported_left_censored": ["20/23", "23/23"], "reported_observed_emergence_event_ids": ["event_009", "event_015", "event_016"]}`.

Metric role: Recording-onset censoring claims, not newly observed train arrivals or human-verified counts.

Exact documentary sources: `docs/DATASET_ANNOTATION_QUALITY_AUDIT.md`, line 59 (SHA-256 `286661120451ab4c8650f66ada22b84576f7efd20bb0467ec08af42d2ad57273`); `README.md`, line 162 (SHA-256 `d40b6918989c53bea5ed75fefc575b6e92dd884436cd1994def1ec27ad045854`); `docs/PAPER_DRAFT_DESCRIPTIVE_BENCHMARK.md`, line 163 (SHA-256 `03444930ec0d73e9dad16a2b510511c61e9a1302e3e6a25cf83307d81a26ea78`); `docs/generated/SAME_CAMERA_FEASIBILITY_CENSORING_AND_ENGINE_EXCLUSION_20261101_M4E3.md`, line 54 (SHA-256 `bc6fa789784d9bcfd9426a167b1c222d01685d63671fd7ef42b153b66d8fa75e`).

Required qualifications: No new inference, checkpoint/cache access or raw-data evaluation; Historical report is not an independently reproduced result; Exact source/member/model rights and current physical identities remain unverified; Do not infer onset from recording zero or fill missing time; Retain originals/disagreements and per-metric eligibility; no current 20/23 or 23/23 empirical claim.

Manuscript location: Section 7, Table 5 and accompanying text. Positive empirical reuse: excluded. Independent reproduction: not performed. Rights: unresolved exact-member/model scope; external publication remains separately gated.

## H29-M4M5

Reported metadata: `{"reported_evaluable_count": 0, "observed_real_M4_rate": null, "observed_real_M5_count": null}`.

Metric role: M4 premature opening is primary; M5 integer failure companion. Historical report says unavailable T4 made real outcomes non-evaluable.

Exact documentary sources: `docs/generated/master_reaudit/HISTORICAL_BENCHMARK_CAUSALITY_IMPACT_AUDIT.md`, line 22 (SHA-256 `08b201c78a4c6ca6b4ed2638cc76824f2accfd771a0a3261849b31e8b4f37154`); `docs/generated/phase2/EXPERIMENT_DESIGN_CONSOLIDATED.md`, line 73 (SHA-256 `f9ae618bb1d61afe7610d28c3a3399293f5b28a76d9abb12ad8dfb53285c2d1b`).

Required qualifications: No new inference, checkpoint/cache access or raw-data evaluation; Historical report is not an independently reproduced result; Exact source/member/model rights and current physical identities remain unverified; Non-computable is not a measured zero percent or zero failures; Do not drop independent back-camera primary analysis in favor of the old front-only draft.

Manuscript location: Section 7, Table 5 and accompanying text. Positive empirical reuse: excluded. Independent reproduction: not performed. Rights: unresolved exact-member/model scope; external publication remains separately gated.

## H29-MTR

Reported metadata: `{"historical_3_6s": "ENGINEERING_DIAGNOSTIC_NOT_REGULATORY_STANDARD", "fresh_physical_MTR": null}`.

Metric role: MTR remains a feasibility screen, with censoring/eligibility and actuator convention explicit.

Exact documentary sources: `docs/generated/master_reaudit/MTR_ARITHMETIC_CENSORING_RECHALLENGE.md`, line 26 (SHA-256 `3cbe0dbafb966e187086bed12d3ce4605461ea752f2eb0dc573e9160da072162`); `docs/generated/master_reaudit/HISTORICAL_BENCHMARK_CAUSALITY_IMPACT_AUDIT.md`, line 243 (SHA-256 `08b201c78a4c6ca6b4ed2638cc76824f2accfd771a0a3261849b31e8b4f37154`).

Required qualifications: No new inference, checkpoint/cache access or raw-data evaluation; Historical report is not an independently reproduced result; Exact source/member/model rights and current physical identities remain unverified; No new scientific threshold or inferential test; A fixed-command mathematical correction is not a rerun of a real-data experiment.

Manuscript location: Section 7, Table 5 and accompanying text. Positive empirical reuse: excluded. Independent reproduction: not performed. Rights: unresolved exact-member/model scope; external publication remains separately gated.

## Focused accuracy findings

Vision retains mAP50 0.9946, mAP50:95 0.8550, 487 objects, development_fallback, leakage risk true and ungrouped fallback allowed. The canonical register stores the numerically equivalent 0.855; the manuscript preserves README precision 0.8550. README's single-class description (line 99) conflicts with the frozen configuration's front/rear/side mapping (lines 17–20). Neither is chosen as verified asset identity.

The detailed audio report, lines 173–175, describes validation threshold selection at 0.3700 and validation F1 0.9942. Lines 178–188 report test-window F1 0.8690/AUC 0.9613; lines 198–206 report recording-level F1 0.8667/AUC 0.9408. README line 117 labels 0.869/0.961 as validation. Rounding and split-role conflict are reported separately. The declared checkpoint identity was not verified against weights; Audio V2 remains prohibited.

Event_010 retains the resolution/ambiguity/corroboration conflict and stays outside R04. The 20/23 and 23/23 censoring reports are both retained, without computing a new proportion. Historical M4/M5 nulls remain null rather than measured zeros. MTR's recorded 3.6–3.8-second diagnostic conventions are not an approved railway standard or a new threshold.

No contradiction was resolved through favorable-number selection, acoustic GT shift, inferred source identity, invented physical T2, annotation, media inspection or model execution. Canonical records are unchanged.
