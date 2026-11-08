"""Constructed governance journal sharing WP04 permission, quota and transaction.

Retained anchors are caller-owned cooperative metadata. This is not independent
identity/storage/time, an authenticated human log or a power-loss guarantee.
"""

from __future__ import annotations

from dataclasses import asdict

from railway_detection.annotation.evidence_review.contracts import (
    FIXTURE,
    Batch,
    BoundaryObservation,
    Permission,
    Reviewer,
    canonical,
    digest,
)
from railway_detection.annotation.evidence_review.lifecycle import (
    Adjudication,
    Assignment,
    ReviewLifecycle,
)
from railway_detection.annotation.human_review_domain import Observation
from railway_detection.annotation.human_review_service import ReviewScope
from railway_detection.application.contracts import closed_json
from railway_detection.safety.constructed_authority import (
    ConstructedAuthority,
    Receipt,
    encode_payload,
    identity,
    sha,
)

SCHEMA = "CONSTRUCTED_GOVERNANCE_JOURNAL/1"


def observation(value: dict) -> BoundaryObservation:
    values = dict(value)
    item = dict(values.pop("observation"))
    if item["timebase"] is not None:
        item["timebase"] = tuple(item["timebase"])
    return BoundaryObservation(observation=Observation(**item), **values)


def apply_command(engine: ReviewLifecycle, command: dict) -> str:
    if set(command) != {"operation", "arguments", "permission", "now"}:
        raise ValueError("closed governance command required")
    p = dict(command["permission"])
    p["events"], p["operations"] = tuple(p["events"]), tuple(p["operations"])
    permission = Permission(**p)
    args = dict(command["arguments"])
    operation = command["operation"]
    if operation == "ASSIGN":
        a = dict(args["assignment"])
        a["source_ids"] = tuple(a["source_ids"])
        if set(args) != {"assignment"}:
            raise ValueError("closed assignment arguments required")
        return engine.assign(Assignment(**a), permission, now=command["now"])
    assignment_id = args.pop("assignment_id")
    if operation == "OPEN_SESSION" and not args:
        return engine.open_session(assignment_id, permission, now=command["now"])
    if operation == "SUBMIT" and set(args) == {"observation"}:
        return engine.submit(
            assignment_id, observation(args["observation"]), permission, now=command["now"]
        )
    if operation == "COMPLETE" and set(args) == {"risks"}:
        return engine.complete(
            assignment_id, tuple(tuple(v) for v in args["risks"]), permission, now=command["now"]
        )
    if operation == "ADJUDICATE" and set(args) == {"adjudication"}:
        a = dict(args["adjudication"])
        a["contributors"] = tuple(a["contributors"])
        if a["resolution"] is not None:
            a["resolution"] = observation(a["resolution"])
        return engine.adjudicate(assignment_id, Adjudication(**a), permission, now=command["now"])
    raise ValueError("unsupported governance operation/arguments")


