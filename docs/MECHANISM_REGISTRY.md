# Mechanism registry (living)

**Updated:** 2026-07-29  
**Directive:** `docs/MECHANISM_DISCOVERY_DIRECTIVE.md`  
**Machine:** `research_kb/mechanism_registry.json`

## Status legend

| Status | Meaning |
|--------|---------|
| `active_study` | Under investigation with declared design |
| `partially_mapped` | Some observables exist; mechanism incomplete |
| `exhausted_op` | Current operationalisation tested null/retired |
| `blocked_missing_obs` | Missing free reconstructible observations |
| `deferred` | Lower EV or paid-only |

## Ranked mechanisms

### 1. `vol_clustering` — What processes cause volatility clustering? **(active)**

| Item | Content |
|------|---------|
| **Hypothesis** | High-vol states persist not only by statistical inertia but because **leverage stress** and **liquidity withdrawal** co-occur with high RV and prolong uncertainty. |
| **Min observables** | RV path; leverage proxies (funding, premium, OI); liquidity stock growth; participation intensity |
| **In lab** | RV, funding, premium, stable supply growth, intensity, OI series |
| **Missing** | None for first causal co-factor study |
| **EV** | **High** — explains LEDA-1 RV skill; synthesis showed RV dominates next-vol; mechanism asks *why* |
| **Status** | `study_v1_done` — co-factor prolongation **not supported**; RV inertia dominates |

### 2. `leverage_cycle` — How does leverage build and unwind?

| Item | Content |
|------|---------|
| **Hypothesis** | Funding/premium/OI form a cycle: build → stress → unwind → calmer vol. |
| **Min observables** | Funding, premium, OI, RV, optionally liquidations |
| **In lab** | Funding, premium, OI, RV; free liquidations series previously conf-null as *trade filters* |
| **Missing** | True PIT liquidation path quality uncertain |
| **EV** | High — related to vol_clustering; study after or jointly with (1) |
| **Status** | `study_v1_done` — build > unwind next-RV (**descriptive**); not LEDA candidate |

### 3. `liquidity_creation_destruction` — How is liquidity created/transferred/destroyed?

| Item | Content |
|------|---------|
| **Hypothesis** | Stable mint/burn and venue flows change risk-bearing capacity; contractions amplify vol. |
| **Min observables** | Aggregate supply stock **and** mint/burn or net creation; venue transfer; depth |
| **In lab** | Aggregate supply **stock** growth only |
| **Missing** | Free reliable mint/burn; quality venue inventory |
| **EV** | Medium–high; stock property characterised; creation process missing |
| **Status** | `blocked_missing_obs` (mint/burn) / partial on stock |

### 4. `uncertainty_behaviour` — How do participants change under uncertainty?

| Item | Content |
|------|---------|
| **Hypothesis** | Under high RV, intensity falls, taker aggression changes, basis widens. |
| **Min observables** | RV, intensity, tbr, basis |
| **In lab** | All |
| **Missing** | None for descriptive conditioning |
| **EV** | Medium — can run with existing data after vol_clustering |
| **Status** | `study_v1_done` — intensity higher in high RV; leverage proxies elevated |

### 5. `info_propagation` — How does information propagate across markets?

| Item | Content |
|------|---------|
| **Hypothesis** | Shocks transmit ETH↔BTC, spot↔perp, venue↔venue with lags. |
| **Min observables** | Multi-asset returns, premium, basis, optional PM |
| **In lab** | ETH, premium, basis; PM panel explor-null as path odds |
| **Missing** | Clean multi-horizon lead-lag design (not more indicators) |
| **EV** | Medium; prior xasset mom null |
| **Status** | `partially_mapped` |

### 6. `dislocation_persistence` — Why do venue dislocations persist?

| Item | Content |
|------|---------|
| **Hypothesis** | Inventory, USD/USDT rails, and capital controls sustain basis; stress widens \|basis\|. |
| **Min observables** | Cross-venue basis, funding, RV, stable supply |
| **In lab** | Basis (persistent), funding, RV, supply |
| **Missing** | True USD/USDT FX, inventory labels |
| **EV** | Medium — basis characterised; mechanism incomplete |
| **Status** | `partially_mapped` |

### Explicitly not the goal

- Expanding property catalogue without a mechanism  
- Re-mining exhausted atomistic long/flat grammar  
- Equal-rank stress average family (`leda_synth_stress_equal_rank_v1` **retired**)  
