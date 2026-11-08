# Project Structure and Research Documentation Index

**Project:** Train Gate Automation — a multimodal, temporal, safety-oriented
railway-crossing decision architecture (research prototype; see `README.md` for the
research overview, experimental status, and blockers).

This document maps the repository as it actually is (verified 2026-11-08) and indexes
the research documentation. It does not duplicate the reports it links to.

---

## 1. Repository map

### Root

| Path | Contents |
|---|---|
| `README.md` | Project overview, architecture, experimental status, blockers |
| `PROJECT_STRUCTURE.md` | This document |
| `pyproject.toml` | Package build (`railway-detection`, src layout), dependencies, pytest/ruff/mypy configuration |
| `requirements.lock` | Pinned dependency lockfile |
| `.env.example` | Environment template (copy to `.env`; never commit `.env`) |
| `.gitignore` | Version-control exclusions (see §4) |
| `Railway_Crossing_Automation_Research_Report.docx` | Early progress report (2026-08-31). **Historical**: contains claims later corrected by project audits (see research recovery report, conflict register) |
| `INDEPENDENT_RESEARCH_DESIGN_AUDIT.md` | Independent design audit (2026-10-13); findings CF-01…CF-03 |
| `RECOVERY_INVENTORY_REPORT.md`, `RECOVERY_RESTORATION_REPORT.md` | Repository recovery records |
| `dashboard.py`, `demo_video.py` | Standalone demonstration utilities |

### Source code — `src/railway_detection/` (170 Python modules)

| Package | Modules | Responsibility |
|---|---|---|
| `fusion/` | 8 | **Decision core**: evidence contracts (`evidence.py`), time-aligning collector (`collector.py`), frozen rules (`rules.py`), decision engine (`decision_engine.py`), sensor-health tracker (`source_tracker.py`), plus the unauthorised v2 candidate (`rules_v2_candidate.py`, `decision_engine_v2_candidate.py`) |
| `simulation/` | 5 | Formal state-machine mirror (`state_machine.py`), gate physics (`gate_model.py`), replay/simulation runner (`runner.py`), failure injection (`failure_injector.py`) |
| `vision/` | 8 | YOLOv8n adapter, video/PTS handling, temporal evidence buffer, training, evaluation, failure analysis |
| `audio/` | 10 | Log-mel features, `CompactTrainHornCNN`, evidence pipeline, dataset/training/evaluation, noise mixer |
| `evaluation/` | 24 | Governed replay (`cache_only_engine.py`), descriptive-execution gate (`descriptive_exec_gate.py`), replay producer, metrics, governance, ground-truth loading, perturbation |
| `annotation/` | 37 | Annotation proposals, schemas, review/readiness tooling |
| `application/` | 16 | Application-level orchestration |
| `experiments/` | 11 | Experiment processors, incl. the Layer-B input-assembly processor (`layer_b_processor.py`) |
| `data/` | 11 | Dataset loading and synchronisation alignment |
| `safety/` | 8 | **Research-governance/access control only** (media authorisation, pytest access guard, constructed-fixture authority). Despite the name, this package contains *no* gate fail-safe logic — fail-safe behaviour lives in `fusion/` |
| `synthetic/` | 7 | Synthetic fixture generation |
| `field_validation/` | 4 | Field-validation support |
| `optimization/` | 5 | Optimisation utilities |
| `config/`, `cli/`, `demo/`, `utils/`, `reproducibility/` | 13 | Configuration loading, command-line entry points, demos, utilities, reproducibility helpers |

Package root notice (`src/railway_detection/__init__.py`): *"research software only. It
is not a railway control system and must not be connected to live railway
infrastructure."* Version 0.1.0.

### Configuration — `configs/` (9 files)

