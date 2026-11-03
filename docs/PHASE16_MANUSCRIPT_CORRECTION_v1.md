# Phase 16 — Historical Manuscript Correction (v1)

**Status:** Corrected, evidence-limited draft; not publication-approved  
**Version:** `phase16-manuscript-correction/1`  
**Date:** 2026-10-19  
**Original preserved:** `Railway_Crossing_Automation_Research_Report.docx` (unchanged)

## Purpose and preservation rule

This file is an additive correction to the historical progress report. The original
DOCX is preserved byte-for-byte so that the historical record remains auditable. This
correction must not be substituted for the original without an explicit researcher
decision. It removes unsupported safety language and separates Layer A image metrics
from the still-blocked Layer B event evaluation.

The reproducibility audit currently reports findings in the historical DOCX. That is
expected: the audit records the historical defect rather than silently rewriting it.
The corrected text below is the version intended for any future review.

## Corrected executive summary

This report documents a research prototype for multimodal railway level-crossing
perception. The repository contains a YOLOv8n image detector, an audio processing
pipeline, and a simulated decision-policy implementation. The available quantitative
vision evidence is a held-out still-image (Layer A) evaluation; it is not an event-level
railway safety evaluation.

The Layer A evaluation recorded mAP@50 of 99.46% and mAP@50:95 of 85.50% at the
documented thresholds. The rear class recorded precision 100.0%, recall 100.0%, and
AP@50 99.84% in that image evaluation. These values describe the evaluated image
objects only and do not establish train-clearance detection, gate timing, or safe
operation. [evidence: experiments/vision/39f402dfe460/evaluation/metrics.json]

## Corrected limitations and scope

- No approved Stage-2.1 ground truth is available for a formal Layer B evaluation.
- R04 synchronization scope remains unresolved for the affected events; the exploratory
  dual-camera run is not treated as hardware-synchronization validation.
- Recordings begin after the train is visible in the available event material, so a
  true detection-latency claim is not made.
- Barrier behavior is simulated. No physical gate, safety integrity level, standards
  compliance, deployment readiness, or safety certification is claimed.
- The historical report did not establish flawless detection, guaranteed clearance, elimination of premature-opening risk, or state-of-the-art performance; those statements are retired and must not be reused.

## Corrected results language

The reproducible result currently supported by repository evidence is the Layer A
per-image detector evaluation described above. The evaluation contains 487 annotated
objects, 480 true positives, 94 false positives, and 7 false negatives at its recorded
operating point. These are image-object counts from that evaluation artifact, not event
counts or field outcomes. [evidence: experiments/vision/39f402dfe460/evaluation/metrics.json]

The rear-class result is reported as a class-level image metric. It must not be
described as proof that a departure camera observes the physical tail of every train,
that crossing occupancy is maintained continuously, or that a gate may safely open.
Those questions require an approved event-level protocol, verified synchronization,
approved labels, and an authorized run; they remain outside this correction.

## Reproducibility record

- Frozen configuration: `configs/frozen_experiment_v1.yaml`.
- Decision policy: `configs/decision_policy_v1.yaml`.
- Vision checkpoint: `experiments/vision/39f402dfe460/checkpoints/weights/best.pt`.
- Audio method described for future work is the frozen V3 artifact only; no prohibited
  legacy audio checkpoint is used or treated as valid evidence.
- Exact package and environment findings are recorded in
  `docs/PHASE16_REPRODUCIBILITY_AND_ENVIRONMENT_20261019.md`.
- The read-only audit is run with:

  ```text
  venv/bin/python scripts/audit_reproducibility.py \
    --root . --json /tmp/reproducibility-audit.json --md /tmp/reproducibility-audit.md
  ```

No official Layer B result, seed, device, or result-producing command is asserted by
this correction. Those fields must come from an actual authorized run manifest.

## Version history

| Version | Date | Change | Original altered? |
|---|---|---|---|
| `phase16-manuscript-correction/1` | 2026-10-19 | Additive evidence-limited correction; retires historical overclaims and separates Layer A from Layer B | No |