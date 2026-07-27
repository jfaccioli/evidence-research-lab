# Programme: Funding PIT — 4h power study (v1) — **DESIGN ONLY**

**Status:** Pre-registered design lock. **No data fetch. No runs. No threshold mining.**  
**Parent result:** Daily funding PIT v1 programme null + gate autopsy  
(`docs/PROGRAMME_FUNDING_PIT_V1.md`, `examples/batch/funding/GATE_AUTOPSY_V1.md`).  
**Mode:** Research only — no paper/shadow/live; **gates unchanged**.  
**Budget:** ≤ **6** pre-registered exploratory hypotheses (tight; power-focused).  
**Authority:** Follow-on from autopsy Cluster A (min_trades-limited near-misses).

---

## 1. Scientific question

> On **4h** bars, do the **same economic funding-level claims** that failed daily
> only (or mainly) on `min_trades` / few-trade reality checks survive **unchanged
> gates** with adequate trade count — or does higher frequency also fail bootstrap
> / excess / cost stress?

This is a **power and horizon** test, **not** a new funding-threshold grid.

Success:

1. Clean null at 4h for the locked level filters → strengthens “not just daily underpower,” or  
2. Exploratory pass under frozen gates → **nominate** confirmatory (gates still frozen).

---

## 2. Why this programme exists (autopsy link)

| Daily autopsy fact | Implication for 4h |
|--------------------|--------------------|
| 6/10 failed `min_trades` | Power may be insufficient on daily |
| `high_flat` & `trend_and_not_high`: CI lo &gt; 0, excess &gt; 0, n=19 only | **Primary targets** for power study |
| 4/10 had n≥30 and still failed bootstrap | 4h is **not** assumed to “fix” funding |
| Mean-revert cluster multi-gate dead | **Excluded** from 4h budget (do not revive) |

---

## 3. Dataset / bars (when executed later)

| Field | Spec |
|-------|------|
| OHLCV | BTC/USDT **4h**, versioned parquet + manifest (same discipline as 1d) |
| Funding | Same true exchange series as daily programme (`exchange_native`); **no mock for science** |
| Join | As-of: last `funding_time ≤ bar close`; signal → **next bar open** (lab default) |
| Features | Reuse funding PIT feature definitions from `funding.py` on 4h master index |
| Costs | **Same** cost model / stress as default config (do not cheapen for 4h) |

**Not in this design step:** network fetch, feature build, or batch execution.

---

## 4. Binding constraints

1. **No new funding thresholds** — reuse daily locked feature flags (`funding_high`, `funding_pos`, causal median/z definitions).  
2. **No mean-revert revival** — `neg_long` / `z_low_long` / `only_neg_mom` out of budget.  
3. **No gate softening** — `min_trades`, bootstrap CI, cost stress, reality checker stay as in `configs/default.yaml`.  
4. **Separate multiplicity programme** — new programme id; do not pretend these are free re-tests of daily.  
5. **Exploratory only** until nomination rules say otherwise.

---

## 5. Pre-registered hypotheses (≤6)

Exact YAML paths to be added under `examples/batch/funding_4h/` **only when executing**; expressions locked here.

| ID | Claim | Entry (closed 4h bar) | Exit | Maps from daily |
|----|-------|----------------------|------|-----------------|
| `hyp_f4h_high_flat` | High funding → avoid long | `funding_high==1` → flat; else `above_sma_200==1` (200 bars @4h ≈ 33d) | inverse | `hyp_funding_high_flat` |
| `hyp_f4h_trend_and_not_high` | Trend only when funding not high | `above_sma_200==1 and funding_high==0` | inverse | `hyp_funding_trend_and_not_high` |
| `hyp_f4h_high_exit_only` | Funding as exit filter | enter trend; exit if `funding_high` or trend breaks | — | `hyp_funding_high_exit_only` |
| `hyp_f4h_pos_flat` | Sign filter (simpler level) | `funding_pos==1` → flat; else mild trend | inverse | `hyp_funding_pos_flat` |
| `hyp_f4h_chg_up_flat` | Rising funding pressure | `funding_chg_1>0` avoid within trend | see YAML | `hyp_funding_chg_up_flat` |
| `hyp_f4h_z_high_flat` | Extreme z crowding | `funding_z_60>1` → flat else mom gate | inverse | `hyp_funding_z_high_flat` |

**SMA window note:** `above_sma_200` on 4h is **not** calendar-identical to daily SMA-200; it is the pre-registered operationalisation for “slow trend on this bar grid.” Do not grid alternative windows in this programme.

**Falsification:** fail val gates; or pass only via cost blindness; or trade count still sparse without economic story.

---

## 6. Explicit non-goals

- Daily threshold re-mining  
- Softening `min_trades` because “4h should have more trades”  
- Mean-revert funding longs  
- OI, X, Polymarket  
- Live/paper/shadow  
- Claiming 4h results apply to daily without a new design

---

## 7. Execution checklist (later — not now)

1. Ingest/version 4h OHLCV if missing.  
2. Join funding → 4h features; unit tests for as-of.  
3. Materialise 6 YAMLs from this lock; `crl batch` exploratory + temp registry.  
4. Gate autopsy; Thesis Tree update; **no** threshold chase.  
5. Confirmatory only if exploratory nomination earned.

---

## 8. Budget / stop rules

- Max **6** exploratory evals in this programme version.  
- If all fail: record null; **stop** funding-level long-only line unless a *new* economic claim (e.g. OI interaction) is designed.  
- If any pass: freeze, nominate, do not expand the family ad hoc.
