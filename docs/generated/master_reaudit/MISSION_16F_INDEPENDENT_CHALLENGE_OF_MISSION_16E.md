# MISSION 16F: INDEPENDENT CHALLENGE OF MISSION 16E RECOMMENDATIONS AND GOVERNANCE DEPENDENCY SEQUENCE

**Project:** Train Gate Automation — Bangladesh  
**Mission:** 16F — Adversarial Audit of Mission 16E Governance Proposals, Security Models, and Mathematical Claims  
**Auditor:** Independent Principal Research, Security, Mathematical, and Governance Auditor  
**Audit Target:** Mission 16E Findings, Protocol v7.1.0-PROPOSED, ±0.10s Tolerance Proposal, EVAL-AUTH v1.1 Architecture, Adjudication Tooling, Eight-Stage Governance Sequence, Table 11 Mathematical Proof, Front-Camera Scope, and Corrected PI Dossier  
**Historical Baseline HEAD:** `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`  
**Execution Authority:** NONE — AUDITOR DOES NOT DECIDE, APPROVE, OR EXECUTE  
**Audit Mode:** STRICT READ-ONLY AUDIT  
**Date:** 2026-11-03  

---

## 1. Executive Verdict

This independent audit rigorously challenges the findings, proposed technical amendments, security architectures, mathematical proofs, and governance sequencing presented in Mission 16E ([`docs/generated/master_reaudit/MISSION_16E_MASTER_DECISION_REGISTER_INDEPENDENT_CHALLENGE.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/master_reaudit/MISSION_16E_MASTER_DECISION_REGISTER_INDEPENDENT_CHALLENGE.md)).

### Statutory Disposition:
$$\mathbf{MISSION\_16E\_RECOMMENDATIONS\_REQUIRE\_MAJOR\_REVISION}$$

### Executive Summary of Independent Findings:
1. **Ad-Hoc and Defective Tolerance Formulation (Challenge B):**  
   Mission 16E’s proposed temporal agreement tolerance of `±0.10 seconds / 3 frames at 30 fps` is mathematically and physically flawed:
   - It assumes a uniform 30 fps corpus, whereas primary manifest evidence ([`data/manifests/real_world_v2_video_manifest.jsonl`](file:///Users/sayemuddin/Desktop/Train_automation/data/manifests/real_world_v2_video_manifest.jsonl)) proves the back-camera corpus runs at **59.94 fps** for key events (where $\pm 0.10\,\text{s}$ equals 6 frames).
   - It ignores downstream controller discretization: at 5.0 Hz ($\Delta t = 0.20\,\text{s}$), a $\pm 0.10\,\text{s}$ human divergence can straddle a sampling boundary, inducing an entire 0.20s actuation tick shift.
   - It applies a single arbitrary threshold across physically disparate boundaries ($T_0$ optical haze vs $T_1$ rail switch frog vs $T_4$ vendor stall exit). Tolerance must not be adopted ad-hoc; it requires an empirical calibration pilot.
2. **Critical Security Blind Spots in EVAL-AUTH v1.1 (Challenge C):**  
   Mission 16E’s proposed token architecture contains severe security loopholes:
   - **The Working-Tree Bypass:** Binding a token strictly to `git commit` (HEAD SHA) checks only committed history. The active repository currently contains **25 modified tracked files and 388 untracked porcelain entries** (`VERIFIED_FROM_SAFE_SOURCE`). An evaluator could alter runtime logic without changing HEAD, and the token verification would pass. A token MUST bind to the working-tree tree hash (`git write-tree`) or require a clean working tree.
   - **Nonce Replay Vulnerability:** A UUIDv4 nonce stored in an unauthenticated local JSON file (`data/governance/revocations.json`) provides zero tamper resistance against the executing user and lacks atomic locking against concurrent multi-process replay.
3. **Valid Diagnosis but Incomplete Remediation of Adjudication Tooling (Challenge D):**  
   Mission 16E correctly proved that [`src/railway_detection/annotation/adjudication_session.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/annotation/adjudication_session.py) is hard-coded to reject real event IDs (`_require_synthetic_id`) and non-temp paths (`_require_temp_path`). However, Mission 16E failed to emphasize that these restrictions are **intentional security guards** protecting synthetic regression tests. The correct architectural path is **Option D2**: keep `adjudication_session.py` strictly for synthetic testing and author an independent human review runner (`human_review_session.py`).
4. **Conditional Proof of the Table 11 Timing Bound (Challenge F):**  
   The claim that $T_{\text{causal}} = T_{\text{Table 11}} - 0.20\,\text{s}$ across all 27 events is mathematically valid **only conditional upon**:
   - Strictly uniform sampling cadence ($\Delta t_i = 0.2000\,\text{s}$). If sampling jitter occurs, the start lead and unblocking delay do not cancel, and forward-causal duration can exceed retroactive duration ($\Delta T > 0$).
   - Terminal recording blockage ($\theta \le 45.0^\circ$). If an event completed its opening cycle, $\Delta T = 0.00\,\text{s}$.
   While timeline inspection confirms that Condition B4 met both conditions historically, Mission 16E stated this correction as an unconditional property of discrete simulation, which is mathematically overgeneralized.
5. **Over-Coupled Governance Sequence (Challenge E):**  
   Mission 16E’s eight-stage sequence introduced artificial bottlenecks. Stage 0 bundled protocol adoption, administrative incident closure (F13-08), and manuscript authorship into a single gate. Furthermore, Stage 2 coupled model checkpoint policy (F13-09) to human annotation tooling, despite model weights being completely irrelevant to human video review. A decoupled, capability-oriented sequence is required.

---

## 2. Audit Scope and Authority

- **Role:** Independent Principal Research, Security, Mathematical, and Governance Auditor.
- **Authority:** Strictly advisory. The auditor possesses **zero execution authority**, **zero research authorization**, and **zero governance authority**. No decision is approved, no schema is altered, no token is issued, and no code is committed.
- **Boundary Adherence:**
  - Zero raw media files (`.mov`, `.mp4`, `.wav`, `.mp3`) were decoded, previewed, or hashed (`VERIFIED_FROM_SAFE_SOURCE`).
  - Zero checkpoint weights (`best.pt`) were read or hashed (`VERIFIED_FROM_SAFE_SOURCE`).
  - Zero real-data evaluations, simulations, or training runs were executed (`VERIFIED_FROM_SAFE_SOURCE`).
  - Git state remains identical to baseline HEAD `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b` with 25 modified and 388 untracked files preserved (`VERIFIED_FROM_SAFE_SOURCE`).

---

## 3. Evidence Classification and Limitations

Every finding in this report is classified under strict evidentiary standards:
- `VERIFIED_FROM_SAFE_SOURCE`: Established directly from permitted Python code, configuration, or text metadata.
- `REPORTED_BY_MISSION_16E`: Asserted by Mission 16E, subjected here to independent challenge.
- `REPORTED_BY_PRIOR_AUDIT`: Documented in historical audit reports (Missions 1–16D).
- `INDEPENDENT_MATHEMATICAL_DERIVATION`: Formally proven by mathematical analysis under stated assumptions.
- `INFERENCE`: Logical conclusion deduced from verified technical evidence.
- `REQUIRES_HUMAN_CONFIRMATION`: Governance policy or domain choice reserved exclusively for the Principal Investigator.
- `NOT_VERIFIABLE_WITH_CURRENT_AUTHORITY`: Operation crossing safety boundaries.

---

## 4. Challenge A — Protocol v7.1.0 Proposal and Researcher-Direction Consistency

Mission 16E recommended promoting [`docs/generated/mission_5a/FINAL_GROUND_TRUTH_PROTOCOL_v7.1.0_PROPOSED.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/mission_5a/FINAL_GROUND_TRUTH_PROTOCOL_v7.1.0_PROPOSED.md) to replace in-place [`docs/FINAL_GROUND_TRUTH_PROTOCOL.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/FINAL_GROUND_TRUTH_PROTOCOL.md) (v7.0.0).

### 4.1 Requirement-by-Requirement Audit Matrix (RD-001 through RD-013)

| Requirement / Direction | v7.0.0 Status (In-Place) | v7.1.0-PROPOSED Status | Compliance Verdict | Evidentiary Basis |
| :--- | :--- | :--- | :--- | :--- |
| **RD-001 (Document Authority)** | Treats design doc as binding | States design doc non-binding; v7 for boundaries, v9 for metrics | **`COMPLIANT`** | §1, §6 (`VERIFIED_FROM_SAFE_SOURCE`) |
| **RD-002 (Wording Before Hash)** | Unbound; contains errors | Proposed wording drafted before cryptographic hash binding | **`COMPLIANT`** | Header banner (`VERIFIED_FROM_SAFE_SOURCE`) |
| **RD-004 ($T_1$ Approach Landmark)** | Vague danger zone entry | Explicitly defines turnout switch frog casting / pedestrian line | **`COMPLIANT`** | §2.1, §2.4 (`VERIFIED_FROM_SAFE_SOURCE`) |
| **RD-005 ($T_2$ Roadway Entry Boundary)**| Camera lens transverse plane | Leading end crosses physical roadway entry boundary | **`COMPLIANT`** | §2.1, §2.4 (`VERIFIED_FROM_SAFE_SOURCE`) |
| **RD-006 (Entry Landmark Deferral)** | Assumed camera plane | Explicitly **`DEFERRED`**; CCA defined without invented entry landmark | **`COMPLIANT`** | §2.1, §2.5 (`VERIFIED_FROM_SAFE_SOURCE`) |
| **RD-007 (`T_OCC_START` Alias)** | Used interchangeably | Prose alias only permitted after RD-005 + RD-006 resolved | **`COMPLIANT`** | §2.1 notes (`VERIFIED_FROM_SAFE_SOURCE`) |
| **RD-008 (M4/M5 Metric Terminology)** | Defines POR via $t \in [T_1, T_4]$ | Replaces $T_1$ POR with M4/M5 references; wraps old text in `<!--HISTORICAL-->` | **`COMPLIANT`** | §2.2 (`VERIFIED_FROM_SAFE_SOURCE`) |
| **RD-009 (Governance Identifiers)** | Uses ambiguous D-1..D-11 | Adopts GOV-, EXP-, AUTH- canonical identifiers | **`COMPLIANT`** | Document aliases (`VERIFIED_FROM_SAFE_SOURCE`) |
| **RD-010 (Travel Direction per Event)**| Inferred from candidate | Explicitly required to be verified per event under future review | **`COMPLIANT`** | §2.4 4a (`VERIFIED_FROM_SAFE_SOURCE`) |
| **RD-011 (Censoring Exclusions)** | Formula heuristics | Excludes censored events from point estimates; counts reasons | **`COMPLIANT`** | §2.4 4a (`VERIFIED_FROM_SAFE_SOURCE`) |
| **RD-012 (Review Tolerance Deferral)** | Unaddressed | Explicitly marked **`DEFERRED`**; does not invent ad-hoc value | **`COMPLIANT`** | Header, §2.4 4a (`VERIFIED_FROM_SAFE_SOURCE`) |
| **RD-013 (Blind Pilot Review)** | Unaddressed | Enforces blind first-pass review for $T_1, T_2, T_4$ | **`COMPLIANT`** | §2.4 4a (`VERIFIED_FROM_SAFE_SOURCE`) |

### 4.2 Detailed Findings on Challenge A:
1. **Preservation of Non-Authority:** The header of `v7.1.0_PROPOSED.md` explicitly preserves governance non-authority: `PROPOSED — NOT APPROVED — NOT AUTHORIZED... D1 is selected by the researcher but not bound` (`VERIFIED_FROM_SAFE_SOURCE`).
2. **No Invented Physical Landmarks:** The document explicitly avoids creating an unverified entry landmark for $T_2$ (§2.5: *"Only the exit plane is documented. The entry landmark is DEFERRED (RD-006)... Until the researcher states it, T2 and any duration anchored on it remain unevaluable"*).
3. **Schema Compatibility:** The proposed boundaries match [`src/railway_detection/annotation/schemas.py:28-35`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/annotation/schemas.py#L28-L35) (`CANONICAL_TIMESTAMPS`) and [`src/railway_detection/annotation/stage2_1_schema.py:33`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/annotation/stage2_1_schema.py#L33) (`STAGE_2_1_SCHEMA_VERSION = "8.1.0-stage2.1"`).
4. **Resolution of POR Contradiction:** v7.0.0 contained a fatal scientific contradiction: it defined Premature Opening as gate ascent while $t \in [T_1, T_4]$. But $T_1$ occurs well before gate closure; evaluating POR from $T_1$ would count normal open gates before train arrival as premature openings! v7.1.0-PROPOSED correctly points to M4/M5 (`first_blocked_to_t4_clearance`).
5. **Verdict on Challenge A:** Mission 16E’s recommendation to adopt `v7.1.0_PROPOSED.md` over v7.0.0 is **independently confirmed** as technically and methodologically sound.

---

## 5. Challenge B — Second-Review Temporal Agreement Tolerance

Mission 16E proposed an operational agreement tolerance of `±0.10 seconds / 3 frames at 30 fps`. This independent challenge audits the mathematical, sensor, and empirical defensibility of that proposal.

### 5.1 Mathematical and Video Timing Analysis
1. **Heterogeneous Frame Rates:**  
   Primary manifest inspection of [`data/manifests/real_world_v2_video_manifest.jsonl`](file:///Users/sayemuddin/Desktop/Train_automation/data/manifests/real_world_v2_video_manifest.jsonl) establishes:
   - Front camera (`camera_front.mov`): $29.97\,\text{fps}$ ($\Delta t_{\text{frame}} \approx 33.367\,\text{ms}$). A 3-frame window corresponds to $3 \times 33.367\,\text{ms} = 100.1\,\text{ms} \approx 0.100\,\text{s}$.
   - Back camera (`camera_back.mov`): `event_001` runs at **$59.94\,\text{fps}$** ($\Delta t_{\text{frame}} \approx 16.683\,\text{ms}$), while `event_002` runs at $30.00\,\text{fps}$.
   - At $59.94\,\text{fps}$, a $\pm 0.10\,\text{s}$ window encompasses **6 frames**, not 3 frames! Calling this "3 frames at 30 fps" is an incorrect characterization of the corpus (`INDEPENDENT_MATHEMATICAL_DERIVATION`).
2. **Coupling to Controller Sampling Cadence (5.0 Hz):**  
   The crossing decision policy runs on a discrete grid with `timing_tick_s = 0.2` (5.0 Hz).  
   Consider two human reviewers whose annotations differ by $0.08\,\text{s}$ (within the proposed $\pm 0.10\,\text{s}$ tolerance):
   - Reviewer 1 marks $T_1 = 1.95\,\text{s}$ (sampled by controller at tick $t = 2.0\,\text{s}$).
   - Reviewer 2 marks $T_1 = 2.03\,\text{s}$ (sampled by controller at tick $t = 2.2\,\text{s}$).
   Although human observers agreed within tolerance, the downstream discrete simulation steps an entire tick later ($+0.20\,\text{s}$ shift), altering warning lead time calculations (`INDEPENDENT_MATHEMATICAL_DERIVATION`).
3. **Physical Heterogeneity of Boundary Visuals:**  
   - **$T_0$ (First Visual Appearance):** Locomotive emerges from distant heat shimmer and track curve. Inter-rater variance across human observers is naturally high ($\sigma \approx 0.3\,\text{s} - 0.8\,\text{s}$). A $\pm 0.10\,\text{s}$ tolerance would force virtually all $T_0$ observations into adjudication.
   - **$T_1$ (Frog Switch Line):** Sharp geometric rail landmark on high-contrast foreground track. Inter-rater variance is low ($\sigma \approx 1 - 2$ frames, $\approx 0.03\,\text{s} - 0.07\,\text{s}$).
   - **$T_4$ (Tail Clearance):** High-speed departure across vendor stall line. High optical motion blur on trailing coupler.
4. **Interval Overlap vs Symmetric Absolute Difference:**  
   If Reviewer 1 specifies $t_1$ and Reviewer 2 specifies $t_2$, and $|t_1 - t_2| \le 0.10\,\text{s}$, which value is promoted to ground truth?
   - Selecting $t_1$ arbitrarily introduces primary-reviewer bias.
   - Averaging $(t_1 + t_2) / 2$ was already refuted in Mission 16E (creates an unobserved synthetic timestamp).
   - The scientifically robust representation is an **observation interval** $[t_{\min}, t_{\max}]$ with primary reference to the lead observation.

### 5.2 Recommendation on Challenge B:
$$\mathbf{REJECT\ UNILATERAL\ \pm 0.10s\ TOLERANCE}$$
- The Principal Investigator must **not** adopt $\pm 0.10\,\text{s}$ as a hard rule.
- **Interim Standard:** Retain strict equality with mandatory adjudication for discrepancies, OR adopt an explicit boundary-specific provisional tolerance:
  - $T_0$: $\pm 0.30\,\text{s}$ (optical approach uncertainty).
  - $T_1, T_3, T_4$: $\pm 2$ native video frames (frame-quantized: $\approx \pm 0.067\,\text{s}$ at 29.97 fps, $\approx \pm 0.033\,\text{s}$ at 59.94 fps).
- Ground truth must record the primary human observation, the second reviewer observation, and the resolution record independently.

---

## 6. Challenge C — EVAL-AUTH v1.1 Security Architecture Threat Modeling

Mission 16E proposed upgrading `EVAL-AUTH` to v1.1 with UUIDv4 nonces, a 4-hour lease, Git commit binding, and a local revocation ledger (`data/governance/revocations.json`).

### 6.1 Threat Model and Adversarial Analysis

| Threat # | Attack Vector / Scenario | Mission 16E Proposed Defense | Vulnerability / Gap Identified | Severity | Required Architectural Control |
| :---: | :--- | :--- | :--- | :---: | :--- |
| **T-01** | **Working-Tree Logic Tampering** | Binds token to Git commit hash (HEAD SHA) | **CRITICAL FLAW:** Repository has 25 modified tracked files and 388 untracked files. Code can be altered without changing HEAD! | **HIGH** | Bind token to `git write-tree` (working-tree state hash) or enforce `git status --porcelain == 0`. |
| **T-02** | **Token Replay (Same Machine)** | UUIDv4 nonce in token JSON | Evaluator reads JSON; has no persistent memory of used nonces without stateful locking | **HIGH** | Atomic append to an append-only consumed-nonce ledger with file lock (`fcntl.flock`). |
| **T-03** | **Concurrent Replay / TOCTOU** | Single-run statement | Two parallel processes read token simultaneously before either records consumption | **MED** | File-system mutex lock during token validation and consumption recording. |
| **T-04** | **Clock Rollback** | 4-hour UTC validity window | System clock manipulated backwards to revive expired token | **MED** | Monotonic time checking against filesystem timestamps and commit dates. |
| **T-05** | **Revocation Ledger Deletion** | Check `revocations.json` | Local user/process can delete or truncate `revocations.json` | **HIGH** | Gate fails closed if ledger is missing or older than repo baseline; verify SHA-256 chain. |
| **T-06** | **Token Theft / Cross-Machine** | Attestation string | Token file copied to another machine and executed against cloned data | **LOW** | Bind token to local machine identity (e.g. MAC / hardware UUID hash). |
| **T-07** | **Environment Token Leakage** | In-memory context | Subprocess calls, shell wrappers, or crash logs export environment variables | **LOW** | Pass context strictly as in-memory Python object; forbid `os.environ` passing. |
| **T-08** | **Partial Execution Crash** | Token consumed on start | Process crashes after 3 events; token is burned, blocking completion | **MED** | Support idempotent session resume bound to same run nonce and output directory. |
| **T-09** | **Unsigned Attestation Spoofing**| `ATTESTATION_RECORDED_STATEMENT` | Any script can write a JSON file asserting `authorized_by: raihankabirrahu@gmail.com` | **HIGH** | Without asymmetric PKI, authorization relies entirely on file permission boundaries. |

### 6.2 Key Security Findings on Challenge C:
1. **The Uncommitted Working Tree Vulnerability:**  
   In `src/railway_detection/evaluation/execution_gate.py:948-973`, checking `git rev-parse HEAD` is insufficient when 25 modified tracked files exist. A researcher token bound to HEAD `d4db94d...` does not protect against modified simulation code in the working tree. The token must cryptographically bind the working tree hash (`git write-tree`) or require a clean tree (`VERIFIED_FROM_SAFE_SOURCE`).
2. **Local PKI Reality:**  
   As proven in [`src/railway_detection/evaluation/governance.py:494`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/evaluation/governance.py#L494), the repository contains zero signature or key infrastructure. While full PKI is excessive for a local single-user research repository, relying on an unsigned JSON statement creates zero cryptographic authenticity.
3. **Verdict on Challenge C:**  
   Mission 16E’s v1.1 proposal is **inadequate** without working-tree state binding and atomic nonce consumption locking.

---

## 7. Challenge D — Human Adjudication Tool Architecture

Mission 16E reported that [`src/railway_detection/annotation/adjudication_session.py`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/annotation/adjudication_session.py) cannot process real events due to synthetic ID and temp-path assertions.

### 7.1 Independent Code Verification
Direct inspection of `src/railway_detection/annotation/adjudication_session.py` lines 126–142 establishes:
```python
def _require_synthetic_id(event_id: str) -> None:
  """This implementation is deliberately incapable of real-event review."""
  if not isinstance(event_id, str) or not re.fullmatch(
      r"synthetic_[A-Za-z0-9_-]+", event_id
  ):
    raise EventNotInManifestError(
        "Synthetic-only runner requires an event_id beginning with"
        " 'synthetic_'."
    )


def _require_temp_path(path: Path | str, *, label: str) -> Path:
  """Resolve a path and require it to stay inside the OS temporary directory."""
  resolved = Path(path).expanduser().resolve()
  temp_root = Path(tempfile.gettempdir()).resolve()
  if not resolved.is_relative_to(temp_root):
    raise AdjudicationSessionError(
        f"SYNTHETIC_ONLY_PATH_REQUIRED: {label} must resolve beneath {temp_root}"
    )
  return resolved
```
1. **Code Behavior Verified:** Calling `adjudication_session.py` against `train_events_001` or any real repository video path unconditionally raises `EventNotInManifestError` or `AdjudicationSessionError` (`VERIFIED_FROM_SAFE_SOURCE`).
2. **Design Intent Verified:** Lines 20–24 explicitly state: *"Authorization boundary: this module is intentionally synthetic-only. It rejects non-synthetic event IDs and media/output paths outside the OS temporary directory, so it cannot be used for genuine adjudication. It never calls promote_record"* (`VERIFIED_FROM_SAFE_SOURCE`).

### 7.2 Architectural Evaluation of Remediation Options

- **Option D1 (Modify `adjudication_session.py` directly):**  
  *Critique:* **REJECTED**. Modifying this file to accept real paths strips away the intentional tripwires protecting synthetic tests and regression suites.
- **Option D2 (Dedicated Human Review CLI — `human_review_session.py`):**  
  *Critique:* **RECOMMENDED**. Create a clean, separate, human-operated CLI tool designed specifically for interactive human adjudication. It enforces reviewer allowlisting (`authorized_reviewers.json`), requires an active `AUTH-MEDIA-ACCESS (REVIEW)` token, computes live media hashes, presents blind candidate boundaries, and writes immutable Stage-2.1 review records directly to `data/ground_truth/reviews/`.
- **Option D3 (Shared Schema with Execution Adapters):**  
  *Critique:* Both tools should import shared data structures from `stage2_1_schema.py` while maintaining strict isolation of execution runtimes.

---

## 8. Challenge E — Eight-Stage Governance Dependency Audit

Mission 16E proposed an eight-stage sequential governance plan. This audit tests every dependency for circularity, over-coupling, and missing prerequisites.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ GOVERNANCE STAGE DECOUPLING AND CRITICAL PATH AUDIT                         │
├─────────────────────────────────────────────────────────────────────────────┤
│ MISSION 16E PROPOSAL                        INDEPENDENT AUDIT VERDICT       │
│                                                                             │
│ Stage 0: Protocol v7.1 + M12 + Authorship ──► OVER-COUPLED: Decouple M12   │
│ Stage 1: Reviewer Gov & Calibration ────────► DEFECTIVE: Tolerance ad-hoc   │
│ Stage 2: Security & Review Tooling ─────────► MISORDERED: Checkpoint unneeded│
│ Stage 3: Human Review Execution ────────────► VALID: Needs scoped token     │
│ Stage 4: GT Promotion ──────────────────────► VALID: Batch sign-off needed  │
│ Stage 5: Simulation Causality Remediation ──► CRITICAL: Forward stepping    │
│ Stage 6: Descriptive Benchmark Replay ──────► VALID: Front-camera caches    │
│ Stage 7: Manuscript Finalization ───────────► VALID: Non-computable POR     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 8.1 Detailed Stage Dependency Critique:
1. **Stage 0 Over-Coupling:**  
   Mission 16E bundled Protocol v7.1.0 adoption, Mission 12 Incident F13-08 closure, and Manuscript Authorship into Stage 0.  
   *Audit Finding:* Protocol adoption is a prerequisite for human review; closing Incident F13-08 is an administrative risk memo; authorship is an editorial task. Coupling them means that if the PI has questions regarding the incident memo, protocol adoption is blocked. They must be split into independent governance tracks.
2. **Stage 2 Checkpoint Security Misordering:**  
   Mission 16E placed checkpoint hashing policy (F13-09) in Stage 2 prior to human annotation (Stage 3).  
   *Audit Finding:* Human annotators inspect video to determine ground truth timestamps ($T_0 - T_4$). They do not load, run, or evaluate neural network checkpoints! Checkpoint policy (F13-09) is completely irrelevant to Stage 3 and belongs immediately before Stage 6 (Benchmark Replay).
3. **Stage 3 Scope and Cohort Integrity:**  
   The 27 active events consist of: 23 full trains, 3 no-train negatives, and 1 engine-only event (`VERIFIED_FROM_SAFE_SOURCE`).  
   Under `RD-026`, dual-camera exploratory analysis is frozen to 11 events; `event_010` is excluded from dual-camera analysis. Stage 3 must explicitly enforce that only front-camera annotations are required for the primary benchmark, with back-camera annotations scoped to clearance exit planes ($T_3, T_4$).

---

## 9. Challenge F — Table 11 Independent Mathematical Challenge

Mission 16E concluded that historical Table 11 closed duration satisfies:
$$T_{\text{causal}} = T_{\text{Table 11}} - 0.2000\,\text{s} \quad (\forall \, i \in \{1, \dots, 27\})$$
This independent audit challenges whether this theorem is universally proven or conditional.

### 9.1 Mathematical Formulation of the Simulation Stepping Problem
Let simulation timestamps be $t_0, t_1, \dots, t_N$ with step intervals $\Delta t_i = t_i - t_{i-1}$.  
Let the crossing decision engine issue commanded state $u_i \in \{\text{OPEN}, \text{CLOSING}, \text{CLOSED}, \text{OPENING}\}$ at step $i$.  
Gate angle $\theta_i$ evolves at linear angular velocity $\dot{\theta} = \pm 30.0^\circ/\text{s}$.  
Passage is blocked when $\theta_i \le 45.0^\circ$.  
The accumulator in [`src/railway_detection/simulation/runner.py:232-233`](file:///Users/sayemuddin/Desktop/Train_automation/src/railway_detection/simulation/runner.py#L232-L233) evaluates:
$$T_{\text{closed}} = \sum_{i=1}^N \Delta t_i \cdot \mathbf{1}_{\{\theta_i \le 45.0^\circ\}}$$

- **Convention A (Retroactive Stepping):** At step $i$, decision engine evaluates frame at $t_i$, issuing $u_i$. Physical gate steps over $[t_{i-1}, t_i]$ using $u_i$. Accumulator evaluates $\theta_i \le 45^\circ$ and adds $\Delta t_i$.
- **Convention B (Forward-Causal Stepping):** At step $i$, command $u_i$ applies strictly to the forward interval $[t_i, t_{i+1}]$. Motion during $[t_{i-1}, t_i]$ was governed by previous command $u_{i-1}$.

### 9.2 Derivation Across the Twelve Boundary Conditions

1. **Complete Cycle (Descent, Blocked, Ascent, Unblocked before $t_N$):**  
   - Start of blockage: Convention A reaches $\le 45^\circ$ at step $k_{\text{close}} + \lceil 45 / (30 \Delta t) \rceil - 1$. Convention B reaches it at $k_{\text{close}} + \lceil 45 / (30 \Delta t) \rceil$.  
     Shift at onset: $k_{\text{block}}^{\text{B}} - k_{\text{block}}^{\text{A}} = +1$ tick.
   - Unblocking: Gate begins opening at $k_{\text{open}}$. By exact symmetry of $|\dot{\theta}_{\text{open}}| = |\dot{\theta}_{\text{close}}| = 30.0^\circ/\text{s}$, Convention A unblocks ($\theta > 45^\circ$) at $k_{\text{open}} + \lceil 45 / (30 \Delta t) \rceil - 1$, and Convention B unblocks at $k_{\text{open}} + \lceil 45 / (30 \Delta t) \rceil$.  
     Shift at unblocking: $k_{\text{unblock}}^{\text{B}} - k_{\text{unblock}}^{\text{A}} = +1$ tick.
   - Net duration: $\Delta T = (t_{\text{unblock}}^{\text{B}} - t_{\text{block}}^{\text{B}}) - (t_{\text{unblock}}^{\text{A}} - t_{\text{block}}^{\text{A}}) = (1 - 1) \Delta t = \mathbf{0.00\,\text{s}}$.
2. **Terminal Blocked Episode (Recording terminates while $\theta_N \le 45.0^\circ$):**  
   - Both conventions accumulate all ticks up to $N$.  
   - Convention A accumulated step $k_{\text{block}}^{\text{A}}$; Convention B did not.  
   - Net duration: $\Delta T = T_{\text{causal}} - T_{\text{retro}} = -\Delta t = \mathbf{-0.2000\,\text{s}}$ (at 5.0 Hz).
3. **Multiple Complete Episodes:**  
   - Sum of zero-delta episodes: $\sum 0.00\,\text{s} = \mathbf{0.00\,\text{s}}$.
4. **Multiple Complete Episodes + Terminal Blocked Episode:**  
   - Sum = $0.00\,\text{s} + (-\Delta t) = \mathbf{-0.2000\,\text{s}}$.
5. **Clip Ending at Exact Blockage Transition Step:**  
   - If clip ends at step $k_{\text{block}}^{\text{A}}$: Convention A has $\theta \le 45^\circ$ (accumulates $\Delta t$). Convention B has $\theta = 48.0^\circ > 45^\circ$ (accumulates $0$).  
   - Net duration: $0 - \Delta t = \mathbf{-0.2000\,\text{s}}$.
6. **Clip Ending Immediately Before Blockage:**  
   - Neither convention accumulated closed time. $\Delta T = \mathbf{0.00\,\text{s}}$.
7. **Irregular Time Intervals ($\Delta t_i \ne \text{const}$):**  
   - Let onset step have interval $\Delta t_{\text{start}}$ and unblocking step have interval $\Delta t_{\text{end}}$.  
   - $\Delta T = \Delta t_{\text{start}} - \Delta t_{\text{end}}$.  
   - If $\Delta t_{\text{start}} > \Delta t_{\text{end}}$, $\Delta T > 0$! Forward-causal closed duration is **greater** than retroactive closed duration!  
   - *Crucial Finding:* The one-sided bound $[T - 0.20\,\text{s}, T]$ is **violated** if sampling intervals are irregular (`INDEPENDENT_MATHEMATICAL_DERIVATION`).
8. **Missing Frames / Jitter:**  
   - If frame drop occurs during transition, $\Delta t$ expands, perturbing the cancellation.
9. **Duplicate Timestamps:**  
   - Filtered by Rule 10 without advancing gate model; does not alter duration.
10. **Non-Monotonic Timestamps:**  
    - Filtered by Rule 8; clock does not advance.
11. **Threshold-Crossing Interpolation:**  
    - Code uses step-discrete accumulation, not continuous root-finding interpolation.
12. **Floating-Point Boundaries:**  
    - At 5.0 Hz, $\Delta \theta = 30.0 \times 0.2 = 6.0^\circ$. Angles are exact integers ($90, 84, \dots, 48, 42^\circ$). $42.0 \le 45.0$ is exact in IEEE 754.

### 9.3 Empirical Verification vs Mathematical Generalization
- **Empirical Reality of Table 11:** Inspection of [`results/experiments/B4/timelines/`](file:///Users/sayemuddin/Desktop/Train_automation/results/experiments/B4/timelines/) and [`results/experiments/phase5_full_dataset_run_20261013/frozen_config_meta.json`](file:///Users/sayemuddin/Desktop/Train_automation/results/experiments/phase5_full_dataset_run_20261013/frozen_config_meta.json) confirms that for the historical B4 run, **$\Delta t = 0.2000\,\text{s}$ was 100% strictly uniform** and **all 27 events ended while blocked**.  
- **Conclusion:** The exact $-0.2000\,\text{s}$ correction is **empirically true for Table 11**, but it is **not a universal mathematical law** for arbitrary simulations. Mission 16E’s theorem is confirmed **with explicit conditionality**.

---

## 10. Challenge G — Front-Camera-Only Benchmark Scope

Mission 16E recommended officially scoping the descriptive benchmark to front-camera conditions (`B0`, `B1`, `B2`), closing back-stream cache gap `M-03` for the Version 1.0 manuscript.

### 10.1 Condition and Scope Reconciliation Matrix

| Condition | Modalities / Camera | Historical Replay Status | Primary Benchmark Eligibility | Relation to RD Directions |
| :--- | :--- | :--- | :--- | :--- |
| **B0** | Front Vision Only | Verified in `cache_only_engine.py` | **`ELIGIBLE (PRIMARY)`** | Aligns with `RD-015`, `RD-028` (independent camera) |
| **B1** | Front Audio Only | Verified in `cache_only_engine.py` | **`ELIGIBLE (EXPLORATORY)`** | Aligns with `RD-030` (audio supporting only; cannot actuate gate) |
| **B2** | Front Vision + Audio | Verified in `cache_only_engine.py` | **`ELIGIBLE (PRIMARY)`** | Aligns with `RD-035`, RQ1 (multimodal approach fusion) |
| **B0_back**| Back Vision Only | **Refused** (`cache_only_engine.py:77`) | **`INELIGIBLE (NO CACHES)`** | Back-stream feature caches do not exist (`M-03`) |
| **B2_back**| Back Vision + Audio | **Refused** (`cache_only_engine.py:77`) | **`INELIGIBLE (NO CACHES)`** | Back-stream feature caches do not exist (`M-03`) |
| **B3 / B4**| Dual-Camera Fusion | **Refused** (R04 uncalibrated) | **`INELIGIBLE (EXPLORATORY)`**| `RD-026` limits R04 to 11 events; `event_010` excluded |

### 10.2 Scientific Coherence of the Front-Camera Scope:
1. **Research Question Alignment:** The core research questions of the manuscript (RQ1: Does multimodal fusion improve detection reliability over unimodal vision? RQ2: Does acoustic sensing provide advance warning lead time?) are evaluated entirely at the **approach danger zone ($T_1$)**, which is observed exclusively on `camera_front.mov`.
2. **Clearance Latency Separation:** Tail clearance ($T_4$) and Premature Opening ($M4$) require the rear camera departure plane. Because historical real-data runs have $T_4 = \text{null}$ and yield non-computable $M4$, attempting to force back-stream replay into Version 1.0 adds zero computable safety metrics while introducing unverified cache risks.
3. **Verdict on Challenge G:** Scoping Version 1.0 of the descriptive benchmark to front-camera conditions (`B0`, `B1`, `B2`) is **independently confirmed** as the only scientifically defensible and reproducible path.

---

## 11. Corrected Principal Investigator Decision Dossier

The auditor provides this corrected, internally consistent dossier across all 13 decisions.

### Classification Summary:
- `DECISION_READY_FOR_PI`: **2** (Decisions 9, 12)
- `DECISION_READY_WITH_CONDITIONS`: **4** (Decisions 3, 4, 10, 11)
- `FURTHER_EVIDENCE_REQUIRED`: **2** (Decisions 6, 8)
- `OPTIONS_INADEQUATE`: **4** (Decisions 1, 2, 5, 7)
- `DEFERRED_PENDING_OTHER_GATE`: **1** (Decision 13)

---

### Detailed Decision Sheets:

#### Decision 1: Checkpoint Integrity Hashing (F13-09)
- **Status:** `OPTIONS_INADEQUATE`
- **Corrected Framing:** Shall checkpoint integrity verification be separated into: (1) Static preflight check against signed manifest metadata without byte reads, and (2) Runtime full SHA-256 byte verification executed immediately prior to inference under an explicit `AUTH-CHECKPOINT-ACCESS` token?
- **Recommended Option:** Option 1-R1 (Two-phase verification with explicit capability token).
- **Prerequisites:** Decision 13 token decomposition.

#### Decision 2: EVAL-AUTH Token Lifecycle & Revocation (F13-10)
- **Status:** `OPTIONS_INADEQUATE`
- **Corrected Framing:** Shall `EVAL-AUTH` v1.1 enforce a UUIDv4 nonce, 4-hour lease window, working-tree state hash binding (`git write-tree`), and atomic file locking against `data/governance/revocations.json`, without external PKI?
- **Recommended Option:** Option 2-R1 (Stateful nonce ledger with working-tree binding).
- **Prerequisites:** Implementation of atomic locking in `execution_gate.py`.

#### Decision 3: Descriptive Back-Stream Cache Route (M-03)
- **Status:** `DECISION_READY_WITH_CONDITIONS`
- **Corrected Framing:** Shall the official descriptive benchmark replay be scoped exclusively to front-camera conditions (`B0`, `B1`, `B2`) where validated static feature caches exist, formally deferring dual-camera back-stream replay (`M-03`) to Version 2.0?
- **Recommended Option:** Option 3-R1 (Adopt front-camera primary scope; close M-03 as deferred).
- **Conditions:** Explicit disclosure in manuscript that clearance metrics ($T_4$, $M4$, $M5$) are deferred.

#### Decision 4: Process Context Token Binding (F13-15)
- **Status:** `DECISION_READY_WITH_CONDITIONS`
- **Corrected Framing:** Shall evaluation execution be strictly confined to a single synchronous Python process, passing the verified authorization context object directly via in-memory function parameters?
- **Recommended Option:** Option 4A (Single-process synchronous execution).
- **Conditions:** Disallow environment-variable fallback.

#### Decision 5: State Machine Bounds & MTR Feasibility (DEC-B05)
- **Status:** `OPTIONS_INADEQUATE`
- **Corrected Framing:** Shall the PI split DEC-B05 into: (a) DEC-B05a: Freeze controller parameters (2-frame optical, 5.0s acoustic dwell, 2.0s staleness) as heuristic design constants; and (b) DEC-B05b: Classify physical MTR as `NOT_ESTIMABLE` due to 20/23 left-censored approaches, reporting 3.6s strictly as an implementation-derived latency?
- **Recommended Option:** Option 5-R1 (Split and adopt DEC-B05a and DEC-B05b).

#### Decision 6: Second-Review Agreement Tolerance (RD-012 / RD-043)
- **Status:** `FURTHER_EVIDENCE_REQUIRED`
- **Corrected Framing:** Shall the PI reject the arbitrary $\pm 0.10\,\text{s}$ tolerance and instead authorize a controlled human calibration pilot on training events to determine empirical inter-reviewer variance across 29.97 fps and 59.94 fps streams?
- **Recommended Option:** Option 6-R1 (Authorize calibration pilot to establish empirical tolerance).
- **Prerequisites:** Second reviewer appointment (Decision 8).

#### Decision 7: Disagreement Resolution Protocol (RD-045)
- **Status:** `OPTIONS_INADEQUATE`
- **Corrected Framing:** Shall boundary disagreements be resolved exclusively through an append-only Lead Researcher adjudication record (leaving unresolved disputes as `UNCERTAIN`), while formally rejecting arithmetic timestamp averaging?
- **Recommended Option:** Option 7-R1 (Adopt RD-045 append-only adjudication; reject averaging).
- **Prerequisites:** Schema implementation in `stage2_1_schema.py`.

#### Decision 8: Authorized Human Reviewer Appointment
- **Status:** `FURTHER_EVIDENCE_REQUIRED`
- **Corrected Framing:** Shall the PI nominate an independent, qualified second human reviewer and submit their CV, domain qualifications, and conflict-of-interest disclosure for allowlist expansion?
- **Required Evidence:** Reviewer nomination dossier and calibration test records.

#### Decision 9: Protocol and Schema Version Binding
- **Status:** `DECISION_READY_FOR_PI`
- **Corrected Framing:** Shall the PI promote `FINAL_GROUND_TRUTH_PROTOCOL_v7.1.0_PROPOSED.md` to become canonical in-place `FINAL_GROUND_TRUTH_PROTOCOL.md` and cryptographically bind its SHA-256 digest alongside Schema v8.1.0-stage2.1?
- **Recommended Option:** Option 9-R1 (Promote v7.1.0 and bind SHA-256).

#### Decision 10: Stage-2.1 Promotion Gate Authorization
- **Status:** `DECISION_READY_WITH_CONDITIONS`
- **Corrected Framing:** Shall `promotion_gate.py` be authorized to execute under batch-level human researcher sign-off, utilizing a scoped, single-use `AUTH-MEDIA-ACCESS (PROMOTION)` permit?
- **Recommended Option:** Option 10-R1 (Batch human sign-off with single-use promotion permit).
- **Conditions:** Zero unresolved disputes; all second reviews completed.

#### Decision 11: Mission 12 Incident Administrative Review (F13-08)
- **Status:** `DECISION_READY_WITH_CONDITIONS`
- **Corrected Framing:** Shall the PI sign an administrative review memo closing Incident F13-08 based on formal risk acceptance (acknowledging that historical test execution occurred, that retrospective byte access cannot be proven or disproven, and that current fail-closed guards prevent recurrence)?
- **Recommended Option:** Option 11-R1 (Sign administrative risk acceptance memo).

#### Decision 12: Manuscript Authorship and AI Attribution (RD-054)
- **Status:** `DECISION_READY_FOR_PI`
- **Corrected Framing:** Shall the manuscript authorship block be updated immediately to list human researchers as sole authors in compliance with COPE/IEEE guidelines, accompanied by a comprehensive Generative AI Disclosure in the Acknowledgments?
- **Recommended Option:** Option 12-R1 (Adopt human-only authors + formal AI disclosure).

#### Decision 13: Future Real-Data Evaluation Authorization
- **Status:** `DEFERRED_PENDING_OTHER_GATE`
- **Corrected Framing:** Shall evaluation authorization be decomposed into phased, scoped capability tokens (`AUTH-MEDIA-ACCESS`, `AUTH-DESCRIPTIVE-CACHE-EXEC`, `EVAL-AUTH-FULL`), deferring full raw-media evaluation until Stage-3 ground truth and simulation causality are certified?
- **Recommended Option:** Option 13-R1 (Phased capability token architecture).

---

## 12. Corrected Governance Dependency Graph

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ CORRECTED DECOUPLED GOVERNANCE DEPENDENCY GRAPH                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ TRACK A: PROTOCOL & EDITORIAL (Immediate PI Decision)                       │
│   [D09: Promote Protocol v7.1.0] ──► Canonical GT Protocol Defined          │
│   [D12: Authorship & AI Disclosure] ──► Academic Compliance Certified       │
│   [D11: M12 Administrative Memo] ──► Incident F13-08 Closed                 │
│                                                                             │
│ TRACK B: HUMAN GROUND TRUTH & ADJUDICATION                                  │
│   [D08: Appoint 2nd Reviewer] ──► [D06: Calibration Pilot & Tolerance]      │
│                                           │                                 │
│                                           ▼                                 │
│   [Tool D2: human_review_session.py] ◄───┘                                  │
│   [D07: Schema Adjudication Record]                                         │
│                     │                                                       │
│                     ▼                                                       │
│   [Human Review & Adjudication (27 Events)] under AUTH-MEDIA-ACCESS(REVIEW) │
│                     │                                                       │
│                     ▼                                                       │
│   [D10: Promotion Gate Execution] under AUTH-MEDIA-ACCESS(PROMOTION)        │
│                     │                                                       │
│                     ▼                                                       │
│   [Stage-3 Certified Ground Truth Receipts Bound]                           │
│                                                                             │
│ TRACK C: SIMULATION CAUSALITY & BENCHMARK REPLAY                            │
│   [Refactor runner.py: Forward-Causal Stepping]                             │
│   [Apply Verified -0.20s Correction to Table 11]                            │
│   [D05: Split DEC-B05; Freeze SM Constants; Classify MTR NOT_ESTIMABLE]     │
│   [D03: Adopt Front-Camera Scope B0, B1, B2]                                │
│   [D01/D02/D04: Token Binding with Working-Tree Tree-Hash]                  │
│                     │                                                       │
│                     ▼                                                       │
│   [D13: Issue AUTH-DESCRIPTIVE-CACHE-EXEC] ──► Deterministic Replay Executed│
│                                                                             │
│ TRACK D: PUBLICATION FINALIZATION                                           │
│   [Populate Tables 1-3 with Verified Descriptive Counts]                    │
│   [Disclose M4/M5 and Physical MTR as Non-Computable]                       │
│   [Final Privacy Scrub & Journal Submission]                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 13. Manuscript Claims Safety Implications

1. **Premature Opening ($M4$) and Clearance Latency:** Must remain explicitly reported as **`NON-COMPUTABLE`** in manuscript Table 3. Any claim of "0% premature openings" on real data is scientifically false because roadway clearance $T_4$ was unobserved.
2. **Missed-Train Rate ($MTR$) and Lead-In Feasibility:** Must be reported as **`NOT_ESTIMABLE`** on the historical dataset due to left-censoring of 20/23 train arrivals. The 3.6s threshold must be described strictly as an implementation-derived minimum controller latency.
3. **Table 11 Closed Duration:** Must be reported as *Simulated Passage-Blocked Duration* under legacy discrete stepping (Convention A), with an explicit note that forward-causal stepping yields exactly $T - 0.20\,\text{s}$ across all 27 events.
4. **Computer Vision Performance:** Layer A test split performance (99.46% mAP@50) is verified, but single-site geographical limitations and environmental generalization must be stated as research limitations.
5. **Authorship Block:** Generative AI agents must be removed from authorship lines, with AI assistance documented in Acknowledgments per COPE guidelines.

---

## 14. Unresolved Questions for the Principal Investigator

1. **Protocol Adoption:** Does the PI approve promoting `FINAL_GROUND_TRUTH_PROTOCOL_v7.1.0_PROPOSED.md` to canonical in-place status?
2. **Reviewer Nomination:** Who is the proposed independent second human reviewer, and will their credentials and conflict-of-interest statement be submitted?
3. **Reviewer Agreement Pilot:** Does the PI authorize a small human calibration pilot on synthetic/training events to measure empirical frame-level variance before fixing agreement tolerances?
4. **Primary Benchmark Scope:** Does the PI confirm scoping Version 1.0 of the descriptive paper strictly to front-camera conditions (`B0`, `B1`, `B2`), deferring dual-camera back-stream replay (`M-03`) to Version 2.0?
5. **Incident F13-08 Closure:** Does the PI approve the administrative risk-acceptance closure memo for Incident F13-08?

---

## 15. Git and Access-Boundary Integrity Report

### Baseline and Final Working Tree Status:
- **Git HEAD:** `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b` (Identical to baseline).
- **Tracked Modifications:** Exactly 25 modified tracked files preserved without alterations.
- **Untracked Porcelain Files:** Exactly 388 untracked files preserved without additions or deletions.
- **Staged Changes:** Exactly 0 files staged (`git diff --cached` is empty).
- **New Deliverable Created:** Exactly one file created:  
  [`docs/generated/master_reaudit/MISSION_16F_INDEPENDENT_CHALLENGE_OF_MISSION_16E.md`](file:///Users/sayemuddin/Desktop/Train_automation/docs/generated/master_reaudit/MISSION_16F_INDEPENDENT_CHALLENGE_OF_MISSION_16E.md).

### Boundary Compliance:
- Zero raw media files (`.mov`, `.mp4`, `.wav`, `.mp3`) were accessed or decoded.
- Zero production checkpoints (`best.pt`) were accessed or hashed.
- Zero real evaluation replays or simulations were run.
- Zero administrative tokens were generated.

---

## 16. Final Statutory Disposition

$$\mathbf{MISSION\_16E\_RECOMMENDATIONS\_REQUIRE\_MAJOR\_REVISION}$$

### Formal Justification:
While Mission 16E correctly diagnosed the fatal tool incapacity of `adjudication_session.py` and the obsolescence of Protocol v7.0.0, its own positive proposals contained severe technical and security flaws:
1. It proposed an unsupported $\pm 0.10\,\text{s}$ tolerance that mischaracterizes 59.94 fps video streams and ignores 5 Hz controller discretization.
2. It proposed an `EVAL-AUTH` v1.1 token bound to Git commit SHA, overlooking the uncommitted working-tree loophole across 25 modified tracked files.
3. It over-coupled independent governance decisions into artificial sequential bottlenecks.
4. It stated the Table 11 timing bound without explicitly documenting its strict dependence on uniform cadence and terminal blockage.
The restructured PI dossier and decoupled governance sequence established in this report resolve these defects and provide an airtight foundation for researcher decision-making.

---

REAL-DATA EXECUTION: NOT AUTHORIZED.
