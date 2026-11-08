"""Phase 15 controlled-validation data-collection interfaces (planning-grade).

Nothing here authorizes, schedules or performs field activity, and nothing here
connects to a gate, signal or any other railway control.
"""

from railway_detection.field_validation.capture_session import (
    CAPTURE_SESSION_SCHEMA,
    CaptureSessionValidation,
    SessionViolation,
    describe_capture_files,
    validate_capture_session,
)
from railway_detection.field_validation.capture_session_v2 import (
    CAPTURE_SESSION_V2_SCHEMA,
    SessionValidationReport,
    collect_software_provenance,
    json_schema,
    validate_capture_session_v2,
    verify_session_files,
)
from railway_detection.field_validation.capture_session_manifest import (
    MANIFEST_SCHEMA,
    PREFLIGHT_SCHEMA,
    build_capture_manifest,
    capture_preflight,
    write_capture_manifest,
)

__all__ = [
    "CAPTURE_SESSION_V2_SCHEMA",
    "SessionValidationReport",
    "collect_software_provenance",
    "json_schema",
    "validate_capture_session_v2",
    "verify_session_files",
    "CAPTURE_SESSION_SCHEMA",
    "CaptureSessionValidation",
    "SessionViolation",
    "describe_capture_files",
    "validate_capture_session",
    "MANIFEST_SCHEMA",
    "PREFLIGHT_SCHEMA",
    "build_capture_manifest",
    "capture_preflight",
    "write_capture_manifest",
]
