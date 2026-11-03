"""Formal railway crossing state machine with safety transition invariants and audit logging."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from railway_detection.fusion.rules import CrossingState
from railway_detection.utils.logging import get_logger

logger = get_logger("simulation.state_machine")


class InvalidTransitionError(ValueError):
    """Raised when an illegal state transition is attempted according to safety invariants."""


@dataclass(frozen=True)
class TransitionEvent:
    """Immutable audit record of a crossing state transition."""

    from_state: CrossingState
    to_state: CrossingState
    timestamp_s: float
    reason: str
    guard_satisfied: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


# Strictly enforced transition matrix based on EXPERIMENT_PROTOCOL_V2.md §9
ALLOWED_TRANSITIONS: dict[CrossingState, set[CrossingState]] = {
    CrossingState.IDLE: {
        CrossingState.IDLE,
        CrossingState.TRAIN_APPROACHING,
        CrossingState.WARNING,
        CrossingState.FAULT_FAIL_SAFE,
    },
    CrossingState.TRAIN_APPROACHING: {
        CrossingState.TRAIN_APPROACHING,
        CrossingState.WARNING,
        CrossingState.IDLE,
        CrossingState.FAULT_FAIL_SAFE,
    },
    CrossingState.WARNING: {
        CrossingState.WARNING,
        CrossingState.GATE_CLOSING,
        CrossingState.FAULT_FAIL_SAFE,
    },
    CrossingState.GATE_CLOSING: {
        CrossingState.GATE_CLOSING,
        CrossingState.TRAIN_PRESENT,
        CrossingState.FAULT_FAIL_SAFE,
    },
    CrossingState.TRAIN_PRESENT: {
        CrossingState.TRAIN_PRESENT,
        CrossingState.CROSSING_OCCUPIED,
        CrossingState.FAULT_FAIL_SAFE,
    },
    CrossingState.CROSSING_OCCUPIED: {
        CrossingState.CROSSING_OCCUPIED,
        CrossingState.TRAIN_DEPARTING,
        CrossingState.FAULT_FAIL_SAFE,
    },
    CrossingState.TRAIN_DEPARTING: {
        CrossingState.TRAIN_DEPARTING,
        CrossingState.REAR_CONFIRMED,
        CrossingState.FAULT_FAIL_SAFE,
    },
    CrossingState.REAR_CONFIRMED: {
        CrossingState.REAR_CONFIRMED,
        CrossingState.CROSSING_CLEAR,
        CrossingState.TRAIN_PRESENT,
        CrossingState.WARNING,
        CrossingState.GATE_CLOSING,
        CrossingState.FAULT_FAIL_SAFE,
    },
    CrossingState.CROSSING_CLEAR: {
        CrossingState.CROSSING_CLEAR,
        CrossingState.GATE_OPENING,
        CrossingState.GATE_CLOSING,
        CrossingState.WARNING,
        CrossingState.FAULT_FAIL_SAFE,
    },
    CrossingState.GATE_OPENING: {
        CrossingState.GATE_OPENING,
        CrossingState.IDLE,
        CrossingState.GATE_CLOSING,
        CrossingState.WARNING,
        CrossingState.FAULT_FAIL_SAFE,
    },
    CrossingState.FAULT_FAIL_SAFE: {
        CrossingState.FAULT_FAIL_SAFE,
        CrossingState.IDLE,
        CrossingState.TRAIN_PRESENT,
    },
}


class CrossingStateMachine:
    """Formal safety state machine tracking crossing states and transitions with audit logging."""

    def __init__(self, initial_state: CrossingState = CrossingState.IDLE, initial_time_s: float = 0.0) -> None:
        self.current_state = initial_state
        self.state_entry_time_s = float(initial_time_s)
        self.history: list[TransitionEvent] = []

    def can_transition(self, to_state: CrossingState) -> bool:
        """Check whether a transition to `to_state` is legally permissible from current state."""
        allowed = ALLOWED_TRANSITIONS.get(self.current_state, set())
        return to_state in allowed

    def time_in_current_state(self, current_time_s: float) -> float:
        """Return duration in seconds spent in current state."""
        return max(0.0, float(current_time_s) - self.state_entry_time_s)

    def transition(
        self,
        to_state: CrossingState,
        timestamp_s: float,
        reason: str = "",
        metadata: dict[str, Any] | None = None,
        force_fault: bool = False,
    ) -> TransitionEvent:
        """Execute a state transition with invariant validation."""
        timestamp = float(timestamp_s)
        meta = metadata if metadata is not None else {}

        if to_state == self.current_state:
            # Self-transition / dwell
            return TransitionEvent(
                from_state=self.current_state,
                to_state=self.current_state,
                timestamp_s=timestamp,
                reason=reason or "dwell",
                guard_satisfied=True,
                metadata=meta,
            )

        if not force_fault and not self.can_transition(to_state):
            msg = (
                f"Illegal state transition from {self.current_state.value} to {to_state.value}. "
                f"Forbidden by safety invariants."
            )
            logger.error(msg)
            raise InvalidTransitionError(msg)

        event = TransitionEvent(
            from_state=self.current_state,
            to_state=to_state,
            timestamp_s=timestamp,
            reason=reason,
            guard_satisfied=True,
            metadata=meta,
        )
        self.history.append(event)
        self.current_state = to_state
        self.state_entry_time_s = timestamp
        return event

    def reset(self, initial_state: CrossingState = CrossingState.IDLE, initial_time_s: float = 0.0) -> None:
        """Reset state machine to initial configuration."""
        self.current_state = initial_state
        self.state_entry_time_s = float(initial_time_s)
        self.history.clear()
