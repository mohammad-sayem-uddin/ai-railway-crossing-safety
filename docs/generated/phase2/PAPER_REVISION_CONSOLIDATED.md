# PROPOSED — Consolidated Paper Revision (independent-camera descriptive benchmark)

> **PROPOSED — NOT APPROVED — NOT APPLIED — NO RESULTS EXIST**
>
> Agent-prepared (Mission 5B, Phase 2). `docs/PAPER_DRAFT_DESCRIPTIVE_BENCHMARK.md` (SHA-256 `03444930ec0d73e9dad16a2b510511c61e9a1302e3e6a25cf83307d81a26ea78`) is **unchanged**. This is a skeleton and a list of corrections for the researcher to adopt, edit or reject; the researcher owns the manuscript and every claim in it (RD-053, RD-054). It is built from the draft, the Mission 5A paper proposal, RD-001…RD-055, and the proposed protocols v9.1.1 and v7.1.1. It contains **no empirical value**. Author identities, affiliations, ORCIDs and the publication venue are **not invented** and are left as placeholders.

---

## 1. Proposed title

*An Auditable Independent-Camera Descriptive Benchmark Framework for Level-Crossing Protection: Outcome Definitions, Governance and Provenance* (RD-052, RD-053). The researcher may replace it. The current draft title ("…Front-Camera Vision, Acoustic, and Fusion Baselines") is not retained because the primary outcomes (M4, M5) need the back-stream replay.

## 2. Research motivation

Roadside vision-and-audio sensing is a candidate low-cost alternative to wayside train-detection hardware at level crossings, but offline evaluations of such systems are easily overstated: incomplete replay evidence is read as safe behaviour, left-censored recordings distort lead times, sensor clocks are unsynchronized, and tiny single-site cohorts are presented as evidence of safety. This work specifies, before any evaluation, how outcomes are defined and how incomplete evidence is handled, so that a later descriptive benchmark is auditable. The motivating background in the current draft (§1) carries general statements about passive crossings and sensing alternatives; they are **uncited in this skeleton** and need sources before use.

## 3. Proposed research questions (RD-051)

- **RQ1 (outcome definition and auditability).** Can premature opening (M4) and never-protected (M5) be defined, classified and reported so that incomplete replay evidence is never counted as safe and never as never-protected?
- **RQ2 (camera roles).** Which outcomes are computable from a front-stream replay, which from a back-stream replay, and which require an unresolved inter-camera offset?
- **RQ3 (descriptive behaviour).** *Conditional on approved ground truth and authorization:* how does the frozen pipeline behave, event by event, on the 27-event single-site cohort? **(Results pending.)**
- **RQ4 (empirical bounds).** What can and cannot be claimed from a single-crossing cohort of 23 train events?

## 4. Study design

A **single-site, fixed-crossing, descriptive benchmark** and software replay study. No train/validation/test split; no official event split (the full cohort is described). No hypothesis test; no claim of improvement. The frozen perception models, configuration and decision policy are not modified for the study. Independent-camera analysis is primary; the fused (R04) analysis is exploratory and limited to the existing 11-event scope. No additional recordings are collected. The study is a design and methodology contribution until an authorized evaluation exists.

## 5. Dataset description

27 events recorded at one crossing: 23 train events (46 streams), 3 no-train events (6 streams), 1 engine-only event (2 streams), each with a front and a back camera; the quarantined historical duplicate is excluded. Events are cohort-qualified (`train_events/event_001`, …) because event numbers repeat across cohorts. The number of capture sessions, their dates, the acquisition hardware (handheld or tripod) and the rolling-stock mix **must be taken from approved metadata**; the source documents disagree (§15). Camera clocks are independent and unsynchronized; no hardware genlock or time-protocol synchronization exists; inter-camera offsets are unresolved (R04). No-train exposure is about 120.8 camera-stream-seconds in total; concurrent overlap is unresolved.

## 6. Camera-specific evaluation strategy

| Replay stream | Outcomes | Notes |
|---|---|---|
| Front (`B0`, `B1`, `B2`) | MTR with the physical lead-in screen; warning lead time | `B1` (audio-only) yields descriptors only because audio is supporting evidence under the frozen policy (RD-030) |
| Back (`B0_back`, `B0_back_stateless`, `B2_back` — *provisional names*) | M4, M5, clearance latency | $T_4$ is a back-camera time; replay configurations to be confirmed by the researcher; back-stream audio availability not verified |
| Fused (R04) | exploratory comparison | existing 11-event scope only; no official dual-camera scope; the 20/23 calibration criterion is not claimed |

