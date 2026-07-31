# PROGRAMME_MS_FUNDING_CARRY_V1

**Status:** Locked for research (H1 test)  
**Human:** Hedged research authorized 2026-07-31 (`docs/HUMAN_AUTHORIZATIONS.md`)  
**Not live.** Not long/flat spot PnL.

## Question

Does a **point-in-time funding-carry style** rule (be in approximate cash-and-carry when lagged funding is attractive) earn positive risk-adjusted returns after costs under frozen scientific metrics?

## Economic story

When perpetual funding is high, longs pay shorts. A hedged book (long spot + short perp) can earn funding with reduced directional beta. We approximate daily funding income from the PIT funding series and apply trading costs on regime flips. Optional residual-risk haircut so “perfect hedge” is not assumed.

## Model (explicit, imperfect)

- **In carry (position=1):** daily bar return ≈ `funding_income_1d` − residual_haircut − flip costs  
- **Flat (0):** 0 − flip costs  
- `funding_income_1d` = sum of funding rates with `funding_time` in the prior UTC day (known only after events; as-of lag via features)  
- Residual haircut = `residual_beta * |spot_return|` (default 0.05) — conservative leakage  
- Costs: same one-way cost fraction as lab default, charged on position changes  
- Decision lag: position from closed-bar signal → apply next bar (shift 1)

## Budget

≤4 exploratory rules; ≤1 confirmatory-style holdout if any pass exploratory metrics.

## Reject if

Null under costs + lag + min activity + bootstrap/skeptical checks (same spirit as lab gates).
