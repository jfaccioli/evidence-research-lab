"""Reproducibility stamps: git SHA, config hash, python version."""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path
from typing import Any

from crl.shared.config import config_hash
from crl.shared.types import ReproStamp


def _git(cmd: list[str], cwd: Path | None = None) -> str | None:
    try:
        out = subprocess.check_output(
            ["git", *cmd],
            cwd=cwd,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return out.strip()
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return None


def git_info(cwd: Path | None = None) -> tuple[str, bool]:
    sha = _git(["rev-parse", "HEAD"], cwd=cwd) or "unknown"
    dirty_out = _git(["status", "--porcelain"], cwd=cwd)
    dirty = bool(dirty_out)
    return sha, dirty


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def make_repro_stamp(
    cfg: dict[str, Any],
    *,
    dataset_id: str = "",
    data_sha256: str = "",
    hypothesis_id: str = "",
    hypothesis_version: int = 1,
    mode: str = "exploratory",
    seed: int = 42,
    cwd: Path | None = None,
) -> ReproStamp:
    sha, dirty = git_info(cwd)
    return ReproStamp(
        git_sha=sha,
        git_dirty=dirty,
        config_hash=config_hash(cfg),
        dataset_id=dataset_id,
        data_sha256=data_sha256,
        python_version=sys.version.split()[0],
        seed=seed,
        hypothesis_id=hypothesis_id,
        hypothesis_version=hypothesis_version,
        mode=mode,
    )
