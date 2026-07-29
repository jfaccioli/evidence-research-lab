# Observation inventory — what the lab can see

**Updated:** 2026-07-29  
**Philosophy:** `docs/OBSERVATION_DISCOVERY_DIRECTIVE.md`

## Currently observed (in store or tested)

| Observation family | Source | Role tested | Status |
|--------------------|--------|-------------|--------|
| Spot OHLCV (price path) | Binance public | Trend/MR/breakout atomistic | Exhausted as long/flat grammar |
| Spot volume | Binance public | Participation programmes | Mostly null as filters |
| Funding rate | Binance futures | Crowding/leverage proxy | Conf nulls |
| Open interest | Bybit | Leverage stock | Conf nulls |
| Free CMD netflow / stables / MVRV / liq / premium | GitHub CMD | Inventory proxies | Conf null wave |
| Polymarket path + panel | CLOB | Crowd path odds | Explor/conf null |
| FRED USD + 2Y (lag+1) | FRED | Macro regime | Programme null |
| Lagged RV (LEDA-1) | Derived OHLCV | Risk persistence | **Skill strong**; policy maps fail holdout |
| Lagged mom rank (LEDA-2) | Derived OHLCV | Forecast | IC ~null |
| ETH lagged mom (LEDA-5a) | ETH OHLCV | Cross-asset | IC ~null |

## Blind spots (high priority free)

| ID | Observable property | Why independent | Acquisition |
|----|---------------------|-----------------|-------------|
| **`kline_aggression`** | Taker buy share + trade count on each bar | Not a function of close alone; Binance kline fields we **previously discarded** | Free; same kline API — **retain columns** |
| `perp_premium` | Perpetual mark–index premium | Futures consensus vs spot path | Free Binance futures premiumIndex klines |
| `cross_venue_basis` | Spot multi-venue dislocation | Venue-specific inventory/pressure | Multi-exchange free APIs; more effort |
| `stablecoin_supply_growth` | Aggregate stable supply change | Macro crypto liquidity (not exchange netflow clone if total supply) | Free DefiLlama-type; verify PIT |
| `etf_flow` | Spot BTC ETF create/redeem | Institutional pipe | Often delayed/paid; EIR later |

## Explicitly low EV (do not re-mine)

- Another free daily CMD on-chain metric of the same inventory family  
- More SMA/mom/donchian parameter clones  
- Vol-veto threshold fishing beyond LEDA-6 pre-reg grid  

## Active characterization

| Family | Claim under test | Trade mapping |
|--------|------------------|---------------|
| **kline_aggression** | Done — intensity ↔ next RV ~-0.26; tbr ↔ ret_lag ~0.36; weak direction | **None** until pre-reg state/risk channel |
| **perp_premium** | Next free family | Acquire + characterize |

See `docs/OBSERVATION_KLINE_AGGRESSION_V1.md`.
