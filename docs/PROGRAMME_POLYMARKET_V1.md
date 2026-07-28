# Programme: Polymarket crypto odds (v1)

**Status:** Locked exploratory (public CLOB history, no API key).  
**Supersedes for execution:** `PROGRAMME_POLYMARKET_V1_DEFERRED.md` remains historical.

## Scientific question

> Does point-in-time **market-implied probability** that BTC reaches a pre-registered year-end threshold, joined with lag to daily BTC bars, support long-only / flat rules under frozen gates?

## Pre-registered series (binding — do not swap after results)

| Field | Value |
|-------|-------|
| Event | What price will Bitcoin hit in 2025? (`what-price-will-bitcoin-hit-in-2025`) |
| Market | **Will Bitcoin reach $150,000 by December 31, 2025?** (YES token) |
| Rationale for pick | Mid-tier year-end threshold with multi-month public history; **not** chosen by maximising price variance after the fact |
| series_id | `pm_btc_150k_eoy2025_yes_v1` |
| Join | CLOB daily price history; `publish_lag_days=1` |
| Features | prefix `pm_` via external series module |

Token id is frozen at ingest time in `data/processed/external/*.meta.json`.

## Hyps (≤5)

See `examples/batch/polymarket/`. Do not expand without v2.

## Caveats

- Odds series are **partially collinear with path of BTC** (not pure orthogonal alt-data).  
- Sample shorter than multi-year OHLCV (~1y).  
- Illiquid tails and resolution effects possible near expiry.  
- Still must clear frozen gates; mock not used.

## Non-goals

Cherry-picking the most variable threshold after scanning std; election markets as BTC proxy without pre-reg map; live trading on Polymarket.
