# Phase 2 Completion Report — Protocol and Research-Design Consolidation (Mission 5B)

**Status: PASS WITH CONDITIONS.** All twelve acceptance criteria of the prompt are met except that the repository is **not** lint-clean (the 59 Phase 1 findings were deliberately left) and **nine scientific or factual questions need the researcher** (Section 15). Nothing in this phase is approved, hash-bound or authorized. Phase 3 has not been started.

Written for: the researcher, reviewing Gate 2.

---

## 1. Executive summary

Four proposal documents, two unified diffs, a snapshot-preparation helper, a 110-test synthetic suite and this report were created. No existing file was modified. The two working-tree protocols (v9.0.0, v7.0.0), the experiment-design reference, the paper draft, the frozen configuration and the frozen policy are byte-identical to their starting hashes.

The four residual v9.1.0 contradictions named in the plan are resolved: EMA removed from the active experiment path; audio reduced to supporting evidence; the independent-camera design replaces E1–E10 as the primary matrix; inferential and outcome-predicting claims removed. The Phase 1 metric contract is written into the protocol (§5.2.1, §5.7) and each reason string it names is checked against the production code by a test. The review also found issues beyond the plan's list (Section 15): a mislabeled hash and invented items in the paper draft, a conflict between an audio-only condition and RD-030, a naming collision with the legacy runner, and conflicting dataset facts across source documents. These are surfaced, not resolved.

## 2. Initial repository state (read-only audit, before any work)

| Item | Observed |
|---|---|
| Path / branch / HEAD | `/Users/sayemuddin/Desktop/Train_automation` · `main` · `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b` |
| Staged | **0** · modified tracked **19** (identical to the original list) · untracked entries **361** |
| Phase 1 report | present; Phase 1 manifest `verify`: 872 ok · 0 missing · 0 changed · 0 refused · `clean: true` |
| v9.0.0 working tree | `7c183b323970591b68f0db692e70413e54dcacfc4bf78a358c28f1b1ed68734c` — equals the historical baseline |
| v7.0.0 working tree | `d100c1e6a63280c375f94e297416efb0cf7dd3c15c9aa8df076ede052d49ecf4` — equals the historical baseline |
| Other protected files | `EXPERIMENT_DESIGN_FINAL.md` `2e906c1e…` · `PAPER_DRAFT_DESCRIPTIVE_BENCHMARK.md` `03444930…` · `frozen_experiment_v1.yaml` (raw) `b8ef5da0…` · `decision_policy_v1.yaml` (raw) `c87c1432…` |

No stop condition was triggered. I did not rely on the Phase 1 report's claims alone: its manifest, the protocol hashes, the git state, and the production code behavior it describes were re-checked (the tests exercise `classify_m4`, the screen and `evaluate_event_replay`).

## 3. Phase 1 baseline and conditions acknowledged

DEC-C01…C05 and F-19 are reflected as implemented. The four conditions are preserved, not resolved: (1) 59 Ruff findings remain (Section 11); (2) **no** sampling-gap or density threshold for M5 was invented, and the protocol states that sampled replay does not establish continuous state; (3) a censored $T_0$ with unknown direction is *unverifiable* for the physical screen in both v9.1.1 (§5.3 item 4, §5.7) and v7.1.1 (§2.3); (4) literal M3 is stated as existing on `LeadInScreenResult` only, with propagation into the evaluation record and summary preserved as a **Phase 4** requirement — a test asserts that statement is currently true of the code.

## 4. DEC-C06 workflow used

DEC-C06-A: proposals are under `docs/generated/phase2/`; nothing was copied into `docs/FINAL_*.md`; no agent commit; no protocol hash binding; no governance record. The helper prepares and verifies; the researcher adopts, commits and snapshots (Section 18).

## 5. v9.1.1 reconciliation table

File: `FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL_v9.1.1_PROPOSED.md` (619 lines; 18 marked historical blocks).

