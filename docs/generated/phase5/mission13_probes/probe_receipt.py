import json, pathlib, tempfile, sys, copy
sys.dont_write_bytecode=True
from datetime import datetime, UTC, timedelta
from railway_detection.evaluation import governance as g
from railway_detection.annotation.receipt import receipt_body_sha256
def run(label, mutate=None, now=None, live_override=None):
    with tempfile.TemporaryDirectory() as t:
        root=pathlib.Path(t); p=root/g.PROMOTION_RECEIPT_RELATIVE; p.parent.mkdir(parents=True,exist_ok=True)
        rec={"schema_version":g.PROMOTION_RECEIPT_SCHEMA,"produced_by":g.PROMOTION_RECEIPT_PRODUCER,
             "produced_at_utc":"2026-10-01T00:00:00Z","verdict":{"ready":True,"blocker_count":0},
             "media_hashes_verified_live":True,"stage":"stage-2.1",
             "review_record_sha256":{"train_events/event_001_review.json":"a"*64},
             "inputs":{"allowlist_sha256":"b"*64,"inventory_sha256":"c"*64}}
        if mutate: mutate(rec)
        rec["receipt_sha256"]=receipt_body_sha256(rec) if not rec.pop("_badhash",False) else "0"*64
        p.write_text(json.dumps(rec))
        live={"allowlist_sha256":"b"*64,"inventory_sha256":"c"*64}
        if live_override: live=live_override
        try:
            g.verify_promotion_receipt(root, review_record_sha256={"train_events/event_001_review.json":"a"*64}, live_inputs=live, now=now)
            print(f"{label}: ACCEPTED")
        except g.GovernanceError as e: print(f"{label}: REJECTED {e.code}: {str(e.detail)[:90]}")
NOW=datetime(2026,11,2,tzinfo=UTC)
run("R0 hand-computed receipt, correct live hashes (no CLI ever run)", now=NOW)
run("R1 invalid self-hash", lambda r:r.__setitem__("_badhash",True), now=NOW)
run("R2 wrong review-record hash", lambda r:r["review_record_sha256"].__setitem__("train_events/event_001_review.json","d"*64), now=NOW)
run("R3 wrong input (protocol/allowlist) binding", now=NOW, live_override={"allowlist_sha256":"e"*64,"inventory_sha256":"c"*64})
run("R4 wrong producer", lambda r:r.__setitem__("produced_by","evil"), now=NOW)
run("R5 verdict not ready", lambda r:r["verdict"].__setitem__("ready",False), now=NOW)
run("R6 future-dated", lambda r:r.__setitem__("produced_at_utc","2027-01-01T00:00:00Z"), now=NOW)
run("R7 ancient (5y old) receipt, expiry?", lambda r:r.__setitem__("produced_at_utc","2021-01-01T00:00:00Z"), now=NOW)
run("R8 'revoked':true extra field (revocation mechanism?)", lambda r:r.__setitem__("revoked",True), now=NOW)
