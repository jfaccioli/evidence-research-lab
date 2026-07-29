"""Property synthesis review — pre-registered stress family."""

from __future__ import annotations

import numpy as np
import pandas as pd

from crl.research.market_properties.synthesis import (
    FAMILY_ID,
    equal_rank_stress,
    evaluate_stress_family,
    run_property_synthesis_review,
)
from crl.shared.data.sources.mock import MockOHLCVSource


def test_equal_rank_and_family_on_mock():
    ohlcv = MockOHLCVSource(n=500, seed=11).fetch_ohlcv("BTCUSDT", "1d")
    if ohlcv.index.tz is None:
        ohlcv.index = ohlcv.index.tz_localize("UTC")
    # Minimal panel-like frame via full review with no externals
    report = run_property_synthesis_review(ohlcv)
    assert report["synthesis_version"] == 1
    assert "stress_family_evaluation" in report
    fam = report["stress_family_evaluation"]
    assert fam["family_id"] == FAMILY_ID
    assert "open_composite_leda_programme" in fam
    # With only rv_lag present, composite degenerates toward baseline
    assert fam["inputs_present"] == ["rv_lag"] or "rv_lag" in fam["inputs_present"]


def test_evaluate_stress_family_explicit_panel():
    idx = pd.date_range("2020-01-01", periods=400, freq="D", tz="UTC")
    rng = np.random.default_rng(0)
    rv = np.abs(rng.normal(0.02, 0.01, size=len(idx)))
    panel = pd.DataFrame(
        {
            "rv_lag": rv,
            "rv_next": np.roll(rv, -1),
            "abs_premium_lag": np.abs(rng.normal(0, 0.001, size=len(idx))),
            "abs_funding_lag": np.abs(rng.normal(0, 0.0001, size=len(idx))),
            "abs_supply_dlog30_lag": np.abs(rng.normal(0, 0.05, size=len(idx))),
        },
        index=idx,
    )
    panel.iloc[-1, panel.columns.get_loc("rv_next")] = np.nan
    fam = evaluate_stress_family(panel, include_basis=False)
    assert fam["n_eval"] > 100
    assert fam["family_trial_cost"] >= 1
    st = equal_rank_stress(panel, ["rv_lag", "abs_premium_lag"])
    assert st.notna().sum() > 50
