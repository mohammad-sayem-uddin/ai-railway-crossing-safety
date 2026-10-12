# Research Decisions Log

**Status:** Active — records key design decisions, their rationale, and conditions for reconsideration.

**Last updated:** 2026-08-10

> **Protocol status (2026-10-11 update):** Decisions D-001 through D-010 remain historical records. System-level methodology is governed by the authoritative protocols: [`FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md`](FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md), [`FINAL_GROUND_TRUTH_PROTOCOL.md`](FINAL_GROUND_TRUTH_PROTOCOL.md), [`FINAL_EXPERIMENT_DATA_FLOW.md`](FINAL_EXPERIMENT_DATA_FLOW.md), and [`FINAL_ABLATION_MATRIX.md`](FINAL_ABLATION_MATRIX.md). The historical protocol v2 is archived at [`archive/RESEARCH_PROTOCOL_V2.md`](archive/RESEARCH_PROTOCOL_V2.md). The former “fail-safe” wording must not be interpreted as a physical-safety claim; material replacement decisions must be appended below rather than silently editing historical records.

---

## Decision Record Format

Each decision is recorded with:

- **DATE:** When the decision was made
- **DECISION:** What was decided
- **REASON:** Why this choice was made
- **ALTERNATIVES CONSIDERED:** What else was evaluated
- **EVIDENCE:** What supports this decision
- **STATUS:** Current state (Active / Superseded / Under Review)
- **WHAT WOULD CAUSE US TO CHANGE IT:** Conditions that would trigger reconsideration

---

## Decision Log

### D-001: Viewpoint Classes

**DATE:** 2026-08-10
**DECISION:** Use front/side/rear as the three initial visual viewpoint classes.
**REASON:** The research architecture explicitly studies viewpoint-dependent detection for approach (front), occupancy (side), and departure (rear). A single "train" class would erase this distinction.
**ALTERNATIVES CONSIDERED:** Single "train" class (rejected — loses viewpoint information needed for the research question). Four classes including "oblique/ambiguous" (deferred — may use metadata tag internally, but a fourth class needs experimental justification).
**EVIDENCE:** Architecture design requires viewpoint-contextualized detection for the state machine to distinguish approach vs. departure.
**STATUS:** Active
**WHAT WOULD CAUSE US TO CHANGE IT:** If annotation experiments show excessive inter-annotator disagreement or label noise that undermines model performance, reconsider class design or merge classes.

---

### D-002: Two-Camera Configuration

**DATE:** 2026-08-10
**DECISION:** Use two cameras with distinct roles: Camera 1 (approach detection — front/side), Camera 2 (departure confirmation — side/rear).
**REASON:** A single camera cannot simultaneously detect both approach and departure. Two cameras provide complementary viewpoints aligned with the crossing safety workflow.
**ALTERNATIVES CONSIDERED:** Single camera (rejected — cannot confirm departure without additional logic). Three or more cameras (deferred — adds complexity without clear justification at this stage).
**EVIDENCE:** Conceptual alignment with railway crossing geometry where approach and departure are on opposite sides.
**STATUS:** Active
**WHAT WOULD CAUSE US TO CHANGE IT:** If experiments show that a single high-FOV camera with different regions of interest achieves comparable results, or if the 5–6 meter separation is infeasible for real crossings.

---

### D-003: Audio as Independent Modality

**DATE:** 2026-08-10
**DECISION:** Include audio train horn detection as an additional independent evidence source.
**REASON:** Audio provides a modality that is unaffected by visual occlusion, fog, darkness, and camera failure. Train horns are a distinctive acoustic signal in the railway environment.
**ALTERNATIVES CONSIDERED:** Vision-only system (rejected — loses the multimodal fail-safe advantage that is central to the research question). Vibration or other sensors (deferred to future work).
**EVIDENCE:** Conceptual — train horns are a real-world signal used at Bangladeshi crossings.
**STATUS:** Active
**WHAT WOULD CAUSE US TO CHANGE IT:** If audio experiments show horn detection is unreliable under realistic noise conditions, or if the false-positive rate from environmental sounds makes audio more harmful than helpful in the fusion system.

---

### D-004: Safety-Oriented Gate Logic

**DATE:** 2026-08-10
**DECISION:** Implement asymmetric gate logic: aggressive toward closing (low evidence threshold), conservative toward opening (requires positive departure evidence).
**REASON:** In safety-critical systems, false negatives (failing to close when a train approaches) are far more dangerous than false positives (closing unnecessarily).
**ALTERNATIVES CONSIDERED:** Symmetric threshold-based logic (rejected — does not reflect the asymmetric safety costs). Human-in-the-loop override (possible future addition, not current scope).
**EVIDENCE:** Standard safety-engineering principle: prefer the safe state under uncertainty.
**STATUS:** Active
**WHAT WOULD CAUSE US TO CHANGE IT:** Only if the system is found to produce an unacceptable rate of unnecessary gate closures that would cause real-world operators to disable the system. In that case, the tradeoff curve should be explicitly parameterized and studied.

---

