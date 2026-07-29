# LEDA-1: Vol / risk evidence channel (v1)

**Status:** Implemented as Risk-layer channel (not a trade programme)  
**Channel id:** `leda1_vol_risk` v1  
**Sink:** **Risk** (not Forecast)  
**Architecture:** `docs/ARCHITECTURE_LAYERED_DECISION_STACK.md`

## Scientific claim

> Lagged realized volatility (log-return std over `rv_window`) is a **persistence forecast** of next-bar realized vol. Mapping lagged RV to a causal rolling percentile rank yields **risk-off evidence** in [0, 1].

## What this is / is not

| Is | Is not |
|----|--------|
| Risk-layer evidence stream | Directional long/flat alpha programme |
| Evaluated by forecast **skill** (corr) | Promotion to APPROVED trading |
| PIT: score at t uses RV through t−1 only | Same-bar vol look-ahead |

## Parameters (locked for v1)

| Param | Value |
|-------|-------|
| `rv_window` | 20 |
| `rank_window` | 60 |
| `score` | rolling percentile rank of `rv_lag` |

## Evaluation

```bash
python -m crl leda eval-vol-risk
```

Metrics: Pearson/Spearman of `rv_lag` vs `rv_next`; score vs `rv_lag` (should be high by construction of rank).

## Downstream

Portfolio may use `e_risk >= threshold` as **veto** (thin Risk→Portfolio map). Full-stack economic gates only after LEDA-2/3 exist.
