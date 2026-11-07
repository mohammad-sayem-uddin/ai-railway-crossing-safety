# Mission 31 research gaps and unresolved conflicts

Status: AUDIT_COMPLETE_WITH_DECLARED_COVERAGE_GAPS; EMPIRICAL_EXECUTION_NOT_READY.

“Newly surfaced” below means found in this wider roadmap audit relative to the bounded Mission29/30 summary; it does not imply the underlying conflict was created now. No historical artifact is edited, and no disagreement is resolved by favorable-number selection.

## GAP-01 — Source identity and rights are not established

The 63 documentary source references remain identity-unknown; 62 rights records are unknown and one partial, with all 630 dimension statuses unknown. Known paths, historical hash claims or public upstream/software terms do not establish exact recording/member/model use. “Blocked by data” means missing verified legitimate input evidence, not proof that a physical file is absent.

Affected activity IDs: M31-DATA-INVENTORY; all current conditional research. Evidence: `docs/generated/master_reaudit/MISSION_29_FINAL_VALIDATION.json:L39`.

## GAP-02 — Vision split warning versus actual event independence

Retain development_fallback, leakage_risk=true and allow_ungrouped_fallback=true. The revised grouped-CV specification distinguishes these flags from proof that a fallback branch ran or that actual cross-role duplication occurred. Its source-name assignments do not certify physical-event grouping or unseen model exposure. No protected split/manifest/checkpoint was inspected to settle the question.

Affected activity IDs: M31-VISION-LEAKAGE; M31-GROUPED-CV. Evidence: `docs/generated/master_reaudit/MISSION_17C2_REVISED_GROUPED_CV_SPLIT_SPEC.md:L20`.

## GAP-03 — Conflicting vision values, class descriptions and count roles

The older experimental-status table reports mAP50 0.782/mAP50:95 0.521 for declared checkpoint prefix 3f5bb5b2, while README and the bounded historical register report 0.9946/0.8550. The same table names 3157 images versus README 3165 cropped images/487 objects. These may involve different roles or evaluation histories; no explanation is established. Single-class train versus front/rear/side mapping also remains unresolved. Do not choose the higher result, infer eight extra images, or claim direction validation.

Affected activity IDs: M31-VISION-SCORE; six vision run records. Evidence: `docs/generated/EXPERIMENTAL_MATRIX_AND_STATUS_20261029.md:L63`; `README.md:L102`.

## GAP-04 — Audio V1, V2, V3 and aggregation roles

V1 remains historical; no actual training completion is established from filenames. V2 remains prohibited. V3 README labels F1 0.869/AUC 0.961 as validation, whereas the detailed report gives validation F1 0.9942 at threshold 0.3700, test-window F1 0.8690/AUC 0.9613 over reported 182 windows/26 recordings, and recording F1 0.8667/AUC 0.9408. Retain roles and reported precision separately; none is a crossing-event or safety result.

Affected activity IDs: M31-A1-*; M31-A3-VAL/WINDOW/RECORDING; audio run rows. Evidence: `README.md:L117`; `docs/AUDIO_MODEL_V3_ESC50_REPORT.md:L174`.

## GAP-05 — Audio features, checkpoint lineage and the cross-validation label

Historical 128-versus-64 mel and transform/hop descriptions conflict. The current expected checkpoint hash is configuration-declared only here. The deep completion audit calls V3 training “Cross-Validation”; the detailed report describes one fold-based train/validation/test allocation. That title does not establish repeated independent CV runs. No protected features/weights were opened or hashed.

Affected activity IDs: M31-AUDIO-FEATURES; M31-AUDIO-CV-LABEL. Evidence: `docs/DEEP_RESEARCH_COMPLETION_AUDIT_20261025.md:L320`; `docs/generated/master_reaudit/MISSION_29_HISTORICAL_RESULTS_REGISTER.json:L188`.

## GAP-06 — Legacy condition vocabularies are not equivalent

The experimental-status table describes B5b as audio dropout and B6b as 30% detection jitter; current runner documentation describes B5b as midway front-camera loss and B6b as dual dropout. Legacy/cache-engine/template B0–B4 and E-factor names also differ. An indexed package needs its exact run manifest before its applied treatment is known. S1–S3 are qualified proposal aliases, not additional completed replications. B8 exists in family metadata without a recovered scientific run definition.

Affected activity IDs: 17 historical B packages; template/metadata/mapping rows. Evidence: `docs/generated/EXPERIMENTAL_MATRIX_AND_STATUS_20261029.md:L22`; `src/railway_detection/experiments/runner.py:L10`; `docs/generated/phase5/MISSION_10_CONDITION_MAPPING.md:L11`.

## GAP-07 — Older completion and authorization labels are not current grants

