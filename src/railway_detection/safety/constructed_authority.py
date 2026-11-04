"""Cooperative-local CONSTRUCTED_ONLY authority/transaction service.

Caller injects a SQLite connection to a constructed test store. No connection,
resource path, real identity, signature, media or model opener is created here.
SQLite atomic durability is not independent/OS-protected authority storage.
"""

from __future__ import annotations

import hashlib
import json
import unicodedata
from contextlib import contextmanager
from dataclasses import asdict, dataclass

PROFILE = "CONSTRUCTED_ONLY"
OPERATIONS = ("READ", "PROBE", "HASH", "MODEL", "CACHE", "REVIEW", "PUBLISH", "EVALUATE")


def _strings(value):
    if type(value) is str:
        if unicodedata.normalize("NFC", value) != value or any(
            unicodedata.category(c) in ("Cc", "Cs") for c in value
        ):
            raise ValueError("noncanonical/control/surrogate Unicode")
    elif type(value) is dict:
        for k, v in value.items():
            if type(k) is not str:
                raise ValueError("string object keys required")
            _strings(k)
            _strings(v)
    elif type(value) in (tuple, list):
        for x in value:
            _strings(x)
    elif value is not None and type(value) not in (int, bool):
        raise ValueError("floats/unsupported codec types forbidden")


def canonical(value):
    _strings(value)
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _pairs(pairs):
    result = {}
    for k, v in pairs:
        if k in result:
            raise ValueError("duplicate JSON key")
        result[k] = v
    return result


def encode_payload(payload):
    return canonical({"schema": PROFILE, "kind": "CONSTRUCTED_PAYLOAD", "payload": payload})


def decode_payload(body):
    def reject(_):
        raise ValueError("noninteger codec number forbidden")

    if type(body) is not str:
        raise ValueError("canonical UTF8 JSON text required")
    value = json.loads(body, object_pairs_hook=_pairs, parse_float=reject, parse_constant=reject)
    if (
        type(value) is not dict
        or set(value) != {"schema", "kind", "payload"}
        or value["schema"] != PROFILE
        or value["kind"] != "CONSTRUCTED_PAYLOAD"
        or canonical(value) != body
    ):
        raise ValueError("unknown/noncanonical envelope")
    return value


