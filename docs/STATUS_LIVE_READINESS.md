# Live-readiness status (honest)

**Updated:** 2026-07-27 (breakout/volume/paper-replay)  
**Branch tip:** see `git log -1`

See also: `docs/MANDATE_CURRENT_SCOPE.md`, `crl doctor`.

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
| Breakout | 0/5 | — |
| Volume | 0/5 | — |

**Scientific reading:** Daily long-only public technical + leverage-state filters under frozen gates are **hard**. Val teases die on test. That is progress (uncertainty reduction), not a reason to soften gates.

## Scientific outlook (honest, not defeatist)

**Question:** Is it looking more likely that this stack will *not* support good autotrading because the science cannot back it?

**Short answer: for daily (and selective 4h) BTC long-only public rules under frozen costs/gates — yes, that is currently the more likely outcome.** That is a *scientific* conclusion so far, not a product failure.

| Evidence | Implication |
|----------|-------------|
| Many pre-reg programmes → **0 confirmatory candidates** | No earned strategy to automate |
| Val teases die on test (OI, vol-regime) | Looking at val alone would *fake* readiness |
| 4h power often fails even with n_trades ≫ 30 | Not “just need more trades” |
| Bootstrap CI / costs / WF dominate | Edges are fragile or noise |

**What this does *not* prove**

- That *no* crypto edge exists anywhere (other horizons, venues, microstructure, true alt-data with PIT, short-side, pairs, etc. remain open).  
- That the **lab is useless** — a fail-closed rejection engine that blocks live is exactly the point.  
- That paper/shadow plumbing was wasted — you need it *if* a candidate appears; until then it prevents premature live.

**Product implication**

The “app” can still become **operationally complete** as: research + paper + shadow + kill-switched tiny-live *capability*.  
**Good autotrading** (positive expectancy after costs, out of sample) is a separate, harder claim and may never clear the bar. Prefer that honesty over a bot that trades noise.

## What remains before “operational live”

1. Keep hunting **distinct** mechanisms / horizons until true confirmatory survivors exist (or lock a written “exhausted under these gates” meta-conclusion for this mandate).  
2. Paper clock on survivors (not on failed catalog).  
3. Shadow on live data feed (keys for feed only).  
4. Human Phase-5 open + venue API keys + independent safety review.  
5. Accept that Phase 5 may stay closed indefinitely if no survivors — still a valid lab.

## Human actions still needed (when ready)

- Git remote + push (backup)  
- Exchange API keys **only** for Phase 5  
- Explicit Phase-5 enablement  
