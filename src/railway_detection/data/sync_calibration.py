"""R04 cross-camera calibration acceptance rule.

Applies ONE predeclared, deterministic rule to raw GCC-PHAT diagnostics
(`scripts/estimate_camera_sync_offsets.py` output) to classify each event's
calibration candidate as CALIBRATION_SUPPORTED, PROVISIONAL, AMBIGUOUS,
FAILED, or NOT_ASSESSABLE.

The rule is applied identically to every event by this module -- it is never
hand-adjusted per event to preserve a desired outcome. Changing a threshold
here changes the verdict for every event simultaneously and must be done
before classification, not after seeing which events it would flag.

Thresholds (frozen for this classification pass; see
docs/R04_CALIBRATION_VALIDATION_REPORT.md section "Reconciled Acceptance
Rule" for the rationale behind each number):

  SUPPORTED   : psr >= 2.0  AND window_range_s <= 0.20  AND snr >= 15.0
                AND |lag_s - qt_delta_s| <= 1.5   (sanity bound; QuickTime
                device-clock drift of tens of seconds is handled by passing
                the *acoustic* lag through this check, not the raw QT delta --
                see `metadata_sanity_note`)
  PROVISIONAL : psr >= 1.3  AND window_range_s <= 1.00  AND snr >= 10.0
                AND |lag_s - qt_delta_s| <= 5.0
  AMBIGUOUS   : anything else that produced a finite lag estimate
  FAILED      : the estimator raised an error (e.g. empty/corrupt audio) or
                returned a non-finite lag
  NOT_ASSESSABLE : no diagnostic record exists for the event at all

Uncertainty is reported, never fabricated: SUPPORTED carries an explicit
+/-0.05s acoustic-geometry-bounded figure ONLY as an upper bound on sub-frame
jitter -- it is NOT a claim that device clock offset is known to that
precision (see the physical-factors discussion in the report). PROVISIONAL
and AMBIGUOUS carry `uncertainty_s: "unknown"` rather than an invented sigma.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Literal
from railway_detection.safety.media_guard import require_media_authorization

Verdict = Literal[
    "CALIBRATION_SUPPORTED", "PROVISIONAL", "AMBIGUOUS", "FAILED", "NOT_ASSESSABLE"
]

# Frozen thresholds -- see module docstring. Do not tune per event.
SUPPORTED_MIN_PSR = 2.0
SUPPORTED_MAX_WINDOW_RANGE_S = 0.20
SUPPORTED_MIN_SNR = 15.0
SUPPORTED_MAX_QT_DISAGREEMENT_S = 1.5

PROVISIONAL_MIN_PSR = 1.3
PROVISIONAL_MAX_WINDOW_RANGE_S = 1.00
PROVISIONAL_MIN_SNR = 10.0
PROVISIONAL_MAX_QT_DISAGREEMENT_S = 5.0

# Upper bound on sub-frame jitter from acoustic path geometry alone (NOT a
# claim about overall calibration uncertainty -- see physical-factors note).
SUPPORTED_GEOMETRIC_JITTER_BOUND_S = 0.05


@dataclass(frozen=True)
class CorroborationRecord:
    """Independent empirical corroboration for an inter-camera sync offset.

    Used when device wall-clock metadata (e.g. QuickTime creationdate) is known
    to be corrupted or desynchronized by tens of seconds, so that an empirical
    external source (e.g. human visual-landmark alignment or surveyed passage)
    can serve as the independent sanity corroboration required by safety invariant.
    """

    source: str
    verified: bool
    candidate_offset_s: float
    tolerance_s: float = 0.50
    reviewer: str | None = None
    evidence_provenance: str | None = None
    notes: str | None = None

    def validate(self) -> list[str]:
        """Validate that this corroboration record satisfies all authenticity and integrity constraints."""
        errors: list[str] = []
        if self.verified is not True:
            errors.append("verification status is not True (must be explicitly boolean True)")
        if not self.reviewer or not self.reviewer.strip():
            errors.append("reviewer identity is required and cannot be empty")
        elif self.reviewer.strip().lower() in {
            "agent", "assistant", "ai", "automated", "synthetic",
            "bot", "self", "none", "unknown", "unspecified", "auto",
        }:
            errors.append(
                f"reviewer '{self.reviewer}' is a prohibited automated/unspecified identity; "
                "must be a verified human practitioner"
            )
        if not self.evidence_provenance or not self.evidence_provenance.strip():
            errors.append(
                "evidence_provenance is required (must reference review artifact path or sha256)"
            )
        valid_sources = {
            "visual_landmark",
            "site_survey",
            "physical_transit",
            "audio_visual_fiducial",
        }
        if not self.source or self.source not in valid_sources:
            errors.append(
                f"source '{self.source}' is invalid; must be one of {sorted(valid_sources)}"
            )
        if not _is_finite(self.candidate_offset_s):
            errors.append("candidate_offset_s must be a finite float")
        if not _is_finite(self.tolerance_s) or self.tolerance_s <= 0.0 or self.tolerance_s > 1.0:
            errors.append("tolerance_s must be a positive finite float <= 1.00s")
        return errors

    @property
    def is_valid(self) -> bool:
        return len(self.validate()) == 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CorroborationRecord:
        """Construct CorroborationRecord from a dictionary."""
        return cls(
            source=str(data.get("source", "")),
            verified=bool(data.get("verified", False)),
            candidate_offset_s=float(data.get("candidate_offset_s", float("nan"))),
            tolerance_s=float(data.get("tolerance_s", 0.50)),
            reviewer=str(data.get("reviewer")) if data.get("reviewer") is not None else None,
            evidence_provenance=str(data.get("evidence_provenance"))
            if data.get("evidence_provenance") is not None
            else None,
            notes=str(data.get("notes")) if data.get("notes") is not None else None,
        )


def diagnose_sidelobe_mode(
    lag_s: float | None,
    secondary_lag_s: float | None,
    psr: float | None,
    snr: float | None,
    window_range_s: float | None,
    qt_disagreement_s: float | None,
) -> str:
    """Diagnose the root physical or algorithmic mechanism for an event's calibration status.

    Returns one of:
      - 'NOT_ASSESSABLE': missing diagnostics
      - 'SUPPORTED': meets all supported criteria
      - 'CORRELATION_DECORRELATION': flat correlation (PSR < 1.10 or SNR < 10.0)
      - 'TEMPORAL_WINDOW_DRIFT': sub-window lag instability (window_range_s > 1.0)
      - 'COMPETING_MULTIPATH': competing acoustic peaks causing window hopping (window_range_s > 0.20 and psr < 1.30)
      - 'METADATA_CLOCK_DISCREPANCY': clean acoustics blocked solely by container clock jump (|lag - QT| > 1.5)
      - 'ADJACENT_SHOULDER': secondary peak within 100 ms of primary peak (reverberation skirt)
      - 'HARMONIC_PERIODICITY': secondary peak > 100 ms with sub-50 ms window stability (rail axle/engine harmonics)
      - 'MODERATE_ACOUSTIC_MARGIN': provisional acoustics without distinct structural failure
    """
    if lag_s is None or not _is_finite(lag_s):
        return "NOT_ASSESSABLE"

    psr_val = float(psr) if (psr is not None and _is_finite(psr)) else 0.0
    snr_val = float(snr) if (snr is not None and _is_finite(snr)) else 0.0
    win_range = (
        float(window_range_s)
        if (window_range_s is not None and _is_finite(window_range_s))
        else float("inf")
    )
    qt_dis = (
        float(qt_disagreement_s)
        if (qt_disagreement_s is not None and _is_finite(qt_disagreement_s))
        else None
    )

    if (
        psr_val >= SUPPORTED_MIN_PSR
        and win_range <= SUPPORTED_MAX_WINDOW_RANGE_S
        and snr_val >= SUPPORTED_MIN_SNR
        and qt_dis is not None
        and qt_dis <= SUPPORTED_MAX_QT_DISAGREEMENT_S
    ):
        return "SUPPORTED"

    if psr_val < 1.10 or snr_val < 10.0:
        return "CORRELATION_DECORRELATION"

    if win_range > PROVISIONAL_MAX_WINDOW_RANGE_S:
        return "TEMPORAL_WINDOW_DRIFT"

    if (
        psr_val >= SUPPORTED_MIN_PSR
        and win_range <= SUPPORTED_MAX_WINDOW_RANGE_S
        and snr_val >= SUPPORTED_MIN_SNR
        and (qt_dis is None or qt_dis > SUPPORTED_MAX_QT_DISAGREEMENT_S)
    ):
        return "METADATA_CLOCK_DISCREPANCY"

    if win_range > SUPPORTED_MAX_WINDOW_RANGE_S and psr_val < PROVISIONAL_MIN_PSR:
        return "COMPETING_MULTIPATH"

    if secondary_lag_s is not None and _is_finite(secondary_lag_s):
        sec_dist = abs(float(secondary_lag_s) - lag_s)
        if sec_dist <= 0.100:
            return "ADJACENT_SHOULDER"
        if win_range <= 0.050:
            return "HARMONIC_PERIODICITY"

    return "MODERATE_ACOUSTIC_MARGIN"


@dataclass(frozen=True)
class CalibrationVerdict:
    event_key: str
    verdict: Verdict
    lag_s: float | None
    qt_delta_s: float | None
    qt_disagreement_s: float | None
    psr: float | None
    snr: float | None
    window_range_s: float | None
    uncertainty_s: float | str
    reasons: tuple[str, ...]


def _is_finite(x: Any) -> bool:
    try:
        return math.isfinite(float(x))
    except (TypeError, ValueError):
        return False


def classify_event(
    event_key: str,
    diagnostics: dict[str, Any] | None,
    qt_delta_s: float | None,
    corroboration: dict[str, Any] | CorroborationRecord | None = None,
) -> CalibrationVerdict:
    """Apply the single frozen acceptance rule to one event's raw diagnostics."""
    if diagnostics is None:
        return CalibrationVerdict(
            event_key=event_key,
            verdict="NOT_ASSESSABLE",
            lag_s=None,
            qt_delta_s=qt_delta_s,
            qt_disagreement_s=None,
            psr=None,
            snr=None,
            window_range_s=None,
            uncertainty_s="unknown",
            reasons=("no diagnostic record available for this event",),
        )

    if "error" in diagnostics or not _is_finite(diagnostics.get("lag_s")):
        return CalibrationVerdict(
            event_key=event_key,
            verdict="FAILED",
            lag_s=None,
            qt_delta_s=qt_delta_s,
            qt_disagreement_s=None,
            psr=None,
            snr=None,
            window_range_s=None,
            uncertainty_s="unknown",
            reasons=(diagnostics.get("error", "non-finite lag estimate"),),
        )

    lag_s = float(diagnostics["lag_s"])
    psr = float(diagnostics["psr"]) if _is_finite(diagnostics.get("psr")) else 0.0
    snr = float(diagnostics["snr"]) if _is_finite(diagnostics.get("snr")) else 0.0
    window_range_s = (
        float(diagnostics["window_range_s"])
        if _is_finite(diagnostics.get("window_range_s"))
        else float("inf")
    )

    qt_disagreement_s = None
    if qt_delta_s is not None and _is_finite(qt_delta_s):
        qt_disagreement_s = abs(lag_s - float(qt_delta_s))

    # Evaluate independent corroboration (e.g. human visual landmark verification)
    is_corroborated = False
    corroboration_note: str | None = None
    if corroboration is not None:
        if isinstance(corroboration, CorroborationRecord):
            corrob_record = corroboration
        elif isinstance(corroboration, dict):
            corrob_record = CorroborationRecord.from_dict(corroboration)
        else:
            corrob_record = None

        if corrob_record is None:
            corroboration_note = "external corroboration rejected: invalid record type"
        else:
            validation_errors = corrob_record.validate()
            if validation_errors:
                is_corroborated = False
                corroboration_note = (
                    f"external corroboration rejected (validation failed: {'; '.join(validation_errors)})"
                )
            else:
                c_offset = corrob_record.candidate_offset_s
                c_tol = corrob_record.tolerance_s
                discrepancy = abs(lag_s - c_offset)
                if discrepancy <= c_tol:
                    is_corroborated = True
                    corroboration_note = (
                        f"external corroboration verified by {corrob_record.reviewer} via {corrob_record.source} "
                        f"[provenance: {corrob_record.evidence_provenance}] "
                        f"(candidate={c_offset:.4f}s, delta={discrepancy:.3f}s<={c_tol:.2f}s)"
                    )
                else:
                    is_corroborated = False
                    corroboration_note = (
                        f"external corroboration rejected: lag {lag_s:.4f}s differs from "
                        f"{corrob_record.source} candidate {c_offset:.4f}s by {discrepancy:.3f}s > {c_tol:.2f}s"
                    )

    reasons: list[str] = []

    metadata_supported = (
        (qt_disagreement_s is not None and qt_disagreement_s <= SUPPORTED_MAX_QT_DISAGREEMENT_S)
        or is_corroborated
    )
    metadata_provisional = (
        qt_disagreement_s is None
        or qt_disagreement_s <= PROVISIONAL_MAX_QT_DISAGREEMENT_S
        or is_corroborated
    )

    supported = (
        psr >= SUPPORTED_MIN_PSR
        and window_range_s <= SUPPORTED_MAX_WINDOW_RANGE_S
        and snr >= SUPPORTED_MIN_SNR
        and metadata_supported
    )
    if supported:
        if is_corroborated and (
            qt_disagreement_s is None or qt_disagreement_s > SUPPORTED_MAX_QT_DISAGREEMENT_S
        ):
            reasons.append(
                f"psr={psr:.2f}>={SUPPORTED_MIN_PSR}, "
                f"window_range_s={window_range_s:.3f}<={SUPPORTED_MAX_WINDOW_RANGE_S}, "
                f"snr={snr:.1f}>={SUPPORTED_MIN_SNR}, "
                f"{corroboration_note}"
            )
        else:
            reasons.append(
                f"psr={psr:.2f}>={SUPPORTED_MIN_PSR}, "
                f"window_range_s={window_range_s:.3f}<={SUPPORTED_MAX_WINDOW_RANGE_S}, "
                f"snr={snr:.1f}>={SUPPORTED_MIN_SNR}, "
                f"qt_disagreement_s={qt_disagreement_s:.2f}<={SUPPORTED_MAX_QT_DISAGREEMENT_S}"
            )
        return CalibrationVerdict(
            event_key=event_key,
            verdict="CALIBRATION_SUPPORTED",
            lag_s=lag_s,
            qt_delta_s=qt_delta_s,
            qt_disagreement_s=qt_disagreement_s,
            psr=psr,
            snr=snr,
            window_range_s=window_range_s,
            uncertainty_s=SUPPORTED_GEOMETRIC_JITTER_BOUND_S,
            reasons=tuple(reasons),
        )

    provisional = (
        psr >= PROVISIONAL_MIN_PSR
        and window_range_s <= PROVISIONAL_MAX_WINDOW_RANGE_S
        and snr >= PROVISIONAL_MIN_SNR
        and metadata_provisional
    )
    if provisional:
        reasons.append(
            f"psr={psr:.2f} in [{PROVISIONAL_MIN_PSR},{SUPPORTED_MIN_PSR}) or "
            f"window_range_s={window_range_s:.3f} in "
            f"({SUPPORTED_MAX_WINDOW_RANGE_S},{PROVISIONAL_MAX_WINDOW_RANGE_S}] or "
            f"snr={snr:.1f} in [{PROVISIONAL_MIN_SNR},{SUPPORTED_MIN_SNR}); "
            "does not meet full SUPPORTED criteria"
        )
        if corroboration_note:
            reasons.append(corroboration_note)
        return CalibrationVerdict(
            event_key=event_key,
            verdict="PROVISIONAL",
            lag_s=lag_s,
            qt_delta_s=qt_delta_s,
            qt_disagreement_s=qt_disagreement_s,
            psr=psr,
            snr=snr,
            window_range_s=window_range_s,
            uncertainty_s="unknown",
            reasons=tuple(reasons),
        )

    reasons.append(
        f"psr={psr:.2f}<{PROVISIONAL_MIN_PSR} or "
        f"window_range_s={window_range_s:.3f}>{PROVISIONAL_MAX_WINDOW_RANGE_S} or "
        f"snr={snr:.1f}<{PROVISIONAL_MIN_SNR} or "
        f"qt_disagreement_s={qt_disagreement_s}>{PROVISIONAL_MAX_QT_DISAGREEMENT_S}"
    )
    if corroboration_note:
        reasons.append(corroboration_note)
    return CalibrationVerdict(
        event_key=event_key,
        verdict="AMBIGUOUS",
        lag_s=lag_s,
        qt_delta_s=qt_delta_s,
        qt_disagreement_s=qt_disagreement_s,
        psr=psr,
        snr=snr,
        window_range_s=window_range_s,
        uncertainty_s="unknown",
        reasons=tuple(reasons),
    )


