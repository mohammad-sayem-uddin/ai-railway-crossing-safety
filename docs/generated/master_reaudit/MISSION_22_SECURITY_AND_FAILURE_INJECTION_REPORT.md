# Mission 22 — Security and failure injection

Prepared 2026-11-05, America/New_York. All listed cases executed and passed in the 62-case integration suite. Parameter labels below describe actual parameter values; see JUnit/test node IDs in the final JSON for exact pytest IDs. Sources: `tests/synthetic_mission22/test_review_service.py`, `test_metric_bridge.py`, `test_workflow.py`, `test_crash_and_adversarial.py`.

This is a focused challenge by the implementing assistant, not an independent third-party assessment. No live service, credentials, source media, checkpoints, caches or real human review was exercised. Tests target real Python validators and actual temporary SQLite/filesystem/process boundaries using constructed principals/resources. They cannot prove OS isolation or independent identity.

| Requested case | Executed test (`test_` prefix omitted) | Expected and actual result | Result / boundary |
|---|---|---|---|
| Invalid principal | `unauthorized_review_never_writes[actor]` | deny before review write | PASS; cooperative constructed validator |
| Wrong role | `missing_scope_wrong_role_replay_and_malformed_receipt` | deny REVIEW when actor has only ISSUER | PASS; cooperative constructed validator |
| Wrong resource identity | `unauthorized_review_never_writes[resource]` | deny before resource/domain mutation | PASS; cooperative constructed validator |
| Wrong purpose | `unauthorized_review_never_writes[purpose]` | deny even when request ID/actor match | PASS; cooperative constructed validator |
| Wrong environment | `unauthorized_review_never_writes[context]` | deny mismatched constructed context | PASS; cooperative constructed validator |
| Expired permission | `unauthorized_review_never_writes[now=10]` | deny at exclusive expiry boundary | PASS; cooperative constructed validator |
| Revoked permission | `revocation_and_atomic_rollback` | deny current use after revocation | PASS; cooperative constructed validator |
| Missing authorization binding | `missing_scope_wrong_role_replay_and_malformed_receipt` | None scope denies; no fallback identity | PASS; cooperative constructed validator |
| Modified source after authorization | `source_version_change_after_authorization_is_not_rebound` | retained registry digest mismatch denies | PASS; cooperative constructed validator |
| Duplicate request | `atomic_result_retry_and_wrong_purpose` | identical retry returns prior result with quota still1 | PASS; cooperative constructed validator |
| Replay attempt | `missing_scope_wrong_role_replay_and_malformed_receipt` | new request cannot reseal an existing first observation | PASS; cooperative constructed validator |
| Malformed receipt | `missing_scope_wrong_role_replay_and_malformed_receipt` | controlled ValueError; no fabricated success | PASS; cooperative constructed validator |
| Stale snapshot | `tampered_completed_artifacts_never_recertified` | artifact digest mismatch denies completion | PASS; cooperative constructed validator |
| Missing lineage parent | `lineage_cv_join_rejects_boundary_tampering[parent]` | deny unresolved exact parent | PASS; cooperative constructed validator |
| Tampered lineage reference | `lineage_cv_join_rejects_boundary_tampering[group/source_hash/fit_exposure]` | deny event/content/transitive-exposure mismatch | PASS; cooperative constructed validator |
| Invalid timestamp | `native_rejections_remain_traceable_at_metric_boundary[invalid]` | incomplete prefix; missing horizon metrics null | PASS; cooperative constructed validator |
| Out-of-order frames | `native_rejections_remain_traceable_at_metric_boundary[out_of_order]` | record rejected input index; no command for it | PASS; cooperative constructed validator |
| Duplicate frames | `native_rejections_remain_traceable_at_metric_boundary[duplicate]` | same-time input rejected; no silent extra actuation | PASS; cooperative constructed validator |
| Missing camera stream | `camera_boundary_failure[missing]` | deny absent back stream; never impute zero | PASS; cooperative constructed validator |
| Camera identity mismatch | `camera_boundary_failure[wrong_camera/wrong_event/fused]` | deny source/event/fusion substitution | PASS; cooperative constructed validator |
| Incomplete simulation horizon | `incomplete_and_tampered_outputs_not_safe` | M5 and non-witness M4 remain null with reasons | PASS; cooperative constructed validator |
| Process interruption | `abrupt_exit_during_shared_transaction_rolls_back` | actual child exit73 rolls back both journals/quota | PASS; actual process + constructed SQLite state |
| Recovery from persisted state | `process_interruption_and_restart` | actual child exit75 at3 cuts; resumed output equals direct output | PASS; actual process + constructed SQLite state |
| Inconsistent configuration | `inconsistent_controller_configuration_denied_before_execution` | mismatched controller settings denied | PASS; cooperative constructed validator |
| Deterministic replay mismatch | `coherent_file_digest_change_still_fails_deterministic_replay` | changed B controller_calls rejected even with updated file digest | PASS; cooperative constructed validator |
| Protected-root snapshot input | `protected_output_path_denied_before_access` | lexical denial before resolution/stat/read | PASS; cooperative constructed validator |

