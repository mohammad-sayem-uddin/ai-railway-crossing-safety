# Final Research Handover — Train Gate Automation

**Date:** 2026-10-21
**Repository:** `/Users/sayemuddin/Desktop/Train_automation`
**Branch / HEAD at baseline:** `main` / `d4db94d4a4ea83ae4c510d65dfc99c5d6798304b`
**Disposition:** definitive research stopping point; handover documentation complete; official evaluation and field validation remain blocked.

> This report is the authoritative final handover for the current repository state. It distinguishes implemented software, historical evidence, synthetic verification, genuine-media evidence, researcher decisions, authorization, and unresolved incident facts.

## 1. Executive summary

Train Gate Automation is a research prototype for multimodal train/crossing perception, conservative evidence fusion, and simulated gate-state behavior. The repository contains substantial implementation and governance infrastructure: vision and audio evidence adapters, temporal buffering, synchronization/calibration diagnostics, a conservative decision engine, gate simulation, annotation schemas and review controls, evaluation metrics and replay tooling, reproducibility audits, and fail-closed readiness gates.

The engineering foundation is usable for code review, synthetic testing, metadata-only contract checks, and future authorized research. It is **not** a validated railway safety system, deployment, field trial, or official Layer-B evaluation result. The available 27-event Layer-B corpus has candidate/provenance artifacts and an inventory, but zero valid Stage-2.1 approved ground-truth records. The 27 legacy review files are preserved and invalidated; their historical `APPROVED` fields are not evidence of human review.

The latest existing official readiness assessment (2026-10-19) was `ready: false`, exit `3`, with 9 blocker instances across 7 codes. This finalization did not rerun that prohibited official command. No evaluation, promotion, LEG-EXEC, real-media review, source-media read/hash/decode/preview/playback, genuine pilot record, or release activation was performed.

The October 19 media-access incident is administratively closed as `INVESTIGATION_CLOSED_UNRESOLVED`. Whether source-media bytes were read or hashed remains unknowable from surviving evidence. The timing-pilot release remains held, the pilot inactive, and the old release manifest unchanged.

## 2. Research objectives and actual contributions

### Objective

The project investigates whether conservative fusion of camera and acoustic train evidence can support safer level-crossing warning/closure decisions in offline replay and simulation. The intended contribution is a traceable research framework, not a certified interlocking controller.

### Implemented contributions (without a novelty or validation claim)

- YOLO-compatible vision evidence and held-out image evaluation contracts.
- Audio feature, preprocessing, classifier, training-safety, and evaluation components, including the frozen Audio V3 path and explicit prohibition of legacy Audio V2.
- Temporal evidence persistence, source-health/staleness tracking, cross-sensor collection, and conservative rule-based decision/state handling.
- Simulated crossing-gate dynamics, fault injection, fail-safe transitions, and deterministic synthetic experiment infrastructure.
- Dataset manifests, hash/provenance contracts, event/group split utilities, camera-sync diagnostics, and R04 scope evidence.
- A three-stage ground-truth lifecycle: candidate proposal, human review/adjudication, and approved manifest ingestion. Model predictions are excluded from human label authority.
- Fail-closed ground-truth loading, promotion/readiness gates, evidence-bound evaluation input manifests, replay/metric contracts, and metadata-only audit isolation.
- Evidence-limited manuscript correction and preservation of historical reports/overclaim findings rather than silently rewriting them.

These are software and documentation contributions. They do not establish field performance, operational safety, or superiority over another method.

## 3. Implementation inventory and status classification

| Area | Evidence | Status classification |
|---|---|---|
| Vision/train detection | `src/railway_detection/vision/`; frozen checkpoint records | **Complete and verified as software contracts.** Real Layer-B accuracy is not newly established. |
| Audio/train-horn evidence | `src/railway_detection/audio/`; Audio V3 report/checkpoint/config | **Complete as infrastructure.** Human confirmation and real-media performance remain absent; Audio V2 is prohibited. |
| Fusion/decision engine | `fusion/collector.py`, `decision_engine.py`, `rules.py`, `evidence.py` | **Complete and synthetic-tested.** No operational actuation is supported. |
| Gate simulation/fault injection | `simulation/` | **Complete and verified as simulation, not field validation.** |
| Synchronization/calibration | `data/sync.py`, `sync_calibration.py`, R04 evidence | **Partially complete; candidate evidence only.** Independent clocks and uncertainty remain. |
| Annotation/review | `annotation/`, Stage-2.1 schema, promotion controls | **Infrastructure complete; genuine review blocked.** |
| Evaluation | `evaluation/` loader, metrics, replay, governance, gate | **Engineering path tested; official evaluation blocked.** |
| Phase 13–15 work | experiment/optimization/capture contracts | **Optional future or blocked.** No authorized official ablation, field session, hardware, or safety case. |
| Reproducibility/governance | `pyproject.toml`, `requirements.lock`, audits | **Complete for software boundary; scientific inputs unresolved.** |
| Release/incident controls | Stage21 record and incident/closure reports | **Complete administratively.** Release held/inactive; incident fact unresolved. |

