"""Exact forward-causal actuator calculations for in-memory synthetic commands.

Profile: SYNTHETIC_CONVENTION_B_V1 (Mission 17C-4 SC01--SC11).
No production controller, media reader, cache, checkpoint or file API is used.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import asdict, dataclass, replace
from decimal import Decimal
from enum import Enum
from fractions import Fraction
from typing import Any

PROFILE = "SYNTHETIC_CONVENTION_B_V1"
SECOND_US = 1_000_000
_DECIMAL = re.compile(r"(?:0|[1-9][0-9]*)(?:\.[0-9]+)?\Z")
_ID = re.compile(r"synthetic:[A-Za-z0-9][A-Za-z0-9._:-]*\Z")


class Command(str, Enum):
    HOLD = "HOLD"
    LOWER = "LOWER"
    RAISE = "RAISE"


def timestamp_us(value: int | str) -> int:
    """Integers are microseconds; decimal strings are seconds; never round."""
    if type(value) is int and value >= 0:
        return value
    if type(value) is str and _DECIMAL.fullmatch(value):
        micros = Fraction(value) * SECOND_US
        if micros.denominator == 1:
            return micros.numerator
    raise ValueError("timestamp must be nonnegative integer us or exact grid decimal seconds")


def legacy_float_to_us(value: float) -> int:
    """Explicit shortest-round-trip-decimal import policy, not float equality.

    0.2 imports as 200000 us. 0.1 + 0.2 rejects rather than rounding noise away.
    Scientific timing precision/accuracy is not established by this adapter.
    """
    if type(value) is not float or not math.isfinite(value) or value < 0:
        raise ValueError("legacy timestamp must be a finite nonnegative float")
    return timestamp_us(format(Decimal(repr(value)), "f"))


def _exact(value: int | str | Fraction) -> Fraction:
    if type(value) is int or isinstance(value, Fraction):
        return Fraction(value)
    if type(value) is str and _DECIMAL.fullmatch(value):
        return Fraction(value)
    raise ValueError("angle/duration must be an exact integer, decimal string or Fraction")


def normalize_command(target: str | Command, nested: str | Command | None = None) -> Command:
    mapping = {
        "H": Command.HOLD, "HOLD": Command.HOLD,
        "L": Command.LOWER, "LOWER": Command.LOWER,
        "CLOSED": Command.LOWER, "CLOSING": Command.LOWER,
        "R": Command.RAISE, "RAISE": Command.RAISE,
        "OPEN": Command.RAISE, "OPENING": Command.RAISE,
    }
    key = target.value if isinstance(target, Command) else target
    if type(key) is not str or key not in mapping:
        raise ValueError("unknown command/target")
    result = mapping[key]
    if nested is not None and normalize_command(nested) != result:
        raise ValueError("nested command conflicts with target")
    return result


@dataclass(frozen=True)
class SyntheticEvent:
    event_id: str
    timestamp: int | str | None
    target: str | Command
    nested_command: str | Command | None = None


@dataclass(frozen=True)
class Watchdog:
    mode: str = "NONE"
    timeout_us: int | None = None
    response: str | Command | None = None

    def __post_init__(self) -> None:
        if self.mode == "NONE":
            if self.timeout_us is not None or self.response is not None:
                raise ValueError("NONE watchdog has no timeout or response")
        elif self.mode in ("SCHEDULED", "DETECT_ON_ARRIVAL"):
            if type(self.timeout_us) is not int or self.timeout_us <= 0:
                raise ValueError("watchdog timeout must be a positive integer us")
            normalize_command(self.response)
        else:
            raise ValueError("unknown synthetic watchdog profile")


def _canonical(value: Any) -> str:
    def encode(item: Any) -> Any:
        if isinstance(item, Fraction):
            return {"numerator": item.numerator, "denominator": item.denominator}
        if isinstance(item, Enum):
            return item.value
        if isinstance(item, dict):
            return {k: encode(v) for k, v in item.items()}
        if isinstance(item, (list, tuple)):
            return [encode(v) for v in item]
        return item
    return json.dumps(encode(value), sort_keys=True, separators=(",", ":"), allow_nan=False)


@dataclass(frozen=True)
class RunConfiguration:
    """Exact configuration snapshot consumed by a run, including reporting choices."""

    initial_angle: Fraction
    closing_seconds: Fraction
    opening_seconds: Fraction
    watchdog: Watchdog
    mode: str
    cutoff_us: int | None
    report_times_us: tuple[int, ...] | None
    profile: str = PROFILE
    schema_version: str = "SYNTHETIC_RUN_CONFIGURATION_V1"
    timestamp_policy: str = "INTEGER_US_OR_EXACT_GRID_DECIMAL_SECONDS_V1"
    dynamics: str = "CLIPPED_LINEAR_0_90_STRICT_BLOCKED_LE_45_V1"
    command_latency_us: int = 0
    watchdog_priority: str = "SENSOR_FIRST_ONE_SHOT_V1"

    def __post_init__(self) -> None:
        if (any(type(v) is not Fraction for v in
                (self.initial_angle, self.closing_seconds, self.opening_seconds))
                or not 0 <= self.initial_angle <= 90
                or self.closing_seconds <= 0 or self.opening_seconds <= 0):
            raise ValueError("complete exact actuator configuration required")
        if type(self.watchdog) is not Watchdog or type(self.watchdog.mode) is not str:
            raise ValueError("explicit watchdog configuration required")
        self.watchdog.__post_init__()
        if self.watchdog.response is not None and type(self.watchdog.response) is not Command:
            raise ValueError("watchdog response configuration must be normalized")
        if type(self.mode) is not str or self.mode not in ("ARRIVAL", "OFFLINE"):
            raise ValueError("explicit run mode required")
        if self.cutoff_us is not None:
            timestamp_us(self.cutoff_us)
            if type(self.cutoff_us) is not int:
                raise ValueError("configuration cutoff must be integer us")
        if self.report_times_us is not None:
            if (type(self.report_times_us) is not tuple or not self.report_times_us
                    or any(type(t) is not int or t < 0 for t in self.report_times_us)
                    or any(b <= a for a, b in zip(self.report_times_us, self.report_times_us[1:]))):
                raise ValueError("configuration report grid must be increasing integer us")
        for actual, expected in (
            (self.profile, PROFILE), (self.schema_version, "SYNTHETIC_RUN_CONFIGURATION_V1"),
            (self.timestamp_policy, "INTEGER_US_OR_EXACT_GRID_DECIMAL_SECONDS_V1"),
            (self.dynamics, "CLIPPED_LINEAR_0_90_STRICT_BLOCKED_LE_45_V1"),
            (self.watchdog_priority, "SENSOR_FIRST_ONE_SHOT_V1"),
        ):
            if type(actual) is not str or actual != expected:
                raise ValueError("unsupported configuration contract")
        if type(self.command_latency_us) is not int or self.command_latency_us != 0:
            raise ValueError("only existing zero-latency synthetic command contract supported")

    def canonical_json(self) -> str:
        self.__post_init__()
        return _canonical(asdict(self))

    @property
    def digest(self) -> str:
        return hashlib.sha256(self.canonical_json().encode()).hexdigest()


@dataclass(frozen=True)
class Interval:
    start_us: int
    end_us: int
    applied_command: Command
    effective_us: int
    origin_event_id: str
    pre_angle: Fraction
    post_angle: Fraction
    blocked: bool
    continuous_seconds: Fraction
    end_kind: str


@dataclass(frozen=True)
class CommandIssue:
    timestamp_us: int
    event_id: str
    command: Command
    requested_command: Command
    kind: str
    mapping_provenance: str


@dataclass(frozen=True)
class Rejection:
    input_index: int
    event_id: str
    timestamp_us: int
    reason: str


@dataclass(frozen=True)
class RunResult:
    profile: str
    fixture_id: str
    status: str
    reason: str | None
    mode: str
    reordered: bool
    origin_us: int | None
    horizon_us: int | None
    initial_angle: Fraction | None
    final_angle: Fraction | None
    intervals: tuple[Interval, ...]
    issues: tuple[CommandIssue, ...]
    rejections: tuple[Rejection, ...]
    accepted_event_ids: tuple[str, ...]
    event_grid_us: tuple[int, ...]
    report_grid_us: tuple[int, ...]
    report_grid_kind: str
    endpoint_seconds: Fraction
    continuous_seconds: Fraction
    report_endpoint_seconds: Fraction | None
    configuration: RunConfiguration
    configuration_digest: str

    def canonical_json(self) -> str:
        """Deterministic synthetic output string; no file is written."""
        verify_run_configuration(self, expected_configuration=self.configuration)
        return _canonical(asdict(self))


def verify_run_configuration(result: RunResult, *,
                             expected_configuration: RunConfiguration | None = None) -> None:
    """Check recorded settings against separately retained expected settings.

    This binds configuration, not source-code authenticity or a full trajectory proof.
    """
    if type(result) is not RunResult or type(expected_configuration) is not RunConfiguration:
        raise ValueError("result and independent expected configuration required")
    expected_configuration.__post_init__()
    if type(result.configuration) is not RunConfiguration:
        raise ValueError("missing run configuration")
    result.configuration.__post_init__()
    if (type(result.configuration_digest) is not str
            or result.configuration_digest != result.configuration.digest
            or result.configuration != expected_configuration):
        raise ValueError("run configuration binding mismatch")
    config = result.configuration
    if result.profile != config.profile or result.mode != config.mode:
        raise ValueError("result contradicts configured profile/mode")
    if result.origin_us is not None and (
            type(result.initial_angle) is not Fraction or result.initial_angle != config.initial_angle):
        raise ValueError("result contradicts configured initial angle")
    expected_grid_kind = "EVENT_GRID" if config.report_times_us is None else "FIXED_GRID"
    expected_grid = result.event_grid_us if config.report_times_us is None else config.report_times_us
    if result.report_grid_kind != expected_grid_kind or result.report_grid_us != expected_grid:
        raise ValueError("result contradicts configured report grid")


def _motion(q: Fraction, command: Command, seconds: Fraction,
            down: Fraction, up: Fraction) -> tuple[Fraction, Fraction]:
    if command == Command.LOWER:
        post = max(Fraction(0), q - down * seconds)
        blocked = seconds if q <= 45 else max(Fraction(0), seconds - (q - 45) / down)
    elif command == Command.RAISE:
        post = min(Fraction(90), q + up * seconds)
        blocked = Fraction(0) if q > 45 else min(seconds, max(Fraction(0), (45 - q) / up))
    else:
        post = q
        blocked = seconds if q <= 45 else Fraction(0)
    return post, blocked


def _report_endpoint_seconds(intervals: list[Interval], report: tuple[int, ...],
                             down: Fraction, up: Fraction) -> Fraction:
    """Merge two ordered grids; each interval/report boundary is visited O(1) times."""
    index = 0
    total = Fraction(0)
    for start, end in zip(report, report[1:]):
        while index < len(intervals) and intervals[index].end_us < end:
            index += 1
        if index == len(intervals):
            raise ValueError("report endpoint outside trajectory")
        interval = intervals[index]
        if not interval.start_us <= end <= interval.end_us:
            raise ValueError("report endpoint outside trajectory")
        angle = _motion(interval.pre_angle, interval.applied_command,
                        Fraction(end-interval.start_us, SECOND_US), down, up)[0]
        total += (end-start) * Fraction(int(angle <= 45), SECOND_US)
    return total


class CausalRunner:
    """Commanded actuator helper; does not execute a research controller."""

    def __init__(self, *, initial_angle: int | str | Fraction = 90,
                 closing_seconds: int | str | Fraction = 3,
                 opening_seconds: int | str | Fraction = 3,
                 watchdog: Watchdog | None = None) -> None:
        closing, opening = _exact(closing_seconds), _exact(opening_seconds)
        if watchdog is not None and type(watchdog) is not Watchdog:
            raise ValueError("watchdog must be an explicit synthetic Watchdog")
        wd = watchdog or Watchdog()
        normalized = Watchdog(wd.mode, wd.timeout_us,
                              None if wd.response is None else normalize_command(wd.response))
        self._configuration = RunConfiguration(_exact(initial_angle), closing, opening,
                                               normalized, "ARRIVAL", None, None)

    @property
    def initial_angle(self) -> Fraction:
        return self._configuration.initial_angle

    @property
    def down(self) -> Fraction:
        return 90 / self._configuration.closing_seconds

    @property
    def up(self) -> Fraction:
        return 90 / self._configuration.opening_seconds

    @property
    def watchdog(self) -> Watchdog:
        return self._configuration.watchdog

    def run(self, events: list[SyntheticEvent] | tuple[SyntheticEvent, ...], *,
            fixture_id: str, mode: str = "ARRIVAL", cutoff: int | str | None = None,
            report_times: tuple[int | str, ...] | None = None) -> RunResult:
        if type(fixture_id) is not str or not _ID.fullmatch(fixture_id):
            raise ValueError("explicit synthetic fixture identity required")
        if type(events) not in (list, tuple) or mode not in ("ARRIVAL", "OFFLINE"):
            raise ValueError("events must be an in-memory list/tuple and mode explicit")
        cutoff_us = None if cutoff is None else timestamp_us(cutoff)
        fixed = None if report_times is None else tuple(timestamp_us(t) for t in report_times)
        if fixed is not None and (not fixed or any(b <= a for a, b in zip(fixed, fixed[1:]))):
            raise ValueError("report grid must be nonempty and strictly increasing")
        config = replace(self._configuration, mode=mode, cutoff_us=cutoff_us,
                         report_times_us=fixed)
        down, up = 90 / config.closing_seconds, 90 / config.opening_seconds
        intervals: list[Interval] = []
        issues: list[CommandIssue] = []
        rejects: list[Rejection] = []
        accepted: list[str] = []
        seen_ids: set[str] = set()
        q = config.initial_angle
        origin: int | None = None
        now: int | None = None
        last_sensor: int | None = None
        active = Command.HOLD
        effective = 0
        origin_id = "synthetic:initial"
        generation = 0
        timer_fired = False
        reordered = False

        def finish(status: str, reason: str | None = None) -> RunResult:
            grid = (() if origin is None else (origin,)) + tuple(i.end_us for i in intervals)
            endpoint = sum(((i.end_us-i.start_us) * Fraction(int(i.blocked), SECOND_US)
                            for i in intervals), Fraction(0))
            continuous = sum((i.continuous_seconds for i in intervals), Fraction(0))
            report = grid if fixed is None else fixed
            report_value: Fraction | None = None
            if status in ("COMPLETE", "EMPTY"):
                if origin is None:
                    if fixed is not None:
                        raise ValueError("empty run cannot span a fixed report grid")
                    report_value = Fraction(0)
                else:
                    if not report or report[0] != origin or report[-1] != now:
                        raise ValueError("report grid must span exact accepted origin/horizon")
                    report_value = (endpoint if fixed is None else
                                    _report_endpoint_seconds(intervals, report, down, up))
            return RunResult(PROFILE, fixture_id, status, reason, mode, reordered, origin, now,
                             config.initial_angle if origin is not None else None,
                             q if origin is not None else None, tuple(intervals), tuple(issues),
                             tuple(rejects), tuple(accepted), grid, report,
                             "EVENT_GRID" if fixed is None else "FIXED_GRID", endpoint,
                             continuous, report_value, config, config.digest)

        def append_until(t: int, kind: str) -> None:
            nonlocal q, now
            assert now is not None
            if t > now:
                post, blocked_time = _motion(q, active, Fraction(t-now, SECOND_US),
                                             down, up)
                intervals.append(Interval(now, t, active, effective, origin_id, q, post,
                                          post <= 45, blocked_time, kind))
                q, now = post, t

        def issue(t: int, event_id: str, command: Command, requested: Command,
                  kind: str, provenance: str) -> None:
            nonlocal active, effective, origin_id
            active, effective, origin_id = command, t, event_id
            issues.append(CommandIssue(t, event_id, command, requested, kind, provenance))

        def advance(t: int, kind: str) -> None:
            nonlocal timer_fired
            wd = config.watchdog
            if wd.mode == "SCHEDULED" and last_sensor is not None and not timer_fired:
                assert wd.timeout_us is not None
                due = last_sensor + wd.timeout_us
                # Valid sensor at equality wins; cutoff has no sensor to cancel it.
                if due < t or (due == t and kind == "CUTOFF"):
                    append_until(due, "TIMER")
                    response = normalize_command(wd.response)
                    issue(due, f"synthetic:timer:{generation}", response, response,
                          "TIMER", "EXPLICIT_SYNTHETIC_WATCHDOG")
                    timer_fired = True
            append_until(t, kind)

        indexed = list(enumerate(events))
        if mode == "OFFLINE":
            try:
                for _, e in indexed:
                    if type(e) is not SyntheticEvent:
                        raise ValueError("explicit synthetic event required")
                    timestamp_us(e.timestamp)
                    if type(e.event_id) is not str or not _ID.fullmatch(e.event_id):
                        raise ValueError("synthetic event identity required")
                    normalize_command(e.target, e.nested_command)
                indexed.sort(key=lambda pair: (timestamp_us(pair[1].timestamp), pair[0]))
                reordered = [i for i, _ in indexed] != list(range(len(events)))
            except ValueError as exc:
                return finish("INCOMPLETE", str(exc))

        for index, e in indexed:
            try:
                if type(e) is not SyntheticEvent:
                    raise ValueError("explicit synthetic event required")
                t = timestamp_us(e.timestamp)
                if origin is not None and cutoff_us is not None and t > cutoff_us:
                    advance(cutoff_us, "CUTOFF")
                    return finish("COMPLETE")
                if type(e.event_id) is not str or not _ID.fullmatch(e.event_id):
                    raise ValueError("synthetic event identity required")
                if last_sensor is not None and t <= last_sensor:
                    rejects.append(Rejection(index, e.event_id, t,
                                             "DUPLICATE" if t == last_sensor else "OUT_OF_ORDER"))
                    continue
                if e.event_id in seen_ids:
                    raise ValueError("accepted event identity reused at a different instant")
                requested = normalize_command(e.target, e.nested_command)
            except ValueError as exc:
                return finish("INCOMPLETE", str(exc))
            if origin is None:
                if cutoff_us is not None and cutoff_us < t:
                    raise ValueError("cutoff precedes origin")
                origin = now = t
            else:
                advance(t, "SENSOR")
            command, kind = requested, "SENSOR"
            wd = config.watchdog
            if wd.mode == "DETECT_ON_ARRIVAL" and last_sensor is not None:
                assert wd.timeout_us is not None
                if t - last_sensor > wd.timeout_us:
                    command, kind = normalize_command(wd.response), "GAP_DETECTED"
            issue(t, e.event_id, command, requested, kind,
                  "DERIVED_FROM_TARGET" if e.nested_command is None else "REPORTED_INTENT")
            accepted.append(e.event_id)
            seen_ids.add(e.event_id)
            last_sensor, generation, timer_fired = t, generation + 1, False
            if cutoff_us is not None and t == cutoff_us:
                return finish("COMPLETE")
        if origin is None:
            return finish("EMPTY")
        if cutoff_us is not None and now is not None and cutoff_us > now:
            advance(cutoff_us, "CUTOFF")
        return finish("COMPLETE")
