# Market property: defi_agg_tvl v1

**Status:** Characterized — **not** a trading programme  
**Series:** `defillama_tvl_agg_usd_lag1_988e515005b9`  
**CLI:** `python -m crl observe fetch-defi-tvl` · `characterize-defi-tvl`  
**PIT:** lag+1 day (conservative free-research policy)

## 1. What it measures

Aggregate **DeFi TVL** (USD locked in protocols) and 7d/30d log growth.

## 2. Mechanism

Capital allocation into DeFi smart contracts — risk-on commitment of crypto capital,
distinct from circulating stablecoin stock and from futures leverage prints.

## 3. Independence

| Comparator | corr with tvl dlog7_lag |
|------------|-------------------------|
| ret_lag | ~0.00 |
| rv_lag | ~-0.03 |
| stable dlog7 | ~0.20 (related, not collinear) |
| funding | ~0.35 |
| premium | ~0.39 |

## 4. Role / next-state associations

| Association | Corr |
|-------------|------|
| dlog7 → fwd_ret | ~-0.01 (null) |
| dlog7 → rv_next | ~-0.03 (null) |
| dlog30 → rv_next | ~-0.08 (weak) |

**Linear predictive skill for BTC direction and next RV: not supported.**

## 5. Understanding without edge

Yes — the lab can now measure DeFi capital commitment with versioned PIT lag and
compare it to stable supply and futures state. Null linear association with BTC
next return/RV is itself useful (reduces false hope for a simple TVL→BTC edge).

## 6. LEDA

`leda_candidate: false`.
