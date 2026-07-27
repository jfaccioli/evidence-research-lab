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

## Gate autopsy

**Done (write-up only):** `GATE_AUTOPSY_V1.md`

Summary: bootstrap CI lo kills 8/10; min_trades kills 6/10; mean-revert cluster multi-gate fails; two near-misses (`high_flat`, `trend_and_not_high`) fail only on trade count / reality few-trades.

## Next scientific options (in order)

1. ~~Inspect gate failure modes~~ → **done** (`GATE_AUTOPSY_V1.md`).  
2. Update Thesis Tree `funding_crowding` (programme null / pivot; no daily re-mining).  
3. Optional **separate** pre-registered **4h power study** for the power cluster only — design: `docs/PROGRAMME_FUNDING_4H_POWER_V1.md`.  
4. Orthogonal **true OI PIT** programme — design: `docs/PROGRAMME_OI_PIT_V1.md`.  