Additional passed cases cover concurrent two-connection first-seal races (one commit/one refusal), stale checkpoint step versus anchor, persisted context/schema substitution, database capacity failure with original SQLite error retained, three metadata symlink substitutions refused before read, completion manifest omission, audio-only inability to issue LOWER or CROSSING_CLEAR, and inactive proposed-schema import fencing.

## Claim classification

Numbers follow the mission's requested classes; they apply only to the stated claim.

| Claim | Class | Evidence and limit |
|---|---|---|
| Review and authorization journal atomicity under abrupt ordinary-process exit | 1 — executed tests | SQLite trigger kills a real child after domain insertion/before authority journal insertion; reopening shows neither journal/quota committed. Not power-loss durability. |
| Concurrent first-seal serialization | 1 — executed tests | Two real connections and synchronized threads: exactly one commit, one refusal. Broader distributed concurrency unverified. |
| Role/purpose/resource/context/time/revocation/fence/quota binding | 2 — constructed only | Mock appointments, mock integer time and local SQLite checks execute before use. No independent issuer/person/environment authentication. |
| Lineage, request, configuration and detached-result integrity | 2 — constructed only | Exact expected digests and deterministic B replay reject tested substitutions. Caller-retained expectations remain a trust assumption. |
| Idempotent retry, prefix recovery and correction immutability | 2 — constructed only | Shared transaction and separately retained local anchor, immutable domain history; coherent replacement of DB plus anchor by their owner is outside this profile. |
| Snapshot path and completion integrity | 3 — partial | Closed-name digest set, lexical protected-root rejection and parent-first symlink refusal tested. Cooperative checks do not prevent hostile TOCTOU replacement. |
| Source-only regression access policy | 3 — partial | Python audit hooks inherited into allowed Python children; protected-path and forbidden-backend attempts denied/logged. Native access bypass is not an OS sandbox. |
| Wall-clock authenticity, real identity, independently protected storage and rollback resistance | 5 — external controls | Caller controls mock time, roles and anchors. Separate trusted infrastructure required for stronger claims. |
| Machine power failure, storage-controller durability, hostile root recovery | 4 — not verified | No power failure or independent recovery infrastructure was exercised. |
| All32 ES/live-service acceptance | 4 — not verified | Relevant local subsets executed; no claim that all live deployment scenarios or external appointments exist. |

The legacy invalidation/evaluation/media guards and strict active record schemas remain in force. No ready/approved bypass flag, live token, human appointment, GT promotion receipt or resource grant was created. Snapshot manifests and fixture authority receipts are explicitly constructed consistency evidence.

The regression-policy child test separately verifies blocked protected reads, checkout writes, external network connections, child Python without inherited policy, and a synthetic backend-profile tripwire. Loopback bind and actual FD-relative temporary-directory cleanup succeed. Scratch Python source scanning is allowed; this does not grant protected corpus access.
