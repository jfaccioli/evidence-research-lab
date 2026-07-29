# Market property: stablecoin_agg_supply v1

**Status:** Characterized — **not** a trading programme  
**Series:** `defillama_stablecoins_agg_supply_usd_lag1_e522163c536b` (n≈3165)  
**CLI:** `python -m crl observe fetch-stable-supply` · `characterize-stable-supply`  
**PIT:** observation day D usable only after lag+1 UTC day (conservative free-research policy)

## 1. What it measures

Aggregate **stablecoin circulating supply** (USD-pegged, DefiLlama) and its
7d / 30d log growth. This is a **liquidity stock**, not:

- exchange stablecoin netflow (prior conf-null family)  
- spot OHLCV transforms  
- funding / premium (futures leverage)

## 2. Mechanism

Mint/burn and capital entry/exit into crypto as a whole. Expanding supply may
coincide with risk-on liquidity; contraction with stress — hypothesis, not edge.

## 3. Independence (lagged growth)

| Comparator | corr with dlog7_lag | corr with dlog30_lag |
|------------|---------------------|----------------------|
| ret_lag | ~-0.03 | ~-0.05 |
| rv_lag | ~0.16 | ~0.29 |
| funding_lag | ~0.29 | — |
| premium_lag | ~0.34 | — |

Partially related to futures leverage state but below strong collinearity thresholds.

## 4. Role: direction vs uncertainty

| Association | Value |
|-------------|--------|
| dlog7 → fwd_ret | ~-0.02 (null direction) |
| dlog7 → rv_next | ~0.16 |
| dlog30 → fwd_ret | ~-0.04 |
| **dlog30 → rv_next** | **~0.29** |

Conditional: high 7d growth (p80) → higher next RV (~0.038 vs ~0.026 at p20).

**Primary role (descriptive):** **uncertainty / liquidity regime**, not linear direction.

## 5. Understanding without edge

Yes — the lab can now measure crypto-wide liquidity stock with versioned PIT lag.
Material association of slower supply growth with next RV is a **scientific**
finding about market structure, not a promotion to trade rules.

## 6. LEDA

`leda_candidate: false` until a pre-registered **risk/state** claim (e.g. supply
growth as vol conditioner) is locked. Do **not** fish long/flat on supply growth.
