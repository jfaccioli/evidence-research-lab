# Trading Platform Programme v1

**Status:** Parallel engineering track  
**Package:** `crl.platform`  
**Does not replace:** Alpha Discovery, confirmatory gates, or LEDA science

## Objective

Ensure that when a scientifically justified strategy exists, it can be deployed
**immediately and safely**. The platform is developed **independently of alpha**.

## Architecture

```text
Strategy plug-in  →  Sizing  →  Portfolio  →  Risk Manager  →  Execution / Backtest
                         ↓
              Cost model · Audit · Broker abstraction
```

| Component | Module |
|-----------|--------|
| Strategy interface | `platform.strategy` |
| Benchmarks (BH, SMA, TSMOM, Random) | `platform.benchmarks` |
| Sizing | `platform.sizing` |
| Portfolio | `platform.portfolio` |
| Risk manager | `platform.risk` |
| Engine | `platform.engine` |
| Walk-forward harness | `platform.walkforward` |
| Attribution vs B&H | `platform.attribution` |
| Deployment / rollback | `platform.deployment` |
| Brokers | `production.execution.broker` (paper / shadow / live-stub) |
| Ops readiness | `production.ops_readiness` |

## Benchmark strategies (engineering only)

| ID | Rule |
|----|------|
| `bench_buy_and_hold` | Always long |
| `bench_sma_cross` | SMA50 > SMA200 |
| `bench_tsmom` | 20d return > 0 |
| `bench_random_control` | Deterministic RNG long/flat |

These are **not** scientific claims or trading recommendations.

## Scientific coupling

- Alpha Discovery continues independently.  
- Only strategies that pass the **existing confirmatory pathway** and enter
  `production.strategies.APPROVED` may replace benchmarks for paper-clock / shadow.  
- **LIVE** remains dual-flag fail-closed and stubbed.  
- Platform readiness **never** softens science gates.

## CLI

```bash
python -m crl platform list
python -m crl platform run --strategy bench_tsmom
python -m crl platform walkforward --strategy bench_sma_cross
python -m crl platform attribute
python -m crl platform deploy-gate --strategy bench_buy_and_hold
```

## Deployment & rollback

See `platform.deployment.DEPLOYMENT_CHECKLIST` and `rollback_plan()`.
