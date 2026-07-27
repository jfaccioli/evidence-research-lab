# Operator runbook — Crypto Research Lab

Minimal commands for a **reliable research lab** (not a forced trading bot).

## Setup

```bash
cd /path/to/crypto-research-lab
source .venv/bin/activate   # or use .venv/bin/python
export PYTHONPATH=src
# or: python -m crl …
```

## Health check (start here)

```bash
python -m crl doctor
# exit 0 = hard checks pass; LIVE should report disabled
```

## Core research loop

| Command | Purpose |
|---------|---------|
| `python -m crl fetch --interval 1d` | Pin BTC daily OHLCV |
| `python -m crl fetch --interval 4h` | Pin 4h OHLCV |
| `python -m crl plan` | Evidence-driven next IG suggestions |
| `python -m crl batch --hyp-dir examples/batch/<prog> --registry-path data/processed/tmp_prog.sqlite` | Run **locked** programme (no catalog rewrite) |
| `python -m crl learn` | Refresh KB from registry |
| `python -m crl thesis` | Print Thesis Tree |
| `python -m crl programmes` | Inventory programme dirs + hyp counts |
| `python -m crl batch --hyp-dir … --temp-registry` | Programme batch with auto temp sqlite |

### Programme batch pattern (recommended)

```bash
python -m crl batch \
  --hyp-dir examples/batch/funding \
  --dataset-id binance_public_BTCUSDT_1d_79cfad335046 \
  --registry-path data/processed/tmp_funding.sqlite \
  --no-write
```

- **Do not** use live `registry/crl.sqlite` for speculative programmes until you mean it.  
- `--hyp-dir` defaults to **not** rewriting the hyp catalog (avoids clobbering locks).

## Paper / shadow (no capital)

```bash
python -m crl paper -H examples/batch/hyp_sma200_long.yaml --cash 50
python -m crl paper --hyp-dir examples/batch/breakout --limit 3 --cash 50
python -m crl shadow -H examples/batch/hyp_sma200_long.yaml
```

Journals: `data/paper_journal/`, `data/shadow/`.  
**Paper equity is not a promotion gate** — research gates are.

## Frozen rules

| Doc | Role |
|-----|------|
| `AGENTS.md` | Philosophy |
| `docs/AUTONOMOUS_CHARTER.md` | Autonomy + dual track |
| `docs/PROMOTION_LADDER.md` | Path to tiny live |
| `docs/STATUS_LIVE_READINESS.md` | Honest distance to live |
| `docs/MANDATE_CURRENT_SCOPE.md` | What “strong tool” means |
| `docs/META_NULL_SYNTHESIS_2026-07-27.md` | Null wave summary |
| `configs/default.yaml` | **Do not soften gates** |

## Programme inventory (examples)

| Dir | Notes |
|-----|--------|
| `funding/`, `funding_4h/` | True funding PIT; nulls |
| `oi/` | True OI; val tease confirmatory-killed |
| `capacity/` | Elevated friction |
| `asymmetric/`, `liquidity/`, `atr_trail/`, `slow_fast/`, `vol_regime/`, `calendar/`, `breakout/`, `volume/`, `hold_4h/`, `breakout_4h/` | See each EXPLORATORY_NOTE |

## Human-only

API keys, LIVE Phase-5 flags, paid data, gate policy changes, git remote/push if desired.
