# LEDA-0 protocol

**Version:** 1  
**Date:** 2026-07-29

## Evidence record

Required fields: `channel_id`, `version`, `sink` (`forecast`|`risk`|`both`), `asof_time`, `score` ∈ [0,1], `inputs_hash`.

## Layers

See `crl.leda.types.LAYER_CONTRACTS` and `docs/ARCHITECTURE_LAYERED_DECISION_STACK.md`.

| Layer | Thin default now |
|-------|------------------|
| Forecast | `leda2_trend` scores; no size |
| Risk | `leda1_vol_risk` scores; veto map |
| Portfolio | 0/1 long-only + veto (`stack.decide_bar`) |
| Execution | Intent + existing paper/shadow path (no LIVE) |

## Forbidden

- Free-text LLM votes as promotion evidence  
- Fitting portfolio on confirmatory test  
- Look-ahead in channel scores  

## CLI

```bash
python -m crl leda protocol
python -m crl leda eval-vol-risk
python -m crl leda eval-trend
python -m crl leda decide --e-forecast 0.7 --e-risk 0.2
python -m crl leda eval-stack          # LEDA-4 exploratory economics
python -m crl leda eval-vol-veto-grid  # LEDA-6 multi-threshold (report all)
python -m crl leda paper               # LEDA-7 paper audit wire
```
