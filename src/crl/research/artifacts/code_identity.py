"""System-derived code identity for checkpoints (caller strings are not proof)."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class CodeIdentity:
    git_sha: Optional[str]
    package_version: str
    dirty: bool
    source: str  # e.g. "git+package"


def _package_version() -> str:
    try:
        from crl import __version__ as ver

        text = str(ver).strip()
        if text:
            return text
    except Exception:
        pass
    return "0.0.0-unknown"


def _git_identity(repo_hint: Optional[Path] = None) -> tuple[Optional[str], bool]:
    """Return (sha, dirty) from the local git checkout when available."""
    cwd = str(repo_hint) if repo_hint is not None else None
    try:
        sha_proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if sha_proc.returncode != 0:
            return None, True
        sha = (sha_proc.stdout or "").strip().lower()
        if not sha or any(ch not in "0123456789abcdef" for ch in sha):
            return None, True
        dirty_proc = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if dirty_proc.returncode != 0:
            return sha, True
        dirty = bool((dirty_proc.stdout or "").strip())
        return sha, dirty
    except (OSError, subprocess.SubprocessError):
        return None, True


def derive_code_identity(*, repo_hint: Optional[Path] = None) -> CodeIdentity:
    """Derive code identity from package metadata + git; never trust callers."""
    git_sha, dirty = _git_identity(repo_hint)
    version = _package_version()
    return CodeIdentity(
        git_sha=git_sha,
        package_version=version,
        dirty=dirty,
        source="git+package",
    )
