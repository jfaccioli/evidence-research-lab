# Market property: perp_premium v1

**Status:** Characterized — **not** a trading programme  
**Series:** `binance_premium_BTCUSDT_premium_1d_5f3bba74d0f0` (n≈2409, 2019-12 → 2026-07)  
**CLI:** `python -m crl observe fetch-premium` · `characterize-premium`  
**Directive:** `docs/MARKET_PROPERTIES_DIRECTIVE.md`

## 1. What does it measure?

USDT-M perpetual **premium index** over each daily bar (Binance `premiumIndexKlines` close):  
continuous mark–index deviation. Known at bar close (PIT as-of join).

## 2. Putative mechanism

Leverage demand / inventory imbalance in perpetual futures. Related to funding
*equilibrium* but is a **persistent level process**, not the discrete 8h funding print.

## 3. Independence from known properties (lagged)

| Comparator | Corr with `premium_lag` |
|------------|-------------------------|
| ret_lag | ~-0.03 |
| rv_lag | ~0.14 |
| **funding_lag** | **~0.68** (related, not identical) |
| taker_buy_ratio_lag | ~0.03 |

**Note:** Moderately collinear with funding. Any future evidence channel should
consider **premium residual after funding** (or joint model) to avoid double-counting.

## 4. Role: direction vs uncertainty

| Association | Corr |
|-------------|------|
| premium_lag → fwd_ret | ~**-0.002** (null direction) |
| premium_lag → rv_next | ~**0.16** |
| Autocorr lag-1 of premium | ~**0.78** (persistent) |

High |premium| (top 20% abs): mean next RV **higher** (~0.035 vs ~0.027).

**Primary role (descriptive):** **uncertainty / leverage-stress**, not direction.

## 5. Conditions

- Informative as a **state variable** when |premium| is elevated (stress).  
- Linear return forecast: not supported on this sample.  

## 6. Understanding without edge

Yes. The lab now has a versioned, PIT measure of futures consensus deviation
independent of spot close transforms and only partially overlapping funding.

## 7. LEDA

`leda_candidate: false` until a pre-registered **risk/state** claim (prefer residual vs funding).  
**No** atomistic long/flat promotion.
