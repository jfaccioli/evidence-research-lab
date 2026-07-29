# Living research queue (Research Director)

**Updated:** 2026-07-29  
**RD programme:** `docs/RESEARCH_DIRECTOR_PROGRAMME.md`  
**Science roadmap:** `docs/RESEARCH_ROADMAP_SCIENCE.md`  
**Platform:** `docs/TRADING_PLATFORM_V1.md`

## Top-level programmes

| Programme | Role |
|-----------|------|
| **Research Director** | Prioritise, knowledge graph, prevent waste |
| **Alpha Discovery** | Only path to production strategies |
| **Mechanism Discovery** | Economic mechanisms |
| **LEDA** | Decision architecture (stable scaffold) |
| **Trading Platform** | Engineering deploy readiness |
| **Ops / Governance** | Safety, frozen gates |

## Current model

RV lag dominates next-RV skill. Incremental leverage/ETH residual families **retired**.
Dislocation widens under stress (descriptive). **0** confirmatory trading candidates.

## RD commands

```bash
python -m crl rd status          # full director report
python -m crl rd rank            # scored future directions
python -m crl rd graph           # knowledge graph
python -m crl rd programmes      # programme map
python -m crl rd areas           # research areas
python -m crl rd check --query "daily momentum"   # anti-duplication
python -m crl rd sync            # refresh research_kb/rd/director_state.json + RD_STATUS.md
```

## Parallel execution

```bash
# Science
python -m crl observe mechanisms

# Platform (engineering)
python -m crl platform list

# Ops
python -m crl ops-readiness check
```
