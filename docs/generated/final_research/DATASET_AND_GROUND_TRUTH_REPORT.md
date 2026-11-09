# Dataset and Ground-Truth Report

## The dataset

- **27 events** from a single site (`crossing_A`), daytime only:
  23 train events, 3 no-train events, 1 engine-only event (always reported
  separately; never pooled, never counted twice via its two cameras).
- **54 camera sources** (front + back per event), digests verified; two
  historical duplicate sources were excluded upstream and stay excluded.
- Both cameras are lateral trackside units ~5–6 m apart (Decision D-002);
  no site survey exists. Back-camera offsets are validated
  (CALIBRATION_SUPPORTED) for 11 of 27 events; those 11 are the only events
  supporting shared-timeline dual-camera claims.

## Ground truth: what exists and what it is

Ground truth for this programme is **researcher-adopted AI-assisted
reference annotations** — not canonical ground truth, and never described
as such in this package.

- Adoption record: `docs/generated/professor_evidence/mission43/RESEARCHER_ANNOTATION_ADOPTION.json`
  (2026-11-08), preserving the researcher's verbatim statement and the
  per-file SHA-256 of all 27 adopted active proposals
  (`data/ground_truth/proposals/…`; train events mostly v2, event_001 v6,
  event_005 v4; no-train v2; engine event v3, schema 8.0.0).
- The adoption's own recorded limitations: it is genuine evidence of
  researcher approval of the AI-assisted content; it is **not** independent
  human observation, creates no missing annotation products, and does not
  effect canonical promotion. The researcher's manual annotations were
  never separately stored, so no inter-rater or verification statistics
  exist.

## Completeness (adopted references)

| Product | Coverage |
|---|---|
| Event labels | 27/27 |
| Horn presence status | 24/27 (13 present, 11 absent_observed, 3 null — nulls stay null) |
| Horn onsets | 13 |
| Horn offsets | 0 |
| Bounding boxes | 0 |
| Audio window labels | 0 |
| Independently stored human observations | 0 |
| Stage-2.1 review records (schema 8.1.0, APPROVED, second-reviewed) | 0 |

Consequences: event-level analyses are legitimate under the adopted-reference
scope; detection-level and window-level metrics are structurally
uncomputable; canonical (Stage-2.1) evaluation is impossible until the
human review work package (Blocker B §4 of the staging analysis; summarized
in the professor handoff) is performed. The legacy Phase 11 inventory
(`docs/PHASE11_EVENT_INVENTORY.csv`, marked INVALID_FABRICATED_APPROVAL) is
not evidence and is cited nowhere in this package.

## Mission 3 replay assembly (2026-11-09)

For decision replay, Mission 3 assembled `data/manifests/m3_multimodal_replay_manifest.json`
(SHA-256 `3c720167ea06b67141beb7cf33bd02ce325db62a3e100819f8aa4ad213d5bbbb`)
from the Mission 43 B2 evaluation manifest (SHA-256 `2fb08c92…46b72`):
all 27 events carry front-vision, front-audio and back-vision cache paths;
every front/audio file was re-hashed and matched the Mission 43 recorded
value (0 mismatches); back predictions resolve to the Mission 43 copies
for 22 events and the Mission 39 originals for the 5 pilot events.
Coverage: `results/m3_mm_assembly/coverage_report.csv`.