| Item | Resolution | Authority |
|---|---|---|
| Heading / status | First heading `# PROPOSED — Final Real-World Experiment Protocol (v9.1.1-PROPOSED)`; banner `PROPOSED — NOT APPROVED — NOT HASH-BOUND`; "authority" text rewritten as *proposed, effective only if adopted* | prompt §6.1 |
| A. EMA | Active EMA α = 0.50 removed (§2.3, §14); "no EMA" stated; the code and frozen config verified to contain none; old text kept in historical blocks | RD-031 |
| B. Audio authority | §12.1, INV-2 rewritten: audio is supporting evidence only; cannot initiate a warning, start the transition, or grant clearance; cites `RULE_2_AUDIO_SUPPORT_ONLY` (policy file untouched); §17 no longer credits audio with advance warning | RD-030 |
| C. Execution order | §8 independent-camera design: front `B0`/`B1`/`B2`; back `B0_back`, `B0_back_stateless`, `B2_back` (*provisional*); fused R04 exploratory, existing 11-event scope; `event_010` not added. E1–E10 matrix and 22-step order moved to historical blocks; §26 is now an explicitly **unauthorized** dependency order | RD-015/028/035, RD-026 |
| D. Claims | §1 objective and central question reframed as descriptive; §19 inferential text already historical; §24 "Supported" claims replaced by claim boundaries; §27 self-critique outcome predictions and "large effect sizes" moved to historical | RD-023, RD-051–053 |
| M4 / M5 / empty interval / grid | new §5.2.1 (nine rules) matching Phase 1: observed first blocked step, strict open interval, witnessed violation, reach $T_4$, ≥1 interior step else `no_steps_in_protection_interval` (not safe, with diagnostics), M4 needs no zero origin, M5 needs zero origin + coverage, `replay_started_late`, `replay_started_at_or_after_T4`, `round(float(t), 6)` with strict comparisons, no density threshold, sampled-replay limitation | DEC-C01/02/05 |
| Lead-in screen | new §5.7: physical screen primary; literal M3 secondary; default off; unverifiable for unknown-direction $T_0$; latency not an approved threshold (the number 3.6 is not printed in the protocols); Phase 4 integration noted | DEC-C03 |
| Priorities | M4 primary, M5 companion count, MTR secondary; "descriptive goal 0.0 %" removed (no acceptance threshold) | RD-022 |
| Engineering corrections | §13 controller states replaced by the implemented `CrossingState` names (old chain historical); reference to v6.0.0 / `file://` link replaced; change log made a historical record | Category A |
| Not changed | §5.1 boundary table, §6 GT lifecycle, §7 alignment, §11 no-train exposure, §20–21, §25, §28.1 prerequisite statuses (R01–R04 are as of v9.0.0 and were not re-verified) | — |

## 6. v7.1.1 reconciliation table

File: `FINAL_GROUND_TRUTH_PROTOCOL_v7.1.1_PROPOSED.md` (877 lines; 3 historical blocks).

| Item | Resolution |
|---|---|
| Heading / status | `# PROPOSED — Final Ground Truth Annotation Protocol (v7.1.1-PROPOSED)`; same banner; states that no ground-truth record exists and every JSON example is mock |
| Cross-references | v9.1.0 → v9.1.1 (§2.2) |
| $T_4$ role | "baseline for POR" → M4/M5 and clearance latency (§2.1) |
| Premature opening | GT supplies only $T_4$, never $t_{\text{blocked}}$; replay rules deferred to v9.1.1 §5.2.1; grid `round(float(t), 6)`, strict, no tolerance; review tolerance stays DEFERRED (§2.2) |
| Censoring direction | New in §2.3: a censored/uncertain $T_0$ must record its direction; unknown direction → screen *unverifiable*; visibility from $t=0$ never inferred. Notes the proposed Stage-2.1 schema would require it (inactive) |
| Illustrative examples | §6.0 gains item 5: `"approval_status": "APPROVED"`, verifier ids and model fields are placeholders, not evidence, and must not be copied into `data/ground_truth/` |
| Fix | "EMA states" removed from the anti-leakage list (no EMA exists) |
| Unchanged | T0–T4 definitions, T1 frog line, T2 deferred landmark, CCA, applicability matrix, horn schema, no-train rules, alignment, prerequisites R01–R04 text, manifest spec |

## 7. Experiment-design changes

