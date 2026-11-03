# MASTER MANUSCRIPT READINESS AUDIT

**Project:** Train Gate Automation — Bangladesh  
**Audit Mission:** Master Mission 16A  
**Auditor:** Independent Principal Research Reviewer, Scientific Editor, and Reproducibility Auditor  
**Status:** COMPLETE AUDIT  
**Date:** 2026-11-02  
**Baseline HEAD:** `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`  
**Execution Authority:** NONE  

---

## 1. Executive Summary

This audit evaluates the publication readiness of all research manuscripts in the repository, focusing primarily on `docs/PAPER_DRAFT_DESCRIPTIVE_BENCHMARK.md`, `docs/PHASE16_MANUSCRIPT_CORRECTION_v1.md`, and the historical research progress report.

Key findings:
1. **Manuscript Maturation:** The manuscript has progressed from an ungrounded progress report into a well-structured descriptive benchmark skeleton (`PAPER_DRAFT_DESCRIPTIVE_BENCHMARK.md`).
2. **Authorship Defect (Mandatory Editorial Fix):** The current draft lists `Antigravity Autonomous Research Engineering Agent` as a formal co-author. This violates universal academic publication standards (COPE, IEEE, ACM, Nature), which mandate that authors must be legal persons capable of taking ethical and legal responsibility. The AI agent must be moved to the Acknowledgments section.
3. **Empty Results Tables:** All primary empirical tables (Tables 1, 2, and 3) correctly remain unpopulated placeholders (`[RESULTS PENDING - EVALUATION NOT AUTHORIZED]`). Because zero approved Stage-2.1 ground truth records exist, these tables cannot be filled without violating research integrity.
4. **Historical vs. Benchmark Disambiguation:** Previous drafts conflated exploratory still-image metrics (mAP 99.46% on 487 objects) with event-level crossing safety. The manuscript draft must maintain strict segregation between Layer A (held-out still images) and Layer B (video/audio events).

---

## 2. Comprehensive Manuscript Claim Ledger

Every major factual or scientific claim asserted across the manuscript drafts was audited against underlying repository evidence:

| Claim Description | Manuscript Section | Evidence Source | Evidentiary Status | Required Correction / Status |
| :--- | :--- | :--- | :--- | :--- |
| **YOLOv8n Still Image Detection (mAP@50 = 99.46%)** | Section 7.1 | `experiments/vision/39f402dfe460/evaluation/metrics.json` | **SUPPORTED (Layer A)** | Confirmed on 487 static objects. Must be explicitly labeled as Layer A still-image detection, not crossing event safety. |
| **Acoustic Horn F1 = 0.869, AUC = 0.961** | Section 7.2 | `experiments/audio/RUN_20261008_AUDIO_V3_ESC50/` | **SUPPORTED (Audio V3)** | Valid on held-out ESC-50 + local audio split. Must note threshold $\theta = 0.3700$. Legacy Audio V2 must be excluded. |
| **M4 Premature Opening Rate = 0.0%** | Historical Docx | Pre-Phase 5 Replay Logs | **INADMISSIBLE** | Evaluated on invalidated legacy ground truth. Must remain pending until Stage-2.1 ground truth is approved. |
| **Dual-Camera Synchronized Cohort (N = 12)** | Historical Docx | `docs/FINAL_DUAL_CAMERA_SYNC_CALIBRATION_REPORT.md` | **UNSUPPORTED / FALSE** | R04 dual-camera scope is strictly 11 events. `event_010` is ambiguous ($+11.800\,\text{s}$ anomaly) and must be excluded. |
| **Left-Censored Approach Latency** | Section 6.2 | `data/ground_truth/candidate_values.json` | **SUPPORTED** | 18 of 23 train events have $T_0 \le 0.0\,\text{s}$. Correctly stated: approach latency is unobservable; $T_1$ must serve as surrogate baseline. |
| **Physical Barrier Deployment Readiness** | Historical Docx | N/A | **INDEFENSIBLE / RETRACTED** | Barrier is simulated ($30^\circ/\text{s}$ kinematic model). Correctly retracted in `PHASE16_MANUSCRIPT_CORRECTION_v1.md`. |
| **All-Weather Generalization** | Historical Docx | N/A | **INDEFENSIBLE / RETRACTED** | Data collected only at daytime on a single crossing (`crossing_A`). Correctly retracted. |

