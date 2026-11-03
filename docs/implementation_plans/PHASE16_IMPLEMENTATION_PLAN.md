# Phase 16 — Publication and Research Release: Implementation Plan

**Status:** PLANNING ARTIFACT — not authorized, not implemented.

## 1. Objective and research justification

Prepare the research findings for publication and/or public release: write the manuscript, prepare supplementary materials, ensure all claims are traceable to evidence, verify reproducibility, and manage data/code release decisions. This phase is about communication integrity — every claim must be supported by a specific, citable artifact in this repository.

## 2. Verified starting state

Depends on Phases 12–15 (at minimum 12): evaluation metrics exist against approved ground truth; ablation and robustness findings exist; real-time characterization exists (if 14 was done); validation planning exists (if 15 was done). All frozen artifacts intact.

## 3. Dependencies and prerequisites

- Phase 12 evaluation report complete.
- Phase 13 ablation report complete (if authorized).
- Phase 14 optimization report complete (if authorized).
- Phase 15 validation protocol complete (if authorized).
- Researcher decision on publication venue, co-authorship, and data release scope.

## 4. Explicit authorization boundary

MAY draft manuscripts, prepare figures, organize supplementary materials, and prepare a code/data release plan. MUST NOT publish without researcher approval. MUST NOT claim safety certification. MUST NOT include raw video or personally identifiable information in any public release without explicit researcher decision. MUST NOT overstate findings beyond what the evidence supports.

## 5. Files/modules to inspect

- All phase reports (11.x, 12, 13, 14, 15 as available)
- `docs/EXPERIMENT_DESIGN_FINAL.md` (the research questions)
- `docs/FINAL_ABLATION_MATRIX.md`
- `docs/OPEN_DECISIONS_AND_BLOCKERS.md` (which questions were answered)
- `results/` directory structure (what is citable)
- `configs/frozen_experiment_v1.yaml` (for reproducibility statement)

## 6. Expected files to modify or create

Proposed: `docs/PHASE16_MANUSCRIPT_DRAFT.md` (or LaTeX); `docs/PHASE16_SUPPLEMENTARY_MATERIALS.md`; `docs/PHASE16_RELEASE_PLAN.md`; `docs/PHASE16_REPORT.md`; figures in `docs/figures/`. No code changes expected.

## 7. Detailed implementation tasks in dependency order

**Unit 1 (evidence audit):** for every claim the manuscript will make, identify the exact file/figure/table in the repository that supports it. Flag any claim without direct evidence. This is the anti-overclaim gate.
**Unit 2 (manuscript structure):** outline following the research questions from `EXPERIMENT_DESIGN_FINAL.md`; map each section to specific evidence; identify gaps.
**Unit 3 (figure and table preparation):** generate publication-quality figures from Phase 12–14 data; ensure every figure has a caption that states exactly what is shown and what is NOT shown.
**Unit 4 (reproducibility statement):** document exact environment, config hashes, checkpoint hashes, seed, and commands needed to reproduce every reported number.
**Unit 5 (release planning):** decide what code/data is released publicly vs. kept private; prepare a README for the public subset; handle any IRB/ethics considerations.
**Unit 6 (final review):** Opus reviews the manuscript for overclaim, logical gaps, and reproducibility; researcher gives final approval.

## 8. Data, schema, and API changes

None.

## 9. Tests and acceptance criteria

- Every claim in the manuscript has a traceable evidence reference (Unit 1 audit is complete).
- Every figure is reproducible from repository data.
- Reproducibility statement includes exact hashes and commands.
- Release plan explicitly lists what is included and excluded.
- Researcher has approved the final manuscript.

## 10. Negative tests and adversarial cases

- Grep the manuscript for safety-certification language → must find zero instances.
- Check that no raw video paths or personal identifiers appear in the public release plan.
- Verify that the Audio V2 checkpoint is not referenced as a valid model in any manuscript section.

## 11. Scientific-validity safeguards

Every number is traceable; limitations are stated prominently; R04 unresolved status is disclosed; small-n findings are reported with appropriate CIs; simulated gate behavior is labeled as simulation.

## 12. Safety invariants and prohibited shortcuts

No safety certification claims. No overclaim beyond evidence. No release of raw video without explicit researcher decision. No publication without researcher approval.

## 13. Expected outputs and report paths

`docs/PHASE16_MANUSCRIPT_DRAFT.md`, `docs/PHASE16_SUPPLEMENTARY_MATERIALS.md`, `docs/PHASE16_RELEASE_PLAN.md`, `docs/PHASE16_REPORT.md`, figures.

## 14. Rollback and recovery procedure

All outputs are documents; rollback = delete files. No production system is modified.

## 15. Integrity checks

Frozen config/checkpoint hashes unchanged; no modification to results/ or data/ directories.

## 16. Definition of done

Manuscript draft complete with evidence audit; figures generated; reproducibility statement verified; release plan approved by researcher; Opus overclaim review passed.

## 17. Stop conditions and escalation criteria

STOP if the evidence audit reveals a claim that cannot be supported (remove the claim, do not fabricate evidence); if the researcher declines publication; if a co-author dispute arises.

## 18. Recommended implementation model

**Gemini 3.8 Flash** for figure generation and formatting; **Claude Opus 4.8** for manuscript language review and overclaim detection; **Qwen 3.8 Max** for reproducibility verification.

**Minimum viable implementation:** Units 1–2 (evidence audit + structure). **Deferrable:** Units 5–6 (release planning and final review, only when researcher is ready). **Highest-risk failure mode:** overclaiming safety implications of simulated results (defeated by Unit 1 audit + Opus review). **Cheapest verification:** Unit 1 evidence audit covers 100% of manuscript claims.
