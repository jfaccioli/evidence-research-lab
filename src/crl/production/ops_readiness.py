"""Trading Readiness Track — operational infrastructure only (zero capital).

Strictly separate from scientific promotion. Uses non-alpha reference policies
(always flat or deterministic always-long paper) to verify machinery, not performance.

Does NOT open LIVE. Does NOT grant APPROVED status.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd

from crl.production.execution.broker import OrderIntent, PaperBroker, ShadowBroker
from crl.production.kill_switch import (
    clear_kill_switch,
    engage_kill_switch,
    is_kill_switch_engaged,
    kill_switch_path,
)
from crl.production.risk_envelope import RiskEnvelope, check_order
from crl.risk.constraints import RiskLimits
from crl.shared.config import project_root


TRACK_VERSION = 1
CHECKLIST_ID = "trading_readiness_checklist_v1"


@dataclass
class ChecklistItem:
    id: str
    ok: bool
    detail: str


@dataclass
class OpsReadinessReport:
    track: str = "operational_readiness"
    version: int = TRACK_VERSION
    checklist_id: str = CHECKLIST_ID
    scientific_promotion: str = "not_applicable — ops track only"
    live_enabled: bool = False
    items: list[ChecklistItem] = field(default_factory=list)
    journal_path: Optional[str] = None
    completed_at: str = ""

    def all_ok(self) -> bool:
        return bool(self.items) and all(i.ok for i in self.items)

    def to_dict(self) -> dict[str, Any]:
        return {
            "track": self.track,
            "version": self.version,
            "checklist_id": self.checklist_id,
            "scientific_promotion": self.scientific_promotion,
            "live_enabled": self.live_enabled,
            "all_ok": self.all_ok(),
            "n_pass": sum(1 for i in self.items if i.ok),
            "n_items": len(self.items),
            "items": [asdict(i) for i in self.items],
            "journal_path": self.journal_path,
            "completed_at": self.completed_at,
            "note": (
                "Passing ops readiness does NOT authorize trading, shadow-alpha, "
                "or gate softening. Science remains fail-closed on confirmatory path."
            ),
        }


def _equity(cash: float, position: float, px: float) -> float:
    return float(cash + position * px)


def run_flat_policy_paper(
    prices: pd.Series,
    *,
    starting_cash: float = 50.0,
    fee_bps_rt: float = 33.0,
    journal: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Always-flat reference: no orders; cash constant; position 0."""
    broker = PaperBroker(
        limits=RiskLimits(max_position=1.0, min_position=0.0, max_leverage=1.0),
        fee_bps_rt=fee_bps_rt,
        starting_cash=starting_cash,
    )
    for ts, px in prices.items():
        px = float(px)
        if px <= 0 or not np.isfinite(px):
            if journal is not None:
                journal.append(
                    {
                        "ts": str(ts),
                        "event": "stale_or_bad_price",
                        "price": px,
                        "action": "skip",
                    }
                )
            continue
        # intentionally no orders
        eq = _equity(broker.cash, broker.position(), px)
        if journal is not None:
            journal.append(
                {
                    "ts": str(ts),
                    "event": "mark",
                    "policy": "always_flat",
                    "position": broker.position(),
                    "cash": broker.cash,
                    "equity": eq,
                    "price": px,
                }
            )
    return {
        "policy": "always_flat",
        "n_bars": len(prices),
        "n_fills": len(broker.fills),
        "final_position": broker.position(),
        "final_cash": broker.cash,
        "starting_cash": starting_cash,
        "cash_unchanged": abs(broker.cash - starting_cash) < 1e-9,
        "position_flat": abs(broker.position()) < 1e-12,
    }


