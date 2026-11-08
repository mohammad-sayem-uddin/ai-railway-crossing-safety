import hashlib
import json

import pytest

from railway_detection.synthetic.integration_workflow import run_demo

CODE = "2" * 40


@pytest.mark.parametrize(
    "field", ["mock_review", "boundary_projection", "separate_A_metric_receipt"]
)
def test_rehashed_substituted_public_results_fail_full_replay(tmp_path, field):
    output = tmp_path / "constructed"
    run_demo(output, code_identity=CODE)
    core = json.loads((output / "execution.json").read_text())
    core[field] = {"substituted": "CONSTRUCTED_TAMPER"}
    (output / "execution.json").write_text(json.dumps(core))
    marker = json.loads((output / "COMPLETE.json").read_text())
    marker["artifacts"]["execution.json"] = hashlib.sha256(
        (output / "execution.json").read_bytes()
    ).hexdigest()
    (output / "COMPLETE.json").write_text(json.dumps(marker))
    with pytest.raises(ValueError, match="full constructed replay"):
        run_demo(output, code_identity=CODE, resume=True)


@pytest.mark.parametrize(
    "artifact", ["results_absent_report.md", "snapshot/src/fixture.py", "ACK.json"]
)
def test_rehashed_non_result_artifacts_fail_full_replay(tmp_path, artifact):
    output = tmp_path / "constructed"
    run_demo(output, code_identity=CODE)
    (output / artifact).write_text("CONSTRUCTED_TAMPER")
    marker = json.loads((output / "COMPLETE.json").read_text())
    marker["artifacts"][artifact] = hashlib.sha256((output / artifact).read_bytes()).hexdigest()
    (output / "COMPLETE.json").write_text(json.dumps(marker))
    with pytest.raises(ValueError, match="full constructed replay"):
        run_demo(output, code_identity=CODE, resume=True)


def test_completed_run_cannot_hide_pending_metadata(tmp_path):
    output = tmp_path / "constructed"
    run_demo(output, code_identity=CODE)
    (output / "ACK.json.pending").write_text("{")
    with pytest.raises(ValueError, match="incomplete pending"):
        run_demo(output, code_identity=CODE, resume=True)
