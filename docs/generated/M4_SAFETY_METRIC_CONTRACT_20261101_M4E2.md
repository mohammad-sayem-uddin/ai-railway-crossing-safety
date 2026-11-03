# M4 Safety Metric Contract — Premature Gate Opening (`first_blocked_to_t4_clearance`)

> **PROPOSED — NOT APPROVED — NOT AUTHORIZATION.**
> The researcher selected M4 as the premature-opening safety metric. The profile is **not frozen, not bound**
> (`data/manifests/phase12_protocol_decision.json` is absent), and no event is M4-eligible today.

> **Revised in Mission 4E.3:** incomplete-replay handling corrected — see `M4_INCOMPLETE_REPLAY_CLASSIFICATION_CORRECTION_20261101_M4E3.md`. Superseded text is marked.

**Mission:** 4E.2 · **Implementation inspected:** `src/railway_detection/evaluation/metrics.py` (SHA-256 `8e38992cfa9ce841c47296f28669f6f2cfa0ab49532f2b48e6edbd498e29a673`).
**Note:** that file is **untracked** in git (`git ls-files` does not list it; `git log -- <path>` is empty). The implemented M4 has no commit history.

## 1. Nature of the metric

M4 is a **safety predicate over a protection interval**, evaluated per event: *"after the system first physically blocked the
passage, did it ever stop blocking / start opening before the train tail cleared?"*

**It is NOT an elapsed clearance-duration metric.** It returns a boolean, not seconds. A duration must never be derived from it
(the interval length `T4 − t_blocked` is not reported and has no meaning as clearance time). Elapsed duration is a separate
metric: see `OCCUPANCY_DURATION_METRIC_CONTRACT_20261101_M4E2.md`.

## 2. Definition (matches `m4_premature_opening`, metrics.py:105-122)

| Symbol | Definition | Source |
|---|---|---|
| `t_blocked` | `timestamp_s` of the **first retained replay `SimulationStep` with `is_passage_blocked=True`** | replay timeline (system-side) |
| `T4` | `boundary_adjudications.T4_tail_clearance.value_s`, state `OBSERVABLE`, human-reviewed and promoted | back-camera-local ground truth |
| Interval | strictly open: `t_blocked < t < T4` | — |
| Premature | any retained step in the interval with `is_passage_blocked == False` **or** `gate_state ∈ {"OPENING","OPEN"}` | — |

Output per event: `(premature: bool|None, never_protected: bool)`.

### Rules

| ID | Rule |
|---|---|
| M4-R1 | `t_blocked` is replay-derived. It is **not** T0/T1/T2/T3/T4, is not a ground-truth field and must not be added to Stage-2.1 records. |
| M4-R2 | Interval is open at both ends. The start step and any step with `timestamp_s == T4` are excluded (tests: `test_start_boundary_step_itself_is_excluded`, `test_step_exactly_at_t4_is_excluded`). |
| M4-R3 | A gate label `OPENING`/`OPEN` inside the interval is premature **even if `is_passage_blocked` is still True** (e.g. arm still >45°). This is stricter than "unblocked"; it is current behaviour (test `test_opening_or_open_state_inside_interval_is_premature_even_if_still_blocked`). |
| M4-R4 | Unblocked steps *before* `t_blocked` are irrelevant (test `test_unblocked_steps_before_start_are_ignored`). |
| M4-R5 | A re-open followed by re-close inside the interval is still premature. |
| M4-R6 | If no blocked step exists with `t_blocked < T4` → M4 = `None`, **M5 `never_protected = True`**. The event is excluded from the M4 denominator. |
| M4-R7 | `T4` missing / CENSORED / UNCERTAIN / UNOBSERVABLE → M4 *and* M5 not evaluable (`never_protected=None`). No substitution by T1, T0, T3 or `T_scene_clear`. |
| M4-R8 | Replay timestamps must be finite, ≥ 0, strictly increasing; `T4` finite and ≥ 0; otherwise `ValueError` (raised by `evaluate_run`). |
| M4-R9 | Population: train-cohort events only. Engine events → `engine_event_excluded`; no-train events → false-alarm path; unverified GT → not evaluable. |
| M4-R10 | A cohort aggregate may use exactly one `premature_opening_window`; mixing M4 with the v9 window raises `ValueError`. The window has no default; `None` = metric not computed (`premature_opening_window_undecided`). |
| ~~M4-V6~~ *(superseded by 4E.3)* | ~~Replay should reach T4, else M4-not-evaluable.~~ **Replaced by M4-V6′…V10:** classify by replay coverage (`t_last ≥ T4`): a *witnessed* violation is definite premature even on an incomplete replay; an incomplete replay with no violation, or with no blocked step, is `NOT_EVALUABLE` (`replay_ended_before_T4`) and **never M5**; an empty replay is `NOT_EVALUABLE` (`replay_empty`). Current code instead returns "not premature" (blocked, no violation) or **M5** (no blocked step, empty replay) for these cases. |

## 3. Replay provenance and dual-camera R04 prerequisites (identification only — **R04 is not approved here**)

| Need | Why | Current state |
|---|---|---|
| Replay evidence produced under the frozen config with provenance (`frozen_config_canonical_sha256`, `checkpoint_sha256` for vision & audio_v3, `media_sha256` front/back, thresholds, `annotation_labels_used=false`) | `t_blocked` is only meaningful if the replay is attributable and label-free (`replay_evidence.py:59-150`) | No production replay/cache exists; none authorized |
| Declared replay timeline identity: `front`, `back`, or `fused` | `T4` is on the **back** clock. M4 is non-computable on a front-only replay (`B0_B1_B2_METRIC_SPECIFICATION.md:260-277`; `clock_aware.py` rejects cross-clock comparison) | undecided per event |
| **Back-only replay:** no R04 needed for the boundary function. Caveat: `t_blocked` then reflects what the *back* stream alone could trigger, so M5 is "never protected *by that replay's sensing*", not "never protected by the dual-camera system" | interpretation limit | researcher must acknowledge |
| **Fused / dual-camera replay:** requires an accepted per-event synchronization (R04): `data/manifests/phase12_r04_scope_decision.json` (absent) with `event_modes` and `accepted_sync_events`; offset convention `Δt = t_back − t_front`; alignment status per GT v7 §5 (`aligned` δ≤0.5 s; `partially_aligned` ≤2.0 s with error bounds; `unaligned` excluded) | unresolved; candidate offsets exist only as `data/manifests/camera_sync_offsets_candidate.yaml` (unapproved; count reconciliation lives in `R04_ELEVEN_VS_TWELVE_RECONCILIATION_20261101_M4D.md`, not re-verified here) |
| Approved T4 | end boundary | 0 approved records exist (4E.1 audit; not re-run) |

R04 is therefore **required only if the replay fuses both cameras**; it is *not* approved or satisfied by this document.

## 4. Known limits (see gap register)

- Sparse retained steps: an interval with no retained step is vacuously "not premature" (test `test_empty_interval_is_vacuously_not_premature`).
- Replay ending before T4: current code returns "not premature" if blocked throughout, and **M5 `never_protected=True`** if never blocked or empty (4E.2 recorded only the first; corrected in 4E.3; pinned by tests in `TestKnownCharacterizedGap` and `TestCharacterizationOfCurrentCodeVsCorrection`).
- Rejected frames (Rule 8/10) are not in `steps`, so they cannot create or hide a blocked/unblocked state.

## 5. Not claimed

No event is declared eligible; no result computed from real data; no approval of R04; the profile is not frozen.