## 4. Datasets, provenance, and ground truth

### 4.1 Inventories

- `data/manifests/layer_b_v2_annotation_inventory.json` records the Layer-B v2 event inventory, paths, sizes, hashes, and metadata: 27 events (23 train, 3 no-train, 1 engine); the historical duplicate is excluded.
- `data/manifests/dataset_inventory_summary.json` separately records an older/retired video state and an 87-file audio development inventory with a missing negative-background note and duplicate/extension anomalies. These records must not be conflated.
- `data/splits/705d388743ea/` is a development/fallback, leakage-risk split, not an approved event-level evaluation split. Audio splits are development artifacts; embedded Layer-B test audio must not enter training before authorization.
- Frozen model paths, config hashes, and provenance are recorded in the README, frozen config, experiment manifests, and reports. Historical claims are not promoted without matching evidence.

### 4.2 Ground-truth limitations

- Candidate proposals and review sheets exist. The 27 legacy review JSONs are schema `6.0.0`, carry invalidated historical approval claims, and have sibling invalidation notices. They are preserved for audit history and cannot satisfy Stage-2.1.
- Current valid Stage-2.1 records: **0**; promotion receipt: absent/invalid; approved ground-truth manifest: absent.
- `T0` is first observed presence, but many train events are left-censored because the train is visible at recording start. A frame-0 value must not be treated as physical onset.
- `T1` is danger-zone entry; `T2` is roadway obstruction onset; **`T3` is locomotive-rear/unit clearance**; **`T4` is final-vehicle-rear/complete-train clearance**. Engine-only `T3 ≡ T4` does not collapse full-train definitions.
- Right-censoring, unobservable/uncertain boundaries, and insufficient post-clearance margin remain explicit denominator exclusions. Front/back timestamps are independent camera-local clocks unless a validated mapping is accepted. Durations must not be summed as synchronized exposure. Audio/model positives are not human-confirmed horns, and model predictions cannot determine human labels.

## 5. Experiments and results

### Supported evidence

- Existing reports document Layer-A development/model artifacts and historical still-image metrics. Those claims remain historical and evidence-scoped; they do not establish Layer-B event performance.
- Existing synthetic tests exercise schema rejection, metric arithmetic, state transitions, fault injection, governance, split/manifest contracts, metadata-only isolation, and timing-pilot safety boundaries. They demonstrate software behavior on fixtures, not genuine-media performance.
- Existing reports document candidate calibration/R04 diagnostics and preserved experiment outputs. They do not constitute researcher-approved scope decisions or official evaluation results.
- The historical DOCX and its nine overclaim/unsupported-number findings are preserved. The active evidence-limited manuscript/correction is separate; historical findings were not erased.

### Results not supported

There is no supported current claim for real-media precision/recall, MTR, POR, clearance latency, warning lead time, false alarms per hour, official ablation effect, field validation, target-hardware timing, deployment readiness, or railway safety certification. No official Layer-B result was produced in this final pass.

## 6. Evaluation readiness

The latest existing live gate record (`docs/generated/OFFICIAL_EVALUATION_READINESS_20261019.json`) reports:

- `ready: false`; exit code `3`.
- 9 blocker instances across 7 codes: three derived `COHORT_APPROVAL_MISSING`; `EVAL_AUTH_NOT_GRANTED`; `EVENT_SPLIT_DECISION_MISSING`; `MANIFEST_MISSING`; `PREMATURE_OPENING_DEFINITION_UNDECIDED`; `R04_SCOPE_DECISION_MISSING`; and `STAGE21_RECORDS_MISSING`.
- Null live bindings for the event split, input manifest, protocol profile, R04 scope decision, and Stage-2.1 promotion receipt.
- The separate Stage-2.1 readiness record is `NO_RECORDS`, exit `2`, because no valid records exist.

