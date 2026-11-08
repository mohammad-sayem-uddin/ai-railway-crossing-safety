"""Machine-readable reproducibility and claim audit.

The audit is a pure function of repository files. It never repairs, regenerates or
fabricates anything; every item resolves to one of four statuses:

``PASS``           the repository substantiates the item;
``FAIL``           evidence exists and contradicts or violates the requirement;
``UNRESOLVED``     a required researcher decision / artifact does not exist yet;
``NOT_AVAILABLE``  the item cannot exist yet (e.g. an official result before any run).

``UNRESOLVED`` and ``NOT_AVAILABLE`` are honest states, not failures of the audit.

Manuscript claims are checked heuristically but conservatively. A sentence is flagged when
it (a) reports a metric-like number that no evidence file in the repository contains and that
carries no resolvable ``[evidence: path]`` tag, (b) uses guarantee / elimination / "proven" /
"validated" / real-time style language about system behavior without a negation or an explicit
status marker, or (c) states an event or recording count that disagrees with the annotation
inventory. Software-verification statements ("862 passed") are not empirical railway claims and
are not flagged.
"""

from __future__ import annotations

import importlib.util
import json
import re
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from railway_detection.annotation import receipt as receipt_module
from railway_detection.annotation.readiness_audit import audit_ground_truth_readiness
from railway_detection.evaluation import governance, protocol_choices
from railway_detection.optimization.benchmark_suite import artifact_fingerprints

AUDIT_SCHEMA = "reproducibility-audit/1"
PASS, FAIL, UNRESOLVED, NOT_AVAILABLE = "PASS", "FAIL", "UNRESOLVED", "NOT_AVAILABLE"

REQUIRED_DATASET_MANIFESTS = (
    "data/manifests/layer_b_v2_annotation_inventory.json",
    "data/manifests/real_world_v2_video_manifest.json",
    "data/manifests/train_horn_audio_manifest.json",
    "data/manifests/camera_sync_offsets_candidate.yaml",
)
DEFAULT_MANUSCRIPTS = (
    "docs/PHASE16_MANUSCRIPT_DRAFT.md",
    "docs/PHASE16_MANUSCRIPT_CORRECTION_v1.md",
)
HISTORICAL_MANUSCRIPTS = ("Railway_Crossing_Automation_Research_Report.docx",)
EVIDENCE_GLOBS = (
    "experiments/*/evaluation/*.json",
    "experiments/*/evaluation/*.md",
    "experiments/*/*/metrics/*.json",
    "experiments/*/*/reports/*.json",
    "experiments/*/*/evaluation/*.json",
    "reports/*.md",
)
MAX_EVIDENCE_BYTES = 4_000_000

# --------------------------------------------------------------------------- claim scanner

_METRIC_WORDS = re.compile(
    r"\b(map|accuracy|precision|recall|f1|auc|roc|latency|fps|throughput|false[- ]alarm|"
    r"miss(?:ed)?[- ]train|premature|lead time|clearance|confidence interval|ci|error)\b",
    re.I,
)
_NUMBER = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)\s*(%|ms|s\b|fps)?")
_OVERCLAIM = re.compile(
    r"\b(guarantee[sd]?|eliminat(?:e|es|ed|ing)\b[^.]{0,40}\b(?:risk|premature|opening|failure)s?|"
    r"flawless(?:ly)?|proven|prove[sd]?|deployment[- ]ready|state[- ]of[- ]the[- ]art|"
    r"outperform(?:s|ed)?|real[- ]time (?:capable|performance|operation)|"
    r"successfully (?:designed|implemented|validated)|safe(?:ly)? operat\w+)\b",
    re.I,
)
_NEGATION = re.compile(
    r"\b(no|not|never|cannot|can't|without|must not|do(?:es)? not|did not|has not|have not|"
    r"nor|none|"
    r"unsupported|unproven|unvalidated|prohibited|forbidden|disclaim\w*|limitation\w*|"
    r"no claim|not claimed|not asserted)\b",
    re.I,
)
_STATUS_MARKERS = re.compile(
    r"(NOT OBTAINED|NOT RUN|NOT AVAILABLE|UNRESOLVED|SYNTHETIC|PLANNED|HISTORICAL|"
    r"BLOCKED|PENDING|UNSET|NOT PRODUCED|NOT COMPUTED|Candidate sources only)"
)
_EVIDENCE_TAG = re.compile(r"\[evidence:\s*([^\]]+)\]")
_COUNT = re.compile(
    r"\b(\d+)\s+(?:active\s+|full[- ]train\s+|no[- ]train\s+|engine[- ]only\s+|paired\s+"
    r"|layer b\s+)?"
    r"(events?|recordings?|passages?)\b",
    re.I,
)
_TEST_STATUS = re.compile(r"\b(passed|failed|tests?|pytest|ruff)\b", re.I)


