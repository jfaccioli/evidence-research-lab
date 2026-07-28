"""Historical shadow walk — would-be signals without capital."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from crl.production.kill_switch import is_kill_switch_engaged
from crl.production.paper.session import desired_long_only
from crl.production.shadow.logger import ShadowSession
from crl.shared.types import HypothesisSpec


def shadow_walk(
    spec: HypothesisSpec,
    features: pd.DataFrame,
    *,
    price_col: str = "close",
    burn_in_cols: tuple[str, ...] = ("sma_200",),
    log_dir: Path | None = None,
) -> dict[str, Any]:
    if is_kill_switch_engaged():
        raise RuntimeError("Kill switch engaged — shadow walk refused")
    work = features.copy()
    need = [c for c in burn_in_cols if c in work.columns]
    if need:
        work = work.dropna(subset=need)
    session = ShadowSession(hypothesis_id=spec.id)
    prev = 0.0
    for ts, row_s in work.iterrows():
        row = row_s.to_dict()
        row.setdefault("close", float(row_s[price_col]))
        px = float(row_s[price_col])
        desired = desired_long_only(
            spec.entry.expression, spec.exit.expression, row, prev
        )
        session.on_bar(ts=str(ts), signal=desired, mark_price=px, symbol="BTCUSDT")
        prev = desired
    path = None
    if log_dir is not None:
        from datetime import datetime, timezone

        log_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = log_dir / f"shadow_{spec.id}_{stamp}.jsonl"
        session.write_jsonl(path)
    n_intent = sum(1 for e in session.events if e.intent is not None)
    return {
        "hypothesis_id": spec.id,
        "n_bars": len(work),
        "n_signal_changes": n_intent,
        "log_path": str(path) if path else None,
    }
