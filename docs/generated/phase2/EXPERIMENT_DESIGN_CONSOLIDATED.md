# PROPOSED — Consolidated Experiment Design (independent-camera descriptive benchmark)

> **PROPOSED — NOT APPROVED — NOT HASH-BOUND — NO CONDITION EXECUTED**
>
> Agent-prepared (Mission 5B, Phase 2) from `docs/EXPERIMENT_DESIGN_FINAL.md` (SHA-256 `2e906c1e19426d2fa406fe626858b0b308fc6abb38510afd660768e954fbb407`, unchanged), the Mission 5A reconciliation `EXPERIMENT_DESIGN_RECONCILIATION_20261101_M5A.md`, the RD-001…RD-055 implementation matrix, the Phase 1 completion report, and the proposed protocols v9.1.1 and v7.1.1. `EXPERIMENT_DESIGN_FINAL.md` is a **non-binding reference** except where this document says an item is adopted (RD-001). This document records the researcher's *confirmed directions*; it is not a formal approval and creates no governance record. Every empirical field is empty and marked pending an authorized evaluation.

**Version:** 1.0-PROPOSED (consolidation)  **Date:** 2026-11-01

---

## 1. Authority and status vocabulary

| Term | Meaning in this document |
|---|---|
| **Researcher-confirmed direction** | An RD answer (RD-001…RD-055) the researcher confirmed in conversation. It is direction, not a signed governance artifact. |
| **Formal approval** | A researcher-authored on-disk governance record (e.g. `GOV-D1-PROTOCOL-AUTHORITY`). **None is created or implied here.** |
| **Agent-prepared proposal** | Everything in this folder. |
| **Execution authorization** | An explicit on-disk authorization for media access, review, promotion or evaluation. **None exists.** |

Authority order (RD-001): v7 governs ground-truth boundaries; v9 governs system and metric definitions; this design document is a non-binding reference. Its claim to supersede v9 is rejected; its inclusion of the engine event in M4/M5 is rejected (RD-024); its McNemar/Wilcoxon/Holm contrasts are rejected (RD-023); its new decision policy and audio authority are rejected (RD-029, RD-030).

## 2. Scope of the study

- **Single-site, fixed-crossing, descriptive benchmark** on a 27-event cohort: 23 train events (46 streams), 3 no-train events (6 streams), 1 engine-only event (2 streams) (RD-041). The quarantined historical duplicate is excluded by an explicit deny-list entry. The inventory is a recorded fact; formal inventory sign-off is pending.
- **No official event split** exists or is created (descriptive full cohort, RD-039; BR-13). No train/validation/test claim is made.
- **No additional recordings** are part of this study (RD-037).
- **Unit of analysis:** the event. Streams and ticks are not independent observations. Events recorded in the same session share geometry and background and are not independent samples of railway environments.
- Nothing here tests generalization to other crossings, weather, devices or mounting.
- Sessions are reported separately where the approved metadata supports it (RD-039). **The session dates differ between source documents (§14, item 9); none is asserted here.**

## 3. Independent-camera primary design (RD-015, RD-028, RD-035)

| Condition | Stream | Description | Outcomes it can feed | Status |
|---|---|---|---|---|
| `B0` | front | vision only | MTR (with screen), warning lead time | design only |
| `B1` | front | audio only | acoustic-detection descriptors (see note) | design only |
| `B2` | front | container-native front vision + audio fusion | MTR (with screen), warning lead time | design only |
| `B0_back` *(provisional)* | back | vision, stateful | M4, M5, clearance latency | design only |
| `B0_back_stateless` *(provisional)* | back | vision, stateless | M4, M5, clearance latency | design only |
| `B2_back` *(provisional)* | back | vision + audio | M4, M5, clearance latency | design only |
| Fused R04 | fused | exploratory only | exploratory comparison | **11-event scope only** |