def _decimals(token: str) -> int:
    return len(token.split(".")[1]) if "." in token else 0


def _extract_floats(text: str) -> set[float]:
    values: set[float] = set()
    for match in re.finditer(r"-?\d+(?:\.\d+)?(?:[eE]-?\d+)?", text):
        try:
            values.add(float(match.group(0)))
        except ValueError:
            continue
    return values


def _supported(number: str, unit: str | None, evidence: set[float]) -> bool:
    value, places = float(number), _decimals(number)
    tolerance = 0.5 * 10 ** (-places) + 1e-9
    candidates = [value]
    if unit == "%":
        candidates.append(value / 100.0)
    for candidate in candidates:
        tol = tolerance if candidate == value else tolerance / 100.0
        if any(abs(candidate - item) <= tol for item in evidence):
            return True
    return False


def _sentences(text: str) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        for part in re.split(r"(?<=[.!?])\s+|•|\u2022", line):
            if part.strip():
                out.append((line_no, part.strip()))
    return out


def scan_manuscript_claims(
    text: str,
    *,
    source: str,
    evidence_numbers: set[float],
    allowed_counts: set[int],
    root: Path | None = None,
) -> list[dict[str, Any]]:
    """Flag unsupported empirical numbers, overclaims and dataset-count mismatches."""
    findings: list[dict[str, Any]] = []
    for line_no, sentence in _sentences(text):
        marked = bool(_STATUS_MARKERS.search(sentence))
        negated = bool(_NEGATION.search(sentence))
        tag = _EVIDENCE_TAG.search(re.sub(r"`[^`]*`", "", sentence))  # not inside code spans
        tag_ok = bool(tag and root is not None and (root / tag.group(1).strip()).exists())
        if tag and not tag_ok:
            findings.append(
                _finding(
                    "BROKEN_EVIDENCE_TAG",
                    source,
                    line_no,
                    sentence,
                    f"evidence path {tag.group(1).strip()!r} does not exist",
                )
            )
        if _OVERCLAIM.search(sentence) and not (marked or negated or tag_ok):
            findings.append(
                _finding(
                    "OVERCLAIM_LANGUAGE",
                    source,
                    line_no,
                    sentence,
                    "guarantee/elimination/validation/real-time style claim with "
                    "no hedge, negation, status marker or resolvable evidence tag",
                )
            )
        if _METRIC_WORDS.search(sentence) and not _TEST_STATUS.search(sentence):
            for number, unit in _NUMBER.findall(sentence):
                if unit not in ("%", "ms", "fps") and _decimals(number) == 0:
                    continue  # bare integers are handled as counts, not metric values
                if marked or negated or tag_ok:
                    continue
                if not _supported(number, unit or None, evidence_numbers):
                    findings.append(
                        _finding(
                            "UNSUPPORTED_EMPIRICAL_NUMBER",
                            source,
                            line_no,
                            sentence,
                            f"{number}{unit or ''} appears in no evidence file; no evidence tag",
                        )
                    )
        for count, _noun in _COUNT.findall(sentence):
            if int(count) not in allowed_counts and not (marked or negated):
                findings.append(
                    _finding(
                        "DATASET_COUNT_MISMATCH",
                        source,
                        line_no,
                        sentence,
                        f"{count} is not a count supported by the annotation inventory "
                        f"{sorted(allowed_counts)}",
                    )
                )
    return findings


