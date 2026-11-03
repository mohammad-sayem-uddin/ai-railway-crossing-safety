# Open Decisions and Blockers

| | |
|---|---|
| Date | 2026-10-13 |
| Purpose | The decisions that need your judgment before, or during, the work in `IMPLEMENTATION_PLAN_FOR_SONNET.md`. Everything else in the plan can proceed without you. |
| References | `IMA-nn` → `FINDINGS_REGISTER.csv`; design sections → `EXPERIMENT_DESIGN_FINAL.md` |

Each entry gives a recommended default. If you accept all defaults, the only things you must still do personally are **D-1** (choose where the backup goes), **D-2** (confirm a fact), **D-7** (look at three clips) and the annotation review itself.

## Summary

| ID | Decision | Needed before | Default |
|---|---|---|---|
| D-1 | Where the work lives, where the backup goes, whether to push it | Phase 0 | External drive copy; relocate out of Desktop; push a private preservation branch |
| D-2 | Confirm you did not write the 27 "APPROVED" review records | Phase 9 | Treat as invalid |
| D-3 | Accept the audio cross-correlation calibration and the mode rule | Phase 5 | Accept as written |
| D-4 | Clearance rule and fault recovery | Phase 3 | Absence-with-dwell primary, rear-required as variant; automatic recovery into a closed state |
| D-5 | May audio alone start a warning? | Phase 2–3 | No — supporting only, as the code does now |
| D-6 | What "temporal filter" means | Phase 2–3 | Confirm 2, miss tolerance 2; no EMA |
| D-7 | Are the three no-train clips truly train-free? More negative footage? | Phase 8 (N1) | You check the clips; more footage optional |
| D-8 | Second annotator on a subset | Gate F | Yes, 8 events, T1 and T4 only |
| D-9 | Engine-only event: where T3 and T4 are marked | Phase 9 | Both on the back camera; right-censored if the clip ends first |
| D-10 | Replace the protocol's primary endpoints | Phase 8 | Yes: M4 and M7 primary, M1 key secondary, M3 reported with a feasibility screen |
| D-11 | Policy revised after a pilot on the same recordings | Before submission | Disclose; confirmatory recordings optional |

---

## D-1 — Location, backup and pushing

**Situation.** The only complete copy of the project is `~/Desktop/Train_automation`. The clean repository and the backup named in the recovery reports are gone. The iCloud shadow copy has no data in it. GitHub has 223 files and none of the fusion, evaluation or annotation work (IMA-01). The disk has 12 GiB free; the project needs about 6 GiB.

**What I could not determine.** How the tree moved to the Desktop after the recovery reports were written, and whether Desktop syncing could be switched back on by a system setting.

**Options.**
- (a) External drive or second machine for the hash-verified copy; keep working where you are.
- (b) As (a), and also move the working repository to a folder that no cloud service manages (for example `~/Research/Train_automation`).
- (c) Second copy on the same disk only.

**Pushing.** The preservation branch would contain source, tests, scripts, documents, manifests and candidate annotations — no video, no weights. If the GitHub repository is public, the candidates and site details become public.

**Recommended.** (b), with a push to a **private** repository or a private branch. A same-disk copy does not protect against the failure you already had. Tell Sonnet the destination path and whether the remote is private.

**Blocks.** Phase 0, and therefore everything.

## D-2 — The "APPROVED" review records

**Situation.** All 27 files in `data/ground_truth/reviews/` say `adjudication_status: APPROVED`, `reviewer_id: human_researcher_lead`, with 154 fields "accepted", 46 "marked unobservable" and none corrected, all stamped within one hour on 2026-10-12, each pointing at a proposal version that has since been superseded (IMA-06).

**What I need from you.** A yes or no: did you personally perform any of these reviews?

**Recommended.** If no — which is what you told me — they are listed in an invalidation file and no loader will ever accept them. They stay on disk as history. If any were yours, say which, and they will still need re-review against the current candidates.

**Blocks.** Gate F.

## D-3 — Camera synchronisation

**Situation.** The code fuses the two cameras as if they started together. Their recording-start tags differ by up to 33 s (IMA-11). Entry is annotated on the front clock, clearance on the back clock.