- Front-dependent outcomes use the **front-stream replay**; $T_4$-dependent outcomes use the **back-stream replay**. Front and back outputs are reported separately and never merged into one score. No combined or composite score is defined.
- `B0_back`, `B0_back_stateless`, `B2_back` are **reversible naming conventions** (DEC-B05), not scientific approvals. The underlying replay configuration of each must be confirmed by the researcher; the legacy experiment runner uses B0–B7 labels with different meanings (its B2 is dual-camera and stateless). Back-stream audio availability has not been verified. No condition has been executed.
- **Note on `B1`:** the frozen policy makes audio supporting evidence only (`RULE_2_AUDIO_SUPPORT_ONLY`, RD-030), so an audio-only condition cannot produce gate-level outcomes of its own. How B1 is reported is an open researcher question (§14, item 3).
- The E1–E10 matrix of `EXPERIMENT_DESIGN_FINAL.md` is **not** restored as the primary execution matrix. Its C×T×P×A factor grammar is not adopted.
- **Fused R04 analysis is exploratory only.** It is limited to the **existing 11-event exploratory scope** (RD-026; `GOV-D4-R04-SYNCHRONIZATION` pending). No official dual-camera scope exists. `train_events/event_010` is **not** added to that scope, and no 12-event scope is created or implied. The design's "fused is primary if ≥ 20/23 events calibrate" criterion is superseded; it is not claimed met. Acoustic synchronization offsets never shift human ground-truth timestamps (RD-027).
- Historical B0–B7f outputs are diagnostic only and are never cited as results (RD-036).

## 4. Metric table

"Not evaluable" always carries a stated reason and is counted by reason (RD-011, RD-040). No outcome-dependent global exclusion exists. Censored events are excluded from point estimates and counted by reason; any bound is exploratory only (RD-011).