def sha(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def identity(value):
    if type(value) is not str or not value.startswith("synthetic:"):
        raise ValueError("synthetic fixture identity required")


def exact_time(value):
    if type(value) is not int or value < 0:
        raise ValueError("available exact nonnegative authority clock required")


@dataclass(frozen=True)
class Grant:
    grant_id: str
    actor: str
    event: str
    operations: tuple[str, ...]
    resources: tuple[str, ...]
    purpose: str
    context: str
    valid_from: int
    expires: int
    max_uses: int = 1


@dataclass(frozen=True)
class Receipt:
    session: str
    transaction: str
    sequence: int
    body_digest: str
    head: str


class ConstructedAuthority:
    def __init__(self, connection, *, appointments, expected_context, profile):
        if profile != PROFILE or type(expected_context) is not str or not expected_context:
            raise ValueError("explicit constructed service/profile/context required")
        self.db = connection
        self.context = expected_context
        self.roles: dict[str, tuple[str, ...]] = {}
        for actor, roles in appointments:
            identity(actor)
            if (
                actor in self.roles
                or not set(roles) <= {"ISSUER", "REVIEWER", "PROMOTER"}
                or ("ISSUER" in roles and "REVIEWER" in roles)
            ):
                raise ValueError("separate fixture appointment roles required")
            self.roles[actor] = tuple(roles)
        self.db.isolation_level = None
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS grants(id TEXT PRIMARY KEY, body TEXT NOT NULL,
          revoked INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS sessions(id TEXT PRIMARY KEY, grant_id TEXT UNIQUE NOT NULL,
          actor TEXT NOT NULL, event TEXT NOT NULL, initial TEXT NOT NULL, fence INTEGER NOT NULL,
          state TEXT NOT NULL, uses INTEGER NOT NULL, UNIQUE(actor,event));
        CREATE TABLE IF NOT EXISTS tx(session TEXT NOT NULL,id TEXT NOT NULL,body TEXT NOT NULL,
          state TEXT NOT NULL,receipt TEXT,binding TEXT NOT NULL,PRIMARY KEY(session,id));
        CREATE TABLE IF NOT EXISTS entries(seq INTEGER PRIMARY KEY,body TEXT NOT NULL,
          prev TEXT,head TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS metadata(id TEXT PRIMARY KEY,value INTEGER NOT NULL);
        INSERT OR IGNORE INTO metadata VALUES('clock',0);
        CREATE TABLE IF NOT EXISTS batches(id TEXT PRIMARY KEY,body TEXT NOT NULL,
          receipt TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS objects(id TEXT PRIMARY KEY,body TEXT NOT NULL);
        """)

    @contextmanager
    def _transaction(self):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            yield
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def _role(self, actor, role):
        if role not in self.roles.get(actor, ()):
            raise ValueError("role unavailable or self elevation denied")

    def issue(self, issuer, grant):
        self._role(issuer, "ISSUER")
        if type(grant) is not Grant:
            raise ValueError("typed constructed grant required")
        for x in (grant.grant_id, grant.actor, grant.event, *grant.resources):
            identity(x)
        if grant.actor not in self.roles or grant.context != self.context or not grant.purpose:
            raise ValueError("actor/purpose/expected runtime mismatch")
        for numeric in (grant.valid_from, grant.expires, grant.max_uses):
            exact_time(numeric)
        if (
            grant.expires <= grant.valid_from
            or grant.max_uses < 1
            or not grant.operations
            or len(set(grant.operations)) != len(grant.operations)
            or not set(grant.operations) <= set(OPERATIONS)
            or not grant.resources
        ):
            raise ValueError("invalid exact operation/time/quota scope")
        self.db.execute(
            "INSERT INTO grants VALUES(?,?,0)", (grant.grant_id, canonical(asdict(grant)))
        )

    def _check(self, grant_id, *, actor, operation, resource, context, now):
        exact_time(now)
        row = self.db.execute("SELECT body,revoked FROM grants WHERE id=?", (grant_id,)).fetchone()
        if row is None or row[1]:
            raise ValueError("missing/revoked authority")
        grant = json.loads(row[0])
        old_clock = self.db.execute("SELECT value FROM metadata WHERE id='clock'").fetchone()[0]
        if (
            now < old_clock
            or not grant["valid_from"] <= now < grant["expires"]
            or context != self.context
            or grant["context"] != context
            or actor != grant["actor"]
            or actor not in self.roles
            or operation not in grant["operations"]
            or resource not in grant["resources"]
        ):
            raise ValueError("authority clock/scope/runtime mismatch")
        self.db.execute("UPDATE metadata SET value=? WHERE id='clock'", (now,))
        return grant

    def reserve(self, grant_id, *, session, actor, initial_body, operation, resource, context, now):
        identity(session)
        decode_payload(initial_body)
        with self._transaction():
            g = self._check(
                grant_id,
                actor=actor,
                operation=operation,
                resource=resource,
                context=context,
                now=now,
            )
            row = self.db.execute(
                "SELECT grant_id,actor,initial,fence,state FROM sessions WHERE id=?", (session,)
            ).fetchone()
            if row:
                if row[:3] != (grant_id, actor, initial_body) or row[4] != "ACTIVE":
                    raise ValueError("reservation replay/conflicting initialization")
                return row[3]
            self.db.execute(
                "INSERT INTO sessions VALUES(?,?,?,?,?,1,?,0)",
                (session, grant_id, actor, g["event"], initial_body, "ACTIVE"),
            )
            return 1

    def _session(self, session, fence, *, actor, operation, resource, context, now):
        row = self.db.execute(
            "SELECT grant_id,actor,fence,state,uses FROM sessions WHERE id=?", (session,)
        ).fetchone()
        if row is None or type(fence) is not int or row[1:4] != (actor, fence, "ACTIVE"):
            raise ValueError("stale fence/owner/terminal session")
        grant = self._check(
            row[0], actor=actor, operation=operation, resource=resource, context=context, now=now
        )
        return row, grant

    def prepare(
        self, session, transaction, body, *, fence, actor, operation, resource, context, now
    ):
        identity(transaction)
        decode_payload(body)
        with self._transaction():
            row, g = self._session(
                session,
                fence,
                actor=actor,
                operation=operation,
                resource=resource,
                context=context,
                now=now,
            )
            existing = self.db.execute(
                "SELECT body,state,binding FROM tx WHERE session=? AND id=?", (session, transaction)
            ).fetchone()
            binding = canonical({"operation": operation, "resource": resource, "context": context})
            if existing:
                if existing[0] != body or existing[2] != binding:
                    raise ValueError("transaction payload substitution")
                return existing[1]
            if row[4] >= g["max_uses"]:
                raise ValueError("quota consumed")
            self.db.execute(
                "INSERT INTO tx VALUES(?,?,?,'PREPARED',NULL,?)",
                (session, transaction, body, binding),
            )
            self.db.execute("UPDATE sessions SET uses=uses+1 WHERE id=?", (session,))
            return "PREPARED"

    def commit(self, session, transaction, *, fence, actor, operation, resource, context, now):
        with self._transaction():
            existing = self.db.execute(
                "SELECT body,state,receipt,binding FROM tx WHERE session=? AND id=?",
                (session, transaction),
            ).fetchone()
            if existing is None:
                raise ValueError("no prepared body")
            if existing[3] != canonical(
                {"operation": operation, "resource": resource, "context": context}
            ):
                raise ValueError("transaction execution binding changed")
            if existing[1] == "COMMITTED":
                # Historical receipt only; no repeated resource operation or quota.
                stored_actor = self.db.execute(
                    "SELECT actor FROM sessions WHERE id=?", (session,)
                ).fetchone()[0]
                if actor != stored_actor:
                    raise ValueError("receipt owner mismatch")
                return Receipt(**json.loads(existing[2]))
            self._session(
                session,
                fence,
                actor=actor,
                operation=operation,
                resource=resource,
                context=context,
                now=now,
            )
            if existing[1] != "PREPARED":
                raise ValueError("unknown/aborted transaction cannot commit")
            previous = self.db.execute(
                "SELECT seq,head FROM entries ORDER BY seq DESC LIMIT 1"
            ).fetchone()
            seq, prev = (1, None) if previous is None else (previous[0] + 1, previous[1])
            head = sha(canonical({"seq": seq, "prev": prev, "body": existing[0]}))
            receipt = Receipt(session, transaction, seq, sha(existing[0]), head)
            self.db.execute("INSERT INTO entries VALUES(?,?,?,?)", (seq, existing[0], prev, head))
            self.db.execute(
                "UPDATE tx SET state='COMMITTED',receipt=? WHERE session=? AND id=?",
                (canonical(asdict(receipt)), session, transaction),
            )
            return receipt

    def revoke(self, issuer, grant_id):
        self._role(issuer, "ISSUER")
        with self._transaction():
            self.db.execute("UPDATE grants SET revoked=1 WHERE id=?", (grant_id,))
            self.db.execute(
                "UPDATE tx SET state='ABORTED' WHERE state='PREPARED' AND session IN "
                "(SELECT id FROM sessions WHERE grant_id=?)",
                (grant_id,),
            )
            self.db.execute(
                "UPDATE sessions SET state='ABORTED' WHERE grant_id=? AND state='ACTIVE'",
                (grant_id,),
            )

    def recover(self, session, *, actor):
        with self._transaction():
            row = self.db.execute(
                "SELECT actor,fence,state FROM sessions WHERE id=?", (session,)
            ).fetchone()
            if row is None or row[0] != actor or row[2] != "ACTIVE":
                raise ValueError("same permitted principal/session recovery only")
            self.db.execute("UPDATE sessions SET fence=fence+1 WHERE id=?", (session,))
            return row[1] + 1

    def mark_unknown(self, session, transaction):
        self.db.execute(
            "UPDATE tx SET state='UNKNOWN_EXTERNAL' WHERE session=? AND id=? AND state='PREPARED'",
            (session, transaction),
        )

    def finalize(self, session, *, actor):
        with self._transaction():
            row = self.db.execute(
                "SELECT actor,state FROM sessions WHERE id=?", (session,)
            ).fetchone()
            if row != (actor, "ACTIVE"):
                raise ValueError("wrong owner/terminal session")
            if self.db.execute(
                "SELECT 1 FROM tx WHERE session=? AND state IN ('PREPARED','UNKNOWN_EXTERNAL')",
                (session,),
            ).fetchone():
                raise ValueError("BUSY unresolved transaction")
            self.db.execute("UPDATE sessions SET state='COMPLETED' WHERE id=?", (session,))

    def audit(self, *, expected_head, expected_count):
        if type(expected_count) is not int or expected_count < 0:
            raise ValueError("independent anchor required")
        rows = self.db.execute("SELECT seq,body,prev,head FROM entries ORDER BY seq").fetchall()
        previous = None
        for n, (seq, body, prev, head) in enumerate(rows, 1):
            decode_payload(body)
            if (
                seq != n
                or prev != previous
                or head != sha(canonical({"seq": seq, "prev": prev, "body": body}))
            ):
                raise ValueError("ledger corruption")
            committed = self.db.execute(
                "SELECT body,receipt FROM tx WHERE state='COMMITTED'"
            ).fetchall()
            matching = [
                (b, json.loads(rc)) for b, rc in committed if json.loads(rc)["sequence"] == seq
            ]
            if (
                len(matching) != 1
                or matching[0][0] != body
                or matching[0][1]["head"] != head
                or matching[0][1]["body_digest"] != sha(body)
            ):
                raise ValueError("missing or altered acknowledged journal/body")
            previous = head
        if len(rows) != expected_count or previous != expected_head:
            raise ValueError("independent anchor mismatch; quarantine")
        return True

    def publish_constructed_batch(self, *, promoter, batch_id, objects, approved_digest):
        """Atomic fixture publication only, never an active GT adapter or live grant."""
        self._role(promoter, "PROMOTER")
        identity(batch_id)
        if (
            type(objects) is not tuple
            or not objects
            or len({k for k, _ in objects}) != len(objects)
        ):
            raise ValueError("nonempty unique qualified objects required")
        for key, body in objects:
            identity(key)
            decode_payload(body)
            if len(key.split(":")) < 4:
                raise ValueError("cohort-qualified object key required")
        payload = canonical(objects)
        if sha(payload) != approved_digest:
            raise ValueError("exact independently retained constructed batch approval required")
        receipt = sha(canonical({"batch": batch_id, "digest": approved_digest, "profile": PROFILE}))
        with self._transaction():
            existing = self.db.execute(
                "SELECT body,receipt FROM batches WHERE id=?", (batch_id,)
            ).fetchone()
            if existing:
                if existing[0] != payload:
                    raise ValueError("batch identity substitution")
                return existing[1]
            for key, body in objects:
                self.db.execute("INSERT INTO objects VALUES(?,?)", (key, body))
            self.db.execute("INSERT INTO batches VALUES(?,?,?)", (batch_id, payload, receipt))
        return receipt
