# Evidence Research Lab

Fail-closed **scientific research lab**: pre-registered hypotheses, frozen validation gates, paper/shadow path.

**First application:** BTC/USDT spot ideas (this repo’s data + cost model).  
**Framework:** domain-general evidence / rejection engine — not crypto-only.

**GitHub (private):** https://github.com/jfaccioli/evidence-research-lab  

**Product identity:** strong rejection engine + paper/shadow path toward tiny live **only if** confirmatory survivors exist.  
**Not** a bot that trades noise. Finding zero edges is success.

**Phase 2 stance:** `docs/PHASE2_STANCE.md` (no more daily technical clone spam).

## Quick start

```bash
cd crypto-research-lab
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
export PYTHONPATH=src   # or: pip install -e .

make doctor          # health check
make status          # LIVE/kill/programmes snapshot
make check           # doctor + tests + status

# Public OHLCV (no API key)
python -m crl fetch --interval 1d
python -m crl fetch --interval 4h

# Locked programme (temp registry, notes + autopsy)
python -m crl run-programme examples/batch/fade

# Paper / shadow (no capital; LIVE disabled)
python -m crl paper -H examples/batch/hyp_sma200_long.yaml --cash 50
python -m crl shadow -H examples/batch/hyp_sma200_long.yaml
```

## Operator CLI

| Command | Role |
|---------|------|
| `crl doctor` | Config, data, LIVE off, programmes |
| `crl status` / `--write-md` | Compact snapshot → `docs/LAB_STATUS.md` |
| `crl programmes` / `--write-md` | Inventory → `docs/PROGRAMME_INVENTORY.md` |
| `crl run-programme <dir>` | Doctor + temp batch + confirmatory on passes + autopsy |
| `crl autopsy <dir>` | GATE_AUTOPSY from report JSON |
| `crl batch --hyp-dir … --temp-registry` | Exploratory batch without clobbering catalog |
| `crl paper` / `crl shadow` | Historical sim / signal log |
| `crl plan` / `learn` / `thesis` | Planner + knowledge base |
| `crl fetch` | Pin OHLCV |

Full runbook: `docs/OPERATOR_RUNBOOK.md`.  
Mandate: `docs/MANDATE_CURRENT_SCOPE.md`.  
Live ladder: `docs/PROMOTION_LADDER.md`.  
Build checklist: `docs/LAB_BUILD_CHECKLIST.md`.

## Layout

```
src/crl/
  shared/       # data, features, config
  research/     # pipeline, stats, planner, registry
  production/   # paper/shadow/risk/kill-switch; LIVE fail-closed
  ops/          # doctor, programmes, run-programme, autopsy, status
  risk/         # constraints + promotion gates
configs/
examples/batch/ # pre-registered programmes (see PROGRAMME_INVENTORY.md)
docs/
research_kb/    # thesis + learnings
```

## Validation standards

- Closed-bar signal → next-open position (no look-ahead)
- Causal features only
- Costs + 2× stress; chronological splits + walk-forward
- Bootstrap CI, reality checker, exploratory vs confirmatory
- **Never soften gates** to invent candidates

## Current science state

Broad pre-registered wave under frozen gates → **zero confirmatory candidates**.  
Ops path (paper/shadow) is built; **LIVE stays off** until Phase 5 + human keys + survivors.

## Tests

```bash
make test
# or
pytest -q
```

## Philosophy

Root `AGENTS.md` + `docs/AUTONOMOUS_CHARTER.md`: maximise **knowledge per research budget**, not win rate or hyp count.
