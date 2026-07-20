"""Reality Checker — economic/execution plausibility tests."""

from __future__ import annotations

import pandas as pd

from crl.research.backtest.engine import run_backtest
from crl.research.pipeline.run import prepare_frame
from crl.research.reality.checker import run_reality_checks
from crl.research.stats.metrics import compute_metrics
from crl.shared.data.sources.mock import MockOHLCVSource
from crl.shared.types import CostConfig, HypothesisSpec, Metrics, RuleSpec, Taxonomy


def _daily_frame(n: int = 800):
    df = MockOHLCVSource(n=n, seed=7).fetch_ohlcv("BTCUSDT", "1d")
    return prepare_frame(df).dropna(subset=["sma_200", "rvol_20"])


def test_daily_sma_is_human_executable():
    feat = _daily_frame()
    spec = HypothesisSpec(
        id="real_ok",
        timeframe="1d",
        taxonomy=Taxonomy.TREND,
        entry=RuleSpec(expression="close > sma_200"),
        exit=RuleSpec(expression="close < sma_200"),
    )
    costs = CostConfig()
    res = run_backtest(feat, spec, costs)
    m = compute_metrics(res, timeframe="1d")
    rc = run_reality_checks(spec, metrics=m, result=res, df=feat, costs=costs, cfg={})
    assert "Could a human actually have executed this?" in rc.answers
    assert rc.scores.get("human_executable", 0) >= 0.6
    # No hard reject for latency on daily
    assert not any(i.code == "latency" and i.severity == "reject" for i in rc.issues)


def test_subhourly_rejected_as_not_human_executable():
    feat = _daily_frame(400)
    spec = HypothesisSpec(
        id="real_hf",
        timeframe="15m",
        taxonomy=Taxonomy.OTHER,
        entry=RuleSpec(expression="close > sma_50"),
        exit=RuleSpec(expression="close < sma_50"),
    )
    # need sma_50
    costs = CostConfig()
    res = run_backtest(feat.dropna(subset=["sma_50"]), spec, costs)
    m = compute_metrics(res, timeframe="15m")
    rc = run_reality_checks(
        spec, metrics=m, result=res, df=feat, costs=costs, cfg={}
    )
    assert rc.passed is False
    assert any(i.code == "human_exec" for i in rc.issues)


def test_extreme_sharpe_few_trades_flagged():
    spec = HypothesisSpec(
        id="noise",
        timeframe="1d",
        taxonomy=Taxonomy.OTHER,
        entry=RuleSpec(expression="close > 0"),
        exit=RuleSpec(expression="close < 0"),
    )
    m = Metrics(
        n_bars=100,
        n_trades=5,
        sharpe_after_cost=5.0,
        edge_bps_per_trade=800.0,
        avg_trade_return=0.08,
        beta_proxy=0.9,
        excess_return_vs_bh=-0.1,
    )
    empty_res = run_backtest(
        _daily_frame(300),
        HypothesisSpec(
            id="x",
            entry=RuleSpec(expression="close > sma_200"),
            exit=RuleSpec(expression="close < sma_200"),
        ),
        CostConfig(),
    )
    rc = run_reality_checks(
        spec,
        metrics=m,
        result=empty_res,
        df=_daily_frame(300),
        costs=CostConfig(),
        cfg={},
    )
    assert any(i.code == "economic_plausibility" for i in rc.issues)
    assert rc.passed is False  # extreme sharpe + few trades → reject


def test_crowded_sma_warns_publication_decay():
    feat = _daily_frame()
    spec = HypothesisSpec(
        id="crowded",
        timeframe="1d",
        taxonomy=Taxonomy.TREND,
        entry=RuleSpec(expression="close > sma_200"),
        exit=RuleSpec(expression="close < sma_200"),
    )
    costs = CostConfig()
    res = run_backtest(feat, spec, costs)
    m = compute_metrics(res, timeframe="1d")
    rc = run_reality_checks(spec, metrics=m, result=res, df=feat, costs=costs, cfg={})
    assert any(i.code == "publication_decay" for i in rc.issues)
