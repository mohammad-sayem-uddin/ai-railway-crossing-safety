# Phase 15 — Controlled Validation Protocol

**Status:** PLANNING ONLY. No field activity has occurred or is authorized.
**Date:** 2026-10-15.

---

## 1. Summary

Phase 15 is primarily planning and safety-case development. No live railway control is authorized or planned. No field deployment has occurred.

## 2. Prerequisites

| Prerequisite | Status |
|---|---|
| Phases 12–14 complete | ❌ Blocked |
| Researcher authorization | ❌ Not granted |
| Site access authorization | ❌ Not obtained |
| Safety case approved | ❌ Not drafted |

## 3. Validation Protocol Design (Draft — Not Approved for Execution)

This document is a planning outline, not an approved protocol or safety case.
It must not be used to arrange field access, place equipment, collect data, or
set acceptance criteria. The draft's illustrative success criteria below are
unapproved placeholders and must not be interpreted as operational or
scientific thresholds.

### 3.1 What Will Be Validated
- Detection accuracy against passive observation.
- Timing characteristics (warning lead time, gate cycle).
- False alarm rate under real ambient conditions.

### 3.2 How
- **Passive observation only.** No intervention. No gate control.
- Sensors record; system processes offline.
- No connection to any actuator or control system.

### 3.3 Success Criteria — UNSET
- To be defined by the researcher and relevant safety/site authorities after
  Phases 12–14 evidence and approvals. No numerical threshold or pass/fail rule
  is proposed here.

### 3.4 Stop Conditions
- Any indication of safety-relevant failure.
- Site access revoked.
- Researcher withdraws authorization.

## 4. Safety Case Draft (Outline)

### 4.1 Scope
This safety case addresses **passive observation only**. It is NOT a safety certification. The system is a research prototype.

### 4.2 Hazards of Passive Observation
- Physical presence near railway (mitigated by: observer at safe distance, no track access).
- Equipment placement (mitigated by: no equipment on or near tracks).
- Data collection (mitigated by: no interference with railway operations).

### 4.3 What the System CANNOT Do
- Control a gate or barrier.
- Stop a train.
- Issue warnings to road users.
- Interface with railway signaling.
- Operate autonomously without human supervision.

### 4.4 Residual Risks
- Domain shift between Layer B evaluation data and the study site.
- R04 cross-camera synchronization unresolved for 16/27 events.
- Small sample size (27 events) limits statistical confidence.

## 5. Hardware Requirements (Draft)

| Component | Specification | Purpose |
|---|---|---|
| Camera (×2) | 1080p, 30fps, weatherproof | Front/back observation |
| Microphone | 16kHz, omnidirectional | Audio recording |
| Compute | Laptop, CPU-only | Offline processing |
| Storage | 500GB SSD | Data capture |
| Power | Battery + solar | Field operation |

## 6. Blocked Operations

All Phase 15 operations are blocked pending Phases 12–14 completion, researcher authorization, and site access.


---

## Additive update — 2026-10-16 (data-collection interface; no field activity)

`src/railway_detection/field_validation/capture_session.py` defines the `phase15-capture-session/1` record and a validator. Nothing here authorizes, schedules or performs field activity, and nothing connects to any gate, signal or control.

The validator enforces: passive observation only (no actuator connection, controls operated, intervention or model-derived labels); site-authorization and safety-case references pinned to document hashes and recorded by an allowlisted identity; observer distance compared with the minimum **taken from the safety-case record** (this code supplies no distance threshold); an explicit clock-offset estimate with method, or an explicit `unresolved` declaration, for multi-camera sessions (the R04 lesson); honored stop conditions; relative, hash-pinned data files never under `data/raw`.

`CaptureSessionValidation.external_authorization_verified` is always `false`: software cannot confirm that an authority granted access or that a safety case is sound, so a structurally valid record is **not** permission. Success criteria remain unset (section 3.3), and the safety case remains an unapproved outline. Tests: `tests/unit/test_phase15_capture_session.py` (31, synthetic records).

---

## Additive update — 2026-10-16 (overnight): capture-session v2

`phase15-capture-session/2` (`src/railway_detection/field_validation/capture_session_v2.py`; machine-readable schema `docs/schemas/phase15-capture-session-2.schema.json`) adds session identity and captured software provenance, a camera inventory (one camera, or exactly one `front` and one `back`) with hardware/firmware, environment metadata where `unknown` must be stated, per-device exposure accounting with ordered non-overlapping recording gaps and dropped-frame counts, per-device clock-drift checks, and a hash-chained chain of custody per file (`verify_session_files` recomputes hashes and sizes from disk). The validator emits PASS/FAIL checks; **every numeric limit it applies (minimum observer distance, maximum clock drift, stop conditions) must come from the record's own safety-case section — absent means FAIL**. It can never mark site authorization, operator permission or the safety case as verified (`external_authorization_verified` is always `false`; the strongest outcome is `STRUCTURALLY_VALID_NOT_PERMISSION`). No field activity occurred or is authorized. Tests: `tests/unit/test_phase15_capture_session_v2.py` (65).

## Additive update — deterministic manifest and preflight

`capture_session_manifest.py` adds a read-only, canonical JSON manifest and
preflight. It records a stable hash of the submitted session record, verifies
media hashes when a session directory is supplied, and emits explicit
`missing`, `invalid_reference`, or `recorded_reference_unverified` states for
site authorization and the safety case. The only successful internal outcome
is `STRUCTURALLY_VALID_NOT_PERMISSION`; external verification remains false.
Manifest writes are atomic and contain no wall-clock generation timestamp, so
the same record produces the same bytes. This is planning/audit tooling only;
it does not open devices, collect data, or authorize field activity.