| File | Status |
|---|---|
| `frozen_experiment_v1.yaml` | **Authoritative executed configuration** (pinned checkpoints + SHA-256, thresholds 0.35/0.37, timing). Provenance hash `999a7970…a42e` |
| `decision_policy_v1.yaml` | **Frozen executed policy** (RULE_1–RULE_9 parameters) |
| `decision_policy_v2_candidate.yaml` | Candidate under research review — **not authorised, not the default** |
| `vision.yaml`, `audio.yaml` | Training configurations (grouped splits; classes front/rear/side; horn/non-horn) |
| `exploratory_dual_camera_v1_supported_subset.yaml` | Dual-camera subset definition (11 `CALIBRATION_SUPPORTED` events), `authorized_for_execution: false` |
| `exploratory_dual_camera_v1.1.0_authorized_20261013.yaml` | Same subset with owner authorisation dated 2026-10-13; explicitly does not extend to full-cohort conditions |
| `fusion.yaml` | **SUPERSEDED Phase-0 placeholder schema** — not executed; marked in-file (2026-11-08) |
| `simulation.yaml` | **SUPERSEDED Phase-0 placeholder schema** — not executed; marked in-file (2026-11-08) |

### Data — `data/`

| Subdirectory | Contents |
|---|---|
| `raw/` | Original recordings — **local-only, git-ignored** (`layer_b/` media, standalone audio). Never modified |
| `ground_truth/` | Annotation proposals, reviews, snapshots, authorised-reviewer records. Content is the researcher-adopted AI-assisted reference (see README §5) |
| `governance/` | Researcher authorisation records (e.g. media-access). The descriptive-execution authorisation record does **not** exist yet — see README §7 |
| `manifests/` | Dataset and experiment manifests (hash-bound) |
| `metadata/`, `splits/`, `interim/`, `processed/` | Event metadata, train/val/test split descriptors, intermediate artifacts |
| `cache/` | Derived prediction caches from executed inference (Missions 39/43), versioned |

### Experiments, models, results

| Path | Contents |
|---|---|
| `experiments/` | Training runs for vision and audio (descriptors, metrics, checkpoints). Checkpoint weights (`*.pt`) are git-ignored but hash-pinned by the frozen config |
| `models/` | Local model assets. Contains the legacy Audio V2 checkpoint, which the frozen config **prohibits** from inference |
| `results/` | Experiment outputs and benchmark summaries, incl. `results/experiments/cache/` (per-event evidence caches) and the historical `.docx` report copy |
| `research/` | Manuscript support: figure registry (`FIGURE_REGISTRY.md`), figures, templates, scripts (`research/README.md`, 2026-08-18) |
| `reports/` | Progress reporting |
| `schemas/` | Data schemas |
| `scripts/` | Utility and audit scripts |
| `tests/` | Guarded test programme: unit, integration, and synthetic-fixture suites, incl. `tests/synthetic_mission44/` (display-rotation tests). Latest full run: 3,815 cases, 3,700 passed / 84 failed / 31 errors — all non-passing cases triaged as protected-dependency policy exceptions (Mission 40/43). The suite must not be described as passing |
| `outputs/` | Local runtime outputs (empty by design; git-ignored patterns) |

### Local-only (git-ignored, not published)

`data/raw/layer_b/` and other original media, `Unseen_Video/` (two 2026-08 screen
recordings — not an evaluation corpus), `ESC-50-master/` (third-party corpus),
`scratch/` (researcher pilot-inspection workspace, retained locally by design),
`venv/` and `.venv/`, tool caches (`.mypy_cache/`, `.pytest_cache/`, `.ruff_cache/`,
`__pycache__/`), `.commandcode/` (local tool configuration), `.env` and credential
files, all `*.pt`/`*.pth` weights.

---

## 2. Research documentation index

### Founding documents (the original research design)

