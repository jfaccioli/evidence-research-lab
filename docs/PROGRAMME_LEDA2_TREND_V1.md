# LEDA-2: Trend forecast evidence channel (v1)

**Status:** Implemented as Forecast-layer channel (not a trade programme)  
**Channel id:** `leda2_trend` v1  
**Sink:** **Forecast**  
**Architecture:** `docs/ARCHITECTURE_LAYERED_DECISION_STACK.md`

## Scientific claim

> Lagged log-momentum over `mom_lookback` bars is weakly informative about next-bar log return. Mapping lagged momentum to a causal rolling percentile rank yields **long-support evidence** in [0, 1].

## What this is / is not

| Is | Is not |
|----|--------|
| Forecast-layer evidence stream | Full trading strategy / size rule |
| Evaluated by return-forecast **skill** (IC, mean ret by score bin) | Promotion to APPROVED trading |
| PIT: score at t uses momentum through t−1 only | Same-bar look-ahead |

## Parameters (locked for v1)

| Param | Value |
|-------|-------|
| `mom_lookback` | 20 |
| `rank_window` | 60 |
| `score` | rolling percentile rank of `mom_lag` |

## Evaluation

```bash
python -m crl leda eval-trend
```

Metrics: Pearson/Spearman of `mom_lag` and `score` vs `fwd_ret`; mean next return when score ≥ 0.5 vs < 0.5.

## Downstream

Portfolio thin map: `want_long = (e_forecast >= 0.5)` and not risk veto (LEDA-3). Full-stack economic gates only at LEDA-4.
