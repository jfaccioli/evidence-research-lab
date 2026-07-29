"""Operational readiness track — non-promotional machinery checks."""

from __future__ import annotations

from pathlib import Path

from crl.production.ops_readiness import (
    run_flat_policy_paper,
    run_ops_readiness_checklist,
    run_unit_flip_paper,
)
from crl.shared.data.sources.mock import MockOHLCVSource


def test_flat_and_flip_policies():
    ohlcv = MockOHLCVSource(n=80, seed=1).fetch_ohlcv("BTCUSDT", "1d")
    prices = ohlcv["close"]
    flat = run_flat_policy_paper(prices)
    assert flat["n_fills"] == 0
    assert flat["cash_unchanged"]
    flip = run_unit_flip_paper(prices)
    assert flip["n_fills"] > 0
    assert flip["fees_nonneg"]


def test_ops_checklist(tmp_path: Path, monkeypatch):
    # Isolate kill switch path under tmp via project_root is hard; use checklist with journal
    # Clear any ambient kill switch after
    from crl.production import kill_switch as ks
    from crl.shared.config import project_root

    root = project_root()
    # ensure clear
    ks.clear_kill_switch(root)
    rep = run_ops_readiness_checklist(root=root, journal_dir=tmp_path / "j")
    d = rep.to_dict()
    assert d["scientific_promotion"].startswith("not_applicable")
    assert d["n_items"] >= 10
    # All should pass on healthy install
    assert rep.all_ok(), d["items"]
    assert d["journal_path"] is not None
