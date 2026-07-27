# Meta synthesis — daily long-only discovery wave (2026-07-27)

## Headline

Under **frozen gates** and pre-registered programme budgets, **no confirmatory candidates** emerged across funding, OI, capacity/friction, asymmetric, liquidity, ATR trail, slow/fast, vol regime, calendar, breakout, and volume programmes.

Val-only teases (OI change filter; vol-regime exit-on-spike) **failed confirmatory**.

## Failure modes (recurring)

1. **Bootstrap Sharpe CI lo &lt; 0** — point Sharpe can look fine; uncertainty does not.  
2. **min_trades** — sparse “insurance” / breakout filters.  
3. **2× cost stress / fee_fragile** — turnover kills edge.  
4. **WF instability** — fold inconsistency.  
5. **Reality few-trades** — high edge_bps with n≪30 is not an edge.

## What this means for live trading

Live automation is **not** blocked by missing broker code (paper/shadow scaffolds exist).  
It is blocked by **absence of honest confirmatory survivors**.

Softening gates would produce false live readiness.

## Paper path caveat

`crl paper` full-sample equity is a **path-hardening tool**, not a substitute for train/val/test + gates. Do not promote from paper journals alone.

## Next research options (priority)

1. **4h** power only where daily autopsy showed pure min_trades (selective, pre-reg).  
2. **Different claim classes** not yet stressed (e.g. multi-day hold constraints, explicit cost-aware low-turnover with 4h bars).  
3. **Meta-conclusion draft:** daily BTC long-only public technical space may be **near-saturated** under these costs/gates — still open for true alternative data with PIT.  
4. Continue paper/shadow ops maturity without LIVE.
