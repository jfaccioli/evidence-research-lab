#!/usr/bin/env python3
"""Smoke-test OI PIT join + rule eval on mock data only (not science).

Does not write the live registry. Does not fetch exchange data.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crl.research.hypotheses.rules import eval_rule
from crl.shared.data.feature_store import load_or_build_features
from crl.shared.data.sources.mock import MockOHLCVSource
from crl.shared.data.sources.oi_mock import generate_mock_oi_events


def main() -> int:
    ohlcv = MockOHLCVSource(n=800, seed=1).fetch_ohlcv("BTCUSDT", "1d")
    start = str(ohlcv.index[0].date())
    end = str((ohlcv.index[-1] + __import__("pandas").Timedelta(days=1)).date())
    events = generate_mock_oi_events(start=start, end=end, seed=1)
    cache = ROOT / "data" / "processed" / "features_mock_oi_smoke"
    feat = load_or_build_features(
        ohlcv,
        dataset_id="mock_oi_smoke",
        cache_dir=cache,
        force=True,
        oi_events=events,
        oi_series_id="mock_seed1",
    )
    assert "oi_last" in feat.columns
    hyp_dir = ROOT / "examples" / "batch" / "oi"
    n_ok = 0
    for path in sorted(hyp_dir.glob("hyp_oi_*.yaml")):
        raw = yaml.safe_load(path.read_text())
        entry = raw["entry"]["expression"]
        row = feat.dropna(subset=["oi_last", "sma_200"]).iloc[-1].to_dict()
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
