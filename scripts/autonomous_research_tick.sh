#!/bin/zsh
# Wrapper for launchd — always run from repo root
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
mkdir -p "$ROOT/logs/autonomous"
exec "$ROOT/.venv/bin/python" "$ROOT/scripts/autonomous_research_tick.py" >>"$ROOT/logs/autonomous/launchd_wrapper.log" 2>&1
