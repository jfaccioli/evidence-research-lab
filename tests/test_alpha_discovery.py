"""Alpha Discovery information-advantage catalog."""

from __future__ import annotations

from pathlib import Path

from crl.research.meta.alpha_discovery import (
    discovery_summary,
    ranked_advantages,
    self_critique_prompt,
    sync_catalog,
)


def test_rank_prefers_panel_over_clones():
    items = ranked_advantages()
    assert items[0]["id"] == "cross_event_implied_state"
    assert any(i["id"] == "free_onchain_metric_clone" and i["action"] == "reject" for i in items)


def test_summary_and_critique():
    s = discovery_summary()
    assert s["next"] == "cross_event_implied_state"
    assert "free_onchain_metric_clone" in s["rejected"]
    c = self_critique_prompt()
    assert "world-class" in c["question"].lower() or "World-class" in c["question"]


def test_sync(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(
        "crl.research.meta.alpha_discovery.catalog_path",
        lambda root=None: tmp_path / "a.json",
    )
    assert sync_catalog().exists()