| Metric | Scientific meaning | Required camera stream | Required GT boundaries | Evaluability conditions | Denominator | Known limitations | Implementation status |
|---|---|---|---|---|---|---|---|
| **M4 premature opening** (primary, RD-022) | After the barrier is first observed blocked and before tail clearance, did the replay show the passage unblocked, or an `OPENING`/`OPEN` gate state? Per-event yes/no. | back-stream replay (fused: exploratory) | $T_4$ only (approved, observable, on the replay's clock) | $t_{\text{blocked}} < T_4$; replay reaches $T_4$ (unless a violation is witnessed); at least one retained step strictly inside $(t_{\text{blocked}}, T_4)$ | train events that are M4-evaluable; Wilson 95 % interval | sampled steps do not establish continuous state between observations; no density threshold; interior-empty events are not evaluable; a replay that starts already blocked cannot reveal an earlier close-and-reopen; single-site | implemented (`classify_m4`, Phase 1) |
| **M5 never protected** (companion, counts only, RD-017) | Replay began at the zero origin, reached $T_4$, and showed no blocked step before $T_4$. | back-stream replay | $T_4$ | first retained step at the zero origin; last step $\ge T_4$; no blocked step before $T_4$ | count only; no rate; outside the M4 denominator | replay-relative ("never protected by that replay's sensing"); no sampling-density requirement; late-start and start-at-or-after-$T_4$ replays are not evaluable, never M5 | implemented (Phase 1) |
| **MTR, physical screen** (secondary, RD-021/022) | Was the barrier not blocking when the train reached $T_1$, given enough physical lead-in? | front-stream replay | $T_1$ (front clock); $T_0$ with a known censoring direction for the screen | $T_1$ observable; if the screen is enabled, lead-in sufficient. `insufficient_lead_in` and `lead_in_unverifiable` are not evaluable and are **not** system failures | evaluable train events; Wilson 95 % interval | the minimum block latency is a synthetic value from the frozen configuration at its 0.2 s tick (about 3.6 s in Phase 1) and **not an approved threshold**; censored $T_0$ with unknown direction is unverifiable | implemented; screen **default-off**, unused by the official runner; wiring is Phase 4 |
| **Literal Design M3** (secondary comparison) | Design-document rule: $T_1$ observable and ($T_0$ observable or $T_1 \ge$ minimum latency) | front | $T_1$, $T_0$ | as stated | reported beside the physical-screen denominator | implicitly assumes visibility from $t=0$ when $T_0$ is unknown | `m3_design_literal_evaluable` exists on `LeadInScreenResult` only; **not** propagated to `SingleEventEvaluation` or the summary (Phase 4 requirement) |
| **Warning lead time** (operational/exploratory) | $T_1 - t_{\text{warn}}$ | front-stream replay | $T_1$ | $T_1$ observable and a warning exists | evaluable train events; median, range | recording starts after the train is visible in many events, so values can be bounded by recording start; any bound is exploratory | field `warning_lead_time_s` exists |
| **Clearance latency** (operational) | $T_{\text{open}} - T_4$ | back-stream replay | $T_4$ | an opening step at or after $T_4$ exists | evaluable events; median, range | requires the back clock; right-censored when the recording ends first | field `clearance_latency_s` exists |
| **Excess closed duration** (exploratory) | blocked time beyond the approach-to-clearance time | fused only | $T_1$ **and** $T_4$ on one clock | one common timeline | evaluable fused events only | in independent-camera mode it is `not_evaluable: clock_mismatch` (T1 and T4 are on different clocks) | field `excess_closed_duration_s` exists |
| **Detection latency** | $T_{\text{detect}} - T_0$ | front | $T_0$ (not left-censored) | $T_0$ observable and uncensored | uncensored events only; left-censored events excluded | cannot be computed against a left-censored $T_0$; lower bounds are exploratory | defined in v9 §18; **no field in `SingleEventEvaluation`** — not implemented in the evaluation record |
| **No-train nuisance** | event-level: did the barrier block on a no-train recording; blocked seconds; closure episodes; per-stream exposure | each stream separately | none (no train markers) | the no-train recording is confirmed train-free (RD-025: human confirmation **not yet obtained**) | the 3 no-train events (`k/3`), reported separately from train aggregates | no hourly rate (≈120.8 stream-seconds is insufficient); concurrent overlap unresolved | counts, blocked seconds, episodes and exposure fields exist; the "train-free" claim is deferred |
| **Engine-only case study** | the single engine pass, reported alone | back for $T_3 \equiv T_4$ | $T_3 \equiv T_4$ | separate case study | never pooled | $N = 1$ | engine records are excluded from pooled M4/M5/train aggregates (RD-024) |
| **Full crossing occupancy duration** | duration the conflict area is occupied | — | needs the entry landmark and a same-camera pair | **DEFERRED** (RD-018/RD-019) | none | entry landmark undefined (RD-006); no valid same-camera pair; cross-camera alignment not approved | **not implemented, not reported** |
| **Gate chatter count** | open/close reversals per event | per stream | none | always | per-event count | implementation for train events not verified in this phase | v9 §18 definition only; closure-episode counts exist for no-train events |
| **Fault-injection outcomes** | software behaviour under modelled faults | n/a | none | separate section | **never pooled** with natural events (RD-038) | correlated repeated measures; B7e numerics deferred (RD-034) | outside Phase 2; no result |
| Design metrics M1, M2, M6–M10, V1, F1, D1 | — | — | — | — | — | non-binding reference | **unimplemented / out of scope** (RD-020) |

## 5. Phase 1 metric contract (reflected in the protocols)

1. **Zero-origin M5.** M5 requires a zero-origin replay and coverage through $T_4$ (DEC-C01). A late start or a start at or after $T_4$ is `NOT_EVALUABLE`, never M5. M4 is independent of the origin.
2. **Empty interval.** `no_steps_in_protection_interval` stays `NOT_EVALUABLE` with diagnostics (DEC-C02).
3. **Physical screen primary.** Literal M3 is secondary (DEC-C03).
4. **Baseline.** The Mission 5A.1 corrections are the baseline (DEC-C04).
5. **Timestamps** are normalized with `round(float(t), 6)` before strict comparison; no physical tolerance (DEC-C05).
6. **Multi-system propagation (F-19).** The M4/M5 record is taken from a system that carries $T_4$; the screen record from a system that carries $T_1$.
7. **Conditions acknowledged from Phase 1:** (i) 59 Ruff findings remain in three untouched files (deferred engineering); (ii) M5 has no sampling-gap or density threshold — sparse replay evidence must not be described as proof of continuous gate state; (iii) a censored $T_0$ with unknown direction is unverifiable for the screen; (iv) literal M3 is not yet in the evaluation and summary layers.

## 6. Frozen policy and constants (RD-029–RD-033)

- `decision_policy_v1` is **frozen** for the descriptive study; neither the v2 candidate nor the design document's corrected policy replaces it. This proposal edits no configuration or policy file.
- **Audio is supporting evidence only** (RD-030; `RULE_2_AUDIO_SUPPORT_ONLY`). **Two-tick confirmation, two-miss tolerance, no EMA** (RD-031).
- All constants (vision 0.35/0.35, audio 0.37, staleness 2.0 s, tick 0.2 s, confirm 2, miss 2, dwell and travel times) are **exploratory/descriptive only**, with no scientific approval and no calibration or sensitivity run (RD-032). ROI-dependent official analysis is excluded (RD-033); the danger zone is defined by ground-truth landmarks only.
- Documented limitations (not fixed): no implementation of "positive rear confirmation" for clearance; the fault state is described in the design's audit as lacking an exit; the policy was developed after seeing these recordings (pilot contamination, to be disclosed); barrier timings are simulated; `rear` detections are rare in the field outputs. These are second-hand statements from the source documents.
- Tick conflict (documented): `decision_policy_v1.yaml` has `tick_interval_s: 0.1`, which no code reads; `timing.tick_s: 0.2` in the frozen configuration governs.

## 7. Population, strata and aggregation rules

- **Engine events stay outside pooled M4/M5/train aggregates** and are reported in their own table (RD-024).
- **No-train false-alarm analysis stays separate**: event-level counts, blocked seconds, closure episodes and per-stream exposure; no hourly rate; no "train-free" claim until a human confirmation exists (RD-025).
- **Synthetic fault-injection results stay separate from natural-event descriptive results** (RD-038). Synthetic-test outputs are labelled synthetic and never mixed with real descriptive results.
- Cohort summaries expose unverified-ground-truth and excluded-train-event counts; the partition identity holds and no metric denominator changes (Phase 1, DEC-B04).
- Identity is cohort-qualified (`<cohort>/<event_id>`); bare ids fail closed.

## 8. Statistics (RD-023)

**Descriptive statistics only:** event-level counts, Wilson 95 % intervals, medians, ranges, counts of not-evaluable events by reason. No p-values; McNemar, Wilcoxon, Holm and bootstrap contrasts are **not** planned or approved. The interval describes variation among passages recorded at this site in these sessions and is not a bound on field failure probability. For orientation only, 0 events of 23 gives a Wilson 95 % upper limit of about 14 % under independence. Stress conditions are reported descriptively and are never presented as additional sample size.

## 9. Governance and execution prerequisites (all pending)

Formal approvals pending: D1 protocol authority, D2 evaluation profile (M4/M5 contract), D4 R04 scope, thresholds, ROI, B7e, ratification of the four 2026-10-30 items. Execution authorizations pending: media access, pilot, adjudication, promotion, descriptive evaluation. No official split. No `EVAL-AUTH`. Stage-2.1 human review and ground-truth promotion have not occurred, so **no ground-truth-dependent metric can be computed**.

## 10. Deferred items (never invented)

Entry landmark (RD-006) · per-event direction (RD-010) · full occupancy duration (RD-018/019) · human confirmation that no-train clips are train-free (RD-025) · B7e numerics (RD-034) · review tolerance and `T4 ± u` sensitivity (RD-012) · review-duration floor (RD-046) · audit percentage (RD-044) · reviewer identities beyond the single allow-listed one (RD-042) · real-data descriptive pathway (RD-039; the approved descriptive mode accepts synthetic evidence only) · wiring the lead-in screen into the official runner (BR-19).

## 11. Results (all pending)

<!--RESULTS-TABLES-->
| Outcome | `B0` | `B1` | `B2` | `B0_back` | `B0_back_stateless` | `B2_back` |
|---|---|---|---|---|---|---|
| M4 events (evaluable / premature) | NOT COMPUTABLE (needs back stream) | NOT COMPUTABLE | NOT COMPUTABLE | [RESULTS PENDING] | [RESULTS PENDING] | [RESULTS PENDING] |
| M4 not-evaluable by reason | NOT COMPUTABLE | NOT COMPUTABLE | NOT COMPUTABLE | [RESULTS PENDING] | [RESULTS PENDING] | [RESULTS PENDING] |
| M5 count | NOT COMPUTABLE | NOT COMPUTABLE | NOT COMPUTABLE | [RESULTS PENDING] | [RESULTS PENDING] | [RESULTS PENDING] |
| MTR (evaluable / missed) | [RESULTS PENDING] | NOT COMPUTABLE | [RESULTS PENDING] | NOT COMPUTABLE | NOT COMPUTABLE | NOT COMPUTABLE |
| MTR screen exclusions by reason | [RESULTS PENDING] | NOT COMPUTABLE | [RESULTS PENDING] | NOT COMPUTABLE | NOT COMPUTABLE | NOT COMPUTABLE |
| Warning lead time | [RESULTS PENDING] | NOT COMPUTABLE | [RESULTS PENDING] | NOT COMPUTABLE | NOT COMPUTABLE | NOT COMPUTABLE |
| Clearance latency | NOT COMPUTABLE | NOT COMPUTABLE | NOT COMPUTABLE | [RESULTS PENDING] | [RESULTS PENDING] | [RESULTS PENDING] |
<!--/RESULTS-TABLES-->

Engine-only case study, no-train counts, fault-injection outcomes and the exploratory fused (11-event) comparison: [RESULTS PENDING — AUTHORIZED EVALUATION NOT EXECUTED].

## 12. Disposition of `EXPERIMENT_DESIGN_FINAL.md`

| Design item | Disposition |
|---|---|
| Event as unit of analysis; Wilson 95 % intervals; no hourly nuisance rate; N1 form | adopted |
| Engine event as a separate case study | adopted (and excluded from M4/M5) |
| M4 / M5 | adopted in the implemented, corrected form (witnessed violation; zero-origin M5; strict open interval); the design's "any opening command" wording is not used |
| M3 with `insufficient_lead_in` | adopted as the physical screen (primary); the literal rule is reported beside it |
| Independent-camera clock rule | adopted (RD-015, RD-028) |
| Censoring excluded from point estimates, counted by reason | adopted (RD-011); the design's "censored marker stores a bound" is exploratory only |
| McNemar, Wilcoxon, Holm, bootstrap, "primary contrasts" | **not adopted** (RD-023) |
| `T4 ± u` sensitivity | deferred (RD-012) |
| Fused primary if ≥ 20/23 calibrate | superseded; not claimed |
| Corrected policy (ABS/REAR clearance, C×T×P×A, EMA) | **not adopted** (RD-029) |
| Audio may start a warning | **not adopted** (RD-030) |
| M1, M2, M6–M10, V1, F1, D1 | unimplemented / out of scope |
| Quarantined engine duplicate deny-list | inventory stays 27 = 23 + 3 + 1 |

## 13. What this consolidation changes relative to the 5A reconciliation

Adds: the Phase 1 metric contract (§5); an eight-column metric table with implementation status (§4); the explicit provisional condition names (§3); the results skeleton (§11).

## 14. Open questions and contradictions found (need the researcher)

1. **Condition names and definitions.** The legacy runner's B0–B7 labels differ from the paper's B0–B2 and from the provisional back-stream names; the replay configuration behind each name must be fixed by the researcher.
2. **Stateless vs stateful back-stream conditions.** Whether `B0_back_stateless` corresponds to an existing replay configuration is not verified here.
3. **`B1` audio-only vs RD-030.** Audio cannot actuate the gate on its own under the frozen policy; how B1 is reported is undecided.
4. **M5 sparse pre-$T_4$ sampling.** M5 has no density requirement (Phase 1 condition); a researcher decision would be needed to add one.
5. **Censoring direction.** The ground-truth loader has no censoring-direction field, so the screen treats a censored $T_0$ as unverifiable.
6. **Detection latency** has a v9 definition but no evaluation-record field.
7. **Gate chatter** for train events is defined but its implementation was not verified.
8. **Session facts** (§2) and **left-censoring counts** (the paper draft says 23/23, other documents say 20/23) conflict across source documents and must be taken from approved ground truth.
9. **Session dates:** `EXPERIMENT_DESIGN_FINAL.md` gives S1 = 2026-09-14 and S2 = 2026-10-04; the paper draft gives 3 and 7 October 2026. Neither is asserted.
10. **Tick conflict** `tick_interval_s` 0.1 vs `timing.tick_s` 0.2 is documented, not resolved.
