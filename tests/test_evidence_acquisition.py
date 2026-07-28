"""Evidence acquisition catalog and spend recommendations."""

from __future__ import annotations

from pathlib import Path

from crl.research.meta.evidence_acquisition import (
    acquisition_summary,
    recommend_spend,
    ranked_items,
    sync_catalog,
)


def test_catalog_ranked():
    items = ranked_items()
    assert items[0]["rank"] <= items[-1]["rank"]
    assert any(i["id"] == "pm_kalshi_panel_free" for i in items)


def test_reject_cmd_clones():
    r = recommend_spend("cmd_free_clones")
    assert r["should_spend_money_now"] is False
    assert r["recommendation_base"] == "reject"


def test_vendor_requires_programme():
    r = recommend_spend("vendor_exchange_flow", programme_locked=False)
    assert r["should_spend_money_now"] is False
    r2 = recommend_spend(
        "vendor_exchange_flow",
        programme_locked=True,
        free_alternatives_exhausted=True,
        annual_usd_cost=400,
    )
    assert r2["should_spend_money_now"] is True


def test_sync_catalog(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(
        "crl.research.meta.evidence_acquisition.catalog_path",
        lambda root=None: tmp_path / "cat.json",
    )
    p = sync_catalog()
    assert p.exists()
    s = acquisition_summary()
    assert s["next_free"] is not None
