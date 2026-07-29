# Market property: cross_venue_basis v1

**Status:** Characterized (alignment fixed) — **not** a trading programme  
**Series:** `cross_venue_binance_usdt_vs_coinbase_usd_d54a084a5189`  
**CLI:** `python -m crl observe fetch-cross-basis` · `characterize-cross-basis`

## What it measures

`basis = log(Binance BTCUSDT close / Coinbase BTC-USD close)` on the **same UTC
calendar day**. Includes USD/USDT wedge as part of the measured dislocation.

## PIT

Same-day closes known after the UTC day completes. Predictive work uses **lag-1**.

## Alignment note (scientific integrity)

An earlier as-of join shifted Coinbase by ~1 day and contaminated basis with
returns (corr ~0.99). Fixed to **inner join on UTC floor day**. Always verify
`corr(basis_lag, ret_lag)` is not near 1 after rebuilds.

## Characterization (post-fix)

| Metric | Value |
|--------|--------|
| corr basis_lag vs ret_lag | ~-0.11 |
| corr abs_basis vs rv_lag | ~0.05 |
| corr abs_basis vs rv_next | ~0.07 |
| corr basis_lag vs fwd_ret | ~-0.04 |
| autocorr basis | ~0.90 |

**Role:** market dislocation / fragmentation (persistent level).  
**LEDA:** refused.
