# Research executive summary

The project examines camera and supporting acoustic outputs for train-crossing event analysis. Its current evidence is a five-event single-site pilot: three designated train events, one engine-only case and one designated no-train control, each with front/back recordings. These are the same five physical events across modalities, not fifteen independent observations. Source cohort labels are not promoted truth.

| Existing stage | Actually measured/saved | Scope of interpretation |
|---|---|---|
| B0_front | Five fronts; 1,079 sampled records; 13 predicted objects | Frozen model predictions, not detected unique trains or correctness |
| B0_back | Five backs; 1,100 sampled records; 276 predicted objects | Independent camera outputs; literal trained class names do not establish back clearance |
| B1_audio | Five embedded front audio tracks; 423 windows; 120 scores ≥0.37 | Correlated acoustic window predictions, not horn counts or calibrated correctness |
| B2_front | Five-event input assembly; 1,079 frames; 634 with both stream records | Input availability only; no executed decision replay |

The acoustic runtime was corrected to the training source's natural-log mel transform. Earlier dB-scale outputs (423 windows, 80 positive) remain separate superseded diagnostics and are excluded from final counts. Standalone horn recordings belong to model development and were not substituted for held-out embedded audio.

The 445 B2 input frames without an audio record comprise 25 before the first causal acoustic output and 420 later singleton gaps under the input collector's window. Missing records were not assigned negative predictions or padded. The decision replay collector has different timing semantics, so this does not establish decision-stage missingness or fusion benefit.

The researcher reports separate first-pass review of all five fronts by the researcher and a university classmate, followed by exact agreement between both humans and existing AI annotations. Neither person stored separate original observations; the compared AI version is unspecified. The classmate's partial familiarity is retained. This is positive researcher-reported experience, not independently auditable field-level agreement, accepted GT or a calculated accuracy estimate. AI annotations remain a separate comparison reference.

Accepted canonical GT is not established. The genuine promotion receipt and live canonical protocol-choice/hash are unavailable; the existing B2 execution boundary refused admission. M4/M5/MTR, T1-warning and truth-based accuracy/precision/recall/F1/FP/FN, control/engine and human-agreement metrics therefore remain unavailable, not zero.

Mission40 software validation is reused: 3,815 cases, 3,700 passed, 84 failed, 31 errors and zero skipped. Its 115 nonpassing protected-dependency cases are included in those totals. Mission41 and Mission42 did not rerun that suite. Software fixture checks do not establish empirical accuracy.

The evidence supports bounded description of these model outputs, clocks, processing conditions and input assembly. It does not demonstrate safety improvement, accident reduction, deployment readiness, superiority of fusion or generalization. The professor should assess these limits and the requirements for legitimate reference-dependent evaluation before selecting claims or the next research phase.
