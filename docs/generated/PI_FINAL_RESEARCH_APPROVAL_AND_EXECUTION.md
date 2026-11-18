# Principal Investigator Final Research Approval & Execution Handoff

**Repository:** `/Users/sayemuddin/Desktop/Train_automation` | **Branch:** `exp/four-layer-completion`  
**Audience:** Principal Investigator / Authorized Reviewers (`elaf85777@gmail.com`, `raihankabirrahu@gmail.com`)  
**Current Automated Readiness:** **`official_phase12_ready = false` (`7` blockers)** | **`option_a_descriptive_ready = false`** | **`physical_raspberry_pi_tested = false`**

> **Hard Scientific Boundary:** No human approvals have been fabricated and no raw video/audio under `data/raw/` has been accessed. Never approve any `train/val/test` partition of the existing `27` single-crossing events as `leakage_safe = true` — doing so cannot turn single-crossing, session-confounded recordings into an independent generalization test.

---

## 1. Decisions the PI Must Make (vs Automated Technical Tasks)

| Decision / Action | Owner | What Must Be Decided or Signed |
|---|---|---|
| **D1. Research Scope** | **PI (Human)** | Elect **Option A** (complete 27-event single-crossing descriptive cohort study on existing data) as the immediate milestone, **Option C** (collect `235` balanced multi-crossing events before official Phase 12 evaluation), or **Both Sequentially** (publish Option A descriptively now -> collect Option C for generalization). |
| **D2. Raw Media Ethics** | **PI (Human)** | Authorize human inspection, upright rotation re-extraction, and `Stage-2.1` review on `data/raw/layer_b/` (`AUTH-MEDIA-ACCESS`). |
| **D3. Ground Truth (`Stage-2.1`)** | **Human Reviewers** | Perform independent frame-by-frame review across all `27` events (`+ RD-043` second reviewer where triggered), fixing the `7` AI-proposal Session-2/lighting bugs and separating road horns from locomotive horns. |
| **D4. Execution Sign-Off** | **PI (Human)** | Sign `AUTH-DESCRIPTIVE-EVAL-EXEC.json` (Option A) and/or `phase12_event_split_decision.json` + `eval_authorization.json` (Option C / Phase 12) once bound SHA-256 hashes match. |
| **T1–T4. CLI Execution** | **Software / Agent** | After D2–D4 exist on disk: emit promotion receipt (`readiness_cli`), build manifest (`manifest_builder`), run `prepare_and_execute_official_evaluation.py`, and run `rpi_edge_benchmark.py` on Pi hardware. |

---

## 2. Scientific Evidence Supporting These Decisions

