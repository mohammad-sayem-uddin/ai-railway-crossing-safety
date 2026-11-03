# Mission 10 — Rebuild Readiness Assessment (WP10.9) and Back-Stream Findings (WP10.5)

> Written for: the researcher. Stage A/B/C authorizations are **missing and were not created**.

## 1. What must exist before anything touches real data
| Gate | Needed record | Present? |
|---|---|---|
| Stage A — media access (hash, probe, extract, inference) | `data/governance/AUTH-MEDIA-ACCESS.json` (schema `phase5-media-access-authorization/2`), signer on allowlist, protocol-document binding | **No** |
| Stage B — promotion | second allowlisted reviewer; Stage-2.1 records with every RD-043 trigger satisfied; readiness CLI READY (needs media re-hash ⇒ Stage A); receipt `data/governance/stage21_promotion_receipt.json` | **No** (no Stage-2.1 records at all; only invalidated legacy records) |
| Stage C — descriptive/official evaluation | `AUTH-DESCRIPTIVE-EVAL-EXEC.json` (descriptive replay) and/or `eval_authorization.json` (official), plus split decision, R04 decision, protocol decision | **No** |

## 2. Blockers (each independent)
1. No second reviewer on the allowlist ⇒ any trigger event is unpromotable (RD-042/043).
2. RD-043, RD-045 (adjudication format), RD-046 (duration floor) are proposals/deferred; GOV-REVIEW-SECOND-REVIEW-TRIGGERS PENDING.
3. D-BACK / DEC-B05 undecided (back-stream condition naming and descriptive back replay).
4. `annotation/`, `evaluation/`, `safety/` are untracked in git: nothing is reproducibly versioned.
5. M-02 (forgeable in-process permit), M-06 (reproducibility completeness) open.
6. Event-level: the exploratory subset test hashes real media; it can only run after Stage A.

## 3. Back-stream architecture (WP10.5)
Facts verified in code:
* The **official** path models the back camera as its own `back_vision` stream (`STREAM_SPEC` → `camera_2`),
  required in `independent_camera`/`dual_camera`, forbidden in `single_camera`; `RealEventReplayProducer` builds a
  separate system on its own clock, so M4/M5 (back-reference T3/T4) have a route. Fused/dual operation is for
  accepted-sync events only (R04, exploratory).
* The **descriptive** `CacheOnlyReplayEngine` has front-only streams, no back cache field in its manifest, and
  refuses every other condition name.
* `B0_back`, `B0_back_stateless`, `B2_back` exist only as *provisional* names in the proposed protocol and plan
  (DEC-B05 PENDING). `B0_dual`/`B2_dual` appear in no protocol document.
* Gemini's recommendation to restrict Phase 5 to front B0–B2 would remove the primary M4/M5 evidence — a design
  change, not an engineering fix.

Not implemented, deliberately: adding `B0_back` needs (a) DEC-B05 naming, (b) a manifest-schema extension for a
back-vision cache, (c) a statement that its outputs stay on the back clock. **Decision requested: D-BACK.**

## 4. Recommended order (for the researcher)
1. Commit the working tree (or tell me to prepare the commit). 2. Decide D-BACK/DEC-B05 and RD-043/045/046.
3. Allowlist a second reviewer. 4. Only then consider recording AUTH-MEDIA-ACCESS (Stage A). 5. Request re-audit of
Mission 10.
