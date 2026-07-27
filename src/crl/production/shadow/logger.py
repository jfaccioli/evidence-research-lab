"""Shadow-mode signal logger — records would-be actions without orders."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from crl.production.execution.broker import OrderIntent, ShadowBroker


@dataclass
class ShadowEvent:
    ts: str
    hypothesis_id: str
    signal: float  # desired position 0/1
    mark_price: float
    intent: Optional[dict[str, Any]] = None
    note: str = ""


@dataclass
class ShadowSession:
    hypothesis_id: str
    events: list[ShadowEvent] = field(default_factory=list)
    broker: ShadowBroker = field(default_factory=ShadowBroker)

    def on_bar(
        self,
        *,
        ts: str,
        signal: float,
        mark_price: float,
        symbol: str = "BTCUSDT",
    ) -> ShadowEvent:
        prev = self.broker.position()
        intent_dict = None
        if signal > prev + 1e-12:
            fill = self.broker.place_order(
                OrderIntent(symbol=symbol, side="buy", qty=1.0),
                mark_price=mark_price,
            )
            intent_dict = asdict(fill)
        elif signal < prev - 1e-12:
            fill = self.broker.place_order(
                OrderIntent(symbol=symbol, side="sell", qty=1.0),
                mark_price=mark_price,
            )
            intent_dict = asdict(fill)
        ev = ShadowEvent(
            ts=ts,
            hypothesis_id=self.hypothesis_id,
            signal=float(signal),
            mark_price=float(mark_price),
            intent=intent_dict,
            note="shadow: no exchange order",
        )
        self.events.append(ev)
        return ev

    def write_jsonl(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w") as f:
            for ev in self.events:
                f.write(json.dumps(asdict(ev), default=str) + "\n")
        return path


def new_shadow_log_path(root: Path, hyp_id: str) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return root / "data" / "shadow" / f"shadow_{hyp_id}_{stamp}.jsonl"
