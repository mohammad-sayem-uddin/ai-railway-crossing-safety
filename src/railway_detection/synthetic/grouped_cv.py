"""Deterministic physical-event grouping over constructed synthetic metadata.

SYNTHETIC_GROUPED_V1 is heuristic-first with bounded feasibility search. It does
not promise C2's exhaustive lexicographic optimum, authenticate real lineage,
load files, train models or write official split manifests.
"""

from __future__ import annotations

import hashlib
import heapq
import json
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

PROFILE = "SYNTHETIC_GROUPED_V1"
_ID = re.compile(r"synthetic:[A-Za-z0-9][A-Za-z0-9._:-]*\Z")
_LABEL = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]*\Z")
MAX_SEARCH_EVENTS = 18


class InvalidInput(ValueError):
    """Explicit no-allocation error channel for malformed synthetic metadata."""

    status = "INVALID_INPUT"


class DatasetRole(str, Enum):
    DEVELOPMENT_POOL = "DEVELOPMENT_POOL"
    CALIBRATION_ONLY = "CALIBRATION_ONLY"
    RESERVED_CONTROL = "RESERVED_CONTROL"
    CASE_STUDY = "CASE_STUDY"
    FINAL_DESCRIPTIVE = "FINAL_DESCRIPTIVE"


@dataclass(frozen=True)
class MetadataValue:
    value: str | None = None
    unknown_reason: str | None = "not supplied by synthetic fixture"
    provenance_ref: str = "synthetic:metadata:fixture"


@dataclass(frozen=True)
class PhysicalEvent:
    event_id: str
    role: DatasetRole
    labels: tuple[str, ...]
    aliases: tuple[str, ...] = ()
    weather: MetadataValue = field(default_factory=MetadataValue)
    lighting: MetadataValue = field(default_factory=MetadataValue)
    direction: MetadataValue = field(default_factory=MetadataValue)
    provenance_ref: str = "synthetic:event:fixture"


@dataclass(frozen=True)
class Capture:
    capture_id: str
    event_ids: tuple[str, ...]
    kind: str = "STILL"
    camera: MetadataValue = field(default_factory=MetadataValue)
    crossing: MetadataValue = field(default_factory=MetadataValue)
    session: MetadataValue = field(default_factory=MetadataValue)
    provenance_ref: str = "synthetic:capture:fixture"


@dataclass(frozen=True)
class Transform:
    transform_id: str
    version: str
    parameters: tuple[tuple[str, str], ...]
    provenance_ref: str = "synthetic:transform:fixture"


@dataclass(frozen=True)
class Asset:
    asset_id: str
    event_id: str
    kind: str
    annotation_ids: tuple[str, ...]
    capture_id: str | None = None
    parent_ids: tuple[str, ...] = ()
    transform: Transform | None = None
    frame_index: int | None = None
    pts_ticks: int | None = None
    timebase: tuple[int, int] | None = None
    unavailable_reason: str | None = None
    content_identity: str | None = None
    provenance_ref: str = "synthetic:asset:fixture"


@dataclass(frozen=True)
class Annotation:
    annotation_id: str
    asset_id: str
    labels: tuple[str, ...]
    confirmed_empty: bool = False
    provenance_ref: str = "synthetic:annotation:fixture"


@dataclass(frozen=True)
class SyntheticDataset:
    dataset_id: str
    events: tuple[PhysicalEvent, ...]
    captures: tuple[Capture, ...]
    assets: tuple[Asset, ...]
    annotations: tuple[Annotation, ...]
    version: str = "1"


@dataclass(frozen=True)
class Group:
    event_id: str
    role: DatasetRole
    labels: tuple[str, ...]
    original_asset_count: int
    asset_ids: tuple[str, ...]


@dataclass(frozen=True)
class ValidatedDataset:
    dataset: SyntheticDataset
    groups: tuple[Group, ...]
    aliases: tuple[tuple[str, str], ...]
    input_digest: str


def _identity(value: str) -> None:
    if type(value) is not str or not _ID.fullmatch(value):
        raise InvalidInput("explicit synthetic identity required; missing/real/ambiguous ID denied")