| Document | Date | What it is |
|---|---|---|
| [`docs/archive/RESEARCH_CONCEPT.md`](docs/archive/RESEARCH_CONCEPT.md) | 2026-08-10 | Original concept and source of truth for intent: problem, three-phase goal, hedged novelty candidates, failure-injection design, the "weak version to avoid" |
| [`docs/archive/RESEARCH_PROTOCOL_V2.md`](docs/archive/RESEARCH_PROTOCOL_V2.md) | 2026-08-13 | **Authoritative protocol**: the primary research question ("change", not "improve"), B0–B7 baseline conditions, audio-authority limits, Layer A/B evidence boundary |
| [`docs/RESEARCH_DECISIONS.md`](docs/RESEARCH_DECISIONS.md) | 2026-08-10/13 | Decision log D-001…D-014 (viewpoint classes, asymmetric gate logic, software-only scope, Layer A/B split) |
| [`docs/HAZARD_MODEL.md`](docs/HAZARD_MODEL.md) | 2026-08-13 | Safety invariants and hazard register for the simulated policy (explicitly *not* a physical safety case) |
| [`docs/archive/EXPERIMENT_PLAN.md`](docs/archive/EXPERIMENT_PLAN.md) | 2026-08-10 | Original experiment plan (A–G ladder, fusion comparison M-EXP-1, failure experiments DE-EXP-2) |
| [`docs/archive/IDEA_LOG.md`](docs/archive/IDEA_LOG.md) | 2026-08-10 | Idea log; I-003 "Audio Train Horn Detection as Fail-Safe", I-009 learned fusion (deferred) |

### Audit-era methodology (October–November 2026 narrowing)

| Document | What it is |
|---|---|
| [`docs/EXPERIMENT_DESIGN_FINAL.md`](docs/EXPERIMENT_DESIGN_FINAL.md) | Narrowed design (2026-10-13): stateful-vs-stateless reopening question, E1–E10 taxonomy |
| [`docs/FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md`](docs/FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md) | Real-world experiment protocol v9 (2026-10-12) |
| [`docs/FINAL_GROUND_TRUTH_PROTOCOL.md`](docs/FINAL_GROUND_TRUTH_PROTOCOL.md) | Ground-truth protocol (Stage 2.1 promotion path — never completed) |
| [`docs/B0_B1_B2_ARCHITECTURE_AUDIT.md`](docs/B0_B1_B2_ARCHITECTURE_AUDIT.md) | Architecture audit of the B0/B1/B2 line |
| [`INDEPENDENT_RESEARCH_DESIGN_AUDIT.md`](INDEPENDENT_RESEARCH_DESIGN_AUDIT.md) | Independent audit (2026-10-13): CF-01/CF-02 (tests give zero performance evidence), CF-03 (B/E taxonomies unreconciled) |
| [`docs/PREMATURE_OPENING_DECISION_EVIDENCE.md`](docs/PREMATURE_OPENING_DECISION_EVIDENCE.md) | Evidence for the still-undecided `premature_opening_window` definition |
| [`docs/generated/master_reaudit/MASTER_SCIENTIFIC_NOVELTY_AUDIT.md`](docs/generated/master_reaudit/MASTER_SCIENTIFIC_NOVELTY_AUDIT.md) | Novelty audit (2026-11-02): reframes contribution as M4/M5/MTR + asymmetric authority; lists standard-practice items and retracted early overclaims |

### Mission record