**Missing evidence.** A measured offset per event.

**Options.**
- (a) Estimate offsets from the two audio tracks by cross-correlation, with the quality and acceptance rule in design §6.3. You confirm each accepted event with one frame pair. Fused analysis is primary only if at least 20 of 23 train events pass; otherwise independent-camera analysis is primary.
- (b) Skip calibration. Independent-camera analysis only; no dual-camera claim.
- (c) Manual offsets from a visual event in both views. Slower, coarser (one frame at best), and subjective.

**Recommended.** (a). It uses evidence already in the recordings, takes little code, and decides the mode by a rule fixed in advance. Independent-camera results are produced either way. I have not listened to the audio, so I cannot promise the two devices recorded enough common sound; if they did not, the rule falls back to (b) automatically.

**Your part.** Accept the thresholds as written (peak ratio ≥ 2.0, uncertainty ≤ 0.10 s, 20 of 23), then do the frame-pair check per event.

**Blocks.** Fused conditions only. Not raw inference, not annotation.

## D-4 — Clearance rule and fault recovery

**Situation.** The documents promise that the barrier reopens only after "positive rear confirmation". The code does not implement that (IMA-15), and in the field outputs `rear` is 1.2% of detections, with none at all in several events. A rule that truly requires `rear` would leave the barrier closed in many events. The fault state has no exit (IMA-16).

**Options for clearance.**
- (a) **Absence with dwell** (`ABS`): reopen after 3.0 s with no train detection on any available camera. Measurable, usable, exposed to detector dropout — which is exactly what the premature-opening metric measures.
- (b) **Rear required** (`REAR`): as (a) but only if a `rear` detection has been seen. Matches the written invariant; likely fails to reopen often.
- (c) Report both: one primary, one as a predeclared variant. Costs nothing extra in inference; both replay from the same raw outputs.

**Options for fault recovery.**
- (i) Automatic: after 3.0 s with a camera back, move to a closed holding state and let the normal clearance rule decide.
- (ii) Latched: stay closed until an operator reset (in replay: until the clip ends).

**Recommended.** (c) with `ABS` primary, and (i). `ABS` lets the study measure the trade-off between unsafe reopening and failure to reopen; `REAR` shows what the original design intention costs. Choosing which is primary must happen before the formal replay and must not be revisited afterwards.

**Blocks.** Phase 3.

## D-5 — Audio authority

**Situation.** Protocol v9 (§12.1, INV-2) says a confirmed horn may start a warning. The code says audio may never cause any actuation and can only postpone clearance (IMA-20). Under the code's rule, audio cannot produce the "earlier warning" the protocol hypothesises.

**Options.** (a) Supporting only. (b) Audio on 2 consecutive windows may start a warning; it can never grant or shorten clearance.

**Recommended.** (a). The audio model was trained on a different acoustic domain, its only field outputs so far are invalid (IMA-22), and you have three one-minute negatives to detect false warnings with. Giving it actuation authority now would add a nuisance-closure pathway you cannot characterise. Under (a) the E7-vs-E5 contrast will probably be small; report that as the finding. If you prefer (b), it is a one-line configuration difference, but decide before Phase 3.

**Blocks.** Phases 2–3.

## D-6 — Temporal filter

**Situation.** Documents describe confirmation, EMA smoothing (α = 0.5), miss tolerance and evidence expiry. Only confirmation exists in the experiment code (IMA-25). A stateless baseline with no miss tolerance reopens on every one-frame gap, which makes it a strawman.

**Options.** (a) Confirm 2 ticks, tolerate 2 missed ticks; no EMA. (b) Implement EMA as documented.

**Recommended.** (a). Both values are already in the frozen list, so nothing is being tuned. EMA would need a definition (over what quantity, with what threshold) that no document gives.

**Blocks.** Phases 2–3.

## D-7 — Negative controls

**Situation.** The detector fires in all three no-train clips; in `no_train_events/event_002` the front camera has a `side` detection in 60 of 60 frames at up to 0.86 confidence (IMA-21). I have not viewed the video. Total negative exposure is about one minute per camera, all from one evening (IMA-44).

