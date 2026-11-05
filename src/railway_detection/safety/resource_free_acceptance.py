"""Source-bound resource-free test selection; classifications never grant resource rights."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
from typing import Any

SCHEMA = "resource-free-classification/1"


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def source_root(root: Path) -> None:
    project = Path(__file__).resolve().parents[3]
    absolute = root.absolute()
    for forbidden in ("data", "results", "models", "experiments", "outputs"):
        protected = project / forbidden
        if absolute == protected or protected in absolute.parents:
            raise ValueError("protected root cannot be a source inventory")
    if root.is_symlink():
        raise ValueError("source inventory root alias refused")
    resolved = root.resolve()
    for forbidden in ("data", "results", "models", "experiments", "outputs"):
        protected = project / forbidden
        if resolved == protected or protected in resolved.parents:
            raise ValueError("source inventory alias enters protected root")
    for family in ("src", "scripts", "tests", "configs"):
        if (root / family).is_symlink():
            raise ValueError("source inventory family alias refused")


def inventory(root: Path) -> list[str]:
    source_root(root)
    return sorted(str(p.relative_to(root)) for p in (root / "tests").rglob("test*.py"))


def bindings(root: Path) -> dict[str, Any]:
    files = inventory(root)
    if any((root / f).is_symlink() for f in files):
        raise ValueError("test source alias refused")
    modules = {p: hashlib.sha256((root / p).read_bytes()).hexdigest() for p in files}
    shared = {}
    for family in ("src", "scripts", "tests"):
        for p in sorted((root / family).rglob("*.py")):
            if p.is_symlink():
                raise ValueError("source alias refused before hashing")
            relative = str(p.relative_to(root))
            if relative not in modules:
                shared[relative] = hashlib.sha256(p.read_bytes()).hexdigest()
    for p in sorted((root / "configs").rglob("*")):
        if p.is_symlink():
            raise ValueError("configuration alias refused before hashing")
        if p.is_file() and p.suffix in {".yaml", ".yml", ".json"}:
            shared[str(p.relative_to(root))] = hashlib.sha256(p.read_bytes()).hexdigest()
    # Conservative whole-source closure: dynamic imports and loader defaults are included.
    return {"modules": modules, "shared_source_sha256": shared, "shared_digest": digest(shared)}


def case_node(case: dict[str, Any], files: list[str]) -> tuple[str, str]:
    for file in files:
        prefix = file[:-3].replace("/", ".")
        if case["class"] == prefix or case["class"].startswith(prefix + "."):
            suffix = case["class"][len(prefix) :].strip(".").replace(".", "::")
            return file, file + ("::" + suffix if suffix else "") + "::" + case["name"]
    raise ValueError("case has no exact module binding: " + str(case))


def source_evidence(root: Path, file: str, name: str) -> dict[str, Any]:
    text = (root / file).read_text()
    tree = ast.parse(text)
    function = next(
        (
            n
            for n in ast.walk(tree)
            if isinstance(n, ast.FunctionDef) and n.name == name.split("[")[0]
        ),
        None,
    )
    return {
        "file": file,
        "line": function.lineno if function else None,
        "function_source": ast.get_source_segment(text, function)
        if function
        else "collection error",
    }


def build_register(
    root: Path,
    receipt: dict[str, Any],
    captured: dict[str, Any],
    *,
    evidence_ref: str,
    dependency_evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    current = bindings(root)
    entries = {
        f: {
            "sha256": h,
            "classification": "UNKNOWN",
            "reason": "No current executed evidence",
            "evidence": [],
            "cases": [],
        }
        for f, h in current["modules"].items()
    }
    for group in receipt["groups"]:
        for case in group["cases"]:
            file, node = case_node(case, group["files"])
            if file not in entries:
                continue
            bound = (
                captured["modules"].get(file) == current["modules"][file]
                and captured["shared_digest"] == current["shared_digest"]
            )
            diagnostic = case.get("diagnostic", "")
            access = "UNKNOWN"
            reason = "Non-passing/unevidenced behavior requires investigation"
            if bound and case["outcome"] == "passed":
                access = "RESOURCE_FREE"
                reason = "Executed under inherited deny policy; no production resource grant"
            elif bound and ("protected_project_" in diagnostic):
                access = "PROTECTED_DEPENDENCY"
                reason = "Actual protected-path refusal in retained diagnostic; not a passing case"
            manual = (dependency_evidence or {}).get(node)
            if bound and access == "UNKNOWN" and manual:
                denials = [json.loads(row) for row in group.get("policy_denials", [])]
                if (
                    manual.get("module_sha256") == current["modules"][file]
                    and manual.get("reason")
                    and manual.get("reference")
                    and any(
                        manual.get("resource_anchor", "NEVER_MATCH") in str(d.get("detail", ""))
                        and d.get("event", "").startswith("protected_project_")
                        for d in denials
                    )
                ):
                    access = "PROTECTED_DEPENDENCY"
                    reason = (
                        manual["reason"]
                        + "; source-bound dependency evidence corroborated by fresh denial"
                    )
            if not bound:
                reason = "Changed module or shared dependency: classification defaults to UNKNOWN"
            evidence = {
                "receipt": evidence_ref,
                "group": group["group"],
                "original_outcome": case["outcome"],
                "diagnostic_sha256": digest(diagnostic),
                "source": source_evidence(root, file, case["name"]),
            }
            entries[file]["cases"].append(
                {"nodeid": node, "classification": access, "reason": reason, "evidence": evidence}
            )
    for group in receipt["groups"]:
        known = {c["nodeid"] for f in group["files"] if f in entries for c in entries[f]["cases"]}
        for node in group.get("collected_nodeids", []):
            if node not in known and node.split("::", 1)[0] in entries:
                entries[node.split("::", 1)[0]]["cases"].append(
                    {
                        "nodeid": node,
                        "classification": "UNKNOWN",
                        "reason": "Collected without executed result",
                        "evidence": {"receipt": evidence_ref, "group": group["group"]},
                    }
                )
    for item in entries.values():
        kinds = {c["classification"] for c in item["cases"]}
        item["classification"] = (
            next(iter(kinds)) if len(kinds) == 1 else "MIXED" if kinds else "UNKNOWN"
        )
        item["reason"] = (
            "Per-case executed evidence and complete module/source binding"
            if kinds
            else item["reason"]
        )
        item["evidence"] = [evidence_ref] if kinds else []
    return {
        "schema": SCHEMA,
        "shared_source_sha256": current["shared_source_sha256"],
        "shared_digest": current["shared_digest"],
        "modules": entries,
        "scope": "Profile A only; Profile B cannot be executed by this runner",
    }


def validate(root: Path, register: dict[str, Any]) -> list[str]:
    current = bindings(root)
    issues = []
    if register.get("schema") != SCHEMA:
        issues.append("Unsupported classification schema")
    old = register.get("modules", {})
    for missing in sorted(set(current["modules"]) - set(old)):
        issues.append("UNKNOWN missing module: " + missing)
    for ghost in sorted(set(old) - set(current["modules"])):
        issues.append("Removed module needs review: " + ghost)
    for file in sorted(set(old) & set(current["modules"])):
        if old[file].get("sha256") != current["modules"][file]:
            issues.append("UNKNOWN stale module: " + file)
        for case in old[file].get("cases", []):
            if (
                case.get("classification")
                not in {"RESOURCE_FREE", "PROTECTED_DEPENDENCY", "UNKNOWN"}
                or not case.get("reason")
                or not case.get("evidence")
            ):
                issues.append("Invalid evidence/classification: " + file)
            if not case.get("nodeid", "").startswith(file + "::"):
                issues.append("Invalid node/module binding: " + file)
    if register.get("shared_digest") != current["shared_digest"]:
        issues.append("UNKNOWN shared dependency changed; refresh executed evidence after review")
    return issues


def selection(register: dict[str, Any]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {"selected": [], "protected": [], "unknown": []}
    for file, item in register["modules"].items():
        if not item["cases"]:
            result["unknown"].append(file)
        for c in item["cases"]:
            key = {
                "RESOURCE_FREE": "selected",
                "PROTECTED_DEPENDENCY": "protected",
                "UNKNOWN": "unknown",
            }[c["classification"]]
            result[key].append(c["nodeid"])
    for values in result.values():
        if len(values) != len(set(values)):
            raise ValueError("Duplicate case classification")
    return result
