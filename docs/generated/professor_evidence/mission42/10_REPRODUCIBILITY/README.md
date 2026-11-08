# Reproducibility and integrity

Reported baseline e82269521c1222fef0826449e18a386a7a58a362 is the Mission40 commit, although the brief labels it Mission41. Actual starting Mission41 HEAD is 268ec537382c591298693b4cf3686b46a40adca8. Both are preserved in BASELINE_AND_PRESERVATION.json; no reset occurred. The containing Mission42 commit anchors this package and is reported after local commit. Tracking origin/main remains fc3c29a761deaa9e36eca1e5eea4e0205b1f9a74; no push.

From the package root:

```sh
python3 10_REPRODUCIBILITY/verify_package.py
```

The standalone standard-library verifier checks complete checksum inventory, manifest payload identities, CSV/JSON/JUnit parseability and adapted reading links. It reads this package only. It performs no raw-data/model/cache access, inference, test execution, network operation or grant issuance. Checksums establish byte integrity relative to the index/commit, not independent source authenticity or empirical correctness. PACKAGE_FILES.sha256 excludes only itself to avoid self-reference; use the delivery commit/index digest as its anchor. EVIDENCE_MANIFEST.csv excludes itself and the checksum index; both are covered/anchored by that index and containing commit.

The manifest identifies originals, derived presentation copies and new Mission42 syntheses. Original source paths are repository-relative documentary references; packaged SHA is checked independently. Every original copy's SHA equals its source SHA. Link-adapted copies are separately hashed and refer to their immutable original. Historical links outside selection are printed as documentary references in reading copies and listed in UNPACKAGED_HISTORICAL_REFERENCES.json. Original documents preserve their original links/bytes; use reading copies for package navigation.

[Saved-output reconciliation](SAVED_OUTPUT_RECONCILIATION.json) independently counts actual original-derived JSONLs with no new inference. [Recorded run environments](RECORDED_RUN_ENVIRONMENTS.json) retains run IDs, recorded Git commits, package versions and actual command where stored. Front/back manifests did not store an actual_command field; exact retained invocation source is included rather than manufacturing a shell transcript. Audio's recorded actual_command, full corrected/initial/retry invocation sources and lossless logs remain included. Original absolute invocation paths are historical and require relocation; these scripts are not automatic reproduction launchers or current grants.

A byte-identical maintained source/config/test snapshot is supplied for inspection. It covers the current selected code closure, not a complete installation or every historical manuscript/registry needed by all tests. requirements.lock and pyproject.toml are dependency references; actual run versions are in original manifests (including Torch 2.13.0, Ultralytics 8.4.121, PyAV 18.1.0 where recorded). No package installation is commissioned. Historical run commits and modified runtime code/hash bindings must be read together; the final snapshot alone is not proof that old revisions had identical code.

Original media, PCM, checkpoint binaries, private runtime caches, credentials, external accounts and absent original human notes are not included. Prior checkpoint/container identities are retained without fresh model/media hashing. The expired operation records document past scope only. Re-execution would need legitimate access to exact assets, compatible environment, actual required reference and current exact operation bindings; simply rerunning old scripts is not admitted reproduction.

- [ACTUAL_RUN_MANIFEST.json](originals/docs/generated/research_results/mission39/ACTUAL_RUN_MANIFEST.json)
- [ACTUAL_BACK_RUN_MANIFEST.json](../04_B0_BACK_RESULTS/originals/docs/generated/research_results/mission39/ACTUAL_BACK_RUN_MANIFEST.json)
- [CORRECTED_AUDIO_RUN_MANIFEST.json](../05_B1_AUDIO_RESULTS/originals/docs/generated/research_results/mission39/audio_followup/CORRECTED_AUDIO_RUN_MANIFEST.json)
- [run_b0_front.py](../03_B0_FRONT_RESULTS/originals/docs/generated/research_results/mission39/invocations/run_b0_front.py)
- [run_b0_back.py](../04_B0_BACK_RESULTS/originals/docs/generated/research_results/mission39/invocations/run_b0_back.py)
- [run_embedded_audio_corrected.py](../05_B1_AUDIO_RESULTS/originals/docs/generated/research_results/mission39/audio_followup/invocations/run_embedded_audio_corrected.py)
- [INTEGRITY_VALIDATION.json](originals/docs/generated/research_results/mission41/INTEGRITY_VALIDATION.json)
