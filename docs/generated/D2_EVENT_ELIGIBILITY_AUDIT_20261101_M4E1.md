# D2 Event Eligibility Audit

**Status:** Metadata-only; no media inspection and no eligibility approvals.

## Inventory

| Cohort | Count |
|---|---:|
| Train | 23 |
| No-train | 3 |
| Engine | 1 |
| Total | 27 |

## Evidence available without media

- Review inventory: all 27 `NOT_STARTED`, no assigned reviewer, no Stage-2.1 review file.
- Queue: all 27 `INVALID` due to invalidated legacy records; no active valid Stage-2.1 records.
- Candidate R04 metadata: 12 CALIBRATION_SUPPORTED, 7 PROVISIONAL, 8 AMBIGUOUS.
- Candidate proposals contain T4 fields, but those are unapproved proposal evidence and cannot establish M4 eligibility.

## Eligibility classification

| Category | Count | Basis |
|---|---:|---|
| Confirmed eligible for M4 | 0 | No approved Stage-2.1 records exist |
| Confirmed ineligible | 1 | Engine event is isolated from train metrics |
| Missing start boundary | 23 | First-blocked is replay-derived; no replay executed |
| Missing approved T4 | 27 | No genuine approved records |
| Censored | Unknown | Requires human review; proposal values are not accepted |
| Uncertain | Unknown | Requires human review; proposal flags are not labels |
| Unknown due to absent evidence | 27 | Review/promotion not complete |

The commonly cited 20/23 T0 left-censoring figure does **not** determine M4 eligibility. M4 does not require T0 or T1; it requires replay-derived first-blocked and approved observable T4.

## Event-specific rules

- Train events: potentially eligible after approved review, observable T4, and replay protection.
- No-train events: not M4 train-event denominator; false-alarm path.
- Engine event: excluded from train M4 denominator by current metrics code.

## Conclusion

No real event can currently be declared M4-eligible. A future eligibility table must be rebuilt after genuine Stage-2.1 review, promotion, profile binding, and authorized replay.