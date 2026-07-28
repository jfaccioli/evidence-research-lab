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
python -m crl status --readiness   # lab_ops vs autotrading dual score
```

Exit 0 from doctor/status = hard checks pass; LIVE should report disabled; `git_origin` should point at GitHub.  
`lab_ops_ready: true` with `autotrading_ready: false` is the expected healthy state until confirmatory survivors exist.

## Core research loop

| Command | Purpose |
|---------|---------|
| `python -m crl fetch --interval 1d` | Pin BTC daily OHLCV (default symbol) |
| `python -m crl fetch --interval 1d --symbol ETHUSDT` | Pin ETH daily (universe allow-list) |
| `python -m crl fetch --interval 4h` | Pin 4h OHLCV |
| `python -m crl plan` | Evidence-driven research plan |
| `python -m crl run-programme examples/batch/<prog>` | Doctor + INDEX series attach + explor/conf + note + autopsy |
| `python -m crl series list` | Inventory pinned flow/external series |
| `python -m crl series ready --hyp-dir examples/batch/flow` | Series readiness for a programme |
| `python -m crl new-programme slug --kind external --series-id …` | Scaffold locked programme |
| `python -m crl queue` | Machine research queue state |
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
# After APPROVED survivors only — mandate paper clock (not a science gate):
python -m crl paper -H path/to/survivor.yaml --cash 50 \
  --mandate-limits --require-approved --record-clock
python -m crl shadow -H examples/batch/hyp_sma200_long.yaml
```

Journals: `data/paper_journal/`, `data/paper_clock/`, `data/shadow/`.  
Paper equity is **not** a promotion gate. Paper clock records mandate walk time only.

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
