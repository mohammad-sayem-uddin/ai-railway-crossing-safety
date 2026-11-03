# Mission 11B — Complete Manuscript Claim Ledger

**Audited:** `docs/generated/phase5/PAPER_DRAFT_PHASE5_REVISION.md`, lines 1–201.  
**External literature verification:** not performed; all citation claims requiring external lookup are `UNVERIFIED`.

| ID | Lines | Claim/topic | Evidence checked | Status |
|---|---:|---|---|---|
| CL-001 | 1–16 | Correction notice, failed audits, no authorization/results | Mission 10 recovery/reconciliation; governance directory | SUPPORTED |
| CL-002 | 9–16 | Auditable independent-camera benchmark; results pending | paper header/readiness | PARTIAL (design, not completed benchmark) |
| CL-003 | 13–15 | Baseline, execution agent, date | current workspace; no agent provenance | PARTIAL/UNVERIFIED |
| CL-004 | 16 | No Phase 5 empirical performance numbers | result tables | SUPPORTED |
| CL-005 | 22 | Sensors affordable alternative to track circuits | no cost study/citation | UNVERIFIED |
| CL-006 | 22 | Offline evaluations routinely suffer listed failures | no literature verification | UNVERIFIED |
| CL-007 | 22 | 27-event Bangladesh cohort | inventory | SUPPORTED |
| CL-008 | 22 | M4/M5/MTR contracts | metrics.py/lead_in_screen.py | SUPPORTED |
| CL-009 | 22 | Two-reviewer governance established | second_review.py; GOV policy pending | PARTIAL (proposal, not adopted) |
| CL-010 | 22 | Model-independence firewall | stage2_1_schema.py | SUPPORTED |
| CL-011 | 28 | Highest fatality source; thousands of crossings; prohibitive costs | no cited repository source | UNVERIFIED |
| CL-012 | 31–36 | Replay/censoring/clock/generalization risks | design rationale, no frequency evidence | PARTIAL |
| CL-013 | 42–44 | Research questions and conditional empirical question | paper | SUPPORTED (proposed) |
| CL-014 | 52–62 | Single site, crossing_A, 23/3/1 cohorts, engine isolation | inventory/condition mapping; decisions | SUPPORTED/PARTIAL (authority status) |
| CL-015 | 65 | Qualified IDs and bare-ID rejection | resolve_event_cohort | SUPPORTED |
| CL-016 | 74–82 | Stage-2.1/v7.1.1 landmarks and deferred T2 | proposed protocol/RD-006 | PARTIAL (proposal status) |
| CL-017 | 82 | One-microsecond snapping/strict comparison | timebase/metrics | SUPPORTED |
| CL-018 | 84–88 | RD-043 six triggers/no tolerance/adjudication | second_review.py; policy pending | PARTIAL |
| CL-019 | 96–98 | YOLOv8n, native FPS, audio cadence, 5Hz tick | config supports tick; other claims not independently evidenced | PARTIAL |
| CL-020 | 98 | Decision policy hash | recomputed SHA-256 | SUPPORTED |
| CL-021 | 101 | Audio supporting only/B1 descriptor-only | RD-030/policy | SUPPORTED |
| CL-022 | 104–106 | Camera roles, provisional B0_back, R04 calibration | condition mapping; R04 pending | PARTIAL |
| CL-023 | 113–117 | M4 occupied wording and strict interval | classify_m4 | PARTIAL (wording overstates implementation; interval supported) |
| CL-024 | 120–127 | M5 origin/full coverage and MTR lead-in | metrics/lead-in | SUPPORTED |
| CL-025 | 136–156 | Result tables, negative controls, engine IDs | placeholders/inventory; “shunting” wording unsupported | PARTIAL/PENDING |
| CL-026 | 162–165 | Limitations (censoring, tick, genlock, single site) | config/design docs | SUPPORTED/PARTIAL |
| CL-027 | 173–177 | Claim matrix entries marked VERIFIED | cited sources; focused tests | PARTIAL; “47 tests” not established |
| CL-028 | 178–179 | Empirical outcomes/receipt pending | absent governance files | PENDING |
| CL-029 | 187–191 | Literature citations [1]–[9] statuses | no external lookup; no complete bibliography | UNVERIFIED except explicit unverified labels |
| CL-030 | 197 | Complete implementation verified | Mission 10 says key packages untracked | CONTRADICTED/OVERSTATED |
| CL-031 | 198 | HEAD d4db94d | git rev-parse | SUPPORTED |
| CL-032 | 199 | Exactly 19 modified tracked files | current status: 22 | CONTRADICTED/STALE |
| CL-033 | 200 | Python/torch/Ultralytics/ruff/pytest versions | local environment | SUPPORTED |
| CL-034 | 200 | macOS 26.6.2/Darwin ARM64 | host: Darwin 25.6.0 ARM64 | CONTRADICTED/UNVERIFIED |
| CL-035 | 201 | 1,902 tests passed, no failures | safe runner: 1,802 | CONTRADICTED |
| CL-036 | 201 | No raw-media tests in routine verification | true only for 92-file safe set; 21 protected excluded | PARTIAL |

## Overall classification

Supported level: **proposed methodology + benchmark protocol + engineering implementation description**. Not supported: descriptive empirical study or evaluated real-world system. No performance result should be promoted until authorization, approved ground truth, promotion receipt and evaluation authorization exist.

## Required action items

1. Resolve 1,902 versus 1,802 and 19 versus 22.
2. Remove/qualify “Verified” citation labels until actual publications are checked.
3. Add bibliography, author contribution and AI-use disclosure.
4. Mark RD-043/v9.1.1 as proposed wherever body text implies adoption.
5. Reconcile R04, engine wording/RD attribution, native FPS and reproducibility statements.
6. Treat M-02 and uncovered readers as engineering blockers.