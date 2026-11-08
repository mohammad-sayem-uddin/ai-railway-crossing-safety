# Reading copy — B0_BACK_RESULTS.md

Derived presentation copy: local links are adapted for this package. Evidence text and historical status retain their original scope. Consult the current executive guide for the final result status. [Byte-identical original](../../../../../originals/docs/generated/research_results/mission39/B0_BACK_RESULTS.md). Original SHA-256: `2160f06fa97f40dc42fbe853eba86e83ed9b099d79c5d784cca988c5e36465e6`.

# B0_back actual original-source prediction results

**EMPIRICAL_EXPERIMENT_EXECUTED=1 — ORIGINAL BACK INFERENCE STAGE COMPLETE, 5/5 SOURCES.** This is the separately approved existing back-camera prediction leg, not a completed GT-dependent clearance/metric comparison. 1100 sampled-frame records contain 274 frames with model detections and 276 per-frame predicted objects. Repeated-frame boxes are not unique vehicles or correctness labels.

| Back source/event | Sampled frames | Frames with model detections | Predicted objects front / rear / side | Pipeline wall seconds |
|---|---:|---:|---|---:|
| train_events/event_005 | 391 | 0 | 0 / 0 / 0 | 40.690 |
| train_events/event_021 | 307 | 230 | 1 / 4 / 225 | 54.007 |
| engine_events/event_001 | 49 | 13 | 14 / 0 / 0 | 8.808 |
| train_events/event_001 | 231 | 7 | 0 / 0 / 7 | 58.847 |
| no_train_events/event_001 | 122 | 24 | 25 / 0 / 0 | 12.044 |

Summed event wall time **174.395 seconds**; process peak RSS 465,780,736 bytes. These are observed offline CPU pipeline timings, not controlled hardware comparisons or real-time/deployment proof. Source lengths/views differ from fronts; a larger back prediction count does not establish superior performance. Planned engine/control/train roles remain separate and do not supply canonical labels.

The five exact AUTH35-V back members use absolute video indices 0,1,1,0,0, native timebase1/600 and their own original PTS. Every saved row preserves exact rational clock metadata and validates through the existing generic EvidenceRecord serializer/round trip. Source stat identity matches prior verified members and stays stable. No front timestamp, source or annotation is substituted; clocks are not aligned or shifted and R04 is not executed.

Existing LayerBEventProcessor.run_vision_inference(source_id='camera_2', source_pts=True) and matching controlled provenance were used, with existing serialize_evidence_record. No back record is relabeled camera_front and no unsupported B0_back cache-engine command or new class-to-clearance rule was introduced. The same verified YOLOv8n checkpoint, frozen semantic config, 5 FPS/640×640/confidence0.35/CPU/seed42/square-letterbox request and literal front/rear/side trained class labels remain. Actual packages/effective options/code/times are in [back run manifest](../../../../../originals/docs/generated/research_results/mission39/ACTUAL_BACK_RUN_MANIFEST.json).

**No human back review is asserted.** The researcher-completed review report concerns five fronts only. The worker's inherited global reported_human_review_complete flag referred to that front workflow. The exact [raw manifest](../../../../../originals/docs/generated/research_results/mission39/logs/ACTUAL_BACK_RUN_MANIFEST.raw.json) is retained; the current manifest explicitly renames the context to front-only and marks back human review NOT_REPORTED, with no prediction/time/source changes. [Back validation](../../../../../originals/docs/generated/research_results/mission39/B0_BACK_RESULT_VALIDATION.json) binds both versions. No back boundary/timestamp/GT is invented. M4/M5/clearance, T1/warning/MTR, correctness/control false-positive and other reference-dependent outcomes remain UNAVAILABLE, not zero.

[Event table](../../../../../originals/docs/generated/research_results/mission39/B0_BACK_EVENT_SUMMARY.csv), [per-class descriptors](../../../../../originals/docs/generated/research_results/mission39/B0_BACK_PREDICTED_CLASS_SUMMARY.csv), [prediction-count figure](../../../../../originals/docs/generated/research_results/mission39/figures/B0_BACK_PREDICTED_OBJECTS.png), [processing-time figure](../../../../../originals/docs/generated/research_results/mission39/figures/B0_BACK_PROCESSING_TIME.png), five back JSONLs under predictions/, actual lossless gzip logs and [exact invocation](../../../../../originals/docs/generated/research_results/mission39/invocations/run_b0_back.py) are genuine original-derived outputs. Existing selected-model initializer integrity was enforced at real execution; no standalone verification, raw source rehash/probe, model replacement, threshold tuning, audio/fusion/sync, training/split or raw-media release.

The actual researcher-approved [OP39-B record](../../../../../originals/docs/generated/research_results/mission39/OP39_B_ISSUED_AUTHORIZATION.json) was installed/validated through the existing real canonical guard; [scope completion](../../../../../originals/docs/generated/research_results/mission39/OP39_B_EXECUTION_RECEIPT.json) closes the single invocation and restores the canonical slot to absence while preserving issued/closed evidence. No GT/descriptive-replay grant. Runtime precision-deprecation/native-library warnings are retained exactly; no mid-run changes were made to silence them.
