"""Shared LEDA helpers — keep tiny."""

from __future__ import annotations

import hashlib
import json
from typing import Any

import numpy as np
import pandas as pd


def payload_hash(obj: dict[str, Any]) -> str:
    raw = json.dumps(obj, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:32]


def roll_percentile_rank(s: pd.Series, w: int) -> pd.Series:
    """Causal rolling percentile rank of the last finite value in each window."""
    vals = s.to_numpy(dtype=float)
    out = np.full(len(vals), np.nan)
    min_need = max(5, w // 3)
    for i in range(len(vals)):
        if i + 1 < w or np.isnan(vals[i]):
            continue
        window = vals[i - w + 1 : i + 1]
        window = window[~np.isnan(window)]
        if len(window) < min_need:
            continue
        last = window[-1]
        out[i] = float(np.mean(window <= last))
    return pd.Series(out, index=s.index)
