# Mission 24 — Application persistence and recovery

Prepared 2026-11-05, America/New_York. Persistence is exercised only in temporary constructed directories and SQLite databases.

There are two deliberate completion layers. The existing workflow owns its immutable RUN binding, acknowledged review prefix, SQLite domain/authority transaction and closed nine-artifact manifest. The application owns APPLICATION_REQUEST.json, APPLICATION.json and APPLICATION_COMPLETE.json, whose exact set includes the nested workflow completion digest. No ledger or observation store is duplicated.

Application request/version/event/config mismatch refuses resume. Named metadata aliases and pending writes refuse before reads/certification. A completion marker cannot omit an artifact or certify a missing workflow parent. Full verification reuses the existing deterministic core replay and regenerates the typed application receipt; coherently updating a file digest does not allow altered review/construction or comparator state. No normal resume silently discards corrupt state, resets history or migrates unsupported schema.

Five actual child CLI interruption points are tested: coordinator initialization, review commit before ACK, completed review, nested workflow completion and application receipt before outer completion. Each returns75 without outer COMPLETE; a new process resumes to the same bytes as direct execution. Existing committed work is idempotent. A newly reopened adapter does not own a second DB transaction; original BEGIN/COMMIT/rollback ownership remains unchanged.

Additional application tests corrupt the acknowledged DB, remove the checkpoint parent, change persisted service version, alter outer request schema, substitute application/core output, shrink completion schema, introduce pending metadata or replace an artifact with a symlink. All refuse certification. The original Mission22/23 tests retain abrupt-process rollback, lost-response recovery, SQLITE_FULL, exact retained anchors, concurrency, missing lineage parents and full-public-artifact substitution checks.

A failed outer write may leave a valid nested workflow and a partial outer directory. Exact resume can finish only compatible state; malformed/pending content is quarantined for inspection. No old user artifacts are deleted or overwritten. Verification creates separate constructed temporary replay state and cleans only that owned temporary tree.

These are ordinary process/SQLite/filesystem guarantees within a cooperative profile. File fsync/rename and process-exit tests do not establish power-loss/storage-controller durability, independent backup/anchor trust, hostile concurrent path replacement or root-compromise recovery. Protected caches/databases and physical railway hardware are never accessed.
