"""Chronological train/val/test and walk-forward splits."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from crl.shared.types import SplitConfig


@dataclass
class HoldoutSplit:
    train: pd.DataFrame
    val: pd.DataFrame
    test: pd.DataFrame


@dataclass
class WFFold:
    fold_id: int
    train: pd.DataFrame
    val: pd.DataFrame


def chronological_split(df: pd.DataFrame, cfg: SplitConfig) -> HoldoutSplit:
    n = len(df)
    if n < 50:
        raise ValueError(f"Not enough bars for split: {n}")
    t = int(n * cfg.train_frac)
    v = int(n * cfg.val_frac)
    # remainder to test
    train = df.iloc[:t]
    val = df.iloc[t : t + v]
    test = df.iloc[t + v :]
    if len(test) < 10:
        raise ValueError("Test set too small; adjust fractions or fetch more data")
    return HoldoutSplit(train=train, val=val, test=test)


def walk_forward_folds(df: pd.DataFrame, cfg: SplitConfig) -> list[WFFold]:
    """Rolling walk-forward on the train+val region only (never test)."""
    folds: list[WFFold] = []
    n = len(df)
    tr, va, step = cfg.wf_train_bars, cfg.wf_val_bars, cfg.wf_step_bars
    if tr + va > n:
        # shrink for short series (e.g. unit tests)
        tr = max(30, n // 2)
        va = max(10, n // 5)
        step = max(5, va // 2)
    start = 0
    fold_id = 0
    while start + tr + va <= n:
        train = df.iloc[start : start + tr]
        val = df.iloc[start + tr : start + tr + va]
        folds.append(WFFold(fold_id=fold_id, train=train, val=val))
        fold_id += 1
        start += step
    if not folds:
        # single fold fallback
        mid = int(n * 0.7)
        folds.append(WFFold(fold_id=0, train=df.iloc[:mid], val=df.iloc[mid:]))
    return folds