### D-005: Location-Aware Dataset Splitting

**DATE:** 2026-08-10
**DECISION:** Split dataset by railway crossing/location rather than random frame-level splitting.
**REASON:** Random splitting of frames from the same video or crossing leaks background-specific features into the test set, inflating performance estimates. Location-based splitting measures generalization to unseen crossings — a more honest and publication-worthy evaluation.
**ALTERNATIVES CONSIDERED:** Random split (rejected — scientifically weak for a generalization claim). Temporal split (considered but less important than spatial/crossing split for this problem).
**EVIDENCE:** Well-established ML evaluation practice for geospatial and scene-understanding tasks.
**STATUS:** Active
**WHAT WOULD CAUSE US TO CHANGE IT:** If the number of distinct crossings is too small for a meaningful location-based split (e.g., fewer than 10 crossings), we would need to use session-based splitting as a fallback and explicitly note the limitation.

---

### D-006: Software-Only Initial Scope

**DATE:** 2026-08-10
**DECISION:** Restrict the current research phase to software simulation, dataset creation, model training, and experimental evaluation. Do not implement a physical Raspberry Pi / edge deployment.
**REASON:** Hardware deployment introduces engineering complexity (embedded optimization, latency measurement, sensor integration, field testing) that is not required to answer the core research question. Premature hardware claims without measurement would weaken the publication.
**ALTERNATIVES CONSIDERED:** End-to-end physical prototype (deferred to future work).
**EVIDENCE:** The research question is about architecture and fusion reliability — answerable via carefully designed software experiments with real data.
**STATUS:** Active
**WHAT WOULD CAUSE US TO CHANGE IT:** If a collaborator with hardware expertise joins and a physical deployment becomes feasible within the timeline, or if the publication venue strongly prefers hardware validation.

---

### D-007: YOLO as Initial Vision Architecture

**DATE:** 2026-08-10
**DECISION:** Use a YOLO-family object detector (e.g., YOLOv8) as the initial vision model baseline.
**REASON:** YOLO is well-established, fast, well-documented, and has strong community support. It provides a credible baseline that reviewers will recognize. Starting with a known architecture lets us focus research effort on the multimodal fusion and decision logic rather than vision architecture innovation.
**ALTERNATIVES CONSIDERED:** DETR/transformer-based detectors (may be evaluated as a comparison later if results justify it). Custom CNN (unnecessary for this research question).
**EVIDENCE:** YOLO is a standard baseline in object detection papers and is sufficient for the viewpoint classification task.
**STATUS:** Active
**WHAT WOULD CAUSE US TO CHANGE IT:** If YOLO underperforms significantly on the specific viewpoint classes, or if a literature review reveals a clearly superior detector for railway applications.

---

### D-008: Annotation Workflow

**DATE:** 2026-08-10
**DECISION:** Use human-in-the-loop model-assisted annotation with iterative retraining.
**REASON:** Fully manual annotation of 4,000 images is time-prohibitive. Iterative model-assisted labeling is a well-established workflow that balances annotation quality with efficiency.
**ALTERNATIVES CONSIDERED:** Fully manual annotation (too slow). Fully automated annotation (too unreliable for research-quality labels).
**EVIDENCE:** Standard practice in CV dataset creation, supported by tools like Roboflow.
**STATUS:** Active
**WHAT WOULD CAUSE US TO CHANGE IT:** If the model-assisted annotations introduce systematic bias that manual review cannot correct, the initial manual set should be expanded.

---

### D-009: Reproducible Training Pipeline

**DATE:** 2026-08-10
**DECISION:** Final experiments must use an explicitly configured, reproducible training pipeline (recorded hyperparameters, seeds, software versions), not opaque hosted training.
**REASON:** Reproducibility is essential for a credible publication. A hosted "click train" result cannot be described in a methods section.
**ALTERNATIVES CONSIDERED:** Relying on Roboflow hosted training for final results (rejected for reproducibility reasons — acceptable for exploratory/iterative work only).
**EVIDENCE:** Standard reproducibility expectations in ML conferences.
**STATUS:** Active
**WHAT WOULD CAUSE US TO CHANGE IT:** Not applicable — this is a methodological requirement, not a design choice.

---

### D-010: Publication Target

**DATE:** 2026-08-10
**DECISION:** Target a normal/mid-tier international conference, with possible future Q2 journal extension.
**REASON:** The project scope (Bangladesh-specific dataset, applied engineering focus, moderate novelty) is appropriate for a mid-tier venue. Setting realistic expectations prevents over-engineering for Q1 standards that the project may not meet.
**ALTERNATIVES CONSIDERED:** Target Q1 journal directly (rejected — requires stronger novelty, larger scale, or theoretical contribution). Workshop-only (too narrow — conference offers better visibility).
**EVIDENCE:** Assessment of project scope against typical venue expectations.
**STATUS:** Active
**WHAT WOULD CAUSE US TO CHANGE IT:** If experiments reveal significantly stronger results than anticipated, or if literature review reveals that the specific contribution is more novel than currently estimated, the target could be raised.

