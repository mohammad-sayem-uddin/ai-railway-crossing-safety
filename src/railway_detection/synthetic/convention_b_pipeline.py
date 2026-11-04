"""Constructed-only controller/Convention B integration; no loaders or writers.

The fixture envelope is a caller assertion, not authentication. Cooperative
non-hostile callers retain the request/code identity independently of a result.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import asdict, dataclass, replace

from railway_detection.fusion.collector import MultimodalFrame
from railway_detection.fusion.decision_engine import MultimodalDecisionEngine
from railway_detection.fusion.evidence import DecisionRecord, Detection, EvidenceRecord, Modality
from railway_detection.fusion.rules import RuleId
from railway_detection.synthetic.convention_b import (
    CausalRunner,
    RunResult,
    SyntheticEvent,
    normalize_command,
    timestamp_us,
)

SCHEMA = "CONSTRUCTED_CONVENTION_B_PIPELINE_V1"
_ID = re.compile(r"synthetic:[A-Za-z0-9][A-Za-z0-9._:-]*\Z")
SETTINGS = (
    "warning_dwell_s",
    "gate_closing_s",
    "gate_opening_s",
    "clearance_dwell_s",
    "approach_threshold",
    "departure_threshold",
    "audio_threshold",
    "confirm_frames",
    "source_staleness_s",
    "fault_confirm_frames",
    "fault_recovery_hold_s",
)
REJECT = (
    RuleId.RULE_8_OUT_OF_ORDER_REJECTION.value,
    RuleId.RULE_10_DUPLICATE_FRAME_REJECTION.value,
)


def canonical(value):
    """Canonical JSON owns copies of nested caller dictionaries; NaN rejects."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _identity(value):
    if type(value) is not str or not _ID.fullmatch(value):
        raise ValueError("constructed synthetic identity required")


@dataclass(frozen=True)
class ConstructedInput:
    event_id: str
    timestamp: int | str | None
    frame: MultimodalFrame


@dataclass(frozen=True)
class ConstructedBatch:
    fixture_id: str
    inputs_json: str
    provenance: str

    @classmethod
    def build(cls, fixture_id: str, inputs: tuple[ConstructedInput, ...], *, provenance: str):
        _identity(fixture_id)
        if type(inputs) is not tuple or len(inputs) > 8192:
            raise ValueError("constructed tuple with at most8192 supplied frames required")
        if provenance != "CONSTRUCTED_IN_MEMORY":
            raise ValueError("explicit in-memory construction declaration required")
        rows = []
        for x in inputs:
            if type(x) is not ConstructedInput or type(x.frame) is not MultimodalFrame:
                raise ValueError("typed constructed input/frame required")
            rows.append(
                {"event_id": x.event_id, "timestamp": x.timestamp, "frame": asdict(x.frame)}
            )
        return cls(fixture_id, canonical(rows), provenance)


@dataclass(frozen=True)
class ScriptedDecisions:
    """Explicit constructed command/error injection fixture, never a live callback."""

    commands: tuple[str, ...]


@dataclass(frozen=True)
class IntegrationRequest:
    batch: ConstructedBatch
    mode: str
    controller_json: str
    code_identity: str
    initial_angle: str = "90"
    closing_seconds: str = "3"
    opening_seconds: str = "3"
    cutoff: int | str | None = None
    report_times: tuple[int | str, ...] | None = None
    report_step_us: int | None = None
    schema: str = SCHEMA

    @classmethod
    def prepare(cls, batch, controller, *, mode, code_identity, **kwargs):
        return cls(batch, mode, _settings(controller), code_identity, **kwargs)

    def canonical_json(self):
        return canonical(asdict(self))


@dataclass(frozen=True)
class DecisionLink:
    input_index: int
    timestamp_us: int
    event_id: str
    decision_json: str
    accepted: bool
    logical_target: str
    command: str | None


@dataclass(frozen=True)
class IntegrationResult:
    request_json: str
    request_digest: str
    code_identity: str
    status: str
    reason: str | None
    causal: RunResult
    decisions: tuple[DecisionLink, ...]
    controller_calls: int
    processing_mode: str
    reordered: bool
    schema: str = SCHEMA

    def canonical_json(self):
        data = asdict(self)
        data["causal"] = json.loads(self.causal.canonical_json())
        return canonical(data)


