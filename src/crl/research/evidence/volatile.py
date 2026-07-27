"""Volatile research_kb paths that must never be treated as stable releases."""

from __future__ import annotations

from pathlib import Path, PurePosixPath

# Paths relative to research_kb / repo conventions (design §10.2).
VOLATILE_BASENAMES = frozenset(
    {
        "latest_plan.json",
        "latest_plan.md",
        "knowledge_state.json",
        "research_budget.json",
        "thesis_tree.json",  # machine JSON; md may be release-packaged with banner
    }
)

VOLATILE_DIRNAMES = frozenset(
    {
        "proposed",
    }
)


def is_volatile_research_path(path: str | Path) -> bool:
    """True if path is a volatile planner/KB artefact (not a stable release)."""
    p = PurePosixPath(str(path).replace("\\", "/"))
    name = p.name
    if name in VOLATILE_BASENAMES:
        return True
    parts = p.parts
    for part in parts:
        if part in VOLATILE_DIRNAMES:
            return True
    # Explicit common live plan stems
    if name.startswith("latest_plan"):
        return True
    return False


def refuse_stable_release_of_volatile(path: str | Path) -> None:
    """Raise if caller attempts to treat a volatile path as a stable release."""
    if is_volatile_research_path(path):
        raise ValueError(
            f"volatile path cannot be a stable scientific release: {path}"
        )
