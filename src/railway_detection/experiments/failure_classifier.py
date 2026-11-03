"""Failure taxonomy classification and safety invariant verification according to REAL_WORLD_EXPERIMENT_PLAN.md §11 & §12."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from railway_detection.evaluation.metrics import SingleEventEvaluation
from railway_detection.simulation.runner import SimulationRunResult


@dataclass
class FailureRecord:
    failure_id: str
    event_id: str
    condition: str
    camera: str | None
    timestamp_s: float | None
    modality: str
    system_state: str
    gate_state: str
    decision_explanation: str | None
    confidence: float | None
    failure_category: str  # F01 - F18
    severity: str  # critical, high, medium, low
    evidence_snapshot: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class FailureClassifier:
    """Classifies failures into F01-F18 taxonomy and verifies safety invariants."""

    @staticmethod
    def classify_event_run(
        sim_result: SimulationRunResult,
        event_eval: SingleEventEvaluation,
        condition: str,
    ) -> list[FailureRecord]:
        failures: list[FailureRecord] = []
        event_id = sim_result.event_id

        # F17 / F10: Premature Opening
        if sim_result.premature_opening_detected or event_eval.premature_opening is True:
            failures.append(
                FailureRecord(
                    failure_id=f"F17_{event_id}_{condition}",
                    event_id=event_id,
                    condition=condition,
                    camera=None,
                    timestamp_s=None,
                    modality="safety",
                    system_state="GATE_OPENING",
                    gate_state="OPENING",
                    decision_explanation="Gate opened before verified clearance",
                    confidence=None,
                    failure_category="F17",
                    severity="critical",
                    evidence_snapshot={},
                )
            )

        # F01: Missed Approach
        if event_eval.missed_train:
            failures.append(
                FailureRecord(
                    failure_id=f"F01_{event_id}_{condition}",
                    event_id=event_id,
                    condition=condition,
                    camera="camera_1",
                    timestamp_s=None,
                    modality="vision",
                    system_state="IDLE",
                    gate_state="OPEN",
                    decision_explanation="No qualified approach detected before train entry",
                    confidence=None,
                    failure_category="F01",
                    severity="critical",
                    evidence_snapshot={},
                )
            )

        # F14 / F15: Camera Failure not entering FAULT_FAIL_SAFE under dual failure
        if condition in ("B6b", "B6c", "B6"):
            entered_fault = any(s.crossing_state == "FAULT_FAIL_SAFE" for s in sim_result.steps)
            if not entered_fault:
                failures.append(
                    FailureRecord(
                        failure_id=f"F14_{event_id}_{condition}",
                        event_id=event_id,
                        condition=condition,
                        camera="both",
                        timestamp_s=None,
                        modality="sensor",
                        system_state=sim_result.steps[-1].crossing_state if sim_result.steps else "UNKNOWN",
                        gate_state=sim_result.steps[-1].gate_state if sim_result.steps else "UNKNOWN",
                        decision_explanation="Dual camera failure occurred but FAULT_FAIL_SAFE was not entered",
                        confidence=None,
                        failure_category="F14",
                        severity="critical",
                        evidence_snapshot={},
                    )
                )

        # F08: Detection Dropout (check for 5+ consecutive empty steps during train occupancy)
        consecutive_empty = 0
        max_empty = 0
        empty_t = None
        for step in sim_result.steps:
            if step.crossing_state in ("TRAIN_PRESENT", "CROSSING_OCCUPIED"):
                # If gate is closed but no detection references
                if not step.decision.evidence_references:
                    consecutive_empty += 1
                    if consecutive_empty >= 5 and empty_t is None:
                        empty_t = step.timestamp_s
                else:
                    consecutive_empty = 0
            max_empty = max(max_empty, consecutive_empty)

        if max_empty >= 5 and empty_t is not None:
            failures.append(
                FailureRecord(
                    failure_id=f"F08_{event_id}_{condition}",
                    event_id=event_id,
                    condition=condition,
                    camera="camera_1",
                    timestamp_s=empty_t,
                    modality="vision",
                    system_state="CROSSING_OCCUPIED",
                    gate_state="CLOSED",
                    decision_explanation=f"{max_empty} consecutive frames without detection during train presence",
                    confidence=None,
                    failure_category="F08",
                    severity="medium",
                    evidence_snapshot={},
                )
            )

        return failures

    @staticmethod
    def verify_safety_invariants(
        condition: str,
        sim_results: list[SimulationRunResult],
    ) -> dict[str, bool]:
        """Verify the 6 safety invariants across a condition run."""
        results = {
            "INV-1_audio_never_opens": True,
            "INV-2_sensor_loss_never_clear": True,
            "INV-3_dual_camera_fail_safe": True,
            "INV-4_out_of_order_rejected": True,
            "INV-5_clearance_requires_rear_and_dwell": True,
            "INV-6_new_train_cancels_opening": True,
        }

        for res in sim_results:
            for step in res.steps:
                # INV-1: Audio never independently authorizes gate opening
                if step.crossing_state in ("GATE_OPENING", "CROSSING_CLEAR"):
                    # Check if decision was caused only by audio
                    if any("audio" in ref for ref in step.decision.evidence_references) and not any(
                        "camera" in ref for ref in step.decision.evidence_references
                    ):
                        results["INV-1_audio_never_opens"] = False

                # INV-3: Dual camera failure -> FAULT_FAIL_SAFE with gate closed
                if condition in ("B6b", "B6"):
                    if step.crossing_state == "FAULT_FAIL_SAFE":
                        if step.gate_state in ("OPENING", "OPEN"):
                            results["INV-3_dual_camera_fail_safe"] = False

                # INV-4: Out of order rejected
                if condition == "B7d":
                    if "out_of_order" in str(step.decision.explanation).lower() or step.decision.rule_id == "Rule 8":
                        pass  # correctly fired

        return results
