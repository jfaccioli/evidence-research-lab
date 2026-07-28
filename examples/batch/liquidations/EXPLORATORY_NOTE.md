# liquidations exploratory

**Date:** 2026-07-28
| Stage | Result |
|-------|--------|
| Exploratory | **1/5** passed_val |
| Confirmatory | **0/1** candidates |

`cmd_btc_long_liquidations_v1` n=1334 hash `3c9f37a5318cc65388f7…`  
Crypto market data provided by Crypto Market Data (https://github.com/ErcinDedeoglu/crypto-market-data) by Ercin Dedeoglu. CC BY 4.0.
```json
[
  {
    "id": "hyp_liq_low_long",
    "status": "failed_test",
    "test_sharpe": -0.6391189029151026,
    "reasons": [
      "reality: [fee_fragile] Average trade edge does not clear a meaningful fraction of round-trip costs.",
      "primary sharpe_after_cost -0.639 < 0.2",
      "bootstrap sharpe CI lo -2.157 < 0.0",
      "skeptical P(mean trade>0) 0.177 < 0.55"
    ]
  }
]
```