def _ids(values: tuple[str, ...], *, labels: bool = False) -> None:
    if type(values) is not tuple:
        raise InvalidInput("immutable tuple required")
    pattern = _LABEL if labels else _ID
    if any(type(v) is not str or not pattern.fullmatch(v) for v in values):
        raise InvalidInput("invalid identity/label")
    if len(set(values)) != len(values):
        raise InvalidInput("duplicate identity/label")


def _metadata(value: MetadataValue) -> None:
    if type(value) is not MetadataValue:
        raise InvalidInput("typed metadata with known value or explicit unknown reason required")
    _identity(value.provenance_ref)
    if (value.value is None) == (value.unknown_reason is None):
        raise InvalidInput("metadata must have exactly a known value or an unknown reason")
    text = value.unknown_reason if value.value is None else value.value
    if type(text) is not str or not text.strip():
        raise InvalidInput("metadata value/reason cannot be blank")


def _records(values: tuple, kind: type, key: str) -> dict:
    if type(values) is not tuple or any(type(v) is not kind for v in values):
        raise InvalidInput("typed immutable registry required")
    result = {}
    for record in values:
        identity = getattr(record, key)
        _identity(identity)
        _identity(record.provenance_ref)
        if identity in result:
            raise InvalidInput("duplicate registry identity")
        result[identity] = record
    return result


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def validate_dataset(dataset: SyntheticDataset) -> ValidatedDataset:
    """Validate complete metadata joins before attempting any allocation."""
    if type(dataset) is not SyntheticDataset:
        raise InvalidInput("explicit SyntheticDataset required")
    _identity(dataset.dataset_id)
    if type(dataset.version) is not str or not dataset.version.strip():
        raise InvalidInput("dataset version required")
    events = _records(dataset.events, PhysicalEvent, "event_id")
    captures = _records(dataset.captures, Capture, "capture_id")
    assets = _records(dataset.assets, Asset, "asset_id")
    annotations = _records(dataset.annotations, Annotation, "annotation_id")
    if not events:
        raise InvalidInput("empty event registry")
    aliases: dict[str, str] = {}
    for e in events.values():
        if type(e.role) is not DatasetRole:
            raise InvalidInput("unknown/unapproved synthetic dataset role")
        _ids(e.labels, labels=True)
        _ids(e.aliases)
        for v in (e.weather, e.lighting, e.direction):
            _metadata(v)
        for alias in (e.event_id, *e.aliases):
            if alias in aliases:
                raise InvalidInput("ambiguous/conflicting physical-event alias")
            aliases[alias] = e.event_id

    def resolve(identity: str) -> str:
        _identity(identity)
        if identity not in aliases:
            raise InvalidInput("unknown physical-event identity")
        return aliases[identity]

    capture_members: dict[str, set[str]] = {}
    for c in captures.values():
        _ids(c.event_ids)
        members = [resolve(e) for e in c.event_ids]
        if not members or len(set(members)) != len(members) or c.kind not in ("STILL", "VIDEO"):
            raise InvalidInput("invalid capture event membership or kind")
        for v in (c.camera, c.crossing, c.session):
            _metadata(v)
        capture_members[c.capture_id] = set(members)

    asset_event: dict[str, str] = {}
    content_owner: dict[str, str] = {}
    originals: Counter = Counter()
    event_assets: dict[str, list[str]] = defaultdict(list)
    indegree: dict[str, int] = {}
    children: dict[str, list[str]] = defaultdict(list)
    annotation_owner: dict[str, str] = {}
    transform_versions: dict[str, tuple] = {}
    for a in assets.values():
        event = resolve(a.event_id)
        asset_event[a.asset_id] = event
        event_assets[event].append(a.asset_id)
        _ids(a.parent_ids)
        _ids(a.annotation_ids)
        if not a.annotation_ids:
            raise InvalidInput("every accepted source/derivative needs an annotation disposition")
        if a.kind not in ("ORIGINAL_FRAME", "STILL", "DERIVATIVE"):
            raise InvalidInput("unknown asset kind")
        if a.capture_id is not None:
            _identity(a.capture_id)
            if a.capture_id not in captures or event not in capture_members[a.capture_id]:
                raise InvalidInput("asset/capture/event join mismatch")
        if a.kind == "DERIVATIVE":
            if not a.parent_ids or type(a.transform) is not Transform:
                raise InvalidInput("derivative requires parents and typed transformation")
            t = a.transform
            _identity(t.transform_id)
            _identity(t.provenance_ref)
            if type(t.version) is not str or not t.version.strip() or type(t.parameters) is not tuple:
                raise InvalidInput("transform version/parameters required")
            keys = []
            for pair in t.parameters:
                if type(pair) is not tuple or len(pair) != 2 or any(type(v) is not str for v in pair):
                    raise InvalidInput("transform parameters are exact string key/value pairs")
                if not pair[0]:
                    raise InvalidInput("blank transform parameter key")
                keys.append(pair[0])
            if len(set(keys)) != len(keys):
                raise InvalidInput("duplicate transform parameter")
            transform_key = (t.version, tuple(sorted(t.parameters)), t.provenance_ref)
            if (t.transform_id in transform_versions
                    and transform_versions[t.transform_id] != transform_key):
                raise InvalidInput("conflicting transform identity/version")
            transform_versions[t.transform_id] = transform_key
        elif a.parent_ids or a.transform is not None or a.capture_id is None:
            raise InvalidInput("original asset requires capture and no derivative parents/transform")
        else:
            if a.kind == "ORIGINAL_FRAME" and captures[a.capture_id].kind != "VIDEO":
                raise InvalidInput("video frame must reference a VIDEO capture")
            if a.kind == "STILL" and captures[a.capture_id].kind != "STILL":
                raise InvalidInput("still must reference a STILL capture")
            originals[event] += 1
        if a.frame_index is not None and (type(a.frame_index) is not int or a.frame_index < 0):
            raise InvalidInput("invalid frame index")
        if (a.pts_ticks is None) != (a.timebase is None):
            raise InvalidInput("PTS and timebase must be supplied together")
        if a.pts_ticks is not None:
            if type(a.pts_ticks) is not int or a.pts_ticks < 0 or type(a.timebase) is not tuple:
                raise InvalidInput("invalid PTS")
            if len(a.timebase) != 2 or any(type(v) is not int or v <= 0 for v in a.timebase):
                raise InvalidInput("timebase must be positive exact rational pair")
            if math_gcd(*a.timebase) != 1:
                raise InvalidInput("timebase must be reduced")
        if a.kind == "ORIGINAL_FRAME" and (a.frame_index is None or a.pts_ticks is None):
            if type(a.unavailable_reason) is not str or not a.unavailable_reason.strip():
                raise InvalidInput("unavailable frame timing requires an explicit reason")
        if a.content_identity is not None:
            _identity(a.content_identity)
            if a.content_identity in content_owner and content_owner[a.content_identity] != event:
                raise InvalidInput("cross-event duplicate content identity is unresolved")
            content_owner[a.content_identity] = event
        indegree[a.asset_id] = len(a.parent_ids)
        for parent in a.parent_ids:
            if parent not in assets:
                raise InvalidInput("orphan derivative")
            children[parent].append(a.asset_id)
        for ann_id in a.annotation_ids:
            if ann_id in annotation_owner:
                raise InvalidInput("annotation attached to multiple assets")
            annotation_owner[ann_id] = a.asset_id

    queue = [i for i, degree in indegree.items() if degree == 0]
    heapq.heapify(queue)
    visited = 0
    while queue:
        identity = heapq.heappop(queue)
        visited += 1
        for child in children[identity]:
            if asset_event[identity] != asset_event[child]:
                raise InvalidInput("multi-event derivative rejected under this profile")
            indegree[child] -= 1
            if indegree[child] == 0:
                heapq.heappush(queue, child)
    if visited != len(assets):
        raise InvalidInput("cyclic derivative lineage")
    if set(annotation_owner) != set(annotations):
        raise InvalidInput("missing/orphan annotation registry entry")
    original_labels: dict[str, set[str]] = defaultdict(set)
    for ann in annotations.values():
        _ids(ann.labels, labels=True)
        if type(ann.confirmed_empty) is not bool or (not ann.labels and not ann.confirmed_empty):
            raise InvalidInput("empty labels require explicit confirmed-empty disposition")
        if ann.labels and ann.confirmed_empty:
            raise InvalidInput("nonempty labels cannot be confirmed-empty")
        if ann.asset_id != annotation_owner[ann.annotation_id]:
            raise InvalidInput("annotation-to-asset mismatch")
        e = asset_event[ann.asset_id]
        if not set(ann.labels) <= set(events[e].labels):
            raise InvalidInput("annotation labels conflict with supplied event labels")
        if assets[ann.asset_id].kind != "DERIVATIVE":
            original_labels[e].update(ann.labels)
    if any(originals[e] < 1 or original_labels[e] != set(events[e].labels) for e in events):
        raise InvalidInput("missing originals or unsubstantiated event labels")

    groups = tuple(Group(e.event_id, e.role, tuple(sorted(e.labels)), originals[e.event_id],
                         tuple(sorted(event_assets[e.event_id])))
                   for e in sorted(events.values(), key=lambda e: e.event_id))
    payload = asdict(dataset)
    payload["events"] = sorted(payload["events"], key=lambda e: e["event_id"])
    payload["captures"] = sorted(payload["captures"], key=lambda c: c["capture_id"])
    payload["assets"] = sorted(payload["assets"], key=lambda a: a["asset_id"])
    payload["annotations"] = sorted(payload["annotations"], key=lambda a: a["annotation_id"])
    for e in payload["events"]:
        e["aliases"], e["labels"] = sorted(e["aliases"]), sorted(e["labels"])
    for c in payload["captures"]:
        c["event_ids"] = sorted(resolve(e) for e in c["event_ids"])
    for a in payload["assets"]:
        a["event_id"] = resolve(a["event_id"])
        a["parent_ids"], a["annotation_ids"] = sorted(a["parent_ids"]), sorted(a["annotation_ids"])
        if a["transform"] is not None:
            a["transform"]["parameters"] = sorted(a["transform"]["parameters"])
    for a in payload["annotations"]:
        a["labels"] = sorted(a["labels"])
    digest = hashlib.sha256(_json(payload).encode()).hexdigest()
    return ValidatedDataset(dataset, groups, tuple(sorted(aliases.items())), digest)


