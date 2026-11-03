# Evidence / Schema Gap Register — Mission 4E.2

> **PROPOSED — NOT APPROVED — NOT AUTHORIZATION.** Observations only. No gap below was closed, and no schema, validator or
> readiness rule was changed. "Supported" = exists in code/schema today. "Proposed" = appears only in these 4E.2 documents.

Severity: **B** blocks the stated use · **H** high · **M** medium.

## D1

| ID | Gap | Evidence | Sev | Owner |
|---|---|---|---|---|
| G-D1-01 | D1 not bound: `data/manifests/phase12_protocol_decision.json` absent; register still `PENDING_RESEARCHER_DECISION` | `governance.PROTOCOL_DECISION_RELATIVE`; preflight_validator.py:145-163 | B | researcher |
| G-D1-02 | Selected v9/v7 files are **uncommitted** working-tree edits; HEAD holds v8/v6. Hash pin is fragile | `git status` `M` on both; hashes in D1 doc §1 | H | researcher |
| G-D1-03 | T2 has two incompatible definitions (§2.1 "fully occupies" vs §2.4 "pilot crosses … line") | GT v7 §2.1/§2.4; v9 l.111/145 | H | researcher |
| G-D1-04 | T1-based POR / INV-3 / "Physical Hazard Occupancy" text coexists with selected M4 | v9 l.122-124, 271, 294 | H | researcher |
| G-D1-05 | `PROTOCOL_CHOICE_OPTIONS` has no key for an occupancy metric; unknown `choices` keys are refused | protocol_choices.py:51-110, 133-150 | B (for occupancy) | code+researcher |
| G-D1-06 | `metrics.py` (holds M4/M5) is **untracked**; no commit history | `git ls-files --error-unmatch` fails | M | researcher |
| G-D1-08 | `EXPERIMENT_DESIGN_FINAL.md` (untracked) claims to supersede v9 for endpoints/taxonomy; authority over metric definitions vs the selected v9/v7 not settled | doc header | H |
| G-D1-07 | Legacy generator still emits GT v6.0.0 proposals | batch_multimodal_annotator.py:3,322 | M | historical |

## M4 / M5

| ID | Gap | Evidence | Sev |
|---|---|---|---|
| G-M4-01 | M4 profile not bound (same envelope as G-D1-01) | execution_gate.py:150 | B |
| G-M4-02 | **No replay-coverage check** *(reworded in 4E.3)*: replay ending before T4 yields "not premature" if blocked throughout; **and** a short or empty replay with no blocked step is labelled **M5 never-protected**. Correction specified; code unchanged | tests `TestKnownCharacterizedGap`, `TestCharacterizationOfCurrentCodeVsCorrection` (current behaviour, pass) | H |
| G-M4-03 | Replay timeline identity (front/back/fused) and consequence for M5 meaning not recorded per event | B0_B1_B2_METRIC_SPECIFICATION.md:260-277 | H |
| G-M4-04 | Empty interval ⇒ vacuously not premature (sparse retained steps) | test `test_empty_interval_is_vacuously_not_premature` | M |
| G-M4-05 | `OPENING`/`OPEN` label with `is_passage_blocked=True` counts as premature — stricter than "unblocked"; researcher should confirm intent | metrics.py:119-121 | M |
| G-M4-06 | No approved T4 for any event (0/27); no promotion receipt; no official split; no EVAL-AUTH | 4E.1 audit; governance paths | B |
| G-M4-07 | Fused scope needs `phase12_r04_scope_decision.json` (absent); candidate offsets unapproved | governance.R04_DECISION_SCHEMA | B (fused only) |
| G-M4-08 | No M5 proportion/CI defined | metrics.py:169-170 | M |
| G-M4-10 | Bare (non-cohort-qualified) engine id is evaluated as a **train** event by `evaluate_run` unless `cohort`/status/prefix is supplied | test `test_current_code_bare_engine_id_without_cohort_is_treated_as_train` | H |
| G-M4-11 | `EXPERIMENT_DESIGN_FINAL.md` §8.3 lists M4/M5 population as "Train, engine"; code and v7 exclude engine | design doc vs `metrics.py` | M |
| G-M4-09 | Stale operator text: `execution_gate.py:150-152` says M4 is "not implemented", but `IMPLEMENTED_PREMATURE_WINDOWS` includes it. Message only; not edited (readiness/gate files are out of scope) | execution_gate.py vs metrics.py:94-95 | M |

## Occupancy duration

| ID | Gap | Supported / Proposed | Sev |
|---|---|---|---|
| G-OCC-01 | No designated "physical crossing-blocked onset" boundary. Candidates T1/T2 only | candidates **supported**, designation **absent** | B |
| G-OCC-02 | T2 landmark defined on front camera only; T4 on back ⇒ cross-clock | GT v7 §2.4 | B |
| G-OCC-03 | R04 unresolved ⇒ every cross-camera duration excluded | GT v7 §5, §7 | B |
| G-OCC-04 | Main schema `BoundaryAdjudication` lacks `censoring_direction`, `timestamp_uncertainty_s`, `timestamp_basis`, onset-source provenance. (Timing-pilot schema has the first three but its drafts are permanently unapproved.) | `stage2_1_schema.py:213-250` vs `schemas/stage21_timing_pilot.schema.json:70-86`; `censoring_direction` and `source` in tests are **proposed** | H |
| G-OCC-05 | Left/right-censoring direction recoverable only from free-text rationale | schema | H |
| G-OCC-06 | No occupancy evaluator, no `REQUIRED_BOUNDARIES` entry, no summary class | metrics.py:561-567 | B |
| G-OCC-07 | No approved GT ⇒ zero events can be occupancy-evaluable | 4E.1 audit | B |
| G-OCC-08 | Visibility/occlusion of the onset landmark and prevalence of T2 censoring unknown (media not opened; proposal T2 values deliberately not read) | — | H |
| G-OCC-09 | Frame-level resolution/uncertainty of onset and T4 not carried in promoted records | schema | M |
| G-OCC-10 | Metric not expressible in the protocol-decision envelope (= G-D1-05) | protocol_choices.py | B |
| G-OCC-11 | Name collision: v9 "physical occupancy" = `T4 − T1` | v9 l.122-123, 294 | M |
| G-OCC-13 | `T_OCC_START` appears nowhere in the repo; only a proposed alias | grep, 4E.3 | M |
| G-OCC-14 | T2 reference line described three ways (camera/lens plane, roadway boundary line, roadway occupancy line); legacy generator words it as "transverse lens plane" | GT §2.4; R04 investigation; `batch_multimodal_annotator.py:201` | H |
| G-OCC-15 | Entry plane E not documented as a named plane (only exit plane X is); mirror assumption unconfirmed | GT §2.4(1) | H |
| G-OCC-16 | Same-camera pair not established: front contradicted for T4; back has no documented entry-plane landmark | `OVERNIGHT_RESEARCH_HANDOFF.md:60`; GT §2.4 | B |
| G-OCC-17 | Travel-direction distribution undocumented; front=approach assumed fixed | GT §3 schema | M |
| G-OCC-12 | Engine events: protocol treats `T3≡T4`; whether engine events belong in occupancy is a researcher choice (contract proposes exclusion) | GT v7 §2.2 | M |

## Process note (not a repository gap)

During the Git integrity check I ran `git fsck --lost-found`, which wrote 309 pointer files into `.git/lost-found/`
(146 commit, 163 other; stamped 2026-11-01 11:51:53). HEAD, refs, index and the working tree are unaffected. Disclosed to the researcher before any mission write; not cleaned up.
