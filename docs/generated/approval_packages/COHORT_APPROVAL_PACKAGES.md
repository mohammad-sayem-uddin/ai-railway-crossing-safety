# Three Cohort Approval Packages (`train_events`, `no_train_events`, `engine_events`)

In `execution_gate.py`, **COHORT_APPROVAL_MISSING** clears for each of the three required cohorts once verified, batch-integrity-checked, and RD-043-satisfied `APPROVED` Stage-2.1 (`8.1.0-stage2.1`) review records exist on disk and a signed promotion receipt (`phase12-stage21-promotion-receipt/2`) is emitted by `readiness_cli`.

| Cohort | Events in Cohort | Current Approved Stage-2.1 | Execution Gate Floor | Full Target | Status |
|---|---|---|---|---|---|
| `train_events` | 23 | 0 | >= 1 APPROVED | 23/23 approved + RD-043 second reviews where triggered | `PENDING_HUMAN_STAGE21_REVIEWS` |
| `no_train_events` | 3 | 0 | >= 1 APPROVED | 3/3 approved (note: verify acoustic road-horn vs locomotive independence cleanly) | `PENDING_HUMAN_STAGE21_REVIEWS` |
| `engine_events` | 1 | 0 | >= 1 APPROVED | 1/1 approved + RD-043 second review by second allowlisted reviewer if T3/T4 interpreted | `PENDING_HUMAN_STAGE21_REVIEWS` |

## Post-Review Promotion Receipt Command (Run Only After Human Stage-2.1 Reviews Complete)
```bash
PYTHONPATH=src .venv/bin/python -m railway_detection.annotation.readiness_cli --reviews-dir data/ground_truth/reviews --allowlist data/ground_truth/authorized_reviewers.json --inventory data/manifests/layer_b_v2_annotation_inventory.json --proposals-dir data/ground_truth/proposals --stage stage3_single_camera_baseline --repository-root . --receipt-path data/governance/stage21_promotion_receipt.json
```
