# Mission 24 — Point-of-use authorization integration

Prepared 2026-11-05, America/New_York. All principals, clocks, grants and resources here are constructed. The 21 conditional and six denied/deferred real operation choices remain unchanged.

`ResourceAccessPort` uses versioned immutable `ResourceUseRequest` and `ResourceUseResponse`. Requests carry actor/session/transaction/fence, READ/PROBE/HASH enum, exact resource/version digest, purpose, context and mock integer time. Typed requests require CONSTRUCTED_SYNTHETIC_INPUT. External/pending inputs, missing bindings, boolean clocks/fences and unknown operations refuse. No model/cache/inference/evaluation path is added.

The adapter delegates to `ConstructedResourceBroker.use`. That existing broker checks current authority, exact immutable resource identity, purpose/environment, expiry/revocation and quota inside its owning SQLite transaction before returning bytes or doing the explicitly named operation. No adapter pre-check is treated as an execution grant. Lineage and source hashes establish consistency, not permission. The existing transaction binds returned payload, ledger entry, request ID and quota atomically. Same-binding retry returns the committed result; conflicting replay refuses.

Review mutations separately pass the typed review facade and original atomic service; their event must match the grant as well as domain roles/history. Reopening a session preserves original durable authorization and review journal context. Facade response tuples are process-local convenience events, not replacement trusted logs. The nested coordinator owns history/anchor recovery.

Executed negatives cover wrong principal/resource/purpose/context, expiry/revocation, wrong fence, clock rollback, changed source/registry digest, duplicated/substituted transaction, and no success/journal/quota record on denied access. Existing security/crash suites independently cover injected persistence failures, concurrency and restart. Completed-artifact verification replays constructed fixtures; it does not certify the current state of a live authority service.

Cooperative local roles/time/anchors and same-user storage remain explicit trust assumptions. No independent identity, genuine appointment, trusted wall clock, tamper-resistant storage, hostile-root recovery, all-ES deployment acceptance or OS isolation is claimed. No live grant, EVAL-AUTH, GT receipt or data right is manufactured.

Final execution: all 11 new typed authorization cases and the existing46-case security suite pass freshly within the 3,282 selected cases. Both complete application demonstrations, full-artifact verification/resume, guarded imports and architecture inspection have zero denied accesses. Expected negative guard tests elsewhere in acceptance are recorded by their actual assertions; this is not a claim of zero audit-policy events across every test.
