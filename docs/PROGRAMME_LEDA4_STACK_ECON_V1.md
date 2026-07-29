# LEDA-4: Full-stack exploratory economic evaluation (v1)

**Status:** Implemented as **exploratory diagnostic** (not confirmatory promotion)  
**Module:** `crl.leda.economic.evaluate_stack_economic`  
**CLI:** `python -m crl leda eval-stack`

## Scientific claim under test

> A thin fixed map — long when `leda2_trend` score ≥ 0.5 and not vetoed by `leda1_vol_risk` score ≥ 0.85 — does **not** automatically produce after-cost edge. LEDA-4 measures that map under frozen costs and train/val/test splits.

## Frozen map (not fitted)

| Piece | Value |
|-------|--------|
| Forecast | `leda2_trend` v1 |
| Risk | `leda1_vol_risk` v1 |
| `want_long` | `e_forecast >= 0.5` |
| Veto | `e_risk >= 0.85` |
| Portfolio | unit long-only |
| Fill | next_open lag-1 (lab engine) |
| Costs | `configs/default.yaml` |

## What pass means

`exploratory_hard_gates_pass` is a **diagnostic** checklist (min trades, test Sharpe, DD, overfit gap).  
It does **not**:

- register a confirmatory trial  
- grant APPROVED status  
- justify shadow trading  

Shadow remains blocked until a director review finds scientific justification after genuine confirmatory success under the full pipeline.

## CLI

```bash
python -m crl leda eval-stack
python -m crl leda eval-stack --mock
```
