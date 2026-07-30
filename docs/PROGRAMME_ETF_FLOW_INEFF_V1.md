# PROGRAMME_ETF_FLOW_INEFF_V1

**Status:** **COMPLETE — REJECT family** (2026-07-30). Exploratory 0/4; confirmatory not run.  
**Phase 1:** Economic Inefficiency Programme — slot 1  
**Design freeze:** before any evaluation

## Scientific question

> Does **point-in-time available** US spot Bitcoin ETF aggregate net-flow information contain incremental, economically useful information for a deployable BTC spot **long/flat** decision under frozen gates?

## Economic mechanism

ETF creations and redemptions represent institutional demand/supply. Price impact may transmit gradually because of allocation schedules, primary-market hours, AP inventory risk, and liquidity constraints.  
Therefore **lagged** net flow (not same-day unpublished flow) may still associate with subsequent BTC returns or risk posture.

## Data (binding)

| Field | Value |
|-------|--------|
| series_id | `us_spot_btc_etf_net_flow_usd_m_farside_v1` |
| source | Farside Investors public all-data table |
| source_url | https://farside.co.uk/bitcoin-etf-flow-all-data/ |
| units | US$ millions aggregate net flow |
| sign | **positive = net creations / inflows** (not exchange deposits) |
| publish_lag_days | **1** (fixed; no same-day look-ahead) |
| path | `data/processed/etf/<series_id>.parquet` |
| mock | **Forbidden** for science |

### PIT mapping (defended)

1. Observation calendar day **D** (UTC date of Farside row) has value known only after conservative lag.  
2. `flow_time = end_of_D_UTC + publish_lag_days` (default +1 day → D+1 23:59:59 UTC).  
3. OHLCV daily bars are indexed at **UTC midnight open** of the bar day; as-of join uses that index as decision clock (lab convention — **conservative** vs true end-of-day close).  
4. Signal on bar with last `flow_time ≤ bar index`; engine trades **next open**.  
5. Missing flow → NaN features → rule false (fail closed).  
6. Non-trading Farside days: no row; as-of **carries** last available flow (weekend/holiday hold of last print).  
7. Revisions: source has no revision journal → treat as **revision-risk free-research grade**, not vendor PIT.  
8. Duplicates: rejected at pin (`validate_flow_events`).

**Earliest order for flow of obs day D:**  
`flow_time = (D + lag) 23:59:59` → first bar index **strictly after** that timestamp → order at **open of the following bar**.

Example (lag=1): obs 2024-01-11 → `flow_time` 2024-01-12 23:59:59 → first usable bar 2024-01-13 00:00 → earliest order **2024-01-14 open**.

Fail closed if this mapping cannot be executed (missing series, empty join, mock fallback).

### Sample limitation

History from **2024-01-11** only. Limited regime diversity. **Do not** expand hyp count, horizons, or thresholds to compensate.

## Budget (frozen)

| Item | Cap |
|------|-----|
| Exploratory hyps | **≤ 4** (entire family) |
| Confirmatory-class evals | **≤ 1** (best val survivor only, if any) |
| Family | `family_etf_flow_ineff_v1` — one trial budget |
| Confirmatory period | Untouched holdout (pipeline test split) |
| Parallel programmes | None |

## Pre-registered hypotheses (exactly 4)

| ID | Observable | Direction | Mapping |
|----|------------|-----------|---------|
| `hyp_etf_pos_trend` | signed positive net flow | +flow → long bias | long when `flow_into_exch` + mild trend |
| `hyp_etf_create_extreme` | extreme creation (expanding q80) | large +flow → long | long on `flow_inflow_extreme` + mild trend |
| `hyp_etf_redeem_flat` | extreme redemption (expanding q20) | large −flow → risk-off | trend long **unless** extreme redemption → flat |
| `hyp_etf_z_pos` | causal 60d z-score surprise | high z → long | long when `flow_z_60 > 0` + mild trend |

Horizon: **1d** bars; hold while condition true (no multi-horizon scan).  
Baselines: B&H, cash, price-only (gates + platform attribution).  
Costs: config default fees/spread/slippage + execution lag (next open).

### Rejection conditions (each hyp)

- Fail val gates (Sharpe after cost, min trades, bootstrap CI, reality checks), **or**  
- Pass val but fail confirmatory (if selected), **or**  
- Edge explained by falsification battery (below).

## Required falsification (diagnostic; not extra family hyps)

Pre-registered checks in programme report:

1. **Return → flow:** contemporaneous / lead BTC return vs next flow (does price lead reported flow?).  
2. **Price-already-in:** compare to price-only trend baseline on same window.  
3. **Bull exposure:** time-in-market / correlation with B&H.  
4. **Launch stress:** sensitivity excluding first 60 trading days of ETF era.  
5. **Extremes:** winsorize top/bottom 1% flow days — does val edge vanish?  
6. **Lag ablation:** if exploratory survivor exists, note that lag is already +1d; do **not** search other lags.  
7. **Retired trend overlap:** hyp must not be pure SMA long without flow term.

## Promotion

Only confirmatory **candidate** after costs → shadow package under existing dual-track rules.  
No micro-live.

## If rejected

- Retire **entire** `family_etf_flow_ineff_v1`  
- Update Phase 1 budget  
- Do not reopen ETF flow variants without new data class + human override  
- Proceed to next ranked inefficiency within Phase 1 caps

## Files

- Hyps: `examples/batch/etf_flow/`  
- Series adapter: `src/crl/shared/data/sources/etf_farside.py`  
- Phase 1: `docs/PHASE1_COMPLETION_CRITERIA.md`
