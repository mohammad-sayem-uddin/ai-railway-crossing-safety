# Protocol Reconciliation Report (RD-001…RD-013, TF-04/06/14/21/22)

> **PROPOSED — NOT APPROVED.** v9.0.0 / v7.0.0 remain the *selected direction* of the researcher; D1 is **not bound**. The reconciliation is delivered as **new proposed files** so the in-place working-tree protocols (and the hash pins that depend on them) are untouched.

## 1. Artifacts

| Artifact | Path | SHA-256 of source it was derived from |
|---|---|---|
| Proposed real-world protocol | `docs/generated/mission_5a/FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL_v9.1.0_PROPOSED.md` | v9.0.0 working tree `7c183b323970591b68f0db692e70413e54dcacfc4bf78a358c28f1b1ed68734c` |
| Proposed ground-truth protocol | `docs/generated/mission_5a/FINAL_GROUND_TRUTH_PROTOCOL_v7.1.0_PROPOSED.md` | v7.0.0 working tree `d100c1e6a63280c375f94e297416efb0cf7dd3c15c9aa8df076ede052d49ecf4` |
| Diffs | `v9_working_tree_vs_v9.1.0_PROPOSED.diff`, `v7_working_tree_vs_v7.1.0_PROPOSED.diff` | — |

**Sequence required by RD-002:** adopt wording → (researcher) commit/snapshot → re-hash the *final* files → author the D1 envelope. Binding the current v9.0.0 / v7.0.0 bytes would pin known contradictions. The hashes above are therefore **not** to be bound.

## 2. Document authority (RD-001)
v7 governs ground-truth boundaries. v9 governs system and metric definitions. `EXPERIMENT_DESIGN_FINAL.md`, `OPEN_DECISIONS_AND_BLOCKERS.md` and `RESEARCH_DECISIONS.md` are **non-binding references** except items explicitly adopted (see the experiment-design reconciliation). Historical text is preserved only inside `<!--HISTORICAL-->` blocks.

## 3. Conflicts and their resolution

| # | Conflict (from the 4E.4 report) | Resolution in the proposals | Decision |
|---|---|---|---|
| I-1 | T1 table "into road danger zone" vs frog line | T1 = approach danger-zone / frog line; table reworded | RD-004 |
| I-2 | T2: "fully occupies" vs "pilot crosses line"; camera/lens plane vs roadway line | T2 = leading end crosses the **physical roadway entry boundary**; "fully occupies" and camera/lens plane withdrawn; **landmark deferred**; legacy lens-plane values not automatically valid | RD-005, RD-006 |
| I-3 | five meanings of "occupancy" | `[T1,T4]` → "approach-to-clearance interval"; `T4−T1` → "approach-to-clearance time"; "crossing-conflict-area occupancy duration" reserved and **deferred** | RD-009, RD-018 |
| I-4 | T1-based POR text vs selected M4 | v9 §5.2, INV-3, §18 and v7 §2.2 replaced by M4/M5; old text in HISTORICAL blocks | RD-008 |
| I-5 | design doc "supersedes" v9; includes engine in M4/M5 | authority fixed (§2); engine excluded | RD-001, RD-024 |
| I-6 | paper front-only vs back-only T4 | independent-camera framing (§5.5); paper proposal | RD-015, RD-052 |
| I-7 | descriptive mode synthetic-only | recorded as a blocker; pathway needs separate approval | RD-039 |
| I-8 | R04 11 vs 12 | existing 11-event exploratory scope preserved; `event_010` not silently added | RD-026 |
| I-9 | fused primary if ≥ 20/23 | independent-camera primary; criterion not claimed met | RD-028 |
| I-10 | acoustic offsets vs human GT | offsets never shift GT timestamps | RD-027 |
| I-11 | inferential tests vs descriptive-only | v9 §19 McNemar/Wilcoxon text removed (historical block); descriptive statistics only | RD-023 |
| I-12 | policy v1 vs v2 vs design §5 | v1 frozen; limitations documented | RD-029 |
| I-13 | agent listed as author | removed in paper proposal | RD-054 |

## 4. Terminology and identifier guide (RD-009)
- Governance identifiers use `GOV-`, `EXP-`, `AUTH-`. New governance documents do **not** use `D1…D4`, `D3`, or `D-n`.
- Historical → canonical: `D1`→`GOV-D1-PROTOCOL-AUTHORITY`, `D2`→`GOV-D2-EVALUATION-PROFILE`, `D3` (descriptive mode)→`GOV-D3-DESCRIPTIVE-MODE`, `D3(a)`→`GOV-REVIEW-SECOND-REVIEW-TRIGGERS`, `D3(c)`→`GOV-REVIEW-CLEAR-BOUNDARY-AUDIT`, `D4`→`GOV-D4-R04-SYNCHRONIZATION`, `AUTH-EVAL-OFFICIAL` (4E sheet spelling)→`AUTH-EVAL-AUTH`, `D-1…D-11` (`OPEN_DECISIONS_AND_BLOCKERS.md`)→ see the RD matrix. Aliases for the new ids are in `HISTORICAL_DECISION_ALIASES`.
- "Occupancy" is used only for the deferred crossing-conflict-area occupancy duration; `T_OCC_START` is a prose alias for reconciled T2 (valid only once the entry landmark exists) and is **not** a schema field.

## 5. Technical findings documented here
- **TF-06 (tick interval):** documented in the experiment-design reconciliation (`tick_interval_s` unread; frozen config governs; policy file untouched).
- **TF-14 (stale paper statements):** resolved by the paper revision proposal.
- **TF-21 (legacy schema-version labels):** the 27 legacy review files on disk all carry `schema_version "6.0.0"` (23 train, 3 no-train, 1 engine); 27 invalidation notices exist. Reports that called them `"7.0.0"` conflated them with the 7.0.0 *candidate-proposal* schema (proposal files: 3 × 5.0.0, 27 × 6.0.0, 29 × 7.0.0, 1 × 8.0.0). Legacy records are historical and invalidated; they were not edited or migrated.
- **TF-22 (inventory):** 27 events = 23 train + 3 no-train + 1 engine. The engine cohort has **one** event with three proposal versions (`v1…v3`), not three engine events. Inventory approval status: **not approved** (no signed inventory freeze exists; RD-041 confirmed the inventory as a fact, formal sign-off pending).

## 6. Unresolved / deferred items surfaced
Entry landmark (RD-006); review tolerance (RD-012); full occupancy duration (RD-018); see the blocker register.