`EXPERIMENT_DESIGN_CONSOLIDATED.md` (158 lines): authority vocabulary separating confirmed directions, formal approvals, proposals and authorizations; independent-camera design; the required eight-column metric table (13 rows, each with an implementation status checked against the code or marked unverified); Phase 1 contract; frozen-policy limitations; population rules (engine outside pooled aggregates, no-train separate, fault injection separate, 11-event R04, no `event_010`); descriptive statistics only; deferred items; an empty results skeleton (`[RESULTS PENDING]` / `NOT COMPUTABLE`); a disposition table for every item of `EXPERIMENT_DESIGN_FINAL.md`; ten open questions. One sentence I had adopted from the non-binding design ("fewer than 10 evaluable events → counts only") was removed because it is not in the decision record.

## 8. Paper revision changes

`PAPER_REVISION_CONSOLIDATED.md` (139 lines): all thirteen requested sections; proposed title (RD-052); RQ1–RQ4 (RD-051); human authors only with placeholders (no names, affiliations, ORCIDs or venue); AI-use disclosure *draft*; claim boundaries with an explicit "must not claim" block; an empty results skeleton; and a **twenty-row table of corrections the current draft needs** (Section 15 lists the ones that require a decision). The draft file is untouched.

## 9. Snapshot helper safety design

`scripts/prepare_researcher_snapshot.py` (`check` writes nothing; `prepare` writes three files into a **new** directory).
- **Git:** one function, allow-listed to `rev-parse HEAD`, `rev-parse --abbrev-ref HEAD`, `status --porcelain`, `diff --cached --name-only`; any other verb raises before a process starts. A missing git binary is reported, not raised. Untracked entries are only counted; media-named entries are never listed.
- **Paths:** relative only; no `..`; no symlinks anywhere on the path; must stay inside the root; **text extensions only**; every media/binary extension refused before any open; no `os.walk`/`listdir`/`scandir`/`glob` anywhere (a test patches all of them to raise).
- **Refusals:** missing source (2) · baseline mismatch (3, nothing written) · proposal not labelled PROPOSED / banner missing / header claims approval (3) · a proposal that is itself a protocol file · existing destination (2, nothing written) · output outside `docs/generated/` or through a symlink · file appearing mid-write (exclusive-create; the helper removes only files it created, never an existing one).
- **Never:** `git add/commit/push/reset/clean/checkout/restore`, copying over a protocol file, signing, hash-bound records, governance edits. Proposal hashes are emitted under the key `sha256_PROPOSAL_NOT_APPROVED_NOT_BOUND`.
- **Run on the real repository:** `check` then `prepare` produced `docs/generated/phase2/snapshot_prep/{SNAPSHOT_INVENTORY.json, ADOPTION_CHECKLIST.md, SNAPSHOT_REPORT.md}`; a second `prepare` was refused (exit 2) and changed nothing. These three generated files were written by the helper's designated report step.
- Bugs I found in my own helper while testing: an approval check that was case-insensitive and rejected the proposals' own prose ("must never be treated as an approved … hash"); a default argument that could not be overridden for tests. Both fixed.

## 10. Test files and exact results

All commands with `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest … -p no:cacheprovider -q`.

| File | Result |
|---|---|
| `tests/unit/test_phase2_protocol_consolidation.py` (new) | **110 passed** in 0.69 s |
| Cumulative synthetic set (the 20-file Mission 5A.1 set + `test_phase1_metric_closure.py` + `test_descriptive_only.py` + `test_metadata_only_audit.py` + the Phase 2 file; `-rs`) | **914 passed**, 0 failed, 0 skipped, 13.43 s (804 at the end of Phase 1 + 110) |

The prompt's "at least 725 cumulative" target is exceeded; I report the actual count and did not adjust scope to reach it. Not run, as before: `test_readiness_audit.py` (reads the real `data/ground_truth`), audio tests, real-inventory/loader tests, integration tests.

**Run history:** first run of the new file 106 passed / 4 failed. The failures exposed two real defects, not test errors: (1) the helper's case-insensitive approval check (above); (2) both proposal banners mentioned the literal historical markers in prose, producing a spurious "historical block" for any marker-parsing tool — the banner wording was changed and both diffs regenerated (hashes in Section 13 are of the final files). Then 110 passed.