The deep audit calls model/replay records “PROMOTED / VALID”; Phase8/10 reports quote historical restricted authorization and completion. Later source/rights/human verification is unresolved. Preserve those documents as historical accounts; neither their labels nor authorized_for_execution booleans prove current exact-source canonical permission or legitimate current completion. Corrective rerun files remain uninspected original outputs.

Affected activity IDs: model, R04 and corrective run records. Evidence: `docs/DEEP_RESEARCH_COMPLETION_AUDIT_20261025.md:L315`; `docs/generated/master_reaudit/MISSION_29_FINAL_SCIENTIFIC_EXECUTION_DECISION.json:L21`.

## GAP-08 — event_010 and clock conventions

Retain acoustic +2.7158 s versus metadata -17.0 s and the reported 19.72 s discrepancy, together with resolution/ambiguity/claimed-corroboration disagreements. Audio lag reproducibility is not hardware clock validation. Never acoustically shift human GT. event_010 remains excluded from R04 exactly eleven; resolving it is not an added universal prerequisite for the existing eligible subset or independent-camera work.

Affected activity IDs: M31-SYNC-010; M31-SYNC-CAL; M31-NEXT-R04. Evidence: `docs/generated/master_reaudit/MISSION_29_HISTORICAL_RESULTS_REGISTER.json:L250`.

## GAP-09 — T0, environmental labels and physical lead-in

20/23 and 23/23 censoring reports are both retained. Session/day/night assertions in older narratives are not authenticated condition labels or a known nighttime sample size. Recording zero is not physical approach onset; censored unknown direction remains unverifiable. No weather, fog, rain, night or second-site cohort is established by the present inspection.

Affected activity IDs: M31-CENSOR-T0; environmental rows. Evidence: `docs/generated/master_reaudit/MISSION_29_HISTORICAL_RESULTS_REGISTER.json:L322`; `docs/generated/master_reaudit/MISSION_29_SCIENTIFIC_CLAIMS_REGISTER.json:L157`.

## GAP-10 — T1/T2, occupancy and engine identity

Retain adopted frog/approach T1 and physical-roadway-entry T2 deferral. Legacy E-matrix T1 danger-entry/T2 occupancy wording cannot silently substitute for the current convention. T2 and occupancy remain deferred, no lens-plane or invented exit. Engine-only versions/clearance disagreements do not increase N or permit pooling with train/no-train outcomes.

Affected activity IDs: M31-T1-BOUNDARY; T2-PHYSICAL; OCCUPANCY; ENGINE-IDENTITY. Evidence: `docs/generated/master_reaudit/MISSION_29_PATH_A_EMPIRICAL_RESEARCH_REQUIREMENTS.md:L18`; `docs/FINAL_ABLATION_MATRIX.md:L44`.

## GAP-11 — M4/M5 nulls and historic numerical claims

Canonical M4/M5 were non-evaluable without approved T4 and legitimate replay. A null rate/count is not measured zero. Older “Premature” columns and assertions of eliminated failures are not evidence for computable current M4/M5; exact endpoint/GT/run provenance is unresolved. Historical causal stepping and closed-duration artifacts remain relevant and are not repaired by relabeling old tables.

Affected activity IDs: M31-EVENT-M4/M5; legacy B and stats rows. Evidence: `docs/generated/master_reaudit/HISTORICAL_BENCHMARK_CAUSALITY_IMPACT_AUDIT.md:L22`; `docs/generated/EXPERIMENTAL_MATRIX_AND_STATUS_20261029.md:L33`.

## GAP-12 — MTR terminology, feasibility and controls

README uses Minimum Time Reserve terminology; the metric audit uses missed-train-rate with a lead-in feasibility screen. Do not treat a time diagnostic, a rate and a feasibility decision as interchangeable. Preserve the adopted screen role and exact operative metric contract without introducing thresholds. Historical 3.6/3.7/3.8-second conventions are not a railway standard or measured physical lead-in. Three unconfirmed controls do not establish concurrent overlap or an hourly false-alarm rate.

Affected activity IDs: M31-EVENT-MTR; CONTROL-EXPOSURE. Evidence: `README.md:L161`; `docs/generated/master_reaudit/MASTER_METRIC_AND_EXPERIMENT_AUDIT.md:L100`.

## GAP-13 — Proposed names and actual back-stream interfaces

The condition-mapping audit distinguishes implemented independent-camera producer modes from provisional B0_back/B2_back/stateless names refused by the cache engine. B0_dual/B2_dual are unadopted labels, not executable experiments. The exact scientific/backend binding and actual back-audio availability remain unverified. A naming gap is not permission to build another backend.

Affected activity IDs: M31-TECH-BACK-MAPPING; current back plans. Evidence: `docs/generated/phase5/MISSION_10_CONDITION_MAPPING.md:L14`.

## GAP-14 — Perturbation semantics and retired matrices

