# Programme: Point-in-time BTC USDT-M funding rates (v1)

**Status:** Designed + implementation scaffolded (mock PIT path).  
**Authority:** Meta-research recommendation; human standing research policy.  
**Mode:** Research only — no paper/shadow/live; no gate softening.  
**Budget:** ≤ **10** pre-registered exploratory hypotheses (1u each planned).  
**Lineage:** same `research_lineage_id` as main BTC research (H5 default).

---

## 1. Scientific question

> Does **exchange-native perpetual funding** (USDT-M BTC), as a point-in-time
> state variable of leverage/crowding cost of capital, support a **pre-registered,
> fail-closed** long-only daily rule that survives costs and existing gates —
> or is the claim a clean null on this horizon?

Prior `funding_proxy` / OHLCV stand-ins **do not** falsify true funding.

Success:

1. **Clean null** that retires “funding level/change on daily BTC spot long-only”, or  
2. Exploratory pass → **nominate** confirmatory under **unchanged** gates.

---

## 2. Dataset (PIT)

| Field | Spec |
|-------|------|
| Instrument | BTCUSDT perpetual (USDT-M), funding rate series |
| Source class (live fetch later) | `exchange_native` (e.g. Binance public funding history) |
| Mock / unit tests | `funding_mock` — deterministic synthetic series for join tests only |
| Granularity | Native funding events (~8h on major venues); mapped to **daily decision bars** |
| Versioning | Same discipline as OHLCV: content hash + manifest; never silent revise |
| Trust | Exchange-native base; reject incomplete/non-monotonic/unversioned revisions |

**No live network fetch is required for v1 scaffold.** Real history ingestion is a
later step when network/authorization is available; science join rules are locked now.

---

## 3. Join / lag rules (binding)

1. **Publish time:** A funding observation is known only at its
   `funding_time` (payment/settlement timestamp, UTC).  
2. **As-of merge:** For daily bar with decision at **bar close** `t_close`, the
   funding value available is the last funding with `funding_time ≤ t_close`.  
3. **Signal lag:** Position uses signal from closed bar `t` → fill at **open of t+1**
   (lab default). No same-bar funding peek beyond close.  
4. **No forward fill from future events.** Missing funding → feature NaN → rule false.  
5. **Daily aggregation features** (computed only from as-of-known series):
   - `funding_last` — last known rate as of bar close  
   - `funding_8h` — same as last event rate (native step)  
   - `funding_sum_24h` — sum of funding events in the trailing 24h window ending at t_close (events with funding_time in (t_close−24h, t_close])  
   - `funding_chg_1` — `funding_last −` previous event’s rate (event space), as-of t_close  
   - `funding_z_60` — z-score of `funding_last` vs expanding/rolling **past-only** window of prior daily `funding_last`  
   - `funding_pos` / `funding_neg` — sign flags  
   - `funding_high` — `funding_last` above expanding median (causal)  

6. **Calendar alignment:** OHLCV index is the master; funding is right-asof joined.

---

## 4. Economic mechanisms (pre-registered families)

| Family | Claim (falsifiable) |
|--------|---------------------|
| `family_funding_level` | Extreme positive funding (longs pay) predicts poor long-only continuation → avoid/flat when funding high |
| `family_funding_change` | Rising funding (crowding into longs) predicts worse risk-adjusted long returns |
| `family_funding_trend_gate` | Funding filter only when price trend is already long (one interaction, not a grid) |
| `family_funding_mean_revert` | After very negative funding (shorts crowded), long-only mean-reversion window |

**Not in budget:** OI grids, multi-exchange arb, 4h funding micro-structure, NN.

---

## 5. Pre-registered hypotheses (≤10)

Locked **before** seeing confirmatory test results. Exploratory only until gates say otherwise.

| ID | Family | Entry (closed bar) | Exit | Rationale |
|----|--------|--------------------|------|-----------|
| `hyp_funding_high_flat` | level | `funding_high == 1` → flat; else allow long if `above_sma_200 == 1` | inverse | Crowding: pay-funding regime avoid longs |
| `hyp_funding_pos_flat` | level | `funding_pos == 1` → flat; else `above_sma_200 == 1` | inverse | Simpler sign filter |
| `hyp_funding_neg_long` | mean_revert | `funding_neg == 1 and above_sma_50 == 1` | not that | Negative funding + mild trend |
| `hyp_funding_z_high_flat` | level | `funding_z_60 > 1` → flat; else `mom_pos_20 == 1` | inverse | Extreme z crowding |
| `hyp_funding_z_low_long` | mean_revert | `funding_z_60 < -1 and mom_pos_20 == 1` | inverse | Crowded short extreme |
| `hyp_funding_chg_up_flat` | change | `funding_chg_1 > 0 and above_sma_200 == 1` → flat… | see YAML | Rising funding pressure |
| `hyp_funding_sum24_high_flat` | level | `funding_sum_24h` high flag | see YAML | 24h cumulative pressure |
| `hyp_funding_trend_and_not_high` | trend_gate | `above_sma_200 == 1 and funding_high == 0` | inverse | One interaction only |
| `hyp_funding_only_neg_mom` | composite | `funding_neg == 1 and mom_pos_20 == 1` | inverse | Funding+momentum (single combo) |
| `hyp_funding_high_exit_only` | level | enter `above_sma_200 == 1`; exit if `funding_high == 1` or trend breaks | — | Exit-filter variant |

Exact expressions are frozen in `examples/batch/funding/*.yaml`.

**Falsification (all):** after-cost Sharpe / trade count fail gates on val; or fragility under 2× costs; or single-regime only without economic story intact.

---

## 6. Multiplicity / budget

- Programme counts as **one research programme** for multiplicity lineage.  
- Each evaluated hyp counts under existing trial ledger rules when P1 path is used.  
- **No** parameter grid around funding thresholds beyond the 10 locked YAMLs.  
- Confirmatory peek only after exploratory nomination + budget (existing gates).

---

## 7. Explicit non-goals

- Live/paper/shadow trading  
- Softening `min_trades` or costs  
- Claiming sentiment/X/Polymarket  
- Using mock funding results as scientific evidence for promotion  
- Network fetch of exchange history until separately authorized and hashed

---

## 8. Implementation map

| Artefact | Path |
|----------|------|
| This design | `docs/PROGRAMME_FUNDING_PIT_V1.md` |
| Programme stub config | `configs/programmes/funding_btc_usdt_m_daily_v1.yaml` |
| PIT join + features | `src/crl/shared/data/funding.py` |
| Mock series | `src/crl/shared/data/sources/funding_mock.py` |
| Pre-registered hyps | `examples/batch/funding/` |
| Tests | `tests/test_funding_pit.py` |

---

## 9. Next steps after scaffold

1. Ingest real Binance (or chosen venue) funding history → versioned parquet + manifest.  
2. Join to existing BTC 1d OHLCV; recompute features; run `crl batch` on the 10 hyps **exploratory**.  
3. Update Thesis Tree / learnings with null or nominate.  
4. Only then consider confirmatory budget.

**Blocked for real runs:** network fetch of historical funding + human OK to spend research budget units on the batch.
