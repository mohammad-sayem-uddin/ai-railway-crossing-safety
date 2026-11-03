# Mission 10 — Adversarial Self-Audit

> Written for: the next independent auditor. This is the author attacking their own work; it is **not** an
> independent audit and does not substitute for one. Scripts: `/private/tmp/claude-501/m10/mutate.py` (mutation
> probes) — reproduce with `PYTHONPATH=<mutated src> pytest -o pythonpath= …` (the repo's `pythonpath` setting
> otherwise overrides the mutated tree).

## A. Mutation probes (does a test notice if the control is removed?)
| # | Mutation of the new code | Result |
|---|---|---|
| M01 | `assess_second_reviews` returns no findings | killed |
| M02 | readiness gate ignores second-review findings | killed |
| M03 | execution-gate (consumer) skips its own re-validation | killed |
| M04 | review comparison uses a 1 ms tolerance | killed |
| M05 | media guard becomes a no-op | killed |
| M06 | `revoked` tested by truthiness (accepts `"false"`/`0`) | killed |
| M07 | `repo_root` override allowed for real-repo media | killed |
| M08 | expiry not checked | killed |
| M09 | bound protocol document not re-hashed | killed |
| M10 | hash-pair opener loses its guard | killed |
| M11 | descriptive binding comparison disabled | killed |
| M12 | replay engine drops the per-condition gate | **survived first**, test added, killed |
| M13 | `classify_m4` uses a closed interval | killed |
| M14 | M5 zero-origin rule dropped | killed |
| M15 | manifest staleness check disabled | killed |
| M16 | access guard stops blocking | killed |
| M17 | loader counts a second review as a second event | **survived first**, tests added, killed |

## B. Live bypass attempts (run, observed)
1. `scripts/extract_sync_review_frames.py --event train_events/event_010` on the real repository → refused
   (`AUTH_MEDIA_ACCESS_NOT_GRANTED`) before any file was touched; also with the old env var
   `RAILWAY_ALLOW_RESTRICTED_MEDIA_ACCESS=1` set → still refused.
2. `scripts/run_phase5_full_inference.py` → refused before `reports/progress.md` was touched (mtime unchanged).
3. Direct library calls on a real `camera_front.mov` path: `extract_audio_from_video`, `inspect_media_file`,
   `compute_file_sha256` → refused; no output file created.
4. Symlink from the temp directory to real media → still guarded (test). `repo_root` pointing at a hand-made tree
   with a valid record → refused for real-repo media (test).
5. Forged but self-consistent promotion receipt after deleting the second review → receipt verifies, consumer still
   refuses (`INDEPENDENT_SECOND_REVIEW_MISSING`) (test).
6. Self-reviewing (same reviewer, case variant, non-allowlisted, REJECTED second) → refused (tests).
7. A test that reaches real media is *recorded* as raw-media access even though the boundary guard stopped it
   (found during the work: `test_exploratory_subset_authorization_gate`, fixed as N-03).
8. A mis-classified manifest entry is detected by the runner's post-run log check (test), not trusted.

## C. Things that could still be wrong (author's list)
* The guard is Python-level; `cp`, hard links, or an unwrapped native library are outside it.
* The static opener scan is heuristic; the allowlist (27 entries, each with a stated reason) was reviewed by me only.
* `categorize()` treats `tests/`, `src/`, `scripts/` as code; a test fixture directory under `tests/` holding real
  media would not be guarded (none exists; a media suffix anywhere in the repo is still RAW).
* The oracle for M4/M5 encodes the *documented* rules; if the documented rules are wrong the oracle agrees with the error.
* `FRONT_BACK_CONFLICT` is not evaluated; trigger 6 is skipped when no repository root is supplied (disclosed in
  evidence; the CLI and execution gate always supply it).
* RD-043 is a proposal; enforcing it is my choice of the safe side and the researcher may prefer to adopt, amend or drop it.
* Tests that previously asserted READY now include an independent second review — an auditor should read
  `tests/second_review_support.py` to confirm it models a distinct, allowlisted, agreeing reviewer and nothing more.
