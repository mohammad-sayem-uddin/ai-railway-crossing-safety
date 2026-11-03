import re, sys, pathlib, ast
ROOT = pathlib.Path('.')
PAT = re.compile(r"Image\.open\(|cv2\.(imread|VideoCapture|imdecode)\(|subprocess\.(run|Popen|check_output|check_call)\(|wave\.open\(|YOLO\(|\.predict\(|np\.load\(|torch\.load\(|\"ffmpeg\"|\"ffprobe\"|sha256_file\(|_sha256\(|hashlib\.sha256\(.*read")
GUARD = re.compile(r"require_media_authorization|precheck_operation_authorized|_authorize|authorize_media|require_media_access|media_guard")
out=[]
for base in ("src","research","scripts"):
    for p in sorted((ROOT/base).rglob("*.py")):
        if "__pycache__" in p.parts: continue
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        for i,l in enumerate(lines, 1):
            if l.lstrip().startswith("#"): continue
            if PAT.search(l):
                # find enclosing def start
                j=i-1
                while j>0 and not re.match(r"\s*(async\s+)?def |class ", lines[j-1]): j-=1
                window = lines[max(j-1,i-40):i]
                g = any(GUARD.search(w) for w in window)
                out.append((str(p), i, l.strip()[:110], "GUARD_NEAR" if g else "no-guard-in-40-lines/func"))
for o in out:
    print("|".join(map(str,o)))
