# RESEARCH DECISION RECORD — NO EVENT SPLIT (OPTION A)

- **Decision ID:** SPLIT-DECISION-OPTION-A-2026-11-09
- **Decided by:** Raihan Kabir Rahu (raihankabirrahu@gmail.com), the authorized researcher
- **Recorded:** 2026-11-09, transcribed by the agent from the researcher's adopted
  statement, relayed through Mohammad — the LEG-EXEC agent-transcription precedent.
  Unsigned; no signature is claimed or implied.
- **Subject:** `data/manifests/phase12_event_split_decision.json` — NOT created, by decision.

## Researcher statement (verbatim, as adopted)

> I decide that no train/val/test split record is created for this project. The evaluation is descriptive over the full 27-event cohort from a single crossing, and a partition would support no generalization claim. The official Phase 12 evaluation path remains unexercised by this decision; if a future venue requires it, the partition will be decided and recorded then.

## Why no record file exists

The split-decision schema requires non-empty train/val/test partitions. Encoding
this decision would require inventing a partition the researcher did not choose,
so no JSON record was created. The readiness gate will continue to report
EVENT_SPLIT_DECISION_MISSING; that blocker is now a documented decision, not an
oversight. Governed descriptive evaluation proceeds via the descriptive
execution authorization, which does not require a split.

## Allowlist change recorded the same day

On the researcher's explicit instruction (Phase 11.7 Decision 2), Mohammad
Tanvir Ahmed (elaf85777@gmail.com) was added to
`data/ground_truth/authorized_reviewers.json` as an authorized Stage-2.1
reviewer, serving as the independent second reviewer alongside the researcher
as primary reviewer.
