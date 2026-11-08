"""Constructed blind-review domain/player. Cannot create genuine human evidence.

No real player, resource opener, active-schema promotion or identity service is
wired here. State is cooperative in-process; durable transactions are separate.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from fractions import Fraction

RISK_SUBJECTS = (
    "EXPLICIT_REVIEWER_FLAG",
    "UNCERTAIN_BOUNDARY",
    "ENGINE_T3_T4_INTERPRETATION",
    "FRONT_BACK_CONFLICT",
    "MEDIA_HASH_MISSING_OR_INCONSISTENT",
    "CORRECTED_FROM_CANDIDATE",
)
BOUNDARIES = ("T0", "T1", "T2", "T3", "T4", "SCENE_CLEAR")


def _id(value):
    if type(value) is not str or not value.startswith("synthetic:") or len(value) <= 10:
        raise ValueError("constructed identity required; not a real appointment")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


@dataclass(frozen=True)
class SyntheticReviewer:
    principal: str
    roles: tuple[str, ...]
    qualification: str = "CONSTRUCTED_TEST_ONLY"


@dataclass(frozen=True)
class Observation:
    boundary: str
    camera: str
    state: str
    rationale: str
    value_us: int | None = None
    censoring_direction: str | None = None
    uncertainty_us: int | None = None
    pts_ticks: int | None = None
    timebase: tuple[int, int] | None = None
    origin_us: int = 0
    landmark: str | None = None

    def validate(self):
        if self.boundary not in BOUNDARIES or self.camera not in ("front", "back"):
            raise ValueError("known boundary and local camera required")
        if self.state not in ("OBSERVABLE", "UNCERTAIN", "CENSORED", "NOT_OBSERVABLE"):
            raise ValueError("known state required; no APPROVED state")
        if type(self.rationale) is not str or not self.rationale.strip():
            raise ValueError("rationale required")
        if self.state == "OBSERVABLE":
            if type(self.value_us) is not int or self.value_us < 0:
                raise ValueError("observable exact nonnegative point required")
            if self.boundary == "T2" and not self.landmark:
                raise ValueError("T2 landmark remains deferred")
        elif self.value_us is not None:
            raise ValueError("nonpoint state cannot invent a point")
        if self.state == "CENSORED":
            if self.censoring_direction not in ("LEFT", "RIGHT"):
                raise ValueError("explicit censoring direction required")
        elif self.censoring_direction is not None:
            raise ValueError("censoring direction only on censored state")
        if self.uncertainty_us is not None and (
            type(self.uncertainty_us) is not int or self.uncertainty_us < 0
        ):
            raise ValueError("uncertainty exact or unknown; no default tolerance")
        if type(self.origin_us) is not int or self.origin_us < 0:
            raise ValueError("explicit local origin required")
        if self.pts_ticks is not None:
            tb = self.timebase
            if (
                type(self.pts_ticks) is not int
                or self.pts_ticks < 0
                or type(tb) is not tuple
                or len(tb) != 2
                or any(type(v) is not int or v <= 0 for v in tb)
            ):
                raise ValueError("exact PTS/timebase required")
            if self.value_us is not None and (
                Fraction(self.pts_ticks * tb[0] * 1_000_000, tb[1]) + self.origin_us
                != self.value_us
            ):
                raise ValueError("PTS/local clock mismatch")
        elif self.timebase is not None:
            raise ValueError("timebase without PTS")


@dataclass(frozen=True)
class Seal:
    actor: str
    event: str
    body: str
    digest: str
    kind: str = "BLIND_SEALED"
    previous: str | None = None


class ConstructedPlayer:
    """Neutral PTS surrogate; no arbitrary path or prediction material accepted."""

    def __init__(self, frames: tuple[tuple[int, str], ...]):
        if (
            type(frames) is not tuple
            or not frames
            or any(
                type(t) is not int or t < 0 or v != "NEUTRAL_CONSTRUCTED_FRAME" for t, v in frames
            )
            or any(b[0] <= a[0] for a, b in zip(frames, frames[1:], strict=False))
        ):
            raise ValueError("monotone neutral constructed PTS frames required")
        self._frames = frames

    def seek(self, index):
        if type(index) is not int or not 0 <= index < len(self._frames):
            raise ValueError("frame index outside declared constructed sequence")
        return self._frames[index]


class ReviewWorkflow:
    def __init__(
        self, reviewers: tuple[SyntheticReviewer, ...], *, aliases: tuple[tuple[str, str], ...] = ()
    ):
        self._roles: dict[str, tuple[str, ...]] = {}
        for person in reviewers:
            if (
                type(person) is not SyntheticReviewer
                or person.qualification != "CONSTRUCTED_TEST_ONLY"
            ):
                raise ValueError("synthetic role fixtures only")
            _id(person.principal)
            if person.principal in self._roles or not set(person.roles) <= {
                "REVIEWER",
                "ADJUDICATOR",
            }:
                raise ValueError("duplicate principal or unsupported role")
            self._roles[person.principal] = person.roles
        self._aliases = dict(aliases)
        if len(self._aliases) != len(aliases):
            raise ValueError("duplicate alias")
        for a, target in aliases:
            _id(a)
            _id(target)
            if a in self._roles or target in self._aliases:
                raise ValueError("ambiguous/chained principal alias")
        self._seals: dict[tuple[str, str], Seal] = {}
        self._exposed: set[tuple[str, str]] = set()
        self._history: tuple[Seal | tuple[object, ...], ...] = ()

    @property
    def history(self):
        return self._history

    def _actor(self, actor, role):
        actor = self._aliases.get(actor, actor)
        if role not in self._roles.get(actor, ()):
            raise ValueError("role not appointed in constructed fixture")
        return actor

    @staticmethod
    def _body(observations):
        if (
            type(observations) is not tuple
            or len(observations) != len(BOUNDARIES)
            or any(type(o) is not Observation for o in observations)
            or {o.boundary for o in observations} != set(BOUNDARIES)
        ):
            raise ValueError("all six unique boundary states required")
        for o in observations:
            if type(o) is not Observation:
                raise ValueError("typed observations required")
            o.validate()
        by_name = {o.boundary: o for o in observations}
        for camera in ("front", "back"):
            points = [
                by_name[k].value_us
                for k in BOUNDARIES
                if by_name[k].camera == camera and by_name[k].value_us is not None
            ]
            if points != sorted(points):
                raise ValueError("same-camera chronology conflict; never sort across cameras")
        return canonical([asdict(by_name[k]) for k in BOUNDARIES])

    def seal(self, actor, event, observations):
        actor = self._actor(actor, "REVIEWER")
        _id(event)
        if (actor, event) in self._seals or (actor, event) in self._exposed:
            raise ValueError("first seal consumed or actor/event already exposed")
        body = self._body(observations)
        seal = Seal(actor, event, body, digest(body))
        self._seals[actor, event] = seal
        self._history += (seal,)
        return seal

    def compare(self, actor, event, *, risk_inputs):
        actor = self._actor(actor, "REVIEWER")
        _id(event)
        risks = dict(risk_inputs)
        if (
            len(risk_inputs) != len(RISK_SUBJECTS)
            or set(risks) != set(RISK_SUBJECTS)
            or any(type(v) is not bool for v in risks.values())
        ):
            raise ValueError("all six evaluated risk subjects required; unknown denies")
        own = self._seals.get((actor, event))
        if own is not None and any(o["state"] == "UNCERTAIN" for o in json.loads(own.body)):
            if not risks["UNCERTAIN_BOUNDARY"]:
                raise ValueError("known uncertainty cannot be labeled no-risk")
        if risks["MEDIA_HASH_MISSING_OR_INCONSISTENT"]:
            raise ValueError("agreement cannot repair media identity")
        seals = tuple(s for (a, e), s in self._seals.items() if e == event)
        if (actor, event) not in self._seals or (any(risks.values()) and len(seals) < 2):
            raise ValueError("independent seals or no-second-required evidence missing")
        self._exposed.add((actor, event))
        self._history += (("EXPOSURE", actor, event, tuple(s.digest for s in seals)),)
        return seals

    def correct(self, actor, event, observations, *, reason):
        actor = self._actor(actor, "REVIEWER")
        if (actor, event) not in self._exposed or type(reason) is not str or not reason.strip():
            raise ValueError("informed correction requires exposure and reason")
        original = self._seals[actor, event]
        body = self._body(observations)
        seal = Seal(actor, event, body, digest(body), "INFORMED_CORRECTION", original.digest)
        self._history += (("CORRECTION_REASON", reason), seal)
        return seal

    def adjudicate(self, actor, event, *, source_digests, state, rationale):
        actor = self._actor(actor, "ADJUDICATOR")
        _id(event)
        sources = tuple(s for s in self._seals.values() if s.event == event)
        if (
            len(sources) < 2
            or actor in {s.actor for s in sources}
            or tuple(sorted(source_digests)) != tuple(sorted(s.digest for s in sources))
        ):
            raise ValueError("separate adjudicator and exact independent sources required")
        if state != "UNCERTAIN" or type(rationale) is not str or not rationale.strip():
            raise ValueError(
                "numeric dispute resolution needs actual human/versioned adapter evidence"
            )
        entry = ("ADJUDICATION", actor, event, source_digests, "UNCERTAIN", rationale)
        self._history += (entry,)
        return entry

    def draft(self):
        return {
            "schema": "CONSTRUCTED_REVIEW_DOMAIN_V1",
            "active_schema_satisfied": False,
            "history": canonical([asdict(x) if type(x) is Seal else x for x in self.history]),
        }