Front and back outputs are never merged into one score. Acoustic synchronization offsets never shift human ground-truth timestamps (RD-027).

## 7. Metric definitions

Defined in the protocol (v9.1.1-PROPOSED §5.2.1, §5.7) and the metric table of `EXPERIMENT_DESIGN_CONSOLIDATED.md` §4; summarized here.

- **M4 premature opening (primary).** After the first retained blocked step $t_{\text{blocked}} < T_4$, did any retained step strictly inside $(t_{\text{blocked}}, T_4)$ show the passage unblocked or an `OPENING`/`OPEN` gate state? Per-event yes/no. Needs at least one retained interior step; otherwise *not evaluable* (`no_steps_in_protection_interval`) — never safe.
- **M5 never protected (companion, counts only).** Zero-origin replay that reaches $T_4$ with no blocked step before $T_4$. A late start or a start at or after $T_4$ is *not evaluable*.
- **MTR (secondary).** Barrier not blocking at $T_1$, among events that pass the physical lead-in feasibility screen. `insufficient_lead_in` is not a system failure; `lead_in_unverifiable` (including a censored $T_0$ of unknown direction) is not evaluable. The literal Design-M3 rule is reported beside the physical screen as a secondary comparison; it has not yet been propagated into the evaluation record and summary (a Phase 4 requirement). The minimum block latency is a synthetic value from the frozen configuration and not an approved threshold.
- **Timestamps** use a one-microsecond grid with strict comparisons and no timing tolerance.
- **Limitation (must appear in the paper):** replay steps are discrete observations; they do not establish the continuous state of the barrier between observations; no sampling-density threshold is defined.
- **Deferred:** full crossing occupancy duration (RD-018). **Out of scope:** the design-document metrics M1, M2, M6–M10, V1, F1, D1.
- Engine events are excluded from pooled M4/M5/train aggregates; no-train false-alarm analysis is separate; fault injection is separate.

## 8. Statistical reporting plan (RD-023)

Descriptive statistics only: counts, Wilson 95 % intervals, medians and ranges, and counts of not-evaluable events **by reason**. No p-values, no McNemar/Wilcoxon/Holm/bootstrap contrasts, no effect sizes, no significance language. Per-metric evaluable denominators with explicit exclusion reasons; censored events are excluded from point estimates and counted by reason (RD-011). No combined or composite score. Intervals describe variation among passages recorded at this site and are not bounds on field failure probability.

<!--RESULTS-TABLES-->
| Outcome | Front `B0` | Front `B1` | Front `B2` | Back `B0_back` | Back `B0_back_stateless` | Back `B2_back` |
|---|---|---|---|---|---|---|
| M4 (evaluable / premature) | NOT COMPUTABLE | NOT COMPUTABLE | NOT COMPUTABLE | [RESULTS PENDING] | [RESULTS PENDING] | [RESULTS PENDING] |
| M5 count | NOT COMPUTABLE | NOT COMPUTABLE | NOT COMPUTABLE | [RESULTS PENDING] | [RESULTS PENDING] | [RESULTS PENDING] |
| MTR (evaluable / missed) | [RESULTS PENDING] | NOT COMPUTABLE | [RESULTS PENDING] | NOT COMPUTABLE | NOT COMPUTABLE | NOT COMPUTABLE |
| Not-evaluable counts by reason | [RESULTS PENDING] | [RESULTS PENDING] | [RESULTS PENDING] | [RESULTS PENDING] | [RESULTS PENDING] | [RESULTS PENDING] |
| Warning lead time | [RESULTS PENDING] | NOT COMPUTABLE | [RESULTS PENDING] | NOT COMPUTABLE | NOT COMPUTABLE | NOT COMPUTABLE |
<!--/RESULTS-TABLES-->

The engine-only case study, the no-train counts, the fault-injection section and the exploratory fused comparison are likewise **[RESULTS PENDING — AUTHORIZED EVALUATION NOT EXECUTED]**.

## 9. Limitations (RD-053; to be stated in the paper)

