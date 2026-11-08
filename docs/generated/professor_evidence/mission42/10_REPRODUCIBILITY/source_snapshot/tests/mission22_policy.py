"""Constructed regression access policy. Python audit hooks, NOT an OS sandbox."""

from __future__ import annotations

import hashlib
import json
import os
import sys
import threading
from pathlib import Path

import pytest


class PolicyViolation(PermissionError):
    pass


_INSTALLED = False


def install():
    global _INSTALLED
    if _INSTALLED or not os.environ.get("MISSION22_POLICY_ROOT"):
        return
    _INSTALLED = True
    root = Path(__file__).resolve().parents[1]
    temporary = Path(os.environ["MISSION22_POLICY_ROOT"]).resolve()
    (temporary / "registries").mkdir(exist_ok=True)
    log = temporary / "policy_denials.jsonl"
    state = threading.local()
    protected = tuple(
        str(root / p) for p in ("data", "results", "experiments", "models", "outputs")
    )
    system = (
        "/opt/homebrew/",
        "/usr/",
        "/System/",
        "/Library/",
        "/private/etc/",
        "/etc/",
        "/bin/",
        "/sbin/",
        "/proc/",
        "/opt/X11/",
    )

    def denied(event, detail):
        state.busy = True
        try:
            with log.open("a") as f:
                f.write(json.dumps({"event": event, "detail": str(detail)}) + "\n")
        finally:
            state.busy = False
        raise PolicyViolation("MISSION22_POLICY: " + event + ": " + str(detail))

    def at_directory(path, descriptor):
        if descriptor is None or descriptor == -1 or os.path.isabs(os.fsdecode(path)):
            return path
        # shutil uses relative unlink/rmdir against an already-open directory FD.
        # Resolve that actual directory, not the process cwd, before checking writes.
        if sys.platform == "darwin":
            import fcntl

            base = os.fsdecode(fcntl.fcntl(descriptor, 50, bytes(1024)).split(b"\0", 1)[0])
        else:
            base = os.readlink("/proc/self/fd/" + str(descriptor))
        return os.path.join(base, os.fsdecode(path))

    def check(path, write=False):
        if isinstance(path, int) or path is None:
            return
        p = os.fsdecode(path)
        p = os.path.abspath(p)
        if any(p == x or p.startswith(x + "/") for x in protected):
            denied("protected_project_path", p)
        real = os.path.realpath(p)
        if any(real == x or real.startswith(x + "/") for x in protected):
            denied("protected_project_alias", p)
        if real in {"/dev/null", "/dev/urandom"}:
            return
        in_temporary = real == str(temporary) or real.startswith(str(temporary) + "/")
        if write and not in_temporary:
            denied("write_outside_constructed_temp", p)
        if not write and not (
            in_temporary
            or real == str(root)
            or real.startswith(str(root) + "/")
            or real.startswith(system)
            or real.startswith(str(Path(os.environ["MISSION22_SITE_PATH"]).resolve()) + "/")
            or real == str(Path(os.environ["MISSION22_SITE_PATH"]).resolve())
            or real.startswith(str(Path.home() / ".local/share/fonts"))
            or real.startswith(str(Path.home() / ".fonts"))
        ):
            denied("read_outside_source_runtime_or_fixture", p)

    def audit(event, args):
        if getattr(state, "busy", False):
            return
        if event == "open":
            flags = args[2] if len(args) > 2 and isinstance(args[2], int) else 0
            mode = args[1] if len(args) > 1 and isinstance(args[1], str) else ""
            check(
                args[0],
                bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
                or any(x in mode for x in "wax+"),
            )
        elif event == "sqlite3.connect":
            if args[0] != ":memory:":
                if str(args[0]).startswith("file:"):
                    denied("unapproved_sqlite_uri", args[0])
                check(args[0], True)
        elif event in {"os.listdir", "os.scandir"}:
            check(args[0])
        elif event in {"os.remove", "os.rmdir", "os.mkdir", "os.chmod"}:
            index = 2 if event in {"os.mkdir", "os.chmod"} else 1
            check(at_directory(args[0], args[index] if len(args) > index else None), True)
        elif event in {"os.rename", "os.link", "os.symlink"}:
            # symlink source can be a symbolic target; only creation is allowed in temp.
            if event != "os.symlink":
                check(at_directory(args[0], args[2] if len(args) > 2 else None), True)
            destination_fd = (
                args[2] if event == "os.symlink" else (args[3] if len(args) > 3 else None)
            )
            check(at_directory(args[1], destination_fd), True)
        elif (
            event in {"socket.connect", "socket.bind"}
            and isinstance(args[1], tuple)
            and args[1][0] in {"127.0.0.1", "::1", "localhost"}
        ):
            return
        elif event in {
            "socket.connect",
            "socket.bind",
            "os.system",
            "os.posix_spawn",
            "os.posix_spawnp",
        }:
            denied(event, str(args[:2]))
        elif event == "subprocess.Popen":
            executable, argv, _, env = args
            command = os.fsdecode(executable)
            if Path(command).name.startswith("python") or command in {
                str(root / ".venv/bin" / name) for name in ("mypy", "pytest", "ruff")
            }:
                child_env = os.environ if env is None else env
                if os.environ.get("MISSION22_SITE_PATH", "") not in child_env.get("PYTHONPATH", ""):
                    denied("child_python_missing_policy", argv)
            elif (
                Path(command).name == "fc-list" and all(str(x).startswith("--") for x in argv[1:])
            ) or argv == ["system_profiler", "-xml", "SPFontsDataType"]:
                return
            elif Path(command).name == "git" and "rev-parse" in argv:
                return
            else:
                denied("unapproved_child_program", argv)

    def profile(frame, event, arg):
        if event == "call":
            module = frame.f_globals.get("__name__", "")
            name = frame.f_code.co_name
            if (
                module.startswith(("torch.optim", "ultralytics", "sklearn"))
                and name in {"step", "fit", "train", "partial_fit"}
            ) or (
                module.startswith("railway_detection") and name in {"train_model", "fit_calibrator"}
            ):
                denied("actual_training_backend", module + "." + name)

    sys.addaudithook(audit)
    sys.setprofile(profile)


@pytest.fixture(autouse=True)
def isolated_experiment_registry(request, monkeypatch):
    base = os.environ.get("MISSION22_POLICY_ROOT")
    if not base:
        yield None
        return
    relative = request.node.path.relative_to(Path(__file__).resolve().parents[1] / "tests")
    if not str(relative.parts[0]).startswith("synthetic_"):
        target = request.getfixturevalue("tmp_path") / "experiment_registry.jsonl"
    else:
        target = (
            Path(base)
            / "registries"
            / (hashlib.sha256(request.node.nodeid.encode()).hexdigest() + ".jsonl")
        )
    monkeypatch.setenv("RAILWAY_EXPERIMENT_REGISTRY", str(target))
    yield target
