# Phase 11.3 — Researcher Decision Register

**Status:** Decision register only. No decision below has been made by this phase on the researcher's behalf. Every item marked `PENDING_RESEARCHER_DECISION` requires the researcher's own choice; this document presents options, not answers. No annotation has been approved, invalidated, or promoted by this phase.

**Builds on:** `docs/PHASE11_1_ANNOTATION_INTEGRITY_AUDIT.md`, `docs/PHASE11_1_REMEDIATION_PLAN.md`, `docs/PHASE11_2_STAGE21_IMPLEMENTATION_REPORT.md` (Section 2 of that report first raised the four decisions formalized here).

---

## 0. Readiness summary

| Item | Status |
|---|---|
| Git HEAD / protected-artifact hashes | Preserved and re-verified (Section "Preservation" in `reports/progress.md`'s Phase 11.3 entry). |
| 4 required researcher decisions (Section 1) | **All 4 PENDING_RESEARCHER_DECISION.** None silently defaulted. |
| Disposition of the 27 legacy records (Section 2) | **Proposed, not executed.** Affected records identified, evidence cited, scope stated. Decision-maker/date fields blank, awaiting the researcher. |
| Review workflow (`docs/PHASE11_3_ANNOTATION_REVIEW_WORKFLOW.md`) | Documented. **Explicitly marked NOT READY for production use** until Decisions 1, 2, and 3 (Section 1) are resolved — see that document's own readiness note. |
| Review inventory (`docs/PHASE11_3_REVIEW_INVENTORY.json`/`.csv`) | Built, 27/27 events, no pre-filled boundary labels, `assigned_reviewer: null`, `review_status: "NOT_STARTED"` throughout. |
| Implementation verification (Section 3 below) | Re-confirmed: no permissive default exists anywhere in code for any of the 4 pending decisions. |

**This phase's own conclusion: annotation review preparation is complete; genuine annotation review itself has not begun and should not begin in production until Decisions 1–3 are resolved** (Decision 4 affects promotion-time behavior more than review-time behavior and is less blocking, but should still be resolved before any real promotion is attempted).

---

## 1. The four required decisions

Each entry: context/rationale, the options actually implementable with this repository's existing code, the selected option, the decision-maker, the date, and unresolved concerns. Per the Phase 11.3 brief, **no option is pre-selected below.**

### Decision 1 — Minimum review-session duration and handling of suspiciously short sessions

**Context:** `src/railway_detection/annotation/stage2_1_schema.py`'s `MIN_PLAUSIBLE_REVIEW_DURATION_S = 30.0` is currently a flat floor, reused unchanged from Phase 11.1's forensic constant (itself derived only as a sanity check against the fabricated 27 records' ~0.2s/event write cadence) — it was never a considered, event-complexity-aware threshold, and Phase 11.2 flagged it explicitly as provisional.

**Options:**
- **(A) Keep the flat 30.0s floor as a pure sanity check**, with no further scaling. Simple, uniform, cheap to reason about; does not account for the fact that a 24-second no-train negative-control clip plausibly needs far less inspection time than a 127-second, 24-coach train event.
- **(B) Scale the floor by event complexity** — e.g., a minimum proportional to the event's own recorded duration (such as `max(30s, 0.1 x total_stream_duration_s)`), or by `trailing_cars_count` for train events (more vehicles to visually track through the frame plausibly needs more time). Requires choosing and justifying a specific formula.
- **(C) Set a substantially higher flat floor** (e.g. 180s or more), reasoning that genuine frame-stepped visual inspection of two video streams plus a spectral audio check for even a short event realistically takes several minutes, not 30 seconds.
- **(D) Add a secondary, non-blocking "fast but passing" band**: sessions between the hard floor and a second, higher threshold are accepted but automatically routed to `NEEDS_SECOND_REVIEW` regardless of the first reviewer's own status choice, rather than rejected outright or silently trusted.

**Selected option:** `PENDING_RESEARCHER_DECISION`
**Decision-maker:** _(blank — to be completed by the researcher)_
**Date:** _(blank)_
**Unresolved concerns:** No option above was evaluated against actual genuine review-session timing data, since none exists yet (review has not begun). Whatever is chosen should likely be revisited once a handful of genuine reviews establish a realistic baseline duration, rather than being treated as final.

**Phase 11.6 recommendation (not a decision — presented for explicit researcher approval, not yet confirmed):** **(D)**, the secondary non-blocking "fast but passing" band. Rationale: (A) risks accepting a genuinely too-fast session outright; (C) is a one-size-fits-all floor that is already acknowledged as not evaluated against real timing data, same weakness as (A) just set higher; (B) requires a formula this document is not positioned to justify without the timing data Decision 1's own "unresolved concerns" note says doesn't exist yet. (D) is the only option that does not require trusting an unvalidated number outright — it converts "was this review fast enough" into "does a second reviewer agree," which is verifiable, at the cost of extra reviewer effort on borderline-fast sessions. **Practical implication:** requires choosing the upper threshold of the "fast but passing" band, which is not specified here and remains open even if (D) is approved. **Trade-off not resolved by this recommendation:** (D) does not, by itself, pick a lower hard floor — some flat minimum (per A or C) would likely still be needed beneath the band, meaning a full implementation needs a combined choice, not (D) alone.

**Selected option (researcher-confirmed, 2026-10-14):** **(D)**, with the hard floor and the band's upper threshold both to be **pilot-derived** — i.e., set from timing data gathered during an initial, small-scale genuine-review pilot, not chosen arbitrarily in advance. **The specific numeric values for the hard floor and the upper threshold remain `PENDING` — not yet set — until that pilot data exists and justifies them.** This decision authorizes the *mechanism* (band + automatic second review for fast-but-passing sessions) now; it does not yet authorize any specific number.
**Decision-maker:** `raihankabirrahu@gmail.com`
**Date:** 2026-10-14
**Remaining action before implementation:** run a small pilot of genuine Stage-2.1 reviews, record actual `review_duration_s` values, then set the hard floor and upper threshold from that data and record them here as a further, numbered update to this entry.

---

### Decision 2 — Reviewer authorization policy and registration

**Context:** `REVIEWER_ID_BLOCKLIST` in `stage2_1_schema.py` is a **denylist**, not an allowlist: it permanently blocks the exact known-bad string (`"human_researcher_lead"`) and a handful of generic placeholders, but **any other string is currently accepted as a valid `reviewer_id`** with no registration or verification step. This repository has no authentication system of any kind (confirmed in Phase 11.1/11.2) — there are no user accounts to check a reviewer identity against.

**Options:**
- **(A) Keep denylist-only.** Operationally simplest; requires no registration process; weakest control — anyone running the code can claim to be any (non-blocklisted) reviewer.
- **(B) Implement an allowlist file** (e.g. a new `data/ground_truth/authorized_reviewers.json` the researcher maintains by hand, listing specific individuals permitted to submit Stage-2.1 records) checked by the schema or promotion gate. Stronger in principle, but — stated honestly — still just a text file anyone with filesystem write access could edit; it raises the bar for an accidental or careless mismatch, not a determined bypass.
- **(C) Hybrid**: denylist always enforced (as today); an allowlist is optional — if present, only listed reviewers are accepted; if absent, any non-blocklisted string is accepted with a logged warning. Lets the researcher opt in without an immediate implementation requirement.

**Selected option:** `PENDING_RESEARCHER_DECISION`
**Decision-maker:** _(blank)_
**Date:** _(blank)_
**Unresolved concerns:** Whatever is chosen, it should be stated plainly to anyone reading the resulting ground truth that this project has no cryptographic or access-controlled guarantee of reviewer identity — only a documented convention, same caveat already given for the invalidation-proposal mechanism in Phase 11.2.

**Phase 11.6 recommendation (not a decision — presented for explicit researcher approval, not yet confirmed):** **(C)**, the hybrid. Rationale: this is currently a single-researcher project (confirmed by every phase's attribution to one reviewer identity); (B) mandates a registration artifact before any review can occur, which is process overhead with no other reviewers yet to register; (A) leaves the door open to an unnoticed typo/placeholder reviewer_id slipping through with zero defense beyond the existing denylist. (C) costs nothing today (no allowlist file needed to start reviewing) and upgrades automatically to (B)'s stronger guarantee the moment an allowlist file is added, without a schema or code change. **Practical implication:** if the project remains single-reviewer indefinitely, (C) behaves identically to (A) and the distinction is moot — the recommendation only pays off if/when a second reviewer joins. **Trade-off not resolved:** (C) still shares (B)'s honest limitation — any allowlist is just a text file, not a credential — this recommendation does not claim otherwise.

**Selected option (researcher-confirmed, 2026-10-14):** **(B)**, mandatory explicit reviewer allowlist — stronger than the Phase 11.6 recommendation. A `data/ground_truth/authorized_reviewers.json` (or equivalent) must exist and list every permitted `reviewer_id`; any `reviewer_id` not on it is rejected outright, with no "accepted with a logged warning" fallback.
**Decision-maker:** `raihankabirrahu@gmail.com`
**Date:** 2026-10-14
**Remaining action before implementation:** the allowlist file itself does not yet exist and must be created (listing the researcher, at minimum) before the schema/promotion gate can enforce this — not done by this phase; this decision authorizes the policy, not the artifact.

---

### Decision 3 — Disagreement and adjudication rules

**Context:** The Stage-2.1 schema supports `NEEDS_SECOND_REVIEW`/`DISPUTED` statuses and the promotion gate blocks both, but (a) no rule determines **which events require a second reviewer in the first place** (mandatory-for-all vs. triggered-by-ambiguity), and (b) no **numeric tolerance** exists anywhere in the code for deciding whether two independently-reviewed boundary values "agree" closely enough to not count as a disagreement — confirmed absent by `test_no_automated_tie_breaking_function_exists` (Phase 11.2).

**Options, part (a) — when is a second reviewer required:**
- **(A) Mandatory second review for all 27 events**, unconditionally. Maximum rigor; doubles reviewer effort for every event, including the ones with no ambiguity at all (e.g. a no-train event with no visible train and no horn).
- **(B) Second review only for events the first reviewer marks `UNCERTAIN` on at least one boundary**, per the four-state taxonomy. Targets effort where it is actually needed; relies on the first reviewer correctly self-identifying uncertainty.
- **(C) Second review for a defined subset regardless of the first reviewer's flags** — e.g. always for the 20/23 left-censored events, or always for the events Phase 11 found with sub-3.0s $T_4$ margin, since those are exactly the boundary conditions most likely to be contentious.

**Options, part (b) — numeric agreement tolerance:**
- **(A) No tolerance at all: any numeric difference between two independent reviewers' values for the same boundary is `DISPUTED`**, requiring the researcher's own final adjudication. Simplest, most conservative; may over-flag trivial frame-rounding differences as disputes.
- **(B) A small, explicitly justified tolerance** (e.g., a fixed number of native-fps frames, separately derived from each camera's own frame rate — not the Phase 11 evaluation protocol's ±0.4s system-sampling tolerance, which is a *model-evaluation* concept with a different justification and must not be silently reused here, per Phase 11.2's own caution).

**Selected option:** `PENDING_RESEARCHER_DECISION` (both parts)
**Decision-maker:** _(blank)_
**Date:** _(blank)_
**Unresolved concerns:** Whichever tolerance (if any) is chosen for part (b) must be derived and justified independently of the evaluation protocol's tolerance, with its own stated rationale, to avoid quietly importing a model-evaluation assumption into ground-truth annotation.

**Phase 11.6 recommendation (not a decision — presented for explicit researcher approval, not yet confirmed):** Part (a): **(B)**, second review triggered by a first-reviewer `UNCERTAIN` flag, supplemented by Part (c)'s logic for a fixed subset — specifically, the 16 Phase 11.4/11.5 minimal-progression and long-static-span rows now catalogued in `docs/PHASE11_6_OPEN_ISSUE_REGISTER.csv` are exactly the kind of fixed, evidence-identified subset option (C) describes, so a combined B+C is more concretely justified now than when Decision 3 was first written, since those specific events are now named rather than hypothetical. (A), mandatory-for-all, is defensible but doubles effort on the 6/27 events with no flagged ambiguity at all (the 3 no-train events and at least 2-3 clean train events). Part (b): no change to the recommendation — still **(A), no tolerance**, is the more conservative default until a camera-specific frame-rate-derived tolerance is separately justified; this phase does not attempt that derivation. **Practical implication:** adopting B+C means the open-issue register above effectively becomes the initial "fixed subset" list for (C), which should be kept in sync if new ambiguities are found in future phases. **Trade-off not resolved:** whether a first reviewer's `UNCERTAIN` self-flag can be trusted without a second reviewer catching under-flagging is not addressed by this recommendation.

**Selected option (researcher-confirmed, 2026-10-14):** Part (a): **B+C**, exactly as recommended — second review required whenever the first reviewer marks a boundary `UNCERTAIN`, plus mandatory second review for the fixed subset currently named in `docs/PHASE11_6_OPEN_ISSUE_REGISTER.csv`. Part (b): **(A), no tolerance**, as recommended. **Plus one researcher-added requirement not in the original options (a)/(b), recorded here as Decision 3(c):** every boundary a first reviewer marks as clear/observable (i.e. NOT `UNCERTAIN`, and NOT in the fixed subset, so not already covered by B+C) must still receive a **documented audit** before being treated as final — some form of lightweight secondary check or periodic spot-check, distinct from a full mandatory second review.
**Decision-maker:** `raihankabirrahu@gmail.com`
**Date:** 2026-10-14
**Remaining action before implementation — Decision 3(c) specifically:** the exact audit mechanism and frequency (e.g., spot-check N% of "clear" boundaries, or a lighter-weight single-pass skim of every one) is not specified by the researcher's instruction and is **not decided by this phase** — must be defined before the review workflow can enforce it.

---

### Decision 4 — Media-hash verification requirements at review and promotion time

**Context:** `promotion_gate.py`'s `validate_for_promotion` requires a caller-supplied `media_sha256_registry` with `front`/`back` entries present, but does not itself recompute hashes from raw media files at either review or promotion time — the current implementation trusts whatever registry the caller supplies (in practice, expected to be `data/manifests/layer_b_v2_annotation_inventory.json`, independently verified once in Phase 11).

**Options:**
- **(A) Trust the existing Phase-11-verified manifest at promotion time**, with no re-verification. Fast; the raw media files are static and were already independently hash-checked once; re-checking every promotion run is redundant unless the files could change.
- **(B) Re-verify media hashes fresh from the raw `.mov` files at every promotion run.** Slower (full-file SHA-256 over potentially large video files); catches any post-Phase-11 corruption, accidental edit, or tampering of the raw media that the static manifest would not detect.
- **(C) Require fresh verification at review time only** (the reviewer's own tool independently hashes the file they are about to inspect and the review record carries that independently-observed hash, compared against the proposal's claimed hash as an extra check), while promotion time continues to trust the manifest (split responsibility between "did the reviewer look at the right, uncorrupted file" and "has anything changed since").

**Selected option:** `PENDING_RESEARCHER_DECISION`
**Decision-maker:** _(blank)_
**Date:** _(blank)_
**Unresolved concerns:** Option (C) would require a new field on the Stage-2.1 schema (an independently-reviewer-observed media hash) not currently present; implementing it is itself a design change that should follow, not precede, this decision.

**Phase 11.6 recommendation (not a decision — presented for explicit researcher approval, not yet confirmed):** **(A)**, trust the existing Phase-11-verified manifest. Rationale: every integrity check performed across Phases 11.1–11.6 (27 review-record re-hashes, Phase 8 output re-hashes, raw-media spot checks) has found the raw media files themselves byte-identical throughout; nothing in this project's observed failure modes (fabricated review timestamps, stale proposal references, an untracked `frozen_experiment_v1.yaml` turning out to need the canonical-hash method rather than a raw-byte one — Phase 11.5 Section 6) has been a raw-media-tampering problem. (B)'s full-file re-hash cost is not yet justified by any observed threat in this specific repository. **Practical implication:** this is the lowest-cost option and requires no new code. **Trade-off not resolved:** (A) provides no defense if a raw `.mov` file were corrupted or swapped after Phase 11's manifest was built — this recommendation accepts that residual risk rather than eliminating it, and (B) or (C) remain available if the researcher judges that risk unacceptable.

**Selected option (researcher-confirmed, 2026-10-14):** **(B)+(C) combined** — stronger than the Phase 11.6 recommendation. Full-file SHA-256 re-verification against the raw `.mov` files is required **both** at review time (per C: the reviewer's own tool independently hashes the file before inspection, and the review record carries that independently-observed hash) **and** at promotion time (per B: `promotion_gate.py`'s `validate_for_promotion` re-hashes from raw media rather than trusting the caller-supplied registry).
**Decision-maker:** `raihankabirrahu@gmail.com`
**Date:** 2026-10-14
**Remaining action before implementation:** (i) a new Stage-2.1 schema field for the reviewer-observed hash (noted as a prerequisite for option C back when it was first scoped, Phase 11.3) is not yet implemented; (ii) `validate_for_promotion` does not currently recompute hashes from raw media and would need that code path added; neither change was made by this phase.

---

## 2. Disposition of the 27 legacy approvals — proposed, not executed

**This section is a decision record for the researcher to review and sign. It does not itself invalidate anything. As of this writing, all 27 records in `data/ground_truth/reviews/{cohort}/event_XXX_review.json` remain on disk exactly as they were found in Phase 11 — `schema_version: "7.0.0"`, `adjudication_status: "APPROVED"` — unmodified and un-superseded.** They must not be described as formally invalidated anywhere until the researcher explicitly authorizes and performs the invalidation operation through the workflow below.

### Affected records

All 27: 23 `train_events`, 3 `no_train_events`, 1 `engine_events`. Full list with file paths and SHA-256 hashes (unchanged since Phase 11.1): `docs/PHASE11_1_INTEGRITY_INVENTORY.json`; cross-referenced again in `docs/PHASE11_3_REVIEW_INVENTORY.json` (`legacy_review_file` field per event).

### Evidence supporting the decision

Summarized from `docs/PHASE11_1_ANNOTATION_INTEGRITY_AUDIT.md` (full detail there):
1. All 27 records share one byte-identical `review_date_utc` string.
2. Filesystem mtimes independently show all 27 written within a ~5-second span (~0.2s/record), inconsistent with the claimed per-event frame-by-frame review methodology.
3. All 27 records reference a superseded (non-currently-active) proposal version.
4. No code path anywhere in the repository (tracked or untracked) constructs a review record; the one real approval safeguard that exists was never applied to this write path and checks a different field name than the one these records use.
5. Applying the new Stage-2.1 promotion gate (Phase 11.2) to all 27, read-only, rejects every one on `LEGACY_OR_UNKNOWN_SCHEMA` grounds alone — confirmed in `docs/PHASE11_2_STAGE21_IMPLEMENTATION_REPORT.md` Section 5.

### Scope of invalidation (proposed)

**Full invalidation of all 27 records**, not a partial subset — every one shares the identical-timestamp defect (item 1) and the stale-proposal-reference defect (item 3) independently, so no record among the 27 is distinguishable from the others on integrity grounds; there is no principled basis in the available evidence for invalidating some but not others.

### Proposed mechanism

Either of the two non-destructive options specified in `docs/PHASE11_1_REMEDIATION_PLAN.md` Section 2 (a sibling notice file in `reviews/`, or an archive-and-move preserving byte-for-byte content), formalized as a structured disposition event via `propose_invalidation()`/`write_invalidation_proposal()` (`src/railway_detection/annotation/promotion_gate.py`, implemented and tested in Phase 11.2 against synthetic data only).

### Authorized decision-maker

_(blank — must be filled in by the researcher personally; this repository has no authentication system, so this field is a documented attestation, not a verified credential, per Phase 11.2 Section 6's authorization caveat, restated here.)_

### Date of authorization

_(blank)_

### Execution status

**NOT EXECUTED.** No file under `data/ground_truth/reviews/` has been moved, renamed, annotated with an invalidation marker, or otherwise modified by this phase or any phase to date. Re-verified byte-identical, 27/27, at the end of this phase (see `reports/progress.md`'s Phase 11.3 entry), and again at the start and end of Phase 11.5 and Phase 11.6.

### Phase 11.6 update — additional evidence, still not executed

Phase 11.5 added one new, independent evidentiary thread supporting the same proposed disposition: the researcher personally confirmed three further discrepancies (events 009/015/016, T0 left-censoring) directly in the candidate proposals these legacy reviews claim to have approved — see `docs/PHASE11_5_ADJUDICATION_REPORT.md` Section 1 and `docs/PHASE11_5_FIELD_ADJUDICATIONS.json`. This is evidence that the *content* some of these legacy reviews approved was also substantively wrong, in addition to the Section "Evidence supporting the decision" items above, which concern the review *process* (fabricated timestamps, stale references) independent of content. **This does not change the proposed scope (full invalidation of all 27) or execute anything** — it is logged here for completeness. A fully updated, consolidated disposition document — restating all 27 identifiers, both evidence threads, and the unexecuted status in one place — is prepared separately at `docs/PHASE11_6_LEGACY_RECORD_DISPOSITION.md`, which supersedes no content here and leaves this section's authorized-decision-maker/date fields exactly as blank as they were in Phase 11.3.

### Phase 11.6 update (continued, same day) — scope and mechanism selected by the researcher; execution still pending

The researcher explicitly selected: **scope = full invalidation of all 27**; **mechanism = sibling invalidation notices, originals preserved in place** (not archive-and-move) — with the explicit instruction *"Do not execute invalidation or change the real records until I explicitly authorize execution after reviewing the dry-run plan."* This phase therefore: (1) recorded the selection in `docs/PHASE11_6_LEGACY_RECORD_DISPOSITION.md` Section 6; (2) generated a read-only, code-backed dry-run proposal log (`docs/PHASE11_6_LEGACY_INVALIDATION_DRY_RUN_PROPOSAL.json`, via the existing tested `propose_invalidation()`/`write_invalidation_proposal()` functions, which only read real files to capture their current hash and never write to them) and a human-readable dry-run plan (`docs/PHASE11_6_LEGACY_INVALIDATION_DRY_RUN_PLAN.md`) showing the exact 28 files that would be created and their exact content; (3) re-verified all 27 real records remain byte-identical immediately after generating the dry run. **No file under `data/ground_truth/reviews/` was created, moved, or modified. Execution remains pending a further, separate, explicit instruction from the researcher.**

---

## 3. Document change log

- **v1.0.0 (2026-10-14):** Initial Phase 11.3 decision register. Four decisions recorded as pending with explicit options; legacy-approval disposition recorded as proposed, not executed.
- **v1.1.0 (2026-10-14, Phase 11.6):** Added a non-binding, explicitly-not-yet-approved "Phase 11.6 recommendation" subsection to each of the four decisions (recommended option, rationale, practical implication, unresolved trade-off) for the researcher's explicit review. **No `Selected option` field was changed — all four remain `PENDING_RESEARCHER_DECISION`** until the researcher confirms a choice. Added a Section 2 note pointing to the new, additional T0 evidence from Phase 11.5 and to the consolidated `docs/PHASE11_6_LEGACY_RECORD_DISPOSITION.md`; did not change Section 2's proposed scope, mechanism, or execution status.
- **v1.2.0 (2026-10-14, same day, Phase 11.6 continued):** Recorded the researcher's explicit decisions for all four governance questions (`raihankabirrahu@gmail.com`, 2026-10-14): Decision 1 = (D) with pilot-derived thresholds (numeric values still `PENDING`); Decision 2 = (B), mandatory allowlist; Decision 3 = (B)+(C) for part (a), (A) for part (b), plus a new researcher-added Decision 3(c) requiring documented audits of boundaries marked clear (mechanism/frequency not yet specified); Decision 4 = (B)+(C) combined, full-file verification at both review and promotion time. Recorded the researcher's explicit scope/mechanism selection for the Section 2 legacy disposition (full invalidation, sibling-notice mechanism) and generated a read-only dry-run proposal and plan (`docs/PHASE11_6_LEGACY_INVALIDATION_DRY_RUN_PROPOSAL.json`, `docs/PHASE11_6_LEGACY_INVALIDATION_DRY_RUN_PLAN.md`) per the researcher's explicit instruction not to execute until that dry run is reviewed and separately authorized. **Several implementation prerequisites remain undone** (allowlist file, pilot-derived numeric thresholds, Decision 3(c)'s audit mechanism, Decision 4's new schema field and promotion-gate re-hash code path) — recording a decision here authorizes the policy, not its implementation.
