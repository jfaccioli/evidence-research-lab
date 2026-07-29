# Pre-reg: info_prop_eth_rv_to_btc_residual_v1

**Result:** **FAMILY RETIRED** (null)

## Hypothesis

Lagged ETH realized vol associates with BTC next-RV residual after expanding
control for BTC `rv_lag`.

## Results

| Metric | Value |
|--------|--------|
| IC(BTC rv_lag, BTC rv_next) | ~0.958 |
| IC(ETH rv_lag, BTC rv_next) | ~0.816 (collinear raw skill) |
| **IC(ETH rv_lag, residual)** | **~-0.032** |
| Threshold | 0.05 |
| n residual | ~3125 |

## Decision

**Retire** `info_prop_eth_rv_to_btc_residual_v1`. Cross-asset vol “propagation”
beyond BTC’s own RV lag is **not** supported. High raw ETH–BTC RV correlation is
shared variance, not incremental information.
