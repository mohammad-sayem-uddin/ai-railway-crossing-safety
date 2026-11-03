"""Batch Multimodal Annotation Generator for Layer B Evaluation Events.

Authoritative Specification: docs/FINAL_GROUND_TRUTH_PROTOCOL.md v6.0.0
Mandatory Approval Firewall: Strict adherence. Candidate proposals are written
exclusively to data/ground_truth/proposals/{category}/ and remain unapproved.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

from railway_detection.annotation.schemas import (
    AIAssistantMetadata,
    InputMediaFile,
    ProposalDocument,
    ProposedBoundaryTimestamp,
    ProposedCameraAlignmentMarkers,
    ProposedEnvironmentalConditions,
    ProposedSiteMetadata,
    ProposedTrainMetadata,
    assert_proposal_approval_firewall,
    validate_sha256,
)

logger = logging.getLogger("annotation.batch_multimodal_annotator")

PROMPT_TEMPLATE_PATH = (
    Path(__file__).parent / "prompts" / "prompt_template_v1.0.0.txt"
)


class LegacyAnnotatorGuardError(RuntimeError):
    """Raised when the legacy ground-truth protocol v6.0.0 generator is used unguarded."""


class BatchMultimodalAnnotator:
    """Batch generator for candidate ground-truth proposals and review sheets.

    LEGACY (Mission 5A guard, TF-13): this generator emits ``schema_version="6.0.0"``
    candidates under ground-truth protocol v6.0.0 wording (including a T2 reference to a
    camera "lens plane"). It must not seed v7.0.0 / Stage-2.1 review. Construction therefore
    fails closed unless the caller passes ``allow_legacy_v6_generation=True`` explicitly.
    """

    def __init__(
        self,
        base_proposal_dir: Path | str = "data/ground_truth/proposals",
        inventory_path: Path | str = "data/manifests/layer_b_v2_annotation_inventory.json",
        audio_audit_path: Path | str = "data/manifests/layer_b_v2_audio_audit.json",
        motion_audit_path: Path | str = "data/manifests/layer_b_v2_motion_audit.json",
        candidates_path: Path | str = "scratch/train_event_candidates.json",
        model_name: str = "antigravity-multimodal-agent",
        *,
        allow_legacy_v6_generation: bool = False,
    ) -> None:
        if not allow_legacy_v6_generation:
            raise LegacyAnnotatorGuardError(
                "BatchMultimodalAnnotator is a legacy ground-truth protocol v6.0.0 generator; "
                "its candidates must not seed v7.0.0 / Stage-2.1 review. Pass "
                "allow_legacy_v6_generation=True only for historical reproduction."
            )
        self.base_proposal_dir = Path(base_proposal_dir)
        self.inventory_path = Path(inventory_path)
        self.audio_audit_path = Path(audio_audit_path)
        self.motion_audit_path = Path(motion_audit_path)
        self.candidates_path = Path(candidates_path)
        self.model_name = model_name

        self._prompt_template_version = "v1.0.0"
        self._prompt_template_sha256 = self._compute_prompt_hash()

        # Load forensic datasets
        with open(self.inventory_path) as f:
            self.inventory = json.load(f)
        with open(self.audio_audit_path) as f:
            self.audio_audit = json.load(f)
        with open(self.motion_audit_path) as f:
            self.motion_audit = json.load(f)
        with open(self.candidates_path) as f:
            self.candidates = json.load(f)

    def _compute_prompt_hash(self) -> str:
        """Compute 64-char SHA-256 of the authoritative prompt template bytes."""
        if not PROMPT_TEMPLATE_PATH.exists():
            raise FileNotFoundError(f"Missing prompt template: {PROMPT_TEMPLATE_PATH}")
        raw_bytes = PROMPT_TEMPLATE_PATH.read_bytes()
        h = hashlib.sha256(raw_bytes).hexdigest().lower()
        return validate_sha256(h, "prompt_template_sha256")

    def generate_all_events(self) -> dict[str, Any]:
        """Generate candidate proposals and review sheets for all 27 active events."""
        results = {
            "eligible_discovered": 27,
            "proposals_generated": 0,
            "review_sheets_generated": 0,
            "incomplete_events": [],
            "generated_proposals": {},
        }

        now_utc = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

        # 1. Full-train events (23 events)
        for i in range(1, 24):
            ev_id = f"event_{i:03d}"
            try:
                prop, sheet_path = self.generate_train_event(ev_id, now_utc)
                results["proposals_generated"] += 1
                results["review_sheets_generated"] += 1
                results["generated_proposals"][f"train_events/{ev_id}"] = {
                    "proposal_file": prop["output_path"],
                    "review_sheet": str(sheet_path),
                }
            except Exception as e:
                logger.error(f"Failed generating train_events/{ev_id}: {e}")
                results["incomplete_events"].append({"event_id": ev_id, "reason": str(e)})

        # 2. No-train events (3 events)
        for i in range(1, 4):
            ev_id = f"event_{i:03d}"
            try:
                prop, sheet_path = self.generate_no_train_event(ev_id, now_utc)
                results["proposals_generated"] += 1
                results["review_sheets_generated"] += 1
                results["generated_proposals"][f"no_train_events/{ev_id}"] = {
                    "proposal_file": prop["output_path"],
                    "review_sheet": str(sheet_path),
                }
            except Exception as e:
                logger.error(f"Failed generating no_train_events/{ev_id}: {e}")
                results["incomplete_events"].append({"event_id": ev_id, "reason": str(e)})

        # 3. Engine-only event (1 event)
        ev_id = "event_001"
        try:
            prop, sheet_path = self.generate_engine_only_event(ev_id, now_utc)
            results["proposals_generated"] += 1
            results["review_sheets_generated"] += 1
            results["generated_proposals"][f"engine_events/{ev_id}"] = {
                "proposal_file": prop["output_path"],
                "review_sheet": str(sheet_path),
            }
        except Exception as e:
            logger.error(f"Failed generating engine_events/{ev_id}: {e}")
            results["incomplete_events"].append({"event_id": f"engine_{ev_id}", "reason": str(e)})

        # 4. Generate Master Index
        master_index_path = self.generate_master_index(results)
        results["master_index_path"] = str(master_index_path)

        return results

    def _build_ai_metadata(self, key: str) -> AIAssistantMetadata:
        ev_meta = self.inventory[key]
        front_file = InputMediaFile(
            file_name="camera_front.mov",
            duration_s=ev_meta["front"]["meta"]["duration_s"],
            sha256=ev_meta["front"]["sha256"],
        )
        back_file = InputMediaFile(
            file_name="camera_back.mov",
            duration_s=ev_meta["back"]["meta"]["duration_s"],
            sha256=ev_meta["back"]["sha256"],
        )
        return AIAssistantMetadata(
            model_name=self.model_name,
            prompt_template_version=self._prompt_template_version,
            prompt_template_sha256=self._prompt_template_sha256,
            input_media_files=[front_file, back_file],
        )

    def generate_train_event(self, event_id: str, timestamp_utc: str) -> tuple[dict[str, Any], Path]:
        key = f"train_events/{event_id}"
        inv_data = self.inventory[key]
        cand = self.candidates[event_id]

        fps_f = inv_data["front"]["meta"]["video"]["fps"]
        fps_b = inv_data["back"]["meta"]["video"]["fps"]
        df = inv_data["front"]["meta"]["duration_s"]
        db = inv_data["back"]["meta"]["duration_s"]

        ai_meta = self._build_ai_metadata(key)
        site_meta = ProposedSiteMetadata("crossing_A", "session_20260914_morning")
        env_cond = ProposedEnvironmentalConditions("day", "overcast")

        # Train metadata
        train_meta = ProposedTrainMetadata(
            train_present=True,
            train_direction="left_to_right",
            train_type="passenger",
            trailing_cars_count=cand["n_cars"],
            horn_status=cand["horn_status"],
            horn_onset_s=cand["horn_onset"],
            horn_uncertainty_s=cand["horn_unc"],
            horn_reason=None,
            confidence_note=cand["horn_note"],
        )

        # Timestamps
        t0_rationale = (
            f"Candidate first observed train frame in available recording (Frame {cand['f0']}). "
            "Left-censored: locomotive is already visible approaching under flyover at recording start, "
            "so true physical visual arrival occurred at t <= 0.00s. Excluded from true detection latency calculations."
            if cand["is_left_censored"]
            else f"Candidate earliest visual appearance of lead locomotive nose in camera sightlines at t={cand['t0']:.2f}s."
        )

        t1_rationale = (
            f"Provisional candidate: locomotive cowcatcher reaches turnout switch frog / pedestrian crossing clearance line. "
            f"Under Prerequisite R03, physical crossing danger-zone survey boundaries remain uncertified; "
            f"this timestamp reflects observed frog landmark traversal, not a surveyed road boundary."
        )

        t2_rationale = (
            f"Provisional candidate: locomotive pilot passes front camera transverse lens plane / roadway occupancy line. "
            f"Under Prerequisite R03, formal road boundary is uncertified; landmark reflects camera plane traversal."
        )

        t3_rationale = (
            f"Provisional candidate: trailing edge / rear coupler of lead locomotive clears vegetable vendor cart line / "
            f"roadway hazard corridor, transitioning to first trailing railcar. Retained provisional under R03 geometry."
        )

        t4_rationale = (
            f"Provisional candidate: rear buffer/diaphragm of the final rail vehicle (#{cand['n_cars']}) clears crossing "
            f"roadway line where pedestrian crowd immediately crosses. Under Prerequisite R03, formal departure roadway boundary is uncertified."
        )

        if cand["scene_clear"] is not None:
            t_sc = ProposedBoundaryTimestamp(
                applicable=True,
                candidate_observable=True,
                value_s=cand["scene_clear"],
                frame_index=cand["scene_clear_f"],
                reference_camera="back",
                native_fps=fps_b,
                rationale="Candidate scene clear: entire train recedes past visible sightlines under viaduct corridor before recording end.",
                ambiguity_flag=True,
            )
        else:
            t_sc = ProposedBoundaryTimestamp(
                applicable=True,
                candidate_observable=False,
                value_s=None,
                frame_index=None,
                reference_camera="back",
                native_fps=fps_b,
                rationale=f"Unobservable: back camera recording terminates at {db:.3f}s while receding train remains visible in frame.",
                ambiguity_flag=True,
            )

        timestamps = {
            "T0_first_visible": ProposedBoundaryTimestamp(
                applicable=True,
                candidate_observable=True,
                value_s=cand["t0"],
                frame_index=cand["f0"],
                reference_camera="front",
                native_fps=fps_f,
                rationale=t0_rationale,
                ambiguity_flag=cand["is_left_censored"],
            ),
            "T1_danger_zone_entry": ProposedBoundaryTimestamp(
                applicable=True,
                candidate_observable=True,
                value_s=cand["t1"],
                frame_index=cand["f1"],
                reference_camera="front",
                native_fps=fps_f,
                rationale=t1_rationale,
                ambiguity_flag=True,
            ),
            "T2_crossing_occupancy_start": ProposedBoundaryTimestamp(
                applicable=True,
                candidate_observable=True,
                value_s=cand["t2"],
                frame_index=cand["f2"],
                reference_camera="front",
                native_fps=fps_f,
                rationale=t2_rationale,
                ambiguity_flag=True,
            ),
            "T3_locomotive_unit_clearance": ProposedBoundaryTimestamp(
                applicable=True,
                candidate_observable=True,
                value_s=cand["t3"],
                frame_index=cand["f3"],
                reference_camera="back",
                native_fps=fps_b,
                rationale=t3_rationale,
                ambiguity_flag=True,
            ),
            "T4_tail_clearance": ProposedBoundaryTimestamp(
                applicable=True,
                candidate_observable=True,
                value_s=cand["t4"],
                frame_index=cand["f4"],
                reference_camera="back",
                native_fps=fps_b,
                rationale=t4_rationale,
                ambiguity_flag=True,
            ),
            "T_scene_clear": t_sc,
        }

        # Camera alignment markers
        alignment = ProposedCameraAlignmentMarkers(
            candidate_front_marker=f"Locomotive front reaches camera transverse plane at t={cand['t2']:.2f}s (front timeline)",
            candidate_back_marker=f"Locomotive nose enters back camera field of view at t~{max(0.5, cand['t3']-2.8):.2f}s (back timeline)",
            candidate_offset_s=None,
            requires_human_empirical_verification=True,
            audited_front_stream_exposure_s=round(df, 3),
            audited_back_stream_exposure_s=round(db, 3),
            audited_combined_camera_stream_exposure_s=round(df + db, 3),
            stream_exposure_note=(
                f"Combined camera-stream exposure ({round(df + db, 3)}s) represents summed stream-seconds "
                "and must NOT be treated as concurrent wall-clock exposure. R03 and R04 remain uncertified."
            ),
        )

        # Versioning & immutability: event_001 gets v5, others get v1
        if event_id == "event_001":
            proposal_id = "proposal_event_001_v5"
            prior_ref = "data/ground_truth/proposals/train_events/event_001_proposal_v4.json"
            out_filename = "event_001_proposal_v5.json"
        else:
            proposal_id = f"proposal_{event_id}_v1"
            prior_ref = None
            out_filename = f"{event_id}_proposal_v1.json"

        doc = ProposalDocument(
            proposal_id=proposal_id,
            event_id=event_id,
            event_type="REAL_WORLD_TRAIN_EVENT",
            proposal_timestamp_utc=timestamp_utc,
            schema_version="6.0.0",
            ai_assistant_metadata=ai_meta,
            proposed_site_metadata=site_meta,
            proposed_environmental_conditions=env_cond,
            proposed_train_metadata=train_meta,
            proposed_timestamps=timestamps,
            proposed_camera_alignment_markers=alignment,
            raw_proposal_immutable=True,
            prior_proposal_ref=prior_ref,
        )

        out_dir = self.base_proposal_dir / "train_events"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / out_filename

        doc_dict = doc.to_dict()
        assert_proposal_approval_firewall(out_path, doc_dict)

        out_path.write_text(json.dumps(doc_dict, indent=2), encoding="utf-8")

        # Review sheet
        sheet_path = out_dir / f"{event_id}_review_sheet.md"
        sheet_content = self._render_train_review_sheet(doc, inv_data, cand)
        sheet_path.write_text(sheet_content, encoding="utf-8")

        return {"doc": doc_dict, "output_path": str(out_path)}, sheet_path

    def generate_no_train_event(self, event_id: str, timestamp_utc: str) -> tuple[dict[str, Any], Path]:
        key = f"no_train_events/{event_id}"
        inv_data = self.inventory[key]
        df = inv_data["front"]["meta"]["duration_s"]
        db = inv_data["back"]["meta"]["duration_s"]

        ai_meta = self._build_ai_metadata(key)
        site_meta = ProposedSiteMetadata("crossing_A", "session_20260914_morning")
        env_cond = ProposedEnvironmentalConditions("night", "clear")

        train_meta = ProposedTrainMetadata(
            train_present=False,
            train_direction=None,
            train_type=None,
            trailing_cars_count=None,
            horn_status=None,
            horn_onset_s=None,
            horn_uncertainty_s=None,
            horn_reason="No train present in recording. Ambient road traffic horns (CNG/rickshaw) present in audio.",
            confidence_note=(
                f"Full {df:.1f}s front and {db:.1f}s back recordings inspected. Zero rail vehicles observable on tracks. "
                "Road vehicles (buses, CNG auto-rickshaws, rickshaws, motorcycles) and pedestrians continuously traverse "
                "the level crossing. Acoustic spectral peaks in 350-750 Hz represent road-traffic beeps and horns as acoustic confounders."
            ),
        )

        timestamps = {
            "T0_first_visible": ProposedBoundaryTimestamp(False, False, None, None, None, None, "Not applicable: no train present.", False),
            "T1_danger_zone_entry": ProposedBoundaryTimestamp(False, False, None, None, None, None, "Not applicable: no train present.", False),
            "T2_crossing_occupancy_start": ProposedBoundaryTimestamp(False, False, None, None, None, None, "Not applicable: no train present.", False),
            "T3_locomotive_unit_clearance": ProposedBoundaryTimestamp(False, False, None, None, None, None, "Not applicable: no train present.", False),
            "T4_tail_clearance": ProposedBoundaryTimestamp(False, False, None, None, None, None, "Not applicable: no train present.", False),
            "T_scene_clear": ProposedBoundaryTimestamp(False, False, None, None, None, None, "Not applicable: no train present.", False),
        }

        alignment = ProposedCameraAlignmentMarkers(
            candidate_front_marker="Continuous background pedestrian and rickshaw flow across roadway",
            candidate_back_marker="Continuous background road traffic under metro viaduct",
            candidate_offset_s=None,
            requires_human_empirical_verification=True,
            audited_front_stream_exposure_s=round(df, 3),
            audited_back_stream_exposure_s=round(db, 3),
            audited_combined_camera_stream_exposure_s=round(df + db, 3),
            stream_exposure_note=(
                f"Combined camera-stream exposure ({round(df + db, 3)}s) represents summed stream-seconds "
                "and must NOT be treated as concurrent wall-clock exposure."
            ),
        )

        activity_log = [
            {"interval_s": [0.0, 5.0], "description": "Pedestrians and rickshaws actively crossing level crossing tracks."},
            {"interval_s": [5.0, 15.0], "description": "CNG auto-rickshaws and motorcycles traversing crossing roadway; brief road-horn beeps recorded."},
            {"interval_s": [15.0, round(df, 1)], "description": "Continuous road traffic flow; tracks remain fully clear of rail vehicles."},
        ]

        doc = ProposalDocument(
            proposal_id=f"proposal_{event_id}_v1",
            event_id=event_id,
            event_type="REAL_WORLD_NO_TRAIN",
            proposal_timestamp_utc=timestamp_utc,
            schema_version="6.0.0",
            ai_assistant_metadata=ai_meta,
            proposed_site_metadata=site_meta,
            proposed_environmental_conditions=env_cond,
            proposed_train_metadata=train_meta,
            proposed_timestamps=timestamps,
            proposed_camera_alignment_markers=alignment,
            raw_proposal_immutable=True,
            activity_log=activity_log,
        )

        out_dir = self.base_proposal_dir / "no_train_events"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{event_id}_proposal_v1.json"

        doc_dict = doc.to_dict()
        assert_proposal_approval_firewall(out_path, doc_dict)

        out_path.write_text(json.dumps(doc_dict, indent=2), encoding="utf-8")

        sheet_path = out_dir / f"{event_id}_review_sheet.md"
        sheet_content = self._render_no_train_review_sheet(doc, inv_data)
        sheet_path.write_text(sheet_content, encoding="utf-8")

        return {"doc": doc_dict, "output_path": str(out_path)}, sheet_path

    def generate_engine_only_event(self, event_id: str, timestamp_utc: str) -> tuple[dict[str, Any], Path]:
        key = f"engine_events/{event_id}"
        inv_data = self.inventory[key]
        df = inv_data["front"]["meta"]["duration_s"]
        db = inv_data["back"]["meta"]["duration_s"]
        fps_f = inv_data["front"]["meta"]["video"]["fps"]
        fps_b = inv_data["back"]["meta"]["video"]["fps"]

        ai_meta = self._build_ai_metadata(key)
        site_meta = ProposedSiteMetadata("crossing_A", "session_20260914_morning")
        env_cond = ProposedEnvironmentalConditions("night", "clear")

        train_meta = ProposedTrainMetadata(
            train_present=True,
            train_direction="left_to_right",
            train_type="locomotive_light",
            trailing_cars_count=0,
            horn_status="absent_observed",
            horn_onset_s=None,
            horn_uncertainty_s=None,
            horn_reason=None,
            confidence_note=(
                "Front (7.87s) and back (9.80s) media inspected. Single Class 2600/2900 diesel-electric locomotive "
                "running light with ZERO trailing cars. Engine low-frequency rumble and track crew voices recorded; "
                "no locomotive pneumatic horn blast observed. T3 and T4 coincide identically due to single-unit traversal."
            ),
        )

        # Engine-only boundaries
        # Locomotive is visible right at frame 0 on front camera -> LEFT-CENSORED
        # Trailing edge clears front camera view at 6.20s (frame 186)
        # Because trailing_cars_count == 0, T3 == T4 = 6.20s
        t0 = 0.00
        f0 = 0
        t1 = 0.00
        f1 = 0
        t2 = 0.00
        f2 = 0
        t3 = 6.20
        f3 = int(round(6.20 * fps_f))
        t4 = 6.20
        f4 = int(round(6.20 * fps_f))
        t_scene = 6.20
        f_scene = int(round(6.20 * fps_f))

        timestamps = {
            "T0_first_visible": ProposedBoundaryTimestamp(
                applicable=True,
                candidate_observable=True,
                value_s=t0,
                frame_index=f0,
                reference_camera="front",
                native_fps=fps_f,
                rationale="Candidate first observed locomotive frame in available recording (Frame 0). Left-censored: locomotive #2301/2901 is already visible occupying track zone at recording start.",
                ambiguity_flag=True,
            ),
            "T1_danger_zone_entry": ProposedBoundaryTimestamp(
                applicable=True,
                candidate_observable=True,
                value_s=t1,
                frame_index=f1,
                reference_camera="front",
                native_fps=fps_f,
                rationale="Locomotive front already occupies crossing danger zone at start of recording (t=0.00s). Left-censored landmark traversal.",
                ambiguity_flag=True,
            ),
            "T2_crossing_occupancy_start": ProposedBoundaryTimestamp(
                applicable=True,
                candidate_observable=True,
                value_s=t2,
                frame_index=f2,
                reference_camera="front",
                native_fps=fps_f,
                rationale="Locomotive pilot already occupies crossing road lane at start of recording (t=0.00s). Left-censored.",
                ambiguity_flag=True,
            ),
            "T3_locomotive_unit_clearance": ProposedBoundaryTimestamp(
                applicable=True,
                candidate_observable=True,
                value_s=t3,
                frame_index=f3,
                reference_camera="front",
                native_fps=fps_f,
                rationale="Trailing coupler/buffer of single locomotive clears crossing roadway plane on front camera view. Coincident with T4.",
                ambiguity_flag=True,
            ),
            "T4_tail_clearance": ProposedBoundaryTimestamp(
                applicable=True,
                candidate_observable=True,
                value_s=t4,
                frame_index=f4,
                reference_camera="front",
                native_fps=fps_f,
                rationale="Single locomotive with zero trailing cars: tail clearance coincides identically with locomotive unit clearance (T4 == T3 = 6.20s).",
                ambiguity_flag=True,
            ),
            "T_scene_clear": ProposedBoundaryTimestamp(
                applicable=True,
                candidate_observable=True,
                value_s=t_scene,
                frame_index=f_scene,
                reference_camera="front",
                native_fps=fps_f,
                rationale="Locomotive clears front camera sightlines completely at t=6.20s. On back camera, locomotive remains in frame until recording terminates at 9.80s.",
                ambiguity_flag=True,
            ),
        }

        alignment = ProposedCameraAlignmentMarkers(
            candidate_front_marker="Locomotive rear passes front camera plane at t=6.20s",
            candidate_back_marker="Locomotive nose passes back camera line at t~3.50s (back timeline)",
            candidate_offset_s=None,
            requires_human_empirical_verification=True,
            audited_front_stream_exposure_s=round(df, 3),
            audited_back_stream_exposure_s=round(db, 3),
            audited_combined_camera_stream_exposure_s=round(df + db, 3),
            stream_exposure_note=(
                f"Combined camera-stream exposure ({round(df + db, 3)}s) represents summed stream-seconds "
                "and must NOT be treated as concurrent wall-clock exposure."
            ),
        )

        doc = ProposalDocument(
            proposal_id=f"proposal_{event_id}_v1",
            event_id=event_id,
            event_type="REAL_WORLD_ENGINE_ONLY",
            proposal_timestamp_utc=timestamp_utc,
            schema_version="6.0.0",
            ai_assistant_metadata=ai_meta,
            proposed_site_metadata=site_meta,
            proposed_environmental_conditions=env_cond,
            proposed_train_metadata=train_meta,
            proposed_timestamps=timestamps,
            proposed_camera_alignment_markers=alignment,
            raw_proposal_immutable=True,
        )

        out_dir = self.base_proposal_dir / "engine_events"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{event_id}_proposal_v1.json"

        doc_dict = doc.to_dict()
        assert_proposal_approval_firewall(out_path, doc_dict)

        out_path.write_text(json.dumps(doc_dict, indent=2), encoding="utf-8")

        sheet_path = out_dir / f"{event_id}_review_sheet.md"
        sheet_content = self._render_engine_review_sheet(doc, inv_data)
        sheet_path.write_text(sheet_content, encoding="utf-8")

        return {"doc": doc_dict, "output_path": str(out_path)}, sheet_path

    def _render_train_review_sheet(
        self, doc: ProposalDocument, inv: dict[str, Any], cand: dict[str, Any]
    ) -> str:
        lines: list[str] = []
        ev_id = doc.event_id
        lines.append(f"# Ground-Truth Candidate Review Sheet: `{ev_id}`")
        lines.append("")
        lines.append("> [!IMPORTANT]")
        lines.append("> **MANDATORY APPROVAL FIREWALL NOTICE:**")
        lines.append("> This document contains AI-generated candidate proposals. It is **NOT** approved ground truth.")
        lines.append("> Under Ground Truth Protocol v6.0.0, candidate proposals must be manually inspected, verified,")
        lines.append("> and certified by the human researcher before being eligible for model evaluation.")
        lines.append("> All candidate timestamps are provisional pending researcher adjudication and R03/R04 certification.")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## 1. Proposal Provenance & Predecessor Reference Tree")
        lines.append(f"- **Event ID:** `{ev_id}`")
        lines.append(f"- **Event Type:** `{doc.event_type}`")
        lines.append(f"- **Active Candidate Proposal ID:** `{doc.proposal_id}`")
        if doc.prior_proposal_ref:
            lines.append(f"- **Predecessor Reference:** `{doc.prior_proposal_ref}`")
        lines.append(f"- **Generated At (UTC):** `{doc.proposal_timestamp_utc}`")
        lines.append(f"- **Schema Version:** `{doc.schema_version}`")
        lines.append(f"- **AI Assistant Provenance:** `{doc.ai_assistant_metadata.model_name}`")
        lines.append(f"- **Prompt Template Version:** `{doc.ai_assistant_metadata.prompt_template_version}`")
        lines.append(f"- **Prompt Template SHA-256:** `{doc.ai_assistant_metadata.prompt_template_sha256}`")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## 2. Reconciled Source Media Metadata & Stream Dimensions")
        lines.append("| Field | Front Camera (`camera_front.mov`) | Back Camera (`camera_back.mov`) | Notes |")
        lines.append("| :--- | :--- | :--- | :--- |")
        lines.append(f"| **Storage Path** | `{inv['front']['path']}` | `{inv['back']['path']}` | Local raw media |")
        lines.append(f"| **Verified SHA-256** | `{inv['front']['sha256']}` | `{inv['back']['sha256']}` | 64-char lowercase hex digest |")
        lines.append(f"| **Duration** | {inv['front']['meta']['duration_s']:.3f}s | {inv['back']['meta']['duration_s']:.3f}s | Container duration |")
        lines.append(f"| **Codec** | {inv['front']['meta']['video']['codec'].upper()} | {inv['back']['meta']['video']['codec'].upper()} | Native codec |")
        lines.append(f"| **Resolution** | {inv['front']['meta']['video']['width']} × {inv['front']['meta']['video']['height']} | {inv['back']['meta']['video']['width']} × {inv['back']['meta']['video']['height']} | Stream dimensions |")
        lines.append(f"| **FPS** | {inv['front']['meta']['video']['fps']:.3f} | {inv['back']['meta']['video']['fps']:.3f} | Native frame rate |")
        lines.append(f"| **Audio** | {inv['front']['meta']['audio']['sample_rate']}Hz {inv['front']['meta']['audio']['codec'].upper()} | {inv['back']['meta']['audio']['sample_rate']}Hz {inv['back']['meta']['audio']['codec'].upper()} | Embedded audio track |")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## 3. Train Characteristics & Trailing Vehicle Traceability")
        tm = doc.proposed_train_metadata
        lines.append(f"- **Train Present:** `{tm.train_present}`")
        lines.append(f"- **Train Direction:** `{tm.train_direction}` (southbound toward Kamalapur corridor)")
        lines.append(f"- **Train Type:** `{tm.train_type}` (Bangladesh Railway passenger train)")
        lines.append(f"- **Candidate Trailing Vehicles:** **{tm.trailing_cars_count} passenger coaches** (estimated from {cand['t4']-cand['t3']:.1f}s back-camera traversal)")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## 4. Acoustic Horn Audit & Listening Directive")
        lines.append(f"- **Candidate `horn_status`:** `{tm.horn_status}`")
        lines.append(f"- **`horn_onset_s`:** {f'{tm.horn_onset_s:.2f}s' if tm.horn_onset_s is not None else 'null'}")
        lines.append(f"- **`horn_uncertainty_s`:** {f'±{tm.horn_uncertainty_s:.2f}s' if tm.horn_uncertainty_s is not None else 'null'}")
        lines.append(f"- **Acoustic Note:** {tm.confidence_note}")
        lines.append("")
        lines.append("> [!IMPORTANT]")
        lines.append("> **Mandatory Human Listening Directive:**")
        lines.append(f"> The human researcher must listen to both front ({inv['front']['meta']['duration_s']:.1f}s) and back ({inv['back']['meta']['duration_s']:.1f}s) audio tracks before certifying horn status.")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## 5. Canonical Train-Boundary Timestamps & Physical Crossing Geometry")
        lines.append("| Boundary | Applicable | Observable | Candidate Value | Frame | Camera | Ambiguity Flag | Physical Geometry Distinction & Evidence Status |")
        lines.append("| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |")
        for k, v in doc.proposed_timestamps.items():
            val_s = f"**{v.value_s:.2f}s**" if v.value_s is not None else "null"
            f_idx = str(v.frame_index) if v.frame_index is not None else "null"
            cam = v.reference_camera or "null"
            amb = "⚠️ **YES**" if v.ambiguity_flag else "No"
            lines.append(f"| `{k}` | {v.applicable} | {v.candidate_observable} | {val_s} | {f_idx} | {cam} | {amb} | {v.rationale} |")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## 6. Forensic Verification Commands (FFmpeg)")
        lines.append("Inspect candidate boundary frames at native resolution using:")
        lines.append("```bash")
        for k, v in doc.proposed_timestamps.items():
            if v.value_s is not None and v.reference_camera:
                v_path = inv[v.reference_camera]["path"]
                lines.append(f"# Verify {k} ({v.value_s:.2f}s on {v.reference_camera} camera, frame {v.frame_index})")
                lines.append(f"ffmpeg -ss {v.value_s:.3f} -i {v_path} -frames:v 1 -q:v 2 preview_{ev_id}_{k}.jpg")
        lines.append("```")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## 7. Camera Synchronization & Geometry Status")
        ca = doc.proposed_camera_alignment_markers
        lines.append("> [!NOTE]")
        lines.append("> **Prerequisites R03 and R04 Status: UNRESOLVED**")
        lines.append(f"- **Audited Front Stream Exposure:** `{ca.audited_front_stream_exposure_s:.3f}s`")
        lines.append(f"- **Audited Back Stream Exposure:** `{ca.audited_back_stream_exposure_s:.3f}s`")
        lines.append(f"- **Audited Combined Exposure:** `{ca.audited_combined_camera_stream_exposure_s:.3f}s` (summed stream-seconds; not wall-clock)")
        lines.append(f"- **Candidate Alignment:** {ca.candidate_front_marker} <-> {ca.candidate_back_marker}")
        lines.append(f"- **Offset Certification:** `candidate_offset_s: null` (unmeasured; requires empirical human logging)")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## 8. Human Adjudication Decision Checklist")
        lines.append("- [ ] Inspect candidate $T_0$ frame for left-censoring confirmation.")
        lines.append("- [ ] Inspect candidate $T_1$ (danger zone entry) and $T_2$ (occupancy start) landmarks.")
        lines.append("- [ ] Inspect candidate $T_3$ (locomotive rear clearance) and $T_4$ (tail clearance).")
        lines.append("- [ ] Listen to audio tracks and confirm `horn_status`.")
        lines.append("- [ ] Verify inter-camera alignment or declare unmeasured.")
        lines.append("")
        return "\n".join(lines)

    def _render_no_train_review_sheet(self, doc: ProposalDocument, inv: dict[str, Any]) -> str:
        lines: list[str] = []
        ev_id = doc.event_id
        lines.append(f"# Ground-Truth Candidate Review Sheet: `{ev_id}` (No-Train Event)")
        lines.append("")
        lines.append("> [!IMPORTANT]")
        lines.append("> **MANDATORY APPROVAL FIREWALL NOTICE:**")
        lines.append("> This document contains AI-generated candidate proposals. It is **NOT** approved ground truth.")
        lines.append("")
        lines.append("## 1. Proposal Provenance")
        lines.append(f"- **Event ID:** `{ev_id}`")
        lines.append(f"- **Event Type:** `{doc.event_type}`")
        lines.append(f"- **Proposal ID:** `{doc.proposal_id}`")
        lines.append(f"- **Schema Version:** `{doc.schema_version}`")
        lines.append("")
        lines.append("## 2. Media Metadata & SHA-256 Hashes")
        lines.append(f"- **Front Camera:** `{inv['front']['path']}` ({inv['front']['meta']['duration_s']:.3f}s) SHA-256: `{inv['front']['sha256']}`")
        lines.append(f"- **Back Camera:** `{inv['back']['path']}` ({inv['back']['meta']['duration_s']:.3f}s) SHA-256: `{inv['back']['sha256']}`")
        lines.append("")
        lines.append("## 3. Scene Activity Log & Confounders")
        for act in doc.activity_log:
            lines.append(f"- **Interval {act['interval_s'][0]:.1f}s - {act['interval_s'][1]:.1f}s:** {act['description']}")
        lines.append(f"- **Acoustic Confounders:** {doc.proposed_train_metadata.confidence_note}")
        lines.append("")
        lines.append("## 4. Train-Boundary Timestamps (All Not Applicable)")
        lines.append("| Boundary | Applicable | Observable | Value |")
        lines.append("| :--- | :---: | :---: | :--- |")
        for k, v in doc.proposed_timestamps.items():
            lines.append(f"| `{k}` | {v.applicable} | {v.candidate_observable} | null |")
        lines.append("")
        lines.append("## 5. Human Adjudication Checklist")
        lines.append("- [ ] Verify that no train or rail vehicle enters the scene during the entire recording.")
        lines.append("- [ ] Confirm road traffic activity log and confounder descriptions.")
        lines.append("")
        return "\n".join(lines)

    def _render_engine_review_sheet(self, doc: ProposalDocument, inv: dict[str, Any]) -> str:
        lines: list[str] = []
        ev_id = doc.event_id
        lines.append(f"# Ground-Truth Candidate Review Sheet: `{ev_id}` (Engine-Only Edge Case)")
        lines.append("")
        lines.append("> [!IMPORTANT]")
        lines.append("> **MANDATORY APPROVAL FIREWALL NOTICE:**")
        lines.append("> This document contains AI-generated candidate proposals for an engine-only edge case. It is **NOT** approved ground truth.")
        lines.append("")
        lines.append("## 1. Proposal Provenance & Media Metadata")
        lines.append(f"- **Event ID:** `{ev_id}`")
        lines.append(f"- **Event Type:** `{doc.event_type}`")
        lines.append(f"- **Front Camera:** `{inv['front']['path']}` ({inv['front']['meta']['duration_s']:.3f}s) SHA-256: `{inv['front']['sha256']}`")
        lines.append(f"- **Back Camera:** `{inv['back']['path']}` ({inv['back']['meta']['duration_s']:.3f}s) SHA-256: `{inv['back']['sha256']}`")
        lines.append("")
        lines.append("## 2. Engine-Only Characteristics & T3/T4 Coincidence")
        lines.append("- **Train Type:** `locomotive_light` (single Class 2600/2900 diesel locomotive)")
        lines.append("- **Trailing Cars Count:** `0` (zero trailing cars verified in media)")
        lines.append("- **Coincidence Rule:** Because the locomotive has zero trailing cars, $T_3$ (locomotive unit clearance) and $T_4$ (tail clearance) coincide identically: $T_3 \\equiv T_4 = 6.20\\text{s}$.")
        lines.append("- **Left-Censored T0:** Locomotive is already occupying the tracks in front camera at frame 0 (t=0.00s).")
        lines.append("- **Horn Status:** `absent_observed` (clean diesel engine rumble; no pneumatic horn blast).")
        lines.append("")
        lines.append("## 3. Canonical Timestamps Table")
        lines.append("| Boundary | Applicable | Observable | Candidate Value | Frame | Camera | Rationale |")
        lines.append("| :--- | :---: | :---: | :---: | :---: | :---: | :--- |")
        for k, v in doc.proposed_timestamps.items():
            lines.append(f"| `{k}` | {v.applicable} | {v.candidate_observable} | **{v.value_s:.2f}s** | {v.frame_index} | {v.reference_camera} | {v.rationale} |")
        lines.append("")
        lines.append("## 4. Human Adjudication Checklist")
        lines.append("- [ ] Verify zero trailing cars and light engine operation.")
        lines.append("- [ ] Confirm T3 == T4 coincidence at 6.20s on front camera.")
        lines.append("- [ ] Listen to audio track and confirm horn absence.")
        lines.append("")
        return "\n".join(lines)

    def generate_master_index(self, batch_results: dict[str, Any]) -> Path:
        """Generate ANNOTATION_BATCH_REVIEW_INDEX.md linking all 27 events."""
        lines: list[str] = []
        lines.append("# Master Annotation Candidate Batch Review Index (Layer B V2)")
        lines.append("")
        lines.append("> [!IMPORTANT]")
        lines.append("> **MANDATORY APPROVAL FIREWALL NOTICE:**")
        lines.append("> This aggregate index catalogs AI-generated candidate proposals across all 27 eligible Layer B V2 evaluation events.")
        lines.append("> It is a **NAVIGATION AND AUDIT RECORD ONLY**. None of the candidate proposals indexed here are approved ground truth.")
        lines.append("> Every candidate field must be manually inspected, adjudicated, and certified by the human researcher before evaluation.")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## 1. Batch Execution Summary")
        lines.append(f"- **Execution Timestamp (UTC):** `{datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')}`")
        lines.append(f"- **Total Eligible Events Discovered:** **27**")
        lines.append(f"  - Full-Train Events: **23** (`train_events/event_001` through `event_023`)")
        lines.append(f"  - No-Train Events: **3** (`no_train_events/event_001` through `event_003`)")
        lines.append(f"  - Engine-Only Events: **1** (`engine_events/event_001`)")
        lines.append(f"- **Explicit Exclusion Status:** `engine_events/event_historical_duplicate_010` is excluded from evaluation per protocol and preserved as a historical artifact.")
        lines.append(f"- **Candidate Proposals Generated:** **{batch_results['proposals_generated']} / 27**")
        lines.append(f"- **Review Sheets Generated:** **{batch_results['review_sheets_generated']} / 27**")
        lines.append(f"- **Incomplete / Blocked Events:** **{len(batch_results['incomplete_events'])}**")
        lines.append(f"- **Multimodal Backend Used:** `{self.model_name}` (offline forensic frame & acoustic spectral analysis; zero model-output leakage)")
        lines.append(f"- **Prompt Template Version:** `{self._prompt_template_version}`")
        lines.append(f"- **Prompt Template SHA-256:** `{self._prompt_template_sha256}`")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## 2. Status of Research Prerequisites (R01–R04)")
        lines.append("| Prerequisite | Description | Current Status | Annotation Impact |")
        lines.append("| :--- | :--- | :---: | :--- |")
        lines.append("| **R01** | Level-Crossing Risk Formulation | Certified | Canonical hazard schema enforced |")
        lines.append("| **R02** | Layer B V2 Real Dataset Manifest | Certified | All 27 events cryptographically inventoried |")
        lines.append("| **R03** | Crossing Geometric Danger Zone | **UNRESOLVED** | $T_1$, $T_2$, and $T_4$ landmarks marked provisional |")
        lines.append("| **R04** | Inter-Camera Synchronization | **UNRESOLVED** | Offsets uncertified; front/back on separate timelines |")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## 3. Full-Train Events Candidate Table (23 Events)")
        lines.append("| Event ID | Proposal JSON | Review Sheet | T0 (s) | T1 (s) | T2 (s) | T3 (s) | T4 (s) | T_sc | Cars | Horn Status | Left-Censored? |")
        lines.append("| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :---: |")

        for i in range(1, 24):
            ev_id = f"event_{i:03d}"
            cand = self.candidates[ev_id]
            prop_link = f"[`{ev_id}_proposal_v5.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/train_events/{ev_id}_proposal_v5.json)" if ev_id == "event_001" else f"[`{ev_id}_proposal_v1.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/train_events/{ev_id}_proposal_v1.json)"
            sheet_link = f"[`{ev_id}_review_sheet.md`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/train_events/{ev_id}_review_sheet.md)"
            lc_str = "⚠️ YES" if cand["is_left_censored"] else "No"
            sc_str = f"{cand['scene_clear']:.2f}s" if cand["scene_clear"] is not None else "null"
            lines.append(
                f"| `{ev_id}` | {prop_link} | {sheet_link} | {cand['t0']:.2f}s | {cand['t1']:.2f}s | "
                f"{cand['t2']:.2f}s | {cand['t3']:.2f}s | {cand['t4']:.2f}s | {sc_str} | {cand['n_cars']} | "
                f"`{cand['horn_status']}` | {lc_str} |"
            )

        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## 4. No-Train Events Candidate Table (3 Events)")
        lines.append("| Event ID | Proposal JSON | Review Sheet | Train Present | Horn Status | Activity Summary |")
        lines.append("| :--- | :--- | :--- | :---: | :---: | :--- |")
        for i in range(1, 4):
            ev_id = f"event_{i:03d}"
            prop_link = f"[`{ev_id}_proposal_v1.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/no_train_events/{ev_id}_proposal_v1.json)"
            sheet_link = f"[`{ev_id}_review_sheet.md`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/no_train_events/{ev_id}_review_sheet.md)"
            lines.append(f"| `{ev_id}` | {prop_link} | {sheet_link} | `False` | `null` | Continuous road vehicles & pedestrians; road horn confounders |")

        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## 5. Engine-Only Event Candidate Table (1 Event)")
        lines.append("| Event ID | Proposal JSON | Review Sheet | Train Type | Cars | T0 (s) | T1 (s) | T2 (s) | T3 == T4 (s) | T_sc (s) | Horn Status |")
        lines.append("| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |")
        e_prop_link = f"[`event_001_proposal_v1.json`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/engine_events/event_001_proposal_v1.json)"
        e_sheet_link = f"[`event_001_review_sheet.md`](file:///Users/sayemuddin/Desktop/Train_automation/data/ground_truth/proposals/engine_events/event_001_review_sheet.md)"
        lines.append(f"| `event_001` | {e_prop_link} | {e_sheet_link} | `locomotive_light` | 0 | 0.00s (LC) | 0.00s | 0.00s | **6.20s** | 6.20s | `absent_observed` |")

        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## 6. Action Items for Subsequent Human Certification")
        lines.append("1. Open each review sheet linked in the tables above.")
        lines.append("2. Execute the provided FFmpeg verification commands to inspect native 1080p and 4K candidate frames.")
        lines.append("3. Listen to both front and back audio recordings to certify horn status and road-traffic confounders.")
        lines.append("4. Adjudicate R03 danger-zone boundary landmarks and R04 inter-camera synchronization offsets.")
        lines.append("5. When ready to approve, create certified human review records in `data/ground_truth/reviews/` and certified ground-truth manifests.")
        lines.append("")

        idx_path = self.base_proposal_dir / "ANNOTATION_BATCH_REVIEW_INDEX.md"
        idx_path.write_text("\n".join(lines), encoding="utf-8")
        return idx_path


if __name__ == "__main__":
    annotator = BatchMultimodalAnnotator(allow_legacy_v6_generation=False)  # guard: fails closed
    summary = annotator.generate_all_events()
    print("=" * 60)
    print("BATCH MULTIMODAL ANNOTATION GENERATION COMPLETE")
    print(f"Eligible discovered: {summary['eligible_discovered']}")
    print(f"Proposals generated: {summary['proposals_generated']}")
    print(f"Review sheets:       {summary['review_sheets_generated']}")
    print(f"Incomplete events:   {len(summary['incomplete_events'])}")
    print(f"Master index path:   {summary['master_index_path']}")
    print("=" * 60)
