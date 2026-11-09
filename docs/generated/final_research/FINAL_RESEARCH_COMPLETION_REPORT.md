# Final Research Completion Report — Train Gate Automation

Mission 3 (Master Research Completion), executed 2026-11-08/09.
Repository state at start: local == remote == `25bab63` (Mission 2 release).

## 1. Mandate and overall status

The mandate was to complete the original Protocol V2 research programme —
finish the decision-level experiments on the existing 27-event dataset and
produce a defensible evidence package for the professor — under hard
guardrails: no fabricated approvals, ground truth, timestamps, or
signatures; no bypassing or patching the execution gate; no threshold
changes; no invented statistics; historical evidence preserved.

**Status: PARTIALLY COMPLETE — and the boundary is exact.** Everything
that can legitimately be executed without human governance records is
done and verified (§3). The governed decision-level replays (EXP1–EXP5,
EXP10) remain **not executed**, because the repository's own gate requires
a Stage-2.1 human review chain that does not exist and cannot be created
by an agent without fabrication (§4). This report labels that state
plainly rather than presenting perception results as decision results.

## 2. Guardrail compliance

- No approval, ground-truth record, review timestamp, or signature was
  created, inferred, or simulated. The three governance records the gate
  requires are still absent, and are reported absent.
- The execution gate, readiness CLI, and frozen engine were read and
  tested but never patched; Mission 3's only production-code change is
  one additive subclass module.
- The audio threshold (0.37) and all frozen thresholds/dwells are
  untouched. Nulls stayed null. The engine-only event is reported
  separately throughout.
- The Mission 2 README rewrite causes 23 historical tests to fail against
  Mission 26's sealed catalog; the catalog was NOT rebound (rebinding
  would rewrite sealed evidence). All 37 full-suite failures are
  classified in SOFTWARE_TESTING_REPORT.md; zero are code defects.

## 3. What Mission 3 executed and verified

1. **Phase 0 verification** — HEAD == remote `25bab63`; governance records
   confirmed absent; frozen checkpoint hashes match; 253 cache JSONLs;
   56 raw media files.
2. **Blocker analyses A–D** (staging, Mission 3 working records) — policy
   comparison, annotation status, protocol reconciliation, authorization
   chain, all from direct source reading.
3. **Adoption integrity** — all 27 adopted proposal files re-hashed:
   27/27 SHA-256 match the Mission 43 adoption record.
4. **Policy/fusion tests** — 60/60 pass (Phase 9/10/10.1, engine,
   collector fail-closed, sensor health).
5. **Synthetic decision battery** — 13 scenarios × both engines;
   run 2: **46/46 checks pass** (`results/m3_synthetic_battery_r2/`).
   v1's defects are trace-verified (departure "confirmation" from
   ambiguous labels while the train is still present; RULE_7
   self-interruption ×7 in S1; CROSSING_OCCUPIED trap). v2 passes every
   behavioural check, including the fail-safe and recovery semantics.
6. **Full guarded suite** — 3,787 passed / 37 failed / 0 errors; every
   failure classified (SOFTWARE_TESTING_REPORT.md).
7. **Back-stream replay extension** — `cache_only_engine_multimodal.py`
   (frozen engine untouched): BACK_VISION / DUAL_VISION /
   DUAL_VISION_AUDIO conditions, dual-serialization back validation,
   fail-closed SyncAligner requirement for dual conditions, master-time
   window fix. **8/8 unit tests pass.**
8. **Full multimodal assembly** — anchored on the Mission 43 B2 manifest
   (SHA-256 `2fb08c92…46b72`): **27/27 events with front + audio + back**,
   every front/audio cache hash re-verified (0 mismatches); manifest
   `data/manifests/m3_multimodal_replay_manifest.json` (SHA-256
   `3c720167…bbbb`); coverage in `results/m3_mm_assembly/`.
9. **Label corpus census** — 821 cache files: back-camera detections are
   92.5% `side`, 1.4% `rear` (corpus-scale confirmation that both cameras
   are lateral and positive rear confirmation is geometrically starved).
