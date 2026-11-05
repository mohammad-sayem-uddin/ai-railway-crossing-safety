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
