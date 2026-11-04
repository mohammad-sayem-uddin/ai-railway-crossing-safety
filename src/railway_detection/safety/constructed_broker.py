"""Point-of-use constructed byte broker, sharing the fixture authority transaction.

Accepts exact immutable bytes explicitly supplied as a constructed resource.
No path, arbitrary callback, model/cache loader, network or live token route.
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass

from railway_detection.safety.constructed_authority import (
    PROFILE,
    ConstructedAuthority,
    Receipt,
    canonical,
    decode_payload,
    encode_payload,
    identity,
    sha,
)


@dataclass(frozen=True)
class ConstructedResource:
    resource_id: str
    version_id: str
    contents: bytes
    provenance: str = "CONSTRUCTED_IN_MEMORY"


def resource_digest(resource: ConstructedResource):
    if type(resource) is not ConstructedResource or type(resource.contents) is not bytes:
        raise ValueError("explicit immutable constructed byte resource required")
    identity(resource.resource_id)
    identity(resource.version_id)
    if resource.provenance != "CONSTRUCTED_IN_MEMORY" or len(resource.contents) > 1_048_576:
        raise ValueError("unsupported resource origin/size; no live loader")
    return sha(
        canonical(
            {
                "id": resource.resource_id,
                "version": resource.version_id,
                "content_sha256": hashlib.sha256(resource.contents).hexdigest(),
            }
        )
    )


class ConstructedResourceBroker:
    def __init__(self, authority: ConstructedAuthority, *, resources, expected_registry_digest):
        if type(authority) is not ConstructedAuthority or type(resources) is not tuple:
            raise ValueError("exact constructed authority and immutable resource registry required")
        self._resources: dict[str, tuple[bytes, str]] = {}
        for resource in resources:
            resource_digest(resource)
            if resource.resource_id in self._resources:
                raise ValueError("duplicate constructed resource identity")
            # Copy immutable bytes and the fixture-time digest; READ must not
            # implicitly execute the separately scoped HASH operation.
            self._resources[resource.resource_id] = resource.contents, resource_digest(resource)
        registry = canonical(tuple((r.resource_id, resource_digest(r)) for r in resources))
        if sha(registry) != expected_registry_digest:
            raise ValueError("independent constructed resource registry binding mismatch")
        self.authority = authority

    def use(
        self,
        session,
        transaction,
        *,
        fence,
        actor,
        operation,
        resource,
        context,
        purpose,
        now,
        expected_resource_digest,
    ):
        identity(transaction)
        # No model/inference/evaluation or protected-operation implementation is present.
        if operation not in {"READ", "PROBE", "HASH"}:
            raise ValueError("constructed broker implements only explicit READ/PROBE/HASH")
        a = self.authority
        with a._transaction():
            row, grant = a._session(
                session,
                fence,
                actor=actor,
                operation=operation,
                resource=resource,
                context=context,
                purpose=purpose,
                now=now,
            )
            source = self._resources.get(resource)
            if source is None or source[1] != expected_resource_digest:
                raise ValueError("exact resource version/content mismatch before use")
            binding = canonical(
                {
                    "broker": PROFILE,
                    "resource_digest": expected_resource_digest,
                    "operation": operation,
                    "resource": resource,
                    "context": context,
                    "purpose": purpose,
                }
            )
            prior = a.db.execute(
                "SELECT body,state,receipt,binding FROM tx WHERE session=? AND id=?",
                (session, transaction),
            ).fetchone()
            if prior:
                if prior[1] != "COMMITTED" or prior[3] != binding:
                    raise ValueError("broker request substitution/unknown outcome")
                receipt = a._historical_receipt(session, transaction, prior[0], prior[2])
                return decode_payload(prior[0])["payload"], receipt
            if row[4] >= grant["max_uses"]:
                raise ValueError("quota consumed before resource use")
            # This is the use boundary: permission and the exact immutable object
            # are checked within the same authority transaction before touching bytes.
            result: str | int
            if operation == "READ":
                result = source[0].hex()
            elif operation == "PROBE":
                result = len(source[0])
            else:
                result = hashlib.sha256(source[0]).hexdigest()
            payload = {
                "classification": PROFILE,
                "operation": operation,
                "resource_digest": expected_resource_digest,
                "result": result,
            }
            body = encode_payload(payload)
            a.db.execute(
                "INSERT INTO tx VALUES(?,?,?,'PREPARED',NULL,?)",
                (session, transaction, body, binding),
            )
            a.db.execute("UPDATE sessions SET uses=uses+1 WHERE id=?", (session,))
            previous = a.db.execute(
                "SELECT seq,head FROM entries ORDER BY seq DESC LIMIT 1"
            ).fetchone()
            seq, prev = (1, None) if previous is None else (previous[0] + 1, previous[1])
            head = sha(canonical({"seq": seq, "prev": prev, "body": body}))
            receipt = Receipt(session, transaction, seq, sha(body), head)
            a.db.execute("INSERT INTO entries VALUES(?,?,?,?)", (seq, body, prev, head))
            a.db.execute(
                "UPDATE tx SET state='COMMITTED',receipt=? WHERE session=? AND id=?",
                (canonical(asdict(receipt)), session, transaction),
            )
        return payload, receipt
