import sys, io, pathlib, tempfile
sys.dont_write_bytecode=True
from railway_detection.demo import server as S
class Fake:
    def __init__(s): s.wfile=io.BytesIO(); s.headers={}; s.status=None
    def send_response(s,c,*a): s.status=c
    def send_header(s,*a): pass
    def end_headers(s): pass
    def send_error(s,c,*a): s.status=("error",c)
with tempfile.TemporaryDirectory() as t:
    root=pathlib.Path(t).resolve(); (root/"outputs").mkdir(); (root/"data/raw/ds").mkdir(parents=True); (root/"outputs/ok.mp4").write_bytes(b"OK")
    (root/"data/raw/ds/secret.mov").write_bytes(b"SYNTHETIC-SECRET"); (root/"configs").mkdir(); (root/"configs/c.yaml").write_text("k: v")
    S.PROJECT_ROOT=root
    for route,url in (("output","/outputs/ok.mp4"),("output","/outputs/../data/raw/ds/secret.mov"),("output","/outputs/../configs/c.yaml"),("exp","/experiments/../data/raw/ds/secret.mov")):
        f=Fake(); fn=S.DashboardHTTPRequestHandler._handle_serve_output_file if route=="output" else S.DashboardHTTPRequestHandler._handle_serve_experiment_file
        fn(f,url); print(f"{url:42s} status={f.status} body={f.wfile.getvalue()[:24]!r}")
print("DONE")
