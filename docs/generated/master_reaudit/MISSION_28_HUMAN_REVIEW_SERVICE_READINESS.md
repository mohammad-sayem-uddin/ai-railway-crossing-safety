# Mission 28 human-review service readiness

No genuine deployment was found in the inspected project source/configuration. Existing Mission25/27 interfaces are reused. No cloud identity provider, player, trusted clock, protected store or publisher is invented or connected. No private account was accessed. The existing canonical governance and point-of-use guards remain authoritative.

The complete capability/authentication/authorization/audit/revocation/data-protection/failure/dependency/acceptance assessment is `MISSION_28_HUMAN_REVIEW_SERVICE_REGISTER.json`. All eight rows are MISSING_GENUINE_DEPENDENCY. The two verification rows implement different existing contracts; clock and revocation are deployment dependencies, not new authority systems.

## IDENTITY

Existing: `HumanIdentityProvider.authenticate` in `src/railway_detection/application/evidence_intake/ports.py`. Actual physical-person identity/session, role, qualification and alias resolution.

Trust and authentication: Typed/cooperative software contract versus independently governed actual deployment; no genuine provider accepted. A provider must authenticate physical people; none supplied.

Authorization: Existing canonical scoped grants and current assignments; none supplied. Audit: Authenticated session/physical-principal/assignment audit.

Revocation: Session and assignment revocation at every use. Protection: Actual custodian/provider controls, permitted storage/recipients/retention and protected observation evidence remain unverified.

Failure: Genuine review inactive; deny missing, unverified, expired, revoked or mismatched prerequisites. Missing: Actual provider, people and delegated identity/role authority.

Acceptance needed: Actual provider denies expired/revoked sessions and detects same-person aliases; constructed tests alone do not accept deployment.

## DOCUMENTARY_VERIFICATION

Existing: `DocumentaryVerifier.inspect` in `src/railway_detection/application/evidence_intake/intake.py`. Original issuer/delegation authenticity, exact metadata/scope/stage and current terms.

Trust and authentication: Typed/cooperative software contract versus independently governed actual deployment; no genuine provider accepted. Originals and independent actual verifier must be authenticated; none supplied.

Authorization: Exact source/operation/actor/role/purpose/environment; no grants issued here. Audit: Stage-specific attestation and retained original/source version.

Revocation: Current evidence/issuer revocation and conflicts checked at use. Protection: Actual custodian/provider controls, permitted storage/recipients/retention and protected observation evidence remain unverified.

Failure: Genuine review inactive; deny missing, unverified, expired, revoked or mismatched prerequisites. Missing: Actual original documents and independently governed verifier.

Acceptance needed: Actual verifier refuses forged/expired/revoked/wrong-scope originals and binds independent physical verifier; no genuine positive test available.

## REVIEW_EVIDENCE

Existing: `EvidenceVerifier.verify` in `src/railway_detection/annotation/evidence_review/contracts.py`. Human identity/qualification/independence/participation and human submission attestation.

Trust and authentication: Typed/cooperative software contract versus independently governed actual deployment; no genuine provider accepted. Genuine original human attestations and canonical physical principal; none supplied.

Authorization: Existing Mission25 assignment and canonical point-of-use permission. Audit: Exact reviewer/source/batch/observation and independent parent bindings.

Revocation: Current reviewer/assignment/source access checked at use. Protection: Actual custodian/provider controls, permitted storage/recipients/retention and protected observation evidence remain unverified.

Failure: Genuine review inactive; deny missing, unverified, expired, revoked or mismatched prerequisites. Missing: Actual appointed people, credential evidence and trusted attestation service.

Acceptance needed: Actual human submissions accepted only for exact qualified scope; same-person conflicts and unverified qualifications refuse.

## SOURCE_PRESENTATION

Existing: `BlindSourcePlayer.present` in `src/railway_detection/application/evidence_intake/ports.py`. Neutral blind source presentation with original camera-local PTS.

Trust and authentication: Typed/cooperative software contract versus independently governed actual deployment; no genuine provider accepted. Authenticated actor/session; none supplied.

Authorization: Existing canonical source-operation grant before every use. Audit: Blinding/exposure and exact source/PTS access logs.

Revocation: Stop presentation immediately on current denial/revocation. Protection: Actual custodian/provider controls, permitted storage/recipients/retention and protected observation evidence remain unverified.

Failure: Genuine review inactive; deny missing, unverified, expired, revoked or mismatched prerequisites. Missing: Actually accepted source broker/player plus exact-source permissions.

