"""Resolve programme-attached PIT series for research batches.

Capability: when a new dataset lands under data/processed/{flow,external}/,
a locked programme can run explor+conf without ad-hoc scripts.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import pandas as pd

from crl.ops.programme_index import ExternalAttach, ProgrammeIndex
from crl.shared.config import project_root
from crl.shared.data.external_series import (
    external_events_hash,
    validate_external_events,
)
from crl.shared.data.flow import flow_events_content_hash, validate_flow_events
from crl.shared.data.sources.flow_ingest import resolve_flow_series


class SeriesAttachError(RuntimeError):
    pass


def series_dirs(root: Path | None = None) -> dict[str, Path]:
    root = root or project_root()
    return {
        "flow": root / "data" / "processed" / "flow",
        "external": root / "data" / "processed" / "external",
    }


def list_local_series() -> list[dict[str, Any]]:
    """Inventory pinned series parquet + meta on disk."""
    out: list[dict[str, Any]] = []
    for kind, d in series_dirs().items():
        if not d.exists():
            continue
        for p in sorted(d.glob("*.parquet")):
            meta_path = p.with_suffix(".meta.json")
            meta: dict[str, Any] = {}
            if meta_path.exists():
                import json

                try:
                    meta = json.loads(meta_path.read_text())
                except Exception:
                    meta = {}
            out.append(
                {
                    "kind": kind,
                    "series_id": p.stem,
                    "path": str(p),
                    "has_meta": meta_path.exists(),
                    "n_events": meta.get("n_events") or meta.get("n"),
                    "content_hash": (meta.get("content_hash") or meta.get("hash") or "")[
                        :16
                    ]
                    or None,
                }
            )
    return out


def load_flow_events(series_id: str, path: str | None = None) -> tuple[pd.DataFrame, str]:
    if path:
        p = Path(path)
        if not p.is_absolute():
            p = project_root() / p
        df = pd.read_parquet(p) if p.suffix == ".parquet" else pd.read_csv(p)
        # normalize columns
        if "flow_time" not in df.columns and "event_time" in df.columns:
            df = df.rename(columns={"event_time": "flow_time"})
        if "net_flow" not in df.columns and "value" in df.columns:
            df = df.rename(columns={"value": "net_flow"})
        ev = validate_flow_events(df)
        return ev, flow_events_content_hash(ev)
    return resolve_flow_series(series_id)


def load_external_events(
    series_id: str, path: str | None = None
) -> tuple[pd.DataFrame, str]:
    if path:
        p = Path(path)
        if not p.is_absolute():
            p = project_root() / p
    else:
        p = series_dirs()["external"] / f"{series_id}.parquet"
    if not p.exists():
        raise SeriesAttachError(
            f"external series not found: {p}. Place parquet with event_time,value "
            f"or set external.path in INDEX.yaml"
        )
    df = pd.read_parquet(p) if p.suffix == ".parquet" else pd.read_csv(p)
    if "event_time" not in df.columns and "flow_time" in df.columns:
        df = df.rename(columns={"flow_time": "event_time"})
    if "value" not in df.columns and "net_flow" in df.columns:
        df = df.rename(columns={"net_flow": "value"})
    ev = validate_external_events(df)
    return ev, external_events_hash(ev)


def resolve_attach(att: ExternalAttach) -> dict[str, Any]:
    """Return kwargs for run_batch / run_hypothesis_pipeline."""
    if att.kind == "flow":
        ev, h = load_flow_events(att.series_id, att.path)
        return {
            "flow_events": ev,
            "flow_series_id": att.series_id,
            "series_content_hash": h,
            "attach_kind": "flow",
        }
    if att.kind == "external":
        ev, h = load_external_events(att.series_id, att.path)
        return {
            "external_events": ev,
            "external_series_id": att.series_id,
            "external_prefix": att.prefix,
            "series_content_hash": h,
            "attach_kind": "external",
        }
    raise SeriesAttachError(f"unknown kind {att.kind}")


def series_readiness(att: ExternalAttach | None) -> dict[str, Any]:
    """Checklist for whether a programme can run with its series."""
    if att is None:
        return {
            "ready": True,
            "mode": "ohlcv_only",
            "checks": {"no_external_required": True},
            "message": "Programme uses OHLCV-only features",
        }
    checks: dict[str, Any] = {}
    try:
        resolved = resolve_attach(att)
        n = len(
            resolved.get("flow_events")
            if att.kind == "flow"
            else resolved.get("external_events")
        )
        checks["series_loadable"] = True
        checks["n_events"] = n
        checks["n_events_ge_180"] = n >= 180
        checks["content_hash_present"] = bool(resolved.get("series_content_hash"))
        ready = checks["series_loadable"] and checks["n_events_ge_180"]
        msg = (
            f"Series {att.series_id} ready (n={n})"
            if ready
            else f"Series {att.series_id} short or missing (n={n})"
        )
        return {
            "ready": ready,
            "mode": att.kind,
            "series_id": att.series_id,
            "checks": checks,
            "content_hash": resolved.get("series_content_hash"),
            "message": msg,
        }
    except Exception as e:
        return {
            "ready": False,
            "mode": att.kind,
            "series_id": att.series_id,
            "checks": {"series_loadable": False, "error": str(e)},
            "message": str(e),
        }


def maybe_window_dataset(
    idx: ProgrammeIndex,
    events: pd.DataFrame,
    time_col: str,
    *,
    base_dataset_id: str,
    config_path: str | None = None,
) -> str:
    """If window_from_series, pin truncated OHLCV for fair val under short series."""
    if not idx.window_from_series:
        return base_dataset_id
    from crl.shared.config import load_config
    from crl.shared.data.store import load_dataset, save_dataset

    root = project_root()
    cfg = load_config(config_path)
    ohlcv, _ = load_dataset(
        base_dataset_id,
        manifest_dir=root / cfg["data"]["manifest_dir"],
        verify_hash=True,
    )
    t0 = pd.to_datetime(events[time_col].iloc[0], utc=True) - pd.Timedelta(
        days=int(idx.window_burn_in_days)
    )
    ohlcv2 = ohlcv.loc[ohlcv.index >= t0].copy()
    if len(ohlcv2) < 200:
        raise SeriesAttachError(
            f"windowed dataset too short ({len(ohlcv2)} bars); need longer series"
        )
    man = save_dataset(
        ohlcv2,
        source=f"window_{idx.name}",
        symbol=idx.dataset_symbol,
        interval=idx.dataset_interval,
        processed_dir=root / cfg["data"]["cache_dir"],
        manifest_dir=root / cfg["data"]["manifest_dir"],
        source_class="binance_public",
    )
    return man.dataset_id
