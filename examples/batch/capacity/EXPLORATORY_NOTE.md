# Capacity / tiny-friction v1 — exploratory (non-authoritative)

**Date:** 2026-07-27  
**Config:** `configs/capacity_tiny_friction_v1.yaml` (elevated costs; **gates unchanged**)  
**Dataset:** `binance_public_BTCUSDT_1d_79cfad335046`  
**Registry:** temp only  

## Outcome

| Result | Count |
|--------|-------|
| Run | 5 / 5 |
| `passed_val` | **0** |
| `failed_val` | **5** |
| Errors | 0 (after SMA sensitivity fix) |

All hyps failed primarily on **`min_trades`** (and bootstrap where n was higher). Point Sharpes can look high with few trades — reality checker rejects sparse “large edge bps” stories.

## Interpretation

Under **tiny-capital-elevated friction**, these pre-registered low/medium-turnover long-only daily rules do **not** clear frozen gates. That supports the mechanism claim that **capacity/friction + trade-count realism** is binding — not that any of these is an edge.

## See

`GATE_AUTOPSY_V1.md`
