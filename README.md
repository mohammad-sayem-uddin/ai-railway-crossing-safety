# Safety-Oriented Multimodal Railway-Crossing Train Detection Research Framework

**Research project — Bangladesh railway level-crossing safety using computer vision and audio.**

**Status:** Phase 0 (research software foundation) complete. Model training and multimodal system logic have not been implemented.

---

## Safety and Scope Disclaimer

This software is a research prototype and simulation framework. It is not a certified railway control system and must not be connected to live railway infrastructure or used for real-world safety control.

The strongest permitted claim, if later protocol execution succeeds, is limited to event-level outcomes on synchronized, held-out recordings — not physical safety, certification, deployment readiness, or real-time hardware performance.

---

## Overview

This project investigates whether a multi-view, audio-assisted, state-aware AI detection framework can improve the reliability of train approach and departure detection at railway level-crossings in Bangladesh.

The system uses:
- **Two cameras** for multi-view train detection (front/side/rear)
- **Audio** train horn detection as an independent evidence source
- A **state-based safety-oriented simulated decision engine**
- A **software simulation** of crossing gate control

---

## Documentation

All research documentation lives in `docs/`:

| Document | Purpose |
|----------|---------|
| [`docs/RESEARCH_PROTOCOL_V2.md`](docs/RESEARCH_PROTOCOL_V2.md) | **Current scientific protocol and claim boundary — read before implementation** |
| [`docs/RESEARCH_CONCEPT.md`](docs/RESEARCH_CONCEPT.md) | Historical research concept and architecture |
| [`docs/RESEARCH_DECISIONS.md`](docs/RESEARCH_DECISIONS.md) | Persistent log of design decisions with rationale |
| [`docs/EXPERIMENT_PLAN.md`](docs/EXPERIMENT_PLAN.md) | Experiment designs and status |
| [`docs/IDEA_LOG.md`](docs/IDEA_LOG.md) | Captured ideas with disposition |
| [`docs/PRE_CODING_CHECKLIST.md`](docs/PRE_CODING_CHECKLIST.md) | P0 gates required before research-system coding |
| [`docs/MASTER_IMPLEMENTATION_ROADMAP.md`](docs/MASTER_IMPLEMENTATION_ROADMAP.md) | Ordered implementation roadmap |

---

## Phase 0: What is Implemented

The repository now contains a clean, installable Python foundation:

- Configurable, validated YAML configuration (`configs/`)
- Typed data contracts for vision, audio, Layer B events, evidence, and decisions
- A vision dataset validator (image readability, label syntax, class IDs, bounding boxes, duplicates)
- A deterministic group-aware splitter with explicit leakage-safe fallback handling
- Run-manifest and experiment-registry reproducibility utilities
- Structured logging
- A package CLI with `data validate` and `data split` working; future commands show a clear "not implemented" message
- Unit, integration, and smoke tests with clearly labeled mock fixtures

No model training, fusion, state-machine, or research experiment logic is implemented yet.

---

## Environment and Setup

Supported Python version: **3.11 or newer** (developed and tested on 3.14).

```bash
cd Train_automation
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Dependencies for the Phase 0 foundation are intentionally minimal (PyYAML and Pillow). Development tooling includes pytest, ruff, mypy, and types-PyYAML.

---

## Commands

```bash
# Inspect available commands
python -m railway_detection --help

# Validate a vision dataset (Phase 0 functional)
python -m railway_detection data validate --config configs/vision.yaml

# Generate a group-aware split (Phase 0 functional)
python -m railway_detection data split --config configs/vision.yaml

# Dry-run configuration validation without touching data
python -m railway_detection data validate --config configs/vision.yaml --dry-run
```

Future commands (`vision train`, `audio train`, `simulate run`, `experiment run`, `report generate`) are present in the help surface but return a clear "not implemented in Phase 0" error.

---

## Quality Checks

```bash
pytest
ruff check src tests
mypy src
```

All 31 Phase 0 tests pass, and both static checks are clean.

---

## Repository Structure

```
Train_automation/
├── configs/               ← Versioned YAML configuration
├── data/                  ← Raw/interim/processed data, metadata, splits (gitignored)
├── src/railway_detection/ ← Installable package
├── scripts/               ← Thin wrappers (future)
├── tests/                 ← unit/integration/smoke/fixtures
├── experiments/           ← Future experiment run directories (gitignored)
├── models/                ← Future trained artifacts (gitignored)
├── results/               ← Generated reports and registry (gitignored)
├── docs/                  ← Research documentation (source of truth)
├── pyproject.toml
└── README.md
```

---

## When Real Annotated Data Arrives

Do not train immediately. Follow the intake checklist in `docs/MASTER_IMPLEMENTATION_ROADMAP.md`:

1. Place images under `data/raw/vision/images/` and labels under `data/raw/vision/labels/`.
2. Create metadata under `data/metadata/` with stable sample IDs and `split_group_id`.
3. Run `python -m railway_detection data validate --config configs/vision.yaml` and review the report.
4. Confirm grouping metadata and freeze the split before any model selection.

Phase 1 (ingestion/validation/split hardening) and later training phases should not begin until instructed.

---

*This is a research project, not merely a software project. Layer A images support perception-model development; synchronized Layer B train-passage events are required for multimodal system claims. All claims must be experimentally supported.*
