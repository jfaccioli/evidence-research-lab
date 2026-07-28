# Programme: MVRV valuation filter (v1)

**Mechanism:** BTC MVRV ratio as slow valuation regime (high = rich / risk-off flat; low = cheap / long with trend).

Distinct from SMA technicals: uses on-chain valuation series, not price-only MA.

## Series
- CMD `btc_mvrv_ratio.json`, series_id `cmd_btc_mvrv_ratio_v1`, lag=1, prefix `mvrv_`
