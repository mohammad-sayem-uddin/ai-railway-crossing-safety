# Research Owner Final Action Dashboard — Train Gate Automation

**Branch:** `exp/four-layer-completion`  
**Concise PI Decision Brief:** [`PI_FINAL_RESEARCH_APPROVAL_AND_EXECUTION.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/PI_FINAL_RESEARCH_APPROVAL_AND_EXECUTION.md)  
**Owner Handoff Companion:** [`FINAL_PI_ACTION_REQUIRED.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/FINAL_PI_ACTION_REQUIRED.md) (detailed copy-paste guide for supervisor/PI)  
**Audit & Strategy Engine:** [`layer_b_split_audit_and_collection_plan.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/dataset_audit/layer_b_split_audit_and_collection_plan.json) (`schema: layer-b-event-split-audit/1.2`)

---

## 1. COMPLETED

- **System & Safety Software (`11/11` technical-readiness checks passing):**
  - `V3 Four-Layer Causal FSM` (`decision_engine_v3_four_layer.py`, `rules_v3_four_layer.py`, `occupancy.py`) with non-backfill causal collector (`allow_stale_detection_backfill=False`), orthogonal container rotation normalization (`video.py`), natural log-Mel parity (`audio/features.py`), and opt-in `RULE_L3_OPTICAL_DEGRADED_AUDIO_WAKEUP` (`False` by default).
  - Causal `Convention B` simulation specification & fail-closed governance gates (`media_guard.py`, `governance.py`, `descriptive_exec_gate.py`, `official_handoff.py`).
  - Access guard fix (`_Guard._safe_is_dir` `ENAMETOOLONG` remediation), `9/9` `UNKNOWN` test forensic audit (`133/133` pass, [`UNKNOWN_TESTS_FORENSIC_AUDIT.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/UNKNOWN_TESTS_FORENSIC_AUDIT.md)), `181`-file access registry (`145` safe files).
- **Forensic Leakage Audits & Clean Retraining Splits:**
  - Exposed and repaired Vision V1 leakage (`87.1%` aug + `93.1%` session leakage -> `vision_v1_session_grouped`, `0/29` session crossings) and Audio V3 leakage (`32.56%` YouTube stem overlap -> `audio_v3_stem_grouped`, `0/57` stem crossings).
  - Proved mathematically why the `27` single-crossing (`crossing_A`), `2`-session Layer-B events cannot yield a `leakage_safe = true` 3-way split, documented `7/27` AI-proposal Session-2/lighting bugs, and published **Option A stratified uncertainty diagnostics (`Exp S`)** + **Option C statistical sample-size recalculation**.
- **Unsigned Human-Approval Templates (`12` verified files):**
  - All `12` schemas verified against live code and hashes under `docs/generated/approval_packages/` (covering both **Option A** [`AUTH_DESCRIPTIVE_EVAL_EXEC.template.json`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/approval_packages/AUTH_DESCRIPTIVE_EVAL_EXEC.template.json) and **Option C / Phase 12** [`eval_authorization.template.json`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/approval_packages/eval_authorization.template.json)), zero fabricated approvals, and `FILE_HASH_MANIFEST.sha256` (`23/23 OK`).

---

## 2. APPROVAL REQUIRED

*(Every item below requires human PI / authorized reviewer action (`elaf85777@gmail.com` or `raihankabirrahu@gmail.com`) — software cannot execute these legitimately.)*

| Gate / File Target | Who Approves | Decision Needed | Unlocks |
|---|---|---|---|
| `data/governance/AUTH-MEDIA-ACCESS.json` | PI / Allowlisted Reviewer | Ethical/research authorization for `layer_b` (`27` events) raw video/audio inspection | Upright frame re-extraction & human `Stage-2.1` review |
| `data/ground_truth/reviews/*_review.json` + `data/governance/stage21_promotion_receipt.json` | Human Reviewers (+ `RD-043` second reviewer) | Independent `8.1.0-stage2.1` timestamps (`T0–T4`), road vs train horn attribution, Session 2 lighting fix | Clears `STAGE21_RECORDS_MISSING` & `COHORT_APPROVAL_MISSING` (`3` cohorts) |
| **Research Strategy Choice** | Principal Investigator | **Choose:** **Option A** (keep `SPLIT-DECISION-OPTION-A-2026-11-09` descriptive 27-event study, leave Phase 12 split absent) **OR** **Option C** (hold Phase 12 until new multi-crossing dataset collected) **OR** diagnostic single-site split (`leakage_safe=false`) | Scientific scope & publication framing |
| `data/governance/AUTH-DESCRIPTIVE-EVAL-EXEC.json` *(Option A path)* | Principal Investigator | Sign `AUTH_DESCRIPTIVE_EVAL_EXEC.template.json` bound to `stage21_promotion_receipt` & manifest hash | Authorized **Option A** 27-event descriptive cohort run |
| `data/splits/phase12_event_split_decision.json` + `data/manifests/phase12_evaluation_inputs.json` + `data/governance/eval_authorization.json` *(Option C / Phase 12 path)* | Principal Investigator | Approve event split (`OPTION C` data recommended), compile post-Stage-2.1 `phase12-replay-evidence/1` manifest, sign `EVAL-AUTH` | Official Phase 12 `evaluation run` (`ready: true`) |

