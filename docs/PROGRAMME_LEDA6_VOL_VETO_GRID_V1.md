# LEDA-6: Pre-registered vol-veto threshold grid (v1)

**Status:** Implemented — diagnostic family study  
**CLI:** `python -m crl leda eval-vol-veto-grid`  
**Module:** `evaluate_vol_veto_threshold_grid`

## Pre-registration

| Item | Value |
|------|--------|
| Policy | B&H long except `e_risk >= thr` |
| Channel | `leda1_vol_risk` v1 |
| Thresholds | **0.70, 0.80, 0.90, 0.95** (locked) |
| Family size | 4 |
| Selection | **None** — report all cells |

## Forbidden

- Choosing the best test threshold for promotion  
- Expanding the grid after seeing results without a new pre-reg version  

## Outcome (pinned BTC 1d, 2026-07-29)

Zero thresholds pass exploratory hard gates. See `docs/LEDA_RESULTS_LOG.md`.
