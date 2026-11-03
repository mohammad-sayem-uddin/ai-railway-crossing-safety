# MISSION 16E: MASTER RESEARCHER DECISION REGISTER INDEPENDENT CHALLENGE

**Project:** Train Gate Automation — Bangladesh  
**Mission:** 16E — Independent Governance, Technical Assurance, and Decision Register Challenge  
**Auditor:** Independent Principal Research, Technical Assurance, and Governance Auditor  
**Audit Target:** Master Researcher Decision Register (Mission 16A), 13 Mandatory Decisions, 6-Step Action Plan, RD-001–RD-055 Alignment, Security Tokens, and Ground-Truth Promotion Architecture  
**Historical Baseline HEAD:** `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`  
**Execution Authority:** NONE — AUDITOR DOES NOT DECIDE OR APPROVE  
**Audit Mode:** STRICT READ-ONLY AUDIT  
**Date:** 2026-11-03  

---

## 1. Executive Verdict

This independent audit conducts an adversarial technical, methodological, and governance challenge of the 13 mandatory human researcher decisions and the six-step execution action plan presented in [`docs/generated/master_reaudit/MASTER_RESEARCHER_DECISION_REGISTER.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/master_reaudit/MASTER_RESEARCHER_DECISION_REGISTER.md).

### Statutory Disposition:
$$\mathbf{MASTER\_REGISTER\_REQUIRES\_MAJOR\_RESTRUCTURING}$$

### Principal Audit Findings:
1. **Tool Incompetence and Broken Action Plan Sequence:**  
   The proposed Action Plan directs human adjudication sessions in Step 2 using [`src/railway_detection/annotation/adjudication_session.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/annotation/adjudication_session.py#L126-L142). However, inspection of primary source code proves that `adjudication_session.py` is hard-coded to be **synthetic-only**; it enforces `_require_synthetic_id()` (rejecting all real corpus event IDs) and `_require_temp_path()` (rejecting repository paths). Furthermore, Step 3 attempts to execute [`promotion_gate.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/annotation/promotion_gate.py#L219-L232), which live-hashes raw media files and requires media authorization, yet `AUTH-MEDIA-ACCESS` is not scheduled for issuance until Step 5. Step 2 and Step 3 are structurally incapable of executing as written.
2. **Obsolete and Contradictory Protocol Binding (Decision 9):**  
   Decision 9 proposes locking in-place `FINAL_GROUND_TRUTH_PROTOCOL.md` v7.0.0. This directly contradicts confirmed researcher directions `RD-001`, `RD-004`, `RD-005`, `RD-006`, and `RD-008`. In-place v7.0.0 retains an obsolete, scientifically invalid definition of Premature Opening tied to $T_1$ (instead of $T_4$), lacks the formal entry landmark deferral for $T_2$, and contradicts the `M4`/`M5` metric definitions. Binding v7.0.0 would codify known contradictions into an immutable standard.
3. **Flawed Checkpoint Integrity Verification (Decision 1):**  
   Option 1B suggests adopting a detached SHA-256 sidecar hash "avoiding direct byte reads." An integrity check that avoids reading checkpoint bytes does not verify the integrity of the file on disk; it merely checks that a sidecar file exists. This creates a false security posture and enables undetected weight substitution or corruption. Checkpoint byte hashing must be decoupled between static preflight checks and authorized runtime loading.
4. **Invalid Conflation of Benchmark Parameters with Physical Metrics (Decision 5):**  
   Decision 5 bundles software state machine hysteresis parameters (2-frame optical confirmation, 5-second acoustic dwell, 2.0-second sensor staleness) with the `3.6-second MTR threshold`. Prior audits (Missions 16A, 16A-MTR, 16A-Rechallenge, 16B) proved that the 3.6-second threshold is an implementation artifact of retroactive simulation stepping, that 20/23 train events are left-censored at recording onset ($T_0 \le 0.0\,\text{s}$), and that physical lead-in feasibility is `NOT_ESTIMABLE` on this dataset. Asking the Principal Investigator to formally sign off on 3.6 s as an "official benchmark parameter" under Option 5A conflates software controller dwell with an unvalidated safety metric.
5. **Scientifically Defective Disagreement Resolution (Decision 7):**  
   Option 7B proposes mean/median timestamp averaging for disputed boundary timestamps. Averaging distinct human observations for critical railway arrival/departure boundaries creates synthetic timestamps that neither reviewer observed, obscuring physical disagreement. Furthermore, this directly violates confirmed researcher direction `RD-045` (which mandates a separate recorded adjudication entry, leaving unresolved disagreements as `UNCERTAIN`).
6. **Non-Exhaustive Scope in Back-Stream Architecture (Decision 3):**  
   Decision 3 frames back-stream replay as a binary choice between JSONL feature cache replay (Option 3A) and on-the-fly video decoding (Option 3B). However, primary source inspection of [`src/railway_detection/evaluation/cache_only_engine.py:77-88`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/cache_only_engine.py#L77-L88) reveals that `cache_only_engine` currently only supports front-stream conditions (`B0`, `B1`, `B2`). Option 3A cannot be executed without substantial code development. The register omitted Option 3C: scoping the primary descriptive benchmark strictly to front-camera conditions (closing `M-03` as out-of-scope for the primary benchmark, as originally formulated in Mission 15).

---

## 2. Audit Scope and Limitations

### Permitted Evidence:
- Safe Python source files in `src/railway_detection/`.
- Safe configuration files in `configs/`.
- Governance documents, proposed protocols, and researcher direction matrices in `docs/` and `docs/generated/`.
- Historical audit reports and manifests from Missions 1 through 16D.
- Synthetic mathematical and logical analysis.

### Strict Statutory Prohibitions Honored:
- **Zero raw media access:** No `.mov`, `.mp4`, `.wav`, or `.mp3` files were opened, read, decoded, or hashed (`VERIFIED_FROM_SAFE_SOURCE`).
- **Zero model execution or weight hashing:** No checkpoint files (`best.pt`) were read or hashed (`VERIFIED_FROM_SAFE_SOURCE`).
- **Zero real evaluation or simulation execution:** No real-data replays or test suites outside safe synthetic fixtures were run (`VERIFIED_FROM_SAFE_SOURCE`).
- **Zero administrative token generation:** No `EVAL-AUTH`, `AUTH-MEDIA-ACCESS`, or `AUTH-CHECKPOINT-ACCESS` tokens were created (`VERIFIED_FROM_SAFE_SOURCE`).
- **Zero Git state modification:** No staging, commits, branches, resets, or restores were performed (`VERIFIED_FROM_SAFE_SOURCE`).

---

## 3. Evidence Inspected

| Category | Primary Artifact / Module Inspected | Key Safe Evidence Identified |
| :--- | :--- | :--- |
| **Decision Register** | [`docs/generated/master_reaudit/MASTER_RESEARCHER_DECISION_REGISTER.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/master_reaudit/MASTER_RESEARCHER_DECISION_REGISTER.md) | 13 mandatory decisions, Options A/B(/C), 6-step Action Plan |
| **Historical Decisions** | [`docs/generated/phase5/MISSION_15_RESEARCHER_DECISION_REGISTER.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/phase5/MISSION_15_RESEARCHER_DECISION_REGISTER.md) | Initial 13-decision formulation; Option 3A was "Single-Camera Primary Scope" |
| **Researcher Directions**| [`docs/generated/mission_5a/RD_IMPLEMENTATION_MATRIX_20261101_M5A.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/mission_5a/RD_IMPLEMENTATION_MATRIX_20261101_M5A.md) | Canonical status of RD-001 through RD-055 (7 implemented, 29 proposed, 11 recorded, 7 deferred, 1 prohibited) |
| **Ground Truth Protocol** | [`docs/FINAL_GROUND_TRUTH_PROTOCOL.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/FINAL_GROUND_TRUTH_PROTOCOL.md) | v7.0.0 in-place; obsolete T1-based POR text; missing deferred CCA entry landmark |
| **Proposed Protocol** | [`docs/generated/mission_5a/FINAL_GROUND_TRUTH_PROTOCOL_v7.1.0_PROPOSED.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/mission_5a/FINAL_GROUND_TRUTH_PROTOCOL_v7.1.0_PROPOSED.md) | Proposed v7.1.0 incorporating RD-004, RD-005, RD-006, RD-008 |
| **Reviewer Allowlist** | [`data/ground_truth/authorized_reviewers.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/authorized_reviewers.json) | Single authorized reviewer: `raihankabirrahu@gmail.com` |
| **Adjudication Session**| [`src/railway_detection/annotation/adjudication_session.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/annotation/adjudication_session.py) | L126-142: enforces `_require_synthetic_id` and `_require_temp_path` |
| **Second Review Module**| [`src/railway_detection/annotation/second_review.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/annotation/second_review.py) | L42-58: 5 evaluated triggers, `FRONT_BACK_CONFLICT` not mechanically evaluable, 0 tolerance |
| **Promotion Gate** | [`src/railway_detection/annotation/promotion_gate.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/annotation/promotion_gate.py) | L219-232, L404-450: requires live media hashing via `require_media_authorization` |
| **Cache Replay Engine** | [`src/railway_detection/evaluation/cache_only_engine.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/cache_only_engine.py) | L77-88: supports conditions B0, B1, B2 only; zero back-stream condition support |
| **Evaluation Gate** | [`src/railway_detection/evaluation/execution_gate.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/execution_gate.py) | EVAL-AUTH verification logic; SHA-256 bindings; fail-closed |
| **Governance Engine** | [`src/railway_detection/evaluation/governance.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/governance.py) | L487-503: explicit refusal of signatures ("this repository has no signature or key infrastructure") |
| **Security Governance** | [`docs/generated/master_reaudit/MASTER_SECURITY_GOVERNANCE_AUDIT.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/master_reaudit/MASTER_SECURITY_GOVERNANCE_AUDIT.md) | Findings F13-08, F13-09, F13-10, F13-15, F13-17 |
| **Simulation Timing** | [`docs/generated/master_reaudit/TABLE11_TIMING_BOUND_INDEPENDENT_CHALLENGE.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/master_reaudit/TABLE11_TIMING_BOUND_INDEPENDENT_CHALLENGE.md) | Theorem: complete cycles $\Delta T = 0.00\,\text{s}$, truncated cycles $\Delta T = -0.20\,\text{s}$ |
| **Historical Metrics** | [`docs/generated/master_reaudit/HISTORICAL_BENCHMARK_CAUSALITY_IMPACT_AUDIT.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/master_reaudit/HISTORICAL_BENCHMARK_CAUSALITY_IMPACT_AUDIT.md) | M4, M5, Clearance Latency non-computable historically ($T_4 = \text{null}$) |

---

## 4. Thirteen Individual Decision Challenges

### Decision 1: Model Checkpoint Integrity Hashing Authorization (F13-09)
1. **Original Framing & Options:**  
   - *Context:* Preflight checks verify checkpoint weights (`experiments/vision/39f402dfe460/checkpoints/weights/best.pt`) via SHA-256. Hashing reads bytes.  
   - *Option 1A:* Maintain checkpoints as non-media system assets; allow read-only hashing during preflight.  
   - *Option 1B:* Adopt detached, cryptographically signed SHA-256 sidecar hashes signed by the researcher, avoiding direct byte reads.  
   - *Option 1C:* Require explicit `AUTH-CHECKPOINT-ACCESS` token before any checkpoint byte read.
2. **What the Options Actually Authorize:**  
   - Option 1A authorizes opening and reading checkpoint weights during preflight with zero access control.  
   - Option 1B authorizes validating a detached text file without verifying that the file on disk matches the hash.  
   - Option 1C establishes a formal capability token required prior to opening model weights.
3. **Supporting Repository Evidence:**  
   - `src/railway_detection/experiments/frozen_config.py:184-194` (`compute_file_sha256`) opens files via `open(p, "rb")` and reads full bytes (`VERIFIED_FROM_SAFE_SOURCE`).  
   - `src/railway_detection/safety/media_guard.py:103` notes checkpoint status is uncontrolled (`VERIFIED_FROM_SAFE_SOURCE`).
4. **Contradictions or Missing Evidence:**  
   - Option 1B is technically contradictory: checking a detached signature *without* hashing `best.pt` does not verify checkpoint integrity. It only verifies that a signature over *some* string is valid. If `best.pt` is altered, corrupted, or replaced, Option 1B passes blindly (`INFERENCE`).
5. **Conflicts with RD-001–RD-055:** None directly; aligns with need to formalize governance under `RD-009`.
6. **Security Implications:**  
   - Option 1A bypasses media quarantine. Option 1B introduces a silent verification bypass. Option 1C enforces least-privilege capability access.
7. **Research-Validity Implications:**  
   - True reproducibility requires proving that the exact weight file evaluated matches the published SHA-256 digest (`best.pt`: `f8b22e1...`).
8. **Missing Prerequisites:**  
   - Key management infrastructure: if sidecars are "signed", what key signs them? Who holds the private key?
9. **Exhaustiveness:** Inadequate. Lacks the proper two-phase model: Phase 1 (static metadata check during preflight against signed manifest) and Phase 2 (full byte-hash verification under `AUTH-CHECKPOINT-ACCESS` immediately prior to inference).
10. **Split Recommendation:** Split into (a) Preflight Checkpoint Policy and (b) Runtime Weight Access Authorization.
11. **Recommended Wording Amendment:**  
    *"Decouple checkpoint verification into two phases: (1) Preflight verifies presence and matches registered manifest metadata without byte reads; (2) Evaluation runner verifies full SHA-256 bytes under an explicit `AUTH-CHECKPOINT-ACCESS` token."*
12. **PI Decidability:** `OPTIONS_INADEQUATE`. Requires restructuring before decision.

---

### Decision 2: EVAL-AUTH Token Lifecycle, Expiration, and Revocation (F13-10)
1. **Original Framing & Options:**  
   - *Context:* `EVAL-AUTH` schema v1 lacks single-use nonces and automated revocation lists (CRL).  
   - *Option 2A:* Retain static JSON token model (v1.0.0).  
   - *Option 2B:* Upgrade to `EVAL-AUTH` v2.0 requiring cryptographic nonces, single-run expiration, and HMAC/ECDSA signatures.
2. **What the Options Actually Authorize:**  
   - Option 2A authorizes indefinite token validity and replay. Option 2B mandates cryptographic PKI infrastructure.
3. **Supporting Repository Evidence:**  
   - `src/railway_detection/evaluation/governance.py:487-503` explicitly states: *"only ATTESTATION_RECORDED_STATEMENT is verifiable; this repository has no signature or key infrastructure, so signature-style attestations are refused"* (`VERIFIED_FROM_SAFE_SOURCE`).
4. **Contradictions or Missing Evidence:**  
   - Option 2B mandates "HMAC/ECDSA signatures", but the codebase explicitly rejects digital signatures because no PKI, key escrow, or signature verification library is integrated (`VERIFIED_FROM_SAFE_SOURCE`). Option 2B demands infrastructure that does not exist.
5. **Conflicts with RD-001–RD-055:** Aligns with `RD-009` (canonical identifiers) and `RD-039` (evaluation authorization).
6. **Security Implications:**  
   - Static tokens (2A) allow token re-use across multiple unmonitored runs. Full ECDSA (2B) is currently unimplementable without adding external crypto dependencies and key governance.
7. **Research-Validity Implications:**  
   - An evaluation token must bind to a single run execution hash to ensure that execution receipts cannot be forged or recycled.
8. **Missing Prerequisites:**  
   - Key custody protocol, nonce tracking datastore, and revocation registry location.
9. **Exhaustiveness:** Inadequate. Omits the realistic intermediate model: single-use SHA-256 run nonce bound to system clock, process PID, and git commit hash, with status checked against a local append-only revocation ledger (`data/governance/revocations.json`).
10. **Split Recommendation:** Keep unified, but replace unrealistic PKI requirements with deterministic run-nonce binding.
11. **Recommended Wording Amendment:**  
    *"Upgrade `EVAL-AUTH` to v1.1: require a UUIDv4 run nonce, explicit valid-from/valid-to UTC lease window (max 4 hours), Git commit binding, and a local revocation ledger, while retaining `ATTESTATION_RECORDED_STATEMENT` without external PKI dependencies."*
12. **PI Decidability:** `OPTIONS_INADEQUATE`.

---

### Decision 3: Descriptive Back-Stream Cache Route Architecture (M-03)
1. **Original Framing & Options:**  
   - *Context:* The descriptive benchmark evaluates front-camera and back-stream features. Must decide whether back-stream data is read from precomputed perceptual feature caches or decoded on-the-fly.  
   - *Option 3A:* Cache-only replay using static JSONL feature caches (zero raw media access required).  
   - *Option 3B:* Dynamic on-the-fly video decoding requiring direct access to raw `.mov` video files.
2. **What the Options Actually Authorize:**  
   - Option 3A authorizes running back-stream replay from JSONL caches. Option 3B authorizes breaking media quarantine for `.mov` files.
3. **Supporting Repository Evidence:**  
   - `src/railway_detection/evaluation/cache_only_engine.py:77-88`:  
     `SUPPORTED_CONDITIONS = frozenset({"B0", "B1", "B2"})`  
     `CONDITION_STREAMS = {"B0": {"front_vision"}, "B1": {"front_audio"}, "B2": {"front_vision", "front_audio"}}` (`VERIFIED_FROM_SAFE_SOURCE`).  
   - Back-stream conditions (`B0_back`, `B2_back`, `B3`, `B4`) are **completely unsupported** in `cache_only_engine.py`.
4. **Contradictions or Missing Evidence:**  
   - Option 3A is physically impossible with current code: no back-stream JSONL caches exist, and the engine cannot load them.  
   - In `docs/generated/phase5/MISSION_15_RESEARCHER_DECISION_REGISTER.md:87`, Option 3A was originally framed as: *"Formally define the descriptive benchmark scope as primary-camera only, closing M-03 as not required."* The Mission 16A register altered this option into an unbuilt technical feature (`VERIFIED_FROM_SAFE_SOURCE`).
5. **Conflicts with RD-001–RD-055:**  
   - Conflicts with `RD-015` and `RD-028` (independent-camera primary, fused 11-event exploratory).
6. **Security Implications:**  
   - Option 3B requires global `AUTH-MEDIA-ACCESS` to raw video.
7. **Research-Validity Implications:**  
   - If back-stream caches do not exist, claiming cache-only back-stream evaluation is misleading.
8. **Missing Prerequisites:** Back-stream cache generation pipeline, schema specification, and feature extraction validation.
9. **Exhaustiveness:** Inadequate. Lacks Option 3C (Primary Front-Camera Scope Only).
10. **Split Recommendation:** Re-frame into benchmark scope selection vs cache engineering.
11. **Recommended Wording Amendment:**  
    *"Adopt Option 3C: Restrict the official descriptive benchmark replay to primary front-camera conditions (`B0`, `B1`, `B2`), utilizing verified existing feature caches. Defer dual-camera and back-stream replay (`M-03`) to an exploratory future phase."*
12. **PI Decidability:** `OPTIONS_INADEQUATE`.

---

### Decision 4: Runtime Context Token Binding Across Processes (F13-15)
1. **Original Framing & Options:**  
   - *Context:* Authorization tokens stored in process memory. Multiprocessing could lose or leak tokens.  
   - *Option 4A:* Enforce single-process, single-threaded execution for all official evaluations.  
   - *Option 4B:* Implement environment-variable token passing verified by HMAC signature.
2. **What the Options Actually Authorize:**  
   - Option 4A locks evaluation to a single synchronous process. Option 4B uses environment variables for IPC.
3. **Supporting Repository Evidence:**  
   - `src/railway_detection/evaluation/descriptive_exec_gate.py:288` and `execution_gate.py:948-973` execute synchronously in a single Python process (`VERIFIED_FROM_SAFE_SOURCE`).
4. **Contradictions or Missing Evidence:**  
   - Option 4B is vulnerable to environment leakage (`os.environ` visible to child processes, shell commands, crash logs).
5. **Conflicts with RD-001–RD-055:** None.
6. **Security Implications:**  
   - Single-process execution eliminates IPC token leakage and TOCTOU races between parent and worker processes.
7. **Research-Validity Implications:**  
   - Guarantees 100% deterministic, reproducible evaluation execution orders.
8. **Missing Prerequisites:** None. Single-process execution is already the repository standard.
9. **Exhaustiveness:** Complete.
10. **Split Recommendation:** Keep unified.
11. **Recommended Wording Amendment:**  
    *"Adopt Option 4A: Mandate single-process, single-threaded execution for all official evaluation runs, passing the verified authorization context object directly via function arguments."*
12. **PI Decidability:** `DECISION_READY_WITH_CONDITIONS` (Condition: confirm runner passes context object in-memory).

---

### Decision 5: Crossing State Machine Hysteresis and Bounds (DEC-B05)
1. **Original Framing & Options:**  
   - *Context:* State machine parameters in `configs/decision_policy_v1.yaml`:  
     - 2-frame optical confirmation (`RULE_1`),  
     - 5-second acoustic dwell (`RULE_2`),  
     - 2.0-second sensor staleness clamping (`RULE_8`),  
     - 3.6-second minimum lead-in reaction threshold (`MTR`).  
   - *Option 5A:* Formally sign off on current parameter values as official research benchmark configuration.  
   - *Option 5B:* Revise dwell or staleness thresholds based on empirical field safety considerations.
2. **What the Options Actually Authorize:**  
   - Option 5A adopts all 4 parameters as official standards. Option 5B triggers ad-hoc threshold modifications.
3. **Supporting Repository Evidence:**  
   - `configs/frozen_experiment_v1.yaml:57` sets `warning_dwell_s: 2.0` (`VERIFIED_FROM_SAFE_SOURCE`).  
   - `src/railway_detection/evaluation/lead_in_screen.py` implements the 3.6s screen (`VERIFIED_FROM_SAFE_SOURCE`).  
   - Missions 16A, 16A-MTR, and 16A-Rechallenge established that the 3.6s threshold is an implementation artifact of retroactive simulation stepping, and 20/23 events are left-censored (`REPORTED_BY_PRIOR_AUDIT`).
4. **Contradictions or Missing Evidence:**  
   - Lumping the `3.6-second MTR threshold` in with operational controller hysteresis is a category error. Controller parameters govern barrier lowering logic; MTR is an evaluation metric screening criterion.  
   - Signing off on 3.6s endorses an unvalidated safety claim when physical lead-in is `NOT_ESTIMABLE` (`INFERENCE`).
5. **Conflicts with RD-001–RD-055:**  
   - Conflicts with `RD-021` (insufficient lead-in screen provenance required) and `RD-029` (freeze policy but document limitations).
6. **Security Implications:** None.
7. **Research-Validity Implications:** Severe. Claiming 3.6s is an established safety threshold invalidates scientific credibility.
8. **Missing Prerequisites:** Separation of controller constants from metric evaluation screens.
9. **Exhaustiveness:** Inadequate. Must separate controller parameters from metric feasibility thresholds.
10. **Split Recommendation:** Split into DEC-B05a (Controller Hysteresis) and DEC-B05b (MTR Evaluation Status).
11. **Recommended Wording Amendment:**  
    *"Approve DEC-B05a: Freeze controller parameters (2-frame optical, 5.0s acoustic dwell, 2.0s staleness) as heuristic design constants. Approve DEC-B05b: Disclose the 3.6s MTR threshold as an implementation-derived artifact and classify physical MTR as NOT_ESTIMABLE on the current left-censored dataset."*
12. **PI Decidability:** `OPTIONS_INADEQUATE`.

---

### Decision 6: Adoption of Second-Review Protocol (RD-043)
1. **Original Framing & Options:**  
   - *Context:* `src/railway_detection/annotation/second_review.py` defines 5 deterministic triggers for dual-human review.  
   - *Option 6A:* Formally adopt the 5 triggers (`TRIGGER_CORRECTED`, `TRIGGER_ENGINE_T3_T4`, `TRIGGER_EXPLICIT_FLAG`, `TRIGGER_MEDIA_HASH`, `TRIGGER_UNCERTAIN_BOUNDARY`).  
   - *Option 6B:* Restrict second-review triggers to boundary timestamp corrections only ($>0.5\,\text{s}$).
2. **What the Options Actually Authorize:**  
   - Option 6A mandates dual review for all 5 triggers. Option 6B relaxes dual review to large timestamp shifts.
3. **Supporting Repository Evidence:**  
   - `src/railway_detection/annotation/second_review.py:19-28`:  
     *"There is no timestamp tolerance (RD-012 is deferred): two reviews agree only when states, reference cameras and 1-microsecond-normalized values are identical... A disagreement stays unresolved... because the format of a recorded researcher adjudication (RD-045) has not been adopted"* (`VERIFIED_FROM_SAFE_SOURCE`).  
   - `second_review.py:57`: `FRONT_BACK_CONFLICT` is not mechanically evaluable (`VERIFIED_FROM_SAFE_SOURCE`).
4. **Contradictions or Missing Evidence:**  
   - With zero timestamp tolerance (1-microsecond strict equality), two independent human reviewers will produce 100% disagreements on continuous video boundaries. Adopting Option 6A without defining tolerance (`RD-012`) guarantees an immediate pipeline deadlock (`INFERENCE`).  
   - Furthermore, only one authorized reviewer exists on disk (`authorized_reviewers.json`), making dual review impossible to complete (`VERIFIED_FROM_SAFE_SOURCE`).
5. **Conflicts with RD-001–RD-055:** Aligns with `RD-043`, but conflicts with the deferred state of `RD-012` and `RD-042`.
6. **Security Implications:** None.
7. **Research-Validity Implications:** Dual human review is essential for rigorous ground truth, but must be mathematically operable.
8. **Missing Prerequisites:** Resolution of `RD-012` (timestamp agreement tolerance window) and appointment of a second reviewer (`RD-042`).
9. **Exhaustiveness:** Inadequate without tolerance definition.
10. **Split Recommendation:** Combine with tolerance definition (`RD-012`).
11. **Recommended Wording Amendment:**  
    *"Adopt the 5 second-review triggers conditional upon: (1) defining an operational temporal tolerance window (e.g. $\pm 0.10\,\text{s}$ / 3 frames), and (2) successfully appointing an independent second reviewer."*
12. **PI Decidability:** `OPTIONS_INADEQUATE`.

---

### Decision 7: Adoption of Disagreement Resolution Protocol (RD-045)
1. **Original Framing & Options:**  
   - *Context:* When two human reviewers disagree on a boundary timestamp, formal adjudication is required.  
   - *Option 7A:* Lead Researcher adjudication session serves as final binding ground truth.  
   - *Option 7B:* Mean/median timestamp averaging with recorded uncertainty bounds $[t_{\min}, t_{\max}]$.
2. **What the Options Actually Authorize:**  
   - Option 7A gives the Lead Researcher final binding say. Option 7B synthesizes artificial timestamps by arithmetic averaging.
3. **Supporting Repository Evidence:**  
   - `docs/generated/mission_5a/RD_IMPLEMENTATION_MATRIX_20261101_M5A.md:52`:  
     `RD-045`: *"researcher adjudicates via separate entry; unresolved UNCERTAIN; never overwrite"* (`VERIFIED_FROM_SAFE_SOURCE`).  
   - `src/railway_detection/annotation/second_review.py:27`: Adjudication record schema not implemented (`VERIFIED_FROM_SAFE_SOURCE`).
4. **Contradictions or Missing Evidence:**  
   - Option 7B directly contradicts `RD-045` and scientific integrity: averaging timestamps invents an unobserved physical event. If Reviewer 1 marks entry at 10.0s and Reviewer 2 marks 12.0s, the train was not observed entering at 11.0s (`INFERENCE`).  
   - Option 7A lacks a schema implementation: how is the Lead Researcher adjudication stored without overwriting primary observations?
5. **Conflicts with RD-001–RD-055:** Option 7B directly conflicts with `RD-045`.
6. **Security Implications:** None.
7. **Research-Validity Implications:** Boundary integrity must preserve raw human observations and record formal adjudication metadata.
8. **Missing Prerequisites:** Implementation of an adjudication record schema in `stage2_1_schema.py`.
9. **Exhaustiveness:** Option 7B is scientifically invalid; Option 7A lacks schema backing.
10. **Split Recommendation:** Keep unified; reject Option 7B outright.
11. **Recommended Wording Amendment:**  
    *"Adopt Option 7A in compliance with RD-045: Lead Researcher adjudicates disputes via a distinct, append-only adjudication record in the event history. Original reviewer observations are never overwritten. Disagreements that cannot be resolved remain classified as UNCERTAIN. Reject arithmetic timestamp averaging."*
12. **PI Decidability:** `OPTIONS_INADEQUATE` (Schema update required).

---

### Decision 8: Authorized Human Reviewer Appointment and Expansion
1. **Original Framing & Options:**  
   - *Context:* `data/ground_truth/authorized_reviewers.json` currently contains only `raihankabirrahu@gmail.com`.  
   - *Option 8A:* Maintain single authorized reviewer for Stage 2.1 (permits single-review events; second-review events blocked).  
   - *Option 8B:* Appoint and add a second qualified railway researcher email to the allowlist.
2. **What the Options Actually Authorize:**  
   - Option 8A limits ground truth to a single reviewer. Option 8B expands the allowlist to permit dual review.
3. **Supporting Repository Evidence:**  
   - `data/ground_truth/authorized_reviewers.json:3-5` lists only `raihankabirrahu@gmail.com` (`VERIFIED_FROM_SAFE_SOURCE`).
4. **Contradictions or Missing Evidence:**  
   - Option 8B specifies no candidate identity, qualifications, railway domain knowledge, or conflict-of-interest criteria. Simply adding an email string does not satisfy research governance (`INFERENCE`).
5. **Conflicts with RD-001–RD-055:** Aligns with `RD-042`.
6. **Security Implications:** Allowlist controls write authority to official ground truth.
7. **Research-Validity Implications:** An independent second reviewer is essential to prevent single-researcher bias in subjective video boundaries.
8. **Missing Prerequisites:** Candidate CV, domain qualification statement, conflict-of-interest disclosure, and protocol calibration training.
9. **Exhaustiveness:** Complete in principle, but missing qualification prerequisites.
10. **Split Recommendation:** Keep unified.
11. **Recommended Wording Amendment:**  
    *"Approve the qualification criteria and protocol onboarding for an independent second reviewer. Upon completion of calibration training, add their verified email to `authorized_reviewers.json`."*
12. **PI Decidability:** `FURTHER_EVIDENCE_REQUIRED` (Specific candidate identity and credentials needed).

---

### Decision 9: Protocol and Schema Version Binding
1. **Original Framing & Options:**  
   - *Context:* Multiple document versions exist (`FINAL_GROUND_TRUTH_PROTOCOL.md` v7.0.0, Stage-2.1 schema v8.1.0-stage2.1).  
   - *Option 9A:* Formally lock Protocol v7.0.0 and Schema v8.1.0-stage2.1 as immutable specifications for the official benchmark.  
   - *Option 9B:* Re-version both documents to 8.0.0 for semantic alignment.
2. **What the Options Actually Authorize:**  
   - Option 9A locks in-place v7.0.0 bytes. Option 9B executes a cosmetic renumbering.
3. **Supporting Repository Evidence:**  
   - `docs/FINAL_GROUND_TRUTH_PROTOCOL.md` is in-place v7.0.0 (`VERIFIED_FROM_SAFE_SOURCE`).  
   - `docs/generated/mission_5a/FINAL_GROUND_TRUTH_PROTOCOL_v7.1.0_PROPOSED.md` was drafted specifically to correct known errors in v7.0.0 (`VERIFIED_FROM_SAFE_SOURCE`).  
   - `RD_IMPLEMENTATION_MATRIX_20261101_M5A.md:8-9`: `RD-001` and `RD-002` require adopting proposed wording before hash binding (`VERIFIED_FROM_SAFE_SOURCE`).
4. **Contradictions or Missing Evidence:**  
   - Locking Protocol v7.0.0 (Option 9A) codifies known contradictions: v7.0.0 defines Premature Opening based on $T_1$ (contradicting M4/M5 and RD-008), omits the $T_2$ deferred landmark definition (contradicting RD-006), and retains invalid lens-plane language (contradicting RD-005) (`VERIFIED_FROM_SAFE_SOURCE`).
5. **Conflicts with RD-001–RD-055:** Direct conflict with `RD-001`, `RD-002`, `RD-004`, `RD-005`, `RD-006`, `RD-008`.
6. **Security Implications:** Hash binding creates an immutable cryptographic anchor; binding an erroneous file creates an immutable error.
7. **Research-Validity Implications:** Catastrophic. Benchmark results would be audited against an obsolete protocol.
8. **Missing Prerequisites:** In-place promotion of `v7.1.0_PROPOSED` to replace obsolete `v7.0.0`.
9. **Exhaustiveness:** Severely defective. Must provide Option 9C (Promote v7.1.0-PROPOSED and bind).
10. **Split Recommendation:** Keep unified, but replace options.
11. **Recommended Wording Amendment:**  
    *"Adopt Protocol v7.1.0 (promoting `v7.1.0_PROPOSED.md` to canonical `FINAL_GROUND_TRUTH_PROTOCOL.md`) and Schema v8.1.0-stage2.1, and bind their SHA-256 digests in `data/governance/protocol_bindings.json`."*
12. **PI Decidability:** `OPTIONS_INADEQUATE`.

---

### Decision 10: Stage-2.1 Promotion Gate Execution Authorization
1. **Original Framing & Options:**  
   - *Context:* Once human adjudication is completed, `promotion_gate.py` must run to produce official promotion receipts.  
   - *Option 10A:* Authorize automated promotion gate execution upon completion of valid human adjudication sessions.  
   - *Option 10B:* Require separate, individual promotion approvals per event batch.
2. **What the Options Actually Authorize:**  
   - Option 10A authorizes lights-out automated promotion. Option 10B requires explicit batch-level human review.
3. **Supporting Repository Evidence:**  
   - `src/railway_detection/annotation/promotion_gate.py:219-232, 436-450` executes live media re-hashing via `require_media_authorization` (`VERIFIED_FROM_SAFE_SOURCE`).
4. **Contradictions or Missing Evidence:**  
   - Automated promotion (Option 10A) creates a headless promotion pipeline where software certifies human ground truth without human verification of the resulting promotion receipts (`INFERENCE`).
5. **Conflicts with RD-001–RD-055:** Aligns with `RD-012` and `RD-041`.
6. **Security Implications:**  
   - Requires `AUTH-MEDIA-ACCESS` token to compute live SHA-256 digests during promotion validation.
7. **Research-Validity Implications:**  
   - Promotion creates the immutable Stage-3 ground truth against which all benchmark accuracy is measured.
8. **Missing Prerequisites:** Completed human review sessions and issuance of a scoped promotion media-hashing permit.
9. **Exhaustiveness:** Complete.
10. **Split Recommendation:** Keep unified.
11. **Recommended Wording Amendment:**  
    *"Adopt Option 10B: Require explicit batch-level human inspection and sign-off for each cohort promotion batch, executing `promotion_gate.py` under an explicit, single-use promotion authorization."*
12. **PI Decidability:** `DECISION_READY_WITH_CONDITIONS` (Condition: human reviews must exist first).

---

### Decision 11: Mission 12 Incident Administrative Review (F13-08)
1. **Original Framing & Options:**  
   - *Context:* Mission 12 executed protected Phase 12 tests (`EXECUTION_CONFIRMED_ACCESS_NOT_ESTABLISHED`).  
   - *Option 11A:* Sign formal administrative review memo closing the incident without penalty, noting that the code boundary has since been completely isolated and verified.  
   - *Option 11B:* Request deeper operating-system-level audit logging if available.
2. **What the Options Actually Authorize:**  
   - Option 11A administratively closes the incident. Option 11B requests additional forensics.
3. **Supporting Repository Evidence:**  
   - `docs/generated/master_reaudit/MASTER_SECURITY_GOVERNANCE_AUDIT.md:106-114`: Incident classified as `EXECUTION_CONFIRMED_ACCESS_NOT_ESTABLISHED` (`VERIFIED_FROM_SAFE_SOURCE`).  
   - Pytest access guard plugin now isolates protected tests (`VERIFIED_FROM_SAFE_SOURCE`).
4. **Contradictions or Missing Evidence:**  
   - Option 11A's justification ("noting that the code boundary has since been completely isolated") conflates subsequent remediation with historical fact. Current code isolation cannot prove past non-access. Option 11B is technically infeasible because retrospective OS file audit logs were not enabled (`INFERENCE`).
5. **Conflicts with RD-001–RD-055:** None.
6. **Security Implications:**  
   - Formal closure documents risk acceptance by the PI.
7. **Research-Validity Implications:**  
   - Prevents unverified past executions from clouding future benchmark reproducibility.
8. **Missing Prerequisites:** Honest risk-acceptance framing.
9. **Exhaustiveness:** Complete.
10. **Split Recommendation:** Keep unified.
11. **Recommended Wording Amendment:**  
    *"Sign formal administrative review memo closing Incident F13-08 on the grounds of administrative risk acceptance: acknowledge that historical test execution occurred, recognize that retrospective byte access cannot be forensically proven or disproven, and certify that subsequent fail-closed test guards fully prevent recurrence."*
12. **PI Decidability:** `DECISION_READY_WITH_CONDITIONS`.

---

### Decision 12: Manuscript Authorship and AI Reclassification
1. **Original Framing & Options:**  
   - *Context:* `docs/PAPER_DRAFT_DESCRIPTIVE_BENCHMARK.md` currently lists `Antigravity Autonomous Research Engineering Agent` as co-author.  
   - *Option 12A:* Remove AI agent from author line; list human Principal Investigator(s) as sole authors; add AI disclosure to Acknowledgments per IEEE/COPE standards.  
   - *Option 12B:* Retain current text until journal submission.
2. **What the Options Actually Authorize:**  
   - Option 12A enforces human authorship and ethical AI disclosure. Option 12B defers compliance.
3. **Supporting Repository Evidence:**  
   - `docs/PAPER_DRAFT_DESCRIPTIVE_BENCHMARK.md` author block (`VERIFIED_FROM_SAFE_SOURCE`).  
   - `docs/generated/mission_5a/RD_IMPLEMENTATION_MATRIX_20261101_M5A.md:61`: `RD-054` confirmed human authors only with draft AI disclosure (`VERIFIED_FROM_SAFE_SOURCE`).
4. **Contradictions or Missing Evidence:**  
   - Option 12B violates COPE, IEEE, and ACM publishing standards, which strictly prohibit naming generative AI agents as authors. Retaining an AI author in a formal repository register is improper.
5. **Conflicts with RD-001–RD-055:** Aligns with `RD-054`.
6. **Security Implications:** None.
7. **Research-Validity Implications:** Crucial for manuscript submission and academic integrity.
8. **Missing Prerequisites:** Full list of contributing human authors and affiliations.
9. **Exhaustiveness:** Complete (Option 12A is the only ethically viable path).
10. **Split Recommendation:** Keep unified.
11. **Recommended Wording Amendment:**  
    *"Adopt Option 12A immediately in compliance with RD-054: Designate human researcher(s) as sole authors and incorporate a comprehensive Generative AI Disclosure in the Acknowledgments detailing agent utilization for static code analysis, test authoring, and documentation drafting."*
12. **PI Decidability:** `DECISION_READY_FOR_PI`.

---

### Decision 13: Future Real-Data Evaluation Authorization (EVAL-AUTH)
1. **Original Framing & Options:**  
   - *Context:* Official Phase 5 real-data evaluation remains unauthorized.  
   - *Option 13A:* Issue formal `EVAL-AUTH.json` and `AUTH-MEDIA-ACCESS.json` tokens ONLY AFTER Decisions 1–12 and all 27 human adjudication sessions are completed.  
   - *Option 13B:* Issue descriptive-only evaluation authorization for static feature caches.
2. **What the Options Actually Authorize:**  
   - Option 13A authorizes full real-data execution upon completion of prior milestones. Option 13B authorizes cache replay.
3. **Supporting Repository Evidence:**  
   - `src/railway_detection/evaluation/governance.py:415-465` and `execution_gate.py:948-973` enforce fail-closed evaluation authorization (`VERIFIED_FROM_SAFE_SOURCE`).
4. **Contradictions or Missing Evidence:**  
   - "Decisions 1–12 and 27 human adjudication sessions completed" is **insufficient**: it omits verifying promoted Stage-3 ground truth receipts, omits fixing retroactive simulation stepping (`runner.py`), and ignores that $M4$, $M5$, and clearance latency are non-computable on real data (`REPORTED_BY_PRIOR_AUDIT`).  
   - Conflates `EVAL-AUTH` (execution logic), `AUTH-MEDIA-ACCESS` (video reading), and `AUTH-CHECKPOINT-ACCESS` (weight reading) into a monolithic bundle (`INFERENCE`).
5. **Conflicts with RD-001–RD-055:** Aligns with `RD-039` and `RD-050`.
6. **Security Implications:** Unlocks all guarded assets; requires highest security scrutiny.
7. **Research-Validity Implications:** Must ensure that models and ground truth are immutable before evaluation commences.
8. **Missing Prerequisites:** Granular, token-specific issuance criteria and remediation of simulation stepping causality.
9. **Exhaustiveness:** Inadequate. Lacks granular token decomposition.
10. **Split Recommendation:** Decouple into three distinct tokens: (1) `AUTH-MEDIA-ACCESS` (review & promotion only), (2) `AUTH-DESCRIPTIVE-CACHE-EXEC` (cache replay), and (3) `EVAL-AUTH-FULL` (full raw media pipeline).
11. **Recommended Wording Amendment:**  
    *"Defer full evaluation authorization. Establish a tiered authorization model: (1) Issue scoped media access solely for human adjudication and promotion; (2) Authorize cache-only descriptive replay; (3) Restrict full raw-media evaluation until simulation causality and ground truth promotion are independently validated."*
12. **PI Decidability:** `DEFERRED_PENDING_OTHER_GATE`.

---

## 5. Challenge to the Original Six-Step Action Plan

The original Action Plan proposed in Section 3 of `MASTER_RESEARCHER_DECISION_REGISTER.md` states:
```
STEP 1: Execute Decisions 8, 9, and 11 (Appoint Reviewer, Lock Protocols, Close M12 Incident).
STEP 2: Execute Human Adjudication Sessions for 27 Events using adjudication_session.py.
STEP 3: Execute Decision 10 (Run promotion_gate.py to generate Stage-2.1 Ground Truth).
STEP 4: Execute Decisions 1, 2, and 5 (Finalize Checkpoint Hashing and Policy Configs).
STEP 5: Execute Decision 13 (Issue EVAL-AUTH for Official Descriptive Benchmark Replay).
STEP 6: Execute Decision 12 (Populate Tables 1-3, Finalize Authorship, Submit Paper).
```

### Critical Flaws and Vulnerabilities in the Action Plan:
1. **Tool Incapacity in Step 2:**  
   Step 2 directs executing `adjudication_session.py` across 27 real events. As proven in Section 3, `adjudication_session.py` lines 126–142 explicitly enforce `_require_synthetic_id()` and `_require_temp_path()`. Calling this module on `train_events_001` or any real event path immediately raises `EventNotInManifestError` or `AdjudicationSessionError`. Step 2 cannot be executed without modifying or wrapping the tool.
2. **Missing Media Authorization in Step 2 and Step 3:**  
   Human reviewers in Step 2 must inspect video footage, and `promotion_gate.py` in Step 3 re-hashes raw media files on disk (`compute_media_sha256_pair`). Both require `AUTH-MEDIA-ACCESS`. However, Decision 13 (which issues `AUTH-MEDIA-ACCESS`) is placed in **Step 5**! Step 2 and Step 3 will fail closed due to missing media permissions.
3. **Premature Protocol Lock in Step 1:**  
   Step 1 calls for executing Decision 9 (Lock Protocols). As proven in Section 4, locking in-place Protocol v7.0.0 binds an obsolete specification containing invalid $T_1$-based Premature Opening rules and uncorrected boundary definitions. Protocol `v7.1.0_PROPOSED` must be promoted first.
4. **Retroactive Simulation Defect Ignored in Step 5:**  
   Issuing `EVAL-AUTH` in Step 5 executes the simulation runner without addressing the retroactive actuator stepping defect proven in Missions 16A and 16B. The resulting replay would generate distorted timing profiles.
5. **Fraudulent Publication Pathway in Step 6:**  
   Step 6 directs populating Tables 1–3 and submitting the paper. However, Table 3 contains $M4$ (POR), $M5$, and Clearance Latency, which Mission 16B proved are **`NON-COMPUTABLE`** on the historical real dataset because $T_4$ was never established. Claiming zero premature openings or populated latencies without qualified annotations is scientifically fraudulent.

---

## 6. Cross-Mission Consistency Matrix

| Decision | Related RD | Prior Audit Finding | Conflict or Gap Identified | Evidence Required to Proceed | Status for PI |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **D1: Checkpoint Hashing** | `RD-009` | F13-09; weights quarantined | Detached sidecar without byte read does not verify file integrity | Two-phase verification protocol (metadata preflight + runtime hash) | `OPTIONS_INADEQUATE` |
| **D2: EVAL-AUTH Lifecycle** | `RD-009`, `RD-039` | F13-10; static token re-usable | Option 2B demands PKI/ECDSA rejected by `governance.py` | Nonce & local revocation ledger design | `OPTIONS_INADEQUATE` |
| **D3: Back-Stream Route** | `RD-015`, `RD-028` | M-03; back-stream unsupported | `cache_only_engine.py` supports B0–B2 only; back caches do not exist | Option 3C: scope to primary front-camera only | `OPTIONS_INADEQUATE` |
| **D4: Token Binding** | `RD-039` | F13-15; unsigned memory flag | Option 4B leaks via env vars; Option 4A needs context argument | Verification of synchronous in-memory context passing | `DECISION_READY_WITH_CONDITIONS` |
| **D5: SM Bounds & MTR** | `RD-021`, `RD-029` | 3.6s is simulation artifact; MTR not estimable | Bundles controller dwell with unvalidated 3.6s MTR screen | Decouple controller constants from MTR metric status | `OPTIONS_INADEQUATE` |
| **D6: Second Review** | `RD-012`, `RD-043` | 0 tolerance causes 100% dispute; 1 reviewer | Cannot operate with 1 reviewer and 0-microsecond tolerance | Adopt $\pm 0.10\,\text{s}$ tolerance window; appoint 2nd reviewer | `OPTIONS_INADEQUATE` |
| **D7: Disagreement Res.** | `RD-045` | Adjudication schema not built | Option 7B averaging violates RD-045 and physical reality | Adjudication record schema in `stage2_1_schema.py` | `OPTIONS_INADEQUATE` |
| **D8: Reviewer Allowlist** | `RD-042` | Only 1 reviewer on disk | Option 8B omits qualification & training criteria | CV, independence statement, calibration test record | `FURTHER_EVIDENCE_REQUIRED` |
| **D9: Protocol Binding** | `RD-001`–`RD-008` | v7.0.0 contains known errors | Locking v7.0.0 binds obsolete T1 premature opening | Promote `v7.1.0_PROPOSED.md` to in-place canonical protocol | `OPTIONS_INADEQUATE` |
| **D10: Promotion Gate** | `RD-012`, `RD-041` | Promotion gate calls media hash | Automated 10A abdicates human oversight of receipts | Batch sign-off protocol + promotion media permit | `DECISION_READY_WITH_CONDITIONS` |
| **D11: Mission 12 Incident**| `RD-050` | F13-08; unverified execution | Code isolation today does not prove historical non-access | Frame as administrative risk acceptance memo | `DECISION_READY_WITH_CONDITIONS` |
| **D12: Authorship & AI** | `RD-054` | AI listed as co-author | Option 12B violates COPE/IEEE standards | Human author list + IEEE/COPE AI disclosure statement | `DECISION_READY_FOR_PI` |
| **D13: Future EVAL-AUTH** | `RD-039`, `RD-050` | Real replay unauthorized; M4 non-computable | Conflates media access, cache replay, and pipeline evaluation | Decouple into tiered, scoped authorization tokens | `DEFERRED_PENDING_OTHER_GATE` |

---

## 7. Corrected Human Decision Dossier

### Summary Classification Table:
- `DECISION_READY_FOR_PI`: **1** (Decision 12)
- `DECISION_READY_WITH_CONDITIONS`: **3** (Decisions 4, 10, 11)
- `FURTHER_EVIDENCE_REQUIRED`: **1** (Decision 8)
- `OPTIONS_INADEQUATE`: **7** (Decisions 1, 2, 3, 5, 6, 7, 9)
- `DEFERRED_PENDING_OTHER_GATE`: **1** (Decision 13)
- `NOT_DECIDABLE_WITH_CURRENT_EVIDENCE`: **0**

---

### Detailed Dossier Specifications:

#### Decision 1: Model Checkpoint Integrity Hashing
- **Status:** `OPTIONS_INADEQUATE`
- **Revised Question:** Shall the project adopt a two-phase checkpoint integrity model: Phase 1 (preflight checks verify file presence and match registered manifest hashes without byte reads) and Phase 2 (full SHA-256 byte verification executed under an explicit, scoped `AUTH-CHECKPOINT-ACCESS` token immediately prior to model inference)?
- **Revised Options:**
  - *Option 1-R1 (Recommended):* Adopt two-phase checkpoint verification with explicit runtime `AUTH-CHECKPOINT-ACCESS` token.
  - *Option 1-R2:* Quarantine checkpoints completely; execute evaluation exclusively from precomputed feature caches (zero checkpoint access required).
- **Evidence for PI:** `src/railway_detection/experiments/frozen_config.py:184-194`, `MASTER_SECURITY_GOVERNANCE_AUDIT.md:115-119`.
- **Prerequisites:** Decision 13 token decomposition.

#### Decision 2: EVAL-AUTH Token Lifecycle & Revocation
- **Status:** `OPTIONS_INADEQUATE`
- **Revised Question:** Shall the `EVAL-AUTH` token specification be upgraded to v1.1 to enforce single-run execution nonces, a maximum 4-hour validity window, Git commit hash binding, and a local revocation ledger, while retaining `ATTESTATION_RECORDED_STATEMENT` without external PKI?
- **Revised Options:**
  - *Option 2-R1 (Recommended):* Implement `EVAL-AUTH` v1.1 with UUIDv4 nonce, 4-hour lease window, commit binding, and `data/governance/revocations.json` ledger.
  - *Option 2-R2:* Retain v1.0.0 static tokens, accepting the risk of replay across unmonitored runs.
- **Evidence for PI:** `src/railway_detection/evaluation/governance.py:487-503`, `MASTER_SECURITY_GOVERNANCE_AUDIT.md:120-124`.
- **Prerequisites:** None.

#### Decision 3: Descriptive Back-Stream Cache Route (M-03)
- **Status:** `OPTIONS_INADEQUATE`
- **Revised Question:** Shall the descriptive research benchmark be officially scoped to primary front-camera conditions (`B0`, `B1`, `B2`) where validated static feature caches already exist, deferring dual-camera back-stream replay (`M-03`) to exploratory future work?
- **Revised Options:**
  - *Option 3-R1 (Recommended):* Formally restrict the primary benchmark to front-camera conditions (`B0`, `B1`, `B2`), closing `M-03` as out-of-scope for the primary publication.
  - *Option 3-R2:* Halt benchmark evaluation until a full back-stream video feature caching pipeline is developed, verified, and cached.
- **Evidence for PI:** `src/railway_detection/evaluation/cache_only_engine.py:77-88`, `MISSION_15_RESEARCHER_DECISION_REGISTER.md:87`.
- **Prerequisites:** None.

#### Decision 4: Process Context Token Binding (F13-15)
- **Status:** `DECISION_READY_WITH_CONDITIONS`
- **Revised Question:** Shall official evaluation execution be strictly confined to a single, synchronous Python process, passing the verified authorization context object directly via in-memory function arguments?
- **Options:**
  - *Option 4A (Recommended):* Enforce single-process synchronous execution.
  - *Option 4B:* Allow multiprocessing using HMAC-authenticated environment variables.
- **Conditions:** Runner code must explicitly require the in-memory context object and reject global/thread-local fallback flags.
- **Evidence for PI:** `src/railway_detection/evaluation/descriptive_exec_gate.py:288`.

#### Decision 5: Crossing State Machine Parameters and MTR Feasibility
- **Status:** `OPTIONS_INADEQUATE`
- **Revised Question:** Shall the project separate operational controller hysteresis parameters from evaluation screening thresholds by: (a) approving the 2-frame optical confirmation, 5.0s acoustic dwell, and 2.0s sensor staleness clamping as heuristic controller design constants, and (b) classifying the 3.6s MTR threshold as an implementation artifact, formally reporting physical MTR as `NOT_ESTIMABLE` due to 20/23 left-censored approach intervals?
- **Revised Options:**
  - *Option 5-R1 (Recommended):* Approve controller constants under DEC-B05a; classify MTR as `NOT_ESTIMABLE` under DEC-B05b.
  - *Option 5-R2:* Retain 3.6s as an official benchmark threshold, publishing qualified screening percentages with explicit disclosure of recording pre-roll censoring.
- **Evidence for PI:** `TABLE11_TIMING_BOUND_INDEPENDENT_CHALLENGE.md`, `MTR_PROVENANCE_CHALLENGE_AUDIT.md`.
- **Prerequisites:** Prior audit reconciliation.

#### Decision 6: Adoption of Second-Review Protocol (RD-043)
- **Status:** `OPTIONS_INADEQUATE`
- **Revised Question:** Shall the 5 second-review triggers in `second_review.py` be formally adopted, paired with an explicit temporal agreement tolerance ($\pm 0.10\,\text{s}$ / 3 video frames at 30 fps) to resolve deferred direction `RD-012`?
- **Revised Options:**
  - *Option 6-R1 (Recommended):* Adopt the 5 triggers paired with a $\pm 0.10\,\text{s}$ tolerance window.
  - *Option 6-R2:* Retain zero tolerance (1-microsecond strict equality), recognizing that 100% of second reviews will trigger formal adjudication.
- **Evidence for PI:** `src/railway_detection/annotation/second_review.py:19-28`.
- **Prerequisites:** Decision 8 (Second reviewer appointment).

#### Decision 7: Disagreement Resolution Protocol (RD-045)
- **Status:** `OPTIONS_INADEQUATE`
- **Revised Question:** Shall boundary disagreements between human reviewers be resolved exclusively via an independent, append-only Lead Researcher adjudication record (leaving unresolvable disputes as `UNCERTAIN`), while formally rejecting arithmetic timestamp averaging?
- **Revised Options:**
  - *Option 7-R1 (Recommended):* Adopt RD-045 append-only adjudication; implement adjudication record schema; reject timestamp averaging.
  - *Option 7-R2:* Adopt mathematical timestamp averaging with recorded uncertainty bounds $[t_{\min}, t_{\max}]$.
- **Evidence for PI:** `docs/generated/mission_5a/RD_IMPLEMENTATION_MATRIX_20261101_M5A.md:52`.
- **Prerequisites:** Implement schema support for adjudication records in `stage2_1_schema.py`.

#### Decision 8: Authorized Human Reviewer Appointment
- **Status:** `FURTHER_EVIDENCE_REQUIRED`
- **Revised Question:** Shall the Principal Investigator appoint a specific, qualified second human reviewer to `data/ground_truth/authorized_reviewers.json` following verification of credentials, independence, and completion of protocol calibration?
- **Required Evidence:** Candidate curriculum vitae, statement of railway crossing domain knowledge, conflict-of-interest disclosure, and record of calibration on training events.
- **Prerequisites:** Candidate nomination by the PI.

#### Decision 9: Protocol and Schema Version Binding
- **Status:** `OPTIONS_INADEQUATE`
- **Revised Question:** Shall the project promote `docs/generated/mission_5a/FINAL_GROUND_TRUTH_PROTOCOL_v7.1.0_PROPOSED.md` to become the canonical in-place `docs/FINAL_GROUND_TRUTH_PROTOCOL.md` (formally adopting `RD-004`, `RD-005`, `RD-006`, and `RD-008`), and cryptographically bind its SHA-256 digest alongside Schema v8.1.0-stage2.1?
- **Revised Options:**
  - *Option 9-R1 (Recommended):* Promote v7.1.0-PROPOSED to in-place canonical protocol and bind its SHA-256 hash.
  - *Option 9-R2:* Retain and bind in-place v7.0.0, accepting that it contains contradicted definitions of Premature Opening and crossing boundaries.
- **Evidence for PI:** `docs/generated/mission_5a/v7_working_tree_vs_v7.1.0_PROPOSED.diff`.
- **Prerequisites:** Promotion of protocol text in the repository.

#### Decision 10: Stage-2.1 Promotion Gate Execution Authorization
- **Status:** `DECISION_READY_WITH_CONDITIONS`
- **Revised Question:** Shall `promotion_gate.py` be authorized to execute on completed review batches under explicit, batch-level human researcher sign-off, utilizing a temporary, single-use `AUTH-MEDIA-ACCESS` token strictly for live media hash verification?
- **Options:**
  - *Option 10-R1 (Recommended):* Batch-level human authorization with single-use media-hashing permit.
  - *Option 10-R2:* Headless automated promotion upon session completion.
- **Conditions:** All underlying human reviews and second reviews must be complete, verified, and free of unresolved disputes.
- **Evidence for PI:** `src/railway_detection/annotation/promotion_gate.py:271-311`.

#### Decision 11: Mission 12 Incident Administrative Review (F13-08)
- **Status:** `DECISION_READY_WITH_CONDITIONS`
- **Revised Question:** Shall the Principal Investigator sign an administrative review memo closing Incident F13-08 based on formal risk acceptance (acknowledging that historical test execution occurred, that retrospective byte access cannot be proven or disproven, and that verified fail-closed guards prevent recurrence)?
- **Options:**
  - *Option 11-R1 (Recommended):* Sign administrative risk acceptance memo closing F13-08.
  - *Option 11-R2:* Keep incident open as an unresolvable historical limitation.
- **Conditions:** Acknowledge that code isolation today does not constitute historical proof of non-access.
- **Evidence for PI:** `MASTER_SECURITY_GOVERNANCE_AUDIT.md:106-114`.

#### Decision 12: Manuscript Authorship and AI Reclassification
- **Status:** `DECISION_READY_FOR_PI`
- **Revised Question:** Shall the manuscript authorship block in `docs/PAPER_DRAFT_DESCRIPTIVE_BENCHMARK.md` be updated immediately to list human researchers as sole authors in compliance with COPE/IEEE standards, accompanied by a comprehensive Generative AI Disclosure statement in the Acknowledgments?
- **Options:**
  - *Option 12-R1 (Recommended):* Designate human researchers as sole authors; add comprehensive AI disclosure statement.
  - *Option 12-R2:* Retain AI co-author listing until formal journal submission.
- **Evidence for PI:** `docs/generated/mission_5a/RD_IMPLEMENTATION_MATRIX_20261101_M5A.md:61`, COPE Guidelines on Authorship and AI.

#### Decision 13: Future Real-Data Evaluation Authorization (EVAL-AUTH)
- **Status:** `DEFERRED_PENDING_OTHER_GATE`
- **Revised Question:** Shall full real-data evaluation authorization be decomposed into granular, phased tokens, deferring end-to-end raw-media evaluation until Stage-3 ground truth is promoted, simulation causality is corrected, and descriptive cache replay is verified?
- **Revised Options:**
  - *Option 13-R1 (Recommended):* Defer full evaluation; establish phased authorization gates (Media Review Auth $\to$ Cache Replay Auth $\to$ Full Pipeline Auth).
  - *Option 13-R2:* Issue blanket evaluation authorization upon completion of human adjudication.
- **Evidence for PI:** `src/railway_detection/evaluation/governance.py:415-465`.
- **Prerequisites:** Completion of Stages 0 through 5 of the revised governance sequence.

---

## 8. Required Revised Governance Sequence

To resolve the circular dependencies, tool limitations, and sequencing errors of the original 6-step plan, the auditor establishes this eight-stage dependency-ordered governance sequence.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ EIGHT-STAGE DEPENDENCY-ORDERED GOVERNANCE SEQUENCE                          │
├─────────────────────────────────────────────────────────────────────────────┤
│ STAGE 0: Protocol Alignment & Baseline Hygiene                              │
│   • Promote Protocol v7.1.0-PROPOSED to in-place canonical protocol (D9)    │
│   • Close Mission 12 Incident F13-08 via administrative risk memo (D11)     │
│   • Update Manuscript Authorship & AI Disclosure Statement (D12)            │
│ STAGE 1: Reviewer Governance & Calibration                                  │
│   • Define inter-reviewer temporal agreement tolerance ±0.10s (D6, RD-012) │
│   • Appoint & calibrate independent second human reviewer (D8, RD-042)      │
│   • Implement append-only adjudication schema in stage2_1_schema.py (D7)   │
│ STAGE 2: Security & Review Tooling Modernization                            │
│   • Upgrade adjudication_session.py to accept real events under token       │
│   • Implement EVAL-AUTH v1.1 nonce & local revocation ledger (D2)           │
│   • Decouple preflight checkpoint checks from runtime byte reads (D1)       │
│ STAGE 3: Human Review Execution & Disagreement Resolution                   │
│   • Issue scoped AUTH-MEDIA-ACCESS (REVIEW-ONLY) token                      │
│   • Execute primary human review sessions across all 27 events              │
│   • Execute second review sessions for all RD-043 triggered events          │
│   • Execute Lead Researcher adjudication sessions for any disputes (RD-045) │
│ STAGE 4: Ground Truth Promotion & Stage-3 Certification                     │
│   • Issue scoped AUTH-MEDIA-ACCESS (PROMOTION-HASHING) token                │
│   • Run promotion_gate.py with batch-level human researcher sign-off (D10)  │
│   • Cryptographically bind promoted Stage-3 ground-truth receipts           │
│ STAGE 5: Simulation Engine Causality Remediation                            │
│   • Refactor EventSimulationRunner to enforce forward-causal stepping       │
│   • Formally apply verified -0.20s timing correction to Table 11 values     │
│   • Freeze SM controller hysteresis constants; classify MTR as NOT_ESTIMABLE│
│ STAGE 6: Descriptive Benchmark Replay Execution                             │
│   • Formally scope primary benchmark to front-camera B0-B2 conditions (D3)  │
│   • Issue single-use AUTH-DESCRIPTIVE-CACHE-EXEC token                      │
│   • Execute deterministic replay from validated static feature caches       │
│ STAGE 7: Manuscript Finalization & Publication Release                      │
│   • Populate Tables 1-3 with verified descriptive counts and qualifications │
│   • Explicitly report M4/M5 and physical MTR as NON-COMPUTABLE              │
│   • Perform final privacy scrub and prepare venue submission                │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Stage Gate Specifications:
1. **Stage 0 Stop Condition:** Must halt if in-place protocol contains obsolete $T_1$ Premature Opening text.
2. **Stage 1 Stop Condition:** Must halt if only one authorized reviewer exists on disk.
3. **Stage 2 Stop Condition:** Must halt if `adjudication_session.py` rejects real event IDs.
4. **Stage 3 Stop Condition:** Must halt if any second-review dispute remains unresolved without a recorded adjudication.
5. **Stage 4 Stop Condition:** Must halt if `promotion_gate.py` produces any rejection violation.
6. **Stage 5 Stop Condition:** Must halt if simulation runner continues retroactive interval stepping.
7. **Stage 6 Stop Condition:** Must halt if replay attempts to open raw media files instead of static caches.
8. **Stage 7 Stop Condition:** Must halt if manuscript claims empirical 0% premature openings or validated 3.6s physical lead-in.

---

## 9. Manuscript Claims Safety Check

| Manuscript Statement / Topic | Current Paper Status | Audit Classification | Evidentiary Basis & Safe Replacement Language |
| :--- | :---: | :---: | :--- |
| **3.6-Second MTR Threshold** | Claimed as safety lead-in threshold | `NOT_ESTABLISHED` | **Defect:** Implementation artifact of discrete simulation ($0.2\text{s} + 2.0\text{s} + 1.5\text{s} - 0.1\text{s}$).<br>**Safe Replacement:** *"The 3.6-second latency is an implementation-derived minimum controller blocking latency, not an approved railway safety standard."* |
| **Physical Lead-In Feasibility** | Claims feasibility percentage | `NON_COMPUTABLE` | **Defect:** 20/23 train events are left-censored ($T_0 \le 0.0\,\text{s}$); $T_1$ measures recording pre-roll, not train approach.<br>**Safe Replacement:** *"Physical lead-in feasibility is non-computable on the current dataset due to recording onset truncation for 20 of 23 train events."* |
| **M4 Premature Opening Rate** | Reported as 0.0% / empty | `NON_COMPUTABLE` | **Defect:** Roadway clearance $T_4$ was never annotated in proposals ($T_4 = \text{null}$); evaluable count was 0.<br>**Safe Replacement:** *"M4 (Premature Opening Rate) was non-computable across all historical real-data runs because roadway clearance timestamp $T_4$ was unobserved."* |
| **M5 Companion Failures** | Described as intrusion | `NON_COMPUTABLE` | **Defect:** $M5$ is `NEVER_PROTECTED_M5` (integer count), not companion vehicle intrusion.<br>**Safe Replacement:** *"M5 denotes an un-cleared crossing where gate closure was never witnessed prior to clearance."* |
| **Table 11 Closed Duration** | Reported as exact duration | `SUPPORTED_WITH_QUALIFICATION` | **Defect:** Represents simulated passage-blocked duration under retroactive stepping; forward-causal duration is exactly $T - 0.20\,\text{s}$.<br>**Safe Replacement:** *"Table 11 reports simulated passage-blocked duration ($\theta \le 45.0^\circ$) under legacy discrete stepping (Convention A); forward-causal stepping yields exactly $T - 0.20\,\text{s}$ across all 27 events."* |
| **Simulation Stepping Timing** | Claimed 5 Hz / 10 Hz parity | `NOT_ESTABLISHED` | **Defect:** Parity was an artifact of retroactive interval stepping and floating-point accumulation.<br>**Safe Replacement:** *"Simulation stepping artifacts have been characterized; continuous causal reaction latency is 3.70s at 5 Hz and 3.60s at 10 Hz."* |
| **B1 Audio-Only Evaluation** | Evaluates gate actuation | `NOT_ESTABLISHED` | **Defect:** Audio alone cannot actuate gate or prevent premature opening under current fusion rules.<br>**Safe Replacement:** *"Condition B1 evaluates acoustic horn detection capabilities; acoustic signals provide supporting confirmation only and cannot actuate the barrier independently."* |
| **Historical CV Metrics & Split** | mAP@50 = 99.46% | `SUPPORTED_WITH_QUALIFICATION` | **Defect:** Layer A synthetic metrics verified, but real-world train generalization is unproven.<br>**Safe Replacement:** *"Computer vision models achieved 99.46% mAP@50 on isolated benchmark test splits; single-site field generalization remains an acknowledged limitation."* |
| **Weather & Environmental Claims**| Generalization claimed | `NOT_ESTABLISHED` | **Defect:** Single geographical site in Bangladesh; limited environmental coverage.<br>**Safe Replacement:** *"Evaluations reflect single-site operational conditions; multi-site weather robustness is deferred to future work."* |
| **Safety Improvement Claims** | Claims crossing safety gain | `PROHIBITED_CLAIM` | **Defect:** Cannot assert real-world safety improvements without field actuator telemetry and closed-loop control.<br>**Safe Replacement:** *"The proposed system demonstrates the computational feasibility of automated multimodal detection; operational safety claims require dedicated field hardware trials."* |
| **Authorship Attribution** | Lists AI Agent as Co-Author | `PROHIBITED_CLAIM` | **Defect:** AI cannot hold authorship or legal copyright under COPE/IEEE guidelines.<br>**Safe Replacement:** *"Human researchers are sole authors; AI contributions are fully disclosed in Acknowledgments."* |

---

## 10. Unresolved Questions for the Principal Investigator

1. **Second Reviewer Appointment:** Does the PI approve the nomination of an independent railway engineering researcher, and will their credentials and conflict-of-interest statement be provided before human review commences?
2. **Review Agreement Tolerance:** Does the PI confirm adopting a $\pm 0.10\,\text{s}$ (3 video frames at 30 fps) temporal tolerance window for dual human review under `RD-012`?
3. **Protocol Promotion:** Does the PI authorize in-place promotion of `FINAL_GROUND_TRUTH_PROTOCOL_v7.1.0_PROPOSED.md` to replace the obsolete v7.0.0 protocol prior to cryptographic hash binding?
4. **Primary Benchmark Scope:** Does the PI approve formally restricting the official descriptive benchmark to front-camera conditions (`B0`, `B1`, `B2`), closing back-stream cache gap `M-03` as out-of-scope for the Version 1.0 paper?
5. **MTR Metric Disposition:** Does the PI accept classifying physical Missed-Train Rate (MTR) as `NOT_ESTIMABLE` on the current dataset due to left-censoring of 20/23 train arrivals?
6. **Table 11 Publication Framing:** Does the PI endorse publishing Table 11 as a qualified baseline with an explicit explanatory note stating that forward-causal duration is exactly $0.20\,\text{s}$ lower across all events?
7. **Incident F13-08 Closure:** Does the PI approve signing an administrative risk-acceptance memo closing Finding F13-08?

---

## 11. Statement of Non-Execution

In accordance with strict auditor boundaries:
- **No researcher decision was selected, adopted, approved, signed, or executed.**
- **No ground-truth review, adjudication, or promotion was performed.**
- **No execution authorization token (`EVAL-AUTH`, `AUTH-MEDIA-ACCESS`, `AUTH-CHECKPOINT-ACCESS`) was generated or issued.**
- **No source code, configuration file, test suite, manuscript draft, or governance record was modified.**
- **All findings, classifications, and recommendations presented in this report are strictly advisory.**

---

## 12. Git and Access-Boundary Integrity Report

### Baseline and Final Working Tree Status:
- **Git HEAD:** `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b` (Identical to baseline).
- **Tracked Modifications:** Exactly 25 modified tracked files preserved without alterations.
- **Untracked Porcelain Files:** Exactly 388 untracked files preserved without additions or deletions.
- **Staged Changes:** Exactly 0 files staged (`git diff --cached` is empty).
- **New Deliverable Created:** Exactly one file created:  
  [`docs/generated/master_reaudit/MISSION_16E_MASTER_DECISION_REGISTER_INDEPENDENT_CHALLENGE.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/master_reaudit/MISSION_16E_MASTER_DECISION_REGISTER_INDEPENDENT_CHALLENGE.md).

### Access-Boundary Compliance:
- Zero raw media files (`.mov`, `.mp4`, `.wav`, `.mp3`) were accessed or decoded.
- Zero production checkpoints (`best.pt`) were accessed or hashed.
- Zero protected cache files were opened.
- Zero execution gates were triggered.

---

## 13. Final Statutory Disposition

$$\mathbf{MASTER\_REGISTER\_REQUIRES\_MAJOR\_RESTRUCTURING}$$

### Formal Justification:
The original Master Researcher Decision Register cannot be safely presented to the Principal Investigator in its current form. It contains critical sequencing errors, relies on tools incapable of processing real data (`adjudication_session.py`), proposes locking an obsolete protocol that contradicts confirmed researcher directions, suggests scientifically invalid timestamp averaging, bundles operational controller parameters with an unvalidated simulation-artifact metric threshold, and conflates evaluation execution authority with raw media access permissions. Adopting the restructured dossier and the eight-stage governance sequence established in this report is mandatory prior to any human decision session.

---

REAL-DATA EXECUTION: NOT AUTHORIZED.
