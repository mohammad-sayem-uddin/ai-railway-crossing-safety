"""End-to-end CLI, immutable publication, independent lineage joins and replay."""

import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest
from tests.synthetic_mission25.test_contracts import CODE

from railway_detection.annotation.evidence_review.contracts import canonical, digest
from railway_detection.annotation.evidence_review.integration import (
    demo,
    deterministic_result,
    fixture_contracts,
    interface_contract,
    join_review_lineage,
    open_fixture_journal,
    run_fixture_commands,
    verify,
)
from railway_detection.annotation.evidence_review.lifecycle import ReviewLifecycle
from railway_detection.safety.constructed_authority import sha

ROOT = Path(__file__).resolve().parents[2]


def test_two_independent_demonstrations_identical_complete_history_lineage_and_snapshot(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    assert demo(a, CODE) == demo(b, CODE) == verify(a)
    for name in ("REVIEW_DASHBOARD.json", "REVIEW_LINEAGE.json", "snapshot/SOURCE_MANIFEST.json"):
        assert (a / name).read_bytes() == (b / name).read_bytes()
    d = json.loads((a / "REVIEW_DASHBOARD.json").read_text())
    assert len(d["observations"]) == 9
    assert len(d["audit_history"]) == 15
    assert not d["adjudications"]
    assert d["readiness"]["status"] == "CONSTRUCTED_NON_PROMOTABLE"
    assert all(c["automatic_adjudication"] is False for c in d["comparisons"])
    assert "UNAVAILABLE" in (a / "RESULTS_ABSENT.md").read_text()
    with pytest.raises(ValueError, match="exists"):
        demo(a, CODE)


@pytest.mark.parametrize(
    "fault",
    [
        "dashboard",
        "lineage",
        "report",
        "snapshot",
        "source_snapshot",
        "marker",
        "missing_parent",
        "alias",
        "db_alias",
        "journal",
        "anchor",
        "false_human",
        "false_promotion",
        "unknown_schema",
        "artifact_omission",
    ],
)
def test_publication_and_database_tampering_refused_even_when_public_hashes_recomputed(
    tmp_path, fault
):
    out = tmp_path / "output"
    demo(out, CODE)
    marker = json.loads((out / "REVIEW_COMPLETE.json").read_text())
    names = {
        "dashboard": "REVIEW_DASHBOARD.json",
        "lineage": "REVIEW_LINEAGE.json",
        "report": "RESULTS_ABSENT.md",
    }
    if fault in names:
        p = out / names[fault]
        p.write_text("substituted")
        marker["artifacts"][p.name] = sha("substituted")
    elif fault == "snapshot":
        (out / "snapshot/SOURCE_MANIFEST.json").write_text("{}")
        marker["snapshot_digest"] = sha("{}")
    elif fault == "source_snapshot":
        (out / "snapshot/src/railway_detection/annotation/evidence_review/contracts.py").write_text(
            "changed"
        )
    elif fault == "marker":
        marker["approved"] = True
    elif fault == "missing_parent":
        (out / "REVIEW_LINEAGE.json").unlink()
    elif fault in ("alias", "db_alias"):
        p = out / (
            "constructed-governance.sqlite" if fault == "db_alias" else "REVIEW_DASHBOARD.json"
        )
        p.unlink()
        p.symlink_to(tmp_path / "NEVER_READ")
    elif fault == "journal":
        import sqlite3

        with sqlite3.connect(out / "constructed-governance.sqlite") as db:
            db.execute("UPDATE governance_log SET result='tampered' WHERE seq=1")
    elif fault == "anchor":
        marker["retained_anchor"] = [0, None]
    elif fault == "false_human":
        marker["genuine_evidence"] = True
    elif fault == "false_promotion":
        marker["promotion"] = True
    elif fault == "unknown_schema":
        marker["schema"] = "unknown"
    elif fault == "artifact_omission":
        del marker["artifacts"]["REVIEW_LINEAGE.json"]
    (out / "REVIEW_COMPLETE.json").write_text(canonical(marker))
    with pytest.raises((ValueError, OSError, KeyError)):
        verify(out)


@pytest.mark.parametrize(
    "fault", ["lineage", "source", "event", "manifest", "source_parent", "artifact_exposure"]
)
def test_actual_wp02_wp07_join_refuses_review_identity_and_transitive_parent_substitutions(fault):
    f, b, r, _ = fixture_contracts(CODE)
    if fault == "lineage":
        b = replace(b, lineage_digest="0" * 64)
    elif fault == "source":
        b = replace(b, sources=(replace(b.sources[0], content_digest="0" * 64),))
    elif fault == "event":
        b = replace(
            b,
            events=(("synthetic:other", "TRAIN"),),
            sources=(replace(b.sources[0], event="synthetic:other"),),
        )
    elif fault == "manifest":
        b = replace(
            b,
            manifest_reference="other",
            sources=(replace(b.sources[0], manifest_reference="other"),),
        )
    elif fault == "source_parent":
        rows = f["manifest"].records
        f["manifest"] = replace(
            f["manifest"], records=(replace(rows[0], parents=("synthetic:missing",)),) + rows[1:]
        )
    else:
        artifacts = f["registry"].artifacts
        f["registry"] = replace(
            f["registry"],
            artifacts=(replace(artifacts[0], fit_events=(b.events[0][0],)),) + artifacts[1:],
        )
    with pytest.raises((ValueError, TypeError)):
        join_review_lineage(ReviewLifecycle(b, r), f)


def test_correction_lineage_parent_and_journal_recovery_survive_real_sqlite(tmp_path):
    import sqlite3

    f, b, r, p = fixture_contracts(CODE)
    path = tmp_path / "constructed.sqlite"
    with sqlite3.connect(path) as db:
        j, scopes = open_fixture_journal(db, b, r, p, anchor=(0, None))
        run_fixture_commands(j, scopes, b, r, p)
        joined = join_review_lineage(j.restore(), f)
        anchor = j.anchor
    with sqlite3.connect(path) as db:
        j, _ = open_fixture_journal(db, b, r, p, anchor=anchor)
        assert digest(join_review_lineage(j.restore(), f)) == digest(joined)
    overlays = joined["observation_overlays"]
    assert len(overlays) == 9
    assert overlays[-1]["previous"] == overlays[0]["id"]
    assert not joined["eligible_for_fit_or_promotion"]


def test_cli_interface_demo_verify_and_dashboard_are_actual_commands(tmp_path):
    base = [sys.executable, "-m", "railway_detection", "application", "review"]
    commands = [
        ["interface"],
        ["demo", "--output", str(tmp_path / "demo"), "--code-identity", CODE],
        ["verify", "--output", str(tmp_path / "demo")],
        ["dashboard", "--output", str(tmp_path / "demo")],
    ]
    for args in commands:
        p = subprocess.run(base + args, cwd=ROOT, capture_output=True, text=True)
        assert p.returncode == 0, p.stdout + p.stderr
        body = json.loads(p.stdout)
        assert body["schema"]
    p = subprocess.run(
        base + ["demo", "--output", str(tmp_path / "demo"), "--code-identity", CODE],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert p.returncode == 2
    assert json.loads(p.stdout)["status"] == "REFUSED"


def test_genuine_interface_stays_disabled_and_results_never_claim_human_performance():
    contract = interface_contract()
    assert not contract["genuine_mode_enabled"] and not contract["receipt_issuer_enabled"]
    assert not contract["automatic_adjudication"]
    d, lineage, report, _ = deterministic_result(CODE)
    assert not d["readiness"]["genuine_evidence_accepted"]
    assert not lineage["genuine_evidence"]
    assert "No empirical results supplied" in report


@pytest.mark.parametrize("fault", ["grant", "session", "authority_log", "pending"])
def test_completed_verification_refuses_missing_authority_parents_without_repair(tmp_path, fault):
    import sqlite3

    out = tmp_path / "output"
    demo(out, CODE)
    if fault == "pending":
        (out / "REVIEW_DASHBOARD.json.pending").write_text("unfinished")
    else:
        with sqlite3.connect(out / "constructed-governance.sqlite") as db:
            db.execute(
                {
                    "grant": "DELETE FROM grants WHERE id='synthetic:grant:0'",
                    "session": "DELETE FROM sessions WHERE id='synthetic:session:0'",
                    "authority_log": "DELETE FROM entries",
                }[fault]
            )
    with pytest.raises((ValueError, OSError)):
        verify(out)
    if fault in ("grant", "session"):
        with sqlite3.connect(out / "constructed-governance.sqlite") as db:
            table = "grants" if fault == "grant" else "sessions"
            assert db.execute("SELECT count(*) FROM " + table).fetchone()[0] == 2


def test_protected_destination_is_refused_before_demo_creates_any_output():
    with pytest.raises(ValueError, match="protected"):
        demo(ROOT / "data/raw/mission25_never_created", CODE)


def test_verification_does_not_initialize_missing_persisted_service_tables(tmp_path):
    import sqlite3

    out = tmp_path / "output"
    demo(out, CODE)
    with sqlite3.connect(out / "constructed-governance.sqlite") as db:
        db.execute("DROP TABLE grants")
    with pytest.raises(ValueError, match="never initialize"):
        verify(out)
    with sqlite3.connect(out / "constructed-governance.sqlite") as db:
        assert not db.execute("SELECT name FROM sqlite_master WHERE name='grants'").fetchall()