Single site; a small number of sessions; one cohort of 23 train events, which yields wide intervals; no cross-site, cross-device, weather or night generalization claim; recordings begin after the train is visible in many events (left-censored $T_0$); about 120.8 stream-seconds of no-train exposure is insufficient for a false-alarm rate; a single engine pass; M5 is replay-relative and has no density requirement; sampled replay does not establish continuous barrier state; the physical entry landmark and therefore $T_2$ and full occupancy duration are deferred; the decision policy and its constants were developed after seeing these recordings (pilot contamination) and carry no scientific approval; barrier timing is simulated; ground truth is single-reviewer unless an external audit reviewer is appointed; inter-camera offsets are unresolved; thresholds and ROI are not scientifically approved; historical B0–B7f outputs are diagnostic only; no additional recordings are planned in this study. No certification (SIL, EN 50126/50128/50129) is claimed or implied; the software must not be connected to physical actuators.

## 10. Reproducibility and provenance plan

- **Hash conventions.** Reports cite the *canonical-content* hash of a parsed configuration; a raw `shasum` of the same file differs. Both must be labelled. Frozen configuration: canonical `999a7970d4c47713a1b128f77939916a54bc99c24becd68e383aad2f1db5a42e`, raw file SHA-256 `b8ef5da052f002e75a2da0985add02a72d0d5684936263c14257aa12b0c9ac9a`. Decision policy raw file SHA-256 `c87c1432f473f84def46d343429c21bcd5329adcbce6cfdf7933de446a0c8575`. Checkpoint hashes are in the protocol (§3).
- **A commit hash alone is not enough.** The repository HEAD at Phase 2 (`d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`) does **not** contain most governing code, tests and documents, which are untracked. The reproducibility statement must cite the commit the researcher creates at Gate 2 together with the snapshot manifest.
- **Provenance records:** run identity (commit, configuration hash, checkpoint hashes, media-manifest hash, environment), per-stream completion records, cache-provenance bindings, evaluation-input manifests, preservation manifests with SHA-256 per governing file. The lead-in minimum latency is recorded with the canonical hash of the configuration that produced it.
- Hashes prove bytes, not behaviour. Environment importability, lock-file drift and clean-clone reproduction are **not verified**; no reproducibility claim is made.

## 11. Human-review and ground-truth governance

