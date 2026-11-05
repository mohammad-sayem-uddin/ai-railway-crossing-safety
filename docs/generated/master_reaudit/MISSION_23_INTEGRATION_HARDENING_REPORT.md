# Mission 23 — Integration hardening

Prepared 2026-11-05, America/New_York. No scientific command mapping, production resource permission or human evidence is created.

## Defect and implementation

Mission 22 verified detached B outputs and their metric/lineage joins, but its completed-demo verifier did not compare every public result and deterministic artifact. A caller could substitute a mock-review object, boundary projection, separate A receipt or results-absent report and coherently update its file digest. Hash consistency alone did not reject those substitutions.

Completion verification now runs a fresh constructed workflow in an owned temporary directory, compares the entire public execution object, and compares every artifact in the closed nine-file set byte-for-byte. Existing source/config/event/B replay checks and alias/path guards remain. A completed run containing pending RUN/ACK/result/report/completion metadata is refused. Verification does not mutate the completed original; it creates and cleans a separate temporary replay. Resume therefore includes temporary constructed execution rather than only reading files.

Executed negatives cover coherently rehashed substitutions of review, boundary projection and A outputs, and rehashed report, snapshot source and ACK artifacts; all refuse. A pending ACK is also refused. Original Mission 22 tests cover stale descriptors, camera identity, exact timestamps, missing/censored metrics, lineage joins, authority boundaries, interruptions and resume. SQLite bytes remain outside the deterministic artifact set; this verification does not establish live database health, machine durability or root-compromise resistance.

## Fixture alternatives and boundaries

New tests exercise the actual audio dataset loader and pretraining validation gates against declared constructed manifests and64×61 feature arrays in temporary directories. No training or calibration runs. Original assertions about the real corpus, duplicate recordings or precomputed production features remain blocked; fixture results are not substituted for those facts.

The LEG-EXEC fixture copies27 real legacy reviews/allowlist and depends on the genuine pinned proposal/source bindings. Its25 setup failures cannot be resolved by fabricating a matching source corpus or authorization. Separate tests run the real review-readiness audit on three explicitly constructed, non-promotable legacy-shaped records, reject a relabeled active-schema body and retain denial of missing genuine execution prerequisites. No reviewer is appointed and no observation or promotion receipt is produced.

Two benchmark fixture tests call the same CLI with explicitly injected parsed configuration metadata, unverified artifact fingerprints and a constructed host description. The CLI writes its diagnostic report but correctly returns unverified acceptance and forbids timing claims; no checkpoint hash is manufactured. A reproducibility CLI test uses an empty constructed project and reports missing evidence. These alternatives establish callable/report behavior, not the eight original production-dependency assertions.

Final runtime/static counts and the preserved Mission 22 results are recorded separately in MISSION_23_FINAL_VALIDATION.json. Comparator activation and back audio remain unavailable pending M22-COMP-MAPPING.

## Final execution

All 62 Mission 22 integration/adversarial/recovery cases and 23 new Mission23 cases pass in both the full audit and Profile A. Two fresh guarded demonstrations at `1ab4e71f5f1b98507fb44d7d59b84dec13ee2e96` have identical execution JSON/snapshot manifests; completed-artifact resume performs a full constructed replay and passes with zero policy denials. The complete example and artifact hashes are retained in MISSION_23_DEMONSTRATION_RECEIPT.json.

Run a new demonstration directory locally:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/run_mission22_demo.py --output /tmp/mission23-demo
```

Resume requires the same seed and code identity; a changed Git label is intentionally refused. The selected acceptance profile passes3,091 cases with 118 protected dependencies not executed and 0 unknown. The complete repository audit remains87 failures plus31 setup errors; no full-repository or operational-readiness claim follows.
