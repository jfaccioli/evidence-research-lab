"""Trading Platform — benchmark engineering tests (not science)."""

from __future__ import annotations

from pathlib import Path

import pytest

import crl.platform  # register benchmarks
from crl.platform.attribution import attribute_vs_buy_and_hold
from crl.platform.benchmarks import all_benchmark_ids
from crl.platform.deployment import deployment_gate
from crl.platform.engine import run_platform_backtest
from crl.platform.strategy import get_strategy, list_strategies
from crl.platform.walkforward import walkforward_strategy
from crl.shared.data.sources.mock import MockOHLCVSource


@pytest.fixture
def ohlcv():
    df = MockOHLCVSource(n=500, seed=21).fetch_ohlcv("BTCUSDT", "1d")
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    return df


def test_benchmarks_registered():
    ids = {m.id for m in list_strategies(benchmarks_only=True)}
    for sid in all_benchmark_ids():
        assert sid in ids
        assert get_strategy(sid).meta.is_benchmark is True
        assert get_strategy(sid).meta.is_scientific_candidate is False


def test_run_all_benchmarks(ohlcv, tmp_path: Path):
    for sid in all_benchmark_ids():
        s = get_strategy(sid)
        res = run_platform_backtest(s, ohlcv, audit_dir=tmp_path)
        assert res.strategy_meta.id == sid
        assert "sharpe_after_cost" in res.metrics
        assert res.audit_path is not None
        assert Path(res.audit_path).exists()
        # desired in [0,1]
        assert float(res.desired.min()) >= 0.0
        assert float(res.desired.max()) <= 1.0


def test_random_control_deterministic(ohlcv):
    a = get_strategy("bench_random_control").desired_position(ohlcv)
    b = get_strategy("bench_random_control").desired_position(ohlcv)
    assert a.equals(b)


def test_deploy_gate_benchmarks_block_live():
    g = deployment_gate(get_strategy("bench_buy_and_hold").meta)
    assert g["allow_paper"] is True
    assert g["allow_live"] is False


def test_walkforward_and_attribution(ohlcv):
    s = get_strategy("bench_tsmom")
    wf = walkforward_strategy(s, ohlcv)
    assert wf["n_folds"] >= 1
    assert wf["scientific_promotion"] == "not_applicable"
    att = attribute_vs_buy_and_hold(s, ohlcv)
    assert "buy_and_hold" in att
    assert att["strategy_id"] == "bench_tsmom"
