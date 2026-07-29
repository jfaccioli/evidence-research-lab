# Scientific Research Roadmap (persistent)

**Updated:** 2026-07-29  
**Primary directive:** `docs/MECHANISM_DISCOVERY_DIRECTIVE.md`  
**Mission:** Reduce uncertainty about how markets function — not produce positive backtests.

## Laboratory model (current understanding)

| Claim | Status |
|-------|--------|
| RV is strongly persistent (next-RV skill ~0.96 IC) | **Established** |
| Equal-rank multi-property stress beats RV lag | **Retired null** |
| Leverage/liquidity cofactors *prolong* high-RV beyond inertia | **Retired null** |
| OI-build has higher **mean** next-RV than OI-unwind | **Descriptive only** |
| OI-build adds **incremental** next-RV skill beyond rv_lag | **Retired null** (`leverage_incremental_rv_skill_v1`) |
| Atomistic daily long/flat public-signal grammar | **Exhausted** (0 confirmatory) |

**Working model of uncertainty:** next-RV is dominated by **RV lag**. Leverage states
describe concurrent risk regimes but do not currently justify separate next-RV channels.

## Active mechanisms

| ID | Question | Status |
|----|----------|--------|
| `dislocation_persistence` | Why does basis respond to stress? | **Descriptive support**: \|basis\| ~2× in high RV vs low RV |
| `liquidity_creation_destruction` | Mint/burn dynamics | **Blocked** missing free mint/burn |

## Retired families (permanent unless new data class + new pre-reg)

| Family | Claim |
|--------|--------|
| `leda_synth_stress_equal_rank_v1` | Multi-property stress ≫ rv_lag |
| `vol_clustering` co-factor prolongation | Cofactors raise high-RV persistence |
| `leverage_incremental_rv_skill_v1` | OI-build residual IC ≥ 0.05 for next-RV |
| `info_prop_eth_rv_to_btc_residual_v1` | ETH RV residual skill for BTC next-RV |
| Atomistic V1 long/flat + free series conf wave | Public long/flat edges |
| Intensity-drop under high RV | Intensity falls in high RV |
| ETH→BTC lagged mom IC (LEDA-5a) | Cross-asset mom forecast |

## Open scientific questions

1. ~~Does leverage build add next-RV skill ⊥ rv_lag?~~ **No**.  
2. ~~Does ETH RV add residual BTC next-RV skill?~~ **No** (raw collinear only).  
3. ~~Does stress **widen** \|basis\|?~~ **Yes** (high RV ~2× low RV mean \|basis\|).  
4. Can basis or leverage **incrementally** improve risk **decisions** beyond rv_lag? Open, low priority after nulls.  
5. Directional edges under any mechanism remain **unfound** (0 confirmatory).  

## Unresolved contradictions

- None material on the RV-skill frontier: multi-asset and leverage labels collapse to BTC RV lag for *forecast skill*.  
- Dislocation and leverage remain useful **regime descriptors** without incremental forecast skill.

## Highest-value next experiments (IG / trial cost)

| Rank | Experiment | Sci EV | Econ | Novelty | P(Δ model) | External | Cost |
|------|------------|--------|------|---------|------------|----------|------|
| **1** | Pause RV-skill fishing; document model; seek **new free observation class** for liquidity creation (mint/burn) or paid EIR only if human opens | 4 | Med | High | High | Maybe | deferred |
| 2 | Optional: basis residual ⊥ rv_lag as descriptive only (no LEDA) | 2 | Low | Low | Low | No | skip preferred |
| 3 | Directional edge search only with **new mechanism + new data class** | — | — | — | — | — | not from shelf |

## Programme log

| Date | Programme | Result |
|------|-----------|--------|
| 2026-07-29 | Synthesis stress | Null; family retired |
| 2026-07-29 | vol_clustering v1 | Cofactor prolongation null |
| 2026-07-29 | leverage_cycle v1 | Build mean next-RV > unwind |
| 2026-07-29 | uncertainty_behaviour v1 | Intensity↑ in high RV |
| 2026-07-29 | leverage_incremental_rv_skill v1 | Residual IC 0.027; **retired** |
| 2026-07-29 | info_prop_eth_rv_to_btc_residual v1 | Residual IC -0.03; **retired** |
| 2026-07-29 | dislocation_basis_under_stress v1 | \|basis\|↑ in high RV/funding; **descriptive support** |

## Governance

- Nulls are success.  
- No LIVE/shadow alpha without confirmatory pathway.  
- Ops readiness is separate and non-promotional.
