# Research mandate — current scope (strong tool, not forced alpha)

**Updated:** 2026-07-28  
**Product name:** Evidence Research Lab (GitHub: `jfaccioli/evidence-research-lab`, private).  
**Product intent:** A **reliable rejection / evidence engine** (first application: BTC/USDT), with paper/shadow path toward tiny live **if and only if** evidence clears frozen gates. Framework is domain-general; crypto is not the only future use.

## What “strong & reliable” means here

| Property | Implementation |
|----------|----------------|
| Fail-closed science | Frozen gates; no gate softening |
| Reproducible data | Versioned OHLCV / funding / OI manifests |
| Pre-registration | Programme dirs + INDEX.yaml + design docs |
| Honest nulls | Thesis tree + LEARNINGS + programme notes |
| Ops path without capital risk | `crl paper`, `crl shadow`, LIVE dual-flag stub |
| Health | `crl doctor` |

## Mandate under test (this wave)

- Assets: **BTC/USDT** (primary evidence base) + **ETH/USDT** plumbing (`universe.spot_assets`)  
- Horizons: primarily **1d**, selective **4h** power/hold  
- Costs: lab default (or elevated for capacity programme)  
- Success: confirmatory survivors **or** clean exhaustion under these rules  
- Flow/whale: scaffold only until real PIT series (`docs/DATA_FLOW_SOURCES.md`)  


## Scientific stance (current)

Broad pre-reg wave → **zero confirmatory candidates**.  
**More likely than not:** durable autotrading *from this mandate* will not clear the bar soon.  
**Still valuable:** tool that prevents trading noise; infrastructure for when/if evidence appears.

## Operator contract

1. Prefer `crl doctor` before big batches.  
2. Programme batches: `crl batch --hyp-dir … --registry-path data/processed/tmp_….sqlite` (no catalog rewrite).  
3. Never promote from full-sample paper equity.  
4. LIVE only after promotion ladder + human Phase-5 open.

## Explicit non-goals (until survivors)

- Softening gates to “get something trading”  
- **Daily long-only technical clone spam** (SMA / volume / breakout near-duplicates) — **paused** after broad null wave  
- Unversioned alt-data / social signals without PIT  
- Re-opening spent programme locks without a new programme version + multiplicity  

See `docs/PHASE2_STANCE.md`.