### A. Why Existing 27 Events Cannot Yield a Leakage-Free 3-Way Split
Per [`layer_b_split_audit_and_collection_plan.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/dataset_audit/layer_b_split_audit_and_collection_plan.json) (`v1.2`), all `27` events come from one site (`crossing_A`) across only `2` sessions: **Session 1 (`2026-09-14` daytime, `20` trains, `iPhone 15 Pro Max` back)** and **Session 2 (`2026-10-04` dusk/night, `3` `night_video_lowlight` trains + `3` `no_train` + `1` `engine`, `iPad 10th gen` back)**. Pooled `10/23` (`43.48%`, Wilson CI `[0.2563, 0.6319]`) approach closures hide stark session heterogeneity (`7/20 = 35.0%` `[0.1812, 0.5671]` Session 1 daytime vs `3/3 = 100%` `[0.4385, 1.0000]` Session 2 night lowlight with `85.21%` of side-proxy frames and `76.67%` of `back_rear_dets`, `0/3` in `sync11`).

### B. Why `0/11` `sync11` Clips Completed Autonomous Reopening (Not Automated Success)
Holding closed indefinitely is a **fail-closed safety hold (`FAULT_FAIL_SAFE` / `TRAIN_DEPARTING`), NOT completed autonomous automation**. Forensic inspection across [`real_sync11_v3_traces.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/replays/real_sync11_v3_traces.json), [`exp_d_back_departure.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/exploratory_v2/experiments/exp_d_back_departure.json), and all `27` cached `camera_2` streams establishes four root causes:
1. **`sync11` trace breakdown:** `4` L1 closures (`001, 006, 007, 013`), `5` clip-EOF `RULE_4_FAIL_SAFE_CLAMP` closures (`005, 009, 011, 014, 017`), `2` never closed (`002, 012` `IDLE`), **`0/11` completed reopenings** (one-sided 95% Clopper-Pearson premature-opening upper bound `23.84%`).
2. **`0/11` `rear` boxes & `<= 43.2 s` dropouts on `sync11`:** Unrotated `-90°` `.mov` `camera_2` caches in `sync11` emitted `0/11` `rear` detections and up to `43.20 s` blind gaps (`event_017`), holding `RULE_L4_BACK_SPARSE_DROPOUT_HOLD`.
3. **Mid-passage & pre-`T4` `rear` boxes on unsynced clips:** Naive `>= 2` `rear`-frame opening (`M2`) fires prematurely `-39.0 s` before `T4 = 61.2 s` on `event_008` (`21.6–22.2 s`) and `0.4–4.3 s` before `T4` on dense Session 2 upright clips `021–023` (`4/22` premature). Requiring dense monotonic transit + cessation of all body/rear boxes + `1.5 s` silence (`M3`) reaches **`0/22` premature openings**.
4. **Clip truncation + `0/27` physical occupancy sensors:** Post-`T4` clip duration has median `1.402 s` (`20/22` clips `< 3.5 s` required for `1.5 s` dwell + `2.0 s` gate opening), and **`0/27` events have physical island occupancy sensors** (`OccupancyState.UNKNOWN` locks `REAR_CONFIRMED` closed). Full autonomous reopening requires **`M5` (`V3_CONSERVATIVE_POSITIVE` + `M3` transit/silence + independent `OccupancyState.CLEAR` + `>= 15 s` post-`T4` tail)** — verified `reopened=True, premature=False` in `SYNTHETIC_ONLY` simulation when `occ_sensor=CLEAR` and `post_t4 >= 3.5 s`, and safely `CLOSED` (`reopened=False`) whenever occupancy is absent or post-`T4` footage is truncated.

---

## 3. Exact Approval Artifacts & Post-Approval Execution Commands

**Pre-Verified Live Hashes (`12/12` valid unsigned templates under `docs/generated/approval_packages/`):**
- `decision_policy_sha256`: `c87c1432f473f84def46d343429c21bcd5329adcbce6cfdf7933de446a0c8575`
- `frozen_config_sha256`: `999a7970d4c47713a1b128f77939916a54bc99c24becd68e383aad2f1db5a42e`
- `protocol_profile_sha256`: `6b5edb4852fc0d16a10ac1975f3f18d6feb28fe91638971da7d3761a7a6d42ca`
- `r04_scope_decision_sha256`: `f6eabebaab9a925628c119feb9638ba108b7e0c3fbcb942efdf890c2d6e5fc08`
- `metric_scope_sha256` (Option A): `1e10c02db10336cb8f436f5c791b20b2f58301cfd3d517e1ddf6a2d713562c36`
- `evaluation_manifest_sha256` (`B2_EVALUATION_INPUT_MANIFEST.json`): `2fb08c92e6d389e55e3963c0f47f0d7fa7959922f39b9b4b600f244a57a46b72`

### Option A Execution Sequence (Immediate Existing-Data Milestone)
1. **Approve `AUTH-MEDIA-ACCESS`:** Copy [`AUTH_MEDIA_ACCESS.template.json`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/approval_packages/AUTH_MEDIA_ACCESS.template.json) -> `data/governance/AUTH-MEDIA-ACCESS.json`, fill `__HUMAN_APPROVAL_REQUIRED__` fields, and stamp `record_sha256 = media_guard._canonical_sha256(rec)`.
2. **Complete All `27` Human `Stage-2.1` Reviews:** Follow [`STAGE21_27_EVENT_REVIEW_CHECKLIST.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/approval_packages/STAGE21_27_EVENT_REVIEW_CHECKLIST.md) (`scripts/run_stage21_review.py`, `>= 30 s` inspection per event; mandatory `RD-043` second reviewer for `engine_events/event_001` if `T3/T4` interpreted or on any `UNCERTAIN`/flagged event), correcting Session 2 date/night metadata (`7` events) and checking road-horn vs locomotive independence.
3. **Emit Cohort Promotion Receipt (`data/governance/stage21_promotion_receipt.json`):** Run `readiness_cli` (exact command in [`COHORT_APPROVAL_PACKAGES.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/approval_packages/COHORT_APPROVAL_PACKAGES.md)). *(Optionally re-extract upright `camera_1/camera_2` caches post-`AUTH-MEDIA-ACCESS` to replace `pre-db40305` predictions.)*
4. **Approve Option A Execution (`data/governance/AUTH-DESCRIPTIVE-EVAL-EXEC.json`):** Copy [`AUTH_DESCRIPTIVE_EVAL_EXEC.template.json`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/approval_packages/AUTH_DESCRIPTIVE_EVAL_EXEC.template.json), fill signer/timestamps/statement & `promotion_receipt_sha256`, compute `record_sha256 = governance.canonical_record_sha256(rec)`.
5. **Run Fail-Closed Option A Evaluation:**
   ```bash
   PYTHONPATH=src:. .venv/bin/python scripts/prepare_and_execute_official_evaluation.py \
     --mode execute-option-a-descriptive \
     --output-dir /tmp/tga_option_a_descriptive_out \
     --condition B2
   ```

### Option C / Phase 12 Sequence (Only After New Multi-Crossing Collection)
After Stage-2.1 review on new Option C data (`data/splits/phase12_event_split_decision.json` signed), build clean `phase12-replay-evidence/1` inputs (`manifest_builder`), bind dynamic hashes into `data/governance/eval_authorization.json` from [`eval_authorization.template.json`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/approval_packages/eval_authorization.template.json), verify `evaluation status` (`ready: true`), and run:
```bash
PYTHONPATH=src:. .venv/bin/python scripts/prepare_and_execute_official_evaluation.py \
  --mode execute-after-approval \
  --output-dir /tmp/tga_official_phase12_out
```

---

## 4. Reconciled Option C Sample Sizes & Field Collection Checklist

A `3`-crossing/`6`-session floor (`~12` test trains, `~6` test `no_train`) yields a `22.09%` premature-opening / `39.30%` false-closure 95% upper bound and only `1.87%` McNemar power (`p_10 = 0.20`). Using exact Clopper-Pearson bounds, unconditional exact two-sided McNemar power, and cluster design effect `DEFF = 1 + (m - 1) * rho`:

| Study Tier | Train Cohort (`2` sites, `5` sess) | Val Cohort (`1` site, `3` sess) | Test Cohort (`2` unseen sites) | Grand Total (`5` sites) | Test Statistical Guarantee (`m<=10`, `rho=0.05`) |
|---|---|---|---|---|---|
| **C1: Unclustered** (`rho=0.0`) | `60` train, `30` nt, `8` eng = `98` | `24` train, `15` nt, `4` eng = `43` | `29` train, `29` nt, `8` eng = `66` (`5` sess) | **`207`** (`13` sess) | `9.81%` 95% UB (if unclustered); `49.2%` McNemar (`p_10=0.20`) |
| **C2: Primary Recommended** (`rho=0.05`) | `60` train, `30` nt, `8` eng = **`98`** | `24` train, `15` nt, `4` eng = **`43`** | `43` train, `43` nt, `8` eng = **`94`** (`5` sess) | **`235`** (`13` sess) | `DEFF_actual=1.38` (`N_eff=31.16 >= 29`), **`9.17%` <= 10% UB**, `98.8%` power for `4/11` |
| **C3: High Power McNemar** (`rho=0.05`) | `60` train, `30` nt, `8` eng = `98` | `24` train, `15` nt, `4` eng = `43` | `62` train, `60` nt, `8` eng = `130` (`6` sess) | **`271`** (`14` sess) | `N_eff=42.27 >= 42`, `6.84%` UB, **`81.6%` power at `p_10=0.20, p_01=0.005`** |

**Field Research Assistant Operational Checklist:**
- [ ] **Site Selection:** Select `5` visually/acoustically distinct Bangladeshi crossings (`train`: 2, `val`: 1, `test`: 2). Never place the same site in more than one split role.
- [ ] **Balanced Sessions (`2×2` Strata):** Capture Day-Clear, Day-Rain/Fog, Night-Clear, Night-Rain/Fog with **`no_train` controls (`>= 60 s`) recorded inside the same session using identical camera & mic hardware** as `train` clips.
- [ ] **Distance & Calibration Pilot:** Before bulk capture, record calibration clips at `40 m, 80 m, 120 m, 160 m, 210 m` verifying upright mounting and `>= 24–32 px` vertical locomotive height at `416px` (`84–211 m` is unvalidated until site focal-length verification).
- [ ] **Sync & Timing Windows:** Enable NTP/GPS time sync, clap an audible+visual slate at session start & end (`< 100 ms` residual offset across `100%` of events), start recording **`>= 10 s` before `T0`** (no left-censoring), and continue **`>= 15 s` after `T4` complete rail-island exit** (needed to test full `3.5 s` reopening).
- [ ] **Physical Occupancy Reference:** Record synchronized overhead/island occupancy camera or radar/inductive logger alongside approach, side-box, and exit cameras so `OccupancyState` ground truth exists for `100%` of events.
- [ ] **Manifests & Partition Lock:** Assign unique `crossing_<X>_sess_<YYYYMMDD>_<cohort>_<###>` IDs, log container SHA-256 + QuickTime/EXIF rotation tags, annotate all events under `Stage-2.1` + `RD-043`, freeze models/thresholds on `val` ONLY, and evaluate `test` once.

---

## 5. What Is Blocked & Six-Tier Publication Claim Boundaries

| Evidence Tier | Current Status Today | Legitimately Supported Claims Today | Forbidden Claims Until Unlocked |
|---|---|---|---|
| **1. Tested Software Properties** | **VERIFIED (`11/11` checks, `3,889` pytest)** | Fail-closed FSM transition legality, causal non-backfill alignment, zero-overlap Vision/Audio split synthesis, governance refusal logic. | Real-world field accuracy or barrier certification. |
| **2. Synthetic Simulations** | **VERIFIED (`Exp L, Q, R` wakeup)** | Zero unsafe openings across `100` `Exp Q` stress runs; `M5` nominal reopening when `occ_sensor=CLEAR` & `post_t4 >= 3.5 s`. | Proof of rain/fog detection accuracy on real trains. |
| **3. Cached Exploratory Results** | **EXPLORATORY (`pre-db40305`, `0` reviews)** | Session 1 (`7/20`) vs Session 2 (`3/3`) disparity; `0/11` `sync11` EOF fail-closed holds; `Exp O/R` road-horn runs & `Recall` drop (`0.9231->0.6154`, Brier Δ CI crossing `0`). | Verified human ground-truth performance or reliable real-clip automatic reopening. |
| **4. Human-Verified Descriptive (Opt A)** | **BLOCKED (`0` Stage-2.1 reviews)** | Pipeline prepared; ready once PI completes Section 3 Option A sequence. | Published Option A results prior to review completion. |
| **5. Independent Held-Out Eval (Opt C)** | **BLOCKED (`ready=false`, `1` crossing)** | Quantified `235`-event (`271` high-power) multi-crossing protocol ready. | Any cross-crossing or held-out generalization claim. |
| **6. Physical Hardware Results** | **BLOCKED (`Pi_tested=false`)** | Apple M1 CPU kernel benchmarks & unmeasured analytical Pi 4B/5 scaling (`host_edge_scaling_benchmark.json`). | Real Raspberry Pi latency/thermal SLA or live relay operation (`RASPBERRY_PI_DEPLOYMENT_RUNBOOK.md` §§8–9 mandatory first; never wire to live railway signals). |
