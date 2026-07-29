# Living research queue (Research Director)

**Updated:** 2026-07-29  
**Science roadmap:** `docs/RESEARCH_ROADMAP_SCIENCE.md`  
**Platform:** `docs/TRADING_PLATFORM_V1.md`

## Parallel programmes

| Programme | Objective | Status |
|-----------|-----------|--------|
| **Alpha Discovery** | Mechanisms, pre-reg science, confirmatory gates | Active; **0** promotions |
| **Trading Platform** | Safe deploy when science earns it | **v1** scaffold + benchmarks |
| **Ops readiness** | Paper/safety checklist | 11/11 pass |

Science gates are **never** weakened by platform readiness.  
Benchmarks validate engineering only — not alpha claims.

## Scientific model (short)

Next-RV dominated by RV lag. Leverage/ETH residual skill families **retired**.  
Dislocation widens under stress (descriptive). Directional alpha **unfound**.

## Commands

```bash
# Science
python -m crl observe mechanisms
python -m crl observe study-leverage-incremental-rv

# Trading Platform (engineering)
python -m crl platform list
python -m crl platform run --strategy bench_tsmom
python -m crl platform walkforward --strategy bench_sma_cross
python -m crl platform attribute
python -m crl platform deploy-gate --strategy bench_buy_and_hold

# Ops
python -m crl ops-readiness check
```
