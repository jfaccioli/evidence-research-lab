# Funding 4h power study v1 — exploratory batch (non-authoritative)

**Date:** 2026-07-27  
**Programme:** `docs/PROGRAMME_FUNDING_4H_POWER_V1.md`  
**Mode:** exploratory; temp registry only  
**OHLCV:** `binance_public_BTCUSDT_4h_b02118ab586a` (~19.5k bars)  
**Funding:** `binance_funding_BTCUSDT_funding_d1bbe1f63b23` (same true series as daily)  
**Annualization:** 2190 (4h)  
**Gates:** frozen defaults  

## Outcome

| Result | Count |
|--------|-------|
| Run | 6 / 6 pre-registered |
| `passed_val` | **0** |
| `failed_val` | **6** |
| Errors | 0 |

**Interpretation:** Daily Cluster-A near-misses were **not** rescued by higher-frequency power. All 6 hyps had **n_trades ≥ 63** (most ≫ 30) and still failed WF / bootstrap / cost / primary Sharpe. Clean **power-study null** for this locked level-filter family on 4h.

## Non-claims

- Not COMPLETE / not promotable  
- Live registry not written  
- Do not re-grid funding thresholds on 4h without new programme version  

## Autopsy

`GATE_AUTOPSY_V1.md`
