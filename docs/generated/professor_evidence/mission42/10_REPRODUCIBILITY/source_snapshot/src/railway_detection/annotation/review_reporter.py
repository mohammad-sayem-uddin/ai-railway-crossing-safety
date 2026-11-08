"""Human-review report generator for AI candidate proposals.

Generates structured Markdown review sheets with inspection commands,
forensic provenance, and decision checklists for human researcher adjudication.
"""

from __future__ import annotations

from pathlib import Path

from railway_detection.annotation.schemas import ProposalDocument


class ReviewReporter:
    """Generates human-review sheets for candidate annotation proposals."""

    @staticmethod
    def generate_review_markdown(
        proposal: ProposalDocument,
        event_raw_dir: Path | str | None = None,
    ) -> str:
        """Format a ProposalDocument into a review-friendly Markdown document."""
        lines: list[str] = []

        lines.append(f"# Ground-Truth Candidate Review Sheet: `{proposal.event_id}`")
        lines.append("")
        lines.append("> [!IMPORTANT]")
        lines.append("> **MANDATORY APPROVAL FIREWALL NOTICE:**")
        lines.append("> This document contains AI-generated candidate proposals. It is **NOT** approved ground truth.")
        lines.append("> Under Ground Truth Protocol v5.0.0, candidate proposals must be manually inspected and certified")
        lines.append("> by the human researcher before being eligible for model evaluation.")
        lines.append("")

        # 1. Metadata & Provenance
        lines.append("## 1. Proposal Provenance & Media Hashes")
        lines.append(f"- **Event ID:** `{proposal.event_id}`")
        lines.append(f"- **Event Type:** `{proposal.event_type}`")
        lines.append(f"- **Proposal ID:** `{proposal.proposal_id}`")
        lines.append(f"- **Generated At (UTC):** `{proposal.proposal_timestamp_utc}`")
        lines.append(f"- **Schema Version:** `{proposal.schema_version}`")
        lines.append(f"- **AI Assistant Model:** `{proposal.ai_assistant_metadata.model_name}`")
        lines.append(f"- **Prompt Template Version:** `{proposal.ai_assistant_metadata.prompt_template_version}`")
        lines.append(f"- **Prompt Template SHA-256:** `{proposal.ai_assistant_metadata.prompt_template_sha256}`")
        lines.append("")

        lines.append("### Input Media Files")
        lines.append("| File Name | Duration (s) | Verified SHA-256 |")
        lines.append("| :--- | :--- | :--- |")
        for mf in proposal.ai_assistant_metadata.input_media_files:
            lines.append(f"| `{mf.file_name}` | {mf.duration_s:.3f}s | `{mf.sha256}` |")
        lines.append("")

        # 2. Train Metadata & Horn
        lines.append("## 2. Train Characteristics & Acoustic Horn")
        tm = proposal.proposed_train_metadata
        lines.append(f"- **Train Present:** `{tm.train_present}`")
        lines.append(f"- **Train Direction:** `{tm.train_direction or 'N/A'}`")
        lines.append(f"- **Train Type:** `{tm.train_type or 'N/A'}`")
        lines.append(f"- **Trailing Cars Count:** `{tm.trailing_cars_count if tm.trailing_cars_count is not None else 'N/A'}`")
        lines.append(f"- **Acoustic Horn Status:** `{tm.horn_status or 'N/A'}`")
        if tm.horn_status == "present":
            lines.append(f"- **Horn Onset:** `{tm.horn_onset_s:.2f}s` (uncertainty: `±{tm.horn_uncertainty_s:.2f}s`)")
        elif tm.horn_reason:
            lines.append(f"- **Horn Reason:** {tm.horn_reason}")
        if tm.confidence_note:
            lines.append(f"- **Acoustic Evidence Note:** {tm.confidence_note}")
        lines.append("")

        # 3. Canonical Timestamps Table
        lines.append("## 3. Proposed Canonical Train-Boundary Timestamps")
        lines.append("| Boundary | Applicable | Observable | Value (s) | Frame | FPS | Camera | Ambiguous | Visual Rationale |")
        lines.append("| :--- | :---: | :---: | :--- | :--- | :--- | :--- | :---: | :--- |")
        for k, v in proposal.proposed_timestamps.items():
            val_str = f"{v.value_s:.2f}s" if v.value_s is not None else "null"
            frame_str = str(v.frame_index) if v.frame_index is not None else "null"
            fps_str = f"{v.native_fps:.2f}" if v.native_fps is not None else "null"
            cam_str = v.reference_camera or "null"
            amb_str = "⚠️ YES" if v.ambiguity_flag else "No"
            lines.append(
                f"| `{k}` | {v.applicable} | {v.candidate_observable} | {val_str} | "
                f"{frame_str} | {fps_str} | {cam_str} | {amb_str} | {v.rationale or ''} |"
            )
        lines.append("")

        # 4. Forensic Verification Commands
        if event_raw_dir:
            ev_dir = Path(event_raw_dir)
            lines.append("## 4. Forensic Verification Commands (FFmpeg)")
            lines.append("Run these terminal commands to view the precise proposed frames:")
            lines.append("```bash")
            for k, v in proposal.proposed_timestamps.items():
                if v.value_s is not None and v.reference_camera:
                    vid_file = f"camera_{v.reference_camera}.mov"
                    vid_path = ev_dir / vid_file
                    ts_str = f"{v.value_s:.3f}s"
                    lines.append(f"# Verify {k} ({ts_str} on {v.reference_camera} camera)")
                    lines.append(
                        f"ffmpeg -ss {v.value_s:.3f} -i {vid_path} -frames:v 1 -q:v 2 preview_{proposal.event_id}_{k}.jpg"
                    )
            lines.append("```")
            lines.append("")

        # 5. Camera Synchronization & Geometry
        lines.append("## 5. Camera Synchronization & Geometry Status")
        ca = proposal.proposed_camera_alignment_markers
        lines.append("> [!NOTE]")
        lines.append("> **Prerequisite R03 Status: RETIRED (Operational Danger-Zone Convention Applied)**")
        lines.append("> **Prerequisite R04 Status: UNRESOLVED (Camera Synchronization Limitation)**")
        lines.append("> - Under Protocol v7.0.0, external site surveys (R03) are retired in favor of documented operational visible landmarks.")
        lines.append("> - Inter-camera offsets (R04) remain uncertified; front and back camera timestamps exist in independent media-local timelines.")
        lines.append(f"- **Candidate Front Marker:** {ca.candidate_front_marker or 'None'}")
        lines.append(f"- **Candidate Back Marker:** {ca.candidate_back_marker or 'None'}")
        lines.append(f"- **Candidate Offset:** {f'{ca.candidate_offset_s:.3f}s' if ca.candidate_offset_s is not None else 'Unmeasured'}")
        lines.append(f"- **Audited Front Stream Exposure:** `{ca.audited_front_stream_exposure_s:.3f}s`")
        lines.append(f"- **Audited Back Stream Exposure:** `{ca.audited_back_stream_exposure_s:.3f}s`")
        lines.append(f"- **Audited Combined Stream Exposure:** `{ca.audited_combined_camera_stream_exposure_s:.3f}s` (stream-seconds; not wall-clock)")
        lines.append("")

        # 6. Human Adjudication Checklist
        lines.append("## 6. Human Adjudication Decision Checklist")
        lines.append("To certify this event for evaluation, the human researcher must:")
        lines.append("1. [ ] Inspect extracted frames against candidate boundaries $T_0$–$T_4$.")
        lines.append("2. [ ] Confirm or adjust horn status and onset timestamp.")
        lines.append("3. [ ] Verify camera alignment markers or declare inter-camera offset unmeasured.")
        lines.append("4. [ ] Record human decisions in `data/ground_truth/reviews/{type}/{event_id}_review.json`.")
        lines.append("5. [ ] If approved, write certified ground truth with `\"approval_status\": \"APPROVED\"` into `data/ground_truth/{type}/{event_id}.json`.")
        lines.append("")

        return "\n".join(lines)

    @classmethod
    def save_review_report(
        cls,
        proposal: ProposalDocument,
        output_file: Path | str,
        event_raw_dir: Path | str | None = None,
    ) -> Path:
        out_p = Path(output_file)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        content = cls.generate_review_markdown(proposal, event_raw_dir)
        out_p.write_text(content, encoding="utf-8")
        return out_p
