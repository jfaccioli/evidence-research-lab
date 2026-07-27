# Programme: Point-in-time BTC open interest (OI) (v1) — **DESIGN ONLY**

**Status:** Pre-registered design lock. **No live OI data fetch. No runs. No feature mining.**  
**Authority:** Next orthogonal mechanism after funding daily null (high information gain).  
**Mode:** Research only — no paper/shadow/live; no gate softening.  
**Budget:** ≤ **10** pre-registered exploratory hypotheses.  
**Related:** Funding programme is **separate**; do not grid funding×OI until both single-series programmes have locked results.

---

## 1. Scientific question

> Does **exchange-native open interest** (USDT-M BTC perpetual), as a point-in-time
> measure of leverage capacity / positioning stock, support a **pre-registered,
> fail-closed** long-only rule on daily bars that survives costs and existing gates —
> or is the claim a clean null on this horizon?

**Why now:** Funding (flow/cost of leverage) was tested true-PIT and null on daily
filters. OI is the **stock** of leveraged positions — economically distinct; still
absent from the evidence base as a true series.

Success:

1. Clean programme-level null, or  
2. Exploratory survivor → nominate confirmatory under **unchanged** gates.

---

## 2. Dataset (PIT) — when later authorized

| Field | Spec |
|-------|------|
| Instrument | BTCUSDT perpetual (USDT-M), **open interest** history |
| Source class | `exchange_native` (e.g. Binance futures OI endpoints / hist) |
| Mock / unit tests | Deterministic synthetic OI for join tests only — **never** for promotion |
| Granularity | Native OI snapshots (often 5m–1h depending on source); mapped to **daily** decision bars first |
| Versioning | Content hash + manifest; never silent revise |
| Trust | Reject incomplete, non-monotonic timestamps, unversioned revisions |

**This document does not authorize network fetch.** Design is locked first.

---

## 3. Join / lag rules (binding)

1. **Publish time:** An OI observation is known only at its exchange timestamp `oi_time` (UTC).  
2. **As-of merge:** For daily bar with decision at bar close `t_close`, use last OI with `oi_time ≤ t_close`.  
3. **Signal lag:** Position from closed bar `t` → fill at **open of t+1** (lab default).  
4. **No forward fill from future snapshots.** Missing OI → feature NaN → rule false.  
5. **Daily features** (causal / past-only only):

| Feature | Definition |
|---------|------------|
| `oi_last` | Last known OI level as of `t_close` |
| `oi_chg_1d` | `oi_last` minus prior daily as-of `oi_last` (bar space) |
| `oi_chg_pct_1d` | percent change of daily as-of OI |
| `oi_z_60` | z-score of `oi_last` vs rolling/expanding **past-only** daily window |
| `oi_high` | `oi_last` above expanding median (causal) |
| `oi_rising` | `oi_chg_1d > 0` |
| `oi_falling` | `oi_chg_1d < 0` |
| `oi_sum_chg_5d` | sum of daily `oi_chg_1d` over past 5 closed days (past-only) |

6. **Optional price interaction (≤2 hyps):** use existing causal price features only (`above_sma_200`, `mom_pos_20`) — **no new price grids**.  
7. **Calendar alignment:** OHLCV daily index is master; OI is right-asof joined.

---

## 4. Economic mechanisms (pre-registered families)

| Family | Claim (falsifiable) |
|--------|---------------------|
| `family_oi_level` | Extremely high OI (crowded stock of leverage) precedes poor long-only continuation → flatten when `oi_high` |
| `family_oi_change` | Rapid OI expansion (new leverage) marks fragile risk-on → avoid longs when OI rising hard |
| `family_oi_unwind` | Falling OI after stress can mark de-leveraging completion → allow long only with mild trend (one formulation) |
| `family_oi_trend_gate` | Trend-following only when OI is not elevated (one interaction) |

**Not in budget:** funding×OI grids, multi-asset OI basis, liquidation heatmaps, NN, Polymarket/X.

---

## 5. Pre-registered hypotheses (≤10)

Locked **before** seeing confirmatory results. YAML to be materialised under
`examples/batch/oi/` **only at execution time**.

| ID | Family | Entry (closed daily bar) | Exit | Rationale |
|----|--------|--------------------------|------|-----------|
| `hyp_oi_high_flat` | level | `oi_high==1` → flat; else `above_sma_200==1` | inverse | Crowded OI stock → avoid |
| `hyp_oi_z_high_flat` | level | `oi_z_60 > 1` → flat; else `mom_pos_20==1` | inverse | Extreme OI z |
| `hyp_oi_rising_flat` | change | `oi_rising==1 and above_sma_200==1` → flat… | see YAML | Expanding leverage |
| `hyp_oi_chg_pct_high_flat` | change | large positive `oi_chg_pct_1d` flag (fixed: &gt; expanding 80% causal quantile of past chg_pct) → flat within trend | inverse | One fixed causal quantile — not a grid |
| `hyp_oi_sum5_high_flat` | change | `oi_sum_chg_5d` high flag (expanding median of positive sums) | inverse | Multi-day OI build |
| `hyp_oi_trend_and_not_high` | trend_gate | `above_sma_200==1 and oi_high==0` | inverse | Single interaction |
| `hyp_oi_high_exit_only` | level | enter `above_sma_200==1`; exit if `oi_high` or trend breaks | — | Exit-filter form |
| `hyp_oi_falling_long` | unwind | `oi_falling==1 and above_sma_50==1` | not that | De-lever + mild trend (one) |
| `hyp_oi_z_low_long` | unwind | `oi_z_60 < -1 and mom_pos_20==1` | inverse | Depressed OI + mom (one) |
| `hyp_oi_only_not_high_mom` | composite | `oi_high==0 and mom_pos_20==1` | inverse | Single composite |

**Falsification:** val gates fail; 2× cost stress fails; or sparse noise with reality reject.

**Multiplicity:** One programme; **no** post-hoc OI threshold search on the same data after lock.

---

## 6. Explicit non-goals

- Softening gates because OI is “slow”  
- Combining funding features in this v1 (wait for both single-series autopsies)  
- Using mock OI for scientific promotion  
- Live/paper/shadow  
- X / Polymarket / news

---

## 7. Implementation map (future)

| Artefact | Path (planned) |
|----------|----------------|
| This design | `docs/PROGRAMME_OI_PIT_V1.md` |
| Programme config | `configs/programmes/oi_btc_usdt_m_daily_v1.yaml` |
| PIT join + features | `src/crl/shared/data/oi.py` (to build) |
| Mock series | `src/crl/shared/data/sources/oi_mock.py` (to build) |
| Pre-registered hyps | `examples/batch/oi/` (at execute) |
| Tests | `tests/test_oi_pit.py` (at implement) |

---

## 8. Execution order (later)

1. Implement OI PIT module + mock tests (mirror funding).  
2. Ingest versioned real OI history when authorized.  
3. Join to daily OHLCV; batch ≤10 exploratory on temp registry.  
4. Gate autopsy + Thesis Tree (`oi` / crowding stock mechanism node).  
5. Only then consider funding×OI or 4h OI as **new** programmes.

---

## 9. Relationship to funding

| Series | Economic role | Status |
|--------|---------------|--------|
| Funding | Cost / flow of leverage | Daily v1 **null**; 4h power design optional |
| OI | Stock of open leverage | **This programme** — untested true series |
| Funding × OI | Interaction | **Blocked** until both single-series results exist |

Do not treat funding null as OI evidence (or vice versa).
