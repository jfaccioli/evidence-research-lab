"""Ops kill switch — file or env latch. Fail closed when engaged."""

from __future__ import annotations

import os
from pathlib import Path

from crl.shared.config import project_root

KILL_ENV = "CRL_KILL_SWITCH"
DEFAULT_REL = Path("data") / "ops" / "KILL_SWITCH"


def kill_switch_path(root: Path | None = None) -> Path:
    return (root or project_root()) / DEFAULT_REL


def is_kill_switch_engaged(root: Path | None = None) -> bool:
    env = os.environ.get(KILL_ENV, "").strip().lower()
    if env in {"1", "true", "yes", "on"}:
        return True
    p = kill_switch_path(root)
    if not p.exists():
        return False
    text = p.read_text().strip().lower()
    # empty file or "1"/"on"/"kill" engages; "0"/"off" disengages
    if text in {"", "1", "true", "yes", "on", "kill", "engaged"}:
        return True
    if text in {"0", "false", "no", "off", "clear"}:
        return False
    return True  # unknown content → fail closed


def engage_kill_switch(root: Path | None = None, reason: str = "manual") -> Path:
    p = kill_switch_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(f"engaged\nreason={reason}\n")
    return p


def clear_kill_switch(root: Path | None = None) -> None:
    p = kill_switch_path(root)
    if p.exists():
        p.write_text("off\n")
