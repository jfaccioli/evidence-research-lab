# Living evidence acquisition roadmap

**Updated:** 2026-07-28  
**Objective:** Maximise access to **genuinely novel predictive information** under frozen scientific standards.  
**Not the objective:** More lab engineering theatre; more free CMD-style clone filters.

Machine catalog: `research_kb/evidence_acquisition_catalog.json`  
CLI: `python -m crl evidence-acq`

---

## Decision rule (when cost is justified)

Recommend **spend money** only if **all** hold:

1. **Novelty** — not near-duplicate of a spent operationalisation (see free-series null wave).  
2. **PIT feasibility** — timestamps / lag policy can be stated and tested.  
3. **Programme ready** — ≤8 pre-registered hyps + design doc *before* purchase.  
4. **Sample adequacy** — expected history supports min_trades + train/val/test under our gates.  
5. **Cost / EV** — expected information gain × mandate fit ≥ financial cost (personal AUD scale).  
6. **Integration** — drop-in parquet path already exists (`data/processed/external|flow`); no multi-month platform build.

**Do not buy** “to browse charts” or “because funds use Glassnode.”

**Prefer free first** when a free archive is within ~one programme of the paid claim.

---

## Ranked acquisition queue (living)

Scores: **novelty** (vs lab evidence), **PIT**, **history**, **cost**, **effort**, **overall EV** (1–5; higher better). Costs are order-of-magnitude public list prices, not quotes.

| Rank | Source / class | Cost | Nov | PIT | Hist | Effort | EV | Recommendation |
|------|----------------|------|-----|-----|------|--------|----|----------------|
| **1** | **Polymarket+Kalshi multi-market archives** (e.g. public GitHub prediction-market datasets; free CLOB we already use) | Free | 4 | 3 | 3–4 | Med | **4.5** | **Acquire/process free next** — multi-event panel, not single $150k binary |
| **2** | **Vendor exchange-flow with export/hash** (CryptoQuant / Glassnode exchange netflow) | ~USD 30–100+/mo or export | 3 | **4–5** | 5 | Low* | **4.0** | **Buy only after** free panel path done *or* you accept paid for revision-quality PIT; **one fixed export preferred over open-ended sub** |
| **3** | **Stablecoin large-transfer / whale event studies** (academic papers + reconstructible transfers) | Free–low | 4 | 3 | 3 | High | **3.5** | Design first; use published event lists + free chain data if possible |
| **4** | **Macro / rates / DXY daily** (FRED etc.) as risk-off filter for BTC | Free | 3 | 5 | 5 | Low | **3.5** | **Free acquire** — orthogonal to spent on-chain clones; pre-reg small programme |
| **5** | **Cross-asset (ETH) with non-technical features** | Free OHLCV | 2 | 5 | 5 | Low | **2.5** | Only with new feature class (not SMA clones) |
| **6** | **Social/X historical firehose** | Paid / restricted | 4 | 2 | ? | High | **2.5** | Blocked without archive; human keys if pursued |
| **7** | **Order-book / L2 crypto** | High | 3 | 2 | ? | Very high | **1.5** | **Reject** for personal spot mandate |
| **8** | More free CMD daily metrics (MVRV-like, premium, liq clones) | Free | 1 | 2 | 4 | Low | **1.0** | **Reject** — spent operationalisation class |
| **9** | Full BTC tx-graph academic dumps | Free | 3 | 2 | 5 | Very high | **1.5** | Defer — wrong grain for current daily long-only lab |

\*Integration low **because** series attach tooling already ships.

---

## Explicit spend recommendation (human)

| Action | When |
|--------|------|
| **Do not buy now** | You want charts only; no locked programme waiting |
| **Prefer free #1 + #4 first** | Zero cost; high novelty vs spent free on-chain filters |
| **Consider paid #2 (export)** | After free panel/macro null *or* if you prioritise vendor-grade netflow PIT; prefer **one-time export** of BTC (+ETH) exchange netflow with documented lag, not perpetual subscription “to feel live” |
| **Cost threshold (guidance)** | For this lab: if annual data cost ≫ expected learning value of **one** confirmatory programme, skip. Rule of thumb: **≤ one month personal research budget** for a single pre-reg programme with clear exit (null is success) |

---

## Already tried (do not re-buy for same claim)

| Class | Lab result |
|-------|------------|
| Free CMD BTC netflow / stablecoin / premium / liq / MVRV | Null or conf kill |
| Single Polymarket year-end binary | Expl null (sample/design) |
| Funding / OI public | Prior nulls |
| BTC OHLCV technicals | Exhausted under gates |

---

## Minimum tooling (present / to build)

| Need | Status |
|------|--------|
| Drop parquet → attach via INDEX | **Done** (`crl run-programme`, series ready) |
| Living acquisition catalog + rank CLI | **This workstream** |
| Cost/EV gate helper | **This workstream** |
| Vendor API clients | **Only when human OK + keys** — not before |
| Full data lake / multi-vendor platform | **Out of scope** |

---

## Next autonomous actions (no human)

1. Keep catalog current; re-rank when new free archives appear.  
2. Scaffold **macro (FRED DXY/rates)** free series path if public API works without keys.  
3. Do **not** open paid subscriptions autonomously.

## Next human actions (when you choose)

1. Approve free macro programme run (no cost).  
2. Or: “buy CryptoQuant/Glassnode export for programme X” with budget cap.  
3. Or: provide parquet drop under `data/processed/external/`.
