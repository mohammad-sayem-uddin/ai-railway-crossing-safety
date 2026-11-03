# D1 v9.0.0 / v7.0.0 — Proposed Binding (NOT ACTIVATED)

> **PROPOSED — NOT APPROVED — NOT AUTHORIZATION.**
> The researcher *selected* protocol v9.0.0 and ground-truth v7.0.0 in conversation (Mission 4E.2 input).
> **Formal repository approval and binding of D1 has NOT been authorized.** This document is not a
> decision envelope, does not satisfy `phase12_protocol_decision.json`, and changes no register,
> readiness state or validator. Nothing here may be cited as D1 being bound.

**Mission:** 4E.2 · **Date:** 2026-11-01 · **Repo HEAD at inspection:** `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b` (branch `main`)

## 1. Selected artifacts and exact hashes (SHA-256 of raw file bytes)

| Role | Path | Version string in file | Size (bytes) | SHA-256 |
|---|---|---|---:|---|
| Real-world protocol (selected) | `docs/FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md` (**working tree**) | 9.0.0 | 35008 | `7c183b323970591b68f0db692e70413e54dcacfc4bf78a358c28f1b1ed68734c` |
| Ground-truth protocol (selected) | `docs/FINAL_GROUND_TRUTH_PROTOCOL.md` (**working tree**) | 7.0.0 | 54092 | `d100c1e6a63280c375f94e297416efb0cf7dd3c15c9aa8df076ede052d49ecf4` |
| *Not selected:* same path at `HEAD` | `docs/FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md` | 8.0.0 | — | `dbc7ab783d8b09c8f8141f9965291f82e9c5388c0ab87931cd7454f304671dc5` |
| *Not selected:* same path at `HEAD` | `docs/FINAL_GROUND_TRUTH_PROTOCOL.md` | 6.0.0 | — | `1fe645001dbbe057bf79bf960f3ab5c30f4a969dd2df000d5b84a25fb815c53a` |

Hash method: `shasum -a 256 <file>` on the working-tree bytes; HEAD versions via `git show HEAD:<path> | shasum -a 256`.
Markdown files have no "canonical content hash" convention in this repo (that convention applies to YAML configs only).

**Hazard — the selected files are uncommitted.** Both are working-tree modifications (`M` in `git status`). The pinned
hashes identify *these bytes only*. Any edit before binding invalidates the pin, and a `git checkout`/`restore` of either
file would silently revert the repository to v8/v6. Committing is the researcher's decision; this mission did not stage or commit.

## 2. Compatibility verification (read-only, re-derived this mission)

Confirmed from text:
- v9 §5.4 explicitly delegates the danger-zone convention to GT v7.0.0 §2.4 (v9 line 142).
- Both state R03 retired and R04 unresolved with independent camera-local clocks (v9 line 410; GT §7 items 3–4).
- T3/T4 share one physical exit plane (vendor-stall / departure roadway boundary) on `camera_back.mov` in both.
- Current Stage-2.1 code uses the canonical boundary names `T0…T4, T_scene_clear` (`src/railway_detection/annotation/schemas.py:28`).

**Inconsistencies inside v9/v7 that Mission 4E.1 did not surface** (they do not break D1 selection but must be disclosed in any binding):

| # | Finding | Evidence | Why it matters |
|---|---|---|---|
| C1 | **T2 has two definitions.** §2.1 / v9 table: "locomotive body *fully occupies* the road crossing danger zone." §2.4 / v9 §5.4: "front *pilot crosses* the transverse camera plane / roadway boundary line … commencing physical road lane blockage." | GT v7 §2.1 vs §2.4; v9 line 111 vs 145 | T2 is the closest existing candidate for the occupancy onset (see occupancy contract). The two definitions are different physical instants. |
| C2 | **Premature-opening text is T1-based** in v9/v7 (`t ∈ [T1, T4]`, POR = opening while `t<T4` and `t≥T1`; INV-3). The researcher selected M4 (`first_blocked_to_t4_clearance`). | v9 lines 122–124, 271; GT §2.2 | A binding must state that M4 is selected for the `premature_opening_window` choice and that the T1-based POR text is superseded *for that metric* — otherwise two definitions coexist. |
| C3 | **"Physical occupancy" is already used for `T4 − T1`** (Excess Closed Duration baseline; "Physical Hazard Occupancy t∈[T1,T4]"). | v9 lines 122–123, 294 | The researcher's "full crossing occupancy" (physical onset → T4) collides in name. A distinct identifier is proposed in the occupancy contract. |
| C4 | `T2` §2.4 landmark is defined **only on `camera_front.mov`**, while the §2.1 table lists T2's primary camera as "Front / Back". | GT §2.1 vs §2.4(2) | No back-camera T2 landmark exists. |
| C5 | "transverse camera plane / roadway boundary line" joins two different references with a slash. | v9 line 145 | Which line governs T2 is left to the reviewer. |