**What I need from you.** Watch the three clips, both cameras, and state for each whether any rail vehicle is visible or audible.

**Options on exposure.** (a) Proceed with three clips and report counts only. (b) Record 30–60 minutes of continuous no-train footage at the crossing from a fixed position.

**Recommended.** Do the check now. (b) is the single most valuable addition to the dataset if a nuisance-closure statement matters to the paper; without it the paper can only say "closed in k of 3 short clips".

**Blocks.** Reporting of N1. Nothing else.

## D-8 — Second annotator

**Situation.** Candidates were machine-proposed and show template-like regularity (IMA-07). One annotator gives no estimate of timing uncertainty.

**Options.** (a) A second person independently marks T1 and T4 on at least 8 train events (include events from both sessions). (b) Single annotator; fixed tolerance of 0.5 s.

**Recommended.** (a). Roughly two hours of someone's time, and it gives an empirical tolerance for every timing comparison in the paper.

**Blocks.** Nothing if you choose (b); Gate F waits for the second set if you choose (a).

## D-9 — Engine-only event

**Situation.** The latest candidate puts T3 on the front camera at 6.2 s and marks T4 unobservable on the back camera; the review record asserts T4 = 6.2; the protocol says T3 ≡ T4 for an engine. The candidate's rationale also cites a detection confidence (IMA-09).

**Options.** (a) T3 and T4 are the same instant on the back camera; right-censored at the clip end if the locomotive has not cleared. (b) Use the front-camera clearance for both.

**Recommended.** (a). The departure boundary is defined on the back view for every other event. With (a) this event will probably be censored for reopening metrics and should be reported as such.

**Blocks.** Approval of one file.

## D-10 — Primary endpoints

**Situation.** With the frozen 2 s warning and 3 s closing times, the barrier cannot block before about 3.6 s into a clip. Candidate entry times are at or below 3.2 s in 18 of 22 events, and most clips start with the train already visible. Candidate tail clearance is 1.0–2.7 s before the end of 20 of 22 back recordings, shorter than the 3 s clearance dwell (IMA-31). If the approved labels look like the candidates, "missed-train rate" would be near 100% for any detector and "premature-opening rate" near 0% for any policy that waits.

**Missing evidence.** Approved T0, T1 and T4. The arithmetic does not depend on them; how many events are affected does.

**Options.**
- (a) Keep the protocol's endpoints and report them however they fall.
- (b) Design §8: **M4** (reopening during occupancy) and **M7** (reopened within the recording, with explicit censoring) primary; **M1** (warning issued before entry) as the key secondary; **M3** (blocked at entry) reported only for events that pass a stated feasibility screen, with the screen table published.
- (c) Shorten the warning or closing times so more events become feasible.

**Recommended.** (b). It measures what these recordings can show and states what they cannot. (c) would be tuning a frozen parameter to the evaluation data and must not be done.

**Blocks.** Phase 8.

## D-11 — Pilot contamination

**Situation.** The decision policy has to be corrected, and its behaviour on these 27 events has already been seen (IMA-47).

**Options.** (a) Specify the corrected policy in advance (done in design §5), verify on synthetic traces only, freeze by commit before the formal replay, and say so in the paper. (b) As (a), plus record a small confirmatory set — tripods, 30 s before and after each passage, a clap for synchronisation — evaluated once with the frozen system.

**Recommended.** (a) is sufficient for a pilot paper with honest scope. (b) is what would let you call the result a held-out test, and it would also fix the short-clip problem in D-10.

**Blocks.** Nothing in the plan. Affects how the result may be described.

---

## Blockers that are not decisions

| Blocker | Who | Unblocks |
|---|---|---|
| Frame-by-frame review and approval of 27 events; listening check for horns | You | Gate F, formal evaluation |
| Frame-pair acceptance of estimated camera offsets | You | Fused conditions |
| Signing `APPROVAL_MANIFEST.json` | You, by hand | Gate F |
| A working Python environment | Sonnet, Phase 1 | All execution |
| Checkpoint key inspection (confirms the audio normalisation finding) | Sonnet, Phase 1 | Phase 2 |
