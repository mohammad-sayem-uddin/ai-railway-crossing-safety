# Stage-2.1 Operational Execution Checklist

**Date:** 2026-11-01  
**Status:** Pre-execution checklist; no item is treated as completed by Mission 4B.

> A software-readiness result is not authorization.

## Gate 0 — Authority and scope

- [ ] Researcher authorizes genuine Stage-2.1 review (`ADJ-AUTH`).
- [ ] Exact event keys/cohorts are named; engine event remains separate.
- [ ] Protocol authority/version is recorded.
- [ ] Evaluation profile, event split, and R04 policy are recorded or explicitly deferred.
- [ ] Threshold, ROI, B7e, and official evaluation decisions are recorded before later claims.

**Researcher approval required:** every item.

## Gate 1 — Reviewer selection

- [ ] Select named, individually attributable human reviewers.
- [ ] Verify identity out of band; no role labels or invented aliases.
- [ ] Confirm independence from model predictions and each other's first-pass decisions.
- [ ] Record conflicts/exclusions.
- [ ] Separately update/approve the authoritative allowlist.
- [ ] Verify no duplicate, blocklisted, revoked, inactive, or synthetic identity.
- [ ] Identify a distinct second reviewer when policy requires it.

**Researcher approval required:** identities, eligibility, independence, allowlist writes.

## Gate 2 — Environment and media access

- [ ] Authorize exact front/back sources.
- [ ] Prevent model outputs, caches, predictions, and evaluation reports from the review environment.
- [ ] Confirm queue/inventory are read-only inputs and proposals are current.
- [ ] Confirm tool version/hash and model firewall.
- [ ] Confirm hash-observation and incident/stop procedure.

**Researcher approval required:** media access, environment, tool release.

## Gate 3 — Reviewer instructions

- [ ] Provide onboarding and signed T0–T4 semantics without mixing protocol versions.
- [ ] Explain four states, camera-local clocks, duration measurement, hashes, rationales, corrections, escalation, second review, and completion versus approval.
- [ ] Prohibit model-output exposure, fabricated values, and timestamp padding.

**Researcher approval required:** final instruction set and protocol handout.

## Gate 4 — Inventory and assignment

- [ ] Run the read-only queue validator.
- [ ] Confirm 27/27, no duplicates/missing events, and 23/3/1 cohorts.
- [ ] Confirm engine isolation and verified legacy notices.
- [ ] Confirm no synthetic queue event.
- [ ] Assign only after reviewer authorization; preserve `NOT_STARTED` until then.
- [ ] Keep the tracker non-authoritative.

**Researcher approval required:** assignments and queue/inventory changes.

## Gate 5 — Real review

- [ ] Reviewer confirms key/cohort/sources before inspection.
- [ ] Record UTC start/session ID and front/back hashes.
- [ ] Review independently of model outputs.
- [ ] Record all six states/rationales, camera-local values/frame evidence where observable, and censoring/uncertainty without fabricated values.
- [ ] Record UTC end and actual duration.
- [ ] Stop on hash/source/model-firewall/tooling incidents.

**Researcher approval required:** start of real review and any production record write.

## Gate 6 — Validation and disagreement

- [ ] Validate schema, authorization, hashes, history, identity, and duplicate-event/session safeguards.
- [ ] Apply the researcher-selected second-review trigger.
- [ ] Use a distinct authorized reviewer.
- [ ] Keep disputes unresolved until human adjudication.
- [ ] Preserve audit logs and correction history.

**Researcher approval required:** trigger, final adjudication, approval status.

## Gate 7 — Promotion/evaluation (separate phase)

- [ ] Obtain explicit promotion authorization.
- [ ] Run mechanical readiness/promotion dry-run first.
- [ ] Confirm legacy exclusion, non-synthetic guard, proposal currency, live hashes, batch integrity, and cohort coverage.
- [ ] Researcher signs ground-truth approval separately.
- [ ] Obtain EVAL-AUTH before cache generation, inference, or official evaluation.
- [ ] Freeze protocol/profile/split/R04/threshold/ROI/B7e decisions before claims.

**Researcher approval required:** every item.

## Stop rule

If any gate is incomplete, stop. Passing synthetic tests or a queue audit does not permit real media review, record creation, approval, promotion, caches, inference, or official evaluation.