def _settings(controller):
    if type(controller) is ScriptedDecisions:
        if type(controller.commands) is not tuple:
            raise ValueError("script must be an immutable tuple")
        return canonical({"kind": "SCRIPTED", "commands": controller.commands})
    if type(controller) is not MultimodalDecisionEngine:
        raise ValueError("current exact controller or explicit scripted fixture required")
    values = {k: getattr(controller, k) for k in SETTINGS}
    for k, value in values.items():
        if k in ("confirm_frames", "fault_confirm_frames"):
            if type(value) is not int or value < 1:
                raise ValueError("positive exact controller count required")
        elif type(value) not in (int, float) or not math.isfinite(value) or value < 0:
            raise ValueError("finite nonnegative effective controller setting required")
        if "threshold" in k and value > 1:
            raise ValueError("controller threshold outside[0,1]")
    return canonical({"kind": "CURRENT_ENGINE", "settings": values})


def _fresh(settings):
    data = json.loads(settings)
    if data.get("kind") not in ("SCRIPTED", "CURRENT_ENGINE"):
        raise ValueError("unsupported controller kind")
    if data["kind"] == "SCRIPTED":
        return ScriptedDecisions(tuple(data["commands"]))
    c = MultimodalDecisionEngine()
    if set(data["settings"]) != set(SETTINGS):
        raise ValueError("complete effective controller settings required")
    for k, v in data["settings"].items():
        setattr(c, k, v)
    if _settings(c) != settings:
        raise ValueError("noncanonical controller settings")
    return c


def _frame(row):
    frame = dict(row["frame"])
    for name in ("vision_records", "audio_records"):
        values = []
        for raw in frame[name]:
            raw = dict(raw)
            raw["modality"] = Modality(raw["modality"])
            detections = []
            for d in raw["detections"]:
                d = dict(d)
                if d["bbox_xyxy"] is not None:
                    d["bbox_xyxy"] = tuple(d["bbox_xyxy"])
                detections.append(Detection(**d))
            raw["detections"] = tuple(detections)
            values.append(EvidenceRecord(**raw))
        frame[name] = tuple(values)
    return MultimodalFrame(**frame)


def _decision_json(decision):
    data = asdict(decision)
    # The native controller uses +infinity for unavailable sensor ages.
    # Preserve that explicit sentinel without emitting invalid JSON numbers.
    for key, value in data["observation_ages"].items():
        if type(value) is float and math.isinf(value):
            data["observation_ages"][key] = {"nonfinite_age": str(value)}
    return canonical(data)


def _validate_row(row):
    t = timestamp_us(row["timestamp"])
    if t > 3_600_000_000:
        raise ValueError("unsupported clock beyond one-hour envelope")
    _identity(row["event_id"])
    f = _frame(row)
    if type(f.master_timestamp_s) is not float or f.master_timestamp_s != t / 1_000_000:
        raise ValueError("exact/frame clock disagreement")
    for e in (*f.vision_records, *f.audio_records):
        if (
            type(e.timestamp_s) is not float
            or not math.isfinite(e.timestamp_s)
            or e.timestamp_s > f.master_timestamp_s
        ):
            raise ValueError("evidence time must be finite and not in the future; never retime")
    return t, f


