# Reproducibility Audit

Generated 2026-10-16T20:26:49Z from repository files only (read-only).

Status counts: {'FAIL': 3, 'NOT_AVAILABLE': 2, 'PASS': 3, 'UNRESOLVED': 5}

## Evidence classes
- **implemented_software**: present (see tests)
- **synthetic_tests**: present; never research evidence
- **real_data_evaluation**: NOT OBTAINED
- **target_hardware_measurement**: NOT OBTAINED (no target platform declared)
- **controlled_validation**: NOT OBTAINED (no field session has occurred)

## Items
| Item | Status | Detail |
|---|---|---|
| dataset_manifests | **PASS** | all required manifests present and hashed |
| approved_ground_truth | **UNRESOLVED** | 0 valid Stage-2.1 record(s), 0 eligible; receipt: absent_or_invalid; legacy records are never ground truth |
| protocol_version | **UNRESOLVED** | unresolved protocol definitions: ['premature_opening_window'] |
| event_split_decision | **UNRESOLVED** | no event-level split decision exists; none is invented |
| r04_scope_decision | **UNRESOLVED** | no R04 scope decision recorded |
| model_checkpoint_fingerprints | **PASS** | checkpoints match the frozen configuration |
| config_and_policy_fingerprints | **PASS** | raw-byte and canonical-content hashes recorded for both (they answer different questions: Phase 5 cited the canonical policy hash) |
| evaluation_result_provenance | **NOT_AVAILABLE** | no official evaluation result exists; none is claimed |
| experiment_manifest_completeness | **NOT_AVAILABLE** | no experiment manifest supplied; no official Phase 13 experiment exists |
| dependency_lock | **FAIL** | 15 locked package(s) differ from the installed version |
| ultralytics_importable | **FAIL** | ultralytics resolves to a namespace directory without __init__.py; the frozen vision model cannot be loaded in this environment |
| unresolved_decisions | **UNRESOLVED** | decisions still required of the researcher |
| manuscript_claims_vs_evidence | **FAIL** | 9 unsupported or overreaching statement(s) in ['docs/PHASE16_MANUSCRIPT_DRAFT.md', 'Railway_Crossing_Automation_Research_Report.docx'] |

## Unsupported or overreaching manuscript statements
- `OVERCLAIM_LANGUAGE` Railway_Crossing_Automation_Research_Report.docx:15 — guarantee/elimination/validation/real-time style claim with no hedge, negation, status marker or resolvable evidence tag
  > Flawless Departure Confirmation: The safety-critical 'rear' viewpoint class achieved 100.0% precision and 100.0% recall (AP@50: 99.84%), eliminating catastrophic premature opening risks.
- `UNSUPPORTED_EMPIRICAL_NUMBER` Railway_Crossing_Automation_Research_Report.docx:155 — 1.44% appears in no evidence file; no evidence tag
  > Only 7 targets were missed across the entire dataset (False Negatives = 7, an error rate of merely 1.44%).
- `OVERCLAIM_LANGUAGE` Railway_Crossing_Automation_Research_Report.docx:156 — guarantee/elimination/validation/real-time style claim with no hedge, negation, status marker or resolvable evidence tag
  > Flawless Rear Coach Detection (100% Recall): Crucially for crossing clearance safety, the detector achieved 100.0% Recall and 100.0% Precision on the 'rear' viewpoint class with zero missed rear targets (FN = 0) and zero false rear classifi
- `OVERCLAIM_LANGUAGE` Railway_Crossing_Automation_Research_Report.docx:175 — guarantee/elimination/validation/real-time style claim with no hedge, negation, status marker or resolvable evidence tag
  > Flawless side detection (0 misses).
- `OVERCLAIM_LANGUAGE` Railway_Crossing_Automation_Research_Report.docx:175 — guarantee/elimination/validation/real-time style claim with no hedge, negation, status marker or resolvable evidence tag
  > Guarantees crossing occupancy is maintained continuously during train passage.
- `OVERCLAIM_LANGUAGE` Railway_Crossing_Automation_Research_Report.docx:178 — guarantee/elimination/validation/real-time style claim with no hedge, negation, status marker or resolvable evidence tag
  > Flawless rear detection (0 misses).
- `OVERCLAIM_LANGUAGE` Railway_Crossing_Automation_Research_Report.docx:178 — guarantee/elimination/validation/real-time style claim with no hedge, negation, status marker or resolvable evidence tag
  > Guarantees train clearance is reliably captured before gate opening.
- `OVERCLAIM_LANGUAGE` Railway_Crossing_Automation_Research_Report.docx:222 — guarantee/elimination/validation/real-time style claim with no hedge, negation, status marker or resolvable evidence tag
  > This initial research report demonstrates that the core scientific foundation and vision perception components of the multimodal railway level-crossing safety framework have been successfully designed, implemented, and validated.
- `OVERCLAIM_LANGUAGE` Railway_Crossing_Automation_Research_Report.docx:222 — guarantee/elimination/validation/real-time style claim with no hedge, negation, status marker or resolvable evidence tag
  > The vision detector achieved state-of-the-art accuracy with 99.46% mAP@50, crucially maintaining 100% recall on the safety-critical rear coach detection required for safe crossing clearance.
