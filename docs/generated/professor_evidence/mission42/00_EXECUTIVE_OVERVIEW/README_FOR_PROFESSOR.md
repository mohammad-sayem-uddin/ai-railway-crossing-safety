# Professor evidence guide

Prepared 2026-11-08, America/New_York. This is the frozen evidence package for the existing five-event, single-site Train Gate Automation pilot. Three original inference stages and B2 input assembly are supported by saved outputs. **B2 decision replay has not executed; accepted canonical ground truth is not established.**

Start with [the executive summary](RESEARCH_EXECUTIVE_SUMMARY.md), [scope and objectives](PROJECT_SCOPE_AND_OBJECTIVES.md) and [stage completion](EXPERIMENT_COMPLETION_STATUS.md). Then read each evidence section:

- [Research Protocol](../01_RESEARCH_PROTOCOL/README.md)
- [Source Provenance](../02_SOURCE_PROVENANCE/README.md)
- [B0 Front Results](../03_B0_FRONT_RESULTS/README.md)
- [B0 Back Results](../04_B0_BACK_RESULTS/README.md)
- [B1 Audio Results](../05_B1_AUDIO_RESULTS/README.md)
- [B2 Input Assembly](../06_B2_INPUT_ASSEMBLY/README.md)
- [Human Review](../07_HUMAN_REVIEW/README.md)
- [Metrics And Limitations](../08_METRICS_AND_LIMITATIONS/README.md)
- [Software Validation](../09_SOFTWARE_VALIDATION/README.md)
- [Reproducibility](../10_REPRODUCIBILITY/README.md)
- [Remaining Research](../11_REMAINING_RESEARCH/README.md)

Review the observed outputs, acoustic feature correction, source-clock and preprocessing identities, human-review limitations, unavailable metrics and remaining admission bindings before choosing paper claims or further experiments. This package is evidence preparation; nothing has been sent to the professor or released publicly.

Original evidence filenames and bytes are retained in each section's `originals/` tree. `reading_views/` contains separately identified copies with package-local links; their headings explain historical context. Unpackaged historical references appear as text rather than misleading working links. Earlier “pending inference” statements remain historical; current stage status is in this guide. JSON paths into private runtime caches are historical labels, not included cache directories.

From the package root, run `python3 10_REPRODUCIBILITY/verify_package.py`. It reads packaged files only; no model, raw recording, inference, test suite or network is used. The manifest records original and packaged hashes, mission, category, status and limitations. PACKAGE_FILES.sha256 covers every other package file including the manifest. The checksum index's own identity is anchored by the containing Git commit; this is integrity evidence, not independent authenticity or scientific validation.

[Completion report](../PROFESSOR_PACKAGE_COMPLETION_REPORT.md).