---

### D-011: Evidence Boundary for Multimodal System Claims

**DATE:** 2026-08-13  
**DECISION:** A multimodal temporal/state-policy claim requires synchronized, event-labeled Layer B train-passage recordings with independent event ground truth. The Layer A still-image dataset is limited to perception-model development and evaluation.  
**REASON:** Independent images and separate audio clips cannot validly establish timing, cross-camera fusion, crossing clearance, or event-level gate-policy outcomes.  
**ALTERNATIVES CONSIDERED:** Use Layer A metrics and synthetic scenarios to claim system reliability (rejected — they demonstrate model/software behavior, not real multimodal event outcomes). Narrow the study to a viewpoint-detection paper if Layer B cannot be collected (accepted fallback).  
**EVIDENCE:** Pre-implementation methodology review; formal protocol in `RESEARCH_PROTOCOL_V2.md`.  
**STATUS:** Active.  
**WHAT WOULD CAUSE US TO CHANGE IT:** Only a different, independently justified system-evaluation design that preserves synchronized temporal ground truth and comparable held-out events.

---

### D-012: Phase 0 Python Foundation and Configuration Approach

**DATE:** 2026-08-13
**DECISION:** Implement the research software foundation in Python (>=3.11) as an installable `src/railway_detection` package using PyYAML for human-readable configuration, Pillow for image readability checks, and pytest/ruff/mypy for testing and static checks. No machine-learning or GPU-specific dependencies are introduced in Phase 0.
**REASON:** The roadmap requires a reproducible, typed, configurable foundation before any model work. A `src` layout with a package CLI (`python -m railway_detection`) keeps model-specific code isolated until later phases. PyYAML and Pillow are sufficient for config parsing and image validation without pulling in a full training stack prematurely.
**ALTERNATIVES CONSIDERED:** Pydantic for schema validation (deferred — dataclasses plus explicit validation are simpler and adequate for Phase 0); Poetry/uv for packaging (deferred — a standard `pyproject.toml` with `setuptools` and a virtualenv is simpler and reproducible).
**EVIDENCE:** `RESEARCH_PROTOCOL_V2.md` reproducibility and separation requirements; `MASTER_IMPLEMENTATION_ROADMAP.md` Phase 0 quality gate.
**STATUS:** Active.
**WHAT WOULD CAUSE US TO CHANGE IT:** If the dataset adapter or future training stack needs stricter schema coercion, or if a project convention mandates a specific package/configuration tool, revisit before Phase 1.

---

### D-013: Normalized Dataset and Evidence Contracts

**DATE:** 2026-08-13
**DECISION:** Define frozen dataclasses for `VisionSample`, `AudioSample`, `LayerBEvent`, `EvidenceRecord`, and `DecisionRecord`. All missing metadata is represented as `None` (serialized `null`) or explicit `unknown`, never fabricated. The vision validator works on normalized YOLO-style labels, while the import adapter exposes normalized annotations rather than leaking YOLO parsing into other modules.
**REASON:** Typed contracts let downstream modules rely on validated data and keep source-format specifics out of fusion/simulation logic. Explicit null/unknown keeps "missing" distinguishable from "zero confidence" for evidence.
**ALTERNATIVES CONSIDERED:** JSON-schema-only validation (rejected — loses static type checking and in-process validation). Pydantic models (deferred — dataclasses with explicit validation satisfy Phase 0).
**EVIDENCE:** `MASTER_IMPLEMENTATION_ROADMAP.md` §6 data contracts and evidence contract rules.
**STATUS:** Active.
**WHAT WOULD CAUSE US TO CHANGE IT:** If real dataset metadata requires more coercion, nested validation, or versioned schema migrations, migrate to Pydantic or add a schema version field.

---

### D-014: Group-Aware Split Fallback Policy

**DATE:** 2026-08-13
**DECISION:** The splitter requires `split_group_id` (from `crossing_id` or configured group field) for a leakage-safe split. If grouping metadata is absent, it fails by default and only falls back to a deterministic pseudo-random assignment when `allow_ungrouped_fallback` is explicitly set; the fallback emits a clear leakage warning and is never labeled as group-disjoint.
**REASON:** The protocol mandates `crossing → session → recording → event → window` grouping to avoid splitting related frames. Silent fallback would produce misleading generalization claims.
**ALTERNATIVES CONSIDERED:** Always allow fallback (rejected — unsafe). Require a hard stop with no fallback path (partially accepted — the default is a hard error; the flag exists only for explicit, recorded fallback in Phase 1).
**EVIDENCE:** `RESEARCH_PROTOCOL_V2.md` §24 leakage prevention; `MASTER_IMPLEMENTATION_ROADMAP.md` split quality gate.
**STATUS:** Active.
**WHAT WOULD CAUSE US TO CHANGE IT:** If a stronger grouping field is available for a specific dataset, add it to config and use the highest available hierarchy.

---

*Add new decisions as they are made. Update STATUS field if a decision is superseded. Do not delete old decisions — cross-reference them from the new decision.*
