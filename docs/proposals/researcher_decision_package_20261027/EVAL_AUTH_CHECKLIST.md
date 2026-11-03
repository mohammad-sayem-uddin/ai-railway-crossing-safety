# DRAFT — NOT APPROVED — NOT AUTHORIZATION

## EVAL-AUTH Checklist

**Status:** DRAFT — NOT APPROVED — NOT AUTHORIZATION
**Authoritative path:** `data/governance/eval_authorization.json` (do not create from this draft)

Before a genuine authorization can be verified by `governance.verify_eval_authorization()`:

- [ ] Protocol decision/profile exists and is bound.
- [ ] Event split decision exists and is valid.
- [ ] R04 scope decision exists and is valid.
- [ ] Stage-2.1 promotion receipt exists and is valid.
- [ ] Phase 12 input manifest exists, is real-classified, and is hash-bound.
- [ ] Frozen config hash is live and verified.
- [ ] Decision-policy hash is live and verified.
- [ ] Input-manifest hash is live and verified.
- [ ] Protocol-profile hash is live and verified.
- [ ] R04-scope hash is live and verified.
- [ ] Split-decision hash is live and verified.
- [ ] Promotion-receipt hash is live and verified.
- [ ] `authorized_by` is on the maintained authority allowlist.
- [ ] Authorization scope operation is exactly `phase12_official_evaluation`.
- [ ] `field_or_physical_operations_authorized` is exactly `false`.
- [ ] Attestation is `RECORDED_RESEARCHER_STATEMENT` with `signature: null`.
- [ ] Record digest is self-consistent.
- [ ] Stage matches the valid promotion receipt.

`data/governance/leg_exec_authorization.json` is not an EVAL-AUTH substitute. Chat statements
and documents are not machine-verifiable authorization records. Do not create placeholder
hashes, signatures, or approvals.