Acceptance needed: Accepted deployment preserves PTS, hides candidates/prior/model outputs, and stops before unauthorized source access; no media exercised here.

## OBSERVATION_STORAGE

Existing: `HumanObservationStore.commit_human_submission` in `src/railway_detection/application/evidence_intake/ports.py`. Authenticated immutable originals/corrections; atomic canonical review transaction.

Trust and authentication: Typed/cooperative software contract versus independently governed actual deployment; no genuine provider accepted. Authenticated human submission, not an AI-generated judgment.

Authorization: Existing WP03/WP04 authorization, fence and exact retained parent transaction. Audit: Immutable observations, independent review/adjudication parents, externally retained heads and exact retry recovery.

Revocation: Deny new use after current revocation; retain originals. Protection: Actual custodian/provider controls, permitted storage/recipients/retention and protected observation evidence remain unverified.

Failure: Genuine review inactive; deny missing, unverified, expired, revoked or mismatched prerequisites. Missing: Actual protected storage, authentication, anchoring, backups and recovery acceptance.

Acceptance needed: Deployment proves atomic rollback/lost-response recovery, create-only lineage and independent storage governance. Local SQLite is not that proof.

## PUBLICATION_EXPORT

Existing: `CanonicalPublisher.export_verified_batch` in `src/railway_detection/application/evidence_intake/ports.py`. Canonical active-schema complete batch and specifically scoped metadata export.

Trust and authentication: Typed/cooperative software contract versus independently governed actual deployment; no genuine provider accepted. Actual authenticated publisher, human batch and canonical receipt.

Authorization: Existing promotion/export grant with exact recipient/output scope. Audit: Exact batch/history/source/receipt/output audit.

Revocation: Recheck current grants, evidence and revocation at export. Protection: Actual custodian/provider controls, permitted storage/recipients/retention and protected observation evidence remain unverified.

Failure: Genuine review inactive; deny missing, unverified, expired, revoked or mismatched prerequisites. Missing: Actual canonical publisher and release/output authority where relevant.

Acceptance needed: Genuine fixtures are unavailable; deployment must refuse partial/unverified/constructed batches, revoked receipts and wrong recipients.

## TRUSTED_TIME

Existing: `No trusted provider configured; explicit diagnostic now values only` in `src/railway_detection/application/evidence_intake/cli.py`. Trustworthy current validity/expiry and ordering, separate from source-local PTS.

Trust and authentication: Typed/cooperative software contract versus independently governed actual deployment; no genuine provider accepted. A deployment-owned authenticated clock is required; caller JSON/CLI time is not trusted.

Authorization: Canonical authorization service must supply/check its current time. Audit: Clock source/health and actual session wall/monotonic time audit.

Revocation: Fail closed when clock trust/availability is lost. Protection: Actual custodian/provider controls, permitted storage/recipients/retention and protected observation evidence remain unverified.

Failure: Genuine review inactive; deny missing, unverified, expired, revoked or mismatched prerequisites. Missing: Actual trusted time integration and operational acceptance.

Acceptance needed: Actual service detects invalid/untrusted time and enforces exclusive expiry; no scientific duration threshold is introduced.

## REVOCATION_AUDIT

Existing: `Existing canonical guards plus documentary lineage; no independent genuine service` in `src/railway_detection/application/evidence_intake/ports.py`. Current revocation across actor, source, assignment, permission and evidence; external audit anchors.

Trust and authentication: Typed/cooperative software contract versus independently governed actual deployment; no genuine provider accepted. Authenticated authority/revocation issuer and protected retained anchors.

Authorization: Existing canonical governance path only. Audit: Independent retention, recovery and exact source/operation/actor logs.

Revocation: Point-of-use status, explicit fail-closed outages and incident handling. Protection: Actual custodian/provider controls, permitted storage/recipients/retention and protected observation evidence remain unverified.

Failure: Genuine review inactive; deny missing, unverified, expired, revoked or mismatched prerequisites. Missing: Actual authority/revocation/audit deployment service.

Acceptance needed: Actual deployment denies stale authority after revocation and proves protected anchor recovery; Python audit hooks do not prove OS isolation.

Three focused Mission28 repairs preserve the existing journal: initialization refuses a caller-owned active transaction, CLI exact retries retain the latest accepted audit head while returning the original request result, and explicit expiry can record an already evidenced verifier deadline for a no-fixed-expiry document. These are software integrity repairs, not genuine deployment acceptance. No new evidence database, authorization system, human observation or signature is created.
