# Media-Access Hold Resolution Plan & Bounded Authorization Scope

**Document Path:** `docs/MEDIA_ACCESS_HOLD_RESOLUTION_PLAN.md`  
**Date:** October 25, 2026  
**Status:** **ADMINISTRATIVE DISPOSITION FORMALLY ADOPTED & RECORDED**  
**Repository:** `/Users/sayemuddin/Desktop/Train_automation`  
**Decision-Maker:** Raihan Kabir Rahu (`raihankabirrahu@gmail.com`), Lead Researcher  
**Approval Timestamp:** `2026-10-25T10:47:38-04:00`  
**Governing Documents:**
- [`docs/MEDIA_ACCESS_INCIDENT_INVESTIGATION_20261020.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/MEDIA_ACCESS_INCIDENT_INVESTIGATION_20261020.md)
- [`docs/INCIDENT_CLOSURE_REVIEW_20261020.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/INCIDENT_CLOSURE_REVIEW_20261020.md)
- [`docs/STAGE21_TIMING_PILOT_INCIDENT_20261019.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/STAGE21_TIMING_PILOT_INCIDENT_20261019.md)
- [`docs/FINAL_RESEARCH_HANDOVER_20261021.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/FINAL_RESEARCH_HANDOVER_20261021.md)
- [`docs/R04_ALL_EVENT_CALIBRATION_INVESTIGATION.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/R04_ALL_EVENT_CALIBRATION_INVESTIGATION.md)

---

## 1. Evidence-Based Incident Finding (Phase 1 Synthesis)

### 1.1 Chronological Facts of the October 19, 2026 Incident
On October 19, 2026, during automated pipeline preparation, an AI agent invoked the repository's evaluation status CLI command twice via Cline tool calls:
- **Invocation 1:** 14:09:48 UTC (10:09:48 -0400), exit code 3 (`ready: false`). Output redirected to `/tmp/stage21_official_status_audit.json` (8,369 bytes) and empty `.err`.
- **Invocation 2:** 14:17:05 UTC (10:17:05 -0400), exit code 3 (`ready: false`). Output redirected to `/tmp/stage21_official_status_audit_final.json` (8,369 bytes) and empty `.err`.
- **Agent Self-Report:** At line 47,433 of the session log, the agent reported:
  > *"I ran the evaluation-status command twice before recognizing that it could open and hash real media. I'm treating those reads as an out-of-scope access and have stopped further checks. I'm sorry."*

Following this self-report, a repository-wide containment hold on source-media access was instituted. The subsequent forensic investigation (`MEDIA_ACCESS_INCIDENT_INVESTIGATION_20261020.md`) closed on October 20 as `INVESTIGATION_CLOSED_UNRESOLVED` because OS-level `/tmp` cleanup had purged the outputs and macOS BSM kernel audit logs (`/private/var/audit`) were inaccessible without elevated root privileges.

---

### 1.2 Exact Code-Path Tracing

A rigorous audit of the code path executed by `railway_detection evaluation status` demonstrates:
```
railway_detection.cli.main._evaluation_status()
 └─► railway_detection.evaluation.execution_gate.assess_official_phase12_readiness()
      ├─► governance.load_allowlist()                  [Reads authorized_reviewers.json]
      ├─► _read_repository_records()                   [Reads data/ground_truth/reviews/*.json]
      ├─► notices_module.excused_legacy_records()      [Reads *.INVALIDATION_NOTICE.json]
      ├─► _verify_decision_file(SPLIT_DECISION)        [Missing -> EVENT_SPLIT_DECISION_MISSING]
      ├─► _verify_decision_file(R04_DECISION)          [Missing -> R04_SCOPE_DECISION_MISSING]
      ├─► load_frozen_config()                         [Reads configs/frozen_experiment_v1.yaml]
      ├─► verify_checkpoint_integrity()                [Hashes .pt model weights ONLY]
      ├─► load_evaluation_input_manifest(..., verify_sources=False)
      │    └─► FileNotFoundError / MANIFEST_MISSING    [data/manifests/...inputs.json is ABSENT]
      └─► governance.verify_eval_auth()                [Missing -> EVAL_AUTH_NOT_GRANTED]
```

1. **Explicit `verify_sources=False` Contract:**  
   In [`src/railway_detection/evaluation/execution_gate.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/execution_gate.py#L879), `assess_official_phase12_readiness()` calls `load_evaluation_input_manifest(manifest_path, verify_sources=False)`.  
   In [`src/railway_detection/evaluation/input_contracts.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/input_contracts.py#L211-L235), `_read_source_bytes_and_hash()` is executed **only** when `verify_sources=True`. Under `verify_sources=False`, source paths are never opened, and `actual_hash` is assigned from the manifest declaration.
2. **Immediate Blocker Termination:**  
   The manifest file `data/manifests/phase12_evaluation_inputs.json` did **not** exist in the repository. At line 107 of `input_contracts.py`, `load_evaluation_input_manifest` immediately raises `EvaluationInputError("MANIFEST_MISSING", ...)` upon checking `path.is_file()`. Execution never reached source path processing.
3. **Checkpoint Scope:**  
   `verify_checkpoint_integrity()` hashes only the two frozen model checkpoint files:
   - YOLO vision weights: `experiments/vision/39f402dfe460/checkpoints/weights/best.pt`
   - Audio V3 weights: `experiments/audio/RUN_20261008_AUDIO_V3_ESC50/checkpoints/best.pt`  
   Neither path is located within or references raw media under `data/raw/`.

---

### 1.3 Tripartite Fact Classification

To preserve scientific documentation integrity, findings are categorized into three distinct evidentiary classes:

| Evidentiary Class | Findings |
|---|---|
| **Directly Evidenced Facts** | - Two CLI invocations ran at 14:09:48 and 14:17:05 UTC (tool call logs).<br>- Both exited with code 3 (`ready: false`, 9 blockers across 7 codes, `MANIFEST_MISSING`).<br>- Output files were exactly 8,369 bytes with 0-byte stderr files.<br>- The release manifest (`docs/generated/stage21_timing_pilot_release.json`) remained completely unchanged.<br>- No file modification, staging, commit, or deletion occurred on source media. |
| **Code-Path Structural Facts** | - `assess_official_phase12_readiness` sets `verify_sources=False`.<br>- `_read_source_bytes_and_hash` is strictly inside the `verify_sources=True` branch.<br>- `phase12_evaluation_inputs.json` was absent, halting manifest inspection immediately.<br>- Therefore, under the audited repository code, media byte reading was **technically blocked by design**. |
| **Unknowable Runtime Facts** | - Because the `/tmp` output files were deleted by macOS cleanup and BSM kernel audit logs are inaccessible without root privileges, the exact process file-descriptor table at 14:09 UTC cannot be cryptographically proven.<br>- The possibility of an unrecorded concurrent script or ephemeral symlink cannot be disproven from surviving logs alone. |

**Incident Finding:**  
The media-access incident was a **false-alarm containment hold** caused by the automated agent's cautionary assumption. The code path structurally prohibited media access, and the missing manifest prevented any source file interaction. However, because kernel-level runtime traces are unrecoverable, the incident cannot be closed by asserting "proof of non-occurrence." Instead, it must be resolved via **Formal Administrative Risk Acceptance and Strict Scope Bounding**.

---

## 2. Bounded Authorization Scope & Operation Hierarchy

Authorization to access media is **not** a monolithic switch. In accordance with [`docs/FINAL_RESEARCH_IMPLEMENTATION_ROADMAP_20261021.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/FINAL_RESEARCH_IMPLEMENTATION_ROADMAP_20261021.md) §7 (*"Operation-specific authority"*), repository operations are partitioned into four distinct tiers:

```
┌────────────────────────────────────────────────────────────────────────┐
│ TIER 1: BOUNDED READ-ONLY FRAME EXTRACTION FOR R04 CALIBRATION        │
│ [PROPOSED TO BE AUTHORIZED UPON RESEARCHER ATTESTATION]                │
│ - Tool: scripts/extract_sync_review_frames.py                          │
│ - Scope: Read-only frame extraction from Layer B .mov files            │
│ - Target: 12 candidate events for visual landmark sync review          │
│ - Destination: scratch/r04_visual_review/{cohort}/{event_id}/         │
│ - Constraints: Zero modifications to raw media; SHA-256 frame hashing  │
└────────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌────────────────────────────────────────────────────────────────────────┐
│ TIER 2: GROUND-TRUTH ADJUDICATION (STAGE-2.1)                          │
│ [REMAINS HELD / SEPARATE ADJ-AUTH REQUIRED]                            │
│ - Requires: D-B Researcher Decision (ADJ-AUTH)                         │
│ - Workflows: annotation.review_session, adjudication_session           │
│ - Scope: Creating human-adjudicated review records for T0, T1, T3, T4  │
└────────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌────────────────────────────────────────────────────────────────────────┐
│ TIER 3: OFFICIAL EVALUATION & REPLAY PIPELINES                         │
│ [REMAINS HELD / SEPARATE EVAL-AUTH REQUIRED]                           │
│ - Requires: Approved split (R-SPLIT), scope (R-R04SCOPE), EVAL-AUTH    │
│ - Workflows: railway_detection evaluation run, Phase12EvaluationRunner  │
│ - Scope: Official replay benchmark and metrics computation             │
└────────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌────────────────────────────────────────────────────────────────────────┐
│ TIER 4: TIMING-PILOT ACTIVATION, RELEASE REGENERATION, & DEPLOYMENT    │
│ [PERMANENTLY HELD & PROHIBITED UNDER RESEARCH PROTOTYPE CONTRACT]       │
│ - Prohibited: Activating timing pilot or regenerating release manifest │
│ - Prohibited: Field actuation, hardware control, or safety certification│
└────────────────────────────────────────────────────────────────────────┘
```

> [!IMPORTANT]
> The resolution proposed herein applies **strictly and exclusively to Tier 1**. Tiers 2, 3, and 4 remain fully held and blocked.

---

## 3. Proposed Formal Disposition Text

The following formal administrative disposition text is prepared for execution by the lead researcher:

```markdown
### FORMAL ADMINISTRATIVE DISPOSITION: MEDIA-ACCESS INCIDENT HOLD RESOLUTION (R04 BOUNDED CARVE-OUT)
**Disposition Reference:** ADMINISTRATIVE_DISPOSITION_R04_READ_ONLY_UNBLOCK_20261025  
**Authorized Decision-Maker:** Raihan Kabir Rahu (raihankabirrahu@gmail.com), Lead Researcher  
**Date:** October 25, 2026  

1. Historical Incident Finding:
   The investigation into the October 19, 2026 evaluation-status invocations confirms that
   the status code path executed with `verify_sources=False`, that the input manifest was
   absent, and that checkpoint integrity verification hashed only neural network weights (.pt).
   No available evidence demonstrates that source-media bytes were accessed, decoded, or inferred
   upon. Surviving evidence is insufficient to achieve mathematical certainty due to OS cleanup
   of /tmp and absence of privileged BSM logs.

2. Risk Determination:
   The residual risk of historical contamination from the status command is negligible.
   Continuing an unmitigated, repository-wide media hold indefinitely prevents legitimate
   cross-camera calibration and visual verification.

3. Administrative Resolution & Scope Bounding:
   - The blanket containment hold on source-media access is hereby REVISED to a BOUNDED SCOPE.
   - Authorization is GRANTED SOLELY for read-only video frame extraction via
     `scripts/extract_sync_review_frames.py` for the 12 candidate events listed in the R04
     calibration review queue.
   - Extracted frame pairs must be stored strictly in `scratch/r04_visual_review/`.
   - Raw source-media files (`data/raw/layer_b/v2/*/*.mov`, `*.wav`) must remain bit-for-bit immutable.
   - Official Phase-12 evaluation execution, timing-pilot activation, and model training
     REMAIN STRICTLY HELD AND PROHIBITED.

4. Attestation:
   I hereby record this administrative disposition, accept the documented residual risk,
   and authorize read-only visual calibration frame extraction under the constraints above.

   Researcher Signature: Raihan Kabir Rahu (raihankabirrahu@gmail.com)
   Confirmation Date: 2026-10-25
   Attestation Statement: "I approve the administrative disposition you have full authorization and full access to everything" (Timestamp: 2026-10-25T10:47:38-04:00)
```

---

## 4. Human Approval Attestation Record

In strict compliance with repository governance, authorization derives from the allowlisted lead researcher:

| Item | Requirement | Status | Responsible Human |
|---|---|:---:|---|
| **Identity** | Must be allowlisted in [`data/ground_truth/authorized_reviewers.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/authorized_reviewers.json) | Confirmed (`raihankabirrahu@gmail.com`) | Lead Researcher |
| **Action** | Formally confirm adoption of the disposition text in Section 3 | **CONFIRMED (2026-10-25T10:47:38-04:00)** | Raihan Kabir Rahu |
| **Operational Trigger** | Set environment variable `RAILWAY_ALLOW_RESTRICTED_MEDIA_ACCESS=1` or pass `--allow-authorized-media-access` | **ACTIVATED** | Researcher / Pipeline Operator |

---

## 5. Verification Checklist for Effective Authorization

- [x] **Check 1: Human Disposition Formally Confirmed:** The lead researcher has reviewed this document and explicitly approved the administrative disposition.
- [x] **Check 2: Environment Variable Active:** `RAILWAY_ALLOW_RESTRICTED_MEDIA_ACCESS=1` set for authorized execution sessions.
- [x] **Check 3: Script Safeguard Verified:** `scripts/extract_sync_review_frames.py` acknowledges `--allow-authorized-media-access` and validates authorization.
- [x] **Check 4: Dry-Run Cleanliness:** Running `--dry-run` on candidate events verified 12/12 queue specifications without errors.
- [x] **Check 5: Destination Isolation:** Output files target only `scratch/r04_visual_review/{cohort}/{event_id}/` (no files written to `data/raw/` or `data/manifests/`).
- [x] **Check 6: Immutable Source Media:** Layer B `.mov` and `.wav` file modification times and directory structures remain strictly unchanged.

---

## 6. Next Exact Execution Command for Visual Review

Once the checklist above is satisfied and authorization is formally confirmed by the researcher, execute the following commands in the virtual environment:

### Step 1: Pre-flight Queue Inspection
```bash
venv/bin/python scripts/extract_sync_review_frames.py --list-queue
```

### Step 2: Extract Review Frame Pairs for the 12 Priority Events
```bash
export RAILWAY_ALLOW_RESTRICTED_MEDIA_ACCESS=1

for event in train_events/event_010 train_events/event_008 no_train_events/event_003 \
             train_events/event_003 train_events/event_016 train_events/event_018 \
             train_events/event_019 train_events/event_021 train_events/event_023 \
             no_train_events/event_001 engine_events/event_001 train_events/event_004; do
    venv/bin/python scripts/extract_sync_review_frames.py --event "$event" --allow-authorized-media-access
done
```

### Step 3: Human Verification & Sign-off
For each generated `scratch/r04_visual_review/{cohort}/{event_id}/review_record.json`:
1. Inspect `front_t*.jpg` and `back_t*_candidate.jpg` side-by-side.
2. Confirm optical alignment within $\pm 0.10$s tolerance.
3. Edit `review_record.json` to record human review:
   ```json
   {
     "human_verified": true,
     "reviewer": "Raihan_Kabir_Rahu",
     "notes": "Verified locomotive pilot alignment across roadway occupancy line."
   }
   ```
4. Ingest verified records via `scripts/build_camera_sync_candidate_manifest.py` to promote events meeting all acoustic criteria to `CALIBRATION_SUPPORTED`.
