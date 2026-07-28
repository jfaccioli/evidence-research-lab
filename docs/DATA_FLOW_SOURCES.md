# Exchange-flow / “whale” data — what you need and when

**Updated:** 2026-07-28  
**Related:** `docs/PROGRAMME_FLOW_WHALE_V1.md` (PIT join lock)

## What “flow source” means

**Not** the same as Binance spot OHLCV (candles).

**Flow** = time series of **net coins moving onto/off exchanges** (or large transfers), with a true **availability time** (`flow_time`) so we can join as-of bar close without look-ahead.

| Data | Source example | Role in lab |
|------|----------------|-------------|
| OHLCV prices | Binance public API | Already used (`crl fetch`) — free, no key |
| Funding / OI | Binance / Bybit public | Already used for those programmes |
| **Net exchange flow** | CryptoQuant, Glassnode, Arkham, etc. | **Blocked until you provide versioned history** |

Mock flow exists **only for unit tests**. It never counts as science.

## Do you need an API key?

| Path | Key? | Notes |
|------|------|--------|
| Manual / bulk CSV or parquet export | Often no key in *our* code — you download, we load file | Best for first science batch |
| Vendor REST API | Yes — **your** key; human cost OK | We only wire after you approve vendor |
| Free public dumps | Sometimes | Must still be PIT-reconstructible |

You will **not** be asked for keys until we are ready to ingest a chosen vendor (or you drop a file yourself).

## Platform recommendation (for this lab)

Ordered for **honest multi-year daily (or sub-daily) netflow + usable history**, not marketing:

1. **CryptoQuant** (or similar exchange-flow specialists)  
   - Strength: exchange inflow/outflow / netflow for BTC (and often ETH) with research-grade history.  
   - Fit: closest to the locked programme question.  
   - Cost: typically paid tier for full history API/export.

2. **Glassnode**  
   - Strength: strong on-chain metrics; exchange net position change / similar series.  
   - Fit: good if you already pay or prefer their stack.  
   - Watch: exact metric name + revision policy (PIT).

3. **Arkham / Nansen / similar “whale” UIs**  
   - Strength: entity labels, large transfers.  
   - Fit: weaker as a clean **daily netflow** series unless they export stable history with timestamps. Prefer for later, not first batch.

4. **DIY from free blockchain explorers**  
   - Possible but heavy engineering; easy to get PIT wrong. Not recommended as first path.

**Binance alone** does **not** give you historical “exchange netflow” the way CryptoQuant does. Binance gives you **prices, trades, funding, sometimes OI** — not a ready multi-year exchange-reserve flow series for the whale narrative.

### Practical pick for v1

- **Primary recommendation:** **CryptoQuant BTC (then ETH) exchange netflow** daily, export or API → parquet.  
- **Acceptable alternative:** Glassnode exchange net position change (document metric id + as-of rule).  
- **Avoid first:** live Telegram whale bots, unversioned screenshots, forward-filled free widgets.

## File we need (when it’s time)

```
data/processed/flow/<series_id>.parquet
```

Columns:

- `flow_time` — UTC when the observation was **knowable**  
- `net_flow` — float; **positive = net into exchanges** (lab convention)

Then: locked batch under `examples/batch/flow/` only.

## Free path (in use for Q1 exploratory)

| Source | Role |
|--------|------|
| [crypto-market-data](https://github.com/ErcinDedeoglu/crypto-market-data) BTC Exchange Netflow | Free CC BY 4.0 daily mirror; adapter `flow_cmd_github.py` |
| PIT | Fixed `publish_lag_days=1` (vendor revision journal not available) |
| series_id | `cmd_btc_exchange_netflow_v1` |

**Attribution required** in notes/reports. Not vendor-grade PIT; still valid **exploratory** evidence class vs pure technicals.

## Paid / export path (optional upgrade)

| Stage | Your action |
|-------|-------------|
| Want vendor-grade history | CryptoQuant/Glassnode export or API (human keys/cost) |
| Drop file | `data/processed/flow/<series_id>.parquet` |

CryptoQuant is **optional upgrade**, not required to start Q1 if free series is already ingested.

## Cost / privacy

- Prefer **export once** for the first programme (fixed sample, hashed).  
- Live streaming APIs are optional later for shadow; not required for exploratory science.