def _finding(code: str, source: str, line: int, sentence: str, detail: str) -> dict[str, Any]:
    return {"code": code, "source": source, "line": line, "text": sentence[:240], "detail": detail}


def _manuscript_text(path: Path) -> str | None:
    if not path.is_file():
        return None
    if path.suffix.lower() == ".docx":
        with zipfile.ZipFile(path) as archive:
            xml = archive.read("word/document.xml").decode("utf-8", errors="replace")
        text = re.sub(r"</w:p>", "\n", xml)
        text = re.sub(r"<[^>]+>", "", text)
        return text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    return path.read_text(encoding="utf-8", errors="replace")


def _evidence_numbers(root: Path) -> tuple[set[float], list[str]]:
    values: set[float] = set()
    files: list[str] = []
    for pattern in EVIDENCE_GLOBS:
        for path in sorted(root.glob(pattern)):
            if path.is_file() and path.stat().st_size <= MAX_EVIDENCE_BYTES:
                values |= _extract_floats(path.read_text(encoding="utf-8", errors="replace"))
                files.append(path.relative_to(root).as_posix())
    return values, files


# --------------------------------------------------------------------------------- the audit


def _item(item_id: str, status: str, detail: str, **evidence: Any) -> dict[str, Any]:
    return {"id": item_id, "status": status, "detail": detail, "evidence": evidence}


def _sha256(path: Path) -> str:
    return receipt_module.sha256_file(path)


def _dataset_manifests(root: Path) -> dict[str, Any]:
    entries, missing = {}, []
    for relative in REQUIRED_DATASET_MANIFESTS:
        path = root / relative
        if not path.is_file():
            missing.append(relative)
            continue
        entries[relative] = _sha256(path)
    return _item(
        "dataset_manifests",
        FAIL if missing else PASS,
        f"missing: {missing}" if missing else "all required manifests present and hashed",
        manifests=entries,
        missing=missing,
    )


def _inventory_counts(root: Path) -> tuple[dict[str, int], set[int]]:
    path = root / receipt_module.DEFAULT_INVENTORY_RELATIVE
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}, set()
    by_cohort: dict[str, int] = {}
    for entry in raw.values():
        cohort = entry.get("category", "unknown")
        by_cohort[cohort] = by_cohort.get(cohort, 0) + 1
    total = sum(by_cohort.values())
    allowed = {total, *by_cohort.values(), total * 2}  # events and their two camera streams
    supported = governance.calibration_supported_events(root)
    if supported is not None:
        allowed |= {len(supported), total - len(supported)}
    return by_cohort, allowed


def _environment(root: Path) -> list[dict[str, Any]]:
    import importlib.metadata as metadata

    items: list[dict[str, Any]] = []
    lock = root / "requirements.lock"
    if not lock.is_file():
        return [_item("dependency_lock", FAIL, "requirements.lock is missing")]
    pins = dict(
        line.strip().split("==", 1)
        for line in lock.read_text().splitlines()
        if "==" in line and not line.startswith("#")
    )
    mismatches = {}
    for name, version in pins.items():
        try:
            installed = metadata.version(name)
        except metadata.PackageNotFoundError:
            continue
        if installed != version:
            mismatches[name] = {"locked": version, "installed": installed}
    items.append(
        _item(
            "dependency_lock",
            FAIL if mismatches else PASS,
            f"{len(mismatches)} locked package(s) differ from the installed version"
            if mismatches
            else f"{len(pins)} pinned packages agree with the installed versions",
            lock_sha256=_sha256(lock),
            mismatches=mismatches,
        )
    )
    spec = importlib.util.find_spec("ultralytics")
    broken = spec is not None and spec.origin is None
    items.append(
        _item(
            "ultralytics_importable",
            FAIL if (spec is None or broken) else PASS,
            "ultralytics resolves to a namespace directory without __init__.py; the frozen vision "
            "model cannot be loaded in this environment"
            if broken
            else ("ultralytics is not installed" if spec is None else "ultralytics importable"),
            origin=None if spec is None else spec.origin,
        )
    )
    return items