# ---------------------------------------------------------------------------
# Manifest-backed, event-scoped, fail-closed SyncAligner construction (Problem E)
# ---------------------------------------------------------------------------

import hashlib
from pathlib import Path

import yaml

from railway_detection.data.sync import SyncAligner


class CalibrationNotAcceptedError(RuntimeError):
    """Raised when calibration evidence for an event does not permit cross-camera fusion."""

    def __init__(self, detail: str, *, code: str = "SYNC_CALIBRATION_REJECTED") -> None:
        self.code = code
        super().__init__(detail)


@dataclass(frozen=True)
class ValidatedAlignment:
    """A SyncAligner scoped to exactly one event, built only from accepted calibration."""

    event_key: str
    aligner: SyncAligner
    manifest_version: str
    manifest_status: str
    verdict: str
    uncertainty_s: float | str
    front_source_id: str
    back_source_id: str
    front_offset_s: float
    back_offset_s: float
    front_sha256: str
    back_sha256: str


def _sha256_of(path: Path) -> str:
    require_media_authorization(path, "HASH_RAW_MEDIA")
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def load_validated_sync_aligner(
    manifest_path: Path | str,
    event_key: str,
    repo_root: Path | str = ".",
    front_source_id: str = "camera_1",
    back_source_id: str = "camera_2",
    allow_candidate_status: bool = False,
) -> ValidatedAlignment:
    """Build a `SyncAligner` for exactly one event, strictly from accepted calibration.

    Fails closed (raises `CalibrationNotAcceptedError` or `FileNotFoundError`)
    unless ALL of the following hold:
      1. The manifest file exists and parses as the expected schema.
      2. The manifest's top-level `status` is not the unvalidated-candidate
         marker, UNLESS the caller explicitly opts into exploratory use via
         `allow_candidate_status=True` (never the default; see Problem D --
         candidate calibration must never silently enter production fusion).
      3. `event_key` has an entry in the manifest.
      4. That entry's `calibration_verdict` is exactly `CALIBRATION_SUPPORTED`
         (PROVISIONAL and AMBIGUOUS both fail closed -- there is no partial
         credit).
      5. The SHA-256 of the front and back video files ON DISK, right now,
         under `repo_root`, match the hashes recorded in the manifest (stale
         or mismatched source media is rejected, not silently trusted).

    The returned `SyncAligner` registers ONLY this event's two cameras (never
    a shared/global aligner reused across events -- this is what prevents
    combining observations from unrelated event IDs, Problem E.5).
    """
    root = Path(repo_root)
    manifest_file = Path(manifest_path)
    if not manifest_file.exists():
        raise FileNotFoundError(f"Calibration manifest not found: {manifest_file}")
    try:
        manifest_file.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise CalibrationNotAcceptedError(
            "Calibration manifest path must remain beneath the supplied repository root"
        ) from exc

    try:
        with open(manifest_file, encoding="utf-8") as f:
            manifest = yaml.safe_load(f)
    except (OSError, yaml.YAMLError) as exc:
        raise CalibrationNotAcceptedError(
            f"Calibration manifest at {manifest_file} is unreadable or invalid: {exc}"
        ) from exc

    if not isinstance(manifest, dict) or not isinstance(manifest.get("events"), dict):
        raise CalibrationNotAcceptedError(
            f"Calibration manifest at {manifest_file} is missing a valid 'events' section"
        )

    manifest_status = str(manifest.get("status", "UNKNOWN"))
    if manifest_status == "CANDIDATE_UNVALIDATED_DO_NOT_MERGE" and not allow_candidate_status:
        raise CalibrationNotAcceptedError(
            f"Calibration manifest status is '{manifest_status}'. Candidate calibration must "
            "not be used for production cross-camera fusion. Pass allow_candidate_status=True "
            "only for an explicitly labeled exploratory run, never for the primary experiment."
        )

    event_entry = manifest["events"].get(event_key)
    if not isinstance(event_entry, dict):
        raise CalibrationNotAcceptedError(
            f"No calibration entry for event '{event_key}' in {manifest_file}. "
            "Missing calibration must not silently fall back to offset zero."
        )

    verdict = str(event_entry.get("calibration_verdict", "NOT_ASSESSABLE"))
    if verdict != "CALIBRATION_SUPPORTED":
        raise CalibrationNotAcceptedError(
            f"Event '{event_key}' calibration verdict is '{verdict}', not CALIBRATION_SUPPORTED. "
            "Cross-camera fusion for this event is blocked until independently re-validated."
        )

    front_entry = event_entry.get("camera_front")
    back_entry = event_entry.get("camera_back")
    if not isinstance(front_entry, dict) or not isinstance(back_entry, dict):
        raise CalibrationNotAcceptedError(
            f"Event '{event_key}' calibration entry is missing camera_front or camera_back"
        )

    for label, entry in (("camera_front", front_entry), ("camera_back", back_entry)):
        rel_path = entry.get("relative_path")
        expected_sha = entry.get("sha256")
        if not isinstance(rel_path, str) or not rel_path or not isinstance(expected_sha, str):
            raise CalibrationNotAcceptedError(
                f"Event '{event_key}' {label} entry is missing relative_path or sha256"
            )
        declared_path = Path(rel_path)
        if declared_path.is_absolute():
            raise CalibrationNotAcceptedError(
                f"Event '{event_key}' {label} relative_path must not be absolute"
            )
        media_path = (root / declared_path).resolve()
        try:
            media_path.relative_to(root.resolve())
        except ValueError as exc:
            raise CalibrationNotAcceptedError(
                f"Event '{event_key}' {label} relative_path escapes repository root"
            ) from exc
        if not media_path.exists():
            raise CalibrationNotAcceptedError(
                f"Event '{event_key}' {label} source media missing on disk: {media_path}"
            )
        actual_sha = _sha256_of(media_path)
        if actual_sha != expected_sha:
            raise CalibrationNotAcceptedError(
                f"Event '{event_key}' {label} SHA-256 mismatch: manifest expects "
                f"{expected_sha}, found {actual_sha} at {media_path}. Source media has "
                "changed since calibration was estimated; calibration is stale."
            )

    def required_finite(entry: dict[str, Any], field: str, label: str) -> float:
        value = entry.get(field)
        if isinstance(value, bool) or not isinstance(value, int | float) or not _is_finite(value):
            code = "SYNC_UNALIGNED" if field == "uncertainty_s" else "SYNC_CALIBRATION_REJECTED"
            raise CalibrationNotAcceptedError(
                f"Event '{event_key}' {label} entry requires a finite {field}; "
                "missing or non-computable clock metadata must not be defaulted",
                code=code,
            )
        number = float(value)
        if field == "uncertainty_s" and number < 0.0:
            raise CalibrationNotAcceptedError(
                f"Event '{event_key}' {label} uncertainty_s must be non-negative",
                code="SYNC_UNALIGNED",
            )
        return number

    # The front camera is the declared master-clock reference, but its 0.0
    # offset remains an explicit manifest assertion rather than a loader
    # fallback.  Back-camera uncertainty is mandatory for fusion: an unknown
    # uncertainty cannot be represented as the tolerance default.
    front_offset_s = required_finite(front_entry, "offset_s", "camera_front")
    back_offset_s = required_finite(back_entry, "offset_s", "camera_back")
    back_uncertainty_s = required_finite(back_entry, "uncertainty_s", "camera_back")
    aligner = SyncAligner()
    aligner.add_source(front_source_id, offset_s=front_offset_s, uncertainty_s=0.0)
    aligner.add_source(
        back_source_id,
        offset_s=back_offset_s,
        uncertainty_s=back_uncertainty_s,
    )

    return ValidatedAlignment(
        event_key=event_key,
        aligner=aligner,
        manifest_version=str(manifest.get("manifest_version", "unknown")),
        manifest_status=manifest_status,
        verdict=verdict,
        uncertainty_s=back_uncertainty_s,
        front_source_id=front_source_id,
        back_source_id=back_source_id,
        front_offset_s=front_offset_s,
        back_offset_s=back_offset_s,
        front_sha256=front_entry["sha256"],
        back_sha256=back_entry["sha256"],
    )
