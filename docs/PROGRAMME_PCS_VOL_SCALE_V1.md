# PROGRAMME PCS_VOL_SCALE_V1 (pre-registered)

**Sprint:** Production Candidate Sprint V1  
**Family id:** `pcs_vol_scale_v1`  
**Trial cost:** 1 primary + 2 frozen lookback ablations + 1 stress (all reported; **no winner pick on test**)

## 1. Mechanism

Investors and market makers reduce risk-bearing when short-horizon realised volatility
is high. A long-only BTC mandate can scale exposure **inversely** to lagged RV to target
more stable risk contribution — not to predict direction.

## 2. Target and decision mapping

| Item | Freeze |
|------|--------|
| Asset | BTC/USDT spot |
| Decision clock | 1d bar close → fill next open (lag-1) |
| Forecast | None (risk/sizing policy) |
| Desired weight | `w_t = clip(σ* / rv_lag_t, 0, 1)` |
| `rv_lag` | std of log returns over `L` bars, shifted by 1 |
| `σ*` | causal expanding **median** of `rv_lag` (min 60) |
| Primary L | **20** |
| Ablation L | 15, 30 (report only; promotion requires L=20 pass) |

## 3. Baselines (locked)

1. Cash / flat  
2. Buy-and-hold (unit long)  
3. Constant half-size (w=0.5 always) — simple sizing control  

## 4. Data / costs / splits (locked)

- Pinned Binance BTC 1d (verify_hash)  
- Costs: default.yaml; stress_multiplier on confirmatory test only  
- Splits: train 50% / val 25% / test 25% chronological  
- Construction uses train+val diagnostics only; **pass/fail on test**  

## 5. Confirmatory pass criteria (all required on test, L=20)

1. `sharpe_after_cost >= gates.sharpe_min` (0.20)  
2. `max_drawdown <= gates.max_drawdown` (0.55)  
3. `n_trades >= gates.min_trades` (30) **or** turnover rebalance events ≥ 30  
   (continuous sizing: count |Δw|≥0.05 events as rebalances)  
4. `sharpe_after_cost >= buy_and_hold sharpe − 0.05` **and**  
   `max_drawdown <= buy_and_hold max_drawdown`  
   (must not clearly lose on **both** risk-adjusted return and DD vs B&H)  
5. Stress (2× costs): sharpe ≥ 0 **or** still lower DD than B&H under stress  
6. Overfit: |train_sharpe − test_sharpe| ≤ overfit_gap_max  
7. Ablations L=15,30: test sharpe not driven solely by L=20  
   (fail if L=20 test sharpe > 0.5 and both ablations < 0)  

## 6. Explicit non-goals

- Parameter search on test  
- Binary vol-veto threshold grid (retired LEDA-6 family)  
- Directional alpha claims  

## 7. Family retirement if fail

Retire `pcs_vol_scale_v1` for continuous inverse-vol unit long on daily BTC under this map.
