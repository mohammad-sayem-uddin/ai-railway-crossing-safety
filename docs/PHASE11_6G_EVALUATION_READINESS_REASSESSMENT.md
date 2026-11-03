# Phase 11.6G — Ground-Truth and Evaluation-Readiness Reassessment

**This is a readiness assessment, not permission to perform the next phase.** Nothing in this document authorizes Stage 3, Phase 12, legacy invalidation execution, or any metric computation.

---

## 1. Were legacy records formally dispositioned, merely flagged, or left untouched?

**Left untouched, because authorization was absent — confirmed independently in Phases 11.6D–F of this same work.** All 27 legacy review records remain on disk exactly as Phase 11.1 found them: `schema_version: "7.0.0"`, `adjudication_status: "APPROVED"`, unmodified, byte-identical. A full, reviewable disposition *proposal* exists (scope, mechanism, and a hash-pinned proposal file all researcher-confirmed), and the writer that would apply it is implemented, independently audited, and hardened — but execution authorization, which is a deliberately separate step, has never been given. This is "proposed, not executed," not "untouched because forgotten."

## 2. Does the Stage-2.1 schema and promotion gate still enforce everything required?

Re-checked by source inspection in this phase (not assumed unchanged):
- **Reviewer attribution**: `REVIEWER_ID_BLOCKLIST` still blocks the known-fabricated identity string; every record requires a non-blocklisted `reviewer_id`.
- **Valid review duration**: `MIN_PLAUSIBLE_REVIEW_DURATION_S = 30.0` still enforced as a floor.
- **Model independence**: `ModelIndependenceAttestation` still requires an explicit, non-boilerplate, timestamped attestation.
- **Media-hash verification**: `promotion_gate.validate_for_promotion` still requires a caller-supplied `media_sha256_registry` with both camera hashes present.
- **Append-only history**: `adjudication_history` still required non-empty and schema-validated per entry.
- **Explicit uncertainty handling**: the four-state `BOUNDARY_STATES` taxonomy (`OBSERVABLE`/`UNOBSERVABLE_NOT_APPLICABLE`/`CENSORED`/`UNCERTAIN`) is unchanged.
- **Legacy-schema rejection**: `LEGACY_OR_UNKNOWN_SCHEMA` is still checked first, before any other field is read.

**All confirmed present and unweakened.** None of Phase 11.6A–11.6C's work touched this module (it is a separate, independent module from `invalidation_notice_writer.py`).

## 3. Remaining pending implementation decisions or fields

From `docs/PHASE11_3_RESEARCHER_DECISIONS.md` v1.2.0 — four decisions are researcher-**selected** but not all are fully **implemented** in code:
- **Decision 1** (review-session duration): option (D) selected, but the pilot-derived hard floor and upper threshold are explicitly still `PENDING` — no pilot has run.
- **Decision 2** (reviewer allowlist): mandatory allowlist selected, but `data/ground_truth/authorized_reviewers.json` does not exist and no code enforces it yet.
- **Decision 3(c)** (documented audits of clear-marked boundaries): the exact audit mechanism/frequency is unspecified.
- **Decision 4** (dual hash verification): selected, but requires a new Stage-2.1 schema field and a new promotion-gate raw-media re-hash code path, neither implemented.

**These gaps affect promotion-time rigor and future enforcement, not the ability to begin genuine review today** — a single-researcher project's own reviewer_id trivially satisfies even an unenforced allowlist requirement, and Decision 4's stronger verification matters most at promotion time, which remains far off regardless (no event has a Stage-2.1 record at all yet).

## 4. 27-event inventory reassessment

Reviewed `docs/PHASE11_EVENT_INVENTORY.json`/`.csv` — **not modified, and no unresolved label was filled from a model prediction** in this phase or any prior one. The inventory's `left_censored` flags remain exactly as Phase 11.4/11.5 independently verified them (20/23 originally, +3 researcher-confirmed, see below) — any correction is tracked in the separate, additive `docs/PHASE11_EVALUATION_READINESS_REPORT_ADDENDUM_v1.1.md`, never by silently editing the inventory file itself.

## 5. Researcher-confirmed corrections (events 009/015/016) — preserved, audit trail verified

Re-read `docs/PHASE11_5_FIELD_ADJUDICATIONS.json` fresh in this phase: all three records show `current_status: RESEARCHER_CONFIRMED_CORRECTION`, `corrected_classification: LEFT_CENSORED`, and a 2-entry append-only `adjudication_history` (`FLAGGED_BY_AUDIT` → `RESEARCHER_CONFIRMED_CORRECTION`, attributed to `raihankabirrahu@gmail.com`) for each. **Unchanged and intact.** No numeric T0 value was fabricated for any of the three (consistent with "true arrival not observable from the recording").

