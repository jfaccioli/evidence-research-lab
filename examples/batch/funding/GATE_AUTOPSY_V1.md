# Funding PIT v1 — gate autopsy (write-up only)

**Date:** 2026-07-27  
**Source reports:** `reports/hyp_funding_*_v1_exploratory.json` (local; gitignored)  
**Batch note:** `EXPLORATORY_NOTE.md`  
**Programme lock:** `docs/PROGRAMME_FUNDING_PIT_V1.md`  
**Scope:** Failure-mode inventory only. **No new hypotheses. No threshold retunes. No re-runs.**

---

## 1. Headline

| | |
|--|--|
| Pre-registered hyps | 10 / 10 executed |
| `passed_val` | **0** |
| `failed_val` | **10** |
| Live registry written | **No** (temp registry only) |
| Gates | Frozen `configs/default.yaml` (`min_trades=30`, bootstrap CI lo ≥ 0, …) |

**Programme-level null** for the locked **daily BTC long-only** funding-filter set under existing gates.

---

## 2. Per-hypothesis table (validation split)

| Hypothesis | Family | n_tr | Sharpe_ac | Excess vs B&H | CI lo | 2× stress Sh | WF+ | Gate failures (summary) |
|------------|--------|-----:|----------:|--------------:|------:|-------------:|----:|-------------------------|
| `hyp_funding_chg_up_flat` | change | 82 | 1.180 | −0.181 | −0.084 | 0.78 | 0.75 | bootstrap CI lo |
| `hyp_funding_high_exit_only` | level | 43 | 1.163 | −0.049 | −0.109 | 0.98 | 0.75 | bootstrap CI lo |
| `hyp_funding_high_flat` | level | 19 | 1.481 | **+0.324** | **+0.231** | 1.39 | 0.75 | **min_trades**; reality economic_plausibility (few trades) |
| `hyp_funding_trend_and_not_high` | trend_gate | 19 | 1.481 | **+0.324** | **+0.231** | 1.39 | 0.75 | **min_trades**; reality economic_plausibility (few trades) |
| `hyp_funding_sum24_high_flat` | level | 48 | 0.659 | −0.820 | −0.695 | 0.37 | 0.69 | bootstrap CI lo |
| `hyp_funding_z_high_flat` | level | 66 | 0.500 | −0.904 | −0.736 | 0.18 | 0.69 | bootstrap CI lo |
| `hyp_funding_pos_flat` | level | 18 | 0.898 | −0.949 | −0.808 | 0.64 | 0.81 | min_trades; bootstrap CI lo |
| `hyp_funding_neg_long` | mean_revert | 18 | 0.129 | −1.149 | −1.339 | −0.28 | 0.63 | min_trades; primary Sharpe; bootstrap; 2× cost |
| `hyp_funding_only_neg_mom` | composite | 24 | −0.354 | −1.220 | −1.841 | −0.86 | 0.50 | min_trades; Sharpe; WF; bootstrap; skeptical; 2× cost; fee_fragile |
| `hyp_funding_z_low_long` | mean_revert | 23 | −0.792 | −1.266 | −2.021 | −1.34 | 0.44 | min_trades; Sharpe; WF; bootstrap; skeptical; 2× cost; fee_fragile |

Metrics are **val** after-cost; CI is block-bootstrap Sharpe CI lower bound.

---

## 3. Failure-mode frequency

| Mode | Count (of 10) | Interpretation |
|------|---------------|----------------|
| **Bootstrap Sharpe CI lo &lt; 0** | **8** | Dominant statistical killer even when point Sharpe looks “good” |
| **n_trades &lt; min_trades (30)** | **6** | Sparse daily filters / low turnover |
| **2× cost stress Sharpe &lt; 0** | **3** | Concentrated in mean-revert / composite negatives |
| **Primary Sharpe &lt; 0.2** | **3** | Same weak cluster |
| **WF positive_frac &lt; 0.6** | **2** | Mean-revert cluster unstable across folds |
| **Reality: economic_plausibility (few trades)** | **2** | Near-misses with high point stats but n=19 |
| **Reality: fee_fragile** | **2** | Mean-revert cluster |
| **Skeptical P(mean trade &gt; 0) &lt; 0.55** | **2** | Mean-revert cluster |

**Not the story:** pipeline errors, join bugs, or mock-data leakage (true Binance funding used).

---

## 4. Clusters (scientific reading)

### A. Near-miss power cluster (level + one interaction)

- `hyp_funding_high_flat`, `hyp_funding_trend_and_not_high`  
- Identical val metrics (n=19, Sharpe≈1.48, CI lo≈+0.23, **positive excess vs B&H**).  
- Failed **only** on `min_trades` + reality “few trades / implausible edge bps.”  
- **Does not** pass gates. **Does not** nominate for confirmatory.  
- **Does** justify a **separate, pre-registered** higher-frequency **power study** (4h) for *this family only* — not threshold mining on daily.

### B. Adequate-trades, non-robust “tease” cluster

- `chg_up_flat` (n=82), `high_exit_only` (n=43), `sum24` (n=48), `z_high_flat` (n=66).  
- Enough trades; often decent point Sharpe; **CI lo still negative** and/or **negative excess vs B&H**.  
- Failure is **uncertainty / economic non-edge**, not sample sparsity.  
- Re-running daily with nearby funding thresholds would be **multiplicity abuse**.

### C. Mean-reversion / “long after negative funding” cluster

- `neg_long`, `z_low_long`, `only_neg_mom`.  
- Multi-gate collapse: low/negative Sharpe, fee fragility, cost stress, weak WF.  
- **Strong refutation** of this pre-reg mean-revert operationalisation on daily long-only spot.

### D. Sign-only filter

- `pos_flat`: sparse + CI failure; weaker than the high/median filter forms.

---

## 5. What this retires vs leaves open

### Retired for **this programme** (daily, locked 10, long-only spot)

- Claim that any of the 10 locked rules is an exploratory survivor under frozen gates.  
- Claim that simple **negative-funding mean-reversion** longs work in this setup.  
- Claim that **change / z / sum24** crowding filters deliver robust after-cost edge with positive bootstrap CI on daily.

### Explicitly **not** retired

- Funding as a state variable on **other horizons** (e.g. 4h power study — separate programme).  
- Funding **combined with true OI** (separate mechanism programme).  
- Perp-perp or cross-venue funding arb (out of scope).  
- Short-side / hedge formulations (not in budget).

### Process constraint (binding)

> Do **not** mine more funding thresholds on the same daily series without a **new programme version** and multiplicity accounting.

---

## 6. Implications for next programmes

| Next step | Supported by autopsy? | Why |
|-----------|----------------------|-----|
| **4h funding power study (design-only first)** | **Yes (conditional)** | Cluster A is pure `min_trades`/power; Cluster B shows 4h is not a free pass |
| **More daily funding hyps** | **No** | Budget spent; null recorded |
| **True OI PIT programme** | **Yes (orthogonal)** | Funding tested; OI still untested as true series; high IG |
| Soften gates | **No** | Forbidden by standing policy |

---

## 7. Artefact pointers

- Programme: `docs/PROGRAMME_FUNDING_PIT_V1.md`  
- Hyps: `examples/batch/funding/hyp_*.yaml`  
- Funding dataset id: `binance_funding_BTCUSDT_funding_d1bbe1f63b23`  
- OHLCV: `binance_public_BTCUSDT_1d_79cfad335046`  
- Thesis: `research_kb/THESIS_TREE.md` → `funding_crowding`
