# Phases 12–16 Research Contracts: Scope and Limitations

**Status:** Metadata-only safeguards; not an authorization package and not an
execution plan. These contracts are not connected to evaluation, ablation,
profiling, field-capture, or publication runners.

`src/railway_detection/research_contracts.py` provides narrow mechanical
checks over caller-supplied metadata. Passing any check is not permission to
run a phase, evidence that its prerequisites have actually been met, or a
scientific finding.

## What the checks establish—and what they do not

| Check | Mechanical property checked | Not established |
|---|---|---|
| Event split | Nonempty train/val/test event-ID lists with no repeated IDs | Researcher approval of the split, absence of upstream dataset leakage, or suitability for evaluation |
| R04 camera scope | Declared dual-camera events must appear in a caller-supplied accepted-sync set | Calibration validity, human acceptance, or the researcher's in-scope event decision |
| Phase prerequisite checklists | Strict boolean assertions are listed as present/missing | Authentic approvals, gate verdicts, evidence, or authorization; callers can assert `True` without proof |
| Ablation descriptions | One-factor ablation descriptions, baseline/config-hash shape, and prohibited flags | Execution safety, actual config identity on disk, scientific validity, or authorization |
| Tick-log comparison | Two supplied nonempty byte strings are exactly equal | That either log came from a valid, authorized, reproducible, or representative run |
| Evidence references | Explicit claim-ID-to-path mapping resolves to repository files and avoids specified unsafe paths | That file contents support the claim, that a claim is true, or that disclosure/publication is authorized |

## Evidence-reference boundary

The evidence helper requires an explicit mapping from a nonempty claim ID to
one or more repository-relative file references. It checks path resolution,
repository containment, file type, and a small set of prohibited path classes.
**File existence establishes only path traceability. It does not establish
semantic evidence support or authorization.** An unrelated or empty-but-present
artifact can pass the path check; the function does not read, interpret, or
validate scientific claims in artifact contents.

No semantic claim validator is implemented. If a future, separately authorized
change adds one, it must require explicit claim-to-evidence links and may check
only claim types with predeclared objective validation rules. All other support
judgments remain for qualified human/researcher review; a generic file-existence
check must never be represented as scientific validation.

## Authorization and integration boundary

Caller-supplied checklist booleans are self-reported metadata, not verified
authorization. R04 membership is likewise a caller assertion, not a calibration
review. The helpers do not load approval records, make policy decisions, or
start any runner. Keep them disconnected from execution paths unless a future
phase plan explicitly authorizes and specifies integration.

Evaluation, real-event ablations, profiling, field activity, legacy-record
invalidation, and publication release remain separately gated. A passing
synthetic test or metadata contract does not waive any gate.