Ground truth follows three stages: AI-assisted candidate proposals (an external offline assistant, firewalled from the evaluated models, immutable), human frame-by-frame review recorded in an auditable history, and approved ground truth frozen by a manifest. **No approved ground truth exists**: the 27 legacy review files were invalidated (per the project's Phase 11.6 disposition record cited by the draft); all current proposals are unapproved candidates. Only the researcher can approve. Stage-2.1 review is proposed with: blind first pass for $T_1$/$T_2$/$T_4$, per-event direction verification, risk-based second-review triggers, adjudication by a separate entry that never overwrites original observations, unresolved disagreement stays `UNCERTAIN`, and a single allow-listed reviewer unless the researcher appoints others. Governance identifiers use `GOV-`, `EXP-`, `AUTH-`; every one of the pending approvals and authorizations is listed in the Phase 2 report. The paper may describe the governance design; it may not describe it as completed.

## 12. AI-use disclosure — DRAFT (for the researcher to edit and own)

> *DRAFT — not final.* "Portions of the software analysis, test construction and drafting of this manuscript were assisted by an AI coding and writing assistant operating under the authors' direction. The assistant is not an author and bears no responsibility for the content; all scientific decisions, ground-truth judgements and approvals were made by the human authors, who reviewed and take responsibility for the work. Where AI-generated candidate annotations existed, they were not used as ground truth."

Final wording and placement follow the venue's policy, which is undecided.

## 13. Authors, venue, release (RD-054, RD-055)

**Human authors only. No AI agent is listed as an author.**

```
[Author 1 — name, affiliation, ORCID: to be supplied by the researcher]
[Author 2 …: to be supplied by the researcher]
Corresponding author: [to be supplied by the researcher]
Contribution roles: [to be supplied by the researcher]
Publication venue: UNDECIDED
```
Release plan (plan only): after a privacy review of crowd footage and the researcher's explicit approval, release code and *approved* annotations with hash manifests; **no raw media**. Nothing is released by this proposal.

## 14. Claim boundaries (RD-053)

**The manuscript may claim:** a specified and auditable single-site benchmark design; explicit, tested outcome definitions with fail-closed handling of incomplete evidence; a governance and provenance framework; honest reporting of what is not evaluable.

<!--NOT-CLAIMS-->
**The manuscript must not claim:** cross-site, cross-device or unseen-crossing generalization; national-level or operational railway-safety improvement; proven accident reduction; any measured MTR, M4, M5 or lead-time number before an authorized evaluation; statistically significant improvements; that any policy or architecture improves safety; that full crossing occupancy duration is measurable; that fused analysis is primary; that the 20/23 calibration criterion is met; a completed real-world evaluation before it has been authorized and executed; certification or standards compliance.
<!--/NOT-CLAIMS-->

## 15. Corrections the current draft needs

| # | Location in the draft | Problem | Proposed handling |
|---|---|---|---|
| 1 | Header | An autonomous agent is listed as an author; a target venue is named | human authors only; venue undecided (RD-054/055) |
| 2 | §2 RQs | front-sensor performance questions | RQ1–RQ4 above |
| 3 | §3.3, §5.3 | "primary benchmark strictly restricted to front-camera-only (B0–B2)" | independent-camera framing; back-stream conditions for M4/M5 (RD-035) |
| 4 | §3.4 INV-1 | "audio may provide corroborating evidence to hold **or initiate** warning" | audio is supporting evidence only (RD-030) |
| 5 | §4.1 | sessions given as 3 and 7 October 2026; hardware "tripod-mounted" | conflicts with the design document (S1 = 2026-09-14, S2 = 2026-10-04; "handheld") — take from approved metadata |
| 6 | §4.2 | rolling-stock description (12–88 railcars, freight/intermodal) and no-train content descriptions | not supported by any approved record in this phase; remove or source |
| 7 | §4.3 | "23 of 23 train events" left-censored | other documents say 20/23; state the count only from approved ground truth |
| 8 | §6.2 | claims the evaluator "defaults to [T1,T4)" and that the choice is pending | no default exists; M4 is selected (unbound); replaced by the M4/M5 contract |
| 9 | §7 Tier 3 | POR/CL/ECD "non-computable" and "requires validated R04" | M4/M5 are computable on the back-stream replay without R04; excess closed duration needs one clock |
| 10 | §7.2 WLT | defined with $T_2$ | $T_2$ is deferred (RD-006); use $T_1$ |
| 11 | §7.2 Metric 4 | POR defined on $[T_1, T_4)$ | replaced by M4 |
| 12 | §8 Table 4 | an engine-only $T_3 \equiv T_4$ value taken from a candidate | candidate values are unapproved; no value is reported |
| 13 | §10, §12 | "daylight only, no night, regional freight", "annual or hourly rates" | verify against approved metadata before use; an earlier protocol draft mentions a night stratum — conflict unresolved |
| 14 | §13 | `decision_engine.py` is labelled with SHA-256 `c87c1432…` | that value is the raw hash of `configs/decision_policy_v1.yaml`; the engine source file has a different hash. Also label canonical versus raw hashes |
| 15 | §13 | repository commit cited as the reproducibility anchor | the commit omits most governing files; cite the Gate 2 commit and snapshot |
| 16 | §14 | multi-site roadmap with "≥ 1000 train events, ≥ 500 hours" | invented targets; remove or mark as aspiration with no commitment |
| 17 | §15 | contributions listed for an AI agent | replace with the author block and disclosure draft |
| 18 | §16 | "controlled research access" | future release plan (§13); no raw media |
| 19 | §18 refs 7–9 | bibliographic details of refs. 7–9 could not be confirmed here and look unreliable | verify each against the primary source or remove; **no literature search was performed in Phase 2** |
| 20 | §18 note | states all citations are "authentic, verified" | remove the assertion until each is verified |

## 16. Statements that must stay true in any revision

Full occupancy duration is deferred. Real descriptive results and synthetic-test outputs are never mixed, and synthetic tests are labelled synthetic. Independent-camera analysis is primary; R04 fusion is exploratory (11-event scope; `train_events/event_010` is not added). No inferential statistic is presented as approved. Engine events stay outside pooled aggregates. The wording `[RESULTS PENDING]` stays until an authorized evaluation exists.
