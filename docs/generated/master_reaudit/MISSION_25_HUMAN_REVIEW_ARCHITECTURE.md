# Mission 25 — Human-review and evidence governance architecture

Prepared 2026-11-05, America/New_York. Baseline `053c31e410c5e24679a8605388c1d586138a0a91` matches local, tracking and live main. Exact historical and seven pre-existing work hashes are in MISSION_25_EXECUTION_REGISTER.json.

The review lifecycle is a metadata domain with a separate authenticated evidence-verification port. The default genuine port is disabled. Constructed execution is always labeled CONSTRUCTED_REVIEW_FIXTURE and never satisfies promotion. Existing promotion validators and the inactive comparator remain intact.

| Stage | Input → output/state | Refusal |
|---|---|---|
| Batch / eligibility | Versioned protocol, schema, event/source bindings → immutable batch | Missing identity, duplicate/excluded event or incompatible roles |
| Identity / qualification | Reviewer, qualification and scoped grant references → current assignment | Missing, expired, revoked, conflicted, unverified evidence |
| Session | Assignment + exact batch digest → blind session | Wrong actor/event/source/version |
| Observation / correction | Exact local PTS, uncertainty, censoring and prior digest → append-only record | Invalid clock, acoustic shift, missing physical entry, overwrite |
| Completion / second review | Complete boundary set + explicit risk assessment → comparison requirements | Missing boundaries/risks or same-person second review |
| Disagreement / adjudication | Immutable contributing observations → separate human-submission contract | Automatic averaging, missing authority/reason/parents |
| Batch validation | All event states and lineage → precise readiness reasons | Missing source/schema/human/independence/provenance evidence |
| Promotion readiness | Verified complete batch → pending authorization | Fixtures always non-promotable |
| Receipt validation / publication | External exact-batch receipt + current permission + verified binding → immutable publication interface | Disabled live issuer, expired/revoked/scope/tamper/duplicate substitution |

WP03 remains the constructed observation backend; WP04 provides cooperative point-of-use transactions. New metadata history must preserve exact parents and retained journal anchors. WP02/WP07 join source/physical-event/exposure lineage; WP08 snapshots explicit source/docs only; WP09 reports unavailable empirical results. No protected resource loader is introduced.

The active 8.1 schema has a historical duration check while RD046 retains a deferred floor. Mission25 introduces no numeric floor and does not weaken that validator. Canonical-schema acceptance and final protocol/boundary adoption remain explicit integration prerequisites for genuine promotion.

Real-review UI requires an authenticated session provider, authoritative qualification/role verifier, source-access broker, neutral player, human submission attestation, independent-review controls and canonical publisher. Until connected and accepted, the CLI supports metadata and explicit constructed demonstrations only.

Implemented stage contracts:

| Stage | Concrete input → output / transition | Failure behavior |
|---|---|---|
| 1 Batch definition | REVIEW_GOVERNANCE/1 Batch → validated immutable batch identity | Unknown schema, mutable nested metadata, duplicate requirements or missing provenance refuse. |
| 2 Event eligibility | Batch.events + Source bindings → individual documentary TRAIN/CONTROL/CASE eligibility | Unknown/excluded event, wrong role or missing per-event source refuses; candidate inventory is not signed off. |
| 3 Source identity | Source + external EvidenceVerifier → exact source identity assertion | Missing authenticated source evidence stays a readiness reason; no raw bytes are opened. |
| 4 Assignment | Assignment + Reviewer + Permission → append ASSIGNMENT record | Missing qualification, conflicts, scope mismatch and substituted/duplicate IDs refuse. |
| 5 Authorization | Permission + current actor/batch/event/operation/time → scoped use | Invalid interval, revocation or scope refuses before a write; durable fixtures also check WP04. |
| 6 Session | Assignment ID + current permission → deterministic BLIND_SESSION | Missing assignment, changed permission or expired role refuses. |
| 7 Observation | BoundaryObservation + session/source contract → immutable BLIND_OBSERVATION | Invalid PTS, source/boundary/version, landmark, shift or attribution refuses. |
| 8 Completion | Full assigned source/boundary set + six risk assessments → REVIEW_COMPLETION | Incomplete boundaries or omitted risk subjects refuse. |
| 9 Second-review requirement | Completions + explicit/derived risks → required_second_review and reasons | Caller false flags cannot suppress uncertainty/correction/engine risks. |
| 10 Disagreement | Exact latest independent observations → UNCERTAIN contributor sets | No averaging, cross-camera time shift or inferred tolerance; originals retained. |
| 11 Adjudication preparation | Comparison source/boundary/contributor digest set → submission-ready contract | Missing or changed contributors cannot be silently substituted. |
| 12 Human adjudication | Qualified separate assignment, Adjudication, permission and human evidence → separate versioned record | Automatic resolution, missing reasons/parents, self-adjudication or unverified genuine statements refuse. |
| 13 Batch validation | All event completions, current roles/permissions, resolutions and provenance → Readiness.event_reasons | Exact missing prerequisites remain explicit; corrections invalidate prior contributor bindings. |
| 14 Promotion eligibility | Complete metadata + authenticated adoption/schema/history/source/human/lineage/signoff evidence → pending authorization | Fixture always CONSTRUCTED_NON_PROMOTABLE; genuine adapters absent. |
| 15 Receipt validation | External PromotionReceipt + exact complete object + current promotion permission → authenticated receipt status | Fixture, expiry/revocation, wrong issuer/digest or duplicate substitution refuses; no receipt issuance. |
| 16 Immutable publication | Constructed dashboard/lineage/report + exact snapshot → exclusive files and REVIEW_COMPLETE manifest | Existing destination, missing/unknown/pending/aliased/tampered artifact refuses. Live publication remains disabled and requires the authenticated external service. |

`ConstructedGovernanceJournal` durably exercises assignment/session/observation/completion/adjudication contracts against the same WP04 SQLite transaction, with retained-prefix replay and current-use authorization. It never persists genuine records. `ReviewLifecycle` supplies the metadata domain and external verification port; the default configuration cannot admit genuine submissions. The fixture dashboard is an administrative inspection surface. A genuine blinding-aware view adapter, live journal/player and canonical publisher require separate integration acceptance before real review.
