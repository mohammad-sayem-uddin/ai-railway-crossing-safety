"""Constructed durable review knowledge across sessions; injected SQLite only.

This cooperative metadata store has no player/resource opener or live-human
record acceptance. An independently retained anchor detects rollback relative
to that anchor; same-user database/anchor replacement is not prevented.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, fields

from railway_detection.annotation.human_review_domain import (
    Observation,
    ReviewWorkflow,
    SyntheticReviewer,
    _id,
    canonical,
)


def _sha(body):
    return hashlib.sha256(body.encode()).hexdigest()


@dataclass(frozen=True)
class ReviewCommit:
    count: int
    head: str
    request_id: str
    result_digest: str
    classification: str = "CONSTRUCTED_ONLY_NOT_HUMAN_EVIDENCE"


class ConstructedReviewStore:
    def __init__(
        self,
        connection,
        *,
        reviewers: tuple[SyntheticReviewer, ...],
        events: tuple[str, ...],
        principal_aliases=(),
        event_aliases=(),
        expected_anchor: tuple[int, str | None],
    ):
        if type(events) is not tuple or not events or len(events) != len(set(events)):
            raise ValueError("fixed unique constructed physical-event registry required")
        for event in events:
            _id(event)
        self.reviewers = reviewers
        self.principal_aliases = principal_aliases
        self.events = events
        self.event_aliases = dict(event_aliases)
        if len(self.event_aliases) != len(event_aliases):
            raise ValueError("duplicate event alias")
        for alias, target in event_aliases:
            _id(alias)
            if alias in events or target not in events:
                raise ValueError("event alias must resolve directly into fixed registry")
        ReviewWorkflow(reviewers, aliases=principal_aliases)  # validate fixture roles/aliases
        self.context = canonical(
            {
                "reviewers": [asdict(p) for p in reviewers],
                "events": events,
                "principal_aliases": principal_aliases,
                "event_aliases": event_aliases,
            }
        )
        self.db = connection
        self.db.isolation_level = None
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.executescript("""
          CREATE TABLE IF NOT EXISTS constructed_review_context(body TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS constructed_review_log(
            seq INTEGER PRIMARY KEY, request TEXT UNIQUE NOT NULL, body TEXT NOT NULL,
            previous TEXT, head TEXT NOT NULL, result_digest TEXT NOT NULL);
        """)
        if (
            type(expected_anchor) is not tuple
            or len(expected_anchor) != 2
            or type(expected_anchor[0]) is not int
            or expected_anchor[0] < 0
            or (expected_anchor[0] == 0 and expected_anchor[1] is not None)
            or (
                expected_anchor[0] > 0
                and (
                    type(expected_anchor[1]) is not str
                    or len(expected_anchor[1]) != 64
                    or any(c not in "0123456789abcdef" for c in expected_anchor[1])
                )
            )
        ):
            raise ValueError("typed independent constructed anchor required")
        self.anchor = expected_anchor
        self.db.execute("BEGIN IMMEDIATE")
        try:
            contexts = self.db.execute("SELECT body FROM constructed_review_context").fetchall()
            if not contexts:
                if self.db.execute("SELECT COUNT(*) FROM constructed_review_log").fetchone()[0]:
                    raise ValueError("missing review context cannot be reinitialized over history")
                self.db.execute("INSERT INTO constructed_review_context VALUES(?)", (self.context,))
            elif contexts != [(self.context,)]:
                raise ValueError("review registry/role/context substitution")
            self._restore()
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def _apply(self, workflow, operation, actor, event, args):
        if operation in {"SEAL", "CORRECT"}:
            expected = {"observations"} | ({"reason"} if operation == "CORRECT" else set())
            if set(args) != expected or type(args["observations"]) is not list:
                raise ValueError("closed observation operation fields required")
            observations = []
            for value in args["observations"]:
                if type(value) is not dict or set(value) != {f.name for f in fields(Observation)}:
                    raise ValueError("closed observation record required")
                value = dict(value)
                if value["timebase"] is not None:
                    value["timebase"] = tuple(value["timebase"])
                observations.append(Observation(**value))
            if operation == "SEAL":
                return workflow.seal(actor, event, tuple(observations))
            return workflow.correct(actor, event, tuple(observations), reason=args["reason"])
        if operation == "COMPARE":
            if set(args) != {"risk_inputs"}:
                raise ValueError("closed risk inputs required")
            return workflow.compare(
                actor, event, risk_inputs=tuple(tuple(x) for x in args["risk_inputs"])
            )
        if operation == "ADJUDICATE":
            if set(args) != {"source_digests", "state", "rationale"}:
                raise ValueError("closed source-linked adjudication fields required")
            return workflow.adjudicate(
                actor,
                event,
                source_digests=tuple(args["source_digests"]),
                state=args["state"],
                rationale=args["rationale"],
            )
        raise ValueError("unknown constructed operation")

    @staticmethod
    def _result_digest(result):
        def value(item):
            if isinstance(item, tuple):
                return [value(x) for x in item]
            if hasattr(item, "__dataclass_fields__"):
                return asdict(item)
            return item

        return _sha(canonical(value(result)))

    def _restore(self):
        workflow = ReviewWorkflow(self.reviewers, aliases=self.principal_aliases)
        rows = self.db.execute(
            "SELECT seq,request,body,previous,head,result_digest "
            "FROM constructed_review_log ORDER BY seq"
        ).fetchall()
        if len(rows) > 8192:
            raise ValueError("constructed history workload bound exceeded")
        previous = None
        for index, (sequence, request, body, prev, head, result_digest) in enumerate(rows, 1):
            _id(request)
            payload = json.loads(body)
            if (
                canonical(payload) != body
                or set(payload) != {"operation", "actor", "event", "args"}
                or sequence != index
                or prev != previous
                or payload["event"] not in self.events
                or head != _sha(canonical({"sequence": sequence, "previous": prev, "body": body}))
            ):
                raise ValueError("constructed review journal corruption")
            result = self._apply(workflow, **payload)
            if result_digest != self._result_digest(result):
                raise ValueError("review result substitution")
            previous = head
        if (len(rows), previous) != self.anchor:
            raise ValueError("retained review anchor mismatch; no blind reset")
        return workflow

    def execute(self, operation, actor, event, *, request_id, **args):
        _id(request_id)
        if event in self.event_aliases:
            event = self.event_aliases[event]
        if event not in self.events:
            raise ValueError("unknown event/alias cannot create a fresh assignment")
        if "observations" in args:
            if type(args["observations"]) is not tuple or any(
                type(o) is not Observation for o in args["observations"]
            ):
                raise ValueError("typed immutable constructed observations required")
            args["observations"] = [asdict(o) for o in args["observations"]]
        body = canonical({"operation": operation, "actor": actor, "event": event, "args": args})
        payload = json.loads(body)
        self.db.execute("BEGIN IMMEDIATE")
        try:
            workflow = self._restore()
            existing = self.db.execute(
                "SELECT seq,body,head,result_digest FROM constructed_review_log WHERE request=?",
                (request_id,),
            ).fetchone()
            if existing:
                if existing[1] != body:
                    raise ValueError("review request content substitution")
                receipt = ReviewCommit(existing[0], existing[2], request_id, existing[3])
            else:
                if self.anchor[0] >= 8192:
                    raise ValueError("constructed history workload bound exceeded")
                result = self._apply(workflow, **payload)
                count, previous = self.anchor
                head = _sha(canonical({"sequence": count + 1, "previous": previous, "body": body}))
                receipt = ReviewCommit(count + 1, head, request_id, self._result_digest(result))
                self.db.execute(
                    "INSERT INTO constructed_review_log VALUES(?,?,?,?,?,?)",
                    (receipt.count, request_id, body, previous, head, receipt.result_digest),
                )
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise
        # Exact retries return their historical receipt without moving the current anchor back.
        if receipt.count > self.anchor[0]:
            self.anchor = receipt.count, receipt.head
        return receipt
