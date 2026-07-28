"""Paper-clock mandate records (ops path, not science gates)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from crl.production.paper.clock import (
    PaperClockRecord,
    load_clock,
    paper_clock_satisfied,
    record_session,
    save_clock,
    start_or_get_clock,
)


def test_start_and_record_session(tmp_path: Path):
    rec = start_or_get_clock(tmp_path, "hyp_demo", min_calendar_days=30)
    assert rec.status == "in_progress"
    rec2 = record_session(
        tmp_path,
        "hyp_demo",
        n_bars=100,
        n_fills=3,
        equity_end=51.0,
        max_drawdown=-0.02,
        mandate_limits=True,
        min_calendar_days=30,
    )
    assert len(rec2.sessions) == 1
    # Same day → not yet complete (needs min_calendar_days)
    assert rec2.status == "in_progress"
    loaded = load_clock(tmp_path, "hyp_demo")
    assert loaded is not None
    assert loaded.sessions[0]["n_fills"] == 3


def test_complete_after_elapsed_window(tmp_path: Path):
    past = (datetime.now(timezone.utc) - timedelta(days=35)).replace(microsecond=0)
    rec = PaperClockRecord(
        strategy_id="hyp_ok",
        started_at=past.isoformat(),
        min_calendar_days=30,
        sessions=[],
    )
    save_clock(tmp_path, rec)
    rec2 = record_session(
        tmp_path,
        "hyp_ok",
        n_bars=50,
        n_fills=1,
        equity_end=50.0,
        max_drawdown=0.0,
        mandate_limits=True,
        min_calendar_days=30,
    )
    assert rec2.status == "complete"


def test_satisfied_requires_two_complete(tmp_path: Path):
    past = (datetime.now(timezone.utc) - timedelta(days=40)).isoformat()
    for sid in ("a", "b"):
        save_clock(
            tmp_path,
            PaperClockRecord(
                strategy_id=sid,
                started_at=past,
                min_calendar_days=30,
                sessions=[
                    {
                        "recorded_at": past,
                        "n_bars": 10,
                        "n_fills": 1,
                        "equity_end": 50.0,
                        "max_drawdown": 0.0,
                        "journal_path": None,
                        "mandate_limits": True,
                    }
                ],
                status="complete",
            ),
        )
    ok = paper_clock_satisfied(tmp_path, strategy_ids=["a", "b"], min_survivors=2)
    assert ok["ok"] is True
    missing = paper_clock_satisfied(tmp_path, strategy_ids=["a"], min_survivors=2)
    assert missing["ok"] is False
