# Mission 13 synthetic-only probes

Read-only adversarial probes written by the Mission 13 auditor. They use temporary directories, fake (non-existent)
repository paths and in-process tripwires only. They never open repository media, checkpoints, processed data or
caches. Run from the repository root with:

    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python docs/generated/phase5/mission13_probes/<probe>.py

`reader_scan.py` is a static text scan (run with plain `python3` from the repository root).
Do not point any probe at real data. These files are audit evidence, not tests, and are not part of the safe set.