---

## 3. DATA REQUIRED

- **To Complete Option A (Descriptive Benchmark on Existing Capture):**
  - `0` new recordings required; human `Stage-2.1` ground-truth review across the `27` existing events (correcting the `7` Session-2 / `night_video_lowlight` AI proposal metadata defects) + upright `.mov` re-extraction post-`AUTH-MEDIA-ACCESS`.
- **To Achieve Option C (Leakage-Free Cross-Crossing Validation & Retraining):**
  - Why `3` crossings / `6` sessions is **only a structural floor**: yields ~`12` held-out test trains & ~`6` test `no_train` controls, leaving `0/12` premature openings with a **`22.09%`** one-sided 95% upper risk bound (`39.30%` on `0/6` false closures).
  - **Statistical Power Target (for `<= 10%` upper risk bound at 95% confidence, assuming intra-session `ICC = 0.05`, `m <= 10`, `DEFF = 1 + (m-1)*rho`, Tier `C2` primary recommendation):**
    - **`>= 5` disjoint crossings**, **`13` balanced sessions** (`Day-Clear`, `Day-Rain/Fog`, `Night-Clear`, `Night-Rain/Fog`), **`235` total events (`98 + 43 + 94`, `207` unclustered tier `C1`, or `271` across `14` sessions tier `C3` for `81.6%` unconditional McNemar power at `p_10=0.20`)**:
      - `train` (`2` crossings, `5` sessions): `60` train, `30` `no_train` (`>= 60 s`), `8` `engine` = `98`.
      - `val` (`1` disjoint crossing, `3` sessions): `24` train, `15` `no_train`, `4` `engine` = `43` (locked threshold/calibration tuning only).
      - `test` (`2` unseen crossings, `5` sessions): **`29` unclustered / `43` cluster-adjusted** (`actual DEFF = 1.38`, `N_eff = 31.16 >= 29`, effective 95% upper bound `9.17% <= 10%`; `62` across `6` test sessions in `C3`) synced full-train passages, **`29` / `43` cluster-adjusted** (`60` in `C3`) `no_train` road-horn controls, **`8`** uncensored `engine` passages = `94` (`130` in `C3`).
    - Mandatory controls (`>= 10 s` pre-`T0`, **`>= 15 s` post-`T4` tail** to test `3.5 s` `M5` reopening, locked camera/mic hardware per crossing with no iPhone/iPad cohort swap, `100%` NTP + clapper sync `< 100 ms`, physical island occupancy ground truth, and pre-collection distance/pixel-height `>= 24–32 px` @ `416px` calibration).

---

## 4. HARDWARE REQUIRED