def math_gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return a


@dataclass(frozen=True)
class Allocation:
    profile: str
    dataset_id: str
    input_digest: str
    k: int
    required_support: tuple[tuple[str, int], ...]
    node_budget: int
    visited_nodes: int
    greedy_choices: int
    status: str
    assignments: tuple[tuple[str, int], ...]
    objective: tuple[int, int, int] | None
    reason: str | None
    limitations: tuple[str, ...] = (
        "synthetic metadata only; no physical truth or scientific eligibility certification",
        "feasibility only; no global optimality or independent-model-exposure guarantee",
    )

    def canonical_json(self) -> str:
        return _json(asdict(self))


def _objective(groups: tuple[Group, ...], assignment: dict[str, int], k: int,
               labels: tuple[str, ...]) -> tuple[int, int, int]:
    ec, fc = [0]*k, [0]*k
    counts = {label: [0]*k for label in labels}
    for g in groups:
        if g.event_id not in assignment:
            continue
        fold = assignment[g.event_id]
        ec[fold] += 1
        fc[fold] += g.original_asset_count
        for label in labels:
            counts[label][fold] += int(label in g.labels)
    def score(vs: list[int]) -> int:
        total = sum(vs)
        return sum((k*v-total)**2 for v in vs)
    return score(ec), sum(score(vs) for vs in counts.values()), score(fc)


