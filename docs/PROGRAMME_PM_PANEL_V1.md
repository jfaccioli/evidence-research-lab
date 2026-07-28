# Programme: Prediction-market multi-market panel → BTC (v1)

**Status:** Locked exploratory  
**Information advantage:** Cross-event market-implied **state** (not a single binary).  
**Design date:** 2026-07-28 (pre-results)

## Scientific question

> Does a **pre-registered panel** of prediction-market YES prices, aggregated with lag into daily state features, support long-only / flat BTC rules under frozen gates better than chance (and better than exhausted OHLCV / free on-chain clones)?

## Why not Q2

Q2 used one year-end path market (`$150k EOY 2025`). Panel tests **joint** implied state across several long-horizon markets selected by a fixed rule.

## Pre-registered market selection rule (binding)

From event slug `what-price-will-bitcoin-hit-in-2025`, take YES tokens for markets whose question matches **reach $N by December 31, 2025** for N in the fixed set:

`{100000, 120000, 150000, 200000}`  

(and if present: `dip to $70000` as stress leg).

**Do not** add markets after seeing Sharpe. Missing market → skip that leg; require ≥3 legs.

## Features (prefix `pmp_`)

Built after as-of join of each leg (publish_lag_days=1 per leg):

| Feature | Definition |
|---------|------------|
| `pmp_mean` | Cross-sectional mean of available leg prices |
| `pmp_disp` | Cross-sectional std of leg prices |
| `pmp_bull` | Fraction of legs with price > 0.5 |
| `pmp_mean_z` | 60d z-score of `pmp_mean` |
| `pmp_high` | `pmp_mean` > expanding median |
| `pmp_low` | `pmp_mean` < expanding median |

Binary flags used in rules: `pmp_high`, `pmp_low`, `pmp_bull_hi` (`pmp_bull` > 0.5), `pmp_z_hi` (`pmp_mean_z` > 1).

## Hyps ≤5

`examples/batch/pm_panel/`.

## Sample design

Window BTC OHLCV from first panel observation − 120d (short history vs full BTC sample).

## Success / failure

Null under frozen gates is success (retires this panel operationalisation). Confirmatory candidates only if earned.