**Coverage of the 26 required tests** (class → items): `TestProposalLabelling` 1–3 · `TestEmaAndAudioAuthority` 4–6 · `TestIndependentCameraDesign` 7–10 · `TestMetricContractMatchesPhase1` 11–17 (plus the 3.6-never-approved check) · `TestScopeStatisticsAndClaims` 18–22 · `TestWorkingTreeUntouched` 23 · `TestSnapshotHelperWorks` 24 · `TestSnapshotHelperRefuses` 25 · `TestSnapshotHelperNeverWritesToGit` 26. Tests read the generated artifacts with historical blocks stripped and, wherever a document states a code behavior (reason strings, zero-origin M5, grid, default-off, no density limit, literal-M3 not yet propagated), they also call the production function. In-memory mutation check: injecting an active EMA line, an audio-initiates-warning sentence, an `event_010` scope line or a McNemar sentence is each caught; historical text is correctly exempt.

**Caveat:** `TestWorkingTreeUntouched` pins the pre-adoption hashes. When you adopt wording at Gate 2 it will correctly fail; update or retire it then.

## 11. Ruff results

`ruff check scripts/prepare_researcher_snapshot.py tests/unit/test_phase2_protocol_consolidation.py --no-cache` → **All checks passed.** Combined with the Phase 1 Python files (eight files in total) → **All checks passed.** `ruff format` was applied to the two new files only. **The repository is not lint-clean**: `preflight_validator.py` 36 · `batch_multimodal_annotator.py` 16 · `test_mission2_pipeline_integrity.py` 7 (the Phase 1 59, re-measured today) plus single E501 findings in `descriptive_only.py` and `metadata_only_audit.py`. None was touched.

## 12. Protocol hashes before and after

| File | Before | After |
|---|---|---|
| `docs/FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md` (v9.0.0) | `7c183b323970591b68f0db692e70413e54dcacfc4bf78a358c28f1b1ed68734c` | **identical** |
| `docs/FINAL_GROUND_TRUTH_PROTOCOL.md` (v7.0.0) | `d100c1e6a63280c375f94e297416efb0cf7dd3c15c9aa8df076ede052d49ecf4` | **identical** |
| `docs/EXPERIMENT_DESIGN_FINAL.md` | `2e906c1e19426d2fa406fe626858b0b308fc6abb38510afd660768e954fbb407` | identical |
| `docs/PAPER_DRAFT_DESCRIPTIVE_BENCHMARK.md` | `03444930ec0d73e9dad16a2b510511c61e9a1302e3e6a25cf83307d81a26ea78` | identical |
| `configs/frozen_experiment_v1.yaml` (raw) | `b8ef5da052f002e75a2da0985add02a72d0d5684936263c14257aa12b0c9ac9a` | identical |
| `configs/decision_policy_v1.yaml` (raw) | `c87c1432f473f84def46d343429c21bcd5329adcbce6cfdf7933de446a0c8575` | identical |

## 13. Generated document hashes (SHA-256) — **proposal hashes, not approved or bound hashes**

