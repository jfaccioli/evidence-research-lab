"""Real flow-history ingest (fail-closed until versioned file exists).

Mock never promotes. Place a validated parquet at::

    data/processed/flow/<series_id>.parquet

Required columns: ``flow_time`` (UTC), ``net_flow`` (float).
Optional: run content hash via ``flow_events_content_hash`` after load.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from crl.shared.config import project_root
from crl.shared.data.flow import FlowPITError, flow_events_content_hash, validate_flow_events


def default_flow_dir(root: Path | None = None) -> Path:
    return (root or project_root()) / "data" / "processed" / "flow"


def load_flow_events(
    path: str | Path,
    *,
    allow_nan_flow: bool = False,
) -> pd.DataFrame:
    """Load and validate flow events from parquet or CSV. Fail closed."""
    p = Path(path)
    if not p.exists():
        raise FlowPITError(
            f"flow file not found: {p}. Ingest real history first "
            f"(see data/processed/flow/README.md). Mock is tests-only."
        )
    if p.suffix.lower() in (".parquet", ".pq"):
        df = pd.read_parquet(p)
    elif p.suffix.lower() == ".csv":
        df = pd.read_csv(p)
    else:
        raise FlowPITError(f"unsupported flow file type: {p.suffix}")
    return validate_flow_events(df, allow_nan_flow=allow_nan_flow)


def resolve_flow_series(
    series_id: str,
    *,
    flow_dir: Path | None = None,
) -> tuple[pd.DataFrame, str]:
    """Load ``{flow_dir}/{series_id}.parquet`` and return (events, content_hash)."""
    d = flow_dir or default_flow_dir()
    path = d / f"{series_id}.parquet"
    if not path.exists():
        # also try csv
        csv_path = d / f"{series_id}.csv"
        if csv_path.exists():
            path = csv_path
        else:
            raise FlowPITError(
                f"No real flow series {series_id!r} under {d}. "
                "Do not fall back to mock for science batches."
            )
    ev = load_flow_events(path)
    return ev, flow_events_content_hash(ev)
