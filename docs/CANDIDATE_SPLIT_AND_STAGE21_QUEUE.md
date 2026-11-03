# Candidate Event Split and Stage-2.1 Review Queue

`src/railway_detection/annotation/candidate_split_queue.py` and
`scripts/build_candidate_split_and_review_queue.py` provide a read-only,
deterministic planning boundary for the event corpus. They do **not** approve
a split, approve a review, invalidate a record, or create a ground-truth
label.

## Reports

Run from the repository root:

```bash
python3 scripts/build_candidate_split_and_review_queue.py
```

The command writes only the two reports under `docs/generated/` (or explicit
paths supplied by `--split-output` and `--queue-output`):

* `CANDIDATE_EVENT_SPLIT_PROPOSAL.json` — event-level candidate partitions,
  active proposal versions and hashes, and grouping/leakage diagnostics.
* `STAGE21_REVIEW_QUEUE.json` — one cohort-qualified queue item per event,
  classified as `MISSING`, `INVALID`, `CONFLICT`, `INCOMPLETE`, or `COMPLETE`.
  Version 2 also carries every Stage-2.1 required field, event-specific source
  media paths/hashes, candidate-only boundary status/rationale, workflow
  prerequisites, and concrete human actions. These are review aids, not labels.
* An optional Markdown rendering of the queue can be requested with
  `--queue-markdown-output <path>`; its content is deterministic and carries the
  same candidate-only warnings.

Version 4 candidate splits retain independent crossing and session leakage
checks, including every spanning group and its events by role. The union
`grouping.events_missing_any_group_metadata` lists events missing either
identifier; per-field results show which identifier is absent. A one-site,
one-session corpus necessarily spans any nonempty multi-role event split, so
these ratios are not a leakage-safe execution decision; the researcher must
decide whether the study design can justify an event assignment at all.

Both reports carry `status: CANDIDATE_ONLY` and
`approval_status: NOT_APPROVED`. `event_key` is always
`<cohort>/<event_id>`; a bare `event_id` is not a valid identity because
`event_001` occurs in all three cohorts.

## Split semantics

Event keys are ordered by SHA-256 of their cohort-qualified identity, then
assigned to deterministic train/validation/test buckets using the requested
ratios (default `0.6/0.2/0.2`). Candidate proposal metadata is read only to
report `crossing_id` and `recording_session_id` grouping independently. The
version-2 report names all groups spanning roles and lists their events by role;
missing group metadata or overlap makes the candidate ineligible as a
leakage-safe execution decision. The tool does not invent a group, move a
record, or silently fall back to a frame-level split. A researcher must decide
how to proceed when this corpus has only one crossing/session group.

## Queue semantics

The queue reads the independent Layer-B inventory, the highest-numbered active
candidate proposal, the expected cohort-qualified review path, and any
invalidation notice. Source bytes are hashed as read. Legacy records, invalid
notices, stale proposal references, unresolved adjudications, rejected records,
identity mismatches, and malformed Stage-2.1 records are surfaced as queue
reasons. Verified invalidation notices keep the legacy record unusable; the
queue never edits or removes that record. Candidate proposal timestamp values
are never copied into a Stage-2.1 review record.

The report can therefore be regenerated and compared byte-for-byte without a
clock or random seed. A `COMPLETE` item means
the report's structural checks found no queue blocker; it is not an approval or
an evaluation authorization.

Focused synthetic coverage is in `tests/test_candidate_split_queue.py`.
