# Mission22 — Reproducible constructed demonstration

Prepared 2026-11-05, America/New_York. From the repository checkout, using the
existing virtual environment (no model, corpus, checkpoint or optional training
backend is required):

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/run_mission22_demo.py --output /tmp/mission22-constructed-demo
```

Choose a new output directory. The command uses the current Git commit as a code
label, deterministic seed22, the fixed crossing_A identifier and explicit
`CONSTRUCTED_EVENT_NOT_V2_OBSERVATION` labeling. It does not open project data,
models/caches or produce genuine human observations, GT promotion or release.
Code labels/digests are cooperative consistency bindings, not authentication.

Outputs include:

- `RUN.json`: immutable constructed event/source/config/lineage/CV bindings.
- `constructed.sqlite`: mock grant/authority and review journals; no real tokens.
- `ACK.json`: local constructed recovery checkpoint, not an independent trust root.
- `execution.json`: separate native B logical/applied/physical timelines, B
  sampled metric contracts, separately labeled A receipts, lineage/CV joins,
  mock review and non-promotable boundary projection.
- `results_absent_report.md`: empirical results remain UNAVAILABLE.
- `source_fixture` and `snapshot`: explicit source/docs-only reproducibility
  input and the WP08 deterministic snapshot completion manifest.
- `COMPLETE.json`: closed artifact name/digest list written last.

Two independently generated destinations have identical semantic output and
snapshot manifests when source version and seed are unchanged. Raw SQLite file
bytes are not used as a deterministic artifact or cryptographic authority.

For exact same-run recovery or read-only verification of completed artifacts:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/run_mission22_demo.py --output /tmp/mission22-constructed-demo --resume
```

A changed seed/source/config/schema is refused, not silently migrated. A
controlled test interruption can be requested with `--interrupt-after review_commit`;
exit75 means incomplete, not success. Resume reconciles the exact next committed
review result against the retained prefix. Torn metadata or incomplete snapshots
are quarantined rather than certified complete. Machine/root-compromise
recovery and an independent identity/clock service are not established.

Focused integration tests:

```sh
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest --confcutdir=tests/synthetic_mission22 -p no:cacheprovider --import-mode=importlib tests/synthetic_mission22 -q
```

Complete repository inventory under the constructed-only regression policy:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/run_mission22_regression.py --output /tmp/mission22-full-regression
```

Use a new external output directory. Each synthetic suite runs in its own
process. The remaining test modules run in explicit batches with a temporary
experiment registry fixture; the root conftest's real registry read is omitted.
No test module is excluded. The inherited Python audit policy blocks project
research data and native training backends; it permits source/runtime access,
constructed temporary files and local loopback tests. This is not an OS sandbox.
All commands, JUnit cases and denied attempts are retained in regression.json;
per-group generated test fixtures are removed after their receipts are retained.
Exit1 means at least one failure/error, including denied protected-data attempts.
Those cases are never counted as passing or skipped. Final exact counts and
limitations are in MISSION_22_FINAL_VALIDATION.json.


Executed final verification at implementation commit
`77e78eeb1e81bfa2d96e8725de9ea0d34585fe9f`: two independent destinations and a
completed resume exited 0 under the inherited access policy, with byte-identical
execution JSON/snapshot manifests and zero denied accesses. The committed
MISSION_22_DEMONSTRATION_RECEIPT.json retains the explicitly constructed example.
All 62 new integration cases pass. The complete 146-module regression produced
3,043 passes, 112 failures and 31 setup errors across 3,186 cases, with zero skips;
its remaining blocked-resource cases do not establish operational readiness.