This finalization did **not** execute `evaluation status`, `evaluation run`, readiness CLI, LEG-EXEC, promotion, or any other official gate. The prior recorded results above are cited as existing evidence only.

### Remaining blocker table

| Item | Reason | Evidence required | Blocks official evaluation or publication claims? |
|---|---|---|---|
| Genuine Stage-2.1 ground truth | Human review/adjudication and authorization absent; legacy records invalidated | Authorized media-grounded records, second-review evidence, media hashes, promotion receipt | Yes |
| Review policy and ADJ-AUTH | D1/D3 timing/audit decisions and formal authorization absent | Researcher-attributed decisions and authorized reviewer arrangement | Yes |
| Leakage-safe event split | Existing image split is fallback/leakage-risk; session/crossing leakage unresolved | Researcher-approved event/session split or independent groups | Yes |
| Premature-opening definition | v9 and M4 remain unresolved | Researcher-authored protocol decision bound to run | Yes |
| R04 scope/synchronization | Independent clocks and candidate calibration are not approval | Per-event scope and validated offset evidence | Yes |
| Derived input manifest | Upstream labels, split, protocol, scope, and payloads missing | Hash-bound manifest from verified decisions/payloads | Yes |
| EVAL-AUTH | Exact live bindings incomplete; chat statements do not replace record | Researcher authorization bound to all live hashes | Yes |
| Historical manuscript overclaims | Historical DOCX contains archived findings | Use active evidence-limited manuscript and label history | Yes, if presented as current |
| October 19 media-access fact | Surviving evidence cannot determine read/hash activity | New independent authorized audit evidence, if available | Release trust; not a metric gate |
| Timing-pilot activation | Release held; old manifest hashes stale relative to checkout | Independent review, new versioned release, explicit activation authorization | Yes for pilot |

## 7. Governance and incident status

- `docs/MEDIA_ACCESS_INCIDENT_INVESTIGATION_20261020.md` and `docs/INCIDENT_CLOSURE_REVIEW_20261020.md` are preserved. Administrative disposition is **`INVESTIGATION_CLOSED_UNRESOLVED`**.
- Closure means investigation work reached the limit of surviving evidence; it does **not** establish that media access did or did not occur. This handover makes no such claim.
- The timing-pilot release remains `PREPARED_NOT_ACTIVATED`; release status is **HELD** and the pilot is **INACTIVE**. No activation authorization or genuine pilot record was created.
- `docs/generated/stage21_timing_pilot_release.json` was not regenerated or modified. Its preserved SHA-256 is `9e6d990a3676f4473a5cb8cc2cc6471df3ce8e02b6566d03b38142bb190e1abf`.
- The prohibited Audio V2 checkpoint was not used. No source-media bytes were opened, hashed, decoded, previewed, played, or sent through inference in this finalization.
- No staging, commit, push, reset, clean, or broad revert was performed.

## 8. Safe reproducibility instructions

### Environment

Use Python 3.11 and the canonical `venv/` environment described in `README.md`. The declared dependencies are in `pyproject.toml`; the pinned environment record is `requirements.lock`. `.venv/` is not canonical because its package set differs from the lock record. Installation success does not provide data, authorization, or scientific validation.

### Safe software checks

From the repository root, these checks are safe because they use synthetic fixtures or source/metadata only:

```bash
venv/bin/python -m pytest -q \
  tests/unit/test_decision_engine.py \
  tests/unit/test_temporal_evidence.py \
  tests/unit/test_phase12_metric_arithmetic.py \
  tests/unit/test_metadata_only_audit.py \
  tests/unit/test_phase12_input_contracts.py \
  tests/test_phase11_9_synthetic_pilot.py
venv/bin/python -m pytest -q \
  tests/unit/test_reproducibility_audit.py \
  tests/unit/test_readiness_audit.py \
  tests/unit/test_phase12_documented_metrics.py \
  tests/unit/test_phase12_governance.py
venv/bin/python -m compileall -q src scripts
venv/bin/python -m pip check
```

