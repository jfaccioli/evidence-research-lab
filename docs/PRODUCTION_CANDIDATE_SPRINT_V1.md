# Production Candidate Sprint V1

**Opened:** 2026-07-29  
**Mode:** Time-bounded; deployability-first ranking  
**Gates:** Unchanged (frozen confirmatory standards)

## Deployment envelope (first candidate only)

| Constraint | Value |
|------------|--------|
| Asset | BTC spot |
| Side | Long or flat |
| Leverage | None (max 1) |
| Exchange | One (Binance public data for research; live exchange TBD) |
| Frequency | **1d** (primary) |
| Costs | `configs/default.yaml` (fees+spread+slippage); stress ×2 |
| Lag | next_open (desired lag-1) |
| Sizing | Deterministic, vol-aware |
| Limits | capital/exposure/daily-loss via platform risk (ops) |

## Ranked deployable shortlist

Scores 1–5. **DeployScore** ≈  
`1.4·P(surv_conf) + 1.2·net_EV + 1.0·mechanism + 0.8·novelty − 0.8·turnover_cost − 0.7·ops_complexity − 1.5·retired_overlap`

| Rank | Programme | Mechanism | Novel element | P(surv) | Net EV | Novelty | Turnover risk | Ops | Overlap retired | DeployScore | Role |
|------|-----------|-----------|---------------|---------|--------|---------|---------------|-----|-----------------|-------------|------|
| **1** | **PCS_VOL_SCALE** | Constant-risk long: size ∝ 1/RV | **Decision problem**: continuous inverse-vol exposure (not binary veto grid) | 3 | 3 | 3 | 3 (rebalance cost) | 2 | 1 (related to vol veto but different map) | **~7.1** | **PRIMARY** |
| **2** | **PCS_BASIS_RISKOFF** | Dislocation stress → reduce risk | New property class (cross-venue basis) | 2.5 | 2.5 | 4 | 2 | 2 | 0 | **~6.4** | **RESERVE** |
| 3 | PCS_4H_TSMOM | Underreaction at 4h | Different horizon | 2 | 2.5 | 2 | 4 | 3 | 3 (near mom family) | ~3.5 | Rejected this sprint |
| 4 | PCS_SUPPLY_COND | Liquidity stock growth conditions long | Stable supply growth | 2 | 2.5 | 3 | 2 | 2 | 1 | ~5.0 | Deferred |
| — | Daily mom / stress composite / residual RV skill | — | — | — | — | — | — | — | **5** | **Forbidden** |

### Why PRIMARY = inverse-vol scaling

1. Credible mechanism: risk capacity falls when vol is high; size for ~constant risk.  
2. Novel *decision map* vs retired LEDA-6 binary e_risk veto thresholds.  
3. Free PIT data (OHLCV only).  
4. Matches deployment envelope (BTC spot long, daily, vol-aware).  
5. Decisive in one confirmatory split: either improves risk-adjusted net outcome vs B&H under costs, or fails cleanly.  
6. Low external deps.

### Why RESERVE = basis risk-off

1. New observation class already characterised.  
2. Stress-widens-basis evidence exists.  
3. Open only if PRIMARY is decisive null **and** time remains — not parallel large exploration.

## Outcomes (fill at end)

| Code | Meaning |
|------|---------|
| A | Confirmatory survivor → shadow package |
| B | Shadow pass → micro-live package |
| C | Programme rejected → next ranked |

## Sprint result: **C — programmes rejected**

See `research_kb/pcs/PCS_V1_RESULT.json` and `PCS_V1_BASIS_RESULT.json`.

### PRIMARY `PCS_VOL_SCALE_V1` — REJECTED

| Check | Result |
|-------|--------|
| test Sharpe ≥ 0.20 | pass (0.23) |
| max DD ≤ 0.55 | pass (0.52) |
| activity | **fail** (1 trade segment; 16 rebalances < 30) |
| not worse than B&H on sharpe | **fail** (0.23 vs B&H 0.30) |
| improves DD vs B&H | slight (0.521 vs 0.530) |
| mean weight | **0.98** (almost always full long) |

**Interpretation:** Inverse-vol scaling barely leaves full long; after costs it underperforms B&H Sharpe. **Family `pcs_vol_scale_v1` retired.**

### RESERVE `PCS_BASIS_RISKOFF_V1` — REJECTED

| Check | Result |
|-------|--------|
| long_frac test | **1.0** (risk-off never binds on test after lag) |
| Sharpe vs B&H | worse (0.24 vs 0.30) |
| activity | **fail** (1 trade) |

**Family `pcs_basis_riskoff_v1` retired.**

### Next ranked deployable programme (post-sprint)

| Rank | Programme | Note |
|------|-----------|------|
| 1 | Free **ETF flow** delayed series as liquidity pipe (if reconstructible PIT) | Needs source acquisition |
| 2 | **4h** decision clock with **new** mechanism (not daily mom clone) | Different horizon; design carefully |
| — | Daily mom / stress composite / residual RV / inv-vol scale / basis risk-off binary | **Retired** |

**No shadow. No micro-live.** Gates held.

