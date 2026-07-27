# OI PIT v1 — first exploratory batch (non-authoritative)

**Date:** 2026-07-27  
**Mode:** exploratory only; temp registry; **not** live registry  
**OHLCV:** `binance_public_BTCUSDT_1d_79cfad335046` (Binance spot daily)  
**OI:** `bybit_oi_BTCUSDT_oi_b38c4e688cf0` (Bybit **linear** BTCUSDT OI, 2183 daily points, 2020-08-05 → 2026-07-27)  
**Why Bybit:** Binance public `openInterestHist` retains only ~30 daily points; deep startTime rejected. Series is **true exchange-native OI**, labeled as Bybit — not Binance, not OHLCV proxy.  
**Join:** as-of `oi_time ≤ bar close`; signal lag = next open  
**Gates:** frozen `configs/default.yaml`

## Outcome

| Result | Count |
|--------|-------|
| Run | 10 / 10 pre-registered |
| `passed_val` | **1** (`hyp_oi_chg_pct_high_flat`) |
| `failed_val` | **9** |
| Errors | 0 |

## Confirmatory (same survivor, temp registry)

| Result | |
|--------|--|
| Hyp | `hyp_oi_chg_pct_high_flat` v1 |
| Status | **`failed_test`** |
| Test Sharpe_ac | **−0.10** |
| Test excess vs B&H | **−0.14** |
| Killers | negative primary Sharpe; bootstrap CI lo &lt; 0; fee_fragile; 2× cost; MT hygiene fail-closed; fragility inconclusive |

**Interpretation:** Exploratory val tease **did not** survive confirmatory. High-quality **formulation-level null** for this locked rule — classic “val-only” failure mode. **Not** a candidate. **Not** COMPLETE.

## Non-claims

- Not promotable; no paper/shadow/live  
- Mock OI not used for science batch  
- Live `registry/crl.sqlite` not written  
- Do **not** mine more OI thresholds on the same data without a new programme version  

## Autopsy

See `GATE_AUTOPSY_V1.md`.
