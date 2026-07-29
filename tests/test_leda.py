"""LEDA-0 contracts, LEDA-1/2 channels, LEDA-3 stack."""

from __future__ import annotations

import pandas as pd
import pytest

from crl.leda.channels.trend import (
    CHANNEL_ID as TREND_ID,
    build_trend_evidence,
    evaluate_trend_forecast_skill,
)
from crl.leda.channels.vol_risk import (
    CHANNEL_ID as VOL_ID,
    build_vol_risk_evidence,
    evaluate_vol_forecast_skill,
)
from crl.leda.layers import portfolio_long_only_unit, risk_from_vol_score
from crl.leda.protocol import protocol_summary, validate_evidence_frame
from crl.leda.stack import decide_bar
from crl.leda.types import EvidenceRecord, EvidenceSink
from crl.shared.data.sources.mock import MockOHLCVSource


def _mock_ohlcv(n: int = 400, seed: int = 7):
    ohlcv = MockOHLCVSource(n=n, seed=seed).fetch_ohlcv("BTCUSDT", "1d")
    if ohlcv.index.tz is None:
        ohlcv.index = ohlcv.index.tz_localize("UTC")
    return ohlcv


def test_evidence_record_bounds():
    EvidenceRecord(
        channel_id="x",
        version=1,
        sink=EvidenceSink.RISK,
        asof_time="2020-01-01",
        score=0.5,
        inputs_hash="abc",
    )
    with pytest.raises(ValueError):
        EvidenceRecord(
            channel_id="x",
            version=1,
            sink=EvidenceSink.RISK,
            asof_time="2020-01-01",
            score=1.5,
            inputs_hash="abc",
        )


def test_protocol_summary_has_four_layers():
    s = protocol_summary()
    assert set(s["layers"]) == {"forecast", "risk", "portfolio", "execution"}


def test_vol_risk_channel_pit_and_skill():
    ohlcv = _mock_ohlcv()
    ev = build_vol_risk_evidence(ohlcv, rv_window=20, rank_window=60)
    assert "score" in ev.columns
    assert ev["score"].notna().sum() > 50
    assert pd.isna(ev["rv_next"].iloc[-1])
    skill = evaluate_vol_forecast_skill(ev, min_points=50)
    assert skill["ok"] is True
    assert skill["channel_id"] == VOL_ID
    assert skill["pearson_score_vs_rv_lag"] > 0.5
    validate_evidence_frame(
        ev.dropna(subset=["score"]),
        channel_id=VOL_ID,
        version=1,
        sink=EvidenceSink.RISK,
    )


def test_trend_channel_pit_and_skill():
    ohlcv = _mock_ohlcv(n=500, seed=3)
    ev = build_trend_evidence(ohlcv, mom_lookback=20, rank_window=60)
    assert ev["score"].notna().sum() > 50
    # Forward return unknown on last bar
    assert pd.isna(ev["fwd_ret"].iloc[-1])
    # Score uses lagged mom only: first bars before lookback+rank are NaN
    assert pd.isna(ev["score"].iloc[0])
    skill = evaluate_trend_forecast_skill(ev, min_points=50)
    assert skill["ok"] is True
    assert skill["channel_id"] == TREND_ID
    assert skill["n"] >= 50
    validate_evidence_frame(
        ev.dropna(subset=["score"]),
        channel_id=TREND_ID,
        version=1,
        sink=EvidenceSink.FORECAST,
    )


def test_risk_veto_and_portfolio_unit():
    r = risk_from_vol_score(
        asof_time="t", e_risk=0.9, veto_threshold=0.85, inputs_hash="h"
    )
    assert r.payload["veto"] is True
    p = portfolio_long_only_unit(
        asof_time="t",
        want_long=True,
        risk_veto=True,
        inputs_hash="h",
    )
    assert p.payload["target_position"] == 0.0
    p2 = portfolio_long_only_unit(
        asof_time="t",
        want_long=True,
        risk_veto=False,
        inputs_hash="h",
    )
    assert p2.payload["target_position"] == 1.0