def _valid(groups: tuple[Group, ...], assignment: dict[str, int], k: int,
           support: tuple[tuple[str, int], ...]) -> bool:
    for fold in range(k):
        members = [g for g in groups if assignment.get(g.event_id) == fold]
        if not members or any(sum(label in g.labels for g in members) < minimum
                              for label, minimum in support):
            return False
    return True


def allocate(dataset: SyntheticDataset, *, k: int,
             required_support: tuple[tuple[str, int], ...] = (),
             node_budget: int = 100_000, allow_ungrouped_fallback: bool = False) -> Allocation:
    """Return a verified feasible allocation or explicit no-assignment status."""
    registry = validate_dataset(dataset)
    if type(k) is not int or k < 2:
        raise InvalidInput("k must be an integer >=2")
    if type(node_budget) is not int or node_budget < 1:
        raise InvalidInput("positive deterministic node budget required")
    if allow_ungrouped_fallback is not False:
        raise InvalidInput("ungrouped fallback forbidden under every flag")
    if type(required_support) is not tuple:
        raise InvalidInput("immutable explicit support rules required")
    rules = {}
    for pair in required_support:
        if type(pair) is not tuple or len(pair) != 2:
            raise InvalidInput("support rule is (label,minimum)")
        label, minimum = pair
        if type(label) is not str or not _LABEL.fullmatch(label):
            raise InvalidInput("invalid support label")
        if label in rules or type(minimum) is not int or minimum < 1:
            raise InvalidInput("duplicate/nonpositive support rule")
        rules[label] = minimum
    support = tuple(sorted(rules.items()))
    groups = tuple(g for g in registry.groups if g.role == DatasetRole.DEVELOPMENT_POOL)
    ordered = tuple(sorted(groups, key=lambda g: (-g.original_asset_count, g.event_id)))
    labels = tuple(sorted({label for g in groups for label in g.labels}))
    visited = choices = 0

    def result(status: str, assignment: dict[str, int] | None = None,
               reason: str | None = None) -> Allocation:
        if assignment is not None and not _valid(groups, assignment, k, support):
            raise RuntimeError("internal allocation verification failed")
        return Allocation(PROFILE, dataset.dataset_id, registry.input_digest, k, support,
                          node_budget, visited, choices, status,
                          tuple(sorted((assignment or {}).items())),
                          None if assignment is None else _objective(groups, assignment, k, labels),
                          reason)

    if len(groups) < k or any(sum(label in g.labels for g in groups) < k*minimum
                              for label, minimum in support):
        return result("INFEASIBLE_NECESSARY", reason="insufficient nonempty folds/label support")
    assignment: dict[str, int] = {}
    # Maintain sufficient statistics; scoring K choices must not rescan all M events.
    ec, fc = [0]*k, [0]*k
    lc = {label: [0]*k for label in labels}
    event_squares = frame_squares = frame_total = 0
    label_squares = dict.fromkeys(labels, 0)
    label_totals = dict.fromkeys(labels, 0)
    for g in ordered:
        present = set(g.labels)
        def cost(fold: int) -> tuple[int, int, int, int]:
            event_score = k*k*(event_squares + 2*ec[fold] + 1) - k*(len(assignment)+1)**2
            frame_score = (k*k*(frame_squares + 2*fc[fold]*g.original_asset_count
                                      + g.original_asset_count**2)
                           - k*(frame_total+g.original_asset_count)**2)
            class_score = sum(
                k*k*(label_squares[label] + (2*lc[label][fold]+1 if label in present else 0))
                - k*(label_totals[label]+int(label in present))**2 for label in labels
            )
            return event_score, class_score, frame_score, fold
        fold = min(range(k), key=cost)
        choices += k
        assignment[g.event_id] = fold
        event_squares += 2*ec[fold]+1
        frame_squares += 2*fc[fold]*g.original_asset_count + g.original_asset_count**2
        frame_total += g.original_asset_count
        ec[fold] += 1
        fc[fold] += g.original_asset_count
        for label in labels:
            if label in present:
                label_squares[label] += 2*lc[label][fold]+1
                label_totals[label] += 1
                lc[label][fold] += 1
    if _valid(groups, assignment, k, support):
        return result("FEASIBLE_GREEDY", assignment)
    if len(groups) > MAX_SEARCH_EVENTS:
        return result("UNDETERMINED_SIZE", reason="greedy failed; bounded exact search limited to18")
    assignment = {}
    exhausted_budget = False
    solution = None

    def search(depth: int, max_used: int) -> None:
        nonlocal visited, exhausted_budget, solution
        if solution is not None or exhausted_budget:
            return
        if visited >= node_budget:
            exhausted_budget = True
            return
        visited += 1
        remaining = ordered[depth:]
        used = set(assignment.values())
        if k-len(used) > len(remaining):
            return
        for fold in range(k):
            members = [g for g in ordered[:depth] if assignment.get(g.event_id) == fold]
            if any(sum(label in g.labels for g in members) +
                   sum(label in g.labels for g in remaining) < minimum
                   for label, minimum in support):
                return
        if depth == len(ordered):
            if _valid(groups, assignment, k, support):
                solution = dict(assignment)
            return
        for fold in range(min(k, max_used+2)):
            assignment[ordered[depth].event_id] = fold
            search(depth+1, max(max_used, fold))
            del assignment[ordered[depth].event_id]
            if solution is not None or exhausted_budget:
                return

    search(0, -1)
    if solution is not None:
        return result("FEASIBLE_SEARCH", solution)
    if exhausted_budget:
        return result("UNDETERMINED_BUDGET", reason="deterministic search budget exhausted")
    return result("INFEASIBLE_EXHAUSTIVE", reason="all canonical feasible branches exhausted")


