# OI PIT v1 — gate autopsy

**Date:** 2026-07-27  
**Source reports:** `reports/hyp_oi_*_v1_exploratory.json` (+ confirmatory for survivor)  
**Programme:** `docs/PROGRAMME_OI_PIT_V1.md`  
**Scope:** Write-up only after locked batch. **No new thresholds.**

---

## 1. Headline

| | |
|--|--|
| Pre-registered hyps | 10 / 10 |
| Exploratory `passed_val` | **1** |
| Exploratory `failed_val` | **9** |
| Confirmatory of survivor | **`failed_test`** |
| Live registry | **No** |

Programme outcome: **no confirmatory candidate**. One val tease killed on test — success as uncertainty reduction.

---

## 2. Per-hypothesis (validation)

| Hypothesis | Family | n_tr | Sharpe_ac | Excess vs B&H | CI lo | Status | Main failures |
|------------|--------|-----:|----------:|--------------:|------:|--------|---------------|
| `hyp_oi_chg_pct_high_flat` | change | 30 | **1.377** | **+0.412** | **+0.075** | **passed_val** → **failed_test** | Confirmatory: test Sh −0.10, CI lo −1.38, fee_fragile, stress, MT, fragility |
| `hyp_oi_z_high_flat` | level | 54 | 0.856 | −0.590 | −0.482 | failed_val | bootstrap CI lo |
| `hyp_oi_sum5_high_flat` | change | 72 | 0.507 | −0.919 | −0.551 | failed_val | bootstrap CI lo |
| `hyp_oi_high_exit_only` | level | 232 | 0.474 | −0.941 | −0.894 | failed_val | bootstrap; 2× cost |
| `hyp_oi_falling_long` | unwind | 123 | 0.271 | −1.083 | −1.128 | failed_val | WF; bootstrap; 2× cost |
| `hyp_oi_rising_flat` | change | 133 | 0.167 | −1.142 | −1.314 | failed_val | Sharpe; bootstrap; 2× cost |
| `hyp_oi_z_low_long` | unwind | 20 | 0.075 | −1.165 | −0.966 | failed_val | min_trades; multi-gate |
| `hyp_oi_high_flat` | level | **0** | 0 | −1.163 | 0 | failed_val | **zero trades** on val |
| `hyp_oi_trend_and_not_high` | trend_gate | **0** | 0 | −1.163 | 0 | failed_val | **zero trades** on val |
| `hyp_oi_only_not_high_mom` | composite | **0** | 0 | −1.163 | 0 | failed_val | **zero trades** on val |

---

## 3. Failure-mode clusters

### A. Exploratory tease → confirmatory kill (1)

- `hyp_oi_chg_pct_high_flat`: avoid trend longs when causal `oi_chg_pct_high` (expanding 80% of daily OI % change).  
- Val: n=30 (exactly `min_trades`), Sh≈1.38, CI lo≈0.08, excess≈+0.41, stress≈1.25, reality pass.  
- **Train much weaker** (Sh≈0.29, large negative excess) — val/train gap.  
- Warnings: regime concentration 0.97; MT trial census incomplete.  
- **Test:** Sh≈−0.10, 55 trades, negative excess — **failed_test**.  
- Lesson: do **not** promote OI % change filters from val alone.

### B. Adequate trades, non-robust (bootstrap / cost)

- `z_high_flat`, `sum5_high_flat`, `high_exit_only`, `rising_flat`, `falling_long`.  
- Point Sharpes can look “ok”; CI lo &lt; 0 and/or cost stress kill.

### C. Secular-OI level filter dead on val (0 trades)

- `high_flat`, `trend_and_not_high`, `only_not_high_mom` all need `oi_high == 0`.  
- Raw OI has a strong **secular level rise**; expanding-median `oi_high` is **~0.86** overall and **rarely false in the val window** → filters that require “not high OI” produce **zero val trades**.  
- This is a **feature design failure mode** for stock OI levels, not proof OI is useless.  
- **Do not** retune the median rule on the same data; a new programme would need a pre-registered **de-trended / z-only** level claim (z was already tested and failed bootstrap).

### D. Unwind / depressed OI

- `z_low_long`, `falling_long`: multi-gate or weak — no support for “long after OI drop” in this lock.

---

## 4. Data provenance (binding)

| Field | Value |
|-------|--------|
| OI venue | **Bybit linear** BTCUSDT |
| Reason not Binance hist | Public API ~30 daily points; startTime invalid for deep history |
| OHLCV venue | Binance spot daily (same as funding programme) |
| Cross-venue note | Spot path is Binance; leverage stock signal is Bybit OI — **disclosed**, not same-venue arb |

---

## 5. What is retired vs open

### Retired / exhausted for **this programme lock**

- All 10 pre-reg daily long-only OI rules as **promotable** edges.  
- Val-only survival of `oi_chg_pct_high` filter.  
- Expanding-median raw `oi_high` as a usable long filter on this sample (val sparsity).

### Still open (new programme only)

- Same-venue Binance OI if deep history becomes available.  
- De-trended OI stock measures **pre-registered** without mining.  
- Funding × OI interaction — only after both single-series programmes closed (funding daily null; OI no candidate).  
- 4h OI microstructure — out of v1 budget.

### Process

> Do **not** mine more OI thresholds on this series without a **new programme version** and multiplicity accounting.

---

## 6. Artefacts

- OI series: `data/processed/oi/bybit_oi_BTCUSDT_oi_b38c4e688cf0.{parquet,json}`  
- Temp registry: `data/processed/oi/tmp_oi_exploratory_registry.sqlite`  
- Reports: `reports/hyp_oi_*_v1_exploratory.*`, `reports/hyp_oi_chg_pct_high_flat_v1_confirmatory.*`
