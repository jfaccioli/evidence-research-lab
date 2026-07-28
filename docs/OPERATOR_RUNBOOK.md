# Operator runbook — Evidence Research Lab

Minimal commands for a **reliable research lab** (not a forced trading bot).

**GitHub (private):** https://github.com/jfaccioli/evidence-research-lab  
**Stance:** `docs/PHASE2_STANCE.md` (pause daily technical clones; ops/reliability default)

## Setup

```bash
cd /path/to/crypto-research-lab   # local folder name may differ from GitHub name
source .venv/bin/activate
export PYTHONPATH=src
# or: pip install -e ".[dev]"
```

## Health check (start here)

```bash
make check
# or:
python -m crl doctor
python -m crl status --write-md
```

Exit 0 from doctor/status = hard checks pass; LIVE should report disabled; `git_origin` should point at GitHub.

## Core research loop

| Command | Purpose |
|---------|---------|
| `python -m crl fetch --interval 1d` | Pin BTC daily OHLCV |
| `python -m crl fetch --interval 4h` | Pin 4h OHLCV |
| `python -m crl plan` | Evidence-driven research plan |
| `python -m crl run-programme examples/batch/<prog>` | Doctor + temp registry + note + autopsy |
| `python -m crl batch --hyp-dir … --temp-registry` | Exploratory batch only |
| `python -m crl autopsy examples/batch/<prog>` | Rebuild GATE_AUTOPSY from reports |
| `python -m crl programmes --write-md` | Inventory → `docs/PROGRAMME_INVENTORY.md` |
| `python -m crl learn` / `thesis` | Knowledge base + thesis tree |

### Programme batch pattern

```bash
python -m crl run-programme examples/batch/fade
# or
python -m crl batch \
  --hyp-dir examples/batch/funding \
  --temp-registry
```

Do **not** use live `registry/crl.sqlite` for speculative programmes until intentional.

## Paper / shadow (no capital)

```bash
python -m crl paper -H examples/batch/hyp_sma200_long.yaml --cash 50
python -m crl paper --hyp-dir examples/batch/breakout --limit 3 --cash 50
python -m crl shadow -H examples/batch/hyp_sma200_long.yaml
```

Journals: `data/paper_journal/`, `data/shadow/`.  
Paper equity is **not** a promotion gate.

Kill switch: `data/ops/KILL_SWITCH` or `CRL_KILL_SWITCH=1`.

## Push backup

```bash
git push origin HEAD
```

## Frozen rules

| Doc | Role |
|-----|------|
| `AGENTS.md` | Philosophy |
| `docs/PHASE2_STANCE.md` | Current phase decision |
| `docs/AUTONOMOUS_CHARTER.md` | Autonomy + dual track |
| `docs/PROMOTION_LADDER.md` | Path to tiny live |
| `docs/FRAMEWORK_GENERALIZATION.md` | Beyond crypto |
| `docs/MANDATE_CURRENT_SCOPE.md` | Strong tool definition |
| `configs/default.yaml` | **Do not soften gates** |

## Human-only

API keys, LIVE Phase-5 flags, paid data, gate policy changes.

See `docs/PROGRAMME_INVENTORY.md` for programme table.
