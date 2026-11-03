# Paper Revision Proposal — independent-camera descriptive benchmark

> **PROPOSED — NOT APPLIED — NOT APPROVED.** `docs/PAPER_DRAFT_DESCRIPTIVE_BENCHMARK.md` (untracked) is **unchanged**. This document lists the edits and replacement text the researcher may adopt. No result exists: every results cell stays `[RESULTS PENDING]`.

## 1. Change list against the current draft

| Draft location | Problem | Proposed resolution | Decision |
|---|---|---|---|
| Title | "Front-Camera Vision, Acoustic, and Fusion Baselines" — M4/M5 need the back-stream replay | Proposed title: *"An Auditable Independent-Camera Descriptive Benchmark Framework for Level-Crossing Protection: Outcome Definitions, Governance and Provenance"* | RD-052, RD-053 |
| Header (author line) | lists an autonomous agent as an author | human authors only (see author block below); AI-use disclosure instead | RD-054 |
| §2 Research questions | RQ1–RQ4 are front-sensor performance questions | descriptive-benchmark RQs (§2 below) | RD-051 |
| §3.3 Conditions | B0–B2 are front-only | keep B0–B2 for front-dependent outcomes; add the back-stream condition(s) needed for M4/M5 (named in the experiment-design reconciliation); not executed | RD-035 |
| §4.3 Left-censoring | T0 left-censoring quoted as 23/23 here but 20/23 in the dataset audit | state the count only from approved ground truth; until then "count pending approved GT" | TF-16 |
| §6.1 "Front-Camera Benchmark Framing" | wrong frame | "Independent-camera descriptive framing": front-stream replay → front-dependent outcomes; back-stream replay → M4/M5; fused replay exploratory only | RD-015, RD-028, RD-052 |
| §6.2 comparison table | says the evaluator "defaults to [T1,T4)" (false: no default exists); says the decision is "pending [D-10]" (M4 is now selected, unbound); says both profiles are non-computable because of R04 | replace the table with the M4/M5 contract; v9 `[T1,T4)` kept as a labelled historical alternative; M4 is computable on the back-stream replay without R04 | TF-14, RD-014 |
| §7.1 tiers | "Tier 3 requires validated R04" | Tier 3 requires the back-stream replay and an approved T4; R04 only for fused exploratory | TF-14 |
| §7.2 / Table 1 | POR/CL/ECD "NON-COMPUTABLE" for front conditions is correct but incomplete | add back-stream columns; add rows M5 (counts only), M4 not-evaluable counts by reason, MTR with lead-in screen counts; no combined score | RD-017, RD-021, RD-022 |
| §7.3 statistics | confirm no inferential language | Wilson 95 % intervals and descriptive summaries only | RD-023 |
| Occupancy | any "occupancy" duration | none reported | RD-018 |
| Table 4 engine | one descriptive row | only if approved GT ever exists; never pooled | RD-024 |
| §15 Author contributions | agent listed | replace (below) | RD-054 |
| §16 Data availability | "controlled research access" | future release plan (§6 below) | RD-055 |

## 2. Proposed research questions (descriptive benchmark)

- **RQ1 (outcome definition and auditability).** Can premature opening (M4) and never-protected (M5) be defined, classified and reported so that incomplete replay evidence is never counted as safe and never as never-protected?
- **RQ2 (camera roles).** Which outcomes are computable from a front-stream replay, which from a back-stream replay, and which require an unresolved inter-camera offset?
- **RQ3 (descriptive behaviour).** *Conditional on approved ground truth and authorization:* how does the frozen pipeline behave, event by event, on the 27-event single-site cohort? (Results pending.)
- **RQ4 (empirical bounds).** What can and cannot be claimed from a single-crossing, two-session cohort of 23 train events? (Retained from the current draft.)

## 3. Claims (RD-053)

**May be claimed:** a specified and auditable benchmark design; explicit, tested outcome definitions with fail-closed handling of incomplete evidence; a governance and provenance framework; honest reporting of what is not evaluable.
**May not be claimed (no approved evidence):** any MTR/POR/lead-time number; that any policy "improves safety"; cross-site, cross-device or deployment performance; SIL or standards compliance; that full crossing occupancy duration is measurable; that fused analysis is primary; that the 20/23 calibration criterion is met.

## 4. Limitations to add or sharpen
Single site, two sessions, handheld devices; single reviewer unless an external audit reviewer is appointed; M5 is replay-relative; engine event N = 1 (separate); full occupancy duration is deferred (no valid same-camera pair; cross-camera alignment not approved); thresholds and ROI are not scientifically approved; the decision policy was developed after seeing these recordings; no additional recordings are planned in this study; historical B0–B7f outputs are diagnostic only.

## Proposed author block

Human authors only. Names, affiliations, ORCIDs and contribution roles are **to be supplied by the researcher**; none is invented here.

```
[Author 1 — name, affiliation, ORCID: to be supplied by the researcher]
[Author 2 …: to be supplied by the researcher]
Corresponding author: [to be supplied by the researcher]
```

## 5. AI-use disclosure statement — DRAFT (for the researcher to edit and own)

> *DRAFT — not final.* "Portions of the software analysis, test construction and drafting of this manuscript were assisted by an AI coding and writing assistant operating under the authors' direction. The assistant is not an author and bears no responsibility for the content; all scientific decisions, ground-truth judgements and approvals were made by the human authors, who reviewed and take responsibility for the work. Where AI-generated candidate annotations existed, they were not used as ground truth."

(Journal-specific wording and placement must follow the target venue's policy, which is undecided.)

## 6. Future release plan (RD-055) — plan only
Venue undecided. After a privacy review of crowd footage and explicit researcher approval: release code and *approved* annotations with hash manifests; **no raw media**. Nothing is released by this proposal.

## 7. Statements that must stay true in any revision
Full occupancy duration is deferred. Real descriptive results and synthetic-test outputs are never mixed; synthetic tests are labelled synthetic. Independent-camera analysis is primary; R04 fusion is exploratory.
