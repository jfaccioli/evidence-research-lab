# GATE_AUTOPSY_V1 — etf_flow_ineff_v1

**Date:** 2026-07-30
**Decision:** **REJECT family** `family_etf_flow_ineff_v1`
**Confirmatory:** not run (0 exploratory survivors)

## Exploratory outcomes

| Hyp | Val Sharpe | Val trades | Status | Primary fails |
|-----|------------|------------|--------|---------------|
| `hyp_etf_create_extreme` | -0.474 | 12 | failed_val | reality: [fee_fragile] Average trade edge does not clear a meaningful fraction of round-trip costs.; n_trades 12 < min_trades 30; primary sharpe_after_cost -0.474 < 0.2 |
| `hyp_etf_pos_trend` | -0.471 | 12 | failed_val | reality: [fee_fragile] Average trade edge does not clear a meaningful fraction of round-trip costs.; n_trades 12 < min_trades 30; primary sharpe_after_cost -0.471 < 0.2 |
| `hyp_etf_redeem_flat` | -0.576 | 13 | failed_val | reality: [fee_fragile] Average trade edge does not clear a meaningful fraction of round-trip costs.; n_trades 13 < min_trades 30; primary sharpe_after_cost -0.576 < 0.2 |
| `hyp_etf_z_pos` | 0.156 | 11 | failed_val | n_trades 11 < min_trades 30; primary sharpe_after_cost 0.156 < 0.2; bootstrap sharpe CI lo -2.328 < 0.0 |

## Falsification (pre-registered diagnostics)

- flow→next-return corr: **-0.0065**
- return→next-flow corr: **0.0619**
- IC ex-launch60: **-0.0161**
- IC winsorized: **-0.0085**
- B&H Sharpe (window): **0.884**
- SMA50 control Sharpe: **0.919** (trades=32)
- SMA200 control Sharpe: **0.015**

## Learned

Under Phase 1 constraints and fixed lag-1 Farside aggregate US$m net flows,
no pre-registered long/flat ETF-flow rule cleared exploratory gates.
Trade counts stayed low; edges were fee-fragile or negative after costs.
Do not reopen ETF flow variants without a new data class + human override.

## Phase 1

Major programme slot 1 **completed (null)**. Proceed to next ranked inefficiency within budget.