## 3. Dependent references (grep of `src`, `configs`, `scripts`, `tests`, `schemas`)

- `src/railway_detection/experiments/preflight_validator.py:145-163, 716-723, 1417-1418` — presents D1 as **pending**; v9/v7 labelled `TECHNICAL_RECOMMENDATION_ONLY`. Correct as-is; must not be edited to "force" readiness.
- `src/railway_detection/reproducibility/audit.py:395-402` — points at the two doc paths and reports `protocol_version` **UNRESOLVED** (asserted in `tests/unit/test_reproducibility_audit.py:145`).
- `src/railway_detection/annotation/batch_multimodal_annotator.py` — still cites GT **v6.0.0** and emits `schema_version="6.0.0"` proposals (legacy generator). Historical; legacy 6.0.0 review records are invalidated and must remain untouched.
- `src/railway_detection/annotation/stage2_1_schema.py` — supersedes the `7.0.0` *review-record schema* (a record-schema version, distinct from GT protocol v7.0.0). Do not conflate the two "7.0.0" strings.
- `src/railway_detection/annotation/review_reporter.py:109` — already words R03 as retired under v7.0.0.
- No file under `configs/` pins either protocol version.
- `data/manifests/phase12_protocol_decision.json` — **absent** (`governance.PROTOCOL_DECISION_RELATIVE`).

## 4. What a binding would have to contain (for the researcher to author; NOT created)

The existing loader (`governance.verify_decision_envelope`, `protocol_choices.validate_protocol_choices`) requires:
`schema_version="phase12-protocol-decision/1"`, `decision_status="APPROVED"`, `decision_id`, `decided_by` (must be on the maintained
authority allowlist), `researcher_statement`, `decided_at_utc` (not in the future), and `choices` limited to the keys in
`PROTOCOL_CHOICE_OPTIONS` (`premature_opening_window`, `continuous_metric_weighting`, `censoring_treatment`, `false_alarm_measure`).

Proposed *content* for the researcher to consider (illustrative only — not a file, no approval fields filled):

| Item | Proposed value | Status |
|---|---|---|
| Protocol authority | real-world v9.0.0 + GT v7.0.0, pinned to the two SHA-256 values in §1 | selected by researcher; **unbound** |
| `choices.premature_opening_window` | `first_blocked_to_t4_clearance` | selected by researcher; **unbound** |
| `choices.censoring_treatment` | `exclude_censored_from_point_estimates` (documented profile default) | not yet decided |
| Occupancy-duration metric | **cannot be expressed** — `choices` rejects unknown keys (`ProtocolChoiceError`) | gap G-OCC-10 |
| Supersession note | M4 supersedes T1-based POR text for `premature_opening_window` (C2) | needs researcher wording |
| T2 definition | researcher to pick §2.1 or §2.4 wording (C1) | **open** |

`decided_by`, `researcher_statement`, `decided_at_utc`, `decision_id`, `decision_status` are intentionally **not drafted** here:
those fields carry the researcher's attestation and must be authored by them.

## 5. Not done / not claimed

- No D1 binding, no hash registration, no edit to any decision register, `phase12_protocol_decision.json`, readiness validator or schema.
- No claim that the pair is *approved*; compatibility here is a documentation-level technical finding.
- No migration of the 27 invalidated legacy review records (they stay intact).
