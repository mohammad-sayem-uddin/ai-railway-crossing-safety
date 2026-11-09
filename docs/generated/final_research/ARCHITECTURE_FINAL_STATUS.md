# Architecture — Final Status

Scope: the system as it stands at the end of the completion programme
(2026-11-09, Mission 3 execution phase). "Executed" means run on original
data under a recorded scope; "synthetic" means exercised only on
constructed streams/fixtures.

## Component status

| Component | Status | Notes |
|---|---|---|
| Vision detector (YOLOv8n adapter, classes front/rear/side, frozen checkpoint `39f402dfe460`, SHA-pinned) | IMPLEMENTED, EXECUTED | Perception runs complete for all 27 events, both cameras (Mission 43: front 6,613 records/329 objects; back 6,479 records/1,020 objects) |
| Vision temporal filter (TemporalEvidenceBuffer) | IMPLEMENTED | Evidence-only; never decides |
| Audio classifier (CompactTrainHornCNN, Audio V3, threshold 0.3700 enforced by loader) | IMPLEMENTED, EXECUTED | 27 events, 2,600 windows, 445 positive (Mission 43). The legacy `models/audio/best_checkpoint.pt` (Audio V2) is prohibited and was never used |
| Evidence contracts (Detection / EvidenceRecord / DecisionRecord) | IMPLEMENTED | Unavailable sources cannot carry detections (enforced in `__post_init__`) |
| Collector / synchronization (MultimodalEvidenceCollector, R04 fail-closed) | IMPLEMENTED, EXECUTED (assembly) | Unregistered vision source with an aligner attached raises; duplicate/out-of-order ingestion rejected and audit-logged |
| Source tracker / sensor health | IMPLEMENTED, synthetic-tested | Staleness >2.0 s; recovery requires confirmation frames |
| Fusion rules + decision engine v1 (frozen) | IMPLEMENTED, FROZEN, **defective for departure** | Label sets overlap (`side`,`train` in both approach and departure) with no camera-role scoping; empirically cannot complete departure on real evidence (0/11, Phase 10.1). Never run on original data through the governed replay path |
| Fusion rules + decision engine v2 (candidate) | IMPLEMENTED, **ADOPTED as canonical experimental policy 2026-11-09** | Fixes the label/role defect; adds RULE_3C disappearance confirmation (documented deviation from founding D-004, explicitly recorded in the adoption); clears 6/11 on identical evidence; passes all 46 Mission 3 synthetic checks. Formal decision record is created when the allowlisted researcher's statement is transcribed (decision package D2); v1 remains the frozen comparison baseline. Not a deployment authorization |
| Simulation mirror (state machine + gate physics + EventSimulationRunner) | IMPLEMENTED | Used by replay and diagnostics |
| FailureInjector (8 modes) | IMPLEMENTED | Never run on original data; the Mission 3 synthetic battery (46/46 checks, both engines) covers the equivalent behaviours at engine level |
| Cache-only replay engine | IMPLEMENTED, execution gated | Front streams only (B0/B1/B2 = front_vision / front_audio / both). **Mission 3 extension IMPLEMENTED + TESTED**: `cache_only_engine_multimodal.py` subclasses the frozen engine (frozen module untouched), adds the back stream (BACK_VISION / DUAL_VISION / DUAL_VISION_AUDIO), fail-closed SyncAligner requirement for dual conditions, and fixes the master-time window defect in the subclass; 8/8 unit tests pass |
| Layer-B processor (offline assembly) | IMPLEMENTED, EXECUTED | Built the Mission 39/43 assemblies (front+audio). **Mission 3 full multimodal assembly built 2026-11-09**: `data/manifests/m3_multimodal_replay_manifest.json` (SHA-256 `3c720167…bbbb`) — 27/27 events with front + audio + back, every front/audio file hash-verified against the Mission 43 B2 manifest; coverage in `results/m3_mm_assembly/` |
| Descriptive execution gate + official readiness gate | IMPLEMENTED, EFFECTIVE | Both verified by direct source audit in Mission 3; neither bypassed nor patched |
| `safety/` package | Governance/access control only | Naming trap: the gate fail-safe logic lives in `fusion/`, not here |
| `configs/fusion.yaml` | Placeholder, superseded | Marked SUPERSEDED in Mission 2; executed config is `frozen_experiment_v1.yaml` + `decision_policy_v1.yaml` (hash `999a7970…a42e`) |

## What the architecture has never done

- Run its decision engine on the full original cohort through the governed path (0 decision events/frames in Missions 39–43).
- Been deployed, connected to any physical gate, or validated in the field. It is a **simulated decision architecture** evaluated on recorded data — exactly as the founding concept specified.
- Used a cascade (none exists anywhere in the repository — verified three independent ways in Mission 1) or the weighted-fusion formula from the 2026-08-31 progress report (documented there only; never implemented; its overclaims were retracted by the 2026-11-02 novelty audit).
