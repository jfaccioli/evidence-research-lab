"""Workstream F meta-research + family trial ledger."""

from __future__ import annotations

from pathlib import Path

from crl.research.meta.family_trials import (
    load_ledger,
    multiplicity_snapshot,
    record_programme_trials,
)
from crl.research.meta.workstream_f import PRINCIPLES, principles_report, sync_principles_file


def test_principles_have_decision_fields():
    assert len(PRINCIPLES) >= 10
    for p in PRINCIPLES:
        assert "id" in p and "status" in p and "sci_ev" in p


def test_principles_report_and_sync(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(
        "crl.research.meta.workstream_f.principles_path",
        lambda root=None: tmp_path / "principles.json",
    )
    path = sync_principles_file()
    assert path.exists()
    rep = principles_report()
    assert rep["n_principles"] == len(PRINCIPLES)
    assert "by_status" in rep


def test_family_trial_ledger(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(
        "crl.research.meta.family_trials.ledger_path",
        lambda root=None: tmp_path / "ledger.json",
    )
    out = record_programme_trials(
        programme="demo_prog",
        family_counts={"family_a": 3, "family_b": 2},
        n_passed_val=1,
        n_candidates=0,
    )
    assert out["n_trials_added"] == 5
    led = load_ledger()
    assert led["total_exploratory_trials"] == 5
    assert led["families"]["family_a"]["n_trials"] == 3
    snap = multiplicity_snapshot()
    assert snap["total_exploratory_trials"] == 5
    assert snap["n_families"] == 2
