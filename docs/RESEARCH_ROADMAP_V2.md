# Research Roadmap Version 2 — Search Space Shift

**Effective:** 2026-07-28  
**Basis:** `docs/SEARCH_SPACE_REVIEW_2026-07-28.md`  
**Standards:** Frozen gates / no leverage / fail-closed promotion — **unchanged**  
**Why V2:** V1 grammar (unconditional daily long/flat on public levels) has been **honestly exhausted** across technicals, funding/OI, free on-chain, PM odds/panel, FRED macro. Zero confirmatory survivors.

---

## V1 → V2 (what changes)

| Dimension | V1 (retire as default) | V2 (new default) |
|-----------|------------------------|------------------|
| Core question | “Does feature X beat gates if long/flat?” | “What **scientific object** might still be predictable under our constraints?” |
| Hypothesis unit | Indicator / series level filter | **Class**: conditional, cross-asset, vol target, risk policy |
| Prediction target | Directional long-only | Direction **or** vol/risk/relative (pre-reg) |
| Asset coupling | Single-name BTC | BTC **and** lagged cross-asset (ETH) |
| Data priority | New free daily series of same shape | Free data that enables **new class** first |
| Engineering | Only if blocks a V2 class | Same |

**What does not change:** confirmatory holdout, costs, min_trades, no test tuning, no leverage, paper→shadow→live ladder.

---

## V2 programme queue (ranked)

### Tier 1 — Free data, new grammar (start here)

| ID | Programme class | Prediction object | Data | EV | First lock |
|----|-----------------|-------------------|------|-----|------------|
| **V2-A** | **Vol forecast → risk policy** | Forecast next-horizon realized vol / range; flat or reduce risk when high | BTC OHLCV only (have) | **Highest free** | `PROGRAMME_VOL_FORECAST_V2` |
| **V2-B** | **Cross-asset transfer** | Lagged BTC returns/vol → ETH long/flat (or relative) | BTC+ETH OHLCV (have) | High | `PROGRAMME_CROSS_ASSET_V2` |
| **V2-C** | **Conditional technical** | Pre-reg **vol regime state** × simple trend (interaction only; not new SMAs) | BTC OHLCV | Medium–high | `PROGRAMME_CONDITIONAL_TREND_V2` |
| **V2-D** | **Risk-as-edge** | Pre-reg DD/vol stops on a **fixed** baseline long; evaluate utility/DD not only Sharpe | BTC OHLCV | Medium–high | `PROGRAMME_RISK_POLICY_V2` |

### Tier 2 — Free/new data when available

| ID | Class | Note |
|----|-------|------|
| **V2-E** | Spot **ETF flow** state | After free reconstructible series; structural demand |
| **V2-F** | Event residual (PM) | Only with multi-event outcomes; after path-panel null, low priority |

### Tier 3 — Paid / heavy (EIR required)

| ID | Class | Note |
|----|-------|------|
| **V2-G** | Vendor inventory / labeled flow | Only if Tier 1 null **and** EIR still ranks paid first |
| **V2-H** | Options skew | Defer |
| **V2-I** | Microstructure L2 | Out of live mandate; research-only if ever |

### Explicitly retired as default generators

- Free CMD-style daily on-chain level filters  
- Unconditional PM path binaries / path panels of same shape  
- Technical clone families (SMA/volume/breakout spam)  
- “One more FRED series as long/flat level filter” without conditioning/vol target redesign  

---

## V2-A sketch (first programme — ready to implement next)

**Why first:** Uses data we **already have**; changes **target** (vol) and **use** (risk policy); literature prioritises vol over directional crypto forecasts under low SNR; low acquisition cost; moderate complexity.

**Mechanism:** Volatility clusters; forecasting σ improves when to be flat / reduce exposure.

**Differ from V1 vol_regime programme:** Prior work used vol as **filter for direction**. V2-A primary scientific claim is **forecast skill** of next-period realized vol, then a **pre-registered** mapping forecast→position (e.g. flat if forecast vol > expanding quantile). Two-stage, locked before results.

**PIT:** Expanding quantiles / lagged RV only.

**Overfit control:** ≤4 hyps; one family; no feature shopping after first look.

---

## Success metrics for V2

| Success | Not success |
|---------|-------------|
| Clear null or survivor **per new class** | Programme count |
| Uncertainty reduction on *search space* | Pretty vol charts |
| Confirmatory candidate under frozen gates | Softened gates |
| Honest “class exhausted” | Infinite indicator mining |

---

## Immediate autonomous plan

1. ✅ Search space review (this doc + companion review).  
2. **Next:** Implement **V2-A** vol-forecast programme under frozen standards (no new paid data).  
3. Then **V2-B** cross-asset with existing ETH pin.  
4. Re-EIR before any paid spend.

---

## One-line thesis

**V1 asked the wrong average question with the right scientific method; V2 keeps the method and changes the question.**