class ConstructedGovernanceJournal:
    def __init__(
        self,
        authority: ConstructedAuthority,
        batch: Batch,
        reviewers: tuple[Reviewer, ...],
        *,
        expected_anchor: tuple[int, str | None],
    ):
        if type(authority) is not ConstructedAuthority or batch.classification != FIXTURE:
            raise ValueError(
                "constructed WP04 service/batch required; genuine persistence disabled"
            )
        if (
            type(expected_anchor) is not tuple
            or len(expected_anchor) != 2
            or type(expected_anchor[0]) is not int
            or expected_anchor[0] < 0
            or (expected_anchor[0] == 0) != (expected_anchor[1] is None)
        ):
            raise ValueError("explicit retained prefix required")
        self.authority, self.batch, self.reviewers = authority, batch, reviewers
        self.anchor = expected_anchor
        self.context = canonical(
            {"schema": SCHEMA, "batch": asdict(batch), "reviewers": [asdict(r) for r in reviewers]}
        )
        db = authority.db
        db.execute("CREATE TABLE IF NOT EXISTS governance_context(body TEXT NOT NULL)")
        db.execute(
            "CREATE TABLE IF NOT EXISTS governance_log(seq INTEGER PRIMARY KEY,"
            "request TEXT UNIQUE NOT NULL,body TEXT NOT NULL,result TEXT NOT NULL,"
            "previous TEXT,head TEXT NOT NULL)"
        )
        if [row[1] for row in db.execute("PRAGMA table_info(governance_log)")] != [
            "seq",
            "request",
            "body",
            "result",
            "previous",
            "head",
        ]:
            raise ValueError("governance journal schema changed")
        rows = db.execute("SELECT body FROM governance_context").fetchall()
        if not rows:
            if (
                expected_anchor != (0, None)
                or db.execute("SELECT count(*) FROM governance_log").fetchone()[0]
            ):
                raise ValueError("missing journal genesis; never reset history")
            db.execute("INSERT INTO governance_context VALUES(?)", (self.context,))
        self.restore()

    def restore(self, *, anchor: tuple[int, str | None] | None = None) -> ReviewLifecycle:
        db = self.authority.db
        if db.execute("SELECT body FROM governance_context").fetchall() != [(self.context,)]:
            raise ValueError("batch/roster/context substitution")
        rows = db.execute(
            "SELECT seq,request,body,result,previous,head FROM governance_log ORDER BY seq"
        ).fetchall()
        if len(rows) > 8192:
            raise ValueError("governance history exceeds declared envelope")
        expected = self.anchor if anchor is None else anchor
        if (len(rows), rows[-1][5] if rows else None) != expected:
            raise ValueError("retained governance prefix mismatch; explicit recovery required")
        engine = ReviewLifecycle(self.batch, self.reviewers)
        previous = None
        for index, (seq, request, body, result, parent, head) in enumerate(rows, 1):
            identity(request)
            binding = {
                "context": sha(self.context),
                "seq": seq,
                "request": request,
                "body": body,
                "result": result,
                "previous": parent,
            }
            if (
                seq != index
                or parent != previous
                or head != digest(binding)
                or apply_command(engine, closed_json(body)) != result
            ):
                raise ValueError("tampered governance command/result/history")
            commits = db.execute(
                "SELECT session,body,state,receipt,binding FROM tx WHERE id=?", (request,)
            ).fetchall()
            expected_payload = encode_payload(
                {
                    "classification": FIXTURE,
                    "real_human_evidence": False,
                    "governance_head": head,
                    "request": request,
                    "result": result,
                }
            )
            if (
                len(commits) != 1
                or commits[0][1] != expected_payload
                or commits[0][2] != "COMMITTED"
                or commits[0][4] != body
            ):
                raise ValueError("missing or substituted atomic authority journal parent")
            self.authority._historical_receipt(commits[0][0], request, commits[0][1], commits[0][3])
            previous = head
        return engine

    def perform(
        self,
        scope: ReviewScope,
        *,
        request_id: str,
        operation: str,
        arguments: dict,
        permission: Permission,
        interrupt: str | None = None,
    ) -> str:
        identity(request_id)
        if type(scope) is not ReviewScope or interrupt not in (
            None,
            "before_commit",
            "after_commit",
        ):
            raise ValueError("typed WP04 scope/known interruption point required")
        if (
            permission.actor != scope.actor
            or permission.environment != scope.context
            or permission.purpose != scope.purpose
        ):
            raise PermissionError("metadata permission/runtime principal context mismatch")
        command = {
            "operation": operation,
            "arguments": arguments,
            "permission": asdict(permission),
            "now": scope.now,
        }
        body = canonical(command)
        a = self.authority
        with a._transaction():
            session, grant = a._session(scope.session, scope.fence, **scope.current())
            if (
                grant["event"] not in dict(self.batch.events)
                or grant["event"] not in permission.events
            ):
                raise PermissionError("governance batch/event permission mismatch")
            engine = self.restore()
            prior = a.db.execute(
                "SELECT body,result FROM governance_log WHERE request=?", (request_id,)
            ).fetchone()
            if prior:
                if prior[0] != body:
                    raise ValueError("duplicate governance request substitution")
                tx = a.db.execute(
                    "SELECT body,state,receipt,binding FROM tx WHERE session=? AND id=?",
                    (scope.session, request_id),
                ).fetchone()
                if not tx or tx[1] != "COMMITTED" or tx[3] != body:
                    raise ValueError("governance/authority committed outcome mismatch")
                a._historical_receipt(scope.session, request_id, tx[0], tx[2])
                return prior[1]
            if session[4] >= grant["max_uses"]:
                raise PermissionError("governance permission quota exhausted")
            result = apply_command(engine, closed_json(body))
            # Every mutation must concern this exact WP04 session actor/event.
            target = (
                arguments["assignment"]
                if operation == "ASSIGN"
                else asdict(engine._assignment(arguments["assignment_id"]))
            )
            if target["reviewer_id"] != scope.actor or target["event"] != grant["event"]:
                raise PermissionError("governance operation session actor/event mismatch")
            seq, previous = self.anchor[0] + 1, self.anchor[1]
            head = digest(
                {
                    "context": sha(self.context),
                    "seq": seq,
                    "request": request_id,
                    "body": body,
                    "result": result,
                    "previous": previous,
                }
            )
            a.db.execute(
                "INSERT INTO governance_log VALUES(?,?,?,?,?,?)",
                (seq, request_id, body, result, previous, head),
            )
            payload = encode_payload(
                {
                    "classification": FIXTURE,
                    "real_human_evidence": False,
                    "governance_head": head,
                    "request": request_id,
                    "result": result,
                }
            )
            last = a.db.execute("SELECT seq,head FROM entries ORDER BY seq DESC LIMIT 1").fetchone()
            n, prev = (1, None) if last is None else (last[0] + 1, last[1])
            ledger_head = sha(canonical({"seq": n, "prev": prev, "body": payload}))
            receipt = Receipt(scope.session, request_id, n, sha(payload), ledger_head)
            a.db.execute(
                "INSERT INTO tx VALUES(?,?,?,'COMMITTED',?,?)",
                (scope.session, request_id, payload, canonical(asdict(receipt)), body),
            )
            a.db.execute("INSERT INTO entries VALUES(?,?,?,?)", (n, payload, prev, ledger_head))
            a.db.execute("UPDATE sessions SET uses=uses+1 WHERE id=?", (scope.session,))
            if interrupt == "before_commit":
                raise InterruptedError("constructed governance interruption before commit")
        if interrupt == "after_commit":
            raise InterruptedError(
                "constructed governance lost response; retained prefix unchanged"
            )
        self.anchor = seq, head
        return result

    def recover(self, scope: ReviewScope, *, request_id: str) -> tuple[int, str]:
        a = self.authority
        with a._transaction():
            a._session(scope.session, scope.fence, **scope.current())
            rows = a.db.execute(
                "SELECT seq,request,head,previous FROM governance_log ORDER BY seq"
            ).fetchall()
            if (
                len(rows) != self.anchor[0] + 1
                or rows[-1][1] != request_id
                or rows[-1][3] != self.anchor[1]
            ):
                raise ValueError("recovery requires exact next retained prefix/request")
            tx = a.db.execute(
                "SELECT body,state,receipt FROM tx WHERE session=? AND id=?",
                (scope.session, request_id),
            ).fetchone()
            if not tx or tx[1] != "COMMITTED":
                raise ValueError("missing exact authority commit")
            a._historical_receipt(scope.session, request_id, tx[0], tx[2])
            next_anchor = (rows[-1][0], rows[-1][2])
            self.restore(anchor=next_anchor)
        self.anchor = next_anchor
        return next_anchor