10. **Access-classification manifest repaired** — the two unclassified
    test files (one pre-existing Mission 44 file, one Mission 3 file)
    received UNKNOWN/pending-review entries per the generator's own
    convention; tools suite passes **58/58**; manifest now covers 170
    test files.

## 4. What remains gated, and the exact unlock path

Governed replay of EXP1–EXP5 and EXP10 requires, in order:

1. **Stage-2.1 human review (HUMAN — the researchers only).** Per-event
   review records created through `annotation.review_session` from the
   adopted proposals, an independent second review, adjudication, a
   media-access authorization, and a READY verdict from
   `annotation.readiness_cli`, which alone issues
   `data/governance/stage21_promotion_receipt.json`. The step-by-step
   work package is in the Blocker B analysis (§8). No statement,
   adoption, or agent action substitutes for this.
2. **Decision records (DECISION — drafted).** v2 adoption (D2) and the
   M4 premature-opening definition (D3) were decided on 2026-11-09; the
   R04 scope (D4) and split (D5) recommendations are staged. Formal
   records are created from the allowlisted researcher's own statements,
   transcribed verbatim through the project owner (LEG-EXEC precedent),
   with all hash bindings computed by repository code.
3. **Execution authorizations (D7 — last).** AUTH-DESCRIPTIVE-EVAL-EXEC
   (and EVAL-AUTH for official evaluation), issued once the above exist.

Until step 1 happens, the descriptive gate's five live bindings cannot
all verify, and any decision-level number produced anyway would be
fabrication. The programme therefore stops here, deliberately.

## 5. Decision register (Mission 3)

| ID | Decision | Status |
|---|---|---|
| D1 | Signing route: researcher statements via the project owner, agent transcription (LEG-EXEC precedent) | AGREED 2026-11-09 |
| D2 | Canonical policy: **v2 adopted** (v1 frozen baseline; RULE_3C deviation from D-004 explicitly recorded) | DECIDED 2026-11-09; formal record pending statement |
| D3 | Premature opening: **M4 primary**, v9 sensitivity on the 11 sync events; other three protocol choices as documented | DECIDED 2026-11-09; formal record pending statement |
| D4 | R04 scope: accept the 11 CALIBRATION_SUPPORTED events | RECOMMENDED; pending statement |
| D5 | Split: descriptive evaluation over the full 27-event cohort; no generalization claim | RECOMMENDED; pending statement |
| D6 | Stage-2.1 human review work package | PREPARED; researcher work |
| D7 | AUTH + EVAL-AUTH records | DRAFTED; issued last, after D2–D6 |

## 6. Experiment status (detail: EXPERIMENT_REGISTRY.csv)

- COMPLETE (synthetic): EXP6 failure injection, EXP7 contradictory
  inputs, EXP9 fault recovery; EXP8 synthetic arm.
- HISTORICAL (authorized, Phase 10.1): the v1-vs-v2 paired comparison on
  the 11 sync events — v1 clears 0/11, v2 clears 6/11.
- NOT EXECUTED (gated): EXP1, EXP2, EXP3, EXP5, EXP10 on original data.
- NOT EXECUTED (engineering not built): EXP4's stateless comparator.

## 7. Deliverables

This package (`docs/generated/final_research/`, 21 items incl.
FILE_HASH_MANIFEST.sha256) plus the committed Mission 3 code and results:
the multimodal engine subclass + its tests, the synthetic battery script
+ both runs' outputs, the two manifest builders + classification fix
scripts, the 27-event multimodal manifest + assembly coverage, and the
classification-manifest update. Exact paths are listed in the mission
commit(s) following `25bab63`.

## 8. The one-paragraph summary for the professor

The architecture is implemented and its perception layer is fully
evaluated (audio event agreement: precision 54.6%, recall 92.3%,
specificity 0% at the frozen threshold — a real, reportable weakness).
The frozen v1 policy provably cannot complete departures on this rig
(0/11); the adopted v2 policy fixes the mechanism (6/11) and passes all
46 synthetic behaviour checks, with its one deviation from the founding
decisions explicitly recorded. The remaining step to a complete
decision-level evaluation is not engineering: it is the Stage-2.1 human
review chain, specified as a work package, after which the assembled,
hash-verified 27-event inputs and the gated replay can run unchanged.
