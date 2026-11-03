# Phase 16 — Reproducibility and Environment Record

**Record version:** `phase16-environment/1`  
**Date:** 2026-10-19  
**Scope:** read-only audit, dependency diagnosis, and manuscript correction support

## Reproducibility audit

The repository already contains a machine-readable, read-only audit at
`src/railway_detection/reproducibility/audit.py` and the CLI wrapper
`scripts/audit_reproducibility.py`. The focused regression suite covers claim scanning,
evidence-tag resolution, result provenance, fingerprints, and write-path protection.

Run it from the repository root (outputs are deliberately outside repository evidence
trees):

```text
venv/bin/python scripts/audit_reproducibility.py \
  --root . --json /tmp/reproducibility-audit.json \
  --md /tmp/reproducibility-audit.md
```

The run on 2026-10-19 reported:

| Item | Status | Interpretation |
|---|---|---|
| Dataset manifests | PASS | Required manifests exist and are hashed. |
| Frozen config/checkpoint fingerprints | PASS | Config-pinned Vision and Audio V3 artifacts match. |
| Dependency lock (canonical `venv`) | PASS | All 50 lock entries agree with the canonical environment. |
| `ultralytics` import (canonical `venv`) | PASS | Resolves to a package with `__init__.py`; no repair was needed. |
| Approved ground truth / event split / R04 scope | UNRESOLVED | No decision or eligible Stage-2.1 ground truth is invented. |
| Official evaluation provenance | NOT_AVAILABLE | No official Layer B result exists. |
| Active draft and correction claim audit | PASS | No unsupported statements found in the current draft/correction. |
| Historical DOCX claim audit | FAIL (archival) | Nine historical overclaim/unsupported-number findings remain attached to the byte-preserved original; they are explicitly separate from the active manuscript result. |

The corrected manuscript is `docs/PHASE16_MANUSCRIPT_CORRECTION_v1.md`; it is
additive and does not overwrite the historical DOCX. The reproducibility audit scans the
current draft/correction as its active claim gate and emits a separate `historical_claim_findings`
ledger for the old DOCX, so preserving history does not make a corrected active manuscript
permanently fail while the historical findings remain discoverable.

## Audit scope correction — 2026-10-19

The original audit's default manuscript list included the immutable historical DOCX as though
it were still the current manuscript, despite the separately versioned evidence-limited
correction. The audit now distinguishes active manuscript claims from archived-source findings;
the nine historical findings remain available in JSON/Markdown and the DOCX remains byte-for-byte
unchanged. Regression tests also cover negated historical disclaimers (including “did not”).

## Dependency diagnosis

Two Python 3.11 environments are present:

| Environment | Finding | Action |
|---|---|---|
| `venv` | Python 3.11.15; `pip check` clean; 50/50 lock entries agree; core imports including `ultralytics` pass | Use as canonical validation environment. |
| `.venv` | `pip check` clean, but 15 lock entries differ or are absent (including `ast-serialize`, `mypy`, `typing_extensions`, and several transitive versions) | Do not use for reproducibility; no in-place repair was attempted. |

The drift is dependency reproducibility drift, not a broken package graph in either
environment. Reinstalling or upgrading packages would change the working environment
and could affect unrelated phases, so the smallest safe repair is documentation and
canonical-environment selection rather than mutation. No prohibited Audio V2 checkpoint
was loaded, inspected for inference, or used in validation.

## Historical report handling

`Railway_Crossing_Automation_Research_Report.docx` and its copy under `results/` are
historical artifacts. They remain unchanged. The correction is versioned separately so
that a reviewer can compare the overclaiming historical text with the evidence-limited
replacement. The existing report-generation script is not run because it writes over
historical output paths.

## Reproduction boundary

The available metrics are Layer A still-image metrics only. A future authorized result
must record the exact command, seed, device, input manifest hash, config/policy hashes,
checkpoint hashes, and protocol decisions in a run manifest. Until that exists, no
event-level performance, latency, clearance, field, deployment, or safety claim is
reproducible from this repository.