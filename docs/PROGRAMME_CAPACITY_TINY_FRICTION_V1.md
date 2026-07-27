# Programme: Tiny-capital friction realism (v1)

**Status:** Pre-registered; execute under elevated-cost config (stricter, not softer gates).  
**Mechanism:** `capacity_tiny_friction`  
**Budget:** ≤ **5** exploratory hyps.  
**Mode:** Research only; temp registry; no paper/live.

## Scientific question

> Under **elevated** round-trip costs that stress a ~10–50 AUD mandate (higher fees/slippage than the lab baseline), do **low-turnover** long-only daily rules still pass frozen statistical gates — or do all “edges” die once friction is realistic for tiny capital?

This is **not** a search for new alpha grids. It tests the claim that **capacity/friction** is binding.

## Cost model (programme lock)

Separate config: `configs/capacity_tiny_friction_v1.yaml`

| Parameter | Lab default | This programme |
|-----------|-------------|----------------|
| fee_bps_per_side | 10 | **25** |
| half_spread_bps | 1.5 | **3** |
| slippage_bps_per_side | 5 | **15** |
| stress_multiplier | 2 | **2** (still applies on top) |

**Gates unchanged** from `default.yaml` (min_trades, Sharpe, bootstrap CI, etc.).

## Pre-registered hyps (≤5)

| ID | Claim | Style |
|----|-------|-------|
| `hyp_cap_sma200_hold` | Slow trend hold survives friction | low turnover |
| `hyp_cap_ema200_hold` | EMA200 hold | low turnover |
| `hyp_cap_sma50_200_cross` | Classic cross | moderate turnover |
| `hyp_cap_mom20_trend` | Mom+trend | higher turnover stress |
| `hyp_cap_lowvol_sma50` | Quiet market + mild trend | medium |

Exact expressions in `examples/batch/capacity/*.yaml`.

## Falsification

- All fail under elevated costs → capacity/friction is binding for these formulations (high-quality null for “tiny capital can run public SMA/mom rules after fat fees”).  
- Any exploratory pass → confirmatory under **same elevated config** (not re-run cheap).

## Explicit non-goals

- Softening gates  
- Mining parameters  
- Claiming default-cost survivors transfer to tiny capital without this stress  
