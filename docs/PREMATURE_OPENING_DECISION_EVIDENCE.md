# Premature-Opening Definition — Decision Evidence

**Date:** 2026-10-16 · **Verdict: UNRESOLVED. No definition has a researcher-attributed acceptance.** The evaluator's metric code was **not** changed, and the profile now has **no default** for this decision: an official run is refused (`PREMATURE_OPENING_DEFINITION_UNDECIDED`) until the researcher records a choice.

This corrects the previous report (`APPROVAL_RECONCILIATION_REPORT.md` §7), which called protocol v9's window "documented and implemented" and treated it as the working default. The evidence below does not support presenting either window as accepted.

## 1. The two candidate definitions

| | Definition | Source |
|---|---|---|
| **v9** | A premature opening is an opening command while **T1 ≤ t < T4**. T0 is never part of it. Events with unobservable T4 are excluded | `FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md` §5.2 (POR), §9 (primary endpoint) and INV-3; `FINAL_GROUND_TRUTH_PROTOCOL.md` POR definition |
| **M4** | Failure if any blocked → not-blocked transition or opening command occurs in **(t_blocked, T4)**, where `t_blocked` is the first blocked tick of the replayed system. Needs T4 only | `EXPERIMENT_DESIGN_FINAL.md` §8.3, flagged `[D-10]` |
| (T0-based) | Reopening in [T0, T4) | Appears in no protocol or design document; only a planning-table line in `PHASE12_EVALUATION_REPORT.md` §3 ("Gate opens before T0"), since marked inconsistent with both. All 23 train events are left-censored at T0, so it would be almost never evaluable |

## 2. Who decided what — the record

| Evidence | What it establishes | Author type |
|---|---|---|
| `RESEARCH_DECISIONS.md` header (2026-10-11) calls v9 and companions "the authoritative protocols" | v9 was the working protocol. No researcher name, no acceptance of its endpoints specifically | Repository document, unattributed |
| `INDEPENDENT_MASTER_AUDIT.md` (2026-10-13), document table | States v9 is "Historical. Superseded by `EXPERIMENT_DESIGN_FINAL.md` for endpoints" | **AI audit** (not a researcher decision) |
| `EXPERIMENT_DESIGN_FINAL.md` header | "Governing specification … **subject to the decisions in `OPEN_DECISIONS_AND_BLOCKERS.md`**. Where a decision is pending, this document states the default and marks it `[D-n]`" | AI-authored design |
| `OPEN_DECISIONS_AND_BLOCKERS.md` **D-10** | Options (a) keep v9 endpoints, (b) M4/M7 primary, (c) shorten timings (rejected as tuning). Recommended (b). "If you accept all defaults, the only things you must still do personally are D-1, D-2, D-7 and the annotation review" | AI recommendation awaiting the researcher |
| `HANDOFF_TO_GEMINI.md` §4 | D-2 answered; **"D-3 through D-11 remain open"** | Session handoff |
| `MASTER_REMAINING_PHASES_IMPLEMENTATION_PLAN.md` §2.2 | Design is governing "**subject to still-pending researcher-only decisions**" | AI plan |
| `RESEARCHER_DECISION_REGISTER_REMAINING_PHASES.md` | Lists R-D1 … R-PUB; **does not list D-10**, so it was neither closed nor tracked later | AI register |
| Every researcher-attributed record (`raihankabirrahu@gmail.com`: Decisions 1–4, T0 corrections, legacy-disposition scope, allowlist) | None concerns the premature-opening window or the primary endpoints | Researcher |
| This session's authorization statement | "Subject to the approved protocol" — names no definition | Researcher, chat |

**Conclusion.** "v9 is superseded" is an AI audit note. The design document that would replace it is explicitly conditional on a decision (D-10) that no researcher-attributed record resolves. Choosing either window on recency (design is newer) or convenience (code already does v9) would be choosing for the researcher.

## 3. What the code does today (not an endorsement)

`simulation/runner.py` computes the v9 predicate (`T1 <= t < T4`, gate `OPENING`/`OPEN` and not blocked). It was written before the design document and is the only implemented option; `protocol_choices.IMPLEMENTED_OPTIONS["premature_opening_window"] == {"t1_entry_to_t4_clearance"}`. Choosing M4 or the T0 window is refused (`PROTOCOL_CHOICE_NOT_IMPLEMENTED`) until that definition is implemented and tested.

## 4. Why the decision is not cosmetic — consequences by camera mode

T1 is annotated on the **front** clock and T4 on the **back** clock. The official replay never assumes an offset (`evaluation/clock_aware.py`). Consequently, for the same recordings:

| Camera mode | v9 window [T1, T4) | M4 window (t_blocked, T4) |
|---|---|---|
| `dual_camera` (researcher-accepted, `CALIBRATION_SUPPORTED`) | Computable on the fused timeline (T4 shifted by the validated back offset) | Computable |
| `independent_camera` | **Not evaluable** — T1 and T4 share no timeline (`clock_mismatch`, listed per event) | Computable on the back stream, but only if that stream's replay actually blocks; `rear` is a departure-only label, so the back-only outcome depends on which labels the back detector emits (`side`/`train` count as approach), and the design's companion M5 "never protected" reports the cases where it does not |
| `single_camera` (front only) | Not evaluable: T4 is on the back clock | Not evaluable: T4 is on the back clock |

Only 11 of 27 events have `CALIBRATION_SUPPORTED` synchronization (`documented_r04_candidates`). Under v9 the premature-opening endpoint would therefore be evaluable for, at most, those events whose dual-camera scope the researcher accepts.

## 5. The exact decision needed (one item)

Record in `data/manifests/phase12_protocol_decision.json` (`phase12-protocol-decision/1`, allowlisted `decided_by`, verbatim `researcher_statement`):

```json
"choices": { "premature_opening_window": "t1_entry_to_t4_clearance" }
```

or choose `first_blocked_to_t4_clearance` (M4), which will be refused until implemented. If M4 is chosen, the follow-on work is a bounded engineering task: compute `t_blocked` per replay system and apply the window on the system carrying T4, then add the M5 "never protected" companion the design pairs with it. The other three definitions (event weighting, censoring, false-alarm reporting) are documented consistently in v9 and the design document and need no decision.
