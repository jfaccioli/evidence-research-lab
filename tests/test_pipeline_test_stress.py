"""B3 pipeline-level: final confirmatory gate must use test-slice 2× stress."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest
import yaml

from crl.research.backtest.engine import BacktestResult
from crl.research.pipeline import run as run_mod
from crl.risk.promotion import GateResult
from crl.shared.types import (
    HypothesisSpec,
    Metrics,
    ResearchMode,
    RuleSpec,
    Taxonomy,
)


def _mini_df(n: int = 80) -> pd.DataFrame:
    idx = pd.date_range("2018-01-01", periods=n, freq="1D", tz="UTC")
    rng = np.random.default_rng(0)
    close = 100 * np.exp(np.cumsum(rng.normal(0.0005, 0.01, n)))
    open_ = np.concatenate([[close[0]], close[:-1]])
    return pd.DataFrame(
        {
            "open": open_,
            "high": np.maximum(open_, close) * 1.001,
            "low": np.minimum(open_, close) * 0.999,
            "close": close,
            "volume": np.full(n, 1e6),
            "sma_20": pd.Series(close).rolling(5, min_periods=1).mean().values,
            "sma_200": pd.Series(close).rolling(5, min_periods=1).mean().values,
            "rvol_20": 0.2,
            "rvol_20_exp_median": 0.25,
            "rvol_below_median": 1.0,
            "regime": "bull_low_vol",
        },
        index=idx,
    )


def _result(df: pd.DataFrame, *, stress: bool, slice_tag: str) -> BacktestResult:
    n = len(df)
    # mild positive path
    r = np.full(n, 0.001 if not stress else -0.02)
    if stress and slice_tag == "test":
        r = np.full(n, -0.05)  # strong loss under 2× costs on test
    elif stress and slice_tag == "val":
        r = np.full(n, 0.0005)  # still positive stress on val
    w = 1.0
    eq = []
    for x in r:
        w *= 1.0 + x
        eq.append(w)
    return BacktestResult(
        equity=pd.Series(eq, index=df.index),
        position=pd.Series(1.0, index=df.index),
        trades=[],
        bar_returns=pd.Series(r, index=df.index),
        signals=pd.Series(1.0, index=df.index),
        initial_equity=1.0,
        meta={"stress": stress, "slice_tag": slice_tag},
    )


def test_pipeline_confirmatory_uses_test_stress_not_val(tmp_path: Path, monkeypatch):
    """
    Prove final pipeline failure uses test-slice 2× stress:
    - validation stress Sharpe > 0
    - base-cost test metrics would pass primary thresholds if stress ignored
    - test-slice 2× stress Sharpe < 0
    - final status fails because stress_sharpe from test was used
    """
    root = tmp_path / "proj"
    (root / "configs").mkdir(parents=True)
    (root / "registry").mkdir()
    (root / "reports").mkdir()
    (root / "data" / "processed" / "features").mkdir(parents=True)
    (root / "data" / "manifests").mkdir(parents=True)
    (root / "journal").mkdir()
    cfg = {
        "asset": "BTC/USDT",
        "symbol_binance": "BTCUSDT",
        "costs": {
            "fee_bps_per_side": 10.0,
            "half_spread_bps": 0.0,
            "slippage_bps_per_side": 0.0,
            "stress_multiplier": 2.0,
        },
        "splits": {
            "train_frac": 0.5,
            "val_frac": 0.25,
            "test_frac": 0.25,
            "wf_train_bars": 20,
            "wf_val_bars": 10,
            "wf_step_bars": 5,
        },
        "gates": {
            "primary_metric": "sharpe_after_cost",
            "min_trades": 1,
            "sharpe_min": 0.0,
            "max_drawdown": 0.99,
            "overfit_gap_max": 99.0,
            "wf_min_positive_fold_frac": 0.0,
            "bootstrap_ci_lower_sharpe_min": -99.0,
            "skeptical_p_mean_trade_gt0_min": 0.0,
            "mc_max_dd_breach_frac": 1.0,
            "fragility_min_pass_frac": 0.0,
            "regime_concentration_warn": 1.0,
            "research_budget_confirmatory_per_month": 100,
        },
        "stats": {"bootstrap_n": 20, "bootstrap_block_size": 3, "mc_n": 20, "seed": 0,
                  "annualization_1d": 365},
        "registry": {"path": "registry/crl.sqlite"},
        "reporting": {"dir": "reports"},
        "journal": {"path": "journal/RESEARCH_JOURNAL.md"},
        "data": {
            "cache_dir": "data/processed",
            "manifest_dir": "data/manifests",
            "min_trust_score": 0.0,
        },
        "risk": {"max_position": 1.0, "min_position": 0.0, "max_leverage": 1.0,
                 "allow_short": False, "allow_derivatives": False},
        "reality": {"capital_aud": 50.0},
    }
    (root / "configs" / "default.yaml").write_text(yaml.safe_dump(cfg))

    df = _mini_df(80)
    # freeze split lengths
    n = len(df)
    train_n, val_n = n // 2, n // 4

    captured: dict = {"stress_args": []}

    def fake_project_root():
        return root

    def fake_load_or_build_features(ohlcv, *, dataset_id, cache_dir, force=False):
        return ohlcv

    def fake_run_backtest(frame, spec, costs, stress=False, initial_equity=1.0):
        # Tag slice by position in chronological frame via length relative to full
        # holdout slices have different lengths
        tag = "unknown"
        if len(frame) == val_n or (
            len(frame) > 10 and len(frame) < train_n
        ):
            # crude: val is middle-sized
            tag = "val" if abs(len(frame) - val_n) <= abs(len(frame) - (n - train_n - val_n)) else "test"
        if len(frame) == n - train_n - val_n or len(frame) == n - train_n - val_n:
            tag = "test"
        # Better: mark using first index
        if frame.index[0] == df.index[train_n]:
            tag = "val"
        elif frame.index[0] == df.index[train_n + val_n]:
            tag = "test"
        elif frame.index[0] == df.index[0] and len(frame) <= train_n + 5:
            tag = "train"
        else:
            # WF folds etc.
            tag = "other"
        return _result(frame, stress=stress, slice_tag=tag)

    def fake_compute_metrics(result, **kwargs):
        stress = bool(result.meta.get("stress"))
        tag = result.meta.get("slice_tag", "other")
        sharpe = 1.0
        if stress and tag == "val":
            sharpe = 0.5  # positive val stress
        if stress and tag == "test":
            sharpe = -0.4  # negative test stress — must drive failure
        if not stress and tag == "test":
            sharpe = 0.8  # base test looks fine
        if not stress and tag == "val":
            sharpe = 0.9
        if not stress and tag == "train":
            sharpe = 0.7
        return Metrics(
            n_bars=len(result.bar_returns),
            n_trades=40,
            total_return=float(result.total_return),
            cagr=0.1,
            volatility=0.2,
            sharpe_after_cost=sharpe,
            sortino=0.5,
            calmar=0.2,
            max_drawdown=0.2,
            time_underwater_frac=0.2,
            turnover=5.0,
            avg_trade_return=0.01,
            avg_hold_bars=3.0,
            edge_bps_per_trade=10.0,
            excess_return_vs_bh=0.0,
            ir_vs_bh=0.0,
            beta_proxy=0.5,
        )

    real_eval = run_mod.evaluate_gates

    def spy_evaluate_gates(metrics, gates, **kwargs):
        captured["stress_args"].append(
            {
                "confirmatory": kwargs.get("confirmatory"),
                "stress_sharpe": kwargs.get("stress_sharpe"),
                "sharpe": metrics.sharpe_after_cost,
            }
        )
        return real_eval(metrics, gates, **kwargs)

    # Loose bootstrap etc. via patched stats
    def fake_boot(*a, **k):
        class B:
            sharpe_point = 0.5
            sharpe_ci = (0.1, 1.0)
            mean_bar_ci = (0.0, 0.01)
            p_mean_gt_0_skeptical = 0.9
            n_effective_hint = 50.0
            ann_factor = 365.0
            n_bars = 20

        return B()

    def fake_mc(*a, **k):
        class M:
            terminal_mean = 1.0
            terminal_p5 = 0.9
            terminal_p50 = 1.0
            max_dd_mean = 0.1
            max_dd_p95 = 0.2
            frac_dd_breach = 0.0
            frac_underperform_bh = 0.0

        return M()

    def fake_sens(*a, **k):
        class S:
            n_tested = 3
            n_pass = 3
            pass_frac = 1.0
            neighbors = []
            mode = "none"

        return S()

    def fake_reality(*a, **k):
        class R:
            passed = True
            reject_reasons = []
            warnings = []
            answers = {}

            def to_dict(self):
                return {"passed": True, "answers": {}, "issues": [], "reject_reasons": [], "warnings": []}

        return R()

    def fake_mt(*a, **k):
        class MT:
            n_family = 1
            n_global = 1
            n_trials_display = 1
            bonferroni_alpha = 0.05
            approx_null_selection_proxy = 0.9
            passes_bonferroni_hint = True  # force path past MT to isolate stress
            trials_ambiguous = False
            trial_history_complete = True
            definition = "test"
            note = "test override"
            sharpe_period = 0.1
            sharpe_annualized = 1.0
            se_period = 0.1
            se_annualized = 1.0
            deflated_sharpe = 0.9  # legacy attr unused

        return MT()

    monkeypatch.setattr(run_mod, "project_root", fake_project_root)
    monkeypatch.setattr(run_mod, "load_or_build_features", fake_load_or_build_features)
    monkeypatch.setattr(run_mod, "run_backtest", fake_run_backtest)
    monkeypatch.setattr(run_mod, "buy_and_hold", lambda df, costs, **kw: _result(df, stress=False, slice_tag="bh"))
    monkeypatch.setattr(run_mod, "always_cash", lambda df: _result(df, stress=False, slice_tag="cash"))
    monkeypatch.setattr(run_mod, "sma_crossover_baseline", lambda df, costs, **kw: _result(df, stress=False, slice_tag="sma"))
    monkeypatch.setattr(run_mod, "compute_metrics", fake_compute_metrics)
    monkeypatch.setattr(run_mod, "evaluate_gates", spy_evaluate_gates)
    monkeypatch.setattr(run_mod, "bootstrap_bar_sharpe", fake_boot)
    monkeypatch.setattr(run_mod, "trade_sequence_mc", fake_mc)
    monkeypatch.setattr(run_mod, "sma_neighborhood_sensitivity", fake_sens)
    monkeypatch.setattr(run_mod, "run_reality_checks", fake_reality)
    monkeypatch.setattr(run_mod, "evaluate_multiple_testing", fake_mt)
    monkeypatch.setattr(run_mod, "assert_hypothesis_admissible", lambda s: None)

    from crl.shared.types import DataManifest

    manifest = DataManifest(
        dataset_id="toy",
        source="mock",
        symbol="BTCUSDT",
        interval="1d",
        start=str(df.index[0]),
        end=str(df.index[-1]),
        row_count=len(df),
        sha256="0" * 64,
        trust_score=0.99,
        fetched_at="2020-01-01",
        path=str(tmp_path / "x.parquet"),
    )

    spec = HypothesisSpec(
        id="hyp_stress_pipeline",
        version=1,
        taxonomy=Taxonomy.TREND,
        entry=RuleSpec(expression="close > sma_20"),
        exit=RuleSpec(expression="close < sma_20"),
        rationale="Pipeline isolation test for confirmatory test-slice 2x cost stress wiring.",
        expected_outcome="Must fail confirmatory due to test stress sharpe < 0.",
    )

    out = run_mod.run_hypothesis_pipeline(
        spec,
        cfg,
        dataset_id="toy",
        mode=ResearchMode.CONFIRMATORY,
        df=df,
        manifest=manifest,
    )

    # Find confirmatory gate call
    conf_calls = [c for c in captured["stress_args"] if c["confirmatory"] is True]
    val_calls = [c for c in captured["stress_args"] if c["confirmatory"] is False]
    assert val_calls, "expected exploratory/val gate call"
    assert conf_calls, "expected confirmatory gate call"

    val_stress = val_calls[-1]["stress_sharpe"]
    test_stress = conf_calls[-1]["stress_sharpe"]
    assert val_stress is not None and val_stress > 0, "validation stress should be positive"
    assert conf_calls[-1]["sharpe"] > 0, "base-cost test sharpe should look passable"
    assert test_stress is not None and test_stress < 0, "test-slice 2x stress must be negative"
    assert test_stress != val_stress or test_stress < 0

    assert out["final_status"] in ("failed_test", "failed_val")
    # Specifically failed confirmatory path using test stress
    assert out["final_status"] == "failed_test"
    assert any("2x cost" in r for r in out["gates"]["reasons"])
    # Prove the stress value on the final gate was the test one, not val
    assert abs(out["stats"]["stress_sharpe"] - test_stress) < 1e-9
    assert out["stats"]["stress_sharpe"] < 0
    assert out["stats"]["stress_sharpe_val"] > 0
