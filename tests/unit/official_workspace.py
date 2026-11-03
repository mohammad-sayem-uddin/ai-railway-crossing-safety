"""Synthetic official-run workspace for end-to-end Phase 12 tests.

Builds, under a pytest tmp directory, a complete fake repository root in which every
documented prerequisite is genuinely satisfied by *synthetic* artifacts: Stage-2.1
records from the real builder, a promotion receipt from the real readiness CLI,
allowlisted split/R04/protocol decisions, a derived manifest, evidence payloads and a
recorded EVAL-AUTH. Nothing here touches the real repository, and nothing produced from
it is research data. Evidence payloads say so in ``generated_by``.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from railway_detection.annotation.readiness_cli import main as readiness_main
from railway_detection.evaluation import execution_gate, governance
from railway_detection.evaluation.execution_gate import assess_official_phase12_readiness
from railway_detection.evaluation.replay_evidence import build_replay_evidence_payload
from railway_detection.experiments.frozen_config import load_frozen_config
from railway_detection.fusion.evidence import Detection, EvidenceRecord, Modality
from second_review_support import SECOND_REVIEWER
from test_phase11_9_synthetic_pilot import PILOT_REVIEWER, SYNTHETIC_EVENTS
from test_phase11_12_readiness_gate import _three_records

REPO_ROOT = Path(__file__).resolve().parents[2]
NOW = datetime(2026, 12, 1, tzinfo=UTC)
PREMATURE = {"premature_opening_window": "t1_entry_to_t4_clearance"}  # fixture-only choice

TRAIN = f"train_events/{SYNTHETIC_EVENTS[0]['event_id']}"
NO_TRAIN = f"no_train_events/{SYNTHETIC_EVENTS[1]['event_id']}"
ENGINE = f"engine_events/{SYNTHETIC_EVENTS[2]['event_id']}"
TEST_EVENTS = [TRAIN, NO_TRAIN, ENGINE]
TRAIN_ONLY = "train_events/fixture_train_only"
VAL_ONLY = "train_events/fixture_val_only"
SPLIT = {"train": [TRAIN_ONLY], "val": [VAL_ONLY], "test": TEST_EVENTS}
ALL_EVENTS = [TRAIN_ONLY, VAL_ONLY, *TEST_EVENTS]
DEFAULT_MODES = dict.fromkeys(ALL_EVENTS, "independent_camera")
BACK_OFFSET_S = 1.5


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2), encoding="utf-8")


def envelope(schema: str, **body: object) -> dict:
    return {
        "schema_version": schema,
        "decision_status": "APPROVED",
        "decision_id": f"dec-{schema.split('/')[0]}",
        "decided_by": PILOT_REVIEWER,
        "decided_at_utc": "2026-01-14T10:00:00Z",
        "researcher_statement": "Synthetic fixture statement (test only).",
        **body,
    }


def _vision(source: str, times: list[float], label: str, active: Callable[[float], bool]):
    records = []
    for index, t in enumerate(times):
        detections = (Detection(label=label, confidence=0.9),) if active(t) else ()
        records.append(
            EvidenceRecord(
                timestamp_s=t,
                source_id=source,
                modality=Modality.VISION,
                available=True,
                detections=detections,
                metadata={"frame_index": index},
            )
        )
    return records


def _audio(times: list[float]):
    return [
        EvidenceRecord(
            timestamp_s=t,
            source_id="audio_1",
            modality=Modality.AUDIO,
            available=True,
            detections=(
                Detection(label="ambient", confidence=0.01, metadata={"probability": 0.01}),
            ),
            metadata={"audio_safety_role": "supporting_only"},
        )
        for t in times
    ]


def synthetic_streams(kind: str, mode: str) -> dict[str, list[EvidenceRecord]]:
    """Deterministic fake model outputs (not predictions of any real clip)."""
    times = [round(0.2 * i, 1) for i in range(0, 301)]  # 0 .. 60 s
    if kind == "train":
        front = _vision("camera_1", times, "front", lambda t: 2.0 <= t < 20.0)
        back = _vision("camera_2", times, "rear", lambda t: 8.0 <= t < 44.0)
    else:
        front = _vision("camera_1", times, "front", lambda t: False)
        back = _vision("camera_2", times, "rear", lambda t: False)
    streams: dict[str, list[EvidenceRecord]] = {
        "front_vision": front,
        "front_audio": _audio([float(i) for i in range(1, 60)]),
    }
    if mode != "single_camera":
        streams["back_vision"] = back
    return streams


@dataclass
class Workspace:
    root: Path
    tmp: Path
    config_hash: str
    modes: dict[str, str]
    media: dict[str, dict[str, str]] = field(default_factory=dict)

    def path(self, relative: Path | str) -> Path:
        return self.root / relative

    def assess(self):
        return assess_official_phase12_readiness(self.root, now=NOW)

    def payload_path(self, event_id: str) -> Path:
        return self.root / "data/manifests" / f"{event_id.replace('/', '__')}.evidence.json"

    def rewrite_payload(self, event_id: str, mutate: Callable[[dict], None]) -> None:
        """Mutate a payload and re-derive the manifest hash (as a researcher re-pinning)."""
        path = self.payload_path(event_id)
        payload = json.loads(path.read_text())
        mutate(payload)
        path.write_text(json.dumps(payload), encoding="utf-8")
        manifest_path = self.root / "data/manifests/phase12_evaluation_inputs.json"
        manifest = json.loads(manifest_path.read_text())
        for event in manifest["events"]:
            if event["event_id"] == event_id:
                event["source_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    def record_authorization(self, **overrides: object) -> dict:
        live = self.assess().live_bindings
        record = {
            "schema_version": governance.EVAL_AUTH_SCHEMA,
            "authorization_id": "auth-synthetic-e2e",
            "stage": "synthetic_stage",
            "authorized_by": PILOT_REVIEWER,
            "authorized_at_utc": "2026-01-15T12:00:00Z",
            "authorization_statement": "Synthetic fixture statement (test only).",
            "attestation": {"type": governance.ATTESTATION_RECORDED_STATEMENT, "signature": None},
            "recorded_by": {"kind": "researcher", "identity": PILOT_REVIEWER},
            "scope": {
                "operation": governance.AUTHORIZED_OPERATION,
                "stage": "synthetic_stage",
                "field_or_physical_operations_authorized": False,
            },
            "bindings": dict(live),
        }
        record.update(overrides)
        record["record_sha256"] = governance.canonical_record_sha256(record)
        write_json(self.root / governance.EVAL_AUTH_RELATIVE, record)
        return record


def build_workspace(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    modes: Mapping[str, str] | None = None,
    accepted_sync: tuple[str, ...] = (),
    calibration_verdicts: Mapping[str, str] | None = None,
    authorize: bool = True,
    split: Mapping[str, list[str]] | None = None,
) -> Workspace:
    modes = {**DEFAULT_MODES, **(modes or {})}
    split = {role: list(ids) for role, ids in (split or SPLIT).items()}
    assert sorted(i for ids in split.values() for i in ids) == sorted(ALL_EVENTS)
    root = tmp_path / "repo"
    ground_truth = root / "data/ground_truth"
    write_json(
        ground_truth / "authorized_reviewers.json",
        {"authorized_reviewers": [PILOT_REVIEWER, SECOND_REVIEWER]},
    )

    # --- frozen config / policy: a byte copy of the real config, read-only source
    (root / "configs").mkdir(parents=True)
    shutil.copyfile(REPO_ROOT / "configs/frozen_experiment_v1.yaml",
                    root / "configs/frozen_experiment_v1.yaml")
    config = load_frozen_config(root / "configs/frozen_experiment_v1.yaml")
    (root / "configs/decision_policy_v1.yaml").write_text(
        f"policy_metadata:\n  reference_frozen_config_sha256: '{config.canonical_hash}'\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(execution_gate, "verify_checkpoint_integrity", lambda *a, **k: None)

    # --- Stage-2.1 synthetic records + receipt from the real readiness CLI
    (tmp_path / "media").mkdir()
    records, _a, _r, paths = _three_records(tmp_path / "media")
    proposals = root / "data/ground_truth/proposals"
    inventory_path = root / "data/manifests/layer_b_v2_annotation_inventory.json"
    reviews = ground_truth / "reviews"
    inventory: dict[str, dict] = {}
    media: dict[str, dict[str, str]] = {}
    for record in records:
        event_id, cohort = record["event_id"], record["cohort"]
        proposal = proposals / cohort / f"{event_id}_proposal_v1.json"
        proposal.parent.mkdir(parents=True, exist_ok=True)
        # A real, verifiable proposal whose candidates equal the review (nothing was corrected).
        write_json(
            proposal,
            {
                "proposed_timestamps": {
                    name: {
                        "candidate_observable": entry["state"] == "OBSERVABLE",
                        "value_s": entry["value_s"],
                    }
                    for name, entry in record["boundary_adjudications"].items()
                }
            },
        )
        record["proposal_reference"]["proposal_sha256"] = hashlib.sha256(
            proposal.read_bytes()
        ).hexdigest()
        write_json(reviews / cohort / f"{record['review_id']}_review.json", record)
        entry: dict[str, Any] = {"category": cohort, "event_id": event_id}
        key = f"{cohort}/{event_id}"
        media[key] = {}
        for side in ("front", "back"):
            source = Path(paths[event_id][side])
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            entry[side] = {"path": str(source), "sha256": digest}
            relative = f"data/raw/layer_b/v2/{cohort}/{event_id}/camera_{side}.mov"
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            media[key][side] = digest
            media[key][f"{side}_relative"] = relative
        inventory[key] = entry
    for extra in (TRAIN_ONLY, VAL_ONLY):  # fixture events without approved records
        cohort, event = extra.split("/")
        inventory[extra] = {
            "category": cohort,
            "event_id": event,
            "front": {"path": "x", "sha256": "a" * 64},
            "back": {"path": "y", "sha256": "b" * 64},
        }
    write_json(inventory_path, inventory)
    code = readiness_main(
        [
            "--reviews-dir", str(reviews),
            "--allowlist", str(ground_truth / "authorized_reviewers.json"),
            "--inventory", str(inventory_path),
            "--proposals-dir", str(proposals),
            "--stage", "synthetic_stage",
            "--repository-root", str(root),
            "--receipt-path", str(root / governance.PROMOTION_RECEIPT_RELATIVE),
        ]
    )
    assert code == 0

    # --- decisions
    write_json(
        root / governance.SPLIT_DECISION_RELATIVE,
        envelope(governance.SPLIT_DECISION_SCHEMA, partitions=split),
    )
    write_json(
        root / governance.R04_DECISION_RELATIVE,
        envelope(
            governance.R04_DECISION_SCHEMA,
            event_modes=modes,
            accepted_sync_events=list(accepted_sync),
        ),
    )
    write_json(
        root / governance.PROTOCOL_DECISION_RELATIVE,
        envelope(governance.PROTOCOL_DECISION_SCHEMA, choices=dict(PREMATURE)),
    )

    # --- calibration manifest (only consulted for dual_camera events)
    verdicts = dict(calibration_verdicts or {})
    import yaml

    calibration_events = {}
    for key in TEST_EVENTS:
        cohort, event = key.split("/")
        calibration_events[key] = {
            "cohort": cohort,
            "event_id": event,
            "calibration_verdict": verdicts.get(key, "CALIBRATION_SUPPORTED"),
            "camera_front": {
                "relative_path": media[key]["front_relative"],
                "sha256": media[key]["front"],
                "offset_s": 0.0,
            },
            "camera_back": {
                "relative_path": media[key]["back_relative"],
                "sha256": media[key]["back"],
                "offset_s": BACK_OFFSET_S,
                "uncertainty_s": 0.05,
            },
        }
    (root / "data/manifests").mkdir(parents=True, exist_ok=True)
    (root / governance.CALIBRATION_MANIFEST_RELATIVE).write_text(
        yaml.safe_dump(
            {
                "manifest_version": "0.0.0_SYNTHETIC",
                "status": "CANDIDATE_UNVALIDATED_DO_NOT_MERGE",
                "events": calibration_events,
            }
        ),
        encoding="utf-8",
    )

    # --- evidence payloads + manifest
    provenance_base = {
        "frozen_config_canonical_sha256": config.canonical_hash,
        "checkpoint_sha256": {
            "vision": config.checkpoints.vision.expected_sha256,
            "audio_v3": config.checkpoints.audio_v3.expected_sha256,
        },
        "vision_confidence_threshold": config.vision.confidence_threshold_approach,
        "audio_operating_threshold": config.audio.operating_threshold,
        "inference_run_id": "synthetic-fixture-run",
        "annotation_labels_used": False,
        "generated_by": "synthetic_test_fixture (not model output of any real clip)",
    }
    manifest_events = []
    for event_id in ALL_EVENTS:
        cohort = event_id.split("/")[0]
        kind = "no_train" if cohort == "no_train_events" else "train"
        mode = modes[event_id]
        streams = synthetic_streams(kind, mode)
        media_hashes = (
            {"front": media[event_id]["front"], "back": media[event_id]["back"]}
            if event_id in media
            else {"front": "a" * 64, "back": "b" * 64}
        )
        if mode == "single_camera":
            media_hashes = {"front": media_hashes["front"]}
        payload = build_replay_evidence_payload(
            event_id=event_id,
            cohort=cohort,
            camera_mode=mode,
            streams=streams,
            provenance={**provenance_base, "media_sha256": media_hashes},
        )
        source = root / "data/manifests" / f"{event_id.replace('/', '__')}.evidence.json"
        source.write_text(json.dumps(payload), encoding="utf-8")
        role = next(r for r, ids in split.items() if event_id in ids)
        manifest_events.append(
            {
                "event_id": event_id,
                "cohort": cohort,
                "split_role": role,
                "source_path": source.name,
                "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            }
        )
    write_json(
        root / "data/manifests/phase12_evaluation_inputs.json",
        {
            "schema_version": "phase12-evaluation-inputs/1",
            "evidence_classification": "real",
            "partitions": split,
            "events": manifest_events,
            "camera_scope_by_event": modes,
            "accepted_sync_events": list(accepted_sync),
        },
    )
    workspace = Workspace(
        root=root, tmp=tmp_path, config_hash=config.canonical_hash, modes=modes, media=media
    )
    if authorize:
        workspace.record_authorization()
    return workspace
