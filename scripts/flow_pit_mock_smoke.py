#!/usr/bin/env python3
"""Smoke-test flow PIT join + rule eval on mock data only (not science)."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crl.research.hypotheses.rules import eval_rule
from crl.shared.data.feature_store import load_or_build_features
from crl.shared.data.sources.flow_mock import generate_mock_flow_events
from crl.shared.data.sources.mock import MockOHLCVSource


def main() -> int:
    ohlcv = MockOHLCVSource(n=800, seed=1).fetch_ohlcv("BTCUSDT", "1d")
    start = str(ohlcv.index[0].date())
    end = str((ohlcv.index[-1] + __import__("pandas").Timedelta(days=1)).date())
    events = generate_mock_flow_events(start=start, end=end, seed=1)
    cache = ROOT / "data" / "processed" / "features_mock_flow_smoke"
    feat = load_or_build_features(
        ohlcv,
        dataset_id="mock_flow_smoke",
        cache_dir=cache,
        force=True,
        flow_events=events,
        flow_series_id="mock_seed1",
    )
    assert "flow_last" in feat.columns
    n_ok = 0
    for path in sorted((ROOT / "examples" / "batch" / "flow").glob("hyp_flow_*.yaml")):
        raw = yaml.safe_load(path.read_text())
        entry = raw["entry"]["expression"]
        row = feat.dropna(subset=["flow_last", "sma_200"]).iloc[-1].to_dict()
        try:
            flag = eval_rule(entry, row)
        except Exception as exc:
            print(f"FAIL {path.name}: {exc}")
            return 1
        print(f"OK   {path.name}: entry_eval={flag}")
        n_ok += 1
    print(f"SMOKE_OK hyps={n_ok} bars={len(feat)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