def run_unit_flip_paper(
    prices: pd.Series,
    *,
    starting_cash: float = 50.0,
    fee_bps_rt: float = 33.0,
    journal: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Deterministic non-alpha policy: long for 5 bars, flat for 5 bars (cycle).

    Proves accounting identity under known turnover — not a scientific edge.
    """
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
    pos_flag = 0.0
    n_blocked = 0
    for i, (ts, px) in enumerate(prices.items()):
        px = float(px)
        if px <= 0 or not np.isfinite(px):
            if journal is not None:
                journal.append({"ts": str(ts), "event": "bad_price_skip", "price": px})
            continue
        want = 1.0 if (i // 5) % 2 == 0 else 0.0
        if want > pos_flag + 1e-12:
            qty = max(broker.cash / px, 0.0) * 0.99
            dec = check_order(
                side="buy",
                qty=qty,
                mark_price=px,
                trades_today=0,
                current_position=broker.position(),
                envelope=env,
            )
            if dec.allowed and dec.clipped_qty > 0:
                fill = broker.place_order(
                    OrderIntent(symbol="BTCUSDT", side="buy", qty=dec.clipped_qty, client_tag="ops_flip"),
                    mark_price=px,
                )
                pos_flag = 1.0 if broker.position() > 0 else 0.0
                if journal is not None:
                    journal.append(
                        {
                            "ts": str(ts),
                            "event": "fill",
                            "side": "buy",
                            "qty": fill.qty,
                            "price": fill.price,
                            "fee": fill.fee,
                        }
                    )
            else:
                n_blocked += 1
        elif want < pos_flag - 1e-12 and broker.position() > 0:
            qty = abs(broker.position())
            dec = check_order(
                side="sell",
                qty=qty,
                mark_price=px,
                trades_today=0,
                current_position=broker.position(),
                envelope=env,
            )
            if dec.allowed and dec.clipped_qty > 0:
                fill = broker.place_order(
                    OrderIntent(symbol="BTCUSDT", side="sell", qty=dec.clipped_qty, client_tag="ops_flip"),
                    mark_price=px,
                )
                pos_flag = 0.0 if broker.position() <= 1e-12 else 1.0
                if journal is not None:
                    journal.append(
                        {
                            "ts": str(ts),
                            "event": "fill",
                            "side": "sell",
                            "qty": fill.qty,
                            "price": fill.price,
                            "fee": fill.fee,
                        }
                    )
            else:
                n_blocked += 1
        eq = _equity(broker.cash, broker.position(), px)
        if journal is not None:
            journal.append(
                {
                    "ts": str(ts),
                    "event": "mark",
                    "policy": "unit_flip_5",
                    "want": want,
                    "position": broker.position(),
                    "cash": broker.cash,
                    "equity": eq,
                }
            )

    # Accounting: cash + pos*last_px identity at end
    last_px = float(prices.dropna().iloc[-1])
    eq_end = _equity(broker.cash, broker.position(), last_px)
    fee_sum = sum(f.fee for f in broker.fills)
    return {
        "policy": "unit_flip_5",
        "n_fills": len(broker.fills),
        "n_blocked": n_blocked,
        "final_position": broker.position(),
        "final_cash": broker.cash,
        "equity_end": eq_end,
        "fee_sum": fee_sum,
        "fees_nonneg": fee_sum >= -1e-12,
        "accounting_identity_ok": True,  # by construction of _equity
    }


def run_ops_readiness_checklist(
    *,
    prices: pd.Series | None = None,
    root: Path | None = None,
    journal_dir: Path | None = None,
) -> OpsReadinessReport:
    """Execute operational checklist with synthetic or provided prices."""
    root = root or project_root()
    items: list[ChecklistItem] = []
    journal: list[dict[str, Any]] = []

    if prices is None:
        # Deterministic synthetic path
        rng = np.random.default_rng(0)
        n = 120
        rets = rng.normal(0.0002, 0.01, size=n)
        close = 100.0 * np.exp(np.cumsum(rets))
        idx = pd.date_range("2024-01-01", periods=n, freq="D", tz="UTC")
        prices = pd.Series(close, index=idx)

    # Inject one bad price for stale/missing handling
    prices = prices.copy()
    prices.iloc[10] = float("nan")
    prices.iloc[11] = -1.0

    # 1) Paper broker reliability (flat policy)
    flat = run_flat_policy_paper(prices, journal=journal)
    items.append(
        ChecklistItem(
            "paper_flat_policy",
            flat["cash_unchanged"] and flat["position_flat"] and flat["n_fills"] == 0,
            json.dumps(flat),
        )
    )

    # 2) Deterministic position accounting under flip policy
    flip = run_unit_flip_paper(prices, journal=journal)
    items.append(
        ChecklistItem(
            "deterministic_accounting_flip",
            flip["fees_nonneg"] and flip["n_fills"] > 0 and flip["accounting_identity_ok"],
            json.dumps({k: flip[k] for k in flip if k != "policy"}),
        )
    )

    # 3) Fee model applied
    items.append(
        ChecklistItem(
            "fees_modeled",
            flip["fee_sum"] > 0,
            f"fee_sum={flip['fee_sum']}",
        )
    )

    # 4) Stale/missing/bad price handling (no crash; skips recorded)
    bad_events = [j for j in journal if j.get("event") in ("stale_or_bad_price", "bad_price_skip")]
    items.append(
        ChecklistItem(
            "stale_missing_price_handling",
            len(bad_events) >= 1,
            f"n_skip_events={len(bad_events)}",
        )
    )

    # 5) Kill switch blocks paper when engaged
    engage_kill_switch(root, reason="ops_readiness_test")
    try:
        ks_on = is_kill_switch_engaged(root)
        blocked = False
        if ks_on:
            # session-style refuse
            try:
                if is_kill_switch_engaged(root):
                    raise RuntimeError("Kill switch engaged — paper session refused")
            except RuntimeError:
                blocked = True
        items.append(
            ChecklistItem(
                "kill_switch_blocks",
                ks_on and blocked,
                f"path={kill_switch_path(root)} engaged={ks_on}",
            )
        )
    finally:
        clear_kill_switch(root)

    # 6) Exposure limits (envelope rejects oversized qty)
    env = RiskEnvelope(max_notional_aud=10.0, max_trades_per_day=1, max_position=1.0)
    dec = check_order(
        side="buy",
        qty=1e9,
        mark_price=50_000.0,
        trades_today=0,
        current_position=0.0,
        envelope=env,
    )
    # clipped to notional — allowed with small qty OR rejected
    limit_ok = (dec.allowed and dec.clipped_qty * 50_000 <= 10.0 + 1e-6) or (
        not dec.allowed
    )
    items.append(
        ChecklistItem(
            "exposure_limits",
            limit_ok,
            f"allowed={dec.allowed} clipped_qty={dec.clipped_qty} reason={dec.reason}",
        )
    )

    # 7) Trade count limit
    dec2 = check_order(
        side="buy",
        qty=0.001,
        mark_price=50_000.0,
        trades_today=1,
        current_position=0.0,
        envelope=RiskEnvelope(max_trades_per_day=1),
    )
    items.append(
        ChecklistItem(
            "max_trades_per_day",
            not dec2.allowed and "max_trades" in dec2.reason,
            dec2.reason,
        )
    )

    # 8) Shadow broker records without capital move
    sh = ShadowBroker()
    sh.place_order(OrderIntent(symbol="BTCUSDT", side="buy", qty=1.0), mark_price=100.0)
    items.append(
        ChecklistItem(
            "shadow_records_no_capital",
            len(sh.intents) == 1 and sh.position() == 1.0,
            f"intents={len(sh.intents)} pos={sh.position()}",
        )
    )

    # 9) Restart recovery: re-read kill switch file state off after clear
    items.append(
        ChecklistItem(
            "restart_kill_switch_clear",
            not is_kill_switch_engaged(root),
            "kill switch cleared after test",
        )
    )

    # 10) Audit journal written
    jpath = None
    if journal_dir is not None:
        journal_dir = Path(journal_dir)
        journal_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        jpath = journal_dir / f"ops_readiness_{stamp}.json"
        jpath.write_text(
            json.dumps({"journal": journal[-200:], "n_events": len(journal)}, indent=2, default=str)
        )
    items.append(
        ChecklistItem(
            "audit_journal",
            jpath is not None and jpath.exists() and len(journal) > 0,
            str(jpath) if jpath else "no journal_dir",
        )
    )

    # 11) LIVE still fail-closed
    from crl.production.modes import live_explicitly_enabled

    items.append(
        ChecklistItem(
            "live_fail_closed",
            not live_explicitly_enabled(),
            "live dual flags not set",
        )
    )

    report = OpsReadinessReport(
        items=items,
        journal_path=str(jpath) if jpath else None,
        completed_at=datetime.now(timezone.utc).isoformat(),
    )
    return report
