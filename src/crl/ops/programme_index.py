"""Load programme INDEX.yaml (self-describing locks + optional series attach)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml

from crl.shared.config import project_root


@dataclass
class ExternalAttach:
    """How a programme attaches a PIT series for batch/confirmatory."""

    kind: str  # flow | external
    series_id: str
    prefix: str = "xser"
    path: Optional[str] = None
    # optional ingest hints (not auto-paid)
    source: Optional[str] = None  # parquet | cmd_url | polymarket_token
    source_url: Optional[str] = None
    token_id: Optional[str] = None
    publish_lag_days: int = 1


@dataclass
class ProgrammeIndex:
    name: str
    hyp_dir: Path
    design: Optional[str] = None
    live_data: bool = False
    hypotheses: list[str] = field(default_factory=list)
    external: Optional[ExternalAttach] = None
    dataset_symbol: str = "BTCUSDT"
    dataset_interval: str = "1d"
    window_from_series: bool = False
    window_burn_in_days: int = 120
    raw: dict[str, Any] = field(default_factory=dict)


def load_programme_index(hyp_dir: Path | str) -> ProgrammeIndex:
    root = project_root()
    hyp_dir = Path(hyp_dir)
    if not hyp_dir.is_absolute():
        hyp_dir = root / hyp_dir
    path = hyp_dir / "INDEX.yaml"
    if not path.exists():
        # minimal index from directory
        hyps = sorted(p.name for p in hyp_dir.glob("hyp_*.yaml"))
        return ProgrammeIndex(name=hyp_dir.name, hyp_dir=hyp_dir, hypotheses=hyps)
    raw = yaml.safe_load(path.read_text()) or {}
    ext = None
    if raw.get("external") or raw.get("series"):
        e = raw.get("external") or raw.get("series") or {}
        ext = ExternalAttach(
            kind=str(e.get("kind") or "external").strip().lower(),
            series_id=str(e.get("series_id") or e.get("id") or "").strip(),
            prefix=str(e.get("prefix") or "xser").strip(),
            path=e.get("path"),
            source=e.get("source"),
            source_url=e.get("source_url") or e.get("url"),
            token_id=e.get("token_id"),
            publish_lag_days=int(e.get("publish_lag_days") or 1),
        )
        if not ext.series_id:
            raise ValueError(f"{path}: external.series_id required when external set")
        if ext.kind not in ("flow", "external"):
            raise ValueError(f"{path}: external.kind must be flow|external, got {ext.kind}")
    ds = raw.get("dataset") or {}
    hyps = list(raw.get("hypotheses") or [])
    if not hyps:
        hyps = sorted(p.name for p in hyp_dir.glob("hyp_*.yaml"))
    return ProgrammeIndex(
        name=str(raw.get("programme") or hyp_dir.name),
        hyp_dir=hyp_dir,
        design=raw.get("design"),
        live_data=bool(raw.get("live_data", False)),
        hypotheses=hyps,
        external=ext,
        dataset_symbol=str(ds.get("symbol") or raw.get("symbol") or "BTCUSDT"),
        dataset_interval=str(ds.get("interval") or "1d"),
        window_from_series=bool(ds.get("window_from_series") or raw.get("window_from_series")),
        window_burn_in_days=int(ds.get("window_burn_in_days") or 120),
        raw=raw,
    )
