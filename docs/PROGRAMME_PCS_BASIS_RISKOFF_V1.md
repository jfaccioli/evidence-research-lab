# PROGRAMME PCS_BASIS_RISKOFF_V1 (pre-registered reserve)

**Family id:** `pcs_basis_riskoff_v1`  
**Opened because:** PCS_VOL_SCALE_V1 decisive reject (near-BH, inferior Sharpe).

## Mechanism

Cross-venue dislocation (Binance USDT vs Coinbase USD) widens under stress.
When |basis| is elevated, reduce risk: go **flat**; otherwise **unit long**.

## Decision map (frozen)

- `basis_lag` = lagged same-day log price ratio (existing series)
- `w_t = 0` if `abs(basis_lag) >= expanding p90` else `1`
- Expanding p90 min_periods=60, causal
- Lag-1 fill, default costs, train/val/test 50/25/25

## Pass criteria (test)

Same structure as PCS_VOL_SCALE: sharpe_min, max_dd, activity (entries/exits ≥ 15),
not worse than B&H on both sharpe and DD, improve at least one of sharpe/DD vs B&H,
stress ok, overfit gap ok.

## Retirement

If fail: retire `pcs_basis_riskoff_v1` for binary abs-basis risk-off on daily BTC.
