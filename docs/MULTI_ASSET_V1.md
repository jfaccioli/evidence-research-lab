# Multi-asset v1 (spot allow-list)

**Updated:** 2026-07-28  
**Status:** Plumbing live — default universe **BTC/USDT + ETH/USDT**.

## Goal

Run the same fail-closed research / paper / shadow stack on more than BTC, without turning the lab into an alt-coin backtest farm.

## Config

```yaml
# configs/default.yaml
universe:
  spot_assets:
    - BTC/USDT
    - ETH/USDT
symbol_binance: BTCUSDT   # default fetch when --symbol omitted
```

Add a symbol only by **editing the allow-list** (deliberate product decision). Random alts are rejected by `assert_phase1_universe` and the paper broker.

## Operator commands

```bash
# Pin ETH daily (public Binance — no API key)
python -m crl fetch --interval 1d --symbol ETHUSDT

# Hypothesis YAML must set asset: ETH/USDT
python -m crl run -H examples/batch/eth/hyp_eth_sma200_long.yaml --mock
python -m crl paper -H examples/batch/eth/hyp_eth_sma200_long.yaml --cash 50
```

Dataset ids remain per-symbol (separate manifests/hashes). Do **not** mix BTC and ETH bars in one dataset.

## Scientific rules (binding)

1. **BTC nulls are not ETH evidence** — new asset ⇒ new programme / multiplicity.  
2. Prefer **one small pre-registered programme per new asset**, not clone spam.  
3. Costs may differ (spreads); start with default lab costs; revise only with a programme note.  
4. Funding / OI / flow series are **per symbol** if used; ETH flow is separate from BTC flow.  
5. Gates stay frozen. Multi-asset is not a reason to soften.

## Non-goals (v1)

- Cross-sectional portfolio / pairs trading  
- “Scan top 50 Binance coins”  
- Perps / leverage  
- LIVE multi-asset adapter  

## Code map

| Piece | Location |
|-------|----------|
| Normalize / allow-list | `src/crl/shared/universe.py` |
| Research gate | `assert_phase1_universe(..., cfg=)` |
| Paper broker | `PaperBroker` symbol check |
| Fetch CLI | `crl fetch --symbol` |
