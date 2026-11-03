"""Synthetic-only tests for the isolated human timing-pilot preparation path.

Every media-like byte string and every output is created under pytest's
temporary directory. The guard test rejects repository source-media reads and
writes to official ground-truth/evaluation locations.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from railway_detection.annotation import stage21_timing_pilot as pilot

NOW = datetime(2026, 10, 19, 16, 0, tzinfo=UTC)
RESEARCHER = "researcher.synthetic@example.test"
REVIEWER = "reviewer.synthetic@example.test"
EVENT_KEY = "train_events/event_001"
RELEASE_SHA = "a" * 64
MEDIA_FRONT = b"SYNTHETIC FRONT BYTES -- NOT VIDEO"
MEDIA_BACK = b"SYNTHETIC BACK BYTES -- NOT VIDEO"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sealed(document: dict[str, Any]) -> dict[str, Any]:
    document["record_sha256"] = pilot._body_sha256(document)
    return document


def _release(tmp_path: Path) -> tuple[Path, str]:
    root = tmp_path
    files = [
        (
            "src/railway_detection/annotation/stage21_timing_pilot.py",
            b"synthetic workflow implementation fixture\n",
            "implementation",
        ),
        ("schemas/stage21_timing_pilot.schema.json", b'{"synthetic":true}\n', "schema"),
        ("tests/test_stage21_timing_pilot.py", b"def test_fixture(): assert True\n", "tests"),
    ]
    entries = []
    for rel, payload, role in files:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        entries.append({"path": rel, "sha256": _sha(payload), "role": role})
    manifest = {
        "schema_version": pilot.RELEASE_SCHEMA,
        "version": "0.1.0-test",
        "status": "PREPARED_NOT_ACTIVATED",
        "files": entries,
        "test_results": {"focused_status": "passed"},
        "intended_scope": {
            "operation": pilot.OPERATION,
            "purpose": pilot.PURPOSE,
            "evaluative": False,
            "activated_for_real_media": False,
        },
    }
    manifest_path = root / "release.json"
    manifest_path.write_bytes(pilot.canonical_json_bytes(manifest))
    digest = _sha(manifest_path.read_bytes())
    return manifest_path, digest


def _authorization(
    release_sha: str, inventory_sha: str, media: dict[str, dict[str, str]], proposal: str
) -> dict[str, Any]:
    scope = {
        "operation": pilot.OPERATION,
        "purpose": pilot.PURPOSE,
        "event_keys": [EVENT_KEY],
        "reviewer_ids": [REVIEWER],
        "workflow_release_sha256": release_sha,
        "permitted_operations": sorted(pilot.PERMITTED_OPERATIONS),
        "output_directory": pilot.OUTPUT_RELATIVE.as_posix(),
        "source_inventory_sha256": inventory_sha,
        "source_media_sha256_by_event": media,
        "active_proposal_sha256_by_event": {EVENT_KEY: proposal},
        "no_official_approval": True,
    }
    return _sealed(
        {
            "schema_version": pilot.AUTHORIZATION_SCHEMA,
            "authorization_id": "auth-synthetic-001",
            "authorized_by": RESEARCHER,
            "authorized_at_utc": "2026-10-19T15:00:00Z",
            "expires_at_utc": "2026-10-20T15:00:00Z",
            "authorization_statement": "Synthetic fixture only; no real media is authorized.",
            "scope": scope,
            "attestation": {"type": "RECORDED_RESEARCHER_STATEMENT", "signature": None},
            "recorded_by": {"identity": "synthetic test fixture", "kind": "researcher"},
        }
    )


def _activation(auth: dict[str, Any], release_sha: str) -> dict[str, Any]:
    return _sealed(
        {
            "schema_version": pilot.ACTIVATION_SCHEMA,
            "activation_id": "activation-synthetic-001",
            "activated_by": RESEARCHER,
            "activated_at_utc": "2026-10-19T15:30:00Z",
            "expires_at_utc": "2026-10-20T14:00:00Z",
            "authorization_sha256": pilot.canonical_sha256(auth),
            "workflow_release_sha256": release_sha,
            "scope_sha256": pilot.canonical_sha256(auth["scope"]),
            "activation_statement": (
                "Synthetic fixture only; test activation never grants real access."
            ),
            "attestation": {"type": "RECORDED_RESEARCHER_STATEMENT", "signature": None},
        }
    )


class Fixture:
    def __init__(self, root: Path) -> None:
        self.root = root / "repo"
        self.root.mkdir(parents=True, exist_ok=True)
        self.release_path, self.release_sha = _release(self.root)
        self.event_key = EVENT_KEY
        self.reviewer = REVIEWER
        self.media_paths = {
            "front": self.root / "synthetic_media" / "front.bin",
            "back": self.root / "synthetic_media" / "back.bin",
        }
        for camera, payload in (("front", MEDIA_FRONT), ("back", MEDIA_BACK)):
            self.media_paths[camera].parent.mkdir(parents=True, exist_ok=True)
            self.media_paths[camera].write_bytes(payload)
        self.media_hashes = {"front": _sha(MEDIA_FRONT), "back": _sha(MEDIA_BACK)}
        self.proposal_path = self.root / "metadata" / "proposal.json"
        self.proposal_path.parent.mkdir(parents=True, exist_ok=True)
        self.proposal_path.write_text('{"synthetic_candidate_only":true}\n', encoding="utf-8")
        self.proposal_sha = _sha(self.proposal_path.read_bytes())
        self.inventory_path = self.root / "metadata" / "inventory.json"
        inventory = {
            EVENT_KEY: {
                "category": "train_events",
                "event_id": "event_001",
                "front": {
                    "path": self.media_paths["front"].relative_to(self.root).as_posix(),
                    "sha256": self.media_hashes["front"],
                },
                "back": {
                    "path": self.media_paths["back"].relative_to(self.root).as_posix(),
                    "sha256": self.media_hashes["back"],
                },
            }
        }
        self.inventory_path.write_text(json.dumps(inventory, sort_keys=True), encoding="utf-8")
        self.inventory_sha = _sha(self.inventory_path.read_bytes())
        self.queue_path = self.root / "metadata" / "queue.json"
        queue = {
            "items": [
                {
                    "event_key": EVENT_KEY,
                    "inventory_media_sha256": self.media_hashes,
                    "active_candidate_proposal": {
                        "path": self.proposal_path.relative_to(self.root).as_posix(),
                        "sha256": self.proposal_sha,
                    },
                }
            ]
        }
        self.queue_path.write_text(json.dumps(queue, sort_keys=True), encoding="utf-8")
        self.allowlist_path = self.root / "metadata" / "allowlist.json"
        self.allowlist_path.write_text(
            json.dumps({"authorized_reviewers": [RESEARCHER, REVIEWER]}), encoding="utf-8"
        )
        self.authorization_path = self.root / "metadata" / "authorization.json"
        self.activation_path = self.root / "metadata" / "activation.json"
        self.authorization = _authorization(
            self.release_sha,
            self.inventory_sha,
            {EVENT_KEY: self.media_hashes},
            self.proposal_sha,
        )
        self.activation = _activation(self.authorization, self.release_sha)
        self.write_governance()

    def write_governance(self) -> None:
        self.authorization_path.write_bytes(pilot.canonical_json_bytes(self.authorization))
        self.activation_path.write_bytes(pilot.canonical_json_bytes(self.activation))

    def preparation_grant(self) -> pilot.PreparationOnlyAuthorization:
        return pilot.record_preparation_authorization(
            repository_root=self.root,
            event_key=EVENT_KEY,
            reviewer_id=REVIEWER,
            release=self.verified_release(),
            inventory_path=self.inventory_path,
            queue_path=self.queue_path,
            now=NOW,
            expires_at_utc="2026-10-20T15:00:00Z",
            permitted_operations=frozenset({"record_human_timing"}),
            output_directory=pilot.OUTPUT_RELATIVE.as_posix(),
        )

    def verified_release(self) -> pilot.VerifiedRelease:
        return pilot.verify_release_manifest(
            self.release_path,
            expected_release_sha256=self.release_sha,
            repository_root=self.release_path.parent,
        )

    def validate_auth(self, *, event_key: str = EVENT_KEY, reviewer_id: str = REVIEWER) -> str:
        return pilot.validate_authorization(
            self.authorization,
            allowlisted_researchers=frozenset({RESEARCHER, REVIEWER}),
            release=self.verified_release(),
            event_key=event_key,
            reviewer_id=reviewer_id,
            now=NOW,
        )

    def start(self) -> pilot.TimingSession:
        return pilot.start_timing_session(
            repository_root=self.release_path.parent,
            authorization_path=self.authorization_path,
            activation_path=self.activation_path,
            release_manifest_path=self.release_path,
            expected_release_sha256=self.release_sha,
            inventory_path=self.inventory_path,
            queue_path=self.queue_path,
            allowlist_path=self.allowlist_path,
            event_key=EVENT_KEY,
            reviewer_id=REVIEWER,
            session_id="session-synthetic-001",
            preparation_only=True,
            preparation_grant=self.preparation_grant(),
            now=NOW,
            utc_clock=lambda: NOW,
            monotonic_clock=lambda: 100.0,
        )

    def start_arguments(self) -> dict[str, Any]:
        return {
            "repository_root": self.release_path.parent,
            "authorization_path": self.authorization_path,
            "activation_path": self.activation_path,
            "release_manifest_path": self.release_path,
            "expected_release_sha256": self.release_sha,
            "inventory_path": self.inventory_path,
            "queue_path": self.queue_path,
            "allowlist_path": self.allowlist_path,
            "event_key": EVENT_KEY,
            "reviewer_id": REVIEWER,
            "session_id": "session-synthetic-002",
            "preparation_only": True,
            "preparation_grant": self.preparation_grant(),
            "now": NOW,
        }


@pytest.fixture
def fixture(tmp_path: Path) -> Fixture:
    return Fixture(tmp_path)


def _observation(
    *,
    state: str = "UNCERTAIN",
    value: float | None = None,
    camera: str | None = None,
    basis: str | None = None,
    uncertainty: float | None = None,
    rationale: str = "Synthetic human observation fixture with explicit evidence limits.",
    evidence: str = "INSUFFICIENT",
    missing_reason: str | None = "Synthetic fixture contains no viewable event evidence.",
    censor: str | None = None,
) -> dict[str, Any]:
    return {
        "state": state,
        "value_s": value,
        "reference_camera": camera,
        "timestamp_basis": basis,
        "timestamp_uncertainty_s": uncertainty,
        "rationale": rationale,
        "evidence_status": evidence,
        "missing_evidence_reason": missing_reason,
        "censoring_direction": censor,
    }


def _observations() -> dict[str, dict[str, Any]]:
    return {name: _observation() for name in pilot.BOUNDARIES}


def test_successfully_validates_exact_scoped_authorization_and_activation(fixture: Fixture) -> None:
    grant = fixture.start().grant
    assert grant.event_key == EVENT_KEY
    assert grant.reviewer_id == REVIEWER
    assert grant.workflow_release_sha256 == fixture.release_sha
    assert grant.front_sha256 == fixture.media_hashes["front"]
    assert grant.back_sha256 == fixture.media_hashes["back"]


def test_missing_authorization_fails_closed_before_source_hashing(
    fixture: Fixture, monkeypatch
) -> None:
    grant = fixture.preparation_grant()
    arguments = fixture.start_arguments()
    arguments["preparation_grant"] = grant
    fixture.authorization_path.unlink()

    def forbidden(*_args, **_kwargs):
        raise AssertionError("media bytes must not be read before authorization validation")

    monkeypatch.setattr(pilot, "_metadata_bindings", forbidden)
    with pytest.raises(pilot.PilotWorkflowError, match="ARTIFACT_MISSING"):
        pilot.start_timing_session(**arguments)


def test_preparation_grant_is_required_and_bound_to_synthetic_metadata(fixture: Fixture) -> None:
    arguments = fixture.start_arguments()
    arguments.pop("preparation_grant")
    with pytest.raises(pilot.PilotWorkflowError, match="PREPARATION_GRANT_REQUIRED"):
        pilot.start_timing_session(**arguments)
    arguments = fixture.start_arguments()
    arguments["preparation_grant"] = pilot.record_preparation_authorization(
        repository_root=fixture.root,
        event_key=EVENT_KEY,
        reviewer_id="different.synthetic@example.test",
        release=fixture.verified_release(),
        inventory_path=fixture.inventory_path,
        queue_path=fixture.queue_path,
        now=NOW,
        expires_at_utc="2026-10-20T15:00:00Z",
        permitted_operations=frozenset({"record_human_timing"}),
        output_directory=pilot.OUTPUT_RELATIVE.as_posix(),
    )
    with pytest.raises(pilot.PilotWorkflowError, match="PREPARATION_GRANT_INVALID"):
        pilot.start_timing_session(**arguments)


def test_tampered_authorization_and_mismatched_release_are_rejected(fixture: Fixture) -> None:
    fixture.authorization["authorization_statement"] = "tampered after sealing"
    with pytest.raises(pilot.PilotWorkflowError, match="AUTHORIZATION_TAMPERED"):
        fixture.validate_auth()

    fixture = Fixture(fixture.root.parent / "release_mismatch")
    fixture.authorization["scope"]["workflow_release_sha256"] = "b" * 64
    fixture.authorization = _sealed(fixture.authorization)
    with pytest.raises(pilot.PilotWorkflowError, match="RELEASE_HASH_MISMATCH"):
        fixture.validate_auth()


@pytest.mark.parametrize(
    ("mutation", "event_key", "reviewer_id", "code"),
    [
        ("purpose", EVENT_KEY, REVIEWER, "AUTHORIZATION_SCOPE_MISMATCH"),
        ("operation", EVENT_KEY, REVIEWER, "AUTHORIZATION_SCOPE_MISMATCH"),
        ("event", "no_train_events/event_001", REVIEWER, "EVENT_OUT_OF_SCOPE"),
        ("reviewer", EVENT_KEY, "other.synthetic@example.test", "REVIEWER_OUT_OF_SCOPE"),
    ],
)
def test_wrong_event_reviewer_purpose_or_operation_is_rejected(
    fixture: Fixture, mutation: str, event_key: str, reviewer_id: str, code: str
) -> None:
    if mutation in {"purpose", "operation"}:
        fixture.authorization["scope"][mutation] = "wrong"
        fixture.authorization = _sealed(fixture.authorization)
    with pytest.raises(pilot.PilotWorkflowError, match=code):
        fixture.validate_auth(event_key=event_key, reviewer_id=reviewer_id)


def test_reviewer_must_be_on_allowlist_even_when_in_scope(fixture: Fixture) -> None:
    fixture.allowlist_path.write_text(
        json.dumps({"authorized_reviewers": [RESEARCHER]}), encoding="utf-8"
    )
    with pytest.raises(pilot.PilotWorkflowError, match="REVIEWER_NOT_AUTHORIZED"):
        pilot.start_timing_session(
            repository_root=fixture.release_path.parent,
            authorization_path=fixture.authorization_path,
            activation_path=fixture.activation_path,
            release_manifest_path=fixture.release_path,
            expected_release_sha256=fixture.release_sha,
            inventory_path=fixture.inventory_path,
            queue_path=fixture.queue_path,
            allowlist_path=fixture.allowlist_path,
            event_key=EVENT_KEY,
            reviewer_id=REVIEWER,
            session_id="session-unauthorized-reviewer",
            preparation_only=True,
            preparation_grant=fixture.preparation_grant(),
            now=NOW,
        )


def test_duplicate_or_malformed_event_ids_are_rejected(fixture: Fixture) -> None:
    fixture.authorization["scope"]["event_keys"] = [EVENT_KEY, EVENT_KEY]
    fixture.authorization = _sealed(fixture.authorization)
    with pytest.raises(pilot.PilotWorkflowError, match="EVENT_SCOPE_INVALID"):
        fixture.validate_auth()
    fixture.authorization["scope"]["event_keys"] = ["event_001"]
    fixture.authorization = _sealed(fixture.authorization)
    with pytest.raises(pilot.PilotWorkflowError, match="EVENT_ID_INVALID"):
        fixture.validate_auth(event_key="event_001")


def test_expired_or_missing_activation_is_rejected_before_media_access(fixture: Fixture) -> None:
    fixture.activation_path.unlink()
    with pytest.raises(pilot.PilotWorkflowError, match="ARTIFACT_MISSING"):
        fixture.start()
    fixture = Fixture(fixture.root.parent / "expired")
    fixture.authorization["expires_at_utc"] = "2026-10-19T15:59:59Z"
    fixture.authorization = _sealed(fixture.authorization)
    fixture.activation = _activation(fixture.authorization, fixture.release_sha)
    fixture.write_governance()
    with pytest.raises(pilot.PilotWorkflowError, match="AUTHORIZATION_EXPIRED_OR_INVALID"):
        fixture.start()


def test_activation_tamper_hash_scope_and_release_mismatches_are_rejected(fixture: Fixture) -> None:
    release = fixture.verified_release()
    auth_hash = fixture.validate_auth()
    fixture.activation["activation_statement"] = "tampered"
    with pytest.raises(pilot.PilotWorkflowError, match="ACTIVATION_TAMPERED"):
        pilot.validate_activation(
            fixture.activation,
            authorization=fixture.authorization,
            authorization_sha256=auth_hash,
            release=release,
            allowlisted_researchers=frozenset({RESEARCHER, REVIEWER}),
            now=NOW,
        )
    fixture.activation = _activation(fixture.authorization, fixture.release_sha)
    fixture.activation["workflow_release_sha256"] = "c" * 64
    fixture.activation = _sealed(fixture.activation)
    with pytest.raises(pilot.PilotWorkflowError, match="RELEASE_HASH_MISMATCH"):
        pilot.validate_activation(
            fixture.activation,
            authorization=fixture.authorization,
            authorization_sha256=auth_hash,
            release=release,
            allowlisted_researchers=frozenset({RESEARCHER, REVIEWER}),
            now=NOW,
        )


def test_wrong_permitted_operation_is_rejected(fixture: Fixture) -> None:
    fixture.authorization["scope"]["permitted_operations"] = ["open_source_media"]
    fixture.authorization = _sealed(fixture.authorization)
    with pytest.raises(pilot.PilotWorkflowError, match="OPERATION_SCOPE_INVALID"):
        fixture.validate_auth()


def test_missing_and_contradictory_timing_fields_are_rejected() -> None:
    observations = _observations()
    del observations["T1_danger_zone_entry"]
    with pytest.raises(pilot.PilotWorkflowError, match="TIMING_FIELDS_MISSING"):
        pilot._validate_observations(observations)


@pytest.mark.parametrize("field", ["state", "evidence_status"])
@pytest.mark.parametrize("malformed", [[], {}])
def test_unhashable_timing_values_fail_closed_as_workflow_errors(
    field: str, malformed: Any
) -> None:
    observations = _observations()
    observations["T0_first_visible"][field] = malformed
    with pytest.raises(pilot.PilotWorkflowError, match="TIMING_FIELDS_INVALID"):
        pilot._validate_observations(observations)


def test_unknown_non_string_boundary_key_fails_closed_as_workflow_error() -> None:
    observations = _observations()
    observations[99] = observations["T0_first_visible"]
    with pytest.raises(pilot.PilotWorkflowError, match="TIMING_FIELDS_INVALID"):
        pilot._validate_observations(observations)


def test_observable_timing_with_insufficient_evidence_is_rejected() -> None:
    observations = _observations()
    observations["T1_danger_zone_entry"] = _observation(
        state="OBSERVABLE",
        value=3.0,
        camera="front",
        basis="camera_local_elapsed_seconds",
        uncertainty=0.2,
        evidence="INSUFFICIENT",
        missing_reason="No synthetic media was reviewed.",
    )
    with pytest.raises(pilot.PilotWorkflowError, match="TIMING_FIELDS_CONTRADICTORY"):
        pilot._validate_observations(observations)


def test_unobservable_missing_evidence_and_left_censored_t0_are_explicitly_supported() -> None:
    observations = _observations()
    observations["T0_first_visible"] = _observation(
        state="CENSORED",
        rationale="Synthetic fixture models train already present at start.",
        evidence="PRESENT",
        missing_reason=None,
        censor="LEFT",
    )
    observations["T4_tail_clearance"] = _observation(
        state="UNOBSERVABLE_NOT_APPLICABLE",
        rationale="Synthetic fixture has no train tail event.",
        evidence="MISSING",
        missing_reason="No event footage exists in this synthetic fixture.",
    )
    validated = pilot._validate_observations(observations)
    assert validated["T0_first_visible"]["censoring_direction"] == "LEFT"
    assert validated["T4_tail_clearance"]["evidence_status"] == "MISSING"


def test_left_censor_is_rejected_for_non_t0_and_uncertainty_is_required() -> None:
    observations = _observations()
    observations["T2_crossing_occupancy_start"] = _observation(
        state="CENSORED",
        rationale="Synthetic fixture has no crossing occupancy evidence.",
        censor="LEFT",
    )
    with pytest.raises(pilot.PilotWorkflowError, match="LEFT_CENSOR_INVALID"):
        pilot._validate_observations(observations)
    observations = _observations()
    observations["T1_danger_zone_entry"] = _observation(
        state="OBSERVABLE",
        value=2.0,
        camera="front",
        basis="camera_local_elapsed_seconds",
        uncertainty=None,
        evidence="PRESENT",
        missing_reason=None,
    )
    with pytest.raises(pilot.PilotWorkflowError, match="TIMESTAMP_UNCERTAINTY_INVALID"):
        pilot._validate_observations(observations)


def test_same_camera_chronology_is_checked_without_cross_camera_fusion() -> None:
    observations = _observations()
    observations["T1_danger_zone_entry"] = _observation(
        state="OBSERVABLE",
        value=5.0,
        camera="front",
        basis="camera_local_elapsed_seconds",
        uncertainty=0.2,
        evidence="PRESENT",
        missing_reason=None,
    )
    observations["T2_crossing_occupancy_start"] = _observation(
        state="OBSERVABLE",
        value=4.0,
        camera="front",
        basis="camera_local_elapsed_seconds",
        uncertainty=0.2,
        evidence="PRESENT",
        missing_reason=None,
    )
    with pytest.raises(pilot.PilotWorkflowError, match="TIMING_CHRONOLOGY_CONTRADICTION"):
        pilot._validate_observations(observations)
    observations["T2_crossing_occupancy_start"]["reference_camera"] = "back"
    assert pilot._validate_observations(observations)


def test_draft_is_permanently_unapproved_and_contains_separate_human_observations(
    fixture: Fixture,
) -> None:
    session = fixture.start()
    draft = pilot.build_unapproved_draft(
        session=session,
        observations=_observations(),
        review_end_utc="2026-10-19T16:01:00Z",
        monotonic_ended_s=160.0,
    )
    assert draft["record_state"] == "HUMAN_REVIEW_COMPLETED_UNAPPROVED_PILOT"
    assert draft["ground_truth_eligible"] is False
    assert draft["official_approval"] is False
    assert draft["timing"]["duration_monotonic_s"] == 60.0
    assert "candidate_boundary_evidence" not in draft
    assert "model_predictions" not in draft
    tampered = dict(draft, record_state="APPROVED")
    with pytest.raises(pilot.PilotWorkflowError, match="APPROVAL_TRANSITION_FORBIDDEN"):
        pilot.write_unapproved_draft(tampered, repository_root=fixture.root, preparation_only=True)


def test_authorization_expiry_before_session_completion_rejects_draft(fixture: Fixture) -> None:
    session = fixture.start()
    session = pilot.TimingSession(
        grant=pilot.MediaAccessGrant(
            **{
                **session.grant.__dict__,
                "authorization_expires_at_utc": "2026-10-19T16:00:30Z",
            }
        ),
        session_id=session.session_id,
        started_at_utc=session.started_at_utc,
        monotonic_started_s=session.monotonic_started_s,
        _capability=session._capability,
        utc_clock=session.utc_clock,
        monotonic_clock=session.monotonic_clock,
    )
    with pytest.raises(pilot.PilotWorkflowError, match="AUTHORIZATION_EXPIRED_DURING_SESSION"):
        pilot.build_unapproved_draft(
            session=session,
            observations=_observations(),
            review_end_utc="2026-10-19T16:01:00Z",
            monotonic_ended_s=160.0,
        )


def test_provenance_and_source_hash_mismatches_fail_closed(fixture: Fixture) -> None:
    fixture.authorization["scope"]["source_media_sha256_by_event"][EVENT_KEY]["front"] = "0" * 64
    fixture.authorization = _sealed(fixture.authorization)
    fixture.activation = _activation(fixture.authorization, fixture.release_sha)
    fixture.write_governance()
    with pytest.raises(pilot.PilotWorkflowError, match="MEDIA_BINDING_MISMATCH"):
        fixture.start()
    fixture = Fixture(fixture.root.parent / "media-altered")
    fixture.media_paths["front"].write_bytes(b"altered synthetic input")
    with pytest.raises(pilot.PilotWorkflowError, match="MEDIA_HASH_MISMATCH"):
        fixture.start()


def test_proposal_provenance_hash_mismatch_fails_closed(fixture: Fixture) -> None:
    fixture.proposal_path.write_text('{"changed":true}\n', encoding="utf-8")
    with pytest.raises(pilot.PilotWorkflowError, match="PROPOSAL_BINDING_MISMATCH"):
        fixture.start()


def test_atomic_write_is_idempotent_and_refuses_conflicting_rerun(fixture: Fixture) -> None:
    draft = pilot.build_unapproved_draft(
        session=fixture.start(),
        observations=_observations(),
        review_end_utc="2026-10-19T16:01:00Z",
        monotonic_ended_s=160.0,
    )
    first = pilot.write_unapproved_draft(draft, repository_root=fixture.root, preparation_only=True)
    before = first.read_bytes()
    second = pilot.write_unapproved_draft(
        draft, repository_root=fixture.root, preparation_only=True
    )
    assert first == second and first.read_bytes() == before
    changed = dict(draft, reviewer_id="different.synthetic@example.test")
    with pytest.raises(pilot.PilotWorkflowError, match="IDEMPOTENCY_CONFLICT"):
        pilot.write_unapproved_draft(changed, repository_root=fixture.root, preparation_only=True)


def test_interrupted_atomic_write_leaves_no_partial_or_temporary_file(
    fixture: Fixture, monkeypatch
) -> None:
    draft = pilot.build_unapproved_draft(
        session=fixture.start(),
        observations=_observations(),
        review_end_utc="2026-10-19T16:01:00Z",
        monotonic_ended_s=160.0,
    )

    def interrupted(*_args, **_kwargs):
        raise OSError("synthetic interrupted link")

    monkeypatch.setattr(pilot.os, "link", interrupted)
    with pytest.raises(pilot.PilotWorkflowError, match="DRAFT_WRITE_FAILED"):
        pilot.write_unapproved_draft(draft, repository_root=fixture.root, preparation_only=True)
    output = fixture.root / pilot.OUTPUT_RELATIVE
    assert not list(output.rglob("*.pilot.json"))
    assert not list(output.rglob("*.tmp"))
    assert not list(output.rglob(".pilot-draft-*"))


def test_release_manifest_hash_mismatch_or_changed_implementation_is_rejected(
    fixture: Fixture,
) -> None:
    implementation = (
        fixture.release_path.parent / "src/railway_detection/annotation/stage21_timing_pilot.py"
    )
    implementation.write_text("altered implementation\n", encoding="utf-8")
    with pytest.raises(pilot.PilotWorkflowError, match="RELEASE_FILE_HASH_MISMATCH"):
        fixture.verified_release()
    with pytest.raises(pilot.PilotWorkflowError, match="RELEASE_HASH_MISMATCH"):
        pilot.verify_release_manifest(
            fixture.release_path,
            expected_release_sha256="f" * 64,
            repository_root=fixture.release_path.parent,
        )


def test_isolation_guard_no_real_media_reads_or_official_directory_writes(
    fixture: Fixture, monkeypatch
) -> None:
    real_root = Path("/Users/sayemuddin/Desktop/Train_automation").resolve()
    original_read_bytes = Path.read_bytes
    read_paths: list[Path] = []

    def guarded_read_bytes(path: Path) -> bytes:
        resolved = path.resolve()
        assert (real_root / "data/raw/layer_b").resolve() not in resolved.parents
        assert resolved != (real_root / "data/raw/layer_b").resolve()
        read_paths.append(resolved)
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", guarded_read_bytes)
    session = fixture.start()
    draft = pilot.build_unapproved_draft(
        session=session,
        observations=_observations(),
        review_end_utc="2026-10-19T16:01:00Z",
        monotonic_ended_s=160.0,
    )
    output = pilot.write_unapproved_draft(
        draft, repository_root=fixture.root, preparation_only=True
    )
    assert output.is_relative_to(fixture.root)
    assert read_paths and all(path.is_relative_to(fixture.root) for path in read_paths)
    assert not (real_root / "data/ground_truth/review_pilots").exists()
    assert not (real_root / "data/ground_truth/reviews").exists() or not list(
        (real_root / "data/ground_truth/reviews").glob("*.pilot.json")
    )
    assert not (real_root / "data/evaluation").exists() or not list(
        (real_root / "data/evaluation").glob("*.pilot.json")
    )


def test_preparation_mode_rejects_repository_metadata_and_media_paths(fixture: Fixture) -> None:
    arguments = fixture.start_arguments()
    arguments["inventory_path"] = Path(
        "/Users/sayemuddin/Desktop/Train_automation/data/manifests/"
        "layer_b_v2_annotation_inventory.json"
    )
    with pytest.raises(pilot.PilotWorkflowError, match="PREPARATION_ISOLATION_REQUIRED"):
        pilot.start_timing_session(**arguments)


def test_preparation_mode_rejects_live_checkout_before_any_input_read(
    fixture: Fixture, monkeypatch
) -> None:
    arguments = fixture.start_arguments()
    arguments["repository_root"] = Path("/Users/sayemuddin/Desktop/Train_automation")

    def forbidden(*_args, **_kwargs):
        raise AssertionError("isolation check must precede all input reads")

    monkeypatch.setattr(Path, "read_bytes", forbidden)
    monkeypatch.setattr(Path, "read_text", forbidden)
    with pytest.raises(pilot.PilotWorkflowError, match="PREPARATION_ISOLATION_REQUIRED"):
        pilot.start_timing_session(**arguments)


def test_non_preparation_draft_write_requires_verified_session_grant(fixture: Fixture) -> None:
    draft = pilot.build_unapproved_draft(
        session=fixture.start(),
        observations=_observations(),
        review_end_utc="2026-10-19T16:01:00Z",
        monotonic_ended_s=160.0,
    )
    with pytest.raises(pilot.PilotWorkflowError, match="SESSION_GRANT_REQUIRED"):
        pilot.write_unapproved_draft(draft, repository_root=fixture.root)


def test_forged_timing_session_dataclass_cannot_authorize_real_write(fixture: Fixture) -> None:
    session = fixture.start()
    draft = pilot.build_unapproved_draft(
        session=session,
        observations=_observations(),
        review_end_utc="2026-10-19T16:01:00Z",
        monotonic_ended_s=160.0,
    )
    forged = pilot.TimingSession(
        grant=session.grant,
        session_id=session.session_id,
        started_at_utc=session.started_at_utc,
        monotonic_started_s=session.monotonic_started_s,
    )
    with pytest.raises(pilot.PilotWorkflowError, match="SESSION_GRANT_REQUIRED"):
        pilot.write_unapproved_draft(draft, repository_root=fixture.root, session=forged)


def test_clock_overrides_are_synthetic_preparation_only(fixture: Fixture) -> None:
    arguments = fixture.start_arguments()
    arguments["preparation_only"] = False
    with pytest.raises(pilot.PilotWorkflowError, match="CLOCK_OVERRIDE_FORBIDDEN"):
        pilot.start_timing_session(**arguments)


def test_approval_and_evaluation_operations_are_not_in_permitted_operation_set() -> None:
    assert "approve" not in pilot.PERMITTED_OPERATIONS
    assert "promote" not in pilot.PERMITTED_OPERATIONS
    assert "evaluate" not in pilot.PERMITTED_OPERATIONS
