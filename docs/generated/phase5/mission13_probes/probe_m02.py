"""Mission 13 synthetic-only M-02 probes. Runs only against temp files. No repo data touched."""
import json, hashlib, sys, tempfile, pathlib, traceback
sys.dont_write_bytecode = True
from railway_detection.evaluation import evaluation_runner as er
from railway_detection.evaluation import input_contracts as ic
from railway_detection.evaluation.input_contracts import EvidenceClassification as EC

R = er.Phase12EvaluationRunner()
results = []
def rec(name, expected, actual):
    results.append((name, expected, actual)); print(f"{name} | expected={expected} | actual={actual}")

def code_of(fn):
    try:
        fn(); return "NO_EXCEPTION"
    except er.EvaluationRefused as e: return f"EvaluationRefused:{e.code}"
    except Exception as e: return f"{type(e).__name__}:{str(e)[:90]}"

# tripwires: any source read / hash / producer call is recorded
trips = []
orig_read = ic._read_source_bytes_and_hash
def tw_read(path):
    trips.append(("source_read", str(path))); return orig_read(path)
ic._read_source_bytes_and_hash = tw_read
er.load_evaluation_input_manifest.__globals__  # same module namespace as er
import railway_detection.evaluation.replay_producer as rp
orig_prod = rp.RealEventReplayProducer.produce
def tw_prod(self, root): trips.append(("producer", str(root))); return orig_prod(self, root)
rp.RealEventReplayProducer.produce = tw_prod

def make_manifest(tmp, classification):
    ev = {}
    parts = {"train": ["train_events/a"], "val": ["train_events/b"], "test": ["train_events/c"]}
    events = []
    for role, ids in parts.items():
        for eid in ids:
            p = tmp / f"{eid.replace('/','_')}.json"
            body = json.dumps({"synthetic": True}).encode()
            p.write_bytes(body)
            events.append({"event_id": eid, "cohort": "train_events", "split_role": role,
                           "source_path": p.name, "source_sha256": hashlib.sha256(body).hexdigest()})
    m = {"schema_version": "phase12-evaluation-inputs/1", "evidence_classification": classification,
         "partitions": parts, "events": events,
         "camera_scope_by_event": {e["event_id"]: "front_only" for e in events}}
    mp = tmp / "manifest.json"; mp.write_text(json.dumps(m)); return mp

with tempfile.TemporaryDirectory() as t:
    tmp = pathlib.Path(t)
    mp_real = make_manifest(tmp, "real")
    digest = hashlib.sha256(mp_real.read_bytes()).hexdigest()
    permit = er._OfficialPermit(authorization_sha256="a"*64, attestation_level="X", manifest_sha256=digest)

    # 1 forged permit via public run() with REAL
    trips.clear()
    rec("1 forged _OfficialPermit -> run(REAL)", "refused", code_of(lambda: R.run(evidence_classification=EC.REAL, _permit=permit)))
    # 2 forged _VerifiedOfficialAuthorization (own token) via public run()/run_from_manifest
    ctx = er._VerifiedOfficialAuthorization(token=object(), authorization_sha256="a"*64, attestation_level="X", manifest_sha256=digest)
    rec("2a forged _VerifiedOfficialAuthorization -> run()", "refused", code_of(lambda: R.run(evidence_classification=EC.REAL, _authorization_context=ctx)))
    rec("2b forged ctx -> run_from_manifest()", "refused", code_of(lambda: R.run_from_manifest(manifest_path=mp_real, ground_truth=[], simulation_results={}, evidence_classification=EC.REAL, _authorization_context=ctx)))
    # 2c private core with forged token
    rec("2c forged ctx (wrong token) -> _run_from_manifest_verified()", "refused", code_of(lambda: R._run_from_manifest_verified(manifest_path=mp_real, ground_truth=[], simulation_results={}, _authorization_context=ctx)))
    # 3 matching digest alone via run_from_manifest REAL
    trips.clear()
    rec("3 matching manifest digest/permit -> run_from_manifest(REAL)", "refused", code_of(lambda: R.run_from_manifest(manifest_path=mp_real, ground_truth=[], simulation_results={}, evidence_classification=EC.REAL, _permit=permit)))
    rec("3-trips", "[]", str(trips))
    # 5/6 REAL evidence through public run / run_from_manifest (explicit classification)
    trips.clear()
    rec("5 REAL via run()", "refused", code_of(lambda: R.run(evidence_classification=EC.REAL)))
    rec("6 REAL via run_from_manifest() (explicit kwarg)", "refused", code_of(lambda: R.run_from_manifest(manifest_path=mp_real, ground_truth=[], simulation_results={}, evidence_classification=EC.REAL)))
    rec("6-trips", "[]", str(trips))
    # 6b REAL *manifest* via run_from_manifest WITHOUT classification kwarg (default SYNTHETIC)
    trips.clear()
    out = code_of(lambda: R.run_from_manifest(manifest_path=mp_real, ground_truth=[], simulation_results={}))
    rec("6b REAL manifest, kwarg omitted -> run_from_manifest()", "refused before ANY source read", out)
    rec("6b-trips (source reads before refusal)", "[]", str([(a, pathlib.Path(b).name) for a, b in trips]))
    # 6c caller says SYNTHETIC but manifest is REAL
    trips.clear()
    out = code_of(lambda: R.run_from_manifest(manifest_path=mp_real, ground_truth=[], simulation_results={}, evidence_classification=EC.SYNTHETIC))
    rec("6c kwarg=SYNTHETIC, manifest=real", "refused before source read", out)
    rec("6c-trips", "[]", str([(a, pathlib.Path(b).name) for a, b in trips]))
    # 7 mislabel: permit applied to synthetic
    mp_syn = make_manifest(tmp, "synthetic")
    rec("7 permit on synthetic -> run_from_manifest", "refused", code_of(lambda: R.run_from_manifest(manifest_path=mp_syn, ground_truth=[], simulation_results={}, _permit=permit)))
    # 12 marker: runner-produced results on synthetic path -> official flag False
    # 12b direct construction of provenance object
    from railway_detection.evaluation.output_contracts import EvaluationProvenance
    prov = EvaluationProvenance(schema_version="x", phase="12", evidence_classification=EC.REAL, input_manifest_sha256="", source_sha256_by_event={}, frozen_config_sha256="", decision_policy_sha256="", checkpoint_sha256={}, seed=1, git_commit=None, official_authorization_verified=True)
    rec("12b EvaluationProvenance(official_authorization_verified=True) constructible", "(ideal) not forgeable", f"constructible={prov.official_authorization_verified}")
    # residual: same-process private-name access
    tok = er._OFFICIAL_CONTEXT_TOKEN
    ctx2 = er._VerifiedOfficialAuthorization(token=tok, authorization_sha256="b"*64, attestation_level="FORGED", manifest_sha256=digest)
    trips.clear()
    # fabricate minimal test evidence is heavy; show acceptance of the gate by observing the failure moves PAST the authorization check
    out = code_of(lambda: R._run_from_manifest_verified(manifest_path=mp_real, ground_truth=[], simulation_results={}, _authorization_context=ctx2))
    rec("R1 residual: private token imported by name + private method", "(same-process limitation) gate passes -> later refusal", out)
print("DONE")
