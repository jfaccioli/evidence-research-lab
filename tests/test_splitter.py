from crl.research.backtest.splitter import chronological_split, walk_forward_folds
from crl.shared.data.sources.mock import MockOHLCVSource
from crl.shared.types import SplitConfig


def test_chronological_order():
    df = MockOHLCVSource(n=1000, seed=0).fetch_ohlcv("BTCUSDT", "1d")
    sp = chronological_split(df, SplitConfig())
    assert sp.train.index.max() < sp.val.index.min()
    assert sp.val.index.max() < sp.test.index.min()
    assert len(sp.train) + len(sp.val) + len(sp.test) == len(df)


def test_walk_forward_nonempty():
    df = MockOHLCVSource(n=1000, seed=0).fetch_ohlcv("BTCUSDT", "1d")
    folds = walk_forward_folds(df, SplitConfig(wf_train_bars=200, wf_val_bars=50, wf_step_bars=50))
    assert len(folds) >= 1
    for f in folds:
        assert f.train.index.max() < f.val.index.min()
