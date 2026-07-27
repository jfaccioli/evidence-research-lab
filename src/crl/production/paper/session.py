"""Historical paper-trading session (no exchange, no live clock required).

Walks a feature frame bar-by-bar, maps long-only full/flat rules to
PaperBroker fills. Used to harden the execution path before shadow/live.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import pandas as pd

from crl.production.execution.broker import OrderIntent, PaperBroker
from crl.research.hypotheses.rules import eval_rule
from crl.risk.constraints import RiskLimits, clamp_position
from crl.shared.types import HypothesisSpec


@dataclass
class PaperSessionResult:
    hypothesis_id: str
    n_bars: int
    n_fills: int
    final_position: float
    final_cash: float
    starting_cash: float
    journal_path: Optional[str] = None
    equity_end: Optional[float] = None
    max_drawdown: Optional[float] = None
    notes: list[str] = field(default_factory=list)


def desired_long_only(entry_expr: str, exit_expr: str, row: dict[str, Any], prev: float) -> float:
    """Sticky long-only: enter on entry true; exit on exit true; else hold."""
    try:
        ent = bool(eval_rule(entry_expr, row))
        ex = bool(eval_rule(exit_expr, row))
    except Exception:
        return prev
    if prev <= 0 and ent and not ex:
        return 1.0
    if prev > 0 and ex:
        return 0.0
    if prev > 0 and ent:
        return 1.0
    return prev


def run_paper_session(
    spec: HypothesisSpec,
    features: pd.DataFrame,
    *,
    starting_cash: float = 50.0,
    fee_bps_rt: float = 33.0,
    price_col: str = "close",
    journal_dir: Path | None = None,
    burn_in_cols: tuple[str, ...] = ("sma_200", "atr_14"),
) -> PaperSessionResult:
    """Simulate paper trading on historical features (research path)."""
    if price_col not in features.columns:
        raise ValueError(f"missing price column {price_col}")
    work = features.copy()
    need = [c for c in burn_in_cols if c in work.columns]
    if need:
        work = work.dropna(subset=need)
    broker = PaperBroker(
        limits=RiskLimits(max_position=1.0, min_position=0.0, max_leverage=1.0),
        fee_bps_rt=fee_bps_rt,
        starting_cash=starting_cash,
    )
    # Position unit = fraction of equity notionally 1.0 full long in "units"
    # Mark-to-market uses price; we trade unit size = cash/price when going long.
    pos_flag = 0.0
    journal: list[dict[str, Any]] = []
    equity_series: list[float] = []

    for ts, row_s in work.iterrows():
        row = row_s.to_dict()
        # inject close alias
        row.setdefault("close", float(row_s[price_col]))
        px = float(row_s[price_col])
        if px <= 0 or pd.isna(px):
            continue
        desired = desired_long_only(
            spec.entry.expression, spec.exit.expression, row, pos_flag
        )
        desired = clamp_position(desired, broker.limits)
        if desired > pos_flag + 1e-12:
            # buy to full long: size so notional ≈ cash (tiny capital full-or-flat)
            qty = max(broker.cash / px, 0.0) * 0.99
            if qty > 0:
                fill = broker.place_order(
                    OrderIntent(
                        symbol=spec.asset.replace("/", ""),
                        side="buy",
                        qty=qty,
                        client_tag=spec.id,
                    ),
                    mark_price=px,
                )
                journal.append(
                    {
                        "ts": str(ts),
                        "event": "fill",
                        "fill": asdict(fill),
                        "desired": desired,
                    }
                )
            pos_flag = 1.0 if broker.position() > 0 else 0.0
        elif desired < pos_flag - 1e-12:
            qty = abs(broker.position())
            if qty > 0:
                fill = broker.place_order(
                    OrderIntent(
                        symbol=spec.asset.replace("/", ""),
                        side="sell",
                        qty=qty,
                        client_tag=spec.id,
                    ),
                    mark_price=px,
                )
                journal.append(
                    {
                        "ts": str(ts),
                        "event": "fill",
                        "fill": asdict(fill),
                        "desired": desired,
                    }
                )
            pos_flag = 0.0 if broker.position() <= 1e-12 else 1.0
        # MTM equity
        equity = broker.cash + broker.position() * px
        equity_series.append(equity)
        journal.append(
            {
                "ts": str(ts),
                "event": "mark",
                "position": broker.position(),
                "cash": broker.cash,
                "equity": equity,
                "price": px,
                "desired_flag": desired,
            }
        )

    jpath = None
    if journal_dir is not None:
        journal_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        jpath = journal_dir / f"paper_{spec.id}_{stamp}.jsonl"
        with jpath.open("w") as f:
            for rec in journal:
                f.write(json.dumps(rec, default=str) + "\n")

    max_dd = None
    if equity_series:
        peak = equity_series[0]
        max_dd = 0.0
        for eq in equity_series:
            peak = max(peak, eq)
            if peak > 0:
                max_dd = max(max_dd, 1.0 - eq / peak)

    return PaperSessionResult(
        hypothesis_id=spec.id,
        n_bars=len(work),
        n_fills=len(broker.fills),
        final_position=broker.position(),
        final_cash=broker.cash,
        starting_cash=starting_cash,
        journal_path=str(jpath) if jpath else None,
        equity_end=equity_series[-1] if equity_series else starting_cash,
        max_drawdown=max_dd,
        notes=[
            "historical bar walk; not live clock",
            "LIVE disabled by design",
            "NOT a substitute for train/val/test research gates",
        ],
    )
