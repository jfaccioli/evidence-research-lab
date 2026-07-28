# flow exploratory — CMD BTC exchange netflow v1

**Date:** 2026-07-28  
**Status:** programme complete under frozen gates.

| Field | Value |
|-------|-------|
| series_id | `cmd_btc_exchange_netflow_v1` |
| source | Free GitHub mirror (Ercin Dedeoglu crypto-market-data, CC BY 4.0) |
| n_events | 1334 (≈2022-12 → 2026-07) |
| publish_lag_days | 1 (fixed; vendor revision journal unavailable) |
| OHLCV | `binance_public_BTCUSDT_1d_*` |
| registry | temp only (not live catalog) |

## Results

| Stage | Outcome |
|-------|---------|
| Exploratory | **6/8** `passed_val` |
| Confirmatory | **0/6** candidates — all `failed_test` |

Failed confirmatory (all): negative test Sharpe after costs, bootstrap CI lower &lt; 0, fee_fragile reality checks. Val teases did **not** hold on holdout.

Failed exploratory (2): `hyp_flow_high_flat`, `hyp_flow_into_flat` (bootstrap CI).

## Attribution

Crypto market data provided by [Crypto Market Data](https://github.com/ErcinDedeoglu/crypto-market-data) by Ercin Dedeoglu. CC BY 4.0.

## Scientific reading

Under frozen gates + fixed publish lag, **daily BTC exchange netflow long-only rules in this lock do not earn confirmatory promotion**. High-quality null for this operationalisation — not a reason to soften gates.

## PIT caveat

Not vendor-grade point-in-time (bulk `last_modified` rewrites on source). Results are still stronger evidence than mock and still fail honestly on test.