| File | SHA-256 |
|---|---|
| `FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL_v9.1.1_PROPOSED.md` | `8386c2b295166eb01da644251f1eb5f0d584e207d6dac33f0dcd7849ef56168e` |
| `FINAL_GROUND_TRUTH_PROTOCOL_v7.1.1_PROPOSED.md` | `23b383b89c57e97852f60e320c8e4feb25d99ac6492e399db281abb126b92a6d` |
| `v9_working_tree_vs_v9.1.1_PROPOSED.diff` | `564e61185ecbeadcbac1e5d4973e9ab7d0c2ea3f70bc1afbdd0ab5298d438a81` |
| `v7_working_tree_vs_v7.1.1_PROPOSED.diff` | `4330b24b9fd4dc7be95d0cf6b01b5992abfacdb1564abc5b5c2ff36f5481eb99` |
| `EXPERIMENT_DESIGN_CONSOLIDATED.md` | `f9ae618bb1d61afe7610d28c3a3399293f5b28a76d9abb12ad8dfb53285c2d1b` |
| `PAPER_REVISION_CONSOLIDATED.md` | `6396416a13a26a7a0029ddb9e7e0161d7f77c43e1795759388680a649cbc8539` |
| `scripts/prepare_researcher_snapshot.py` | `6d5687a8d8f47314ca31b28209c8ac079af2cbeb37719807d6ee505ca862848f` |
| `tests/unit/test_phase2_protocol_consolidation.py` | `79acda74ad8e83c2120247f7690ecdfca3eaab17b8fb2ed9394e1c15178740d1` |
| `snapshot_prep/SNAPSHOT_INVENTORY.json` | `68ededf22499c176873aab2b1bb5fed45942bfc0513f642540f6b45a4fec124a` |
| `snapshot_prep/ADOPTION_CHECKLIST.md` | `bf610409de8f3b47f4ade4b2e6d3f1fe86a7733e84d91ecc5831b0c0d984c266` |
| `snapshot_prep/SNAPSHOT_REPORT.md` | `ab1df82b44f355745bf83444d97f0d8db2738519bdbfe31f272f006f306263c8` |
| `PHASE_2_COMPLETION_REPORT.md` | this file (not hashed, to avoid self-reference) |

The diffs are plain `diff -u` output (no Git involved). If you request revisions, every hash above changes; recompute after the final wording.

## 14. Git preservation status

`HEAD` unchanged `d4db94d4…`; **staged 0**; modified tracked **19** (name-for-name identical to the original list); untracked entries **363** (361 at the start, plus two new files: `scripts/prepare_researcher_snapshot.py` and `tests/unit/test_phase2_protocol_consolidation.py`; `docs/generated/` was already one untracked directory entry). No Git write command was run by me or the helper.
**Exposure:** the commit `d4db94d4` does not contain most governing code, tests, protocols' proposals or the Phase 1/2 work, which are untracked or modified. Until you commit, none of it is in version control. The Phase 1 preservation manifest still verifies clean (872 entries); the Phase 2 files are not in it (a new manifest build, and the off-Desktop snapshot of `SNAPSHOT_PROPOSAL_20261101_M5A.md`, are Gate 2 actions). No snapshot was created.

## 15. Unresolved decisions and findings for the researcher

1. **`B1` (front audio-only) vs RD-030.** Under the frozen policy audio alone cannot actuate the gate, so `B1` cannot produce gate-level MTR or lead-time outcomes. I listed it as acoustic-detection descriptors only and flagged it; you decide how it is reported or whether it is dropped.
2. **Condition naming.** The legacy runner's labels B0–B7 mean something else (its B2 is dual-camera and stateless). The provisional back-stream names are used as instructed; whether a `stateless` back-stream replay configuration exists is **not verified**; back-stream audio availability is not verified.
3. **Paper draft contains unsupported or wrong items** (full table in the paper document): the `c87c1432…` hash is attributed to `decision_engine.py` but is the raw hash of `decision_policy_v1.yaml` (the engine source hashes differently); an engine $T_3 \equiv T_4 = 6.20$ s value taken from an unapproved candidate; invented future-work targets; rolling-stock and no-train descriptions without a source; a listed AI author and named venue; references 7–9 that I could not confirm (no literature search was performed); the HEAD commit offered as the reproducibility anchor although it omits most governing files.
4. **Conflicting dataset facts across sources:** session dates (design doc 2026-09-14 / 2026-10-04; paper draft 3 and 7 October 2026); acquisition hardware (handheld vs tripod); left-censoring count (23/23 vs 20/23); a night stratum mentioned in an earlier protocol draft vs "no night recordings" in the paper. None is asserted in any proposal; they must come from approved metadata.
5. **v9 objective reframed.** §1 now states a descriptive objective consistent with RD-051–053 and moves the "improves reliability / better than baselines" objective to a historical block. This is my reading of the confirmed direction; please confirm the wording.
6. **M5 density** (no threshold; sparse pre-$T_4$ replay can be M5), **censoring direction** (loader has no field), **literal M3 propagation** — Phase 1 conditions carried forward unchanged.
7. **Not implemented / not verified:** detection latency (defined in v9 §18, no evaluation field), gate-chatter count for train events, the tick conflict (`tick_interval_s` 0.1 unused vs `timing.tick_s` 0.2).
8. **Engineering fix I made without a decision:** controller state names in v9 §13/INV text were corrected to the implemented `CrossingState` set (old chain kept historical). Veto if you prefer the old names.
9. v9 §28.1 prerequisite statuses (R01–R04) are carried from v9.0.0 and were not re-verified against the repository.

