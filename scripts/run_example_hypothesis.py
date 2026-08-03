#!/usr/bin/env python3
"""Convenience: fetch (if needed) and run the example hypothesis exploratorily."""

from __future__ import annotations

import sys
from pathlib import Path

# ensure project root on path when run as script
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crl.cli import main


if __name__ == "__main__":
    # Prefer real data if present; else mock
    from crl.shared.config import load_config, project_root
    from crl.shared.data.store import latest_manifest

    cfg = load_config()
    root = project_root()
    m = latest_manifest(
        root / cfg["data"]["manifest_dir"],
        symbol=cfg.get("symbol_binance", "BTCUSDT"),
        interval="1d",
        source="binance_public",
    )
    if m is None:
        print("No cached data — using --mock (run `crl fetch --interval 1d` for real BTC).")
        raise SystemExit(main(["run", "-H", "examples/hyp_sma200_vol_filter.yaml", "--mock"]))
    raise SystemExit(main(["run", "-H", "examples/hyp_sma200_vol_filter.yaml"]))
