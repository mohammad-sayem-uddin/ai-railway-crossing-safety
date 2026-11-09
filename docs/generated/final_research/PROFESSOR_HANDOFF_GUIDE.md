# Professor Handoff Guide

## What this package is

The completed research programme for the Train Gate Automation project:
a two-camera, audio-assisted, temporal decision architecture for railway
crossings, evaluated as far as the project's own governance permits, with
every gap stated rather than filled. The professor owns the paper: venue,
framing, authorship, submission.

## How to read it (15 minutes)

1. `FINAL_RESEARCH_COMPLETION_REPORT.md` — what was attempted, what was
   executed, what remains blocked and exactly why. Start here.
2. `ORIGINAL_RESEARCH_OBJECTIVES_STATUS.csv` — the founding objectives,
   one by one: achieved / partially achieved / not achievable, with the
   evidence pointer for each.
3. `LIMITATIONS_AND_UNRESOLVED_ISSUES.md` — the honest boundary of the
   work (single site, adopted AI-assisted references instead of canonical
   ground truth, audio specificity 0% at event level, v1's departure
   failure and v2's recorded D-004 deviation).

## The headline results

- Perception layer (executed, Mission 43, hash-verified): vision and
  audio caches over all 27 events; audio event-level agreement against
  the adopted references: precision 54.6%, recall 92.3%, **specificity
  0%** — the horn detector false-alarms on every horn-absent event at
  the frozen 0.37 threshold. This is a result, not a defect to hide.
- Policy layer (executed synthetically + on the 11 sync-validated events
  historically): the frozen v1 policy clears **0/11** events; the v2
  candidate clears **6/11** on identical inputs, and passes all 46
  synthetic behaviour checks. The mechanism is understood and documented
  (label conflation + RULE_7 self-interrupt; corpus evidence: the back
  camera's detections are 92.5% "side", 1.4% "rear" — both cameras are
  lateral, so positive rear confirmation is geometrically unavailable).
- Researcher decisions recorded for the paper's methods section: v2
  adopted as canonical experimental policy (v1 = frozen baseline) with
  the RULE_3C deviation from founding decision D-004 explicitly recorded;
  premature opening = M4 primary, v9 sensitivity.

## What only the researchers can still do

1. **Stage-2.1 human review** — per-event review records from the adopted
   proposals, independent second review, adjudication, readiness verdict,
   promotion receipt. This is the sole remaining lock on canonical
   decision-level evaluation of the original data; the work package
   (steps, tooling, effort) is specified in the completion report.
2. **Sign the decision/authorization records** — drafted statements are
   prepared for the allowlisted researcher to adopt verbatim; hashes are
   computed by the repository's own code at creation.
3. **Choose the venue and write the paper** — methodology, statistics
   conventions, and reproducibility notes in this package are written to
   be lifted into a manuscript directly.

## What was deliberately NOT done

No approvals, ground truth, human agreement, timestamps, or signatures
were fabricated; no execution gate was patched or bypassed; no threshold
was tuned on evaluation data (the 0.37 audio threshold is untouched);
historical reports and sealed test catalogs were preserved even where
they now fail against the (authorized) rewritten README; missing values
were kept missing. Where a deliverable could not be produced, the file
says so and why.
