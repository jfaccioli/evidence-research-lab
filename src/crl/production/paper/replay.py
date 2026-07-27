"""Batch historical paper replay for a hyp directory (no exchange)."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Optional

import pandas as pd

from crl.production.paper.session import PaperSessionResult, run_paper_session
from crl.research.pipeline.batch import load_hypothesis_yaml
from crl.shared.data.feature_store import load_or_build_features
from crl.shared.types import HypothesisSpec


def replay_hyp_dir(
    hyp_dir: Path,
    features: pd.DataFrame,
    *,
    starting_cash: float = 50.0,
    fee_bps_rt: float = 33.0,
    journal_dir: Path | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Run paper sessions for each hyp_*.yaml; return summary rows."""
    paths = sorted(hyp_dir.glob("hyp_*.yaml"))
    if limit is not None:
        paths = paths[:limit]
    rows: list[dict[str, Any]] = []
    for path in paths:
        spec = load_hypothesis_yaml(path)
        res = run_paper_session(
            spec,
            features,
            starting_cash=starting_cash,
            fee_bps_rt=fee_bps_rt,
            journal_dir=journal_dir,
        )
        rows.append(_row(res))
    return rows


def _row(res: PaperSessionResult) -> dict[str, Any]:
    ret = None
    if res.equity_end is not None and res.starting_cash:
        ret = res.equity_end / res.starting_cash - 1.0
    return {
        "hypothesis_id": res.hypothesis_id,
        "n_bars": res.n_bars,
        "n_fills": res.n_fills,
        "starting_cash": res.starting_cash,
        "equity_end": res.equity_end,
        "total_return": ret,
        "final_position": res.final_position,
        "journal_path": res.journal_path,
    }


def write_replay_summary(rows: list[dict[str, Any]], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"n": len(rows), "results": rows}, indent=2, default=str))
    return path
