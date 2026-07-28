# polymarket exploratory

**Date:** 2026-07-28  
**Window design:** BTC OHLCV truncated to PM series start − 120d (short odds history; full-sample val has no PM signal).

| Stage | Result |
|-------|--------|
| Exploratory | **0/5** passed_val |
| Confirmatory | **0/0** candidates |

## Locked series
- `pm_btc_150k_eoy2025_yes_v1` — Will Bitcoin reach $150,000 by December 31, 2025? (YES)
- n_events: 368; publish_lag_days=1; public CLOB (no key)
- window dataset: `binance_public_pm_window_BTCUSDT_1d_ab89e9fefbce` (691 bars)
- content_hash: `f7759cc7ca0a0d4f5bf398f6…`

## Confirmatory
```json
[]
```

## Reading
Short sample; collinear with path risk. Null or survivor must still respect frozen gates.
