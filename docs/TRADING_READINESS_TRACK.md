# Trading Readiness Track (operational only)

**Version:** 1  
**CLI:** `python -m crl ops-readiness check`  
**Code:** `crl.production.ops_readiness`

## Separation from science

| Track | Purpose |
|-------|---------|
| **Scientific** | Mechanism → properties → LEDA → confirmatory gates → (only then) tradeability |
| **Operational** | Prove machinery is safe and reproducible **without** alpha claims |

Passing ops readiness **never** softens scientific gates and **never** enables LIVE.

## Non-alpha policies used

1. **always_flat** — zero orders; cash constant  
2. **unit_flip_5** — alternate long/flat every 5 bars (deterministic turnover for accounting)

## Checklist items

1. Paper flat policy reliability  
2. Deterministic position accounting under flip  
3. Fees modeled (non-zero under turnover)  
4. Stale/missing/bad price skip handling  
5. Kill switch blocks paper when engaged  
6. Exposure / notional limits  
7. Max trades per day  
8. Shadow broker records without capital  
9. Restart recovery (kill switch clear)  
10. Audit journal written  
11. LIVE dual-flag fail-closed  

## Output

- `data/ops/OPS_READINESS_LATEST.json`  
- journals under `data/ops/readiness_journals/`  

## Explicit non-goals

- Measuring Sharpe of flip policy  
- Shadow “alpha” monitoring  
- LIVE orders  
