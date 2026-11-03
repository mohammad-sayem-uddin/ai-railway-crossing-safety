# Updated Prerequisite Checklist — Mission 4E.2

> **Informational. NOT a canonical readiness record.** It changes no readiness state, approval or register.
> Status legend: **DECIDED-R** researcher decision given (conversation only) · **PENDING-A** formal approval pending ·
> **PENDING-X** execution authorization pending · **TECH-OK** technical finding only · **OPEN** unresolved · **BLOCKED**.

## A. Researcher decisions (given in Mission 4E.2 input; not repository records)

| # | Decision | State |
|---|---|---|
| 1 | D1: protocol v9.0.0 + GT v7.0.0 | DECIDED-R · unbound |
| 2 | D2 outcomes: both premature gate opening and train-clearance duration | DECIDED-R · unbound |
| 3 | M4 = `first_blocked_to_t4_clearance` as premature-opening safety metric | DECIDED-R · unbound |
| 4 | M5 never-protected kept as separate safety outcome | DECIDED-R · unbound |
| 5 | Duration metric = full crossing occupancy, `T_physical_block_onset → T4` | DECIDED-R · onset boundary **undesignated** |

> **Updated in Mission 4E.3** (rows marked 4E.3). Still informational; not a canonical readiness record.

## B. Technical prerequisites

| Item | State | Note |
|---|---|---|
| v9/v7 paths + SHA-256 verified | TECH-OK | D1 doc §1; files uncommitted |
| v9↔v7 documentary compatibility | TECH-OK with caveats C1–C5 | D1 doc §2 |
| M4 start/end semantics verified in code | TECH-OK | `metrics.py` untracked |
| M4 replay-coverage rule (M4-V6) | OPEN | gap G-M4-02 |
| Physical-onset boundary designated | **OPEN (researcher)** | T1 vs T2 vs new boundary |
| T2 definition conflict resolved | **OPEN (researcher)** | C1 |
| Same-camera landmark convention for onset+T4 *or* R04 for cross-camera | **OPEN / BLOCKED** | G-OCC-02/03 |
| Schema carries censoring direction, uncertainty, onset provenance | OPEN | G-OCC-04 (no field added) |
| Occupancy evaluator + choices-key | OPEN | G-OCC-06, G-OCC-10 (no code added) |
| Synthetic tests of written rules | DONE | 68 passed (4E.3: +11); validates written rules only |
| 4E.3 · Terminology T1/T2/T4/`T_OCC_START` reconciled in proposal form | TECH-OK (proposal) | researcher must pick option A/B/C |
| 4E.3 · Crossing conflict area defined by landmarks (no coordinates) | TECH-OK (proposal) | entry-plane mirror assumption **OPEN** |
| 4E.3 · Same-camera (onset, T4) pair | **NOT ESTABLISHED** | front contradicted; back undocumented |
| 4E.3 · M4 incomplete-replay classification corrected (proposal) | TECH-OK (proposal) | code unchanged |
| 4E.3 · Engine exclusion specified (ENG-1…8) | TECH-OK (proposal) | conflicts with design doc §8.3 — researcher to resolve |
| 4E.3 · Replacement wording drafted, not applied | TECH-OK (proposal) | applying it invalidates hash pins |

## C. Formal approvals still pending (PENDING-A)

1. Formal D1 binding (`phase12_protocol_decision.json`) naming v9/v7 with hashes — not created.
2. Decision-register update D1/D2 — not changed.
3. Approval of the exact M4 contract and M5 reporting definition.
4. Approval of the occupancy-duration definition, its onset boundary and denominator rules.
5. Statement on how M4 supersedes T1-based POR text; resolution of T2 definition.
6. R04 scope decision (only if any fused / cross-camera analysis is used).
7. Stage-2.1 genuine human review → approved T4 (and onset) records; promotion receipt.
8. Official event split; evaluation manifest.

## D. Execution authorizations still pending (PENDING-X)

1. EVAL-AUTH (`data/governance/eval_authorization.json`).
2. Authorization for production replay / cache generation and any inference.
3. Authorization for a human-review timing pilot, if wanted.
4. Authorization to open/inspect media for human adjudication.
5. Any experiment run.

## E. Readiness

Canonical readiness was **not re-run or altered** in this mission. The last reported state (Mission 4E.1) was `ready=False`, 9 blockers; nothing in 4E.2 reduces that count.
