# Final Supervisor / PI Action Required — Train Gate Automation Research

**Audience:** Research Supervisor / Principal Investigator (`elaf85777@gmail.com` / `raihankabirrahu@gmail.com`)  
**Repository:** `/Users/sayemuddin/Desktop/Train_automation` (branch `exp/four-layer-completion`)  
**Current Automated Evaluation Readiness:** `ready: false` (`7` governance blockers; zero fabricated signatures or bypassed checks)

---

## Executive Summary (Plain-English Status)

All software engineering, causal discrete-event simulation corrections (`Convention B`), stratified corpus uncertainty diagnostics (`Exp S`), synthetic stress/ablation studies (`Exp K–R`), statistical sample-size recalculation, split-leakage forensic audits, test-suite repairs, and preflight approval templates (`12` unsigned schema-verified files under [`docs/generated/approval_packages/`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/approval_packages/PI_APPROVAL_EXECUTION_GUIDE.md)) have been completed and verified without touching raw video/audio under `data/raw/` or inventing human sign-off. Also inspect the concise research-owner summary in [`RESEARCH_OWNER_FINAL_ACTION_DASHBOARD.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/RESEARCH_OWNER_FINAL_ACTION_DASHBOARD.md).

### Separation of Responsibilities (Scientific Approval vs Technical Execution)

| Layer | Who Performs It | Examples |
|---|---|---|
| **Scientific & Ethical Approval** *(Human Only)* | Research Supervisor / PI (`elaf85777@gmail.com`, `raihankabirrahu@gmail.com`) | Authorizing raw video/audio access (`AUTH-MEDIA-ACCESS`), performing human frame-by-frame `Stage-2.1` video review & dual review, choosing **Option A** (descriptive 27-event study) vs **Option C** (multi-crossing collection), and signing `AUTH-DESCRIPTIVE-EVAL-EXEC` or `eval_authorization.json`. |
| **Technical Execution** *(Autonomous Software / CLI)* | Pipeline / Agent (after approval exists on disk) | Validating 12 approval templates (`prepare_pi_approval_package.py`), computing statistical power (`audit_event_splits.py`), emitting promotion receipt (`readiness_cli`), compiling clean manifests (`manifest_builder`), running fail-closed replay (`prepare_and_execute_official_evaluation.py`), and running Raspberry Pi edge benchmarks (`rpi_edge_benchmark.py`). |

Three classes of prerequisites **cannot legally or scientifically be performed by an autonomous software agent** and now await human researcher decisions or physical lab hardware:

1. **Human Ethical & Media Governance Approvals** (`AUTH-MEDIA-ACCESS`, 27-event human frame-by-frame `Stage-2.1` video review, and final evaluation sign-off).
2. **A Scientific Split / Additional-Data Decision** — **no `train/val/test` partition of the existing 27 events can ever be `leakage_safe = true`**, because all 27 events come from **one single crossing (`crossing_A`)** and only **two physical recording sessions** (`20` daytime train clips on `2026-09-14`; `3` night low-light trains + `3` `no_train` controls + `1` `engine` clip on `2026-10-04`).
3. **Physical Raspberry Pi Hardware Benchmarking** — all edge CPU/preprocess speedups reported so far were measured on the development host (Apple M1 Pro), **not** on physical Raspberry Pi 4B/5 silicon (`physical_raspberry_pi_tested = false`).

| Action # | Decision / Gate | Who Must Act | Blocking What? | Target File(s) |
|---|---|---|---|---|
| **1** | Raw Media Access Authorization (`AUTH-MEDIA-ACCESS`) | Allowlisted PI (`elaf85777@gmail.com` or `raihankabirrahu@gmail.com`) | All raw video/audio inspection, frame rotation re-extraction, `Stage-2.1` review | `data/governance/AUTH-MEDIA-ACCESS.json` |
| **2** | 27-Event Human Ground-Truth Review & Cohort Promotion (`Stage-2.1`) | Human reviewers (`elaf85777@gmail.com`, `raihankabirrahu@gmail.com`; dual review under RD-043) | Replacing quarantined `6.0.0` reviews; unblocking `train_events`, `no_train_events`, `engine_events` cohorts | `data/ground_truth/reviews/*_review.json` & `data/governance/stage21_promotion_receipt.json` |
| **3** | Scientific Study Framing & Split Decision (**Option A** vs **Option C** vs Diagnostic Single-Site Split) | Principal Investigator | Either keeping descriptive 27-event framing (`Option A`), collecting `>= 3` crossings (`Option C`), or explicitly authorizing a non-leakage-safe chronological split | Active `SPLIT-DECISION-OPTION-A-2026-11-09` OR new collection OR `data/splits/phase12_event_split_decision.json` |
| **4** | Official Replay Evidence & Evaluation Input Manifest | Authorized pipeline (post Action 1–3) + PI check | Producing clean post-Stage-2.1 `phase12-replay-evidence/1` inputs (without cached predictions or labels) | `data/manifests/phase12_evaluation_inputs.json` |
| **5** | Final Official Evaluation Authorization | Principal Investigator | Unlocking `python -m railway_detection evaluation run` (`official_phase12_ready = true`) | `data/governance/eval_authorization.json` |
| **6** | Physical Raspberry Pi 4B / 5 & Crossing Sensor Testing | Human engineer with physical Raspberry Pi / crossing hardware | Moving Section 6 / edge benchmarks from host proxy to measured ARM Linux hardware telemetry | External JSON report from `scripts/rpi_edge_benchmark.py` |

---

## Action 1 — Raw Media Access Authorization (`AUTH-MEDIA-ACCESS`)

1. **Who must approve:** An allowlisted researcher (`elaf85777@gmail.com` or `raihankabirrahu@gmail.com`).
2. **Why it is required (scientifically & ethically):** Repository safety policy (`media_guard.py`) enforces fail-closed authorization before any script or human-review CLI hashes, probes, extracts frames from, or replays raw field video/audio recordings under `data/raw/`. Field video of public Bangladeshi level crossings may capture bystanders, road vehicles, and uninvolved rail staff, and requires explicit researcher authorization for audit traceability.
3. **Exact evidence to review first:**
   - [Approval Index](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/approval_packages/PI_APPROVAL_EXECUTION_GUIDE.md)
   - [Unsigned Template (`AUTH_MEDIA_ACCESS.template.json`)](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/approval_packages/AUTH_MEDIA_ACCESS.template.json)
   - [Layer B Split & Metadata Provenance Audit](file:///Users/sayemuddin/Desktop/Train_automation/results/dataset_audit/layer_b_split_audit_and_collection_plan.json) (`corpus_counts` and `events`)
4. **Exact file to approve / produce:** `data/governance/AUTH-MEDIA-ACCESS.json` (matching schema `phase5-media-access-authorization/2`, `status: "APPROVED"`, non-expired `expires_at_utc`, valid `record_sha256`).
5. **Exact missing decision:** Signed researcher authorization statement and SHA-256 integrity hash authorizing `READ_RAW_MEDIA`, `HASH_RAW_MEDIA`, `MEDIA_PROBE`, `FRAME_EXTRACTION`, `AUDIO_EXTRACTION`, `FEATURE_EXTRACTION`, `INFERENCE`, and `REAL_REPLAY` on `layer_b` (`27` events).
6. **Exact copy-paste commands to run:**
   ```bash
   # Step 1A: Copy template to governance destination (edit all __HUMAN_APPROVAL_REQUIRED__ fields first)
   cp docs/generated/approval_packages/AUTH_MEDIA_ACCESS.template.json data/governance/AUTH-MEDIA-ACCESS.json

   # Step 1B: After filling in authorized_by, timestamps, statement, and authorization_id, compute record_sha256
   PYTHONPATH=src:. .venv/bin/python -c "
   import json
   from pathlib import Path
   from railway_detection.safety import media_guard
   p = Path('data/governance/AUTH-MEDIA-ACCESS.json')
   rec = json.loads(p.read_text(encoding='utf-8'))
   rec['record_sha256'] = media_guard._canonical_sha256(rec)
   p.write_text(json.dumps(rec, indent=2) + '\n', encoding='utf-8')
   print('Wrote AUTH-MEDIA-ACCESS with record_sha256:', rec['record_sha256'])
   "

   # Step 1C: Verify authorization is recognized by readiness checker
   PYTHONPATH=src:. .venv/bin/python -m railway_detection evaluation status
   ```
7. **Consequence of rejecting or delaying:** Zero raw media operations can execute (`AUTH-MEDIA-ACCESS.json absent`). Neither `Stage-2.1` human video review, upright frame re-extraction (fixing the `pre-db40305` EXIF/DisplayMatrix `180°/90°` inversion bug), audio/vision model retraining on Layer B, nor official Phase 12 replay evaluation can proceed. Only synthetic/governance/cached exploratory analyses remain valid.

---

## Action 2 — Complete `Stage-2.1` Human Review Across All 27 Events & Cohort Promotion

1. **Who must approve:** Authorized human reviewers `elaf85777@gmail.com` and/or `raihankabirrahu@gmail.com`. Under rule `RD-043`, a **second independent allowlisted reviewer** is mandatory for `engine_events/event_001` whenever `T3` or `T4` is interpreted, and for any of the `27` events marked `UNCERTAIN`, explicitly flagged, or failing timing integrity (`< 30.0 s` review duration or batch bursts).
2. **Why it is required (scientifically & ethically):** All `27` previous `6.0.0` reviews were quarantined because they bypassed minimum timing / integrity safeguards and predated `Stage-2.1` dual-review rules. Additionally, our provenance audit found **`7` inaccurate AI-proposal metadata records**: `batch_multimodal_annotator` hardcoded `session_20260914_morning` on all `7` October 4 Session 2 events and mis-labeled night low-light trains `train_events/021..023` (`22..24(night_video_lowlight).MOV`) as `lighting: "day"`. Human reviewers must independently inspect raw `camera_front.mov` / `camera_back.mov` videos without trusting AI proposals to establish defensible `T0–T4` timestamps and correct metadata.
3. **Exact evidence to review first:**
   - [27-Event Stage-2.1 Checklist (Markdown)](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/approval_packages/STAGE21_27_EVENT_REVIEW_CHECKLIST.md) ([JSON](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/approval_packages/STAGE21_27_EVENT_REVIEW_CHECKLIST.json))
   - [Three Cohort Approval Packages (Markdown)](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/approval_packages/COHORT_APPROVAL_PACKAGES.md) ([JSON](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/approval_packages/COHORT_APPROVAL_PACKAGES.json))
   - [Dataset & Ground Truth Audit](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/DATASET_AND_GROUND_TRUTH_AUDIT.md)
4. **Exact files to approve / produce:**
   - Verified `8.1.0-stage2.1` human review JSON records under `data/ground_truth/reviews/` (`>= 1` APPROVED per cohort required by the technical gate; **`27/27`** events recommended for full study completeness).
   - Cohort promotion receipt: `data/governance/stage21_promotion_receipt.json` (`phase12-stage21-promotion-receipt/2`).
5. **Exact missing decision:** Verified human timestamps (`T0`, `T1`, `T2`, `T3`, `T4` or `NOT_OBSERVABLE`/`UNCERTAIN`), acoustic horn independence vs road horns (`no_train_events/001..003`), Session 2 lighting/session correction, and `APPROVED` status for `train_events` (`23`), `no_train_events` (`3`), and `engine_events` (`1`).
6. **Exact copy-paste commands to run (after Action 1 is complete):**
   ```bash
   # Example human review commands (full 27-command table is in STAGE21_27_EVENT_REVIEW_CHECKLIST.md):
   PYTHONPATH=src:. .venv/bin/python scripts/run_stage21_review.py --reviewer raihankabirrahu@gmail.com --cohort engine_events --event event_001
   # If T3/T4 is interpreted on engine_events/event_001 or UNCERTAIN/flagged anywhere, run second reviewer:
   PYTHONPATH=src:. .venv/bin/python scripts/run_stage21_review.py --reviewer elaf85777@gmail.com --cohort engine_events --event event_001

   PYTHONPATH=src:. .venv/bin/python scripts/run_stage21_review.py --reviewer raihankabirrahu@gmail.com --cohort no_train_events --event event_001
   PYTHONPATH=src:. .venv/bin/python scripts/run_stage21_review.py --reviewer raihankabirrahu@gmail.com --cohort train_events --event event_001
   # ... repeat through train_events/event_023 per STAGE21_27_EVENT_REVIEW_CHECKLIST.md ...

   # After reviews complete, emit the Stage-2.1 cohort promotion receipt:
   PYTHONPATH=src:. .venv/bin/python -m railway_detection.annotation.readiness_cli \
     --reviews-dir data/ground_truth/reviews \
     --allowlist data/ground_truth/authorized_reviewers.json \
     --inventory data/manifests/layer_b_v2_annotation_inventory.json \
     --proposals-dir data/ground_truth/proposals \
     --stage stage3_single_camera_baseline \
     --repository-root . \
     --receipt-path data/governance/stage21_promotion_receipt.json
   ```
7. **Consequence of rejecting or delaying:** Clears `0` real-data cohorts (`STAGE21_RECORDS_MISSING` and `COHORT_APPROVAL_MISSING` remain active). Every quantitative Layer B timing or horn result stays restricted to **`EXPLORATORY / AI-ADOPTED PROPOSALS`** with zero verified human ground truth.

---

## Action 3 — Scientific Decision on Dataset Splitting vs Multi-Crossing Collection

1. **Who must decide:** Principal Investigator (`elaf85777@gmail.com` or `raihankabirrahu@gmail.com`).
2. **Why it is required (scientifically):**
   - Our Mission 4 metadata reconstruction ([`layer_b_split_audit_and_collection_plan.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/dataset_audit/layer_b_split_audit_and_collection_plan.json)) **proved that NO `train/val/test` partition of the existing 27 events can ever be `leakage_safe = true`**, because:
     1. **One crossing only:** All `27/27` events occur at `crossing_A` (`0` held-out crossings exist).
     2. **Two sessions only:** Only `session_20260914` (`20` daytime train clips) and `session_20261004` (`3` night low-light trains + `3` `no_train` + `1` `engine`) exist — mathematically fewer than `3` non-empty split roles.
     3. **Class–session–hardware confounding:** `100%` of `no_train` and `engine` controls occur only in `session_20261004` at night (with `iPad 10th gen` back camera), whereas `20/23` trains occur in daytime `session_20260914` (`iPhone 15 Pro Max` back camera).
     4. **Why prior `16/6/5` (`CANDIDATE_EVENT_SPLIT_PROPOSAL.json`) was rejected:** Besides overlapping `crossing_A` and both sessions, it left **`val` with `0` `no_train` controls**, **`test` with `0` R04 `dual_camera` synced events**, and **split adjacent tied pair `train_events/event_007` and `008`** (shared back `creationdate` `16:12:34`) across `train` vs `val`.
     5. **What the improved chronological alternative (`chrono_temporal_block_15_5_7`, `15/5/7`) achieves:** It keeps `007`/`008` together, places `1` `no_train` and `>= 1` `dual_camera` event in every split (`9/1/1`), and holds out late chronological events — **yet STILL remains `leakage_safe = false`**!
3. **Exact evidence to review first:**
   - [Split Reconciliation (`SPLIT_OPTION_A_RECONCILIATION.md`)](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/approval_packages/SPLIT_OPTION_A_RECONCILIATION.md)
   - [Prior Researcher Decision (`SPLIT_DECISION_OPTION_A_20261109.md`)](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/research_decisions/SPLIT_DECISION_OPTION_A_20261109.md)
   - [Dataset Split Audit & Targeted Collection Plan JSON](file:///Users/sayemuddin/Desktop/Train_automation/results/dataset_audit/layer_b_split_audit_and_collection_plan.json)
   - [Diagnostic Chronological Candidate (`phase12_event_split_decision.candidate.template.json`)](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/approval_packages/phase12_event_split_decision.candidate.template.json)
4. **Exact file / decision fork (choose ONE of two primary scientific strategies — or explicit single-site diagnostic split):**
   - **Recommended Strategy A (For Existing 27 Events) — Keep `Option A` (`SPLIT-DECISION-OPTION-A-2026-11-09`, Descriptive Single-Crossing Study, NO Train/Val/Test Split):** Treat all `27` events (post Action 1 + Action 2 Stage-2.1 review) as a descriptive safety benchmark on `crossing_A` with exact Wilson / Clopper-Pearson 95% confidence intervals and explicit single-site scope disclosure (`AUTH-DESCRIPTIVE-EVAL-EXEC`, unsigned template ready at [`AUTH_DESCRIPTIVE_EVAL_EXEC.template.json`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/approval_packages/AUTH_DESCRIPTIVE_EVAL_EXEC.template.json)), rather than forcing a leaky split through Phase 12.
   - **Recommended Strategy C (For Generalization & Model Retraining) — Collect New Multi-Crossing Data Before Phase 12:** Wait before running held-out Phase 12 evaluation until new balanced multi-site field capture is complete. **Statistical Power Recalculation (`layer_b_split_audit_and_collection_plan.json`):** A minimal `3`-crossing / `6`-session floor (~`12` held-out test trains, `~6` test `no_train` controls) leaves `0/12` premature openings with a **`22.09%`** one-sided 95% Clopper-Pearson upper risk bound (`39.30%` on `0/6` false closures) and single-crossing test fragility. To bound premature opening and false-closure risk **`<= 10%`** (at 95% confidence, assuming intra-session `ICC = 0.05`, `m = 10` passages/session, `DEFF = 1.45`), collect **`>= 29` unclustered (`>= 43` cluster-adjusted)** synced test full-train passages and **`>= 29` (`>= 43` cluster-adjusted)** `no_train` road-horn controls across **`>= 5` crossings (`>= 11` sessions, `>= 220` total events across `train` / `val` / `test` cohorts, `>= 8` engine passages in `test`)** (`>= 59` unclustered / `>= 86` cluster-adjusted test trains for a `<= 5%` bound), with matched cameras/mics per site, `2×2` Day/Night × Clear/Rain balance, NTP+clapper sync (`100%`), physical island occupancy logger, and pre-calibrated upstream siting (replacing the currently unvalidated `84–211 m` kinematic estimate).
   - **Diagnostic Option Only (Not Recommended for Publication) — Single-Site Chronological Held-Out Split:** Sign [`phase12_event_split_decision.candidate.template.json`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/approval_packages/phase12_event_split_decision.candidate.template.json) to `data/splits/phase12_event_split_decision.json`, explicitly accepting `leakage_safe = false`, `cross_crossing_leakage_safe = false`, and `cross_session_leakage_safe = false`.
5. **Exact missing decision:** Explicit PI confirmation choosing Option A (Descriptive study via `AUTH-DESCRIPTIVE-EVAL-EXEC.json` on the existing 27 events), Option C (Collect `>= 5`-crossing dataset before held-out Phase 12), or the explicit non-leakage-safe chronological diagnostic split.
6. **Exact copy-paste commands to run:**
   ```bash
   # Audit split math, Option A stratified uncertainty & Option C sample-size targets (no raw media accessed):
   PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. .venv/bin/python scripts/audit_event_splits.py

   # IF ELECTING OPTION A (Descriptive 27-event cache-only study after Action 1 + Action 2 promotion receipt):
   cp docs/generated/approval_packages/AUTH_DESCRIPTIVE_EVAL_EXEC.template.json data/governance/AUTH-DESCRIPTIVE-EVAL-EXEC.json
   # Fill __HUMAN_APPROVAL_REQUIRED__ fields (status="APPROVED", authorized_by, timestamps, statement,
   # promotion_receipt_sha256, evaluation_manifest_sha256), then compute record_sha256:
   PYTHONPATH=src:. .venv/bin/python -c "
   import json
   from pathlib import Path
   from railway_detection.evaluation import governance
   p = Path('data/governance/AUTH-DESCRIPTIVE-EVAL-EXEC.json')
   rec = json.loads(p.read_text(encoding='utf-8'))
   rec['record_sha256'] = governance.canonical_record_sha256(rec)
   p.write_text(json.dumps(rec, indent=2) + '\n', encoding='utf-8')
   print('Wrote AUTH-DESCRIPTIVE-EVAL-EXEC with record_sha256:', rec['record_sha256'])
   "

   # ONLY IF EXPLICITLY ELECTING DIAGNOSTIC SINGLE-SITE CHRONOLOGICAL SPLIT:
   cp docs/generated/approval_packages/phase12_event_split_decision.candidate.template.json data/splits/phase12_event_split_decision.json
   # Then edit __HUMAN_APPROVAL_REQUIRED__ fields (decision_status="APPROVED", decided_by, decided_at_utc, statement).
   ```
7. **Consequence of rejecting or delaying:** Keeping `data/splits/phase12_event_split_decision.json` absent preserves `EVENT_SPLIT_DECISION_MISSING` in the Phase 12 held-out gate (`evaluation status` stays `ready: false`). This is **scientifically correct** unless the PI deliberately collects `>= 3` crossings or elects a strictly single-site chronological diagnostic run.

---

## Action 4 — Build Clean Official Evaluation Input Manifest (`phase12-evaluation-inputs/1`)

*(Applies only if proceeding to official Phase 12 evaluation after Actions 1, 2, and a split decision.)*

1. **Who must approve:** Authorized researcher running post-Stage-2.1 replay generation + PI review of manifest hashes.
2. **Why it is required (scientifically):** `manifest_builder.build_evaluation_input_manifest` verifies that every event in `phase12_evaluation_inputs.json` comes from a genuine, post-`AUTH-MEDIA-ACCESS`, upright-frame-corrected `phase12-replay-evidence/1` inference stream with `annotation_labels_used: false`. It strictly refuses cached exploratory predictions (`Mission 39`) or synthetic fixtures.
3. **Exact evidence to review first:**
   - [Manifest Runbook (`EVALUATION_INPUT_MANIFEST_RUNBOOK.md`)](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/approval_packages/EVALUATION_INPUT_MANIFEST_RUNBOOK.md)
   - [Corrected Manifest Schema (`phase12_evaluation_inputs.template.json`)](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/approval_packages/phase12_evaluation_inputs.template.json)
4. **Exact file to produce:** `data/manifests/phase12_evaluation_inputs.json` (generated from `data/manifests/phase12_replay_evidence/*.json`).
5. **Exact missing decision:** Confirm inference checkpoints + upright frame extraction post-`AUTH-MEDIA-ACCESS`, then generate clean `phase12-replay-evidence/1` records and compile `phase12_evaluation_inputs.json`.
6. **Exact copy-paste commands to run (post Actions 1–3):**
   ```bash
   # After generating data/manifests/phase12_replay_evidence/*.json via upright LayerBEventProcessor inference:
   PYTHONPATH=src:. .venv/bin/python -c "
   from pathlib import Path
   from railway_detection.evaluation.manifest_builder import build_evaluation_input_manifest
   sources = sorted(Path('data/manifests/phase12_replay_evidence').glob('*.json'))
   build_evaluation_input_manifest(
       repository_root=Path('.'),
       event_sources=sources,
       output_path=Path('data/manifests/phase12_evaluation_inputs.json'),
   )
   "
   PYTHONPATH=src:. .venv/bin/python -m railway_detection evaluation status
   ```
7. **Consequence of rejecting or delaying:** `MANIFEST_MISSING` stays active; official `evaluation run` cannot locate authorized replay inputs.

---

## Action 5 — Final Evaluation Authorization & Fail-Closed Official Execution

1. **Who must approve:** Principal Investigator (`elaf85777@gmail.com` or `raihankabirrahu@gmail.com`).
2. **Why it is required (scientifically):** Binds exact cryptographic SHA-256 hashes of the frozen config, decision policy, protocol profile, R04 sync scope decision, Stage-2.1 promotion receipt, split decision, and replay input manifest so no metric can ever be recomputed silently on altered inputs or unapproved checkpoints.
3. **Exact evidence to review first:**
   - [Eval Auth Template (`eval_authorization.template.json`)](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/approval_packages/eval_authorization.template.json)
   - [PI Execution Guide (`PI_APPROVAL_EXECUTION_GUIDE.md`)](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/approval_packages/PI_APPROVAL_EXECUTION_GUIDE.md)
   - Output of `PYTHONPATH=src:. .venv/bin/python -m railway_detection evaluation status` (confirming ONLY `EVAL_AUTH_NOT_GRANTED` remains before signing).
4. **Exact file to approve / produce:** `data/governance/eval_authorization.json` (`phase12-eval-authorization/1`, matching all live bindings and `record_sha256`).
5. **Exact missing decision:** Signed PI statement authorizing official evaluation on the bound hashes, and choice of a new empty `--output-dir` outside `data/`, `configs/`, `results/`, `docs/`, `models/`, `experiments/`, `src/`, `tests/`.
6. **Exact copy-paste commands to run:**
   ```bash
   # PI Step 5A: Populate live_bindings into data/governance/eval_authorization.json and compute record_sha256
   cp docs/generated/approval_packages/eval_authorization.template.json data/governance/eval_authorization.json
   # (Fill authorized_by, authorized_at_utc, authorization_statement, recorded_by.identity, authorization_id first)
   PYTHONPATH=src:. .venv/bin/python -c "
   import json
   from pathlib import Path
   from railway_detection.evaluation import governance
   readiness = governance.assess_official_phase12_readiness(Path('.'))
   p = Path('data/governance/eval_authorization.json')
   rec = json.loads(p.read_text(encoding='utf-8'))
   rec['bindings'].update({k: v for k, v in readiness.live_bindings.items() if k in rec['bindings']})
   rec['record_sha256'] = governance.canonical_record_sha256(rec)
   p.write_text(json.dumps(rec, indent=2) + '\n', encoding='utf-8')
   print('Bound eval_authorization with live bindings; sha256:', rec['record_sha256'])
   "

   # Verify ALL 7 blockers are cleared (expected: exit 0, ready: true):
   PYTHONPATH=src:. .venv/bin/python -m railway_detection evaluation status

   # Post-Approval Automated Agent / Supervisor Execution Command:
   PYTHONPATH=src:. .venv/bin/python scripts/prepare_and_execute_official_evaluation.py \
     --mode execute-after-approval \
     --output-dir /tmp/tga_official_phase12_eval_out
   ```
7. **Consequence of rejecting or delaying:** Official evaluation remains blocked (`EVAL_AUTH_NOT_GRANTED`, exit code `3`). `scripts/prepare_and_execute_official_evaluation.py --mode execute-after-approval` strictly refuses execution and prints the remaining governance blocker JSON.

---

## Action 6 — Physical Raspberry Pi 4B / 5 & Crossing Hardware Validation

1. **Who must act:** Project engineer / researcher with physical access to a Raspberry Pi 4B / 5 (ARM64 Linux) and field camera/audio/barrier hardware.
2. **Why it is required (scientifically):** Currently `physical_raspberry_pi_tested = false` and `/proc/device-tree/model` is absent because all edge timing measurements (`Exp M`, `Exp P` — `74.91%` TorchScript stripping, `2.32×` `416 px` OpenCV preprocessing speedup, `0.0391 ms/tick` FSM, `96.6%–98.6%` duty-cycle frame reduction) were executed on an **Apple M1 Pro host (`arm64 macOS`)**. Analytical scaling formulas cannot measure ARM Cortex-A72/A76 NEON memory bandwidth, thermal throttling under tropical outdoor temperatures, USB/RTSP camera capture latency, or relay GPIO actuation delay.
3. **Exact evidence to review first:**
   - [Standalone Edge Benchmark CLI (`scripts/rpi_edge_benchmark.py`)](file:///Users/sayemuddin/Desktop/Train_automation/scripts/rpi_edge_benchmark.py)
   - [IEEE Manuscript (`docs/generated/IEEE_MANUSCRIPT_TRAIN_GATE_AUTOMATION.md`)](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/IEEE_MANUSCRIPT_TRAIN_GATE_AUTOMATION.md) Section 6 & Table IV
4. **Exact file to produce:** External JSON telemetry report generated directly on Raspberry Pi Linux ARM64 (e.g., `/tmp/rpi_hardware_benchmark.json`, `physical_raspberry_pi_tested: true`).
5. **Exact missing hardware measurements:**
   - Real Raspberry Pi 4B / 5 multi-thread CPU latency (`ms/frame`, ms per acoustic window, peak `VmHWM` RSS MB, thermal throttling over sustained `>= 30 min` runs).
   - Live RTSP/USB camera + I2S/USB microphone capture overhead and relay-driver hardware actuation latency (`<= T2` margin verification).
6. **Exact copy-paste command to run on the Raspberry Pi (after cloning repo + installing `.venv`):**
   ```bash
   PYTHONPATH=src:. .venv/bin/python scripts/rpi_edge_benchmark.py \
     --output /tmp/rpi_hardware_benchmark.json \
     --export-dir /tmp/rpi_export_bundle \
     --iters 20
   ```
7. **Consequence of rejecting or delaying:** Section 6 and Table IV edge deployment claims remain strictly scoped as **host-measured Apple M1 Pro proxy / analytical projection (`physical_raspberry_pi_tested = false`)** — acceptable for **Option A** architecture/feasibility reporting when honestly disclosed, but **blocking** for real-world hardware deployment claims (`Option B` / field pilot).
