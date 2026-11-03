"""Explicit metadata-only input-manifest audit; never an official readiness check.

The audit parses and hashes only the manifest itself. It validates the existing
manifest contract with ``verify_sources=False`` while installing a byte-access
tripwire that permits reads only from that manifest file. This separate path is
intentionally not used by, and does not alter, the official readiness gate.
"""

from __future__ import annotations

import builtins
import io
import os
from contextlib import ExitStack, contextmanager
from pathlib import Path
from typing import Any
from unittest.mock import patch

from railway_detection.evaluation.input_contracts import (
    EvaluationInputError,
    load_evaluation_input_manifest,
)

AUDIT_MODE = "METADATA_ONLY_MANIFEST_AUDIT_NOT_OFFICIAL_READINESS"
AUDIT_MODE_VERSION = "1"
AUDIT_SCHEMA = f"metadata-only-manifest-audit/{AUDIT_MODE_VERSION}"


class MetadataOnlyIsolationError(RuntimeError):
    """Raised when this audit attempts to read any file other than its manifest."""


def _path_key(file: Any) -> str | None:
    if isinstance(file, int):
        return None
    try:
        raw = os.fsdecode(os.fspath(file))
    except TypeError:
        return None
    return os.path.normcase(os.path.abspath(raw))


@contextmanager
def _deny_non_manifest_byte_access(manifest_path: Path):
    """Tripwire common Python file-open APIs for every non-manifest path.

    Path metadata operations (stat/is_file/is_symlink/resolve) remain available;
    the manifest itself may be read. The input contract currently uses these
    APIs for byte access. Keeping the tripwire around the loader makes a future
    accidental source read fail before the open syscall succeeds.
    """
    allowed = _path_key(manifest_path.resolve())

    def guarded(api_name: str, original):
        def call(file, *args, **kwargs):
            key = _path_key(file)
            if key is not None and key != allowed:
                raise MetadataOnlyIsolationError(
                    f"metadata-only audit blocked {api_name} for non-manifest path"
                )
            if api_name in {"Path.open", "open", "io.open"}:
                mode = kwargs.get("mode", args[0] if args else "r")
                if not isinstance(mode, str) or any(flag in mode for flag in "wax+"):
                    raise MetadataOnlyIsolationError(
                        f"metadata-only audit blocked non-read mode through {api_name}"
                    )
            elif api_name == "os.open":
                flags = args[0] if args else kwargs.get("flags", os.O_RDONLY)
                if flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
                    raise MetadataOnlyIsolationError(
                        "metadata-only audit blocked non-read mode through os.open"
                    )
            return original(file, *args, **kwargs)

        return call

    with ExitStack() as stack:
        stack.enter_context(patch.object(Path, "open", guarded("Path.open", Path.open)))
        stack.enter_context(
            patch.object(Path, "read_bytes", guarded("Path.read_bytes", Path.read_bytes))
        )
        stack.enter_context(patch.object(builtins, "open", guarded("open", builtins.open)))
        stack.enter_context(patch.object(io, "open", guarded("io.open", io.open)))
        stack.enter_context(patch.object(os, "open", guarded("os.open", os.open)))
        yield


def audit_input_manifest_metadata_only(
    manifest_path: Path | str,
    *,
    repository_root: Path | str,
) -> dict[str, Any]:
    """Validate manifest metadata, reporting byte-integrity checks not performed.

    This function does not check source existence or content hashes, read source
    payloads, inspect model checkpoints, verify governance, or assess official
    evaluation readiness. Any non-manifest byte-open attempt raises
    ``MetadataOnlyIsolationError`` and produces no successful audit result.
    """
    root = Path(repository_root).resolve()
    requested_path = Path(manifest_path)
    candidate = requested_path if requested_path.is_absolute() else root / requested_path
    # Resolve before the containment check so roots reached through filesystem
    # symlinks (for example macOS /var -> /private/var) still compare correctly.
    # Symlinked manifest components remain refused by the component walk below.
    candidate = candidate.resolve()
    try:
        relative = candidate.relative_to(root)
    except ValueError as exc:
        raise EvaluationInputError(
            "MANIFEST_PATH_NOT_ALLOWED",
            "manifest path must remain beneath the supplied repository root",
        ) from exc
    if relative != Path("data/manifests/phase12_evaluation_inputs.json"):
        raise EvaluationInputError(
            "MANIFEST_PATH_NOT_ALLOWED",
            "metadata-only audit accepts only "
            "data/manifests/phase12_evaluation_inputs.json beneath repository_root",
        )
    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise EvaluationInputError(
                "MANIFEST_PATH_NOT_ALLOWED", "symlinked manifest path components are refused"
            )
    try:
        with _deny_non_manifest_byte_access(candidate):
            inputs = load_evaluation_input_manifest(candidate, verify_sources=False)
    except MetadataOnlyIsolationError:
        raise
    except EvaluationInputError:
        raise
    except OSError as exc:
        raise EvaluationInputError("MANIFEST_INVALID", f"cannot inspect {candidate}: {exc}") from exc

    return {
        "audit_schema": AUDIT_SCHEMA,
        "audit_mode": AUDIT_MODE,
        "audit_mode_version": AUDIT_MODE_VERSION,
        "overall_status": "METADATA_CONTRACT_VALID_ONLY",
        "manifest_structurally_valid": True,
        "source_media_verified": False,
        "official_evaluation_readiness": "NOT_ASSESSED",
        "readiness_prohibition": (
            "This report is a metadata-only manifest audit. It is not full integrity "
            "verification and must not be interpreted as, or used to satisfy, official "
            "Phase-12 evaluation readiness."
        ),
        "manifest": {
            "path": str(inputs.manifest_path),
            "sha256": inputs.manifest_sha256,
            "evidence_classification": inputs.evidence_classification.value,
            "event_count": len(inputs.events),
        },
        "source_bindings": [
            {
                "event_id": event.event_id,
                "cohort": event.cohort,
                "split_role": event.split_role,
                "declared_source_path": event.source_path.as_posix(),
                "declared_source_sha256": event.source_sha256,
                "source_bytes_opened": False,
                "source_digest_recomputed": False,
            }
            for event in inputs.events
        ],
        "checks_performed": [
            "manifest JSON and schema version",
            "evidence classification and split structure",
            (
                "event identity, declared SHA-256 syntax, relative path containment, symlink "
                "metadata, and duplicate paths"
            ),
            "camera-scope and accepted-sync metadata structure",
            "manifest SHA-256 only",
        ],
        "checks_not_performed": [
            "source-file existence or source-media byte integrity/hash comparison",
            "source payload decoding, parsing, viewing, playback, or inference",
            "checkpoint/model byte-integrity checks",
            "review/promotion/authorization/governance verification",
            "official Phase-12 evaluation-readiness assessment",
        ],
        "limitation": (
            "A valid result covers manifest metadata only; declared source hashes are unverified "
            "claims and this result cannot satisfy or imply official readiness."
        ),
        "provenance_limitations": [
            "declared source SHA-256 values are unverified claims; no source bytes were opened",
            "no checkpoint, model, or annotation artifact was inspected",
            "manifest structure validation is not source-media integrity verification",
            "this audit writes no reports or artifacts into evaluation or ground-truth trees",
        ],
    }