Still pending (not decided, not created): `GOV-D1-PROTOCOL-AUTHORITY`, `GOV-D2` (M4/M5 contract), `GOV-D4` (R04 11-event scope), ratification of the four 2026-10-30 items, thresholds/ROI/B7e approvals, inventory sign-off, reviewer/pilot/media/promotion/evaluation authorizations, the official split (not created), `EVAL-AUTH`.

## 16. Deviations from the prompt

- Three generated files under `snapshot_prep/` exist in the repository (the helper's designated report output).
- I added HTML-comment markers `<!--NOT-CLAIMS-->` and `<!--RESULTS-TABLES-->` so tests can inspect claim and results sections; they are inert in rendering.
- Diffs are produced with `diff -u` using descriptive labels, not `git diff`.
- The work was interrupted by a session resume partway; three scratch files in the temporary directory were lost. No repository file was affected, and the final verification was rerun after the resume.
- I did not re-derive the 5A.1 20-file test list; it is inherited, as in Phase 1.

## 17. Prohibited-operation checklist

Not performed: opening, previewing, hashing or enumerating any `.mov/.mp4/.wav/.mp3`; inference, training, replay, timing pilot, real-data evaluation, cache generation; media access for annotation; any Stage-2.1 record, ground-truth promotion or receipt; an official split; any GOV/EXP/AUTH/EVAL-AUTH record or signature; activation of real-data evaluation; any change to checkpoints, frozen configs, decision policies or numeric thresholds; `event_010` added to R04; occupancy duration implemented or $T_2$ geometry invented; B7e numerics; any inferential test; invented authors, affiliations, ORCIDs, venue, results or signatures; any `git add/commit/push/reset/clean/checkout/restore`; modification of the two protocol files, `EXPERIMENT_DESIGN_FINAL.md`, the paper draft, configs, or any existing file.
Read-only accesses that did occur, for accuracy: text documents named in the plan; the frozen config and policy YAML (read by tests and for facts); `git status/rev-parse/diff --cached` (by me and by the helper); and the Phase 1 manifest `verify`, which SHA-256-hashes text files under `data/governance`, `data/ground_truth`, `data/manifests`, `data/splits` (metadata only; contents not parsed).

## 18. Gate 2 — researcher action list

Review package, in reading order: (1) `FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL_v9.1.1_PROPOSED.md` and its diff; (2) `FINAL_GROUND_TRUTH_PROTOCOL_v7.1.1_PROPOSED.md` and its diff; (3) `EXPERIMENT_DESIGN_CONSOLIDATED.md`; (4) `PAPER_REVISION_CONSOLIDATED.md` (§15 table first); (5) `snapshot_prep/ADOPTION_CHECKLIST.md`; (6) Section 15 above.

You decide, for each document: **adopt**, **request revisions**, **preserve without adopting**, or **adopt and commit/snapshot yourself**. I have done none of these. If you adopt:
1. Edit the protocol files yourself; remove the `PROPOSED` labels.
2. Commit the governing set on a branch you choose, after reviewing `git status` (raw media and generated output trees must not be committed by accident).
3. Rebuild the manifest and create the off-Desktop snapshot you approve.
4. Compute the final protocol hashes from the adopted files; only then author `GOV-D1`.
5. Update or retire `TestWorkingTreeUntouched` and the helper's baselines.

Categories at a glance — **Researcher-confirmed directions:** RD-001…055 and DEC-C01…C06 as recorded. **Agent-prepared proposals:** everything in `docs/generated/phase2/`. **Formal approvals pending:** all in Section 15. **Execution authorizations pending:** all.
