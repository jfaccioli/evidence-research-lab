# LEDA-3: Thin portfolio + execution stack wire (v1)

**Status:** Implemented as decision audit path (not promotion)  
**Module:** `crl.leda.stack.decide_bar`  
**Architecture:** `docs/ARCHITECTURE_LAYERED_DECISION_STACK.md`

## Responsibility

Map Forecast + Risk evidence scores to a **unit long-only** target and an **execution intent** (mode recorded; no live orders).

## Thin defaults (locked)

| Input | Map |
|-------|-----|
| `e_forecast` | `want_long = e_forecast >= 0.5` (None → flat) |
| `e_risk` | veto if `e_risk >= 0.85` (None → no veto) |
| Portfolio | target 0 or 1 under `RiskEnvelope` (no leverage) |
| Execution | `fill=next_open`, `places_live_orders=False` |

## What this is / is not

| Is | Is not |
|----|--------|
| Reproducible F→R→P→X audit trail | Economic promotion gate |
| Compatible with paper/shadow modes as labels | LIVE enablement |
| Unit long-only | Mean-variance optimizer |

## Evaluation

Unit tests for veto / long / flat combinations. Full-stack **economic** evaluation is LEDA-4 under frozen gates.

## CLI

```bash
python -m crl leda decide --e-forecast 0.7 --e-risk 0.2
python -m crl leda decide --e-forecast 0.7 --e-risk 0.9   # veto
```
