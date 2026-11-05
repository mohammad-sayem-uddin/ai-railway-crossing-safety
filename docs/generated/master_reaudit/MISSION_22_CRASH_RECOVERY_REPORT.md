# Mission 22 — Constructed crash recovery

Prepared 2026-11-05, America/New_York. Actual execution: dedicated temporary directories; 62-case integration suite includes these persistence cases. No production cache or protected research data was opened.

| Failure/completion boundary | Executed behavior | Acceptance |
|---|---|---|
| Normal completion and duplicate read-only resume | Closed nine-artifact manifest written last; full B replay and metric/lineage checks on resume; fresh and resumed public JSON identical. | PASS |
| Controlled child interruption after initialization, committed review before ACK, and after review | Three CLI child processes return75 without COMPLETE; restart with same exact binding completes and equals uninterrupted result. | PASS |
| Abrupt child exit during shared SQLite transaction | SQLite trigger invokes os._exit(73) between domain and authority insertion; both journals and quota remain uncommitted on reopen; same request then succeeds. | PASS |
| Exact repeated request / lost response | Same binding returns prior result without second quota charge; next committed review can be reconciled only from retained prior anchor and matching authority transaction. | PASS |
| Conflicting concurrent first seals | Two connections begin simultaneously; one commits and one refuses. Domain and authority journal counts remain1. | PASS |
| Partial .pending write | Existing partial file refuses overwrite/certification; explicit quarantine error. | PASS — fail closed, manual inspection required |
| Incomplete snapshot | Existing destination without SOURCE_MANIFEST completion marker refuses completion. | PASS — fail closed, no automatic deletion |
| Corrupt or missing acknowledged database | SQLite corruption or missing acknowledged state refuses restart; no replacement history is manufactured. | PASS — fail closed |
| Older versioned schema / changed context | Strict service version and replay context mismatch refuse; no silent migration or reset of nonempty history. | PASS — fail closed |
| Missing lineage parent / changed source or producer configuration | Exact retained manifest/request joins refuse before successful downstream output. | PASS — fail closed |
| ACK step incompatible with journal anchor | Refuses skipped-prefix checkpoint; no COMPLETE written. | PASS |
| SQLite capacity exhaustion | PRAGMA max_page_count forces actual SQLITE_FULL; original error survives SQLite auto-rollback, transaction closes, no partial capacity row. | PASS |
| Changed completed output with coherently updated file hash | Deterministic B replay still rejects modified controller output. | PASS |
| RUN/DB/snapshot symlink substitution | Parent-first named metadata check refuses before read/connect. | PASS — local check only |

A real host low-space condition also exposed that unconditional ROLLBACK could mask the original SQLITE_FULL error after SQLite had already rolled back. Authority and standalone review transactions now check in_transaction and preserve the original exception; rollback failure is an exception note. A deterministic capacity test retains this regression.

RUN.json is immutable input binding; ACK.json records only acknowledged review prefix. The DB transaction commits domain history, authority transaction, journal and quota together. The in-memory review anchor advances only after commit. Resume may reconcile the exact next committed transaction from its historical binding; it never accepts an arbitrary current head merely because it exists. Snapshot/report writes use exclusive pending files, file fsync and rename; COMPLETE is written last. All are local cooperative records.

Malformed/partial files are rejected and preserved, not automatically repaired or erased. The CLI returns2 on refused/corrupt state and75 on deliberate interruption. A completed-artifact resume verifies retained artifacts; it is not a claim of a live database health audit.

File fsync and ordinary process tests do not establish parent-directory fsync/power-loss durability, storage-controller behavior, independent backup, root-compromise recovery or resistance to coherent DB-and-anchor replacement. Those remain unverified. Host free disk was approximately306MiB during validation; the runner deletes only its own per-group generated fixtures after retaining receipts. It does not delete researcher work or prior rollback material.
