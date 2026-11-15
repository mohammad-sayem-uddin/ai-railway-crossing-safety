# Principal Investigator (PI) Human Approval & Hardware Validation Package

> **STRICT GOVERNANCE NOTICE:** No synthetic or backdated human approval artifacts were created autonomously. All human-gated authorization and ground-truth files remain absent until an authorized researcher explicitly creates and signs them using the exact sequence below.

**Active Repository Branch:** `exp/four-layer-completion`
**Authorized Reviewers (`data/ground_truth/authorized_reviewers.json`):** `raihankabirrahu@gmail.com`, `elaf85777@gmail.com`
**Current Automated Readiness Check:**
```bash
PYTHONPATH=src:. .venv/bin/python scripts/check_zero_blocker_readiness.py
PYTHONPATH=src:. .venv/bin/python -m railway_detection evaluation status
```

---

## Remaining Human & Hardware Gates (5 Logical Blockers + 1 Physical Gate)

1. **`AUTH-MEDIA-ACCESS.json`** (`data/governance/AUTH-MEDIA-ACCESS.json`, schema `phase5-media-access-authorization/2`) — gates raw video/audio inspection and Stage-2.1 interactive media review, as well as the single intentionally guarded unit test [`test_exploratory_subset_authorization_gate.py`](file:///Users/sayemuddin/Desktop/Train_automation/tests/unit/test_exploratory_subset_authorization_gate.py#L73).
2. **`STAGE21_RECORDS_MISSING`** (plus derived `COHORT_APPROVAL_MISSING`) — requires genuine `8.1.0-stage2.1` human review records under `data/ground_truth/reviews/**/*_review.json` across `train_events`, `no_train_events`, and `engine_events`, followed by a Stage-2.1 promotion receipt (`data/governance/stage21_promotion_receipt.json`).
3. **`EVENT_SPLIT_DECISION_MISSING`** — researcher-authored event-level split at `data/splits/phase12_event_split_decision.json` (`phase12-event-split-decision/1`) covering all 27 events defined in [`phase12_r04_scope_decision.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/manifests/phase12_r04_scope_decision.json).
4. **`MANIFEST_MISSING`** — hash-bound evaluation input manifest at `data/manifests/phase12_evaluation_inputs.json` built by [`build_evaluation_input_manifest`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/manifest_builder.py#L40).
5. **`EVAL_AUTH_NOT_GRANTED`** — final official evaluation authorization at `data/governance/eval_authorization.json` (`phase12-eval-authorization/1`) bound to live SHA-256 digests (`decision_policy_sha256`, `frozen_config_sha256`, `protocol_profile_sha256`, `r04_scope_decision_sha256`, plus `event_split_decision_sha256`, `input_manifest_sha256`, and `stage21_promotion_receipt_sha256`).
6. **Physical Raspberry Pi 4B / 5 Hardware Benchmarking (`physical_raspberry_pi_tested = false`)** — no ARM Linux SBC is attached locally (`/Volumes` contains only `Macintosh HD`); all Pi numbers remain `ANALYTICAL_PROJECTION_UNMEASURED_HARDWARE` until measured on device.

---

## Sequential PI Execution Runbook (Stages 1–6)

### Stage 1 — Grant Raw Media Access (`AUTH-MEDIA-ACCESS.json`)

> **TEMPLATE — HUMAN EXECUTION REQUIRED**

Issue `data/governance/AUTH-MEDIA-ACCESS.json` (`phase5-media-access-authorization/2`) before inspecting raw media or running `run_stage21_review.py` or `tests/unit/test_exploratory_subset_authorization_gate.py`:

```bash
PYTHONPATH=src:. .venv/bin/python -c "
from pathlib import Path
# Inspect exact required fields via railway_detection.safety.media_guard
import inspect, railway_detection.safety.media_guard as mg
print(inspect.getsource(mg))
"
```

Once `data/governance/AUTH-MEDIA-ACCESS.json` is recorded on disk, verify:

```bash
PYTHONPATH=src:. .venv/bin/pytest -q tests/unit/test_exploratory_subset_authorization_gate.py --import-mode=importlib
```

*(Note: to also run `scripts/run_exploratory_dual_camera_subset.py --execute --authorize-exploratory-run`, supply a separately versioned `--config` YAML with `authorized_for_execution: true` and a valid `authorization_record`.)*

---

### Stage 2 — Execute Genuine Stage-2.1 Human Annotation Reviews & Issue Promotion Receipt

`scripts/run_stage21_review.py` enforces reviewer allowlist membership and two-reviewer consensus. Run across the three required cohorts (`train_events`, `no_train_events`, `engine_events`) covering the 27 events in `data/manifests/phase12_r04_scope_decision.json`:

```bash
# Primary review (replace <COHORT> and <EVENT>, e.g. train_events event_001)
PYTHONPATH=src:. .venv/bin/python scripts/run_stage21_review.py \
  --reviewer raihankabirrahu@gmail.com \
  --cohort <COHORT> \
  --event <EVENT>

# Second independent review for dual-review events
PYTHONPATH=src:. .venv/bin/python scripts/run_stage21_review.py \
  --reviewer elaf85777@gmail.com \
  --cohort <COHORT> \
  --event <EVENT> \
  --second-of <PRIMARY_REVIEW_ID>
```

Once `STAGE21_RECORDS_MISSING` and `COHORT_APPROVAL_MISSING` clear, verify readiness and emit the hash-bound Stage-2.1 Promotion Receipt:

```bash
PYTHONPATH=src:. .venv/bin/python -m railway_detection.annotation.readiness_cli \
  --receipt-path data/governance/stage21_promotion_receipt.json
```

---

### Stage 3 — Author Event-Level Split Decision (`data/splits/phase12_event_split_decision.json`)

> **TEMPLATE — HUMAN EXECUTION REQUIRED (Scientific judgment by PI; do not auto-assign without PI approval)**

Author `data/splits/phase12_event_split_decision.json` partitioning all 27 event IDs present in [`phase12_r04_scope_decision.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/manifests/phase12_r04_scope_decision.json) (`engine_events/event_001`, `no_train_events/event_001..003`, `train_events/event_001..023`) into non-overlapping `train`, `val`, and `test` partitions:

```json
{
  "schema_version": "phase12-event-split-decision/1",
  "decision_status": "APPROVED",
  "decision_id": "PHASE12-EVENT-SPLIT-DECISION-YYYY-MM-DD",
  "decided_by": "raihankabirrahu@gmail.com",
  "decided_at_utc": "2026-XX-XXT00:00:00+00:00",
  "researcher_statement": "Approved disjoint event-grouped train/val/test partitions across all 27 Phase-12 events.",
  "partitions": {
    "train": ["<EVENT_IDS...>"],
    "val": ["<EVENT_IDS...>"],
    "test": ["<EVENT_IDS...>"]
  }
}
```

---

### Stage 4 — Build Hash-Bound Evaluation Input Manifest (`data/manifests/phase12_evaluation_inputs.json`)

After `phase12_event_split_decision.json` is recorded and all 27 inference-output JSON sources exist, call [`build_evaluation_input_manifest`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/manifest_builder.py#L40) to emit `data/manifests/phase12_evaluation_inputs.json` and re-check live bindings:

```bash
PYTHONPATH=src:. .venv/bin/python -m railway_detection evaluation status
```

Inspect `live_bindings` printed by `evaluation status`. Currently pre-verified bindings on disk are:
- `decision_policy_sha256`: `c87c1432f473f84def46d343429c21bcd5329adcbce6cfdf7933de446a0c8575`
- `frozen_config_sha256`: `999a7970d4c47713a1b128f77939916a54bc99c24becd68e383aad2f1db5a42e`
- `protocol_profile_sha256`: `6b5edb4852fc0d16a10ac1975f3f18d6feb28fe91638971da7d3761a7a6d42ca`
- `r04_scope_decision_sha256`: `f6eabebaab9a925628c119feb9638ba108b7e0c3fbcb942efdf890c2d6e5fc08`

The remaining three (`stage21_promotion_receipt_sha256`, `event_split_decision_sha256`, `input_manifest_sha256`) populate automatically once Stages 2–4 exist.

---

### Stage 5 — Issue Official Evaluation Authorization (`data/governance/eval_authorization.json`) & Run Official Evaluation

> **TEMPLATE — HUMAN EXECUTION REQUIRED**

Populate `data/governance/eval_authorization.json` (`phase12-eval-authorization/1`) with the 7 `live_bindings` hashes from Stage 4 and compute `record_sha256` using [`canonical_eval_auth_payload`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/governance.py#L404):

```json
{
  "schema_version": "phase12-eval-authorization/1",
  "authorization_id": "PHASE12-EVAL-AUTH-YYYY-MM-DD",
  "stage": "phase12_official_evaluation",
  "authorized_by": "raihankabirrahu@gmail.com",
  "authorized_at_utc": "2026-XX-XXT00:00:00+00:00",
  "authorization_statement": "Official held-out Phase-12 evaluation authorized strictly on verified inputs; field or physical gate actuation remains unauthorized.",
  "attestation": {
    "type": "RECORDED_RESEARCHER_STATEMENT",
    "signature": null
  },
  "recorded_by": "raihankabirrahu@gmail.com",
  "scope": {
    "operation": "phase12_official_evaluation",
    "stage": "phase12_official_evaluation",
    "field_or_physical_operations_authorized": false
  },
  "bindings": {
    "decision_policy_sha256": "c87c1432f473f84def46d343429c21bcd5329adcbce6cfdf7933de446a0c8575",
    "event_split_decision_sha256": "<FROM_EVALUATION_STATUS>",
    "frozen_config_sha256": "999a7970d4c47713a1b128f77939916a54bc99c24becd68e383aad2f1db5a42e",
    "input_manifest_sha256": "<FROM_EVALUATION_STATUS>",
    "protocol_profile_sha256": "6b5edb4852fc0d16a10ac1975f3f18d6feb28fe91638971da7d3761a7a6d42ca",
    "r04_scope_decision_sha256": "f6eabebaab9a925628c119feb9638ba108b7e0c3fbcb942efdf890c2d6e5fc08",
    "stage21_promotion_receipt_sha256": "<FROM_EVALUATION_STATUS>"
  },
  "record_sha256": "<SHA256_OF_CANONICAL_EVAL_AUTH_PAYLOAD>"
}
```

Then execute official evaluation:

```bash
PYTHONPATH=src:. .venv/bin/python -m railway_detection evaluation status
PYTHONPATH=src:. .venv/bin/python -m railway_detection evaluation run
```

---

### Stage 6 — On-Device Raspberry Pi 4B / 5 Hardware Validation

Copy the TorchScript/FP16 deployment bundles and execute [`scripts/rpi_edge_benchmark.py`](file:///Users/sayemuddin/Desktop/Train_automation/scripts/rpi_edge_benchmark.py) directly on an ARM64 Raspberry Pi running Raspberry Pi OS (Bookworm or later) with PyTorch installed:

```bash
PYTHONPATH=src:. python3 scripts/rpi_edge_benchmark.py \
  --export-dir models/edge_bundles_pi \
  --output results/exploratory_v2/optimization_and_stress/pi_measured_edge_benchmark.json \
  --threads 1,2,4 \
  --iters 20
```

Verify that the resulting JSON reports `"is_physical_raspberry_pi": true`, non-null `device_tree_model`, and measured CPU temperature/thermal notes before promoting any SBC latency claim from `ANALYTICAL_PROJECTION_UNMEASURED_HARDWARE` to measured edge performance.
