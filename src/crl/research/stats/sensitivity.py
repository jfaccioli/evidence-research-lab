"""Parameter neighborhood fragility — fail-closed when no params to stress."""

from __future__ import annotations

import re
from dataclasses import dataclass

import pandas as pd

from crl.research.backtest.engine import run_backtest
from crl.research.stats.metrics import compute_metrics
from crl.shared.types import CostConfig, GateConfig, HypothesisSpec, RuleSpec


@dataclass
class SensitivityResult:
    n_tested: int
    n_pass: int
    pass_frac: float | None  # None = not applicable / inconclusive
    neighbors: list[dict]
    mode: str  # "sma_neighborhood" | "numeric_literals" | "none"


_SMA_RE = re.compile(r"(?<![A-Za-z0-9_])sma_(\d+)(?!\d)")
_NUM_RE = re.compile(r"(?<![A-Za-z0-9_])(-?\d+\.?\d*)(?!\w)")


def _swap_sma(expr: str, old: int, new: int) -> str:
    pattern = re.compile(rf"(?<![A-Za-z0-9_])sma_{old}(?!\d)")
    return pattern.sub(f"sma_{new}", expr)


def sma_neighborhood_sensitivity(
    df: pd.DataFrame,
    spec: HypothesisSpec,
    costs: CostConfig,
    gates: GateConfig,
    *,
    center_window: int | None = None,
    deltas: tuple[int, ...] = (-40, -20, 0, 20, 40),
    timeframe: str = "1d",
) -> SensitivityResult:
    """Neighborhood tests. Fail-closed: pass_frac is None if no tunables found."""
    text = spec.entry.expression + " " + spec.exit.expression
    found = _SMA_RE.findall(text)
    if found:
        w = center_window or max(int(x) for x in found)
        neighbors = []
        n_pass = 0
        work = df
        for d in deltas:
            nw = w + d
            if nw < 10:
                continue
            col = f"sma_{nw}"
            if col not in work.columns:
                work = work.copy()
                work[col] = work["close"].rolling(nw, min_periods=nw).mean()
            entry = _swap_sma(spec.entry.expression, w, nw)
            exit_ = _swap_sma(spec.exit.expression, w, nw)
            hyp = spec.model_copy(
                update={
                    "id": f"{spec.id}_sma{nw}",
                    "entry": RuleSpec(expression=entry),
                    "exit": RuleSpec(expression=exit_),
                }
            )
            res = run_backtest(work, hyp, costs)
            m = compute_metrics(res, timeframe=timeframe)
            ok = (
                m.n_trades >= max(5, gates.min_trades // 3)
                and m.sharpe_after_cost >= gates.sharpe_min
            )
            if ok:
                n_pass += 1
            neighbors.append(
                {
                    "sma": nw,
                    "sharpe": m.sharpe_after_cost,
                    "n_trades": m.n_trades,
                    "max_dd": m.max_drawdown,
                    "pass": ok,
                }
            )
        n = len(neighbors)
        return SensitivityResult(
            n_tested=n,
            n_pass=n_pass,
            pass_frac=(n_pass / n) if n else None,
            neighbors=neighbors,
            mode="sma_neighborhood",
        )

    # Try numeric literal neighborhoods (thresholds)
    nums = []
    for m in _NUM_RE.finditer(text):
        try:
            v = float(m.group(1))
        except ValueError:
            continue
        # skip pure 0/1 flags often used as booleans in rules
        if abs(v) in (0.0, 1.0) and "." not in m.group(1):
            continue
        nums.append(v)
    if nums:
        # perturb the largest-magnitude threshold
        target = max(nums, key=lambda x: abs(x))
        neighbors = []
        n_pass = 0
        for scale in (0.8, 0.9, 1.0, 1.1, 1.2):
            new_v = target * scale if target != 0 else scale
            # replace first occurrence of target string carefully
            t_str = str(int(target)) if float(target).is_integer() else str(target)

            def _repl_once(expr: str) -> str:
                return expr.replace(t_str, _fmt(new_v), 1)

            entry = _repl_once(spec.entry.expression)
            exit_ = _repl_once(spec.exit.expression)
            hyp = spec.model_copy(
                update={
                    "id": f"{spec.id}_ thr{scale}",
                    "entry": RuleSpec(expression=entry),
                    "exit": RuleSpec(expression=exit_),
                }
            )
            try:
                res = run_backtest(df, hyp, costs)
                m = compute_metrics(res, timeframe=timeframe)
            except Exception:
                continue
            ok = (
                m.n_trades >= max(5, gates.min_trades // 3)
                and m.sharpe_after_cost >= gates.sharpe_min
            )
            if ok:
                n_pass += 1
            neighbors.append(
                {
                    "scale": scale,
                    "threshold": new_v,
                    "sharpe": m.sharpe_after_cost,
                    "n_trades": m.n_trades,
                    "pass": ok,
                }
            )
        n = len(neighbors)
        return SensitivityResult(
            n_tested=n,
            n_pass=n_pass,
            pass_frac=(n_pass / n) if n else None,
            neighbors=neighbors,
            mode="numeric_literals",
        )

    # Fail-closed: no neighborhood → cannot claim robustness
    return SensitivityResult(
        n_tested=0,
        n_pass=0,
        pass_frac=None,
        neighbors=[],
        mode="none",
    )


def _fmt(v: float) -> str:
    if abs(v - round(v)) < 1e-9:
        return str(int(round(v)))
    return f"{v:.6g}"