---

## 3. Governance and Editorial Audit

### 3.1 Authorship and Attribution Policy
- **Current Text (Section 15):**  
  `Authors: [RESEARCHER CONFIRMATION REQUIRED - Human Principal Investigator], Antigravity Autonomous Research Engineering Agent`
- **Audit Assessment:** **NON-COMPLIANT.**
- **Publication Requirement:**  
  Under IEEE Authorship Guidelines and Committee on Publication Ethics (COPE) standards:
  - An AI entity cannot be named as an author or co-author.
  - The author list must contain exclusively the human researcher(s) who take scientific responsibility.
  - The AI contribution must be stated in the Acknowledgments section (e.g., *"Static code analysis, metric formulation assistance, and documentation synthesis were performed with the assistance of an autonomous AI agent under the direct instruction and oversight of the principal investigator."*).

### 3.2 Reference Integrity (Audit of Finding M-08)
- In earlier missions, Finding M-08 flagged that manuscript citations lacked formal bibliographic verification.
- In `docs/PAPER_DRAFT_DESCRIPTIVE_BENCHMARK.md`, Section 18 provides 12 verified, authentic citations covering:
  - FRA 49 CFR Part 222 (Locomotive horn rule),
  - CENELEC EN 50128 (Railway safety software standard),
  - AREMA Communications and Signals Manual,
  - E.B. Wilson (1927, score interval),
  - Leveson (2011, system safety),
  - Foundational datasets (Piczak ESC-50, Gemmeke AudioSet, Ultralytics).
- **Audit Verdict:** The 12 listed references are authentic and methodologically appropriate. Finding M-08 is satisfied for the current draft structure.

### 3.3 Status of Empirical Benchmark Tables
The paper draft contains three core empirical tables:
- **Table 1:** Primary Safety & Kinematic Benchmark ($M4$, $M5$, $\Delta t_{\text{actuation}}$, $\text{MTR}$).
- **Table 2:** Detection Performance by Subsystem ($P$, $R$, $F_1$, Latency).
- **Table 3:** Multi-Sensor Ablation (B0 vs B1 vs B2).

All rows in these tables currently display:  
`[RESULTS PENDING - EVALUATION NOT AUTHORIZED]`

> [!IMPORTANT]
> This placeholder status is **essential and mandatory**. These tables must NEVER be populated with historical pre-Phase-5 numbers or synthetic test data. They may only be populated after:
> 1. Human adjudication of Stage-2.1 ground truth (`ADJ-AUTH`),
> 2. Official issuance of `EVAL-AUTH` and `AUTH-MEDIA-ACCESS`.

---

## 4. Manuscript Pre-Submission Checklist

Prior to journal submission, the research team must complete the following steps:

1. [ ] **Update Author Line:** Replace AI agent with human researcher names and affiliations.
2. [ ] **Add AI Disclosure:** Insert formal AI disclosure in Acknowledgments per IEEE/COPE policy.
3. [ ] **Complete Human Ground-Truth Adjudication:** Adjudicate all 27 events using `adjudication_session.py`.
4. [ ] **Execute Authorized Benchmark Replay:** Run authorized Phase 5 evaluation to generate empirical numbers for Tables 1–3.
5. [ ] **Insert Hardware Photographs & Geometry Diagrams:** Provide site layout schematics of `crossing_A`.
6. [ ] **Finalize Abstract Word Count:** Condense abstract outline to $\le 250$ words.

---

## 5. Audit Verdict

The manuscript framework is in a **mature, scientifically honest, and methodologically sound state**. Once human ground truth is certified and official evaluation is executed under governance authorization, the paper will be ready for peer-reviewed journal submission.