def verify_allocation(dataset: SyntheticDataset, allocation: Allocation) -> bool:
    registry = validate_dataset(dataset)
    if type(allocation) is not Allocation or allocation.profile != PROFILE:
        raise InvalidInput("wrong allocation type/profile")
    if allocation.input_digest != registry.input_digest or allocation.dataset_id != dataset.dataset_id:
        raise InvalidInput("allocation inputs do not match verified synthetic registry")
    if (type(allocation.k) is not int or allocation.k < 2
            or type(allocation.node_budget) is not int or allocation.node_budget < 1
            or type(allocation.visited_nodes) is not int
            or not 0 <= allocation.visited_nodes <= allocation.node_budget):
        raise InvalidInput("invalid allocation configuration/receipt")
    if allocation.status not in (
        "FEASIBLE_GREEDY", "FEASIBLE_SEARCH", "INFEASIBLE_NECESSARY",
        "INFEASIBLE_EXHAUSTIVE", "UNDETERMINED_BUDGET", "UNDETERMINED_SIZE",
    ):
        raise InvalidInput("unknown feasibility status")
    if type(allocation.required_support) is not tuple:
        raise InvalidInput("invalid support receipt")
    support_labels = set()
    for pair in allocation.required_support:
        if type(pair) is not tuple or len(pair) != 2:
            raise InvalidInput("invalid support receipt")
        label, minimum = pair
        if (type(label) is not str or not _LABEL.fullmatch(label) or label in support_labels
                or type(minimum) is not int or minimum < 1):
            raise InvalidInput("invalid/duplicate support receipt")
        support_labels.add(label)
    if allocation.status not in ("FEASIBLE_GREEDY", "FEASIBLE_SEARCH"):
        if allocation.assignments or allocation.objective is not None:
            raise InvalidInput("failed/undetermined result cannot contain accepted assignment")
        return False
    groups = tuple(g for g in registry.groups if g.role == DatasetRole.DEVELOPMENT_POOL)
    assignment = dict(allocation.assignments)
    if len(assignment) != len(allocation.assignments) or set(assignment) != {g.event_id for g in groups}:
        raise InvalidInput("duplicate/missing/extra or reserved event in allocation")
    if type(allocation.k) is not int or allocation.k < 2:
        raise InvalidInput("invalid fold count")
    if any(type(v) is not int or not 0 <= v < allocation.k for v in assignment.values()):
        raise InvalidInput("invalid fold index")
    if not _valid(groups, assignment, allocation.k, allocation.required_support):
        raise InvalidInput("allocation violates support/nonempty folds")
    labels = tuple(sorted({label for g in groups for label in g.labels}))
    if allocation.objective != _objective(groups, assignment, allocation.k, labels):
        raise InvalidInput("forged objective")
    return True


