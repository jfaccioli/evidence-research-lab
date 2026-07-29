# Observation family: kline_aggression v1

**Status:** Characterized (not a trade programme)  
**Dataset:** `binance_public_BTCUSDT_1d_e686b6637728` (micro columns retained)  
**CLI:** `python -m crl observe characterize-aggression`

## What is observed

| Property | Definition |
|----------|------------|
| `taker_buy_ratio` | `taker_buy_base / volume` ∈ [0,1] |
| `trade_intensity` | `n_trades` per bar |
| `avg_trade_size` | `volume / n_trades` |

These fields were **available on every Binance kline** and previously **discarded** by the lab’s fetch path. They are not transforms of close.

## Characterization (pinned BTC 1d, ~3246 bars)

| Relation | Corr |
|----------|------|
| tbr_lag vs ret_lag | ~0.36 (co-moves with up bars — expected) |
| tbr_lag vs rv_lag | ~0.03 (≈ independent of RV) |
| log intensity vs rv_lag | ~-0.26 |
| tbr_lag vs fwd_ret | ~0.04 (weak direction) |
| tbr_lag vs rv_next | ~0.03 |
| **log intensity vs rv_next** | **~-0.26** (uncertainty association) |
| log intensity vs fwd_ret | ~-0.02 (≈ null direction) |

**Read:** Trade intensity is a better candidate for **state/uncertainty** observation than directional alpha. Taker buy share largely tracks contemporaneous returns.

## What we will not do yet

- Long/flat rules on `taker_buy_ratio > 0.5`  
- Grid search over intensity thresholds on test  
- Claim APPROVED or shadow  

## Next (if pursuing)

Pre-register LEDA **risk/state** evidence channel using lagged log trade intensity (or intensity residual after RV), with skill claim on next RV / regime — not return forecast.

## Sibling free family (not yet acquired)

`perp_premium` — Binance futures premiumIndex klines (mark–index). Ranked #2 after this family.