## 6. event_006 / event_021 — confirmed still unresolved

Re-read `docs/PHASE11_6_OPEN_ISSUE_REGISTER.csv` fresh: `T4_event_006`, `Tsc_event_006`, `T1_event_006`, `T2_event_006`, `T3_event_021`, `T4_event_021`, `Tsc_event_021` all show `current_status: OPEN_UNRESOLVED`. **No new independent evidence surfaced in Phases 11.6A–11.6F that touches either event** (those phases concerned the invalidation-notice-writer tool, not video evidence) — these remain open exactly as Phase 11.6 left them, not silently resolved.

## 7. Site-survey-dependent boundary issues — confirmed still open

23/29 rows in the open-issue register remain `OPEN_UNRESOLVED`; the 16 originally identified as blocked on a missing physical site survey remain so — no site survey has been commissioned or performed by any phase to date.

## 8. R04 camera-synchronization restriction — confirmed not relaxed

`configs/frozen_experiment_v1.yaml`: `status: "R04_UNRESOLVED_REQUIRES_EMPIRICAL_OFFSETS"`, `allow_unverified_zero_offset: false` — re-read fresh, unchanged. `config.verify_all_safeguards()` (Phase 11.6F, Section 6) independently confirmed this safeguard still fires. No cross-camera inference was enabled, no offset was inferred, by any phase through 11.6G.

## 9. No performance metrics computed

Confirmed by code/log inspection: no phase from 11.1 through 11.6G ran model inference, computed MTR/POR/warning-lead-time/clearance-latency/or any other performance metric against any label, approved or otherwise. The invalidation-notice-writer work (11.6A–C) and this phase's audit work (11.6D–F) are entirely about document/record disposition tooling, not model evaluation.

## 10. Technical readiness vs. researcher authorization vs. scientific validity

These are explicitly three different things, and conflating them is exactly what this reassessment is checking against:

- **Technical readiness** (does working, tested tooling exist to do the next step?): **yes**, for both legacy disposition (writer implemented, audited, hardened — Phase 11.6A–C) and for beginning genuine Stage-2.1 review (schema and promotion gate implemented and tested since Phase 11.2, unweakened).
- **Researcher authorization** (has the researcher actually said to execute a specific, consequential action?): **given** for legacy disposition's scope/mechanism and for the three T0 corrections; **not given** for legacy disposition's execution itself, for any Stage-2.1 record's approval, or for Stage 3/Phase 12.
- **Scientific validity** (is there actually approved, trustworthy ground truth to evaluate against?): **no** — zero events currently have a genuine Stage-2.1 record of any kind; the corrected 0/23 Detection Latency eligibility figure (Addendum v1.1) stands; 23 of 29 catalogued issues remain genuinely open, 16 of them on evidence that does not exist (a site survey).

Technical readiness does not imply authorization, and neither implies scientific validity. All three must independently hold before evaluation can proceed, and only the first currently does, fully.

---

# Verdict: `READY_FOR_RESEARCHER_ADJUDICATION`

The project has reached the point where the researcher can begin genuine, individually-attributed Stage-2.1 review of the 27 events — the schema and promotion gate are implemented, tested, and unweakened; all four governance decisions have been made (even where not yet fully code-enforced, none of the gaps block beginning review); the 23 genuinely open issues are catalogued with an honest resolvable/blocked distinction; the three T0 corrections and their audit trails are preserved; and a reviewable, hash-pinned, dry-run-verified path to disposing of the legacy records exists and awaits only the researcher's separate execution authorization.

**This verdict explicitly does NOT mean:**
- Legacy records are invalidated (`NOT_AUTHORIZED`, Phase 11.6D–F).
- Any event has approved ground truth (zero Stage-2.1 records exist).
- `READY_FOR_SPECIFIC_EVALUATION_STAGE` applies to any named stage — it does not; no evaluation-stage prerequisite set is demonstrably satisfied.
- Stage 3 or Phase 12 may begin.
- Any pending implementation gap (Decisions 1/2/3(c)/4's code) is closed — they are not, and should be closed before promotion-time reliance on them, even though they do not block beginning review.

**Prerequisites for the next verdict step (`READY_FOR_SPECIFIC_EVALUATION_STAGE`, naming a specific stage)** include, at minimum: genuine Stage-2.1 review completed and approved for a defined subset of events; the legacy 27-record disposition executed (or explicitly, separately declined) under researcher authorization; Decision 2/4's code implemented if promotion is to rely on them; and a recomputed Section 5 eligibility table from real, approved ground truth rather than candidate proposals. None of these exist yet.
