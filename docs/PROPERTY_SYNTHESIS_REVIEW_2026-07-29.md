# Property Synthesis Review — 2026-07-29

**Version:** synthesis v1  
**CLI:** `python -m crl observe synthesis-review`  
**Family id:** `leda_synth_stress_equal_rank_v1`  
**Philosophy:** `docs/MARKET_PROPERTIES_DIRECTIVE.md`

## Purpose

After a batch of free market properties, ask whether the **shelf jointly**
supports a coherent scientific question — without free combination fishing or
premature trading rules.

**Declared target (pre-registered):** next-bar realized vol (`rv_next`).  
**Declared baseline:** lagged RV (`rv_lag`).  
**Declared composite:** equal-weight mean of causal rolling percentile ranks
(window 60) of stress inputs (higher rank = more stress).

## 1. Role map

| Property | Likely role | Mechanism (short) |
|----------|-------------|-------------------|
| RV lag / persistence | **Volatility / uncertainty** | RV persists |
| Trade intensity | **Participation** | Activity / liquidity intensity |
| Taker aggression | **Participation** | Aggressive buyer share (co-moves with returns) |
| Perpetual premium | **Leverage stress** | Mark–index deviation |
| Funding | **Leverage stress** | Discrete funding print |
| Stablecoin supply growth | **Liquidity** | Aggregate circulating USD stock growth |
| DeFi TVL growth | **Capital allocation** | Capital locked in DeFi |
| Cross-venue basis | **Market dislocation** | Binance USDT vs Coinbase USD log ratio |

## 2. Redundancy (lagged correlations)

Material collinearity (|corr| ≥ 0.6):

| Pair | Corr |
|------|------|
| premium_lag ↔ funding_lag | **~0.68** |

Others on the shelf are only moderately related. Premium residual science already
showed premium’s **linear** next-RV association is largely shared with funding.

Cross-venue basis (after calendar-day fix): corr with ret_lag ~**-0.11**, abs
basis vs rv_lag ~**0.05**, autocorr ~**0.90** — a persistent dislocation level,
not a return clone.

## 3. Incremental information for next-RV (pre-registered family)

| Input | IC vs rv_next |
|-------|----------------|
| **rv_lag (baseline)** | **~0.958** |
| abs_supply_dlog30_lag | ~0.290 |
| abs_funding_lag | ~0.215 |
| abs_premium_lag | ~0.146 |
| abs_basis_lag | ~0.070 |
| **equal-rank stress composite** | **~0.264** |
| Incremental (stress residual ⊥ expanding rv_lag) | **~-0.12** |

**Ablations:** dropping `rv_lag` collapses composite IC to ~0.09. Dropping other
inputs leaves IC ~0.29–0.37 — still far below baseline.

**Decision thresholds (locked before evaluation):**

- composite IC ≥ baseline IC + 0.02  
- |incremental residual IC| ≥ 0.05  

**Result:** composite **does not beat** baseline; residual IC is negative.  
→ **`open_composite_leda_programme = false`**

Family trial cost counted: 1 composite + 5 drop-one ablations = **6**.

## 4. Scientific conclusion

1. The shelf is **complementary by role** (vol, leverage, liquidity, participation,
   allocation, dislocation) but **not jointly superior** to RV persistence for
   forecasting next RV under a simple equal-rank stress map.
2. **Retire** free weight/threshold fishing for family `leda_synth_stress_equal_rank_v1`.
3. A composite null is **success**: we learned RV dominates linear next-vol skill;
   other properties add description and weaker associations, not a better frozen
   stress score under this rule.
4. **No LEDA composite programme** opened. No shadow/live.

## 5. What remains valuable

| Property | Standalone knowledge value |
|----------|----------------------------|
| RV persistence | Dominant risk-state baseline |
| Stable supply growth | Liquidity stock; moderate next-RV IC |
| Funding / premium | Leverage stress family (partly redundant) |
| Kline intensity | Participation; negative IC with next RV |
| DeFi TVL | Allocation description; null BTC linear skill |
| Cross-venue basis | Dislocation; persistent; weak next-RV |

## 6. Recurrence

Run **Property Synthesis Review** after each meaningful batch of new properties
(`crl observe synthesis-review`). Prefer new **orthogonal mechanisms** over
another transform of the same shelf. Any future composite must re-pre-register
target, rule, ablations, and family cost under a **new family id**.
