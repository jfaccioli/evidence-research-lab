# Evidence Investment Review — Phase 1b  
## Historical Deribit BTC options OI / gamma structure

**Date:** 2026-07-30  
**Authority:** Research Director (post free-path Phase 1 conclusion **B**)  
**Question:** What is the **single** paid (or free-if-found) dataset that most improves P(correct conclusion about deployable edge)?

---

## 0. Executive recommendation

| Item | Decision |
|------|----------|
| **Phase 1 free path** | **Exhausted** — ETF / stablecoin-growth / miner-revenue all exploratory null under gates |
| **Recommended acquisition** | Historical **BTC options open interest by strike & expiry** on Deribit (greeks/IV if bundled), snapshot-timestamped for PIT |
| **Pay now?** | **Human only** — default lab paid budget remains $0 |
| **Do not buy** | Another CMD-style netflow; ETF re-vendor after free Farside null; multi-product “terminal” without OI history; free options OHLCV alone |
| **If human declines** | Issue / keep **C** (unlikely robust edge under current constraints) and stop alpha expansion |

**One line:** The only remaining high-EV untested structural channel compatible with our long/flat mandate is **options dealer positioning**; free historical PIT for it is **not** available; one capped history export is the honest next step — or stop.

---

## 1. Why not continue free programmes

| Candidate free idea | Scientific Reviewer kill reason |
|---------------------|--------------------------------|
| More OHLCV technicals | Family mass exhausted; PCS rejected deployable free-shelf candidates |
| ETF flow variants | Family retired; lag-1 aggregate null; literature supports level cointegration more than daily forecast |
| Free “options” OHLCV without OI | Cannot construct dealer gamma; collapses to IV/vol near-clones |
| Live Deribit OI scrape from today only | No history → insufficient sample / no retrospective science under gates |
| Another on-chain free proxy | High overlap with null families; low IScore after learning |

Burning confirmatory or inventing “programme 4” without a new data class would optimise **activity**, not **truth**.

---

## 2. Economic protocol (options dealer hedge)

| # | Answer |
|---|--------|
| **1. Why exist?** | Dealers short options to clients must delta-hedge; net gamma near large strikes/expiries can force mechanical buying/selling of underlying as spot moves. |
| **2. Who?** | Options market makers / dealers on Deribit (dominant BTC OI venue), clients with directional options, leveraged vol traders. |
| **3. Why not arbed immediately?** | Inventory and risk limits; discrete hedge rebalancing; incomplete public real-time positioning historically; capacity and basis between options and spot/perp. |
| **4. Observables?** | OI by strike/expiry, call/put split, mark IV, dealer gamma proxy (if greeks available), expiry calendar, spot distance to max-OI strikes. |
| **5. Lab has?** | **Live** book summary OI (no historical journal); **no** free historical greeks. |
| **6. Min data?** | Daily (or EOD) snapshots of OI×strike×expiry for BTC options ≥2y if possible, with snapshot time for PIT lag policy. |

---

## 3. Literature / industry prior (not a strategy copy)

- Equity options: dealer gamma / “GEX” narratives — mechanical hedge flows near high open interest (industry research dense; treat as **hypothesis generator**, not proof).  
- Crypto: Deribit accounts for the bulk of BTC options OI; public metrics show multi-ten-billion notional OI and strike concentration around key levels.  
- Spot ETF flow research: cointegration / long-run demand (consistent with structure) but **weak daily predictive edge** after lags — aligns with our free ETF programme null.  
- Crypto futures carry (e.g. BIS-style limits to arbitrage): often **delta-neutral** edges; poor fit to pure long/flat without mandate change.

**Extraction for us:** Test **whether lagged options positioning/gamma regime** predicts *subsequent* spot returns or risk-off need — falsify against calendar-only and vol-only baselines.

---

## 4. Free-path attempt (Data Reviewer)

| Probe | Result |
|-------|--------|
| Deribit `get_book_summary_by_currency` (options) | Live OI + mark IV fields; **no greeks** in summary; **no historical** endpoint for full chain OI |
| Free options OHLCV dumps | Price/volume by contract; **insufficient** for OI-weighted gamma |
| CoinGlass-class free pages | Unstable / incomplete for scientific pin + ToS risk |

**Verdict:** Free path for *historical* dealer-relevant OI **fails**. Do not fake a series.

---

## 5. Minimum dataset specification (freeze before purchase)

| Field | Requirement |
|-------|-------------|
| **Venue** | Deribit BTC options (primary) |
| **Series** | End-of-day (or fixed UTC snapshot) OI by instrument or by strike×expiry×call/put |
| **History** | Prefer ≥ 2022-01-01 or earliest consistent vendor history; document gaps |
| **PIT** | `event_time` = first time snapshot is known; if vendor EOD next morning, lag ≥1 session |
| **Optional** | Mark IV, greeks (gamma) if same snapshot — improves proxy quality |
| **Format** | Versioned parquet under `data/processed/options/` + meta hash |
| **Cost class** | One-time export preferred; subscription only if export unavailable and human OK |

### Acceptable vendors (examples — human compares ToS/price)

| Class | Notes |
|-------|--------|
| Amberdata / GVol-style OI+gamma history | Explicit gamma levels products exist commercially |
| CoinAPI / similar options history with OI | Verify OI field completeness historically |
| Direct Deribit historical purchase if offered | Prefer primary |

**Prefer fixed history dump over open-ended multi-market terminal.**

---

## 6. Programme allowed after pin only

**Draft name:** `PROGRAMME_OPTIONS_DEALER_GAMMA_V1`  

| Item | Freeze |
|------|--------|
| Hyps | ≤ **4** exploratory; ≤ **1** confirmatory |
| Family | `family_options_dealer_gamma_v1` (new; not a reopen) |
| Mapping | Long/flat or size-down under existing envelope |
| Baselines | B&H, cash, SMA trend, pure expiry-calendar dummy, pure RV |
| Reject if | Null under costs+lag; or edge = calendar/vol only |

**If null:** Phase 1 conclusion upgrades **B → C**. No automatic second paid dataset.

---

## 7. EV vs cost (qualitative)

| Factor | Assessment |
|--------|------------|
| P(untested structural edge exists) | Highest among remaining classes |
| P(survives our gates as long/flat) | Moderate-low (honest) — still best free-path-relative EV |
| Cost of **not** buying | We may stop at B without learning; risk of under-exploring true edge |
| Cost of buying wrong data | High if OI missing / non-PIT → **fail closed**, demand refund path |
| Alternative: accept C now | Correct if human capital/time values certainty of stop over residual option value |

---

## 8. Human decision menu

1. **Approve Phase 1b** — capped USD for one options OI/gamma history export meeting §5; RD executes single programme under frozen gates.  
2. **Accept C** — unlikely robust edge under current constraints; freeze alpha; optional productise research OS.  
3. **Pause** — keep B on record; no spend; no new free fishing.

---

## 9. Explicit non-goals

- Not a request to rebuild architecture  
- Not permission to reopen free families  
- Not automatic micro-live  
- Not strategy cloning from Twitter/GEX dashboards  

---

*RD belief state: `research_kb/rd/RD_BELIEF_STATE.md`*