def _result_provenance(root: Path, result_dirs: list[Path]) -> dict[str, Any]:
    if not result_dirs:
        return _item(
            "evaluation_result_provenance",
            NOT_AVAILABLE,
            "no official evaluation result exists; none is claimed",
        )
    live = governance.EVAL_AUTH_RELATIVE
    auth_sha = _sha256(root / live) if (root / live).is_file() else None
    problems: list[str] = []
    verified: list[str] = []
    for directory in result_dirs:
        manifest_path = directory / "run_manifest.json"
        if not manifest_path.is_file():
            problems.append(f"{directory}: run_manifest.json missing")
            continue
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        prov = manifest.get("provenance", {})
        checks = {
            "evidence_classification real": manifest.get("evidence_classification") == "real",
            "authorization verified": str(manifest.get("authorization_status", "")).startswith(
                "verified:"
            ),
            "authorization record present": bool(auth_sha)
            and manifest.get("authorization_record_sha256") == auth_sha,
            "input manifest hash": bool(prov.get("input_manifest_sha256")),
            "frozen config hash": bool(prov.get("frozen_config_sha256")),
            "decision policy hash": bool(prov.get("decision_policy_sha256")),
            "checkpoint hashes": bool(prov.get("checkpoint_sha256")),
            "contract versions": bool(manifest.get("contract_versions")),
            "premature window decided": manifest.get("premature_opening_window")
            not in (None, "undecided"),
            "replay provenance": bool(manifest.get("replay_provenance")),
        }
        bad = [name for name, ok in checks.items() if not ok]
        (problems if bad else verified).append(
            f"{directory}: " + (f"missing/invalid {bad}" if bad else "complete")
        )
    return _item(
        "evaluation_result_provenance",
        FAIL if problems else PASS,
        "; ".join(problems or verified),
        results=[str(d) for d in result_dirs],
    )


