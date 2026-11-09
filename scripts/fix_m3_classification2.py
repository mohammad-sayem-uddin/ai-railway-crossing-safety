"""Fix v2 for the two new classification entries (Mission 3).

The cloned UNKNOWN blocks lack the required 'evidence' and 'tests' keys
(the template's copies sit after its tests subblock, which fix v1 dropped),
and the manifest summary counts were not updated. This script:
  1. prints the template block + summary section (for the record),
  2. adds the missing keys to both new entries (tests counts zeroed —
     these files have not been executed under the access guard),
  3. recomputes summary.total_test_files from the actual entry count and
     increments the UNKNOWN category counter by the two added entries.
Idempotent.
"""
from __future__ import annotations

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
EVIDENCE = "source_inventory_only_no_dynamic_classification_claim"


def main():
    lines = open(MANIFEST).read().splitlines(keepends=True)
    starts = [i for i, ln in enumerate(lines)
              if re.match(r"^  \S.*:\s*$", ln)]
    starts.append(len(lines))

    def span(key):
        for j in range(len(starts) - 1):
            if lines[starts[j]].strip() == key + ":":
                return starts[j], starts[j + 1]
        return None

    tspan = span(TEMPLATE_KEY)
    template = lines[tspan[0]:tspan[1]]
    print("== TEMPLATE BLOCK ==")
    print("".join(template))

    test_keys = []
    in_tests = False
    for ln in template:
        if re.match(r"^    tests:\s*$", ln):
            in_tests = True
            continue
        if in_tests:
            m = re.match(r"^      ([a-z_]+):", ln)
            if m:
                test_keys.append(m.group(1))
            elif ln.strip():
                break
    print("template tests keys:", test_keys)

    for target in TARGETS:
        s = span(target)
        assert s, f"entry missing for {target}"
        block = lines[s[0]:s[1]]
        have = {ln.strip().split(":")[0] for ln in block if ln.startswith("    ")}
        add = []
        if "tests" not in have and test_keys:
            add.append("    tests:\n")
            for k in test_keys:
                add.append(f"      {k}: 0\n")
        if "evidence" not in have:
            add.append(f"    evidence: {EVIDENCE}\n")
        if add:
            lines[s[1]:s[1]] = add
            delta = len(add)
            starts = [i if i <= s[1] else i + delta for i in starts]
            print(f"{target}: added {[a.strip() for a in add]}")
        else:
            print(f"{target}: keys already complete")

    total_entries = 0
    in_files = False
    for ln in lines:
        if re.match(r"^test_files:\s*$", ln):
            in_files = True
            continue
        if in_files:
            if re.match(r"^\S", ln):
                break
            if re.match(r"^  \S.*:\s*$", ln):
                total_entries += 1
    print("counted test file entries:", total_entries)
    for i, ln in enumerate(lines):
        m = re.match(r"^(\s*total_test_files:\s*)(\d+)", ln)
        if m:
            print(f"summary total_test_files: {m.group(2)} -> {total_entries}")
            lines[i] = f"{m.group(1)}{total_entries}\n"
        m2 = re.match(r"^(\s*\w*unknown\w*:\s*)(\d+)", ln, re.IGNORECASE)
        if m2 and "summary" in "".join(lines[max(0, i - 30):i]).lower():
            new = int(m2.group(2)) + 2
            print(f"summary unknown counter: {m2.group(2)} -> {new}")
            lines[i] = f"{m2.group(1)}{new}\n"
    open(MANIFEST, "w").write("".join(lines))
    print("CLASSIFY_FIX2_DONE")


if __name__ == "__main__":
    main()
