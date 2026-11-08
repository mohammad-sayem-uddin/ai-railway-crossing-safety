# Software validation evidence

**Mission40 validated 3,815 cases: 3,700 passed, 84 failed, 31 errors, 0 skipped**, across 168 modules/53 groups. The 115 inherited protected-dependency cases are the failure/error subset, not extra tests. Mission41 reused this evidence; Mission42 verifies its retained files/source bindings without running tests. The suite is not fully passing.

All completed group JUnit, stdout/stderr, collection and policy evidence is included in compressed form with actual outcome/triage tables. Three previously nonpassing cases were repaired through two test-fixture isolation corrections: synthetic pilot sentinels/refusal of production reads, and constructed CLI artifact/hash/config inputs. No production algorithm changed in Mission40 and no case was dropped or disabled. The remaining protected dependencies are disclosed.

Earlier relevant changes are separately documented: Mission37 native PTS/neutral browser implementation; Mission38 front-only constructor, frozen prediction options and cache/replay PTS integration; Mission39 demonstrated audio natural-log training/runtime parity correction. Mission37's 52 and Mission38's 51 focused passes overlap subsequent scopes and are not added to Mission40 totals. Model initialization/source inference findings are distinct from generated-fixture software checks. Python audit guards are not OS isolation.

- [PTS_PRESERVATION_IMPLEMENTATION.md](../10_REPRODUCIBILITY/reading_views/docs/generated/master_reaudit/mission37/PTS_PRESERVATION_IMPLEMENTATION.md)
- [FOCUSED_VALIDATION_RECEIPT.json](originals/docs/generated/master_reaudit/mission37/FOCUSED_VALIDATION_RECEIPT.json)
- [B0_FRONT_RUNTIME_ADMISSION.md](../06_B2_INPUT_ASSEMBLY/reading_views/docs/generated/master_reaudit/mission38/B0_FRONT_RUNTIME_ADMISSION.md)
- [FOCUSED_VALIDATION_RECEIPT.json](originals/docs/generated/master_reaudit/mission38/FOCUSED_VALIDATION_RECEIPT.json)
- [TRAINING_RUNTIME_FEATURE_CORRECTION.json](../05_B1_AUDIO_RESULTS/originals/docs/generated/research_results/mission39/audio_followup/TRAINING_RUNTIME_FEATURE_CORRECTION.json)
- [SOFTWARE_TEST_VALIDATION.md](reading_views/docs/generated/research_results/mission40/SOFTWARE_TEST_VALIDATION.md)
- [FAILURE_AND_REGRESSION_ANALYSIS.md](reading_views/docs/generated/research_results/mission40/FAILURE_AND_REGRESSION_ANALYSIS.md)
- [BASELINE_118_CASE_TRIAGE.csv](originals/docs/generated/research_results/mission40/BASELINE_118_CASE_TRIAGE.csv)
- [FULL_RUN_RECEIPT.json](originals/docs/generated/research_results/mission40/software_validation/FULL_RUN_RECEIPT.json)
- [TEST_CASE_OUTCOMES.csv](originals/docs/generated/research_results/mission40/software_validation/TEST_CASE_OUTCOMES.csv)
- [SOFTWARE_OUTCOMES.png](originals/docs/generated/research_results/mission40/software_validation/SOFTWARE_OUTCOMES.png)
