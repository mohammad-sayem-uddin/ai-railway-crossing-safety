# Mission 10 — Verified Condition Mapping (WP10.8)

> **MISSION 12 CORRECTION NOTICE (2026-11-02):** This mapping remains an engineering inventory. No real-data condition has executed; RD-043 and DEC-B05 remain proposals/pending decisions.  
> Written for: the researcher. Status: **IMPLEMENTED** (exists in code and exercised by a test), **PROPOSED**
> (named in a proposal/plan document only), **UNVERIFIED** (code exists but semantics not checked against an
> adopted protocol), **NOT_IMPLEMENTED**. "Executed on real data" is `NO` everywhere.

| Condition / mode | Where defined | Status | Notes |
|---|---|---|---|
| `B0`, `B1`, `B2` (cache-only engine: front vision / front audio / front fusion) | `evaluation/cache_only_engine.py` `SUPPORTED_CONDITIONS` | **IMPLEMENTED** (descriptive; gated by AUTH-DESCRIPTIVE-EVAL-EXEC on the real repo) | `test_cache_only_replay.py`, `test_descriptive_exec_gate.py` |
| `B0`…`B7` (legacy `BenchmarkCondition`) | `experiments/runner.py` | **IMPLEMENTED, semantics UNVERIFIED** | same names, different meanings (B2 = stateless union, B3 = dual-camera temporal) than the cache engine and than protocol v9.1.1; no document reconciles them |
| `single_camera`, `independent_camera`, `dual_camera` (official producer modes) | `evaluation/replay_evidence.py` `MODE_REQUIRED/MODE_FORBIDDEN`; `RealEventReplayProducer` | **IMPLEMENTED** | independent mode scores a separate `back` vision system on its own clock; dual only for accepted-sync events (R04, exploratory) — `test_phase12_official_replay.py` |
| `E1`…`E7` ablation matrix | `docs/FINAL_ABLATION_MATRIX.md`; `evaluation/ablation_runner.py` | **IMPLEMENTED as a plan only**; execution raises `Phase13ExecutionBlocked` | no E-condition has run |
| `B0_back` | proposed protocol v9.1.1 §(provisional), plan DEC-B05 | **PROPOSED** (name provisional, DEC-B05 PENDING) | not in code; engine refuses it |
| `B0_back_stateless`, `B2_back` | same | **PROPOSED** | not in code; refused |
| `B0_stateless` | master plan | **PROPOSED** | not in the cache engine |
| `B0_dual`, `B2_dual` | Gemini's gap assessment only | **NOT_IMPLEMENTED, not in any adopted/proposed protocol** | invented by the assessment; refused |
| M4 / M5 / lead-in screen | `evaluation/metrics.py`, `lead_in_screen.py` | **IMPLEMENTED** | Phase 1 tests + Mission 10 differential oracle |

Test: `tests/unit/test_mission10_back_stream_scope.py` fixes the supported set and asserts the undecided names
are refused (not substituted).
