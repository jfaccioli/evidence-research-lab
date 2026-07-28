"""PIT publish-lag sensitivity harness (capability for future series).

When a new series arrives, re-run a locked hyp set under several lag days
without changing gates — detects fragile “same-day” edges.
"""

from __future__ import annotations

from typing import Any, Callable

import pandas as pd


def shift_event_times(events: pd.DataFrame, lag_days: int, time_col: str) -> pd.DataFrame:
    df = events.copy()
    df[time_col] = pd.to_datetime(df[time_col], utc=True) + pd.Timedelta(days=int(lag_days))
    return df


def lag_sensitivity_grid(
    base_events: pd.DataFrame,
    *,
    time_col: str,
    lag_days_list: list[int],
    run_fn: Callable[[pd.DataFrame, int], dict[str, Any]],
) -> list[dict[str, Any]]:
    """run_fn(events, lag_days) -> summary dict with at least n_passed_val."""
    rows: list[dict[str, Any]] = []
    for lag in lag_days_list:
        # base_events already include some lag; extra lag is additional delay
        ev = shift_event_times(base_events, lag, time_col) if lag else base_events
        if time_col == "event_time":
            # de-dupe after shift
            ev = ev.drop_duplicates(subset=[time_col], keep="last")
        summary = run_fn(ev, lag)
        rows.append(
            {
                "extra_lag_days": lag,
                "n_passed_val": summary.get("n_passed_val"),
                "n_run": summary.get("n_run"),
                "n_candidates": summary.get("n_candidates"),
                "detail": summary.get("detail"),
            }
        )
    return rows