Do not restore the E1–E10 primary grammar, old unsupported audio authority, inferential contrasts or guessed B7e settings. Older B7d/e proposals say disorder may be sorted away and no stale branch exists; current source now preserves requested arrival order and requires an explicit stale schedule. Distinguish that source update from scientific adoption or empirical robustness evidence. Constructed dynamic reapproach E10g is Type2, not a natural event.

Affected activity IDs: retired E rows; ROBUST-ORDER/STALE/JITTER; sweep rows. Evidence: `src/railway_detection/experiments/runner.py:L575`; `src/railway_detection/experiments/runner.py:L124`.

## GAP-15 — Pilot, actual people, accepted services and current grants

The five-event/ten-source pilot is PILOT_NOT_READY. All thirteen prerequisite categories remain evidenced as pending. Actual identity, qualifications, appointments and source access are missing; primary/second/adjudicator must be distinct as required. No local SQLite instance, username, diagnostic clock or fixture verifier establishes deployment acceptance. Optional external audit and public release are not universal private-pilot blockers.

Affected activity IDs: M31-HUMAN-PILOT; TECH-SERVICES; GT-PROMOTION. Evidence: `docs/generated/master_reaudit/MISSION_28_FINAL_PILOT_READINESS_DECISION.json:L3973`.

## GAP-16 — Software, host profiling and the engineering freeze

The saved selected run passes 3649 cases with 118 excluded; the full guarded audit remains NONPASSING with 87 failures and 31 setup errors. Their overlapping subsets are never added. A synthetic host benchmark has timing arrays but no target declaration or acceptance criterion, and is not field real-time evidence. No material new core defect or accepted integration requirement is established by this documentary audit.

Affected activity IDs: closed support rows; target hardware/optimization proposals. Evidence: `docs/generated/master_reaudit/MISSION_29_FINAL_VALIDATION.json:L57`; `docs/PHASE14_REALTIME_OPTIMIZATION_REPORT.md:L6`.

## GAP-17 — Protected completion records and archive coverage

The original experiment registry, protected run manifests, checkpoints, caches, source members and review corpora remain unread. Git index names do not establish physical availability, untracked run coverage, completion or rights. Archive copies and figures are not new independent experiments. Some exact input/output configurations cannot be recovered under this scope and are explicitly UNSET or NOT VERIFIED in the CSV.

Affected activity IDs: M31-TECH-REGISTRY-COMPLETION; all index-only rows. Evidence: `src/railway_detection/experiments/provenance_registry.py:L12`; Git index at 78dad966cb021a450e3cbe0f2e06e696b9e823bd.

## Exact unchanged pilot prerequisites

| Category | Missing evidence/acceptance | Required for |
|---|---|---|
| SOURCE_IDENTITY | Attributable original acquisition/member/custodian evidence | AUTHORIZATION_REVIEW_READINESS |
| EXACT_SOURCE_RIGHTS | Current exact-source and purpose rights | AUTHORIZATION_REVIEW_READINESS |
| EXTERNAL_APPLICABILITY | Actual scoped applicability determinations | AUTHORIZATION_REVIEW_READINESS |
| PRIMARY_REVIEWER | Actual qualified appointed primary reviewer | AUTHORIZATION_REVIEW_READINESS |
| INDEPENDENT_SECOND_REVIEW | Distinct qualified physical person and exposure evidence | AUTHORIZATION_REVIEW_READINESS |
| SEPARATE_ADJUDICATION | Actual separate qualified adjudication capability | AUTHORIZATION_REVIEW_READINESS |
| SOURCE_PRESENTATION | Accepted blind guarded source presentation | AUTHORIZATION_REVIEW_READINESS |
| TRUSTED_IDENTITY | Authenticated physical people and current scoped assignment | AUTHORIZATION_REVIEW_READINESS |
| TRUSTED_TIME | Accepted current time service; diagnostic clock is insufficient | AUTHORIZATION_REVIEW_READINESS |
| EVIDENCE_STORAGE | Authenticated immutable storage; local SQLite is not proof | AUTHORIZATION_REVIEW_READINESS |
| AUDIT_REVOCATION | Retained anchors, current revocation and audit acceptance | AUTHORIZATION_REVIEW_READINESS |
| PROTOCOL_SCHEMA | Exact operative protocol/adoption and active 8.1 compatibility | AUTHORIZATION_REVIEW_READINESS |
| CANONICAL_AUTHORIZATION | Actual current operation-specific canonical authorization | EXECUTION_ONLY |

Canonical authorization is an execution prerequisite, not a circular prerequisite for entering authorization review. Independent observations precede later adjudication and promotion; do not require their own future output receipt before a first blind pass. RD046 remains deferred and the existing active 8.1 plausibility floor is not scientific sufficiency. ACT-01–06 genuine evidence remains necessary; ACT-07 only if an auditor is actually appointed. No new person, right, appointment, observation, condition threshold or grant is invented.
