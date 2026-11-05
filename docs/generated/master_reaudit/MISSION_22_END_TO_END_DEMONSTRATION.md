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

Final regression/security/crash counts and readiness levels will be filled from
actual execution in the final validation packet. No historical Mission21 pass
is counted as a newly executed Mission22 test.
