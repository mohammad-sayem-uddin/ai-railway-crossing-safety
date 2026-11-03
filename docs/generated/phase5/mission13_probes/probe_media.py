"""Mission 13 synthetic-only media-guard probes. Fake (non-existent) repo paths + temp files only."""
import os, sys, json, hashlib, pathlib, tempfile
sys.dont_write_bytecode = True
from railway_detection.safety import media_guard as mg
from railway_detection.evaluation import input_contracts as ic
REPO = mg.REAL_REPO_ROOT

def code(fn):
    try: fn(); return "ALLOWED(no exception)"
    except mg.MediaAccessAuthorizationError as e: return f"DENIED:{e.code}"
    except Exception as e: return f"{type(e).__name__}:{str(e)[:80]}"
def rec(n, exp, act): print(f"{n} | expected={exp} | actual={act}")

fake_mov = REPO/"data/raw/layer_b/train_events/__m13_fake__/front.mov"      # does not exist
fake_jpg = REPO/"data/raw/vision/v1/__m13_fake__/x.jpg"                      # does not exist
with tempfile.TemporaryDirectory() as t:
    tmp = pathlib.Path(t).resolve()
    (tmp/"a.png").write_bytes(b"x"); (tmp/"a.mp4").write_bytes(b"x")
    rec("A1 synthetic tmp image", "ALLOWED", code(lambda: mg.require_media_authorization(tmp/"a.png","READ_RAW_MEDIA")))
    rec("A2 synthetic tmp video", "ALLOWED", code(lambda: mg.require_media_authorization(tmp/"a.mp4","INFERENCE")))
    rec("B1 repo video (fake path)", "DENIED", code(lambda: mg.require_media_authorization(fake_mov,"READ_RAW_MEDIA")))
    rec("B2 repo image (fake path)", "DENIED", code(lambda: mg.require_media_authorization(fake_jpg,"READ_RAW_MEDIA")))
    sysmedia = pathlib.Path("/System/Library/Sounds/Basso.aiff")
    if sysmedia.exists():
        rec("C1 non-temp, non-repo existing media (system sound; guard does not open it)", "DENIED", code(lambda: mg.require_media_authorization(sysmedia,"READ_RAW_MEDIA")))
    rec("C2 non-temp, non-repo ABSENT media", "ALLOWED by design (no bytes)", code(lambda: mg.require_media_authorization(pathlib.Path.home()/"__m13_absent__.mov","READ_RAW_MEDIA")))
    # symlinks
    l1 = tmp/"link.mov"; l1.symlink_to(fake_mov)
    rec("D1 tmp symlink with media suffix -> repo media", "DENIED", code(lambda: mg.require_media_authorization(l1,"READ_RAW_MEDIA")))
    l2 = tmp/"link.dat"; l2.symlink_to(fake_mov)
    rec("D2 tmp symlink with NON-media suffix -> repo media", "DENIED (ideal)", code(lambda: mg.require_media_authorization(l2,"READ_RAW_MEDIA")))
    l3 = tmp/"link"; l3.symlink_to(fake_mov)
    rec("D3 tmp symlink with no suffix -> repo media", "DENIED (ideal)", code(lambda: mg.require_media_authorization(l3,"READ_RAW_MEDIA")))
    # traversal
    trav = tmp/".."/".."/".."/".."/".."/".."/".."/".."/".."/".."/(str(fake_mov).lstrip("/"))
    rec("E1 ../ traversal into repo", "DENIED", code(lambda: mg.require_media_authorization(trav,"READ_RAW_MEDIA")))
    cwd=os.getcwd(); os.chdir(REPO)
    try: rec("E2 relative repo path", "DENIED", code(lambda: mg.require_media_authorization(pathlib.Path("data/raw/layer_b/train_events/__m13_fake__/front.mov"),"READ_RAW_MEDIA")))
    finally: os.chdir(cwd)
    rec("E3 '~' expansion/odd normalization (//, ./)", "DENIED", code(lambda: mg.require_media_authorization(str(fake_mov).replace("/data/","//data/./"),"READ_RAW_MEDIA")))
    # env overrides
    for k in ("AUTH_MEDIA_ACCESS","RAILWAY_ALLOW_MEDIA","ALLOW_RAW_MEDIA","MEDIA_AUTH","PYTEST_CURRENT_TEST","CI"):
        os.environ[k]="1"
    rec("F1 env overrides set", "DENIED", code(lambda: mg.require_media_authorization(fake_mov,"READ_RAW_MEDIA")))
    for k in ("AUTH_MEDIA_ACCESS","RAILWAY_ALLOW_MEDIA","ALLOW_RAW_MEDIA","MEDIA_AUTH","PYTEST_CURRENT_TEST","CI"): os.environ.pop(k,None)
    # repo_root override hand-made auth in tmp
    rec("F2 repo_root override to tmp for in-repo path", "DENIED", code(lambda: mg.require_media_authorization(fake_mov,"READ_RAW_MEDIA",repo_root=tmp)))
    # suffix coverage gaps (pure function; fake repo paths)
    for suf in (".m2ts",".ts",".3gp",".wmv",".flv",".gif",".heic",".mxf",".dng",".MOV",".mov.bak",".bin",""):
        p = REPO/f"data/raw/layer_b/train_events/__m13_fake__/clip{suf}"
        rec(f"G suffix {suf!r} (repo fake path)", "DENIED for any media bytes", code(lambda: mg.require_media_authorization(p,"READ_RAW_MEDIA")))
    # direct calls into readers (PIL tripwire)
    import PIL.Image as PI
    opens=[]; orig=PI.open
    PI.open=lambda *a,**k:(opens.append(a),orig(*a,**k))[1]
    from railway_detection.data import validator as V
    r=V._check_image(fake_jpg); rec("H1 validator._check_image(repo fake jpg) result", "denial surfaced as authorization error", repr(r)[:160])
    rec("H1-open-calls", "0", str(len(opens)))
    r=V._read_dimensions(fake_jpg); rec("H2 validator._read_dimensions", "denial surfaced", repr(r))
    rec("H2-open-calls", "0", str(len(opens)))
    try:
        V._file_sha256(fake_jpg); rec("H3 validator._file_sha256","DENIED","ALLOWED")
    except mg.MediaAccessAuthorizationError as e: rec("H3 validator._file_sha256","DENIED",f"DENIED:{e.code}")
    PI.open=orig
    # evaluation input loader: media-suffix source with NO media guard
    calls=[]; og=ic.require_media_authorization
    ic.require_media_authorization=lambda *a,**k:(calls.append(a),og(*a,**k))[1]
    body=b"\x00\x01notjson"; (tmp/"clip.mov").write_bytes(body)
    m={"schema_version":"phase12-evaluation-inputs/1","evidence_classification":"synthetic",
       "partitions":{"train":["train_events/a"],"val":["train_events/b"],"test":["train_events/c"]},
       "events":[{"event_id":e,"cohort":"train_events","split_role":r,"source_path":"clip.mov" if e=="train_events/a" else f"{e[-1]}.json","source_sha256":"0"*64} for e,r in (("train_events/a","train"),("train_events/b","val"),("train_events/c","test"))]}
    for e in "bc": (tmp/f"{e}.json").write_text("{}")
    (tmp/"man.json").write_text(json.dumps(m))
    try: ic.load_evaluation_input_manifest(tmp/"man.json")
    except ic.EvaluationInputError as e: rec("I1 loader on media-suffix source: error", "guard call before read", f"{e.code}: {e.detail[:150]}")
    rec("I1-guard-calls-by-loader", ">=1 for media suffix", str(len(calls)))
    rec("I1-hash-leak-in-error", "no hash of unguarded media in error", "actual sha256 of file bytes = "+hashlib.sha256(body).hexdigest()[:16]+"... (present in message above if shown)")
    ic.require_media_authorization=og
print("DONE")
