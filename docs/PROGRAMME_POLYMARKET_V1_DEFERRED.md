# Deferred programme: Polymarket / event odds (v1 design sketch)

**Status:** Deferred — **remembered for later**; not current execution.

## Scientific question (when opened)

> Do **timestamped** prediction-market prices on crypto-relevant events, joined point-in-time to BTC decision bars, improve risk-adjusted long-only or flat rules under frozen gates?

## Requirements

1. Reconstructible history of market odds with **trade or mid timestamps**  
2. Map events → BTC decision relevance (pre-registered event list; no cherry-picking after the fact)  
3. As-of join + next-open lag  
4. Versioned dataset + hash  
5. ≤ small pre-reg hyp budget; frozen gates  

## Value if done right

Market-implied event risk **orthogonal** to pure OHLCV technicals.

## Harm if early

Sparse events, illiquid markets, resolution leaks, non-reproducible APIs.

## Open order

After funding/OI v1 closed (done) and preferably after a **PIT data feasibility check**. Human OK for any API keys.