1. **Physical Raspberry Pi 4B / 5 (`aarch64` Linux) Verification (`physical_raspberry_pi_tested = false`):**
   - Run `scripts/rpi_edge_benchmark.py --iters 20 --export-dir /tmp/edge_bundles --output /tmp/rpi_hardware_benchmark.json` directly on target ARM SBC hardware, plus Sections 8–9 of [`RASPBERRY_PI_DEPLOYMENT_RUNBOOK.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/RASPBERRY_PI_DEPLOYMENT_RUNBOOK.md): live camera/audio capture-to-FSM latency (`p50/p95/p99 < 200 ms`), peak `VmHWM` (`< 512 MB`), and `>= 30 min` tropical thermal soak (`soc_temp_c < 80 °C`).
2. **Missing Crossing Field Hardware:**
   - **Independent physical crossing occupancy sensor (`0/27` present):** radar, inductive loop, LiDAR beam, or calibrated overhead box camera — without it, `V3_CONSERVATIVE_POSITIVE` safely latches fail-closed (`0/11` completed real-cache reopenings on `sync11`).
   - **Calibrated upstream approach mounting:** field verification of the unvalidated `84–211 m` kinematic estimate under target focal lengths and track geometry.
   - **Safety Rule:** Zero connection to live railway signaling, barriers, or relays without independent safety certification.

---

## 5. PUBLICATION STATUS

| Claim Scope | Can Be Published / Claimed Today? | Mandatory Qualification / Disclosure |
|---|---|---|
| **Architecture & Safety State Machine (`V3`)** | **YES** | Verified causal semantics, `0` illegal FSM transitions (`18` fault injections, `100` `Exp Q` stress runs), non-backfill alignment (`Exp I`). Simulation safety policy `!=` physical certification. |
| **Dataset Leakage Forensics (`Vision V1` & `Audio V3`)** | **YES** | Strictly verified from repository manifests (`87.1%` / `93.1%` Vision leakage; `32.56%` Audio stem leakage; clean candidate splits verified at `0%` overlap; retraining deferred until `AUTH-MEDIA-ACCESS`). |
| **Exploratory Field Diagnostics (`Exp A–J, O, R, S`)** | **ONLY AS EXPLORATORY DIAGNOSTICS** | Must disclose: `ready: false` (`0` Stage-2.1 reviews), single crossing (`crossing_A`), `pre-db40305` unrotated caches, Session 1 (`7/20`) vs Session 2 (`3/3`) disparity, `0/11` completed `sync11` reopenings (fail-closed EOF latch), and `Exp R` `Recall` drop (`0.9231 -> 0.6154`) + non-significant Brier Δ CI `[-0.0839, +0.0104]`. |
| **Host Edge Optimization (`Exp P`)** | **YES (AS HOST BENCHMARK ONLY)** | Measured on Apple M1 CPU (`SYNTHETIC_ONLY`); Raspberry Pi figures are unmeasured `2.4×`/`5.5×` analytical projections (`physical_raspberry_pi_tested = false`). |
| **Cross-Crossing OOD Accuracy / Field Readiness** | **FORBIDDEN TODAY** | Blocked until Option C multi-crossing capture, model retraining, official `Stage-2.1` + Phase 12 evaluation (`ready: true`), and physical Raspberry Pi validation complete. |

---

## 6. NEXT ACTION

**Shortest Legitimate Sequence to Unlock Valid Research Stage (Option A First, Then Hardware / Option C):**
1. **Today (Supervisor, ~5 min):** Sign [`AUTH_MEDIA_ACCESS.template.json`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/approval_packages/AUTH_MEDIA_ACCESS.template.json) -> `data/governance/AUTH-MEDIA-ACCESS.json` (and copy/confirm Option A framing vs Option C goal).
2. **Next (Human Reviewers):** Execute `Stage-2.1` human review across all `27` events per [`STAGE21_27_EVENT_REVIEW_CHECKLIST.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/approval_packages/STAGE21_27_EVENT_REVIEW_CHECKLIST.md) (`~30s+` per event + `RD-043` second review where triggered), then emit `data/governance/stage21_promotion_receipt.json` via `readiness_cli`.
3. **Option A Completion:** PI signs [`AUTH_DESCRIPTIVE_EVAL_EXEC.template.json`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/approval_packages/AUTH_DESCRIPTIVE_EVAL_EXEC.template.json) (pre-bound to `MM_SUPPORTED_CONDITIONS` + manifest SHA-256 `2fb08c92...`) -> `data/governance/AUTH-DESCRIPTIVE-EVAL-EXEC.json` for authorized upright 27-event descriptive evaluation via `scripts/prepare_and_execute_official_evaluation.py --mode execute-option-a-descriptive`; publish Option A paper strictly under the 6-tier evidence boundaries without cross-site claims.
4. **Hardware & Option C Expansion (Parallel Track):** Run [`scripts/rpi_edge_benchmark.py`](file:///Users/sayemuddin/Desktop/Train_automation/scripts/rpi_edge_benchmark.py) + 30-min soak on physical Raspberry Pi 4B/5, then collect the `>= 5`-crossing / `13`-session (`235`-event primary, `271` high-power) balanced dataset with `>= 15 s` post-`T4` tail and physical occupancy ground truth before unlocking Phase 12 (`eval_authorization.json`).
