# LEDA-5a: Cross-asset (ETH→BTC) forecast evidence (v1)

**Status:** Implemented as Forecast-layer channel (skill eval; not trade promotion)  
**Channel id:** `leda5_xasset` v1  
**Sink:** **Forecast**

## Scientific claim

> Lagged ETH log-momentum is weakly informative about BTC next-bar log return. Mapping lagged ETH mom to a causal rolling percentile yields BTC **long-support** evidence in [0, 1].

## PIT

- Score at BTC bar t uses ETH momentum through t−1 only.
- ETH series reindexed to BTC calendar; missing ETH → NaN score (fail closed for that bar).

## Parameters (locked)

| Param | Value |
|-------|-------|
| `mom_lookback` | 20 |
| `rank_window` | 60 |

## Evaluation

```bash
python -m crl leda eval-xasset
```

## Relation to LEDA-4

LEDA-4 baseline remains BTC trend + vol veto. Cross-asset is a **separate** forecast candidate; stack swap only after skill + exploratory economics justify it.
