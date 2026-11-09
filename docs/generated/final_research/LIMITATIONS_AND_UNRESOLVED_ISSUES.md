# Limitations and Unresolved Issues

Every limitation below is stated with its consequence for interpretation.
Nothing here is remediable by re-analysis; items marked HUMAN require
researcher work, items marked DECISION require a recorded researcher choice,
items marked DATA cannot be fixed with the existing recordings.

## Dataset limitations

1. **Single site, daytime only (DATA).** All 27 events come from one crossing
   (`crossing_A`) in daytime. Protocol V2's cross-site variation objective
   (OBJ-07) is unattainable; no generalization claim to other crossings,
   lighting, weather, or train types is supported.
2. **Small, imbalanced cohort (DATA).** 23 train / 3 no-train / 1 engine-only
   events. The engine-only event is always reported separately; the two
   cameras of one event are never counted as two samples. Event-level
   denominators are small; the programme reports counts and paired outcomes,
   not population estimates.
3. **Short recordings truncate the departure phase (DATA).** Events 002 and
   006 end 0.8 s and 2.8 s after the last possible departure confirmation —
   less than the ~3.2–3.6 s a clearance dwell needs. Their non-clearance is a
   recording-length artifact, not policy behaviour.
4. **Camera geometry (DATA).** Both cameras are lateral trackside units; no
   site survey exists. `rear` viewpoints are rare and late by geometry, which
   is the root cause of the v1/v2 policy dilemma (Blocker A).
5. **Synchronization scope (DATA).** Cross-camera offsets are validated
   (CALIBRATION_SUPPORTED) for only 11 of 27 events. All dual-camera,
   shared-timeline claims are restricted to those 11; elsewhere only
   independent-camera statements are legitimate.
6. **Audio pairing gaps (DATA).** In the Mission 43 assembly, 2,717 of 6,614
   frames have no paired audio window. Missingness is preserved, never
   backfilled; multimodal denominators differ per event and are reported.

## Ground-truth limitations

7. **No canonical ground truth exists (HUMAN).** Zero Stage-2.1 records;
   the promotion chain (records → second reviews → readiness receipt) has
   never been completed. All Mission 43+ results are relative to
   **researcher-adopted AI-assisted references**, and are labelled as such.
8. **Adoption is not independent observation (HUMAN).** The researcher's
   statement that manual annotations matched the AI ones was never stored as
   separate observations: no inter-rater agreement, no human-vs-AI error
   rate, and no independent verification rate can be computed.
9. **Missing annotation products (HUMAN/DATA).** Zero bounding boxes, zero
   audio window labels, zero horn offsets, horn status null for 3 events.
   Detection-level and window-level metrics are structurally uncomputable;
   nulls remain null in every table.
10. **Legacy Phase 11 inventory is fabricated-approval material (—).**
    `docs/PHASE11_EVENT_INVENTORY.csv` is marked INVALID_FABRICATED_APPROVAL
    and is never cited as evidence anywhere in this package.

## Method and governance limitations

11. **Decision-level experiments on original data remain gated (HUMAN).**
    The policy and premature-opening decisions were taken on 2026-11-09
    (v2 adopted; M4 primary) and the decision records are drafted for the
    allowlisted researcher's statements. Until the Stage-2.1 human review
    exists and the AUTH records are issued, the governed replay cannot
    run. This package therefore reports the programme as **partially
    completed** (see the completion report) rather than dressing
    perception results as decision results.
12. **Signing authority rests with one allowlisted identity (DECISION —
    route agreed).** `raihankabirrahu@gmail.com` is the sole entry in
    `authorized_reviewers.json`; the repository owner is not on it.
    Statements come through the project owner and are transcribed verbatim
    (LEG-EXEC precedent); the drafted package is
    DECISION_PACKAGE_FOR_RAIHAN (staging, Mission 3 working records).
13. **v2's RULE_3C deviates from founding D-004 (DECISION — taken).**
    Disappearance confirmation is the only workable departure pathway on
    this rig's geometry. The deviation was **explicitly recorded in the
    2026-11-09 adoption** of v2 as canonical experimental policy, with
    this limitation attached; v1 remains the frozen baseline. The formal
    decision record follows the researcher's transcribed statement.
14. **Frozen descriptive scope is narrower than Protocol V2 (—).** The
    9-metric descriptive scope cannot express every Protocol V2 endpoint;
    supplementary analyses are labelled supplementary and never folded into
    the frozen scope or its hash bindings.
15. **Historical test-suite state (—).** The guarded suite historically
    reports 3,700 passed / 84 failed / 31 errors, where the 115 non-passing
    cases are classified as protected-dependency policy exceptions
    (Mission 43). The Mission 3 re-run and triage are reported in
    SOFTWARE_TESTING_REPORT.md; no assertion was weakened to change a count.

## Unresolved issues carried to the professor handoff

- Formal decision/authorization records — statements drafted (D2–D7);
  transcription awaits the allowlisted researcher's confirmations.
- Stage-2.1 human review commissioning — HUMAN work package prepared (Blocker B §8).
- Novelty positioning — no systematic literature review exists in the repo (OBJ-09, OPEN); the paper stage must do this work rather than inherit the retracted docx claims.
- B5 (back+audio) identification assumption — the single per-event audio stream is front-extracted; treating it as the back condition's audio requires an explicit decision, default NOT assembled.
