# Live-readiness status (honest)

**Updated:** 2026-07-27  
**Branch tip:** see `git log -1`

## Destination

Tiny **automated** live trading (AUD ~10–50, spot BTC, kill-switch) **only after** promotion ladder.

## Ladder checklist

| Gate | Status |
|------|--------|
| Phase 1 research lab | **Done** |
| Phase 2: ≥2–3 confirmatory survivors (distinct mechanisms) | **Not met — zero candidates** |
| Paper ≥1 month on survivors | Blocked on candidates |
| Shadow (live signals, no orders) | Scaffold only |
| Phase 5 LIVE flags + keys + adapter | **Hard-disabled** |

## Track B (built)

| Component | Path / command |
|-----------|----------------|
| Paper broker | `src/crl/production/execution/broker.py` |
| Paper historical session | `src/crl/production/paper/session.py` |
| CLI | `python -m crl paper -H <hyp.yaml> --cash 50` |
| Shadow logger | `src/crl/production/shadow/logger.py` |
| LIVE | Dual flags + **no exchange adapter** |

## Track A (recent programmes)

| Programme | Exploratory | Confirmatory |
|-----------|-------------|--------------|
| Funding daily | 0/10 | — |
| Funding 4h | 0/6 | — |
| OI | 1/10 | failed_test |
| Capacity friction | 0/5 | — |
| Asymmetric v2 | 0/5 | — |
| Liquidity panic | 0/5 | — |
| ATR trail | 0/5 | — |
| Slow/fast | 0/5 | — |
| Vol regime | 1/5 | failed_test |
| Calendar | 0/5 | — |

**Scientific reading:** Daily long-only public technical + leverage-state filters under frozen gates are **hard**. Val teases die on test. That is progress (uncertainty reduction), not a reason to soften gates.

## What remains before “operational live”

1. Keep hunting **distinct** mechanisms / horizons until true confirmatory survivors exist (or honest “exhausted under these gates” meta-conclusion).  
2. Paper clock on survivors (not on failed catalog).  
3. Shadow on live data feed (keys for feed only).  
4. Human Phase-5 open + venue API keys + independent safety review.

## Human actions still needed (when ready)

- Git remote + push (backup)  
- Exchange API keys **only** for Phase 5  
- Explicit Phase-5 enablement  
