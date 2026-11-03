# Evaluation Readiness Blocker Report

- Status: **NOT_READY**
- Stage: `stage3_single_camera_baseline`
- Blockers: **1**
- Mechanical checks do not constitute researcher approval; a human researcher signature remains required.

## Blockers
| Code | Event/cohort | Detail |
|---|---|---|
| `NO_RECORDS` | `—` | zero in-scope records supplied |

## Inputs
- active_proposal_count: `27`
- allowlist: `data/ground_truth/authorized_reviewers.json`
- inventory: `data/manifests/layer_b_v2_annotation_inventory.json`
- inventory_event_count: `27`
- proposals_dir: `data/ground_truth/proposals`
- reviews_dir: `data/ground_truth/reviews`

## Evidence
- 27 legacy record(s) excluded: each has a verified invalidation notice (never promoted, never ground truth)

## Contract
- Exit code `0`: READY; exit code `2`: NOT_READY; exit code `1`: evaluation error.
- This report is read-only with respect to review records, proposals, allowlists, and media.