The metadata-only audit is not official readiness and must report source bytes as unopened. Synthetic pilot tests must never be represented as genuine-media review. Do not run official readiness/evaluation commands, promotion workflows, LEG-EXEC, annotation CLI against real media, or source-media operations under current restrictions.

## 9. Completed during this finalization

### Documentation changes

- Added this authoritative report: `docs/FINAL_RESEARCH_HANDOVER_20261021.md`.
- Corrected `README.md` status wording to require certified ground truth **and** the live readiness gate, linked this handover, and corrected setup/dependency instructions to match `pyproject.toml` and the canonical `venv`/lock evidence. No historical report or protected release record was rewritten.

### Safe checks actually run

| Check | Result / exit code |
|---|---|
| Synthetic/metadata-safe focused pytest subset (6 files) | **69 passed**, exit `0` |
| Reproducibility/readiness/metrics/governance pytest subset (4 files) | **122 passed**, exit `0` |
| Combined tests reported here | **191 passed**, 0 failed, exit `0` (additive, non-overlapping commands) |
| `venv/bin/python -m compileall -q src scripts` | Passed, exit `0` |
| `venv/bin/python -m pip check` | `No broken requirements found`, exit `0` |
| Targeted Ruff on inspected implementation files | Exit `1`: 19 existing `E501` line-length findings; no auto-fix or unrelated cleanup performed |
| `git diff --check` on changed README/metadata scope | Passed, exit `0` |
| Official readiness/evaluation, promotion, LEG-EXEC, media review/access | **NOT RUN — SAFETY CONSTRAINT** |

The final report was written after the checks above; its headings, hashes, and whitespace were verified after creation without reading source-media bytes.

## 10. Final stopping-point checklist

### Complete and verified

- [x] Core perception/fusion/simulation and governance infrastructure inventoried.
- [x] Dataset manifests, candidate/provenance boundaries, split limitations, and ground-truth invalidation status documented.
- [x] T0/T3/T4 semantics, censoring, independent clocks, horn-label, and model-independence limitations preserved.
- [x] Historical results and overclaim findings retained; active claims separated from historical artifacts.
- [x] Safe synthetic/metadata tests, compilation, dependency, and changed-document checks completed.
- [x] Final handover and README setup/status guidance written.
- [x] Incident closure and held-release controls preserved.

### Blocked by missing evidence/authorization

- [ ] Genuine human Stage-2.1 review/adjudication and promotion.
- [ ] Researcher decisions for review policy, split, premature-opening endpoint, and R04 scope.
- [ ] Hash-bound derived input manifest and EVAL-AUTH.
- [ ] Official Layer-B evaluation and any real-data performance result.
- [ ] Field/target-hardware validation, deployment, certification, and safety claims.
- [ ] Resolution of the factual October 19 media-access question.
- [ ] New reviewed timing-pilot release and explicit activation, if a pilot is ever authorized.

### Optional future research—not required for this handover

- Phase 13 official ablations/robustness after separate authorization.
- Cross-site/weather/domain-generalization data collection.
- Hardware/PLC/interlock safety engineering and independent certification.
- Expanded negative-control exposure and validated long-duration false-alarm study.
- Independent camera-clock/visual-landmark calibration research.

## 11. Handover recommendation

The repository can be handed to a supervisor or research collaborator today as an **evidence-limited research software prototype and governance package**. They can inspect the source, manifests, frozen artifacts, synthetic tests, protocols, candidate review materials, historical results, readiness blockers, and incident/release records.

It must not be represented today as officially evaluated, field validated, deployment-ready, railway-safe, synchronized across cameras, or supported by human-confirmed horn labels. The 27 legacy `APPROVED` records must not be cited as genuine ground truth. The historical DOCX must not be presented as the current evidence-limited manuscript without its archival status and findings. The timing pilot must not be activated, and the old held manifest must not be used to authorize activation.

This is the final planned engineering pass. No further sprint is implied; any future work is a separately authorized research activity that must begin with the blockers and evidence requirements above.

## 12. Final integrity statement

At handover, the incident records remain preserved, the timing-pilot release remains **HELD**, the pilot remains **INACTIVE**, the release manifest remains unchanged at the recorded hash, no official readiness/evaluation or prohibited workflow was run in this finalization, no source-media bytes were accessed by this finalization, and no files were staged or committed.