@dataclass(frozen=True)
class RolePlan:
    development: tuple[str, ...]
    outer_evaluation: tuple[str, ...]
    training: tuple[str, ...]
    validation: tuple[str, ...]
    calibration: tuple[str, ...]
    reserved_controls: tuple[str, ...]
    case_studies: tuple[str, ...]
    final_descriptive: tuple[str, ...]
    calibration_mode: str
    frozen_rule_id: str | None


def role_plan(dataset: SyntheticDataset, allocation: Allocation, *, outer_fold: int,
              validation_events: tuple[str, ...] = (), calibration_mode: str = "NONE",
              frozen_rule_id: str | None = None) -> RolePlan:
    if not verify_allocation(dataset, allocation):
        raise InvalidInput("no accepted allocation for role plan")
    if type(outer_fold) is not int or not 0 <= outer_fold < allocation.k:
        raise InvalidInput("invalid outer fold")
    _ids(validation_events)
    if calibration_mode not in ("NONE", "RESERVED_CALIBRATION", "INNER_OOF"):
        raise InvalidInput("unknown calibration operation policy")
    if frozen_rule_id is not None:
        _identity(frozen_rule_id)
    registry = validate_dataset(dataset)
    by_role = {r: {g.event_id for g in registry.groups if g.role == r} for r in DatasetRole}
    dev = by_role[DatasetRole.DEVELOPMENT_POOL]
    evaluation = {e for e, f in allocation.assignments if f == outer_fold}
    validation = set(validation_events)
    complement = dev-evaluation
    if not validation <= complement or not complement-validation:
        raise InvalidInput("inner validation outside outer complement or empty training")
    if not validation and frozen_rule_id is None:
        raise InvalidInput("empty inner tuning requires explicit frozen rule")
    if calibration_mode == "INNER_OOF" and not validation:
        raise InvalidInput("INNER_OOF requires an inner tuning plan")
    calibration = by_role[DatasetRole.CALIBRATION_ONLY]
    if calibration_mode == "RESERVED_CALIBRATION" and not calibration:
        raise InvalidInput("reserved calibration mode requires calibration-only events")
    return RolePlan(tuple(sorted(dev)), tuple(sorted(evaluation)),
                    tuple(sorted(complement-validation)), tuple(sorted(validation)),
                    tuple(sorted(calibration)), tuple(sorted(by_role[DatasetRole.RESERVED_CONTROL])),
                    tuple(sorted(by_role[DatasetRole.CASE_STUDY])),
                    tuple(sorted(by_role[DatasetRole.FINAL_DESCRIPTIVE])),
                    calibration_mode, frozen_rule_id)


