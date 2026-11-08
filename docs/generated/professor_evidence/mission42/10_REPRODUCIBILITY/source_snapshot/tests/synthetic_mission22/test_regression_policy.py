"""Check the full-inventory runner's access boundary in an actual child process."""

import os
import subprocess
import sys
from pathlib import Path


def test_inherited_policy_blocks_resources_and_preserves_temporary_cleanup(tmp_path):
    root = Path(__file__).resolve().parents[2]
    site = tmp_path / "site"
    site.mkdir()
    (site / "sitecustomize.py").write_text("from mission22_policy import install\ninstall()\n")
    work = tmp_path / "work"
    work.mkdir()
    program = r"""
import os, shutil, socket, subprocess, sys
from pathlib import Path
from mission22_policy import PolicyViolation
root, work = map(Path, sys.argv[1:])
def refused(action):
    try:
        action()
    except PolicyViolation:
        return
    raise AssertionError("access policy did not refuse action")
refused(lambda: (root/'data/raw/never_opened').read_bytes())
refused(lambda: (root/'must_not_be_written.txt').write_text('bad'))
refused(lambda: socket.socket().connect(('192.0.2.1', 80)))
refused(lambda: subprocess.run([sys.executable, '-c', 'pass'],
    env=dict(os.environ, PYTHONPATH='')))
namespace = {'__name__':'torch.optim.constructed_tripwire'}
exec('def step(): return 1', namespace)
refused(namespace['step'])
local = socket.socket(); local.bind(('127.0.0.1', 0)); local.close()
folder = work/'nested'; folder.mkdir(); (folder/'fixture.txt').write_text('constructed')
shutil.rmtree(folder)
assert not folder.exists()
print('POLICY_BOUNDARIES_AND_FD_CLEANUP_VERIFIED')
"""
    env = os.environ | {
        "MISSION22_POLICY_ROOT": str(work),
        "MISSION22_SITE_PATH": str(site),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPATH": os.pathsep.join(
            [str(site), str(root / "tests"), os.environ.get("PYTHONPATH", "")]
        ),
    }
    result = subprocess.run(
        [sys.executable, "-c", program, str(root), str(work)],
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "POLICY_BOUNDARIES_AND_FD_CLEANUP_VERIFIED" in result.stdout
