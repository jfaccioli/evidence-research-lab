# Research marathon synthesis — 2026-08-01

**Mode:** Always-on extended (human: 24h token budget)  
**Live trading:** OFF  
**Hedged research:** authorized  

## Scoreboard

| Wave | Content | Passed val | Confirmatory survivors |
|------|---------|------------|------------------------|
| Prior | cycle, funding carry v1–v3, joint fund+prem, basis MR | few teases | **0** |
| **1** | CV basis MR; basis dir filters; OI regime; carry+OI; prem dir; triple filters | **7** | **0** (all conf fail) |
| **2** | ETH trend; BTC 4h+fund; vol-quiet long | **0** | **0** |
| **3** | calendar structure; CB premium dir | **1** tease | **0** |

**Net:** many honest nulls; **no** autotrade candidate.

## Pattern (important)

Several rules **look good on validation** then **fail the holdout** (classic overfit / regime change). Gates are doing their job.

## Diagnostic (not a candidate)

Always-on funding carry with **residual_beta = 0** (perfect hedge fantasy) shows **strong** val *and* test Sharpe.  
With realistic residual (premium move / haircut), edge **dies**.

**Learning:** raw funding income may be real; **harvestability after hedge risk** is the open H1 question — needs better residual model or true paired spot+perp execution study, not more long/flat clones.

## H1 status

Still **leading hypothesis**, not proven. Multiple operationalisations failed. Do **not** promote residual=0 carry.

## Next (continue always-on)

1. Pre-register residual model from **rolling predicted |Δpremium|** without free tuning  
2. Or true multi-leg accounting if we add execution sim  
3. Or free web/X scan for **new** mechanism class (not re-mining)  
4. Paid options OI remains human-gated  

## Autotrade readiness

**Unchanged:** missing a strategy that passes confirmatory under honest costs.  
Long horizon to late 2026 still valid for research; **not** a promise of live bots soon.
