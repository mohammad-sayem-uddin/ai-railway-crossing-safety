"""Versioned CONSTRUCTED_REVIEW_FIXTURE service, never a human identity provider.

Authority and knowledge changes share one injected SQLite transaction. Local
role strings/time/database are cooperative fixtures, not genuine credentials.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass

from railway_detection.annotation.human_review_store import ConstructedReviewStore
from railway_detection.safety.constructed_authority import (
    ConstructedAuthority,
    Receipt,
    canonical,
    decode_payload,
    encode_payload,
    identity,
    sha,
)

SCHEMA = "CONSTRUCTED_REVIEW_FIXTURE/1"


def _value(value):
    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)
    if isinstance(value, (tuple, list)):
        return [_value(x) for x in value]
    if isinstance(value, dict):
        return {k: _value(v) for k, v in value.items()}
    return value


@dataclass(frozen=True)
class ReviewScope:
    session: str
    fence: int
    actor: str
    resource: str
    context: str
    purpose: str
    now: int
    classification: str = "CONSTRUCTED_REVIEW_FIXTURE"

    def current(self):
        if self.classification != "CONSTRUCTED_REVIEW_FIXTURE":
            raise ValueError("mock identity cannot become genuine reviewer evidence")
        return dict(
            actor=self.actor,
            operation="REVIEW",
            resource=self.resource,
            context=self.context,
            purpose=self.purpose,
            now=self.now,
        )


def request_binding(scope, operation, event, args):
    return canonical(
        {
            "service": SCHEMA,
            "actor": scope.actor,
            "event": event,
            "operation": operation,
            "resource": scope.resource,
            "context": scope.context,
            "purpose": scope.purpose,
            "args_digest": sha(canonical(_value(args))),
        }
    )


class ConstructedReviewService:
    def __init__(self, authority, store, *, schema=SCHEMA):
        if (
            type(authority) is not ConstructedAuthority
            or type(store) is not ConstructedReviewStore
            or authority.db is not store.db
            or schema != SCHEMA
        ):
            raise ValueError("same-store versioned constructed service required")
        self.authority, self.store = authority, store
        db = authority.db
        db.execute("CREATE TABLE IF NOT EXISTS constructed_review_service(version TEXT NOT NULL)")
        versions = db.execute("SELECT version FROM constructed_review_service").fetchall()
        if not versions:
            if db.execute("SELECT count(*) FROM constructed_review_log").fetchone()[0]:
                raise ValueError(
                    "unversioned review history requires explicit migration; never reset"
                )
            db.execute("INSERT INTO constructed_review_service VALUES(?)", (SCHEMA,))
        elif versions != [(SCHEMA,)]:
            raise ValueError("unsupported persisted review service schema; never coerce")

    def execute(self, scope, operation, event, *, request_id, **args):
        if type(scope) is not ReviewScope:
            raise ValueError("typed constructed review scope required")
        identity(request_id)
        a, store = self.authority, self.store
        binding = request_binding(scope, operation, event, args)
        with a._transaction():
            if a.db.execute("SELECT version FROM constructed_review_service").fetchall() != [
                (SCHEMA,)
            ]:
                raise ValueError("review service schema changed")
            row, grant = a._session(scope.session, scope.fence, **scope.current())
            if event != grant["event"]:
                raise ValueError("authorized event mismatch; review aliases confer no authority")
            prior = a.db.execute(
                "SELECT body,state,receipt,binding FROM tx WHERE session=? AND id=?",
                (scope.session, request_id),
            ).fetchone()
            if prior and (prior[1] != "COMMITTED" or prior[3] != binding):
                raise ValueError("review authorization request substitution/unknown outcome")
            if not prior and row[4] >= grant["max_uses"]:
                raise ValueError("quota consumed before review write")
            review, next_anchor = store.execute_in_transaction(
                operation, scope.actor, event, request_id=request_id, **args
            )
            payload = {
                "classification": "CONSTRUCTED_REVIEW_FIXTURE",
                "schema": SCHEMA,
                "real_human_evidence": False,
                "review_commit": asdict(review),
            }
            body = encode_payload(payload)
            if prior:
                if prior[0] != body:
                    raise ValueError("review/authority journal mismatch")
                receipt = a._historical_receipt(scope.session, request_id, prior[0], prior[2])
            else:
                a.db.execute(
                    "INSERT INTO tx VALUES(?,?,?,'PREPARED',NULL,?)",
                    (scope.session, request_id, body, binding),
                )
                a.db.execute("UPDATE sessions SET uses=uses+1 WHERE id=?", (scope.session,))
                previous = a.db.execute(
                    "SELECT seq,head FROM entries ORDER BY seq DESC LIMIT 1"
                ).fetchone()
                seq, prev = (1, None) if previous is None else (previous[0] + 1, previous[1])
                head = sha(canonical({"seq": seq, "prev": prev, "body": body}))
                receipt = Receipt(scope.session, request_id, seq, sha(body), head)
                a.db.execute("INSERT INTO entries VALUES(?,?,?,?)", (seq, body, prev, head))
                a.db.execute(
                    "UPDATE tx SET state='COMMITTED',receipt=? WHERE session=? AND id=?",
                    (canonical(asdict(receipt)), scope.session, request_id),
                )
        store.anchor = next_anchor
        return payload | {"authority_receipt": asdict(receipt)}

    @staticmethod
    def recover_anchor(authority, scope, *, request_id, operation, event, args, previous_anchor):
        """Recover one lost response after an atomic commit, relative to a retained prefix.

        Caller must own the current permitted session/fence. Coherent replacement
        of both local journals is outside this cooperative profile.
        """
        if (
            type(scope) is not ReviewScope
            or type(previous_anchor) is not tuple
            or len(previous_anchor) != 2
            or type(previous_anchor[0]) is not int
        ):
            raise ValueError("typed scope and retained prefix required")
        with authority._transaction():
            _, grant = authority._session(scope.session, scope.fence, **scope.current())
            if event != grant["event"]:
                raise ValueError("recovery event mismatch")
            row = authority.db.execute(
                "SELECT body,state,receipt,binding FROM tx WHERE session=? AND id=?",
                (scope.session, request_id),
            ).fetchone()
            if (
                not row
                or row[1] != "COMMITTED"
                or row[3] != request_binding(scope, operation, event, args)
            ):
                raise ValueError("no exact committed review outcome")
            authority._historical_receipt(scope.session, request_id, row[0], row[2])
            review = decode_payload(row[0])["payload"]["review_commit"]
            rows = authority.db.execute(
                "SELECT seq,request,previous,head FROM constructed_review_log ORDER BY seq"
            ).fetchall()
            if len(rows) != previous_anchor[0] + 1 or rows[-1] != (
                review["count"],
                request_id,
                previous_anchor[1],
                review["head"],
            ):
                raise ValueError(
                    "lost-response recovery requires exact next prefix, not arbitrary head"
                )
            if previous_anchor[0] and rows[-2][3] != previous_anchor[1]:
                raise ValueError("retained review prefix mismatch")
            return review["count"], review["head"]
