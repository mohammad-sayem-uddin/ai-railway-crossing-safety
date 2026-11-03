# RD-001 … RD-055 Implementation Matrix

> **State vocabulary.** **IMPLEMENTED** = code/test change made in this mission. **PROPOSED** = document or inactive module only. **RECORDED** = scope statement honored; no artifact needed. **DEFERRED** = intentionally not done (see blocker register). **PROHIBITED** = honored restriction. "Formal approval pending" means the researcher's own governance artifact does not exist — the confirmed RD answer is *direction*, not that artifact.
> Document abbreviations (all in `docs/generated/mission_5a/` unless stated): **PR** protocol reconciliation report · **P9** `…v9.1.0_PROPOSED.md` · **P7** `…v7.1.0_PROPOSED.md` · **MC** M4/M5 production correction · **LS** lead-in screen · **SS** schema & review-governance proposal · **ED** experiment-design reconciliation · **PP** paper proposal · **GD** governance drafts · **RT** ratification draft · **BR** blocker register · **SN** snapshot proposal.

| RD | Confirmed answer | Artifact | Required change | Depends on | Status | Impl. complete? | Formal approval pending? |
|---|---|---|---|---|---|---|---|
| 001 | v7 boundaries, v9 system/metrics, design doc non-binding | PR §2; P9/P7 | authority statement | — | PROPOSED | yes (docs) | yes (D1) |
| 002 | wording before D1 hash binding | P9, P7, diffs; PR §1; GD-1 | proposed files; do not bind current bytes | 004–008 | PROPOSED | yes (docs) | yes |
| 003 | Git + hashed snapshot; researcher commits | manifest + SN + tool script | manifest/snapshot plan | — | PROPOSED | yes (plan) | researcher action |
| 004 | T1 = approach/frog line | P9 §5.1/§5.4; P7 §2.1/§2.4 | reword | — | PROPOSED | yes | yes |
| 005 | T2 = leading end crosses physical entry boundary; lens-plane not auto-valid | P9/P7; annotator guard (code) | reword; guard v6 generator | 006 | PROPOSED + IMPLEMENTED (guard) | yes | yes |
| 006 | entry landmark DEFERRED | BR-01; P9/P7 marked DEFERRED | none invented | researcher/auth. step | DEFERRED | n/a | — |
| 007 | `T_OCC_START` alias only after 005+006 | P9 §5.1; PR §4 | prose alias, no field | 005, 006 | PROPOSED | yes | — |
| 008 | replace T1-based POR text with M4/M5 | P9 §5.2/INV-3/§18; P7 §2.2 | replaced; old text historical | 014 | PROPOSED | yes | yes |
| 009 | GOV-/EXP-/AUTH- ids; no ambiguous D3/D-n | PR §4; register aliases (code) | alias entries added | — | PROPOSED + IMPLEMENTED (aliases) | yes | — |
| 010 | direction verified per event at future review | SS (direction field); P7 4a | field in proposed schema | review auth. | PROPOSED / DEFERRED | schema only | review pending |
| 011 | exclude censored from point estimates; count reasons; bounds exploratory | P9 §5.6; code (existing exclusions + new M4 reasons) | counts by reason | — | IMPLEMENTED (M4 reasons) | yes | — |
| 012 | new proposed schema; tolerance DEFERRED | `stage2_1_schema_proposed.py`; SS | inactive module | — | PROPOSED | yes | yes |
| 013 | blind first pass in pilot | SS; schema flag | procedure + flag | pilot auth. | PROPOSED | yes | pilot auth. |
| 014 | M4 selected | GD-2; code window (existing) | none | — | RECORDED | yes | yes (D2) |
| 015 | back-stream primary M4/M5; fused exploratory | P9 §5.5; ED §3 | documented | 026,028 | PROPOSED | yes | yes |
| 016 | corrected 6-case classification in production | `metrics.py`; MC; tests | **code change** | — | IMPLEMENTED | yes | contract approval pending |
| 017 | M5 counts only | code (counts only; no rate); P9 §5.6 | none new | — | IMPLEMENTED | yes | yes |
| 018 | full occupancy duration DEFERRED | BR-03; P9 §5.6 | nothing reported | 005–007, R04 | DEFERRED | n/a | — |
| 019 | per-event, median, range when data exist | PP/ED note | nothing implemented | 018 | DEFERRED | n/a | — |
| 020 | adopt classification; implement only M4/M5 + support | P9 §5.6; ED §1 | no M1–M10 build | — | IMPLEMENTED (scoped) | yes | yes |
| 021 | insufficient-lead-in screen | `lead_in_screen.py`; `evaluate_run`; LS | **code change** | — | IMPLEMENTED | yes (not wired to runner) | — |
| 022 | M4 primary, M5 companion, MTR secondary | P9 §5.6/§18 | documented | — | PROPOSED | yes | yes |
| 023 | descriptive statistics only | P9 §19 (inferential text removed); ED | removed from proposal; code computes no p-values | — | PROPOSED | yes | yes |
| 024 | engine excluded from pooled M4/M5/occupancy/train | code (existing + fail-closed identity); tests | tests added | — | IMPLEMENTED | yes | ratification pending |
| 025 | no-train: event-level + exposure; no train-free claim | P9 §11 unchanged; BR-04 | none | human confirmation | DEFERRED (confirmation) | n/a | — |
| 026 | keep 11-event exploratory; no official dual scope; no silent event_010 | GD-6 | no artifact changed | — | RECORDED | yes | yes (D4) |
| 027 | offsets never shift GT | P9 §5.5 | stated | — | PROPOSED | yes | — |
| 028 | independent primary; fused secondary; 20/23 not claimed | P9 §5.5 | stated | — | PROPOSED | yes | — |
| 029 | freeze `decision_policy_v1`; document limits | ED §2 | no config change | — | RECORDED | yes | — |
| 030 | audio supporting only | ED §2 | stated (code already supporting-only) | — | RECORDED | yes | — |
| 031 | 2-tick confirm, 2-miss, no EMA | ED §2 | none | — | RECORDED | yes | — |
| 032 | constants exploratory only | ED §2; GD-8 | none | — | RECORDED | yes | yes (thresholds) |
| 033 | no ROI-dependent official analysis | ED §2; GD-8 | none | — | RECORDED | yes | yes (ROI) |
| 034 | B7e numerics DEFERRED | GD-9; BR-06 | none invented | researcher values | DEFERRED | n/a | yes |
| 035 | paper B0–B2 + back-stream conditions (design only) | ED §3 | proposal | — | PROPOSED | yes | — |
| 036 | historical results diagnostic only | ED §3 | stated | — | RECORDED | yes | — |
| 037 | no additional recordings | ED §3; PP §4 | documented limitation | — | RECORDED | yes | — |
| 038 | fault injection separate | ED §3 | stated | — | RECORDED | yes | — |
| 039 | descriptive full cohort; real-data pathway needs approval | ED §3; GD-4; BR-09 | none built | governance | DEFERRED (pathway) | n/a | yes |
| 040 | per-metric denominators; explicit reasons | code aggregation (existing + new reason counts) | counts | — | IMPLEMENTED | yes | — |
| 041 | inventory 27 = 23+3+1; engine = one event, 3 versions | PR §5 (TF-22) | documented | — | RECORDED | yes | inventory sign-off pending |
| 042 | external audit reviewer if appointable; allowlist unchanged | SS; GD-7 | no identity | identity | PROPOSED / DEFERRED | n/a | yes |
| 043 | risk-based mandatory triggers | SS; register `GOV-REVIEW-SECOND-REVIEW-TRIGGERS` (PENDING) | proposal | 042 | PROPOSED | yes | yes |
| 044 | risk-based audit; no fixed % | SS; register entry (PENDING) | proposal | 042 | PROPOSED | yes | yes |
| 045 | researcher adjudicates via separate entry; unresolved UNCERTAIN; never overwrite | schema + tests | encoded | — | PROPOSED (schema) | yes | — |
| 046 | duration floor deferred | BR-08 | none | pilot timings | DEFERRED | n/a | — |
| 047 | hard-case pilot proposal | SS §3 | proposal only | many | PROPOSED | yes | pilot auth. |
| 048 | prioritize T1–T4; horn only if reported | SS | stated | — | PROPOSED | yes | — |
| 049 | ratification draft, marked DRAFT | RT | draft | researcher | PROPOSED | yes | **yes** |
| 050 | media access prohibited | — | none | future mission | PROHIBITED | honored | auth. pending |
| 051 | descriptive-benchmark RQs | PP §2 | proposed | — | PROPOSED | yes | — |
| 052 | reframe to independent-camera | PP §1 | proposed | — | PROPOSED | yes | — |
| 053 | claims limited | PP §3 | proposed | — | PROPOSED | yes | — |
| 054 | human authors only; AI disclosure draft | PP §4–5 | proposed | researcher supplies names | PROPOSED | yes | — |
| 055 | venue undecided; future release plan | PP §6 | plan only | privacy review | PROPOSED | yes | — |

**Totals (55 rows, mutually exclusive primary status):** code/tests IMPLEMENTED only — 7 (011, 016, 017, 020, 021, 024, 040); PROPOSED (documents or inactive module; includes 005 and 009 which also carry a small code change, and 010/042 which are also partly deferred) — 29; RECORDED (scope honored, no artifact needed) — 11; DEFERRED — 7 (006, 018, 019, 025, 034, 039, 046); PROHIBITED — 1 (050). **Formal approval is still pending for every decision that requires a governance artifact; the confirmed RD answers are researcher direction, not those artifacts.**