def run_reproducibility_audit(
    root: Path | str,
    *,
    manuscripts: tuple[str, ...] = DEFAULT_MANUSCRIPTS,
    result_dirs: list[Path] | None = None,
    experiment_manifests: list[Path] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    base = Path(root).resolve()
    now = now or datetime.now(UTC)
    items: list[dict[str, Any]] = []

    items.append(_dataset_manifests(base))

    gt = audit_ground_truth_readiness(base)
    eligible = gt["summary"]["promotion_eligible_pending_media_rehash"]
    items.append(
        _item(
            "approved_ground_truth",
            PASS if eligible and gt["promotion_receipt"]["status"] == "valid" else UNRESOLVED,
            f"{gt['summary']['stage21_records']} valid Stage-2.1 record(s), {eligible} eligible; "
            f"receipt: {gt['promotion_receipt']['status']}; legacy records are never ground truth",
            schema_versions=gt["summary"]["schema_versions"],
            legacy_records=gt["legacy"]["summary"]["record_count"],
        )
    )

    protocol_docs = {
        "protocol_v9": "docs/FINAL_REAL_WORLD_EXPERIMENT_PROTOCOL.md",
        "ground_truth_protocol": "docs/FINAL_GROUND_TRUTH_PROTOCOL.md",
        "design": "docs/EXPERIMENT_DESIGN_FINAL.md",
    }
    present = {k: _sha256(base / v) for k, v in protocol_docs.items() if (base / v).is_file()}
    unresolved_defs = protocol_choices.unresolved_decisions(None)
    items.append(
        _item(
            "protocol_version",
            UNRESOLVED if unresolved_defs else PASS,
            f"unresolved protocol definitions: {unresolved_defs}"
            if unresolved_defs
            else "all protocol definitions decided",
            documents=present,
            unresolved_definitions=unresolved_defs,
        )
    )

    split_path = base / governance.SPLIT_DECISION_RELATIVE
    items.append(
        _item(
            "event_split_decision",
            PASS if split_path.is_file() else UNRESOLVED,
            "event-level split decision recorded (verification is the readiness gate's job)"
            if split_path.is_file()
            else "no event-level split decision exists; none is invented",
            sha256=_sha256(split_path) if split_path.is_file() else None,
        )
    )
    r04 = base / governance.R04_DECISION_RELATIVE
    items.append(
        _item(
            "r04_scope_decision",
            PASS if r04.is_file() else UNRESOLVED,
            "R04 scope decision recorded" if r04.is_file() else "no R04 scope decision recorded",
            candidates=governance.documented_r04_candidates(base),
        )
    )

    try:
        fp = artifact_fingerprints(base)
    except Exception as exc:  # noqa: BLE001 - an unreadable config is itself a finding
        items.append(
            _item(
                "model_checkpoint_fingerprints",
                FAIL,
                f"frozen configuration or policy unreadable: {type(exc).__name__}: {exc}",
            )
        )
        items.append(_item("config_and_policy_fingerprints", FAIL, "unavailable (see above)"))
    else:
        items.append(
            _item(
                "model_checkpoint_fingerprints",
                PASS if fp["verified"] else FAIL,
                "checkpoints match the frozen configuration"
                if fp["verified"]
                else "a checkpoint differs from the frozen configuration, or Audio V2 is present",
                checkpoints=fp["checkpoints"],
            )
        )
        items.append(
            _item(
                "config_and_policy_fingerprints",
                PASS,
                "raw-byte and canonical-content hashes recorded for both (they answer different "
                "questions: Phase 5 cited the canonical policy hash)",
                frozen_config=fp["frozen_config"],
                decision_policy=fp["decision_policy"],
            )
        )

    items.append(_result_provenance(base, list(result_dirs or [])))

    manifests = list(experiment_manifests or [])
    if manifests:
        bad = []
        for path in manifests:
            data = json.loads(path.read_text(encoding="utf-8"))
            need = (
                "plan",
                "input_sha256_by_event",
                "run_id",
                "status",
                "failures",
                "empirical_performance_claim",
            )
            bad += [f"{path}: missing {k}" for k in need if k not in data]
            if data.get("empirical_performance_claim") is not False:
                bad.append(f"{path}: empirical_performance_claim is not false")
        items.append(
            _item(
                "experiment_manifest_completeness",
                FAIL if bad else PASS,
                "; ".join(bad) or "complete",
                manifests=[str(m) for m in manifests],
            )
        )
    else:
        items.append(
            _item(
                "experiment_manifest_completeness",
                NOT_AVAILABLE,
                "no experiment manifest supplied; no official Phase 13 experiment exists",
            )
        )

    items.extend(_environment(base))

    auth = base / governance.EVAL_AUTH_RELATIVE
    leg_exec = gt["leg_exec_preflight"]
    if leg_exec.get("execution_authorized"):
        leg_exec_status = "AUTHORIZED (verified operation-specific recorded statement)"
    else:
        leg_exec_status = "NOT AUTHORIZED (inputs verified by preflight; no valid authorization)"
    unresolved_register = {
        "premature_opening_window": "UNRESOLVED (v9 vs M4; no researcher-attributed acceptance)",
        "event_level_split": "recorded" if split_path.is_file() else "UNRESOLVED",
        "r04_camera_scope": "recorded" if r04.is_file() else "UNRESOLVED",
        "stage21_ground_truth": "present" if eligible else "NOT OBTAINED (0 valid records)",
        "eval_auth": "recorded" if auth.is_file() else "NOT RECORDED",
        "leg_exec": leg_exec_status,
        "d1_review_duration_thresholds": "UNRESOLVED",
        "d3c_clear_boundary_audit": "UNRESOLVED",
    }
    items.append(
        _item(
            "unresolved_decisions",
            UNRESOLVED,
            "decisions still required of the researcher",
            register=unresolved_register,
        )
    )

    # --- active manuscript claims vs evidence
    evidence_numbers, evidence_files = _evidence_numbers(base)
    by_cohort, allowed_counts = _inventory_counts(base)
    findings: list[dict[str, Any]] = []
    scanned: list[str] = []
    for relative in manuscripts:
        text = _manuscript_text(base / relative)
        if text is None:
            continue
        scanned.append(relative)
        findings += scan_manuscript_claims(
            text,
            source=relative,
            evidence_numbers=evidence_numbers,
            allowed_counts=allowed_counts,
            root=base,
        )

    # Preserve the historical claim audit without treating an immutable source
    # artifact as the active manuscript after an additive correction exists.
    # The archived findings remain visible in both machine- and human-readable
    # reports; they are not rewritten or discarded.
    historical_findings: list[dict[str, Any]] = []
    historical_scanned: list[str] = []
    for relative in HISTORICAL_MANUSCRIPTS:
        text = _manuscript_text(base / relative)
        if text is None:
            continue
        historical_scanned.append(relative)
        historical_findings += scan_manuscript_claims(
            text,
            source=relative,
            evidence_numbers=evidence_numbers,
            allowed_counts=allowed_counts,
            root=base,
        )
    items.append(
        _item(
            "manuscript_claims_vs_evidence",
            FAIL if findings else PASS,
            f"{len(findings)} unsupported or overreaching statement(s) in {scanned}"
            if findings
            else f"no unsupported statements found in {scanned}",
            scanned=scanned,
            historical_scanned=historical_scanned,
            historical_findings=len(historical_findings),
            evidence_files=len(evidence_files),
            inventory_counts=by_cohort,
        )
    )

    status_counts: dict[str, int] = {}
    for item in items:
        status_counts[item["status"]] = status_counts.get(item["status"], 0) + 1
    return {
        "schema_version": AUDIT_SCHEMA,
        "generated_at_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "read_only": True,
        "status_counts": dict(sorted(status_counts.items())),
        "items": items,
        "claim_findings": findings,
        "historical_claim_audit_status": FAIL if historical_findings else PASS,
        "historical_source_disposition": "preserved_with_findings",
        "historical_claim_findings": historical_findings,
        "evidence_classes": {
            "implemented_software": "present (see tests)",
            "synthetic_tests": "present; never research evidence",
            "real_data_evaluation": "NOT OBTAINED" if not result_dirs else "supplied",
            "target_hardware_measurement": "NOT OBTAINED (no target platform declared)",
            "controlled_validation": "NOT OBTAINED (no field session has occurred)",
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Reproducibility Audit",
        "",
        f"Generated {report['generated_at_utc']} from repository files only (read-only).",
        "",
        f"Status counts: {report['status_counts']}",
        "",
        "## Evidence classes",
        *[f"- **{k}**: {v}" for k, v in report["evidence_classes"].items()],
        "",
        "## Items",
        "| Item | Status | Detail |",
        "|---|---|---|",
    ]
    for item in report["items"]:
        detail = item["detail"].replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {item['id']} | **{item['status']}** | {detail} |")
    lines += ["", "## Active manuscript findings"]
    if not report["claim_findings"]:
        lines.append("None found.")
    for finding in report["claim_findings"]:
        lines.append(
            f"- `{finding['code']}` {finding['source']}:{finding['line']} — {finding['detail']}\n"
            f"  > {finding['text']}"
        )
    historical_findings = report.get("historical_claim_findings", [])
    historical_status = report.get("historical_claim_audit_status", "NOT_REPORTED")
    historical_disposition = report.get("historical_source_disposition", "NOT_REPORTED")
    lines += [
        "",
        "## Historical source findings (preserved; not the active manuscript)",
        f"Archival audit status: **{historical_status}**; disposition: "
        f"**{historical_disposition}**. These findings remain attached to the immutable "
        "historical artifact and are not silently removed from the audit.",
    ]
    if not historical_findings:
        lines.append("None found.")
    for finding in historical_findings:
        lines.append(
            f"- `{finding['code']}` {finding['source']}:{finding['line']} — {finding['detail']}\n"
            f"  > {finding['text']}"
        )
    return "\n".join(lines) + "\n"
