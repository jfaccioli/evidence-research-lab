from crl.research.stats.sensitivity import _SMA_RE, _swap_sma


def test_swap_does_not_corrupt_sma200():
    expr = "close > sma_20 and close > sma_200"
    # swapping 20 must not touch 200
    out = _swap_sma(expr, 20, 40)
    assert "sma_200" in out
    assert "sma_40" in out
    assert "sma_400" not in out


def test_swap_does_not_touch_dist_sma():
    expr = "dist_sma_20 < -0.08"
    out = _swap_sma(expr, 20, 40)
    assert out == expr  # dist_sma_20 is not bare sma_20


def test_swap_does_not_corrupt_compound_sma_flags():
    expr = "sma_50_above_200 == 1"
    assert _SMA_RE.findall(expr) == []
    assert _swap_sma(expr, 50, 10) == expr
    assert _swap_sma(expr, 200, 160) == expr
