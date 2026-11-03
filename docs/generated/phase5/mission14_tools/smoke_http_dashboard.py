import http.client, tempfile, threading, pathlib, sys
sys.dont_write_bytecode=True
from http.server import HTTPServer
from railway_detection.demo import server as S
with tempfile.TemporaryDirectory() as t:
    root=pathlib.Path(t).resolve(); (root/"outputs/video_tests/r").mkdir(parents=True); (root/"data/raw/ds").mkdir(parents=True); (root/"configs").mkdir()
    (root/"outputs/video_tests/r/a.mp4").write_bytes(b"OKVIDEO"); (root/"data/raw/ds/secret.mov").write_bytes(b"SECRET-RAW"); (root/"configs/c.yaml").write_text("k: v")
    static=root/"web"; static.mkdir(); (static/"index.html").write_text("<html>spa</html>"); (static/"app.js").write_text("//js")
    S.PROJECT_ROOT=root; S.STATIC_WEB_DIR=static
    srv=HTTPServer(("127.0.0.1",0),S.DashboardHTTPRequestHandler); port=srv.server_address[1]
    th=threading.Thread(target=srv.serve_forever,daemon=True); th.start()
    def get(path):
        c=http.client.HTTPConnection("127.0.0.1",port,timeout=5); c.putrequest("GET",path,skip_host=False); c.endheaders()
        r=c.getresponse(); body=r.read(); c.close(); return r.status, body[:40]
    for p in ["/", "/app.js", "/outputs/video_tests/r/a.mp4", "/outputs/../data/raw/ds/secret.mov", "/outputs/%2e%2e/data/raw/ds/secret.mov",
              "/outputs/%252e%252e/data/raw/ds/secret.mov", "/outputs/..%5cdata%5craw%5cds%5csecret.mov", "/../configs/c.yaml",
              "/%2e%2e/configs/c.yaml", "/experiments/../configs/c.yaml", "/etc/passwd"]:
        print(f"{p:50s} -> {get(p)}")
    srv.shutdown(); srv.server_close()
