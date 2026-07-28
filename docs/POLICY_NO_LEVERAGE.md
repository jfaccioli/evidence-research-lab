# Policy: no leverage (project mandate)

**Effective:** 2026-07-28  
**Applies to:** research promotion, paper/shadow design targets, and any future Phase 5 tiny live.

## Rule

| Allowed | Forbidden (this project) |
|---------|---------------------------|
| Spot BTC (or listed spot pairs later) | Perp/futures **as the trading vehicle** for personal capital |
| Position 0 or 1 (full flat / full long) within cash | Leverage &gt; 1, margin, borrowing to size up |
| Risk envelope notional caps (e.g. AUD 10–50) | “Tiny leverage is fine” exceptions |

Code: `assert_phase1_universe` rejects non-unit leverage; `RiskEnvelope.max_leverage` must stay 1.0; production risk envelope fails closed if leverage &gt; 1.

## Why (product + risk)

1. **Ruin risk** — leverage turns model error into account death.  
2. **Mandate fit** — research success metric is knowledge; live is a system test, not a casino.  
3. **Australia (context, not legal advice)** — retail access to **leveraged crypto products** has been subject to **ASIC product intervention / high-risk treatment**; CFD-style leverage for retail is tightly constrained. Prefer **spot only** so the project does not depend on products that may be restricted or unsuitable.  
   **Confirm with ASIC resources or a licensed adviser before any real account setup.** This file is project policy, not legal advice.

## Funding / OI data vs trading leverage

Using **funding rates or open interest as research features** does **not** mean we trade leveraged perps in Phase 5. Features ≠ vehicle.
