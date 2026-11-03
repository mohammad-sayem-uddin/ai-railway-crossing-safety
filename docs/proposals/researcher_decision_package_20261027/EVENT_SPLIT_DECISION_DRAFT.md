# DRAFT — NOT APPROVED — NOT AUTHORIZATION

## Event-Level Split / Analysis Framing Template

**Decision ID:** R-SPLIT-20261027
**Status:** DRAFT — NOT APPROVED — NOT AUTHORIZATION
**Decision-maker:** ____________________
**Decision date (UTC):** ____________________

### Repository evidence

- Current `data/splits/705d388743ea/` is an image/dataset split, not a Phase 12 event decision.
- Required `data/splits/phase12_event_split_decision.json` is absent.
- The corpus is a single crossing with limited sessions; repository documents warn that
  cross-crossing generalization cannot be claimed.
- Existing metadata does not establish a unique leakage-safe group-disjoint event split.

### Options

- [ ] **A — Full-cohort descriptive benchmark:** evaluate all 27 events descriptively; make
  no held-out/generalization claim. Requires an approved contract/schema decision supporting
  the framing before manifest construction.
- [ ] **B — Two-session exploratory contrast:** session-shift comparison; explicitly report
  confounding and small Session-2 train count.
- [ ] **C — Defer official evaluation:** wait for multi-crossing data.
- [ ] Other researcher-defined framing: ____________________

Selected framing: ____________________
Partitions or full-cohort declaration: ____________________________
Session/crossing leakage statement: ______________________________
Cohort exclusions/eligibility: ___________________________________
Generalization claim permitted: _________________________________
Rationale: ______________________________________________________

**Do not write this template to `data/splits/phase12_event_split_decision.json`.**
