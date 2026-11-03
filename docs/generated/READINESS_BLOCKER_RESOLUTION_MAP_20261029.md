# Readiness Blocker Resolution Map — 2026-10-29

| Blocker | Required artifact/evidence | Owner | Dependency | Safe now |
|---|---|---|---|---|
| Stage21 records/cohorts | valid `8.1.0-stage2.1` human reviews + receipt | researcher/human reviewer | D1/GT scope | checklist/queue |
| EVAL_AUTH | `eval_authorization.json` bound to 7 hashes | researcher | all upstream | schema checklist |
| Event split | `phase12-event-split-decision/1` | researcher | D1/D3 | validator review |
| Manifest | derived `phase12-evaluation-inputs/1` | engineering | split/R04/approved payloads | builder inspection |
| Premature profile | protocol decision choice | researcher | D1/D2 | compare options |
| R04 scope | `phase12-r04-scope-decision/1` | researcher | D1/D4/calibration evidence | evidence map |
| Cache production | approved eligibility + frozen provenance | authorized engineering | GT/split/R04 | deferred runbook |

Current gate: `ready=False`, 9 blockers. No artifact should be manufactured to reduce count.