def run_pipeline(request: IntegrationRequest, controller=None) -> IntegrationResult:
    """Evaluate each supplied eligible frame once; delegate all motion to CausalRunner."""
    if type(request) is not IntegrationRequest or type(request.batch) is not ConstructedBatch:
        raise ValueError("explicit constructed integration request required")
    b = request.batch
    _identity(b.fixture_id)
    _identity(request.code_identity)
    if b.provenance != "CONSTRUCTED_IN_MEMORY" or request.schema != SCHEMA:
        raise ValueError("unsupported constructed envelope")
    if request.mode not in ("ARRIVAL", "OFFLINE"):
        raise ValueError("explicit ARRIVAL or OFFLINE mode required")
    if request.report_times is not None and type(request.report_times) is not tuple:
        raise ValueError("fixed grid must be tuple")
    fixed = (
        None
        if request.report_times is None
        else tuple(timestamp_us(t) for t in request.report_times)
    )
    if fixed is not None and (
        not fixed
        or len(fixed) > 32769
        or any(b <= a for a, b in zip(fixed, fixed[1:], strict=False))
    ):
        raise ValueError("unsupported/nonincreasing report grid")
    step = request.report_step_us
    if step is not None and (type(step) is not int or step <= 0 or fixed is not None):
        raise ValueError("positive report step or explicit tuple, not both")
    cutoff = None if request.cutoff is None else timestamp_us(request.cutoff)
    if cutoff is not None and cutoff > 3_600_000_000:
        raise ValueError("unsupported cutoff beyond one-hour envelope")
    actuator = CausalRunner(
        initial_angle=request.initial_angle,
        closing_seconds=request.closing_seconds,
        opening_seconds=request.opening_seconds,
    )
    rows = json.loads(b.inputs_json)
    if type(rows) is not list or len(rows) > 8192 or canonical(rows) != b.inputs_json:
        raise ValueError("unsupported/noncanonical input batch")
    c = _fresh(request.controller_json) if controller is None else controller
    if _settings(c) != request.controller_json:
        raise ValueError("controller settings differ from retained request")
    indexed = list(enumerate(rows))
    error = None
    if request.mode == "OFFLINE":
        try:
            for _, row in indexed:
                _validate_row(row)
            indexed.sort(key=lambda x: (timestamp_us(x[1]["timestamp"]), x[0]))
        except (ValueError, TypeError, KeyError) as exc:
            error = str(exc)
            indexed = []
    events, links = [], []
    calls = 0
    last = None
    seen = set()
    for index, row in indexed:
        try:
            # ARRIVAL must parse the next time before cutoff, without evaluating it.
            t = timestamp_us(row["timestamp"])
            if events and cutoff is not None and t > cutoff:
                break
            t, frame = _validate_row(row)
            if not events and cutoff is not None and cutoff < t:
                raise ValueError("cutoff precedes origin")
            if last is not None and t > last and row["event_id"] in seen:
                raise ValueError("accepted event identity reused")
            if type(c) is MultimodalDecisionEngine:
                if calls == 0:
                    c.reset(initial_time_s=t / 1_000_000)
                calls += 1
                d = c.evaluate_frame(frame, scenario_run_id=b.fixture_id)
            else:
                command = c.commands[calls]
                calls += 1
                rule = (
                    (REJECT[1] if t == last else REJECT[0])
                    if last is not None and t <= last
                    else None
                )
                d = DecisionRecord(
                    frame.master_timestamp_s,
                    b.fixture_id,
                    "SCRIPTED",
                    "SCRIPTED",
                    "OPEN",
                    command,
                    rule_id=rule,
                    gate_command=command,
                )
            accepted = d.rule_id not in REJECT
            cmd = (
                normalize_command(d.resulting_gate_state, d.gate_command).value
                if accepted
                else None
            )
            links.append(
                DecisionLink(
                    index,
                    t,
                    row["event_id"],
                    _decision_json(d),
                    accepted,
                    d.resulting_gate_state,
                    cmd,
                )
            )
            if accepted:
                if last is not None and t <= last:
                    raise ValueError("controller accepted a rejected exact timestamp")
                events.append(SyntheticEvent(row["event_id"], t, cmd))
                last = t
                seen.add(row["event_id"])
            if cutoff == t and accepted:
                break
        except (ValueError, TypeError, KeyError, IndexError, RuntimeError) as exc:
            error = str(exc)
            if error == "cutoff precedes origin":
                raise ValueError(error) from exc
            break
    if calls == 0 and type(c) is MultimodalDecisionEngine:
        c.reset(initial_time_s=0.0)
    horizon = cutoff if cutoff is not None else last
    if step is not None and events and error is None:
        origin = events[0].timestamp
        assert type(origin) is int and horizon is not None
        if (horizon - origin + step - 1) // step > 32768:
            raise ValueError("unsupported report workload")
        fixed = tuple(range(origin, horizon + 1, step))
        if fixed[-1] != horizon:
            fixed += (horizon,)
    if fixed is not None and len(fixed) > 32769:
        raise ValueError("unsupported report workload")
    causal = actuator.run(
        events,
        fixture_id=b.fixture_id,
        mode="ARRIVAL",
        cutoff=None if error else cutoff,
        report_times=None if error else fixed,
    )
    if error:
        causal = replace(causal, status="INCOMPLETE", reason=error, report_endpoint_seconds=None)
    if len(causal.intervals) > 8192:
        raise ValueError("unsupported emitted interval workload")
    snapshot = request.canonical_json()
    return IntegrationResult(
        snapshot,
        hashlib.sha256(snapshot.encode()).hexdigest(),
        request.code_identity,
        causal.status,
        error,
        causal,
        tuple(links),
        calls,
        request.mode,
        [i for i, _ in indexed] != list(range(len(rows))),
    )


def verify_result(candidate: IntegrationResult, *, expected_request: IntegrationRequest) -> bool:
    """Full deterministic replay; caller retains expected request/code independently."""
    if type(candidate) is not IntegrationResult or type(expected_request) is not IntegrationRequest:
        return False
    try:
        return candidate.canonical_json() == run_pipeline(expected_request).canonical_json()
    except (ValueError, TypeError, KeyError, IndexError):
        return False
