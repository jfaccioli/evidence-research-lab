# Evidence Investment Review — Economic Inefficiency Programme  
**Date:** 2026-07-30  
**Authority:** Research Director / Economic Inefficiency Programme V1  
**Question:** What is the **smallest external dataset** capable of testing the **highest-ranked** remaining inefficiency?

---

## 0. Executive recommendation

| Item | Decision |
|------|----------|
| **Top inefficiency** | Spot BTC **ETF creation/redemption** (`ineff_etf_create_redeem`) |
| **Can free shelf test it?** | **No** — lab has no ETF flow / shares-outstanding series |
| **Recommended acquisition** | **Free delayed daily aggregate US spot BTC ETF net flows** (BTC preferred) with documented publish lag |
| **Pay for vendor API now?** | **No** — free delayed tables first (Farside-class / SoSoValue-class public daily); paid only if free path fails PIT or completeness |
| **Do not buy** | Another CMD-style exchange netflow clone; options history before ETF free path |

**One line:** The most plausible remaining temporary predictability is structural ETF primary-market flow; the lab should acquire the **smallest free delayed flow series**, not invent another OHLCV transform.

---

## 1. Why this inefficiency ranks first

From `research_kb/rd/inefficiency_catalogue.json` (IScore ranking):

1. **Economic story** is post-2024 structural, not a recycled technical.  
2. **Participants** (APs, issuers) are identifiable; lag is operational, not mystical.  
3. **Observables** are daily and publicly discussed; free delayed compilations exist.  
4. **Overlap** with retired free netflow is **low** (different mechanism: primary ETF pipe vs exchange deposit/withdraw).  
5. Maps to deployable envelope: BTC spot, long/flat or size overlay, daily lag, limited turnover if using flow *regime* not high-frequency.

---

## 2. Economic protocol answers (ETF create/redeem)

| # | Answer |
|---|--------|
| **1. Why exist?** | Create/redeem forces BTC demand/supply when AUM flows; lumpy institutional allocation. |
| **2. Who?** | APs, ETF issuers, institutional allocators. |
| **3. Why not arbed away?** | Operational lag, AP capital, NAV window, inventory risk, primary-market hours. |
| **4. Observables?** | Net flows, shares outstanding, premium/discount, publish timestamps. |
| **5. Lab has?** | **No.** |
| **6. Min data?** | Daily **aggregate** US spot BTC ETF net flow (all major funds) + conservative publish lag (≥1 business day if same-day print unreliable). |

---

## 3. Minimum dataset specification (freeze before fetch)

| Field | Requirement |
|-------|-------------|
| **Series** | `us_spot_btc_etf_net_flow_btc` (or USD) daily |
| **History** | From 2024-01-11 (or earliest consistent) to present |
| **PIT** | `event_time` = last moment flow is known for decisions; if source publishes next UTC morning, lag accordingly |
| **Granularity** | Daily is enough for first programme (matches deploy envelope) |
| **Funds** | Aggregate OK for v1; per-fund optional later |
| **Format** | Versioned parquet + meta hash under `data/processed/etf/` |
| **Cost class** | Free delayed public table preferred |

### Acceptable free sources (examples — verify ToS before scrape)

| Source class | Notes |
|--------------|--------|
| Public daily ETF flow tables (Farside-style research pages) | Often used in academic/industry summaries; manual or careful scrape with lag |
| SoSoValue / similar free crypto data UIs | Free display; check export/API terms |
| Issuer 19b-4 / holdings filings | Higher integrity, slower, incomplete for daily |

### Paid (only if free fails)

| Option | When |
|--------|------|
| NewHedge / The Block / CoinGlass / Bloomberg-class ETF flow API | Free path incomplete, non-PIT, or unstable |

**Prefer one-time export / fixed history dump over open-ended subscription** (prior EIR doctrine).

---

## 4. What we will **not** claim after acquisition

- Automatic alpha  
- Same-day trading of unpublished flow  
- Re-use of free CMD netflow conf-null operationalisations  

## 5. Programme that may open **after** data lands

**Name (draft):** `PROGRAMME_ETF_FLOW_INEFF_V1`  

| Item | Draft freeze |
|------|----------------|
| Mechanism | ETF create/redeem demand shock |
| Hypothesis | Lagged positive net creations associate with higher subsequent BTC returns **or** lower risk-off (pre-reg one primary target only) |
| Decision | Long/flat or size overlay under PCS envelope |
| Baseline | B&H + cash + random control (platform) |
| Trial cost | ≤4 pre-reg hyps; family ledger |
| Reject if | Null under costs + lag + confirmatory split |

**Do not open** the programme until the series is pinned and PIT policy written.

---

## 6. Comparison: next inefficiencies (why not first)

| Rank | Inefficiency | Blocker |
|------|--------------|---------|
| 2 | Options dealer hedge | Data cost + PIT; after ETF |
| 3 | Forced liquidations | High overlap with conf-null free series |
| 4 | Stablecoin mint/burn | Good #2 free path if ETF free fails |

---

## 7. Human action (if free scrape blocked)

1. Confirm ToS for chosen free flow table **or** approve **minimal paid export** of daily aggregate US spot BTC ETF flows only.  
2. No open-ended multi-product subscription without second EIR.  
3. After pin: RD opens `PROGRAMME_ETF_FLOW_INEFF_V1` under Alpha Discovery gates.

---

## 8. Decision log

| Decision | Value |
|----------|--------|
| Suspend deployable strategy fishing from free shelf | **Yes** |
| Highest inefficiency | ETF create/redeem |
| Free shelf sufficient | **No** |
| Smallest next information | Daily aggregate ETF net flow + lag |
| Pay now | **No** (free delayed first) |
| Interrupt for human | Only if free path blocked by ToS/credentials/paywall |

*End of EIR.*
