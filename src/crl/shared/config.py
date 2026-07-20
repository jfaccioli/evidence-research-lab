"""Configuration loading and hashing."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from crl.shared.types import CostConfig, GateConfig, SplitConfig


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    if path is None:
        # Walk up from CWD / package for configs/default.yaml
        candidates = [
            Path("configs/default.yaml"),
            Path(__file__).resolve().parents[3] / "configs" / "default.yaml",
        ]
        for c in candidates:
            if c.exists():
                path = c
                break
        else:
            raise FileNotFoundError("configs/default.yaml not found")
    path = Path(path)
    with path.open() as f:
        cfg = yaml.safe_load(f)
    return cfg


def config_hash(cfg: dict[str, Any]) -> str:
    payload = json.dumps(cfg, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def cost_from_config(cfg: dict[str, Any]) -> CostConfig:
    return CostConfig(**cfg.get("costs", {}))


def splits_from_config(cfg: dict[str, Any]) -> SplitConfig:
    return SplitConfig(**cfg.get("splits", {}))


def gates_from_config(cfg: dict[str, Any]) -> GateConfig:
    return GateConfig(**cfg.get("gates", {}))


def project_root() -> Path:
    """Best-effort project root (directory containing configs/)."""
    here = Path(__file__).resolve()
    for p in [Path.cwd(), *here.parents]:
        if (p / "configs" / "default.yaml").exists():
            return p
    return Path.cwd()
