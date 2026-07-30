# PROGRAMME_MINER_REVENUE_STRESS_V1

**Status:** **COMPLETE — REJECT family** (exploratory 0/4) after stablecoin transmission  
**Inefficiency:** `ineff_miner_selling`  
**Internal review:** OPEN_AFTER_STABLE_IF_SLOTS

## Question

Does **lagged miner revenue stress/expansion** (public Blockchain.com series) support a deployable BTC long/flat policy under frozen gates?

## Mechanism

When miner USD revenue falls, treasury selling pressure may rise; when revenue recovers, stress eases. Proxy is imperfect without inventory — treated as partial test of miner-selling inefficiency.

## Data

| Field | Value |
|-------|--------|
| series | `blockchain_miners_revenue_dlog_lag1_v1` |
| source | Blockchain.com charts API miners-revenue |
| lag | 1 day fixed |
| prefix | `mrv` |
| Phase1 dataset pin | **yes** (one free external dataset slot) |

## Budget

≤4 exploratory; ≤1 confirmatory; family `family_miner_revenue_stress_v1`
