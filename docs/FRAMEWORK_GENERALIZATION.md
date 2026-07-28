# Framework generalization (beyond crypto)

**Updated:** 2026-07-28  
**Repo:** https://github.com/jfaccioli/evidence-research-lab (private)

## What is domain-general

| Layer | Portable idea |
|-------|----------------|
| Pre-registration | Lock hypotheses before seeing evaluation outcomes |
| Frozen gates | Single primary metric + sample size + robustness; no post-hoc softening |
| Point-in-time joins | Features only use information available at decision time |
| Exploratory vs confirmatory | Hold out test; one-shot confirmatory |
| Programme budgets | Multiplicity accounting by programme version |
| Thesis tree | Mechanisms, not strategy “winners” |
| Paper → shadow → tiny live | Risk ladder after *evidence*, not after a pretty backtest |
| Kill switch / risk envelope | Ops fail-closed before capital |

## What is domain-specific today (BTC application)

| Piece | Crypto-specific |
|-------|-----------------|
| OHLCV fetch | Binance public BTCUSDT |
| Funding / OI | Perp exchange series |
| Cost model | Fee/spread/slippage bps for crypto spot |
| Asset constraint | Phase-1 long-only BTC/USDT |
| Calendar features | UTC crypto continuous market |

## How to reuse for another science domain

1. **Keep** pipeline, gates, registry, programme discipline, paper/shadow modes.  
2. **Swap** data source adapters (new `sources/*` + manifests + trust).  
3. **Re-specify** cost/friction model for that domain.  
4. **Rewrite** feature set if economic mechanisms differ (still causal/PIT).  
5. **New programmes** with new mechanism IDs in the thesis tree.  
6. **Do not** copy BTC null results as evidence about other domains.

## Naming

- **Product / GitHub:** Evidence Research Lab  
- **Local path / package:** may still say `crypto-research-lab` / `crl` during BTC phase  
- Future rename of Python package is optional and non-urgent

## What we will not do

- Claim the BTC null wave proves “no edges exist” outside this mandate  
- Soften gates to force a multi-domain “demo winner”  
- Build LIVE adapters without survivors + human Phase-5 open  
