# Programme: Macro risk regime → BTC spot (v1)

**Status:** Locked exploratory (pre-results)  
**Date locked:** 2026-07-28  
**Information advantage:** Macro / USD / rates **regime as state** (not another OHLCV technical).  
**EIR:** Highest free science-per-dollar unlock (`docs/EVIDENCE_INVESTMENT_REVIEW_2026-07-28.md`).

## Scientific question

> Do point-in-time **USD strength** and **short-rate** regime features, joined with conservative publication lag to daily BTC bars, support pre-registered long-only / flat rules under **frozen** gates?

## Exact FRED series (binding — do not swap after results)

| FRED id | Name (FRED) | Role in programme | Why included |
|---------|-------------|-------------------|--------------|
| **DTWEXBGS** | Nominal Broad U.S. Dollar Index (Goods & Services) | Primary **USD strength** level / z / high-low | Broad trade-weighted USD; standard macro risk-off proxy when USD rises. Daily history adequate for train/val/test. |
| **DGS2** | Market Yield on U.S. Treasury Securities at 2-Year Constant Maturity | **Policy / rate** level / change / z | Front-end rates capture tightening/easing expectations better than pure price technicals; orthogonal to spent on-chain clones. |

### Series considered and **not** used in v1

| Id | Why excluded |
|----|----------------|
| DFF (EFFR) | Highly related to front-end policy; adds little vs DGS2 for daily long-only; extra multiplicity |
| DGS10 | Longer duration; more growth/term-premium noise for v1 |
| DTWEXB (old broad dollar) | Superseded / discontinued family; use DTWEXBGS |
| VIX / equity indices | Different venue; save for later multi-asset state |

**Primary series for single-series attach tooling:** construct one composite **macro state score** from the two series after lag (see Features). Raw series stored under `data/processed/external/` for audit.

## Publication lag assumptions (binding PIT)

All times UTC. Signal on closed BTC daily bar → trade next open (lab default).

| Series | Observation in FRED | Assumed *knowable* time for lab | `publish_lag_days` applied to FRED `date` |
|--------|---------------------|--------------------------------|------------------------------------------|
| **DTWEXBGS** | Value dated calendar day *D* (daily) | End of UTC day **D+1** (conservative: index updates with short delay; avoid same-day use) | **+1** calendar day from FRED date → `event_time = D 23:59:59 + 1 day` |
| **DGS2** | Yield for business day *D* | End of UTC day **D+1** (Treasury CM yields typically available after the reference day; weekends/holidays gap-filled by FRED as missing) | **+1** calendar day same construction |

**Rationale for +1 day (not 0):**  
Even if a value appears on FRED during day *D* or early *D+1*, we **refuse** same-calendar-day use for a UTC daily BTC close decision. This is intentionally conservative and may discard mild same-day edges; preferred to look-ahead.

**Missing values:** FRED omits non-business days for DGS2; forward-fill is **not** used across series before lag. As-of join uses last available lagged observation only.

**Revision risk:** FRED series can revise. v1 does not reconstruct vintage archives; we use the download snapshot as fixed history (content-hashed). Document as **snapshot-PIT**, not full ALFRED vintage-PIT. Future upgrade: ALFRED vintages if nulls are ambiguous.

## Features (prefix `mac_`)

Built from lagged DTWEXBGS (`usd_*`) and DGS2 (`y2_*`), then combined flags:

| Feature | Definition |
|---------|------------|
| `mac_usd_z` | 60d z-score of lagged USD index |
| `mac_usd_high` | USD > expanding median |
| `mac_y2_z` | 60d z-score of lagged 2Y yield |
| `mac_y2_up` | 5d change in 2Y > 0 |
| `mac_stress` | 1 if `mac_usd_z > 1` **or** `mac_y2_z > 1` |
| `mac_easy` | 1 if `mac_usd_z < -0.5` **and** `mac_y2_z < 0` |

Binary rule tokens: `mac_stress`, `mac_easy`, `mac_usd_high`, `mac_y2_up` (and combinations with existing `above_sma_50` / `above_sma_200`).

## Pre-registered hyps (≤5)

See `examples/batch/macro_regime/`. **Do not expand without v2.**

## Execution

1. Load `FRED_API_KEY` from `.env` (gitignored).  
2. Download full history for DTWEXBGS + DGS2; apply lag; hash; store parquet.  
3. Exploratory batch temp registry + confirmatory on any `passed_val`.  
4. Frozen gates only; null is success.

## Non-goals

- Softening gates for short samples  
- Using VIX/equity without a new programme version  
- Same-day FRED values  
- Paid data in this programme  