def test_decide_bar_long_and_veto():
    long_ok = decide_bar(
        asof_time="t1",
        e_forecast=0.7,
        e_risk=0.2,
        mode="paper",
    )
    assert long_ok["want_long"] is True
    assert long_ok["risk_veto"] is False
    assert long_ok["target_position"] == 1.0
    assert long_ok["layers"]["execution"]["payload"]["places_live_orders"] is False

    vetoed = decide_bar(asof_time="t2", e_forecast=0.9, e_risk=0.9)
    assert vetoed["want_long"] is True
    assert vetoed["risk_veto"] is True
    assert vetoed["target_position"] == 0.0

    flat = decide_bar(asof_time="t3", e_forecast=0.3, e_risk=0.1)
    assert flat["want_long"] is False
    assert flat["target_position"] == 0.0

    no_risk = decide_bar(asof_time="t4", e_forecast=0.8, e_risk=None)
    assert no_risk["risk_veto"] is False
    assert no_risk["target_position"] == 1.0


def test_xasset_channel_skill():
    from crl.leda.channels.xasset import (
        CHANNEL_ID as XID,
        build_xasset_evidence,
        evaluate_xasset_forecast_skill,
    )

    btc = _mock_ohlcv(n=400, seed=1)
    eth = _mock_ohlcv(n=400, seed=2)
    eth.index = btc.index
    ev = build_xasset_evidence(btc, eth)
    assert ev["score"].notna().sum() > 50
    skill = evaluate_xasset_forecast_skill(ev, min_points=50)
    assert skill["ok"] is True
    assert skill["channel_id"] == XID


def test_desired_from_scores_and_economic_eval():
    from crl.leda.economic import desired_from_leda_scores, evaluate_stack_economic
    from crl.shared.types import CostConfig, SplitConfig

    f = pd.Series([0.2, 0.8, 0.9, 0.6], dtype=float)
    r = pd.Series([0.1, 0.1, 0.95, float("nan")], dtype=float)
    d = desired_from_leda_scores(f, r)
    assert list(d.values) == [0.0, 1.0, 0.0, 1.0]

    ohlcv = _mock_ohlcv(n=300, seed=9)
    # Ensure open exists for next_open model
    if "open" not in ohlcv.columns:
        ohlcv = ohlcv.copy()
        ohlcv["open"] = ohlcv["close"] * 0.999
    report = evaluate_stack_economic(
        ohlcv,
        costs=CostConfig(),
        splits=SplitConfig(train_frac=0.5, val_frac=0.25, test_frac=0.25),
    )
    assert report["leda"] == "4"
    assert report["mode"] == "exploratory"
    assert "not_approved" in report["promotion"]
    assert set(report["slices"]) == {"train", "val", "test"}
    assert report["slices"]["test"]["n_bars"] > 0

    from crl.leda.economic import desired_bh_with_vol_veto, evaluate_vol_veto_policy

    r = pd.Series([0.1, 0.9, 0.2], dtype=float)
    assert list(desired_bh_with_vol_veto(r).values) == [1.0, 0.0, 1.0]
    vreport = evaluate_vol_veto_policy(
        ohlcv,
        costs=CostConfig(),
        splits=SplitConfig(train_frac=0.5, val_frac=0.25, test_frac=0.25),
    )
    assert vreport["leda"] == "5b"
    assert "not_approved" in vreport["promotion"]

    from crl.leda.economic import evaluate_vol_veto_threshold_grid

    grid = evaluate_vol_veto_threshold_grid(
        ohlcv,
        thresholds=(0.80, 0.90),
        costs=CostConfig(),
        splits=SplitConfig(train_frac=0.5, val_frac=0.25, test_frac=0.25),
    )
    assert grid["leda"] == "6"
    assert grid["n_thresholds"] == 2
    assert len(grid["results_by_threshold"]) == 2

    from crl.leda.paper import run_leda_paper_session

    paper = run_leda_paper_session(ohlcv, starting_cash=100.0, max_bars=150)
    assert paper["leda"] == "7"
    assert paper["places_live_orders"] is False
    assert paper["n_bars"] == 150
    assert "equity_end" in paper
