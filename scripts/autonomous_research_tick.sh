#!/bin/zsh
# Wrapper for launchd — always run from repo root
set -euo pipefail
ROOT="/Users/jimmyfaccioli/Desktop/crypto-research-lab"
cd "$ROOT"
export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
mkdir -p "$ROOT/logs/autonomous"
PY="$ROOT/.venv/bin/python"
if [[ ! -x "$PY" ]]; then
  echo "Missing venv python: $PY" >> "$ROOT/logs/autonomous/launchd_wrapper.log"
  exit 127
fi
exec "$PY" "$ROOT/scripts/autonomous_research_tick.py" >>"$ROOT/logs/autonomous/launchd_wrapper.log" 2>&1
