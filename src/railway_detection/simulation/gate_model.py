"""Physical railway barrier gate kinematics and actuation modeling."""

from __future__ import annotations

from railway_detection.fusion.rules import GateState
from railway_detection.utils.logging import get_logger

logger = get_logger("simulation.gate_model")


class PhysicalGateModel:
    """Simulates physical gate boom kinematics and angular position over time.

    Angles:
        90.0°: Fully raised (OPEN, vehicular traffic permitted)
        0.0°: Fully lowered (CLOSED, vehicular traffic blocked)
    """

    def __init__(
        self,
        closing_duration_s: float = 3.0,
        opening_duration_s: float = 3.0,
        initial_angle_deg: float = 90.0,
    ) -> None:
        self.closing_duration_s = max(0.1, float(closing_duration_s))
        self.opening_duration_s = max(0.1, float(opening_duration_s))
        self.current_angle_deg = float(initial_angle_deg)
        self.current_state = (
            GateState.OPEN if self.current_angle_deg >= 89.9 else GateState.CLOSED
        )

    @property
    def is_passage_blocked(self) -> bool:
        """True if the barrier arm is lowered enough (<= 45°) to obstruct road vehicles."""
        return self.current_angle_deg <= 45.0

    @property
    def is_fully_closed(self) -> bool:
        """True if barrier arm is completely horizontal."""
        return self.current_angle_deg <= 0.05

    @property
    def is_fully_open(self) -> bool:
        """True if barrier arm is completely vertical."""
        return self.current_angle_deg >= 89.95

    def step(self, dt_s: float, commanded_state: GateState) -> float:
        """Advance gate arm position by dt_s given actuator command.

        Returns:
            Updated arm angle in degrees in [0.0, 90.0].
        """
        dt = max(0.0, float(dt_s))

        if commanded_state in (GateState.CLOSING, GateState.CLOSED):
            closing_rate = 90.0 / self.closing_duration_s
            self.current_angle_deg = max(0.0, self.current_angle_deg - closing_rate * dt)
            if self.is_fully_closed:
                self.current_state = GateState.CLOSED
            else:
                self.current_state = GateState.CLOSING

        elif commanded_state in (GateState.OPENING, GateState.OPEN):
            opening_rate = 90.0 / self.opening_duration_s
            self.current_angle_deg = min(90.0, self.current_angle_deg + opening_rate * dt)
            if self.is_fully_open:
                self.current_state = GateState.OPEN
            else:
                self.current_state = GateState.OPENING

        return self.current_angle_deg

    def reset(self, angle_deg: float = 90.0) -> None:
        """Reset gate boom position."""
        self.current_angle_deg = float(angle_deg)
        self.current_state = (
            GateState.OPEN if self.current_angle_deg >= 89.9 else GateState.CLOSED
        )