| Location | Contents |
|---|---|
| `docs/generated/master_reaudit/` | Missions 16–38 audit programme: per-mission reports/registers (Mission 29 exists as flat registers; Missions 30–38 as subfolders) |
| [`docs/generated/research_results/mission39/`](docs/generated/research_results/mission39/) | Mission 39: first original-data execution — 5-event pilot inference + B2 input assembly |
| [`docs/generated/research_results/mission40/`](docs/generated/research_results/mission40/) | Mission 40: evaluation validation, test triage, first recorded B2 replay refusal |
| [`docs/generated/research_results/mission41/`](docs/generated/research_results/mission41/) | Mission 41: exact B2 admission requirements (five hash bindings) |
| [`docs/generated/professor_evidence/mission42/`](docs/generated/professor_evidence/mission42/) | Mission 42: professor evidence package (1,068 files, integrity manifest) — organisation only, no new experiments |
| [`docs/generated/professor_evidence/mission43/`](docs/generated/professor_evidence/mission43/) | Mission 43: full 27-event inference, adopted-reference audio comparison, B2 replay still blocked (`MISSION_43_FINAL_REPORT.md`, `ACTUAL_FULL_COHORT_RESULTS.json`) |
| [`docs/generated/professor_evidence/mission44/`](docs/generated/professor_evidence/mission44/) | Mission 44: post-43 diagnostics — annotation-capability audit, audio threshold/spectrum analysis, display-rotation defect work |
| [`docs/generated/research_recovery/`](docs/generated/research_recovery/ORIGINAL_RESEARCH_TARGET_AND_BLOCKER_REPORT.md) | **Research recovery report (2026-11-08)**: reconstruction of the original target, architecture and methodology; blocker register; completion roadmap; 10 supporting CSV matrices |
| `docs/generated/repository_maintenance/` | Repository cleanup and GitHub release report (2026-11-08) |

### Historical records — handle with care

- `docs/PHASE11_EVENT_INVENTORY.csv` — every row flagged `INVALID_FABRICATED_APPROVAL`.
  **Never cite as ground truth.**
- The 2026-08-31 `.docx` progress report — contains the weighted-fusion formula and
  performance language that were never implemented / later retracted. Cite only with
  the recovery report's conflict register (C3/C4).
- Superseded protocols and placeholder configs are retained for auditability and are
  marked as superseded in-file or in this index; they do not describe the executed
  system.

---

## 3. Experiment taxonomy map (read this before comparing numbers across eras)

The project used four different condition taxonomies. **They do not map onto each
other**, and results labelled in one era must not be read in another era's terms
(Independent Audit CF-03).

| Era | Labels | Meaning |
|---|---|---|
| Concept (2026-08-10) | A–G | Capability ladder: A front-only → B front+side → C front+side+rear → D vision only → E audio only → F vision+audio → G full state-aware architecture |
| Protocol V2 (2026-08-13) | B0–B7 | **Decision-policy conditions** on synchronized events: B0 single-camera no-temporal … B6 two-camera + audio + temporal + state policy; B7 = B6 with each source removed + fault simulation. *Never executed as decision conditions on original data* |
| Experiment Design Final (2026-10-13) | E1–E10 | Audit-era experiment taxonomy centred on stateful-vs-stateless reopening; **not reconciled** with B0–B7 |
| Missions 39–43 (2026-11) | B0_front, B0_back, B1_audio, B2 | **Perception/assembly labels, not Protocol-V2 conditions**: B0_front/B0_back = vision inference per camera; B1_audio = audio inference; B2 = input assembly (front + audio) and the *blocked* descriptive replay. In `cache_only_engine.py` the replay conditions are B0 = {front_vision}, B1 = {front_audio}, B2 = {front_vision, front_audio} |

Related distinction (Decision D-011): **Layer A** = still-image perception evidence
(benchmarks only); **Layer B** = synchronized passage-event evidence (required for any
system/decision claim).

---

## 4. Version-control policy (summary of `.gitignore`)

Versioned: source, configs, protocols, manifests, annotations/proposals, mission
evidence packages, derived caches, reports. Local-only: original media, third-party
corpora, model weights, virtual environments, tool caches, secrets (`.env*`, keys),
and the researcher's `scratch/` workspace. Narrow patterns only — the evidence-bearing
trees (`results/`, `experiments/`, `docs/generated/`, `data/ground_truth/`,
`configs/`) are deliberately **not** blanket-ignored.

*Maintained 2026-11-08 as part of the repository cleanup and GitHub release.*
