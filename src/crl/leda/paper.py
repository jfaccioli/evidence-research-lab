"""LEDA-7: paper-path audit wire from stack desired positions.

Historical only. No exchange. LIVE remains dual-flag elsewhere.
Not a promotion gate — verifies Execution-layer intent can drive PaperBroker.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from crl.leda.economic import build_leda_desired
from crl.leda.stack import decide_bar
from crl.leda.util import payload_hash
from crl.production.execution.broker import OrderIntent, PaperBroker
from crl.production.kill_switch import is_kill_switch_engaged
from crl.production.risk_envelope import RiskEnvelope, check_order
from crl.risk.constraints import RiskLimits


def run_leda_paper_session(
    ohlcv: pd.DataFrame,
    *,
    starting_cash: float = 50.0,
    fee_bps_rt: float = 33.0,
    price_col: str = "close",
    journal_dir: Path | None = None,
    forecast_long_threshold: float = 0.5,
    risk_veto_threshold: float = 0.85,
    max_bars: int | None = None,
) -> dict[str, Any]:
    """Replay LEDA-4 map through PaperBroker.

    Desired position is lag-1 applied (decision at close t → position bar t+1).
    Mark price is bar close (audit path; research engine uses open_to_next_open).
    """
    if is_kill_switch_engaged():
        raise RuntimeError("Kill switch engaged — LEDA paper session refused")
    if price_col not in ohlcv.columns:
        raise ValueError(f"missing {price_col}")

    desired, aux = build_leda_desired(
        ohlcv,
        forecast_long_threshold=forecast_long_threshold,
        risk_veto_threshold=risk_veto_threshold,
    )
    target = desired.shift(1).fillna(0.0)

    work = ohlcv.copy()
    if max_bars is not None and max_bars > 0:
        work = work.iloc[:max_bars]
        target = target.reindex(work.index).fillna(0.0)
        aux = aux.reindex(work.index)

    broker = PaperBroker(
        limits=RiskLimits(max_position=1.0, min_position=0.0, max_leverage=1.0),
        fee_bps_rt=fee_bps_rt,
        starting_cash=starting_cash,
    )
    env = RiskEnvelope(
        max_notional_aud=max(starting_cash, 50.0),
        max_trades_per_day=10_000,
        kill_switch=False,
    )

    journal: list[dict[str, Any]] = []
    equity_path: list[float] = []
    n_fills = 0
    pos_flag = 0.0

    for ts, row in work.iterrows():
        px = float(row[price_col])
        if px <= 0 or pd.isna(px):
            continue
        want = float(target.loc[ts]) if ts in target.index else 0.0
        want = 1.0 if want >= 0.5 else 0.0

        e_f = aux.loc[ts, "e_forecast"] if ts in aux.index else float("nan")
        e_r = aux.loc[ts, "e_risk"] if ts in aux.index else float("nan")
        e_f_v = None if pd.isna(e_f) else float(e_f)
        e_r_v = None if pd.isna(e_r) else float(e_r)
        decision = decide_bar(
            asof_time=str(ts),
            e_forecast=e_f_v,
            e_risk=e_r_v,
            forecast_long_threshold=forecast_long_threshold,
            risk_veto_threshold=risk_veto_threshold,
            mode="paper",
        )

        if want > pos_flag + 1e-12:
            qty = max(broker.cash / px, 0.0) * 0.99
            chk = check_order(
                side="buy",
                qty=qty,
                mark_price=px,
                trades_today=0,
                current_position=broker.position(),
                envelope=env,
            )
            if chk.allowed and chk.clipped_qty > 0:
                broker.place_order(
                    OrderIntent(
                        symbol="BTCUSDT",
                        side="buy",
                        qty=chk.clipped_qty,
                        client_tag="leda7",
                    ),
                    mark_price=px,
                )
                n_fills += 1
                pos_flag = 1.0 if broker.position() > 0 else 0.0
        elif want < pos_flag - 1e-12 and broker.position() > 0:
            qty = abs(broker.position())
            chk = check_order(
                side="sell",
                qty=qty,
                mark_price=px,
                trades_today=0,
                current_position=broker.position(),
                envelope=env,
            )
            if chk.allowed and chk.clipped_qty > 0:
                broker.place_order(
                    OrderIntent(
                        symbol="BTCUSDT",
                        side="sell",
                        qty=chk.clipped_qty,
                        client_tag="leda7",
                    ),
                    mark_price=px,
                )
                n_fills += 1
                pos_flag = 0.0 if broker.position() <= 1e-12 else 1.0

        eq = float(broker.cash + broker.position() * px)
        equity_path.append(eq)
        journal.append(
            {
                "ts": str(ts),
                "price": px,
                "target": want,
                "position": broker.position(),
                "equity": eq,
                "risk_veto": decision["risk_veto"],
                "want_long": decision["want_long"],
            }
        )

    equity_end = equity_path[-1] if equity_path else starting_cash
    peak = starting_cash
    max_dd = 0.0
    for e in equity_path:
        peak = max(peak, e)
        if peak > 0:
            max_dd = max(max_dd, 1.0 - e / peak)

    out: dict[str, Any] = {
        "leda": "7",
        "mode": "paper",
        "promotion": "not_applicable — paper audit wire only",
        "places_live_orders": False,
        "n_bars": len(work),
        "n_fills": n_fills,
        "starting_cash": starting_cash,
        "equity_end": round(equity_end, 6),
        "total_return": round(equity_end / starting_cash - 1.0, 6),
        "max_drawdown": round(max_dd, 6),
        "final_position": broker.position(),
        "map": {
            "forecast_long_threshold": forecast_long_threshold,
            "risk_veto_threshold": risk_veto_threshold,
            "fill": "bar_close_proxy_lag1",
        },
        "inputs_hash": payload_hash(
            {
                "n": len(work),
                "start": str(work.index[0]) if len(work) else None,
                "end": str(work.index[-1]) if len(work) else None,
                "thr_f": forecast_long_threshold,
                "thr_r": risk_veto_threshold,
            }
        ),
    }

    if journal_dir is not None:
        journal_dir = Path(journal_dir)
        journal_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = journal_dir / f"leda_paper_{stamp}.json"
        path.write_text(
            json.dumps(
                {"summary": out, "journal_tail": journal[-50:]},
                indent=2,
                default=str,
            )
        )
        out["journal_path"] = str(path)

    return out
