# D3 — Descriptive-only versus Official Split

**Status:** `PROPOSED — NOT APPROVED`

| Option | Fit | Risk/consequence |
|---|---|---|
| Preserve official split | Current validator requires exact nonempty disjoint train/val/test; runner evaluates test | Needs genuine event split; current image split has leakage risk |
| Separate descriptive mode | Fits fixed-site descriptive claim; current synthetic aggregator isolated | Requires schema/architecture review; never official test performance |
| Amend official contract | Could represent full cohort in official path | Highest governance/backward-compatibility risk |
| Defer | No unsupported claim | Delays study |

Source: `research_contracts.py:30-70`, `manifest_builder.py:40-128`, `evaluation_runner.py`.
**PROPOSED recommendation:** separate descriptive mode; preserve official validator/runner.
Current implementation is synthetic-only and not an official manifest mode.

**Response:** option __________; permitted claims __________; decision-maker/date __________.
