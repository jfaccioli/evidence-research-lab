"""Lab vs autotrading readiness dual metric."""

from __future__ import annotations

from crl.ops.readiness import readiness_report


def test_readiness_lab_ops_true_autotrading_false():
    r = readiness_report()
    assert r["lab_ops_ready"] is True
    assert r["lab_ops_score"] >= 0.99
    assert r["autotrading_ready"] is False
    assert r["autotrading_score"] == 0.0
    assert r["close_to_tiny_live"] is False
    assert r["lab_ops_checks"]["live_disabled"] is True
    assert r["lab_ops_checks"]["flow_scaffold_present"] is True
    assert "paper_clock_detail" in r
    assert r["paper_clock_detail"]["ok"] is False
