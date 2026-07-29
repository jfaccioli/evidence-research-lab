# Living research queue (Research Director)

**Updated:** 2026-07-29  
**Science:** `docs/MECHANISM_DISCOVERY_DIRECTIVE.md`  
**Ops track:** `docs/TRADING_READINESS_TRACK.md` (separate; non-promotional)

## Dual tracks

| Track | Status |
|-------|--------|
| **Scientific** | Mechanism studies; 0 LEDA promotions |
| **Operational** | Ops readiness checklist **11/11 pass** (zero capital) |

Scientific gates are **not** weakened by ops readiness.

## Mechanism results

| Mechanism | Result | LEDA candidate? |
|-----------|--------|-----------------|
| vol_clustering | Cofactor prolongation **null**; RV inertia | no |
| **leverage_cycle** | Build → higher next RV than unwind (**supported**) | **no** (needs dedicated pre-reg for channel) |
| **uncertainty_behaviour** | Intensity **higher** in high RV; leverage proxies elevated | no |

## Queue

| Rank | Object | Status |
|------|--------|--------|
| **1** | Optional: pre-reg **risk-state** claim “OI-build raises next-RV skill beyond rv_lag” (family cost + ablation) **only if** pursuing LEDA risk channel | Optional science |
| **2** | Continue ops paper-clock / continuous paper shadow with **flat** policy (no alpha) | Ops hygiene |
| **3** | Conf / live | Blocked on science |

## Commands

```bash
# Science
python -m crl observe study-leverage-cycle
python -m crl observe study-uncertainty-behaviour
python -m crl observe mechanisms

# Ops (not science)
python -m crl ops-readiness check
```
