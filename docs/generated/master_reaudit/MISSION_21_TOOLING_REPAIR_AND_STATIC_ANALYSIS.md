# Mission21 — Bounded tooling repair and static analysis

The active runtime is `.venv/bin/python` (Python3.11.15). Initial Mypy execution
failed: `No module named mypy.__main__`. The local 2.3.1 dist-info has only RECORD
and licenses; installed native/source files are partial. `pip show mypy` also
fails because Metadata-Version is absent. The inactive Python3.14 tree is left
unchanged. No global environment is changed.

Repair plan (recorded before mutation): use exact existing requirements.lock
versions mypy2.4.0, mypy_extensions1.1.0, typing_extensions4.16.0, librt0.16.0,
ast_serialize0.13.0. The latter dependency installations have absent metadata
and/or older partial content. pathspec1.1.1 is already intact and is retained.
No dependency specification is changed. Download wheels without dependencies,
stage these five packages in a temporary directory, verify version execution,
quarantine only their old active-runtime namespaces/dist-info and Mypy compiled
support extension, then copy the exact staged package files to the active
site-packages and regenerate the three Mypy CLI wrappers for that interpreter.
Retain a temporary inventory/rollback copy and wheel digests. Do not repair
unrelated packages, use global pip, weaken typing rules or install extra tools.

Focused checks and any remaining diagnostics will be appended after execution.

Staging check revealed pathspec1.1.1 metadata exists but its module is also a
partial namespace (`__file__=None`, missing GitIgnoreSpec). The staged Mypy
import fails at that dependency. Extend the same bounded repair to exact locked
pathspec1.1.1; retain the failed staging receipt and rerun before promotion.

## Executed repair and validation

The six exact locked packages were staged without dependency resolution; Mypy
2.4.0 executed successfully there, then the named active-runtime package trees
were replaced. Previous partial namespaces are retained in
`/tmp/mission21_tooling_rollback`; no Python3.14/global files were changed.
Wheel SHA256 and changed namespace inventory are in the companion repair receipt.
No requirements.lock or pyproject change was required.

Initial analysis found 19 diagnostics in the six new components. Fixed explicit
container/history annotations, variable reuse and command narrowing; no ignores,
rule weakening or dependency upgrades. Metric first-step narrowing is now
explicit after the existing nonempty-replay guard, with unchanged classification.
Mypy now reports **no issues in nine source files**: the six new components,
metrics.py, source snapshot script and descriptive table generator.

Focused tooling tests verify complete locked metadata and that the checker
accepts valid code and rejects a deliberate assignment defect. An initial smoke
test used `-c` against a config with `files=[src]`, which Mypy rejects; changed
the fixture to explicit temporary source files without altering configuration.
All eight tooling cases now pass. Both module and CLI report Mypy2.4.0.

The first broader analysis reported 35 diagnostics in preserved A-runner code,
metric optional narrowing and unavailable legacy docx/pandas typing. The two
metric diagnostics are fixed; the A runner's instrumentation diagnostics and
legacy optional dependency diagnostics remain outside this bounded repair.
Runner edits are restricted by the adopted R02-A to the B delegation entrypoint;
its old A instrumentation and one pre-existing Ruff E501 remain unchanged.
Unneeded docx/pandas packages/stubs are not installed for disabled generators.
This is scoped type acceptance, not a whole-repository typing pass.

Legacy reporting refusal was moved into explicit entrypoint functions so imports
cannot trigger plotting/document writes. Historical template bodies remain
unreachable. Their existing lint was corrected with import ordering, formatting,
AST-equivalent literal wrapping and unused-local naming, without changing fixed
historical value text. All30 changed/new Python files other than the preserved
A runner pass Ruff; all31 parse. The three legacy reporting paths still refuse
before third-party imports/IO in executed negative tests.

Fresh isolated regression: **443 tests, zero failures/errors/skips** across ten
new suites plus the original238 suite in a separate process. Original suite has
five existing record_property/JUnit warnings. Exact phase XML counts/commands
are in the execution register; these are engineering tests, not real-data results.
