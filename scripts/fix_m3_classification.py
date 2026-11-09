"""Add access-classification entries for the two unclassified test files.

Clones the canonical UNKNOWN entry block (the classification tools' own
test) from tests/test_access_classification.yaml, substituting the target
path, its real sha256, and the standard pending-review reason. This matches
the manifest generator's convention for new/changed sources: UNKNOWN until
executed guard evidence exists. Inserts each block in sorted path order.
Idempotent: skips files that already have an entry.
"""
from __future__ import annotations

import hashlib
import os
import re

ROOT = "/Users/sayemuddin/Desktop/Train_automation"
os.chdir(ROOT)
MANIFEST = "tests/test_access_classification.yaml"
TARGETS = [
    "tests/synthetic_mission44/test_display_rotation.py",
    "tests/unit/test_m3_cache_only_engine_multimodal.py",
]
TEMPLATE_KEY = "tests/unit/test_access_classification_tools.py"


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def clone_block(template_lines, target, digest):
    out = []
    skipping_reason = False
    for ln in template_lines:
        stripped = ln.strip()
        if stripped == TEMPLATE_KEY + ":":
            out.append(ln.replace(TEMPLATE_KEY + ":", target + ":", 1))
            continue
        if re.match(r"^tests:\s*$", stripped):
            break  # drop any trailing per-file test-count evidence block
        if "reason:" in ln:
            out.append(f"    reason: '{target}: changed/new source; UNKNOWN "
                       f"pending executed\n      evidence review'\n")
            skipping_reason = not ln.rstrip().endswith("'")
            continue
        if skipping_reason:
            if ln.rstrip().endswith("'"):
                skipping_reason = False
            continue
        ln = re.sub(r"sha256: [0-9a-f]{64}", f"sha256: {digest}", ln)
        out.append(ln)
    return out


def main():
    lines = open(MANIFEST).read().splitlines(keepends=True)
    starts = [i for i, ln in enumerate(lines)
              if re.match(r"^  \S.*:\s*$", ln)]
    starts.append(len(lines))

    def block_span(key, starts_now):
        for j in range(len(starts_now) - 1):
            if lines[starts_now[j]].strip() == key + ":":
                return starts_now[j], starts_now[j + 1]
        return None

    span = block_span(TEMPLATE_KEY, starts)
    assert span, "template block not found"
    template = lines[span[0]:span[1]]

    for target in TARGETS:
        if block_span(target, starts):
            print(f"already classified: {target}")
            continue
        block = clone_block(template, target, sha256_of(target))
        insert_at = len(lines)
        for j in range(len(starts) - 1):
            if lines[starts[j]].strip()[:-1] > target:
                insert_at = starts[j]
                break
        lines[insert_at:insert_at] = block
        starts = [i if i < insert_at else i + len(block) for i in starts]
        print(f"classified (UNKNOWN, pending review): {target}")
    open(MANIFEST, "w").write("".join(lines))
    print("CLASSIFY_FIX_DONE")


if __name__ == "__main__":
    main()