def validate_fit_membership(plan: RolePlan, operation: str, fit_events: tuple[str, ...], *,
                            selection_events: tuple[str, ...] = (),
                            producing_fit_events: tuple[str, ...] = ()) -> None:
    """Check proposed memberships only; no fitting/cache/model operation occurs.

    Full per-artifact evidence/OOF score provenance authentication is deferred.
    INNER_OOF therefore fails closed here rather than trusting a self-report.
    """
    if type(plan) is not RolePlan:
        raise InvalidInput("typed role plan required")
    if plan.calibration_mode not in ("NONE", "RESERVED_CALIBRATION", "INNER_OOF"):
        raise InvalidInput("unknown calibration operation policy")
    if plan.frozen_rule_id is not None:
        _identity(plan.frozen_rule_id)
    if not plan.validation and plan.frozen_rule_id is None:
        raise InvalidInput("empty inner tuning requires explicit frozen rule")
    sibling_roles = [plan.outer_evaluation, plan.training, plan.validation, plan.calibration,
                     plan.reserved_controls, plan.case_studies, plan.final_descriptive]
    seen: set[str] = set()
    for values in sibling_roles:
        _ids(values)
        if seen & set(values):
            raise InvalidInput("overlapping sibling roles")
        seen.update(values)
    _ids(plan.development)
    if (set(plan.development) != set(plan.outer_evaluation+plan.training+plan.validation)
            or not plan.training or not plan.outer_evaluation):
        raise InvalidInput("incomplete/invalid development role coverage")
    for values in (fit_events, selection_events, producing_fit_events):
        _ids(values)
    train, tune = set(plan.training), set(plan.validation)
    if not set(selection_events) <= train | tune:
        raise InvalidInput("selection used outer/reserved evaluation")
    if operation in ("BASE_MODEL_FIT", "PREPROCESSOR_FIT", "FEATURE_CACHE"):
        allowed = train
    elif operation == "FINAL_REFIT" and plan.frozen_rule_id is not None:
        allowed = train | tune
    elif operation == "CALIBRATOR_FIT" and plan.calibration_mode == "RESERVED_CALIBRATION":
        allowed = set(plan.calibration)
    else:
        raise InvalidInput("unsupported/unverified fitting or calibration provenance")
    if not set(fit_events) <= allowed or not set(producing_fit_events) <= train:
        raise InvalidInput("fit/cache producer membership violates declared role policy")
