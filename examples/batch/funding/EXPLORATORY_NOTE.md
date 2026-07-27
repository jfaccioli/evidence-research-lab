# Funding PIT v1 — first exploratory batch (non-authoritative)

**Date:** 2026-07-27  
**Mode:** exploratory only; temp registry; **not** live registry; **not** confirmatory  
**OHLCV:** `binance_public_BTCUSDT_1d_79cfad335046`  
**Funding:** `binance_funding_BTCUSDT_funding_d1bbe1f63b23` (7536 events, 2019-09-10 → 2026-07-27)  
**Join:** as-of `funding_time ≤ bar close`; signal lag = next open (pipeline default)  
**Gates:** frozen defaults from `configs/default.yaml`  

## Outcome

| Result | Count |
|--------|-------|
| Run | 10 / 10 pre-registered |
| `passed_val` | **0** |
| `failed_val` | **10** |
| Errors | 0 |

**Interpretation (honest):** Under the **locked** 10-hypothesis budget and **existing** gates, no funding-PIT rule survived exploratory validation. That is a **high-quality programme-level null for this pre-registered set**, not proof that no funding edge exists on other horizons/venues/definitions.

Do **not** mine more funding thresholds on the same data without a **new** programme version and multiplicity accounting.

## Non-claims

- Not COMPLETE / not promotable  
- Mock funding was not used for this batch  
- Live `registry/crl.sqlite` was not written (temp registry only)  

## Next scientific options (in order)

1. Inspect gate failure modes per hyp (trades vs WF vs cost stress vs overfit) without changing thresholds.  
2. If failures are mostly `min_trades`, consider a **separate** pre-registered 4h power study (secondary meta recommendation)—not ad-hoc threshold tweaks.  
3. Otherwise retire this daily funding-filter family for long-only spot and update Thesis Tree `funding_crowding` stance to exhausted_null / pivot.  
