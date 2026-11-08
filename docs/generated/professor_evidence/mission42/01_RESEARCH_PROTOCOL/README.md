# Protocol, pilot and metric contract

The adopted design uses independent cameras as primary, supporting audio and exploratory fusion. The five selected physical events and ten source references are fixed; no new split, threshold, inference condition or metric is adopted here. Active canonical annotation schema remains 8.1.0-stage2.1. Historical proposed protocols are not automatically operative records.

The existing Mission27 human pilot covers ten front/back sources. Reported human completion covers only five fronts. The broad candidate inventory has 27 events/54 camera references and two excluded duplicates. R04 is separately optional, exactly eleven pairs with event_010 excluded.

M4 is primary; M5 (NEVER_PROTECTED_M5) is its integer companion only with the required complete coverage; MTR is a feasibility screen. Matching source-local reference, actual causal replay coverage, exclusions and eligible per-metric denominators are required. Engine-only interpretation stays separate from pooled train endpoints; no-train controls receive no invented train boundaries. Null/UNCERTAIN/NOT_OBSERVABLE and censoring stay explicit. Do not borrow unaligned back T4 into a front endpoint. Physical T2/occupancy and RD046 remain deferred; no acoustic GT shift, invented exit or duration padding.

[Model/config identity table](MODEL_AND_CONFIG_IDENTITIES.csv) distinguishes raw YAML bytes from canonical semantic configuration identity. Vision uses frozen 5 FPS, 640-square letterbox, confidence 0.35, CPU/seed42; audio uses the corrected V3 transform with threshold 0.37, unchanged window/normalization/model. Model files are not included.

- [MISSION_27_GENUINE_REVIEW_PILOT_PROTOCOL.md](reading_views/docs/generated/master_reaudit/MISSION_27_GENUINE_REVIEW_PILOT_PROTOCOL.md)
- [MISSION_27_HUMAN_REVIEWER_HANDBOOK.md](../07_HUMAN_REVIEW/reading_views/docs/generated/master_reaudit/MISSION_27_HUMAN_REVIEWER_HANDBOOK.md)
- [EXPERIMENT_PROTOCOL_FREEZE.md](reading_views/docs/generated/master_reaudit/mission36/EXPERIMENT_PROTOCOL_FREEZE.md)
- [PHASE11_3_REVIEW_INVENTORY.json](../02_SOURCE_PROVENANCE/originals/docs/PHASE11_3_REVIEW_INVENTORY.json)
- [metrics.py](../10_REPRODUCIBILITY/source_snapshot/src/railway_detection/evaluation/metrics.py)
- [protocol_choices.py](../10_REPRODUCIBILITY/source_snapshot/src/railway_detection/evaluation/protocol_choices.py)
- [stage2_1_schema.py](../10_REPRODUCIBILITY/source_snapshot/src/railway_detection/annotation/stage2_1_schema.py)

The Mission36 freeze is a historical preparation document: later Mission37–39 evidence supersedes its unverified-model/PTS/inference standing without editing its original bytes. The selected M4 profile is preserved; the missing live canonical protocol-choice record remains distinct from its computed candidate profile.
