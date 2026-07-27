# Operator runbook — Crypto Research Lab

Minimal commands to run Phase 2 research without agent babysitting.

## Setup

```bash
cd /path/to/crypto-research-lab
# use project venv
source .venv/bin/activate   # or: .venv/bin/python
export PYTHONPATH=src
```

## Core loop

| Command | Purpose |
|---------|---------|
| `python -m crl fetch --interval 1d` | Pin BTC daily OHLCV |
| `python -m crl fetch --interval 4h` | Pin 4h OHLCV |
| `python -m crl plan` | Next IG suggestions (if wired) |
| `python -m crl batch --hyp-dir examples/batch/<prog>` | Run a pre-reg batch |
| `python -m crl learn` | Refresh KB from registry |
| `python -m crl thesis` | Print Thesis Tree |

Prefer **temp registry** for programme batches:

```bash
python - <<'PY'
from pathlib import Path
import pandas as pd
from crl.research.pipeline.batch import run_batch
# example: pass funding_events=..., registry_path=temp.sqlite
PY
```

## Frozen rules

- Gates: `configs/default.yaml` — do not edit to force passes.  
- Promotion: `docs/PROMOTION_LADDER.md`.  
- Autonomy: `docs/AUTONOMOUS_CHARTER.md`.  
- Project philosophy: root `AGENTS.md`.

## Programme locations

| Programme | Path | Status (see docs) |
|-----------|------|-------------------|
| Funding daily | `examples/batch/funding/` | Null 0/10 |
| Funding 4h power | `examples/batch/funding_4h/` | Null 0/6 |
| OI daily | `examples/batch/oi/` | Val tease → confirmatory fail |
| Capacity / friction | `examples/batch/capacity/` | See programme doc |

## Reports

Per-hyp: `reports/hyp_*_{exploratory,confirmatory}.{json,md}`  
Batch summary: `reports/batch_summary.*`

## Human-only

API keys, live trading, gate changes, paid data sources.
