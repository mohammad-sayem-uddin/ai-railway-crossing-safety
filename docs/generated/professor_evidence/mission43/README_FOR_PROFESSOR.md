# Professor guide — full 27-event execution

Start with [the final findings](MISSION_43_FINAL_REPORT.md), then [the exact27-event coverage](FULL_27_EVENT_COVERAGE_MATRIX.csv), [annotation/reference verification](ANNOTATION_AND_REFERENCE_VERIFICATION.md) and [quantitative metrics](QUANTITATIVE_METRICS_AND_SCOPE.md).

Original inference now covers 27 front recordings, 27 back recordings and 27 front embedded acoustic tracks. The previous five-event inference is reused, not repeated. Actual totals:6613 front records/329 objects; 6479 back records/1020 objects; 2600 audio windows/445 positive at 0.37; 6614 B2 input frames/3897 with both records. No B2 decisions.

Your researcher's approval is preserved as adoption of all 27 active AI-assisted annotation contents. It enabled a limited exploratory event-label audio comparison:TP12/FP10/FN1/TN0 among 23 train events with explicit horn labels. Engine separate; controls' null horn labels excluded. This reveals poor specificity relative to those labels. It is not a frame/window or independent-human-GT accuracy finding.

Read [image findings](IMAGE_MODEL_EXPERIMENT_REPORT.md), [audio findings](AUDIO_MODEL_EXPERIMENT_REPORT.md), [multimodal status](MULTIMODAL_EXPERIMENT_REPORT.md), [failure review](FAILURE_CASE_ANALYSIS.md), [software outcomes](SOFTWARE_TESTING_REPORT.md), [limitations/next work](LIMITATIONS_AND_NEXT_RESEARCH.md) and [reproducibility](REPRODUCIBILITY.md). All nine figures are listed with their actual data inputs in [figure provenance](FIGURE_PROVENANCE.json); no manuscript is prepared.

The package contains original-derived predictions/clock metadata and copied annotation/text evidence, not raw media, PCM, checkpoint binaries, credentials or private caches. Historical inputs keep original filenames/bytes and may contain historical links; their source mapping is explicit. The current reports control current status. No material was sent to anyone.

From this folder run `python3 verify_package.py` for package-local integrity verification. Do not execute old inference scripts as if their past operation grants remain live. Exact grants used here were closed; B2 promotion/protocol bindings remain absent. [Acceptance criteria](FINAL_ACCEPTANCE_STATUS.json) distinguish complete execution from unavailable evaluations.
