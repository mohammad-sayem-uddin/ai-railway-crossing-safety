# DRAFT — NOT APPROVED — NOT AUTHORIZATION

## Stage-2.1 Ground-Truth Preparation Checklist

**Status:** DRAFT — NOT APPROVED — NOT AUTHORIZATION

### Required per active schema `8.1.0-stage2.1`

- [ ] Cohort-qualified event identity.
- [ ] Allowlisted, non-blocklisted human reviewer identity.
- [ ] Review session timestamps and plausible duration (minimum floor currently 30 s; not
      proof of genuine review).
- [ ] Model-independence attestation.
- [ ] Reviewer-observed front/back media hashes.
- [ ] Four-state boundary adjudications: `OBSERVABLE`, `UNOBSERVABLE_NOT_APPLICABLE`,
      `CENSORED`, `UNCERTAIN`.
- [ ] Observable value, reference camera, and frame index where applicable.
- [ ] Nonempty rationale for every boundary.
- [ ] Append-only adjudication history.
- [ ] Approval status attributable to the human workflow.
- [ ] No candidate/proposal fields substituted for approved fields.
- [ ] Duplicate cohort-qualified identities rejected.
- [ ] Promotion-time allowlist, proposal hash, trusted media registry, and live media hash
      checks completed only through the authorized promotion workflow.
- [ ] Stage-2.1 promotion receipt created only after genuine readiness and authorization.

### Cohort coverage

- [ ] `train_events`
- [ ] `no_train_events`
- [ ] `engine_events`

Current verified status: 27 legacy schema-6.0.0 review files exist and are invalidated;
zero active valid Stage-2.1 records are available. Candidate proposals remain non-ground-truth.

Do not edit legacy reviews, promote candidates, or create a promotion receipt from this checklist